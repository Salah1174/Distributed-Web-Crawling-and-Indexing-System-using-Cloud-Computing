from mpi4py import MPI
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Set up logging to both console and file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - Crawler - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        logging.FileHandler(
                            'crawled_urls.log', mode='a')  # Log to file
                    ])


def extract_links_and_text(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
        links = [urljoin(base_url, a.get('href'))
                 for a in soup.find_all('a', href=True)]
        text = soup.get_text(separator=' ', strip=True)

        return links, text
    except Exception as e:
        logging.error(f"Error crawling {url}: {e}")
        return [], ""


def crawler_process():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    logging.info(f"Crawler node started with rank {rank} of {size}")

    crawled_count = 0  # Counter to track the number of crawled URLs
    max_urls = 10  # Maximum number of URLs to crawl

    while crawled_count < max_urls:
        status = MPI.Status()
        url_to_crawl = comm.recv(source=0, tag=0, status=status)

        if not url_to_crawl:
            logging.info(f"Crawler {rank} received shutdown signal. Exiting.")
            break

        logging.info(f"Crawler {rank} received URL: {url_to_crawl}")

        extracted_urls, content = extract_links_and_text(url_to_crawl)

        # Log the crawled URL to the file
        with open('crawled_urls.log', 'a') as log_file:
            log_file.write(f"Crawler {rank} - Crawled URL: {url_to_crawl}\n")

        comm.send(extracted_urls, dest=0, tag=1)
        comm.send(content, dest=size - 1, tag=2)  # Send content to indexer
        comm.send(
            f"Crawler {rank} - Crawled URL: {url_to_crawl}", dest=0, tag=99)

        crawled_count += 1  # Increment the counter after each crawl

    logging.info(
        f"Crawler {rank} has reached the maximum crawl limit ({max_urls}) and is exiting.")


if __name__ == '__main__':
    crawler_process()
