import json
from indexing_utils import index_in_whoosh
from db_utils import store_in_rds, execute_query
from aws_utils import send_sqs_message
from whoosh.qparser import MultifieldParser, OrGroup



def process_message(message , last_indexed_url,ix):

    try:
        
        body = json.loads(message['Body'])
        required_fields = ["url", "title", "description", "keywords", "s3_key", "s3_bucket"]
        for field in required_fields:
            if field not in body or body[field] is None:
                raise ValueError(f"Missing required field: {field}")
            
        index_in_whoosh(body, ix)
            
        store_in_rds(body)
        last_indexed_url["value"] = body["url"]
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Failed to process message: {e}")
        
        
def process_search_request(message, ix, search_response_queue_url):
    try:

        body = json.loads(message['Body'])
        if 'keywords' not in body or 'request_id' not in body:
            raise ValueError("Missing required fields: 'keywords' and/or 'request_id'")

        keywords = body['keywords'].lower()
        request_id = body['request_id']

        sql = """
        SELECT url, title, description, keywords
        FROM indexed_data
        WHERE title LIKE %s OR description LIKE %s OR keywords LIKE %s
        """
        params = (f"%{keywords}%", f"%{keywords}%", f"%{keywords}%")
        results = execute_query(sql, params, fetch_results=True)



        response = {
            'request_id': request_id,
            'results': results
        }
        send_sqs_message(search_response_queue_url, response)
        print(f"Search results sent for request ID: {request_id}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Failed to process search request: {e}")
        