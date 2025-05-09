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

        with ix.searcher() as searcher:
            # query = QueryParser("keywords", ix.schema).parse(f'"{keywords}"')
            parser = MultifieldParser(["title^3", "description", "keywords^2"],  # boost "title" field
                                        ix.schema,
                                        group=OrGroup
                                     )
            # query = Term("keywords", keywords)
            query = parser.parse(keywords)
            print(f"Search query: {query}")
            results = searcher.search(query, limit=10)  # limit to top 10 results

            urls = [result["url"] for result in results]
            print(f"Search results for keywords '{keywords}': {urls}")
            
            # for result in results:
            #     print(f"URL: {result['url']},Score: {result.score} Title: {result['title']}, Description: {result['description']}, Keywords: {result['keywords']}")

        # Fetch full data from RDS
        if urls:
            placeholders = ', '.join(['%s'] * len(urls))
            sql = f"""
            SELECT url, title, description, keywords
            FROM indexed_data
            WHERE url IN ({placeholders})
            """
            print(f"executing SQL: {sql} with params: {urls}")
            whoosh_results = execute_query(sql, urls, fetch_results=True)
        else:
            whoosh_results = []

        sql = """
        SELECT url, title, description, keywords
        FROM indexed_data
        WHERE title LIKE %s OR description LIKE %s OR keywords LIKE %s
        """
        params = (f"%{keywords}%", f"%{keywords}%", f"%{keywords}%")
        print(f"Executing SQL for additional results: {sql} with params: {params}")
        additional_sql_results = execute_query(sql, params, fetch_results=True)

        all_results = {result['url']: result for result in whoosh_results}
        for result in additional_sql_results:
            if result['url'] not in all_results:
                all_results[result['url']] = result
         
        response = {
            'request_id': request_id,
            'results': list(all_results.values())
        }
        send_sqs_message(search_response_queue_url, response)
        print(f"Search results sent for request ID: {request_id}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Failed to process search request: {e}")
        