import traceback
import boto3
import json
import pymysql
import time
import os
import requests
import threading
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re


from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser, OrGroup


last_indexed_url = None
stemmer = PorterStemmer()

# whoosh schema 
schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    description=TEXT(stored=True),
    keywords=TEXT(stored=True),
    s3_key=ID(stored=True),
    s3_bucket=ID(stored=True)
)

# open  whoosh index
index_dir = "whoosh_index"
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
    ix = create_in(index_dir, schema)
else:
    ix = open_dir(index_dir)



# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue'
search_request_queue_url ="https://sqs.us-east-1.amazonaws.com/608542499503/SearchQueue"
search_response_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/SearchResponseQueue"

overallStatus = 1  # 1 -> running succesfully
runningStatus = 1  # 0 ->  busy, 1 ->  free

status_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/IndexerStatus'

# RDS setup
db_config = {
    "host": "index-db.cyv2uaoamjlb.us-east-1.rds.amazonaws.com",  
    "user": "admin",                   
    "database": "new_schema",          
    "region": "us-east-1"                     
}

#heartbeat code
def send_status_message():
    try:
        global last_indexed_url
        ip_address = requests.get("http://checkip.amazonaws.com/").text.strip()
        
        heartbeat_message = {
            "overallStatus": overallStatus,
            "runningStatus": runningStatus,
            "ip_address": ip_address,
            "last_indexed_url": last_indexed_url  # Include the last indexed URL
        }
         
        sqs.send_message(
            QueueUrl=status_queue_url,
            MessageBody=json.dumps(heartbeat_message)
        )
        print(f"Sent status message:{heartbeat_message}")
    except Exception as e:
        print(f"Failed to send status message: {e}")
        

def heartbeat():
    while True:
        send_status_message()
        time.sleep(60)  

# start thread
heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
heartbeat_thread.start()



def get_rds_connection():
    """establish rds connection."""
    password = os.getenv("RDS_PASSWORD")  
    if not password:
        raise ValueError("RDS_PASSWORD environment variable is not set")

    # connect to RDS
    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=password,
        database=db_config["database"]
    )
    return connection

def execute_query(query, params=None, fetch_results=False):
    connection = None
    try:
        connection = get_rds_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor if fetch_results else None)

     
        cursor.execute(query, params)


        if fetch_results:
            return cursor.fetchall()

      
        connection.commit()
    except Exception as e:
        print(f"Database operation failed: {e}")
        raise
    finally:
        if connection:
            connection.close()

def store_in_rds(data, max_retries=3, retry_delay=5):

    retries = 0
    while retries < max_retries:
        try:
            
            #store in rds
            sql = """
            INSERT INTO indexed_data (url, title, description, keywords, s3_key, s3_bucket)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                data["url"],
                data.get("title"),
                data.get("description"),
                data.get("keywords"),
                data.get("s3_key"),
                data.get("s3_bucket")
            )
            execute_query(sql, params)
            
            
            print(f"Stored data for URL: {data['url']} in RDS.")
            break
            
        except Exception as e:
            print(f"Failed to index data in Whoosh: {e}")
            retries += 1
           
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Max retries reached. Failed to store data for URL: {data['url']}")
                raise 


def index_in_whoosh(data):
    try:
        processed_title = clean_text(data.get("title", ""))
        processed_description = stem_text(clean_text(" ".join(analyze_keywords(data.get("description", "")))))
        processed_keywords = clean_text(" ".join(analyze_keywords(data.get("keywords", ""))))

        print(f"Processed fields for URL {data['url']}:")
        print(f"Title: {processed_title}")
        print(f"Description: {processed_description}")
        print(f"Keywords: {processed_keywords}")
        
        writer = ix.writer()
        writer.update_document(
            url=data["url"],
            title=processed_title,
            description=processed_description,
            keywords=processed_keywords
        )
        writer.commit()
        print(f"Indexed data for URL: {data['url']} in Whoosh.")
        
        
    except Exception as e:
        print(f"Failed to index data in Whoosh: {e}")
        traceback.print_exc()
        raise
    


def clean_text(text):
    """Clean and normalize text for indexing."""
    if not text:
        return ""
    try:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        # Strip extra whitespace
        text = text.strip()
        return text
    except Exception as e:
        print(f"Error in clean_text: {e}")
        traceback.print_exc()
        return ""

def analyze_keywords(text):
    """Perform basic keyword analysis."""
    if not text:
        return []

    try:
        words = word_tokenize(text)
        # Remove stop words
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words]
        # Count word frequencies
        word_counts = Counter(filtered_words)
        # Return the most common keywords
        return [word for word, count in word_counts.most_common(10)]
    except Exception as e:
        print(f"Error in analyze_keywords: {e}")
        traceback.print_exc()
        return []
    
def stem_text(text):
    """Stem words in the text."""
    if not text:
        return ""
    try:
        words = word_tokenize(text)
        stemmed_words = [stemmer.stem(word) for word in words]
        return " ".join(stemmed_words)
    except Exception as e:
        print(f"Error in stem_text: {e}")
        traceback.print_exc()
        return ""


def process_message(message):
    global last_indexed_url
    try:
        
        body = json.loads(message['Body'])
        required_fields = ["url", "title", "description", "keywords", "s3_key", "s3_bucket"]
        for field in required_fields:
            if field not in body or body[field] is None:
                raise ValueError(f"Missing required field: {field}")
            
        index_in_whoosh(body)
            
        store_in_rds(body)
        last_indexed_url = body["url"]
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Failed to process message: {e}")
        
        
def process_search_request(message):
    try:

        body = json.loads(message['Body'])
        if 'keywords' not in body or 'request_id' not in body:
            raise ValueError("Missing required fields: 'keywords' and/or 'request_id'")

        keywords = body['keywords'].lower()
        request_id = body['request_id']

        with ix.searcher() as searcher:
            # query = QueryParser("keywords", ix.schema).parse(f'"{keywords}"')
            parser = MultifieldParser(["title^3", "description", "keywords^2"],  # boost "title" field
                                        ix.schema,
                                        group=OrGroup
                                     )
            # query = Term("keywords", keywords)
            query = parser.parse(keywords)
            print(f"Search query: {query}")
            results = searcher.search(query, limit=10)  # limit to top 10 results

            urls = [result["url"] for result in results]
            print(f"Search results for keywords '{keywords}': {urls}")
            
            # for result in results:
            #     print(f"URL: {result['url']},Score: {result.score} Title: {result['title']}, Description: {result['description']}, Keywords: {result['keywords']}")

        # Fetch full data from RDS
        if urls:
            placeholders = ', '.join(['%s'] * len(urls))
            sql = f"""
            SELECT url, title, description, keywords, s3_key, s3_bucket
            FROM indexed_data
            WHERE url IN ({placeholders})
            """
            print(f"executing SQL: {sql} with params: {urls}")
            full_results = execute_query(sql, urls, fetch_results=True)
        else:
            full_results = []


        response = {
            'request_id': request_id,
            'results': full_results
        }
        sqs.send_message(
            QueueUrl=search_response_queue_url,
            MessageBody=json.dumps(response)
        )
        print(f"Search results sent for request ID: {request_id}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Failed to process search request: {e}")
        

def poll_result_queue():
    global runningStatus
    while True:
        # print("Polling for messages in ResultQueue...")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )

        if 'Messages' not in response:
            # print("No messages in ResultQueue.")
            runningStatus = 1
        else:
            for message in response['Messages']:
                runningStatus = 0
                process_message(message)

                # Delete the message after processing
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted message with receipt handle: {receipt_handle}")
                runningStatus = 1

        time.sleep(2)

def poll_search_queue():
    global runningStatus
    while True:
        # print("Polling for messages in SearchQueue...")
        search_response = sqs.receive_message(
            QueueUrl=search_request_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )

        if 'Messages' not in search_response:
            # print("No messages in SearchQueue.")
            runningStatus = 1
        else:
            for message in search_response['Messages']:
                runningStatus = 0
                process_search_request(message)

                # Delete the message after processing
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=search_request_queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted search request with receipt handle: {receipt_handle}")
                runningStatus = 1

        time.sleep(2)
        
            
def main():
    
    
    thread1 = threading.Thread(target=poll_result_queue, daemon=True)
    thread2 = threading.Thread(target=poll_search_queue, daemon=True)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
        
        


if __name__ == "__main__":
    main()