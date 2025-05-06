import boto3
import json
import pymysql
import time
import os
# import requests
import threading


from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
# from whoosh.qparser import QueryParser
# from whoosh.query import Term
from whoosh.qparser import MultifieldParser, OrGroup

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
        sqs.send_message(
            QueueUrl=status_queue_url,
            MessageBody=json.dumps({
                "overallStatus": overallStatus,  
                "runningStatus": runningStatus  
            })
        )
        print(f"Sent status message: overallStatus={overallStatus}, runningStatus={runningStatus}")
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
        writer = ix.writer()
        writer.add_document(
            url=data["url"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            keywords=data.get("keywords", "")
        )
        writer.commit()
        print(f"Indexed data for URL: {data['url']} in Whoosh.")
    except Exception as e:
        print(f"Failed to index data in Whoosh: {e}")
        raise
    
def process_message(message):
    try:
        
        body = json.loads(message['Body'])
        required_fields = ["url", "title", "description", "keywords", "s3_key", "s3_bucket"]
        for field in required_fields:
            if field not in body or body[field] is None:
                raise ValueError(f"Missing required field: {field}")
            
        index_in_whoosh(body)
            
        store_in_rds(body)
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

        keywords = body['keywords']
        request_id = body['request_id']

        with ix.searcher() as searcher:
            # query = QueryParser("keywords", ix.schema).parse(f'"{keywords}"')
            parser = MultifieldParser(["title^2", "description", "keywords"],  # boost "title" field
                                        ix.schema,
                                        group=OrGroup
                                     )
            # query = Term("keywords", keywords)
            query = parser.parse(keywords)
            results = searcher.search(query, limit=10)  # limit to top 10 results

            urls = [result["url"] for result in results]

        # Fetch full data from RDS
        if urls:
            placeholders = ', '.join(['%s'] * len(urls))
            sql = f"""
            SELECT url, title, description, keywords, s3_key, s3_bucket
            FROM indexed_data
            WHERE url IN ({placeholders})
            """
            full_results = execute_query(sql, urls, fetch_results=True)
        else:
            full_results = []


        # sql = """
        # SELECT url, title, description, keywords, s3_key, s3_bucket
        # FROM indexed_data
        # WHERE keywords LIKE %s
        # """
        # results = execute_query(sql, (f"%{keywords}%",), fetch_results=True)

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
        
        
def main():
    global runningStatus
    while True:
        print("Polling for messages...")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            runningStatus = 1
            # continue

        else:
            for message in response['Messages']:
                runningStatus = 0 
                process_message(message)

                # delete after to avoid conflicts
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted message with receipt handle: {receipt_handle}")
                runningStatus = 1 
           
        print("Polling for messages in SearchQueue...")    
        search_response = sqs.receive_message(
            QueueUrl=search_request_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )
        

        if 'Messages' not in search_response:
            print("No messages in SearchQueue.")
            runningStatus = 1
        else:
            for message in search_response['Messages']:
                runningStatus = 0
                process_search_request(message)

                # delete after to avoid conflicts
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=search_request_queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted search request with receipt handle: {receipt_handle}")
                runningStatus = 1 


        time.sleep(2)
        
        


if __name__ == "__main__":
    main()