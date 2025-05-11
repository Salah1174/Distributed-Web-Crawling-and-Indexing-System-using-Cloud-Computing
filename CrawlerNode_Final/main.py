import boto3
import json
import subprocess
import uuid
import time
import sys
import threading
import requests

with open("/home/ec2-user/mainlog.txt", "a") as log:
    log.write(f"Script started at {time.ctime()}\n")
    log.write(f"Args: {sys.argv}\n")

# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

input_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/TaskQueue"
output_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue"
s3_bucket = 'webcrawlerstorage'
url_lock = threading.Lock()

overallStatus = 1
runningStatus = [1]
last_crawled_url = {"value": ""}

status_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler_Status'


def send_sqs_message(queue_url, message_body):
    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        print(f"Sent message to queue: {message_body}")
    except Exception as e:
        print(f"Failed to send message to queue: {e}")


def send_status_message(status_queue_url, overall_status, running_status, last_crawled_url):
    try:
        ip_address = requests.get("http://checkip.amazonaws.com/").text.strip()
        with url_lock:
            last_url = last_crawled_url["value"]
        heartbeat_message = {
            "overallStatus": overall_status,
            "runningStatus": running_status,
            "ip_address": ip_address,
            "last_crawled_url": last_url
        }
        send_sqs_message(status_queue_url, heartbeat_message)
    except Exception as e:
        print(f"Failed to send status message: {e}")


def heartbeat(status_queue_url, overall_status, running_status, last_crawled_url):
    while True:
        send_status_message(status_queue_url, overall_status,
                            running_status, last_crawled_url)
        time.sleep(2)


def start_heartbeat_thread(status_queue_url, overall_status, running_status, last_crawled_url):
    heartbeat_thread = threading.Thread(
        target=heartbeat,
        args=(status_queue_url, overall_status,
              running_status, last_crawled_url),
        daemon=True
    )
    heartbeat_thread.start()
    return heartbeat_thread


# Use the Crawler-Status-Queue for heartbeat/status
crawler_status_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler_Status'

# Start the heartbeat thread, always up to date
start_heartbeat_thread(
    status_queue_url=crawler_status_queue_url,
    overall_status=overallStatus,
    running_status=runningStatus[0],
    last_crawled_url=last_crawled_url
)


def run_spider(start_url, depth, max_pages):
    runningStatus[0] = 0
    result = subprocess.run([
        "scrapy", "crawl", "mycrawler",
        "-a", f"start_url={start_url}",
        "-a", f"depth={depth}",
        "-a", f"max_pages={max_pages}",
        "-o", "output.json"
    ], cwd='/home/ec2-user/CrawlerNode_Final/learncrawling', capture_output=True, text=True)

    print("Crawler STDOUT:", result.stdout)
    print("Crawler STDERR:", result.stderr)

    output_file = 'output.json'
    unique_key = f"results/{uuid.uuid4()}.json"

    try:
        s3.upload_file(output_file, s3_bucket, unique_key)
        print(f"Results uploaded to S3 at {unique_key}")
    except Exception as e:
        print(f"Failed to upload results to S3: {e}")
        return

    # Read output.json and send each item to ResultQueue
    try:
        with open('/home/ec2-user/CrawlerNode_Final/learncrawling/output.json', 'r', encoding='utf-8') as f:
            items = json.load(f)
        for item in items:
            try:
                sqs.send_message(
                    QueueUrl=output_queue_url,
                    MessageBody=json.dumps({
                        "url": item.get("url"),
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "keywords": item.get("keywords"),
                        "s3_key": unique_key,
                        "s3_bucket": s3_bucket
                    })
                )
                print(
                    "************************************************************SUCCESS: SENT TO RESULTQUEUE")
            except Exception as e:
                print(f"Failed to send message to SQS: {e}")
    except Exception as e:
        print(f"Failed to read output.json: {e}")

    with url_lock:
        last_crawled_url["value"] = start_url
    runningStatus[0] = 1


if len(sys.argv) > 3:
    start_url = sys.argv[1]
    depth = sys.argv[2]
    max_pages = sys.argv[3]
    print(
        f"Running direct job for URL: {start_url}, Depth: {depth}, Max Pages: {max_pages}")
    run_spider(start_url, depth, max_pages)

else:
    while True:
        print("Waiting for new jobs...")
        response = sqs.receive_message(
            QueueUrl=input_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            if runningStatus[0] != 1:
                runningStatus[0] = 1
                send_status_message(
                    crawler_status_queue_url, overallStatus, runningStatus[0], last_crawled_url)
            continue

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        job = json.loads(message['Body'])

        if runningStatus[0] != 0:
            runningStatus[0] = 0
            send_status_message(crawler_status_queue_url,
                                overallStatus, runningStatus[0], last_crawled_url)

        start_url = job.get("start_url")
        depth = str(job.get("depth", 1))
        max_pages = str(job.get("max_pages", 5))

        print(
            f"Processing job for URL: {start_url}, Depth: {depth}, Max Pages: {max_pages}")
        run_spider(start_url, depth, max_pages)

        try:
            sqs.delete_message(QueueUrl=input_queue_url,
                               ReceiptHandle=receipt_handle)
            print(
                f"Deleted message from input queue with receipt handle: {receipt_handle}")
        except Exception as e:
            print(f"Failed to delete message from input queue: {e}")

        if runningStatus[0] != 1:
            runningStatus[0] = 1
            send_status_message(crawler_status_queue_url,
                                overallStatus, runningStatus[0], last_crawled_url)

        time.sleep(20)
