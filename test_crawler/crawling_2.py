import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL of the website to crawl
base_url = "https://books.toscrape.com/"

# Set to store visited URLs
visited_urls = set()

# List to store URLs to visit next
urls_to_visit = [base_url]

# Function to crawl a page and extract links
def crawl_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract links and enqueue new URLs
        links = []
        for link in soup.find_all("a", href=True):
            next_url = urljoin(url, link["href"])
            links.append(next_url)

        return links

    except requests.exceptions.RequestException as e:
        print(f"Error crawling {url}: {e}")
        return []

# Crawl the website
while urls_to_visit:
    current_url = urls_to_visit.pop(0)  # Dequeue the first URL

    if current_url in visited_urls:
        continue

    print(f"Crawling: {current_url}")

    new_links = crawl_page(current_url)
    visited_urls.add(current_url)
    urls_to_visit.extend(new_links)

print("Crawling finished.")