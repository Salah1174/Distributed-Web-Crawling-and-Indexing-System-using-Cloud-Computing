import boto3
import json
import pymysql
import time
import os
import requests


# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue'

# RDS setup
db_config = {
    "host": "index-db.cyv2uaoamjlb.us-east-1.rds.amazonaws.com",  
    "user": "admin",                   
    "database": "new_schema",          
    "region": "us-east-1"                     
}

def download_ca_certificate():
    """Download the RDS CA certificate dynamically."""
    url = "https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem"
    cert_path = "/tmp/rds-combined-ca-bundle.pem"
    if not os.path.exists(cert_path):
        response = requests.get(url)
        with open(cert_path, "wb") as cert_file:
            cert_file.write(response.content)
    return cert_path


def get_iam_token():
    """Generate an IAM token for RDS authentication."""
    client = boto3.client('rds', region_name=db_config["region"])
    token = client.generate_db_auth_token(
        DBHostname=db_config["host"],
        Port=3306,  
        DBUsername=db_config["user"]
    )
    return token

def store_in_rds(data):
    connection = None 
    try:
        # Generate IAM token
        token = get_iam_token()
        
        ca_cert_path = download_ca_certificate()

        # Connect to RDS using the IAM token
        connection = pymysql.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=token,
            database=db_config["database"],
            # ssl={"ca": ca_cert_path}  # Use the RDS CA certificate
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