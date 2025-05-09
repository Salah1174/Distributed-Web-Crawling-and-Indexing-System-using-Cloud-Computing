import boto3
import json


# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')

sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

def send_sqs_message(queue_url, message_body):
    try:
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
        print(f"Message sent to SQS: {message_body}")
    except Exception as e:
        print(f"Failed to send message to SQS: {e}")
