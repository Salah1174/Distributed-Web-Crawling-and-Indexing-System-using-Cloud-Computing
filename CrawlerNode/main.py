
import boto3
import json
import subprocess
import uuid
import time
import sys




with open("/home/ec2-user/mainlog.txt", "a") as log: #was for debugging purposes, not needed anymore
    log.write(f"Script started at {time.ctime()}\n")
    log.write(f"Args: {sys.argv}\n")




# AWS setup
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

input_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Client_Master_Queue'
output_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue'
s3_bucket = 'webcrawlerstorage'

# Check if the script was run with command-line arguments (i.e., direct job submission)
# because script can either fully execute crawling from cmd by sending the parameters manually, or just be initiated in cmd to periodically poll for SQS url and args to crawl
if len(sys.argv) > 3:
    # Use command-line arguments: start_url, depth, max_pages
    start_url = sys.argv[1]
    depth = sys.argv[2]
    max_pages = sys.argv[3]
    print(f"Running direct job for URL: {start_url}, Depth: {depth}, Max Pages: {max_pages}")

    # Trigger the scrapy crawl spider directly
    subprocess.run([
        "scrapy", "crawl", "mycrawler",
        "-a", f"start_url={start_url}",
        "-a", f"depth={depth}",
        "-a", f"max_pages={max_pages}"
    ], cwd='/home/ec2-user/test_crawler/learncrawling')  

    # After crawling is done, upload the result to S3
    output_file = 'output.json'
    unique_key = f"results/{uuid.uuid4()}.json"

    try:
        s3.upload_file(output_file, s3_bucket, unique_key)
        print(f"Results uploaded to S3 at {unique_key}")
    except Exception as e:
        print(f"Failed to upload results to S3: {e}")

    # Send the S3 result location to the output queue for further processing
    result_message = {
        "s3_key": unique_key,
        "start_url": start_url
    }
    try:
        sqs.send_message(
            QueueUrl=output_queue_url,
            MessageBody=json.dumps(result_message)
        )
        print(f"Sent result message to output queue: {result_message}")
    except Exception as e:
        print(f"Failed to send message to output queue: {e}")

else:
    # If no arguments are passed, start the continuous polling for jobs in the SQS queue, using infinite loop and long polling  
    while True:
        print("Waiting for new jobs...")
        response = sqs.receive_message(
            QueueUrl=input_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10  # Long polling for up to 10 seconds
        )

        if 'Messages' not in response:
            print("No messages in queue.")
            continue  # If no messages, wait for the next poll

        # Process the received message
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        job = json.loads(message['Body'])

        # Extract job parameters
        start_url = job.get("start_url")
        depth = str(job.get("depth", 1))
        max_pages = str(job.get("max_pages", 5))

        print(f"Processing job for URL: {start_url}, Depth: {depth}, Max Pages: {max_pages}")

        # Trigger the scrapy crawl spider
        subprocess.run([
            "scrapy", "crawl", "mycrawler",
            "-a", f"start_url={start_url}",
            "-a", f"depth={depth}",
            "-a", f"max_pages={max_pages}"
        ], cwd='/home/ec2-user/test_crawler/learncrawling') 

        # After crawling is done, upload the result to S3
        output_file = 'output.json'
        unique_key = f"results/{uuid.uuid4()}.json"

        try:
            s3.upload_file(output_file, s3_bucket, unique_key)
            print(f"Results uploaded to S3 at {unique_key}")
        except Exception as e:
            print(f"Failed to upload results to S3: {e}")

        # Send the S3 result location to the output queue for further processing
        result_message = {
            "s3_key": unique_key,
            "start_url": start_url
        }
        try:
            sqs.send_message(
                QueueUrl=output_queue_url,
                MessageBody=json.dumps(result_message)
            )
            print(f"Sent result message to output queue: {result_message}")
        except Exception as e:
            print(f"Failed to send message to output queue: {e}")

        # Delete the message from the input queue after processing
        try:
            sqs.delete_message(QueueUrl=input_queue_url, ReceiptHandle=receipt_handle)
            print(f"Deleted message from input queue with receipt handle: {receipt_handle}")
        except Exception as e:
            print(f"Failed to delete message from input queue: {e}")

        # Sleep for a short time before checking for new messages again
        time.sleep(5)  # Adjust the sleep time if necessary



