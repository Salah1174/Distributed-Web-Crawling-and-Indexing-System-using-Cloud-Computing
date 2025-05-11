# CrawlerNode/heartbeat.py
import boto3
import json
import threading
import time
import requests

# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

input_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/TaskQueue"
output_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue"
s3_bucket = 'webcrawlerstorage'
status_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler_Status'

def send_sqs_message(queue_url, message_body):
    try:
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
        print(f"Message sent to SQS: {message_body}")
    except Exception as e:
        print(f"Failed to send message to SQS: {e}")
        
def send_status_message(status_queue_url, overall_status, running_status, last_crawled_url):
    try:
        ip_address = requests.get("http://checkip.amazonaws.com/").text.strip()
        heartbeat_message = {
            "overallStatus": overall_status,
            "runningStatus": running_status,
            "ip_address": ip_address,
            "last_crawled_url": last_crawled_url["value"]
        }
        send_sqs_message(status_queue_url, heartbeat_message)
    except Exception as e:
        print(f"Failed to send status message: {e}")

def heartbeat(status_queue_url, overall_status, running_status_ref, last_crawled_url):
    while True:
        # running_status_ref is a function or a mutable object reference
        if callable(running_status_ref):
            running_status = running_status_ref()
        else:
            running_status = running_status_ref[0] if isinstance(running_status_ref, list) else running_status_ref
        send_status_message(status_queue_url, overall_status, running_status, last_crawled_url)
        time.sleep(2)

def start_heartbeat_thread(status_queue_url, overall_status, running_status_ref, last_crawled_url):
    heartbeat_thread = threading.Thread(
        target=heartbeat,
        args=(status_queue_url, overall_status, running_status_ref, last_crawled_url),
        daemon=True
    )
    heartbeat_thread.start()
    return heartbeat_thread
