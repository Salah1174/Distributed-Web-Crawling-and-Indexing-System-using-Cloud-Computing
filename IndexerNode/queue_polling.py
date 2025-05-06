import time
from message_processing import process_message, process_search_request
from aws_utils import sqs
from heartbeat import send_status_message

status_queue_url='https://sqs.us-east-1.amazonaws.com/608542499503/IndexerStatus'
overall_status=1
        
def poll_result_queue(queue_url, last_indexed_url, running_status,ix):
    global status_queue_url, overall_status
    while True:
        response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=5)
        if 'Messages' not in response:
            running_status = 1
        else:
            for message in response['Messages']:
                running_status = 0
                send_status_message(status_queue_url, overall_status, running_status, last_indexed_url)
                process_message(message, last_indexed_url,ix)
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted message with receipt handle: {receipt_handle}")
                running_status = 1
                send_status_message(status_queue_url, overall_status, running_status, last_indexed_url)
                last_indexed_url["value"] = None
        time.sleep(2)

def poll_search_queue(search_request_queue_url, ix, search_response_queue_url, running_status):
    global status_queue_url, overall_status
    while True:
        response = sqs.receive_message(QueueUrl=search_request_queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=5)
        if 'Messages' not in response:
            running_status = 1
            
        else:
            for message in response['Messages']:
                running_status = 0
                send_status_message(status_queue_url, overall_status, running_status, None)
                process_search_request(message, ix, search_response_queue_url)
                receipt_handle = message['ReceiptHandle']
                sqs.delete_message(QueueUrl=search_request_queue_url, ReceiptHandle=receipt_handle)
                print(f"Deleted search request with receipt handle: {receipt_handle}")
                running_status = 1
                send_status_message(status_queue_url, overall_status, running_status, None)
        time.sleep(2)