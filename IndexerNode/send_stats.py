import socket
import threading
import psutil   
import time
from aws_utils import send_sqs_message

def get_instance_info(instance_id):
    try:
        public_ip = socket.gethostbyname(socket.gethostname())
        instance_info = {
            "instanceId": str(instance_id),  
            "cpuUsage": psutil.cpu_percent(interval=1),  
            "memoryUsage": psutil.virtual_memory().percent,  
            "storageUsage": psutil.disk_usage('/').percent, 
            "publicIp": public_ip, 
            "status": "Healthy" if psutil.cpu_percent(interval=1) < 80 else "Warning"  
        }
        return instance_info
    except Exception as e:
        print(f"Error fetching instance info: {e}")
        return None
    
    
def get_indexed_urls_count(ix):
    try:
        with ix.searcher() as searcher:
            indexed_count = searcher.doc_count()  
        return indexed_count
    except Exception as e:
        print(f"Error fetching indexed URLs count: {e}")
        return 0
    
    
def send_stats_to_client_backend(stats_queue_url, ix, instance_id):
    try:
        instance_info = get_instance_info(instance_id)
        if instance_info is None:
            return
        indexed_count = get_indexed_urls_count(ix)



        payload = {
            "instanceInfo": instance_info,
            "indexedCount": indexed_count
        }

        print(f"Sending stats: {payload}")
        
        try:
            send_sqs_message(stats_queue_url, payload)
        except Exception as e:
            print(f"Error sending stats to SQS: {e}")
            return
        print("Stats sent successfully to Client Backend.")
        
        
    except Exception as e:
        print(f"Error sending stats to Client Backend: {e}")
        
def start_stats_thread(stats_queue_url, ix, instance_id):
    def send_stats_periodically():
        while True:
            send_stats_to_client_backend(stats_queue_url, ix, instance_id)
            time.sleep(60)  

    stats_thread = threading.Thread(target=send_stats_periodically, daemon=True)
    stats_thread.start()