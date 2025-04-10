from mpi4py import MPI
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - Master - %(levelname)s - %(message)s')


def master_process():
    """
    Main process for the master node.
    Handles task distribution, worker management, and coordination.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    status = MPI.Status()

    logging.info(f"Master node started with rank {rank} of {size}")

    # Initialize task queue, database connections, etc.
    crawler_nodes = size - 2  # Assuming master and at least one indexer node
    indexer_nodes = 1         # At least one indexer node

    if crawler_nodes <= 0 or indexer_nodes <= 0:
        logging.error(
            "Not enough nodes to run crawler and indexer. Need at least 3 nodes (1 master, 1 crawler, 1 indexer)")
        return

    # Ranks for crawler nodes
    active_crawler_nodes = list(range(1, 1 + crawler_nodes))
    # Ranks for indexer nodes
    active_indexer_nodes = list(range(1 + crawler_nodes, size))

    logging.info(f"Active Crawler Nodes: {active_crawler_nodes}")
    logging.info(f"Active Indexer Nodes: {active_indexer_nodes}")

    # Example seed URL
    seed_urls = ["https://books.toscrape.com/"]
    # Initial crawl queue
    urls_to_crawl_queue = seed_urls
    task_count = 0
    crawler_tasks_assigned = 0

    # Main loop: assign tasks, handle results
    while urls_to_crawl_queue or crawler_tasks_assigned > 0:
        # Check for completed crawler tasks and results
        if crawler_tasks_assigned > 0:
            if comm.iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status):  # Non-blocking check
                message_source = status.Get_source()
                message_tag = status.Get_tag()
                message_data = comm.recv(
                    source=message_source, tag=message_tag)

                if message_tag == 1:  # URLs returned from crawler
                    crawler_tasks_assigned -= 1
                    new_urls = message_data
                    if new_urls:
                        urls_to_crawl_queue.extend(new_urls)
                    logging.info(f"Master received URLs from Crawler {message_source}, "
                                 f"URLs in queue: {len(urls_to_crawl_queue)}, Tasks assigned: {crawler_tasks_assigned}")
                elif message_tag == 99:  # Heartbeat
                    logging.info(
                        f"Crawler {message_source} status: {message_data}")
                elif message_tag == 999:  # Error reported
                    logging.error(
                        f"Crawler {message_source} reported error: {message_data}")
                    crawler_tasks_assigned -= 1  # Consider re-assigning failed task

        # Assign new crawling tasks
        while urls_to_crawl_queue and crawler_tasks_assigned < crawler_nodes:
            url_to_crawl = urls_to_crawl_queue.pop(0)  # FIFO for simplicity
            available_crawler_rank = active_crawler_nodes[crawler_tasks_assigned % len(
                active_crawler_nodes)]  # Round-robin assignment
            task_id = task_count
            task_count += 1

            comm.send(url_to_crawl, dest=available_crawler_rank,
                      tag=0)  # Tag 0 for new task
            crawler_tasks_assigned += 1
            logging.info(f"Master assigned task {task_id} (crawl {url_to_crawl}) to Crawler {available_crawler_rank}, "
                         f"Tasks assigned: {crawler_tasks_assigned}")
            time.sleep(0.1)  # Prevent overwhelming in tight loop

        time.sleep(1)  # Master sleep interval

    logging.info(
        "Master node finished URL distribution. Waiting for crawlers to complete...")
    print("Master Node Finished.")


if __name__ == '__main__':
    master_process()
