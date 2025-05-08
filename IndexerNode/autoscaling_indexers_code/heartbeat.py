import threading
import time
import requests

from aws_utils import send_sqs_message



def send_status_message(status_queue_url, overall_status, running_status, last_indexed_url):
    try:
        ip_address = requests.get("http://checkip.amazonaws.com/").text.strip()
        heartbeat_message = {
            "overallStatus": overall_status,
            "runningStatus": running_status,
            "ip_address": ip_address,
            "last_indexed_url": last_indexed_url["value"] if last_indexed_url else None
        }
        send_sqs_message(status_queue_url, heartbeat_message)
    except Exception as e:
        print(f"Failed to send status message: {e}")

def heartbeat(status_queue_url, overall_status, running_status, last_indexed_url):
    while True:
        send_status_message(status_queue_url, overall_status, running_status, last_indexed_url)
        time.sleep(60)

def start_heartbeat_thread(status_queue_url, overall_status, running_status, last_indexed_url):
    heartbeat_thread = threading.Thread(
        target=heartbeat,
        args=(status_queue_url, overall_status, running_status, last_indexed_url),
        daemon=True
    )
    heartbeat_thread.start()
    
