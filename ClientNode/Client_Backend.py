
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the SQS client
sqs = boto3.client('sqs', region_name='us-east-1')  # AWS region

# Specify your SQS queue URL
queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Client_Master_Queue'  # queue URL
search_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/SearchQueue'

@app.route('/send', methods=['POST'])
def send_seed_to_sqs():
    data = request.get_json()
    if not data or 'url' not in data:                                                        
        return jsonify({'error': 'Invalid JSON payload'}), 400

    try:
        # Send the message to SQS
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(data)
        )
        return jsonify({
            'message': 'Sent to SQS!',
            'aws_response': response
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/send-search', methods=['POST'])
def send_search_query_to_sqs():
    """Send a search query to the SearchQueue."""
    data = request.get_json()
    if not data or 'keywords' not in data:
        return jsonify({'error': 'Invalid JSON payload or missing "keywords"'}), 400

    try:
        # Generate a unique request ID for the search query
        request_id = str(uuid.uuid4())
        data['request_id'] = request_id

        # Send the search query to the SQS queue
        response = sqs.send_message(
            QueueUrl=search_queue_url,
            MessageBody=json.dumps(data)
        )
        return jsonify({
            'message': 'Search query sent to SQS!',
            'request_id': request_id,
            'aws_response': response
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-search-results', methods=['GET'])
def get_search_results():
    """Retrieve search results from the SearchQueue."""
    try:
        # Receive a message from the SQS queue
        response = sqs.receive_message(
            QueueUrl=search_queue_url,
            MaxNumberOfMessages=1,  # Retrieve one message at a time
            WaitTimeSeconds=5  # Long polling for up to 5 seconds
        )

        # Check if any messages were received
        messages = response.get('Messages', [])
        if not messages:
            return jsonify({'message': 'No search results available.'}), 200

        # Process the first message
        message = messages[0]
        receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])

        # Delete the message from the queue after processing
        sqs.delete_message(
            QueueUrl=search_queue_url,
            ReceiptHandle=receipt_handle
        )

        return jsonify({'results': body}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
