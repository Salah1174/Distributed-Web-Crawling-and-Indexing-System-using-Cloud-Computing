import time
import threading
import boto3
import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# AWS SQS Setup
sqs = boto3.client('sqs', region_name='us-east-1')
input_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Client_Master_Queue'
output_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/TaskQueue'
crawler_queue_output_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler-Master-Queue'
crawler_queue_heartbeat = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler_Status'
indexer_queue_heartbeat = 'https://sqs.us-east-1.amazonaws.com/608542499503/IndexerStatus'
master_client_crawlerstatus = 'https://sqs.us-east-1.amazonaws.com/608542499503/Master-Client-CrawlerStatus-Queue'


# Database setup
rds_host = 'rds-test.cyv2uaoamjlb.us-east-1.rds.amazonaws.com'
rds_user = 'admin'
rds_password = 'admin123'
rds_db = 'urls'


def get_db_connection():
    return mysql.connector.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )


def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True if fetch else False)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def url_exists(url):
    result = execute_query(
        "SELECT COUNT(*) as count FROM Urls WHERE url = %s", (url,), fetch=True)
    return result[0]['count'] > 0


def url_status(url):
    result = execute_query(
        "SELECT status FROM Urls WHERE url = %s", (url,), fetch=True)
    return result[0]['status'] if result else None


def insert_url(url, status, depth):
    execute_query("""
        INSERT INTO Urls (url, status, depth, last_dispatched)
        VALUES (%s, %s, %s, %s)
    """, (url, status, depth, datetime.utcnow()))


def update_url_status(url, status):
    execute_query("UPDATE Urls SET status = %s WHERE url = %s", (status, url))


def update_last_dispatched(url):
    execute_query(
        "UPDATE Urls SET last_dispatched = NOW() WHERE url = %s", (url,))


def requeue_stale_urls():
    try:
        rows = execute_query("""
            SELECT url, depth FROM Urls
            WHERE status = 'NEW' AND last_dispatched IS NOT NULL
            AND last_dispatched < NOW() - INTERVAL 2 MINUTE
        """, fetch=True)
        for row in rows:
            url, depth = row['url'], row['depth']
            print(f"[REQUEUE] URL stale > 2 mins, requeuing: {url}")
            sqs.send_message(
                QueueUrl=output_queue_url,
                MessageBody=json.dumps(
                    {'start_url': url, 'depth': depth, 'max_pages': 5})
            )
            update_last_dispatched(url)
    except Exception as e:
        print(f"Error requeueing stale URLs: {e}")


def process_heartbeat(queue_url, component_name):
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=10,
            WaitTimeSeconds=1, VisibilityTimeout=0
        )
        messages = response.get('Messages', [])
        if not messages:
            print(f"No heartbeat received from {component_name}")
            return

        for message in messages:
            try:
                heartbeat = json.loads(message['Body'])
                overall, running = heartbeat.get(
                    'overallStatus'), heartbeat.get('runningStatus')
                ip = heartbeat.get('ip_address', 'Unknown')
                last_url_field = 'last_indexed_url' if component_name == 'Indexer' else 'last_crawled_url'
                last_url = heartbeat.get(last_url_field)

                print(f"\n--- {component_name} Heartbeat ---")
                print(f"IP Address: {ip}")
                print(
                    f"Running Status: {'Running' if running == 0 else 'Idle'}")

                if isinstance(last_url, str) and last_url.strip():
                    print(
                        f"Last {last_url_field.replace('_', ' ').capitalize()}: {last_url}")
                elif last_url is None:
                    print("No last URL provided.")
                else:
                    print("Invalid or empty last URL")

                if overall != 1:
                    print(f"Status: {component_name} is UNHEALTHY")
                elif running == 1:
                    print(f"Status: {component_name} is IDLE")
                else:
                    print(f"Status: {component_name} is HEALTHY and RUNNING")

                if overall == 1 and running == 1 and isinstance(last_url, str) and last_url.strip():
                    if url_exists(last_url):
                        new_status = 'INDEXED' if component_name == 'Indexer' else 'CRAWLED'
                        update_url_status(last_url, new_status)
                        print(
                            f"Updated status to {new_status} for: {last_url}")
                    else:
                        print(f"URL not found in DB: {last_url}")
                else:
                    print(
                        "No valid last URL to process or system is not running/healthy.")
                sqs.send_message(
                    QueueUrl=master_client_crawlerstatus,
                    MessageBody=json.dumps(
                        {'overallStatus': overall, 'runningStatus': running, 'ip_address': ip, 'last_crawled_url': last_url})
                )

                sqs.delete_message(QueueUrl=queue_url,
                                   ReceiptHandle=message['ReceiptHandle'])

            except Exception as e:
                print(f"Failed to process {component_name} heartbeat: {e}")
    except Exception as e:
        print(f"Error reading {component_name} heartbeat: {e}")


def start_heartbeat_thread(queue_url, component_name):
    def heartbeat_loop():
        while True:
            try:
                process_heartbeat(queue_url, component_name)
                time.sleep(5)
            except Exception as e:
                print(f"Error in {component_name} heartbeat thread: {e}")
                time.sleep(5)
    threading.Thread(target=heartbeat_loop, daemon=True).start()


def process_sqs_message(queue_url, delete=True):
    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5)
    return response.get('Messages', [])


def process_client_master_messages():
    for message in process_sqs_message(input_queue_url):
        try:
            body = json.loads(message['Body'])
            url, status, depth = body['url'], body.get(
                'status', 'NEW'), body['depth']

            if status not in ['NEW', 'CRAWLED', 'INDEXED', 'ERROR']:
                print(f"Invalid status '{status}' for URL: {url}. Skipping.")
                continue

            # Ensure URL isn't processed twice
            if url_status(url) not in ['NEW', 'CRAWLED', 'INDEXED']:
                if not url_exists(url):
                    insert_url(url, status, depth)
                    print(f"Inserted URL: {url} with status: NEW")
                else:
                    print(f"URL already exists in DB: {url}")

                sqs.send_message(QueueUrl=output_queue_url, MessageBody=json.dumps(
                    {'start_url': url, 'depth': depth, 'max_pages': 5}))
                update_last_dispatched(url)
                print(f"Sent URL to output queue: {url}")

                sqs.delete_message(QueueUrl=input_queue_url,
                                   ReceiptHandle=message['ReceiptHandle'])
                print(
                    f"Message deleted from input SQS: {message.get('MessageId', 'Unknown')}")
            else:
                print(f"Skipping URL '{url}' as it is already processed")

        except Exception as e:
            print(f"Error processing client-master message: {e}")


def process_crawler_output_messages():
    for message in process_sqs_message(crawler_queue_output_url):
        try:
            body = json.loads(message['Body'])
            new_url = body['url']
            seed_url = body.get('start_url')

            if not seed_url:
                print(f"Missing start_url for: {new_url}. Skipping.")
                continue

            # Get depth of the seed URL
            seed_data = execute_query(
                "SELECT depth FROM Urls WHERE url = %s", (seed_url,), fetch=True)
            if not seed_data:
                print(f"Seed URL not found in DB: {seed_url}. Skipping.")
                continue

            seed_depth = seed_data[0]['depth']
            new_depth = max(seed_depth - 1, 0)  # Prevent negative depth

            # Insert new URL if it doesn't exist or was never processed
            if not url_exists(new_url):
                insert_url(new_url, 'NEW', new_depth)
                print(
                    f"[NEW] Inserted crawler URL: {new_url} with depth: {new_depth}")
                sqs.send_message(QueueUrl=output_queue_url, MessageBody=json.dumps(
                    {'start_url': new_url, 'depth': new_depth, 'max_pages': 5}))
                update_last_dispatched(new_url)
                print(f"Sent to task queue: {new_url}")
            else:
                current_status = url_status(new_url)
                if current_status not in ['NEW', 'CRAWLED', 'INDEXED']:
                    update_url_status(new_url, 'NEW')
                    print(f"[REINSERTED] Reset status to NEW for: {new_url}")
                    sqs.send_message(QueueUrl=output_queue_url, MessageBody=json.dumps(
                        {'start_url': new_url, 'depth': new_depth, 'max_pages': 5}))
                    update_last_dispatched(new_url)
                else:
                    print(
                        f"Skipping already processed URL: {new_url} ({current_status})")

            # ✅ Mark seed URL as CRAWLED
            update_url_status(seed_url, 'CRAWLED')
            print(f"Marked seed URL as CRAWLED: {seed_url}")

            # ✅ Delete message after processing
            sqs.delete_message(QueueUrl=crawler_queue_output_url,
                               ReceiptHandle=message['ReceiptHandle'])

        except Exception as e:
            print(f"Error processing crawler output: {e}")


# Start of program
print("Listening for messages... (Press CTRL+C to stop)")
start_heartbeat_thread(crawler_queue_heartbeat, "Crawler")
start_heartbeat_thread(indexer_queue_heartbeat, "Indexer")

try:
    while True:
        process_client_master_messages()
        process_crawler_output_messages()
        requeue_stale_urls()
        time.sleep(2)
except KeyboardInterrupt:
    print("\nStopping gracefully...")
