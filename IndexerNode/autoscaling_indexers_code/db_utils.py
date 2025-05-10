import time
import pymysql
import os


db_config = {
    "host": "index-db.cyv2uaoamjlb.us-east-1.rds.amazonaws.com",  
    "user": "admin",                   
    "database": "new_schema",          
    "region": "us-east-1"                     
}


def get_rds_connection():
    """establish rds connection."""
    password = os.getenv("RDS_PASSWORD")  
    if not password:
        raise ValueError("RDS_PASSWORD environment variable is not set")

    # connect to RDS
    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=password,
        database=db_config["database"]
    )
    return connection

def execute_query(query, params=None, fetch_results=False):
    connection = None
    try:
        connection = get_rds_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor if fetch_results else None)

     
        cursor.execute(query, params)


        if fetch_results:
            return cursor.fetchall()

      
        connection.commit()
    except Exception as e:
        print(f"Database operation failed: {e}")
        raise
    finally:
        if connection:
            connection.close()

def store_in_rds(data, max_retries=3, retry_delay=5):

    retries = 0
    while retries < max_retries:
        try:
            
            #store in rds
            sql = """
            INSERT INTO indexed_data (url, title, description, keywords, s3_key, s3_bucket)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                data["url"],
                data.get("title"),
                data.get("description"),
                data.get("keywords"),
                data.get("s3_key"),
                data.get("s3_bucket")
            )
            execute_query(sql, params)
            
            
            print(f"Stored data for URL: {data['url']} in RDS.")
            break
            
        except Exception as e:
            print(f"Failed to index data in Whoosh: {e}")
            retries += 1
           
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Max retries reached. Failed to store data for URL: {data['url']}")
                raise 