import threading
import os
from queue_polling import poll_result_queue, poll_search_queue
from heartbeat import start_heartbeat_thread
from whoosh.index import create_in, open_dir
from indexing_utils import schema

def main():
    last_indexed_url = [None]  
    running_status = 1  

    index_dir = "whoosh_index"

    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
        ix = create_in(index_dir, schema)
    else:
        ix = open_dir(index_dir)

    # Start the heartbeat thread
    start_heartbeat_thread(
        status_queue_url='https://sqs.us-east-1.amazonaws.com/608542499503/IndexerStatus',
        overall_status=1,
        running_status=running_status,
        last_indexed_url=last_indexed_url
    )

    # Start threads for polling queues
    thread1 = threading.Thread(target=poll_result_queue, args=('https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue', last_indexed_url, running_status,ix), daemon=True)
    thread2 = threading.Thread(target=poll_search_queue, args=('https://sqs.us-east-1.amazonaws.com/608542499503/SearchQueue', ix, 'https://sqs.us-east-1.amazonaws.com/608542499503/SearchResponseQueue', running_status), daemon=True)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

if __name__ == "__main__":
    main()