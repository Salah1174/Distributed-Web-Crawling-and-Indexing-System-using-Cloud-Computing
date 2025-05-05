import boto3
import json
import pymysql
import time
import os
import requests


# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue'
search_request_queue_url ="https://sqs.us-east-1.amazonaws.com/608542499503/SearchQueue"
search_response_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/SearchResponseQueue"

# RDS setup
db_config = {
    "host": "index-db.cyv2uaoamjlb.us-east-1.rds.amazonaws.com",  
    "user": "admin",                   
    "database": "new_schema",          
    "region": "us-east-1"                     
}

# def download_ca_certificate():
#     """Download the RDS CA certificate dynamically."""
#     url = "https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem"
#     cert_path = "/tmp/rds-combined-ca-bundle.pem"
#     if not os.path.exists(cert_path):
#         response = requests.get(url)
#         with open(cert_path, "wb") as cert_file:
#             cert_file.write(response.content)
#     return cert_path


# def get_iam_token():
#     """Generate an IAM token for RDS authentication."""
#     client = boto3.client('rds', region_name=db_config["region"])
#     token = client.generate_db_auth_token(
#         DBHostname=db_config["host"],
#         Port=3306,  
#         DBUsername=db_config["user"]
#     )
#     return token

def get_rds_connection():
    """Establish a connection to the RDS database."""
    password = os.getenv("RDS_PASSWORD")  
    if not password:
        raise ValueError("RDS_PASSWORD environment variable is not set")

    # Connect to RDS
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

def store_in_rds(data):
    # connection = None 
    try:

        # Insert the data into the table
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
    except Exception as e:
        print(f"Failed to store data in RDS: {e}")


def process_message(message):
    try:
        # Parse the message body
        body = json.loads(message['Body'])
        store_in_rds(body)
    except Exception as e:
        print(f"Failed to process message: {e}")

def process_search_request(message):
    try:
        # Parse the message body
        body = json.loads(message['Body'])
        keywords = body.get('keywords')
        request_id = body.get('request_id')
        title = body.get('title')

        if not keywords or not request_id:
            print("Invalid search request")
            return

        # Query the indexed_data table
        sql = """
        SELECT url, title, description, keywords, s3_key, s3_bucket
        FROM indexed_data
        WHERE keywords LIKE %s
        """
        results = execute_query(sql, (f"%{title}%",), fetch_results=True)

        # Send the results to the response queue
        response = {
            'request_id': request_id,
            'results': results
        }
        sqs.send_message(
            QueueUrl=search_response_queue_url,
            MessageBody=json.dumps(response)
        )
        print(f"Search results sent for request ID: {request_id}")
    except Exception as e:
        print(f"Failed to process search request: {e}")        
        


def main():
    while True:
        print("Polling for messages...")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            # continue

        else:
            for message in response['Messages']:
                process_message(message)

                # Delete the message after processing
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted message with receipt handle: {receipt_handle}")
           
        print("Polling for messages in SearchQueue...")    
        search_response = sqs.receive_message(
            QueueUrl=search_request_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  
        )
        

        if 'Messages' not in search_response:
            print("No messages in SearchQueue.")
        else:
            for message in search_response['Messages']:
                process_search_request(message)

                # Delete the message after processing
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=search_request_queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted search request with receipt handle: {receipt_handle}")


        time.sleep(2)
        
        


if __name__ == "__main__":
    main()