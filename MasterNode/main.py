import time
import boto3
import json
import mysql.connector
from mysql.connector import Error

# AWS SQS Setup
sqs = boto3.client('sqs', region_name='us-east-1')
input_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Client_Master_Queue'
output_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/TaskQueue'

# RDS MySQL Setup
db = mysql.connector.connect(
    host="rds-test.cyv2uaoamjlb.us-east-1.rds.amazonaws.com",
    user="admin",
    password="admin123",
    database="urls"
)
cursor = db.cursor()

print("Listening for messages... (Press CTRL+C to stop)")
try:
    while True:
        # Receive message from SQS
        response = sqs.receive_message(
            QueueUrl=input_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5  # Enable long polling
        )

        messages = response.get('Messages', [])
        if not messages:
            print("No new messages. Waiting...")
            time.sleep(5)  # Wait before checking again
            continue

        for message in messages:
            try:
                body = json.loads(message['Body'])

                url = body['url']
                status = body.get('status', 'NEW')
                depth = body['depth']

                if status not in ['NEW', 'CRAWLED', 'INDEXED', 'ERROR']:
                    print(
                        f"Invalid status '{status}' for URL: {url}. Skipping.")
                    continue

                cursor.execute(
                    "SELECT COUNT(*) FROM Urls WHERE url = %s", (url,))
                url_exists = cursor.fetchone()[0]
                if url_exists == 0:
                    insert_query = """
                        INSERT INTO Urls (url, status, depth)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_query, (url, status, depth))
                    db.commit()
                    print(f"Inserted URL: {url} with status: {status}")
                else:
                    print(f"URL already exists in the database: {url}")

                if status == 'NEW':
                    update_query = """
                        UPDATE Urls SET status = 'CRAWLED' WHERE url = %s AND status = 'NEW'
                    """
                    cursor.execute(update_query, (url,))
                    db.commit()
                    print(f"Updated URL status to 'CRAWLED': {url}")

                message_to_send = {
                    'start_url': url,
                    'depth': depth,
                    'max_pages': 5
                }

                try:
                    sqs.send_message(
                        QueueUrl=output_queue_url,
                        MessageBody=json.dumps(message_to_send)
				    )
                    print(f"Sent URL to output queue: {url}")
                except Exception as e:
                    print(f"Failed to send message to output queue: {e}")

                sqs.delete_message(
                    QueueUrl=input_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                print(f"Message deleted from input SQS: {message['MessageId']}")

            except Error as e:
                print(f"Database error while processing message: {str(e)}")
                db.rollback()

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    cursor.close()
    db.close()
    print("Database connection closed.")