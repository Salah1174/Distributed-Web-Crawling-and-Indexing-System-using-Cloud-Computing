import boto3
import json
import pymysql
import os
import time

from dotenv import load_dotenv
load_dotenv()

# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue'

# RDS setup 
db_config = {
    "host": os.getenv("RDS_HOST"),
    "user": os.getenv("RDS_USER"),
    "password": os.getenv("RDS_PASSWORD"),
    "database": os.getenv("RDS_DATABASE")
}

def store_in_rds(data):
    try:
        # Connect to RDS 
        connection = pymysql.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = connection.cursor()

        # Insert the data into the table
        sql = """
        INSERT INTO crawled_data (url, title, description, keywords, s3_key, s3_bucket)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data["url"],
            data.get("title"),
            data.get("description"),
            data.get("keywords"),
            data.get("s3_key"),
            data.get("s3_bucket")
        ))
        connection.commit()
        print(f"Stored data for URL: {data['url']} in RDS.")
    except Exception as e:
        print(f"Failed to store data in RDS: {e}")
    finally:
        if connection:
            connection.close()

def process_message(message):
    try:
        # Parse the message body
        body = json.loads(message['Body'])
        store_in_rds(body)
    except Exception as e:
        print(f"Failed to process message: {e}")

def main():
    while True:
        print("Polling for messages...")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10  # Long polling
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            continue

        # Process each message
        for message in response['Messages']:
            process_message(message)

            # Delete the message after processing
            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            print(f"Deleted message with receipt handle: {receipt_handle}")

        # Sleep for a short time before polling again
        time.sleep(5)

if __name__ == "__main__":
    main()