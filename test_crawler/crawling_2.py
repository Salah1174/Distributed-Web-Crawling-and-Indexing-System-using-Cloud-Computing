# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin

# # URL of the website to crawl
# base_url = "https://books.toscrape.com/"

# # Set to store visited URLs
# visited_urls = set()

# # List to store URLs to visit next
# urls_to_visit = [base_url]

# # Function to crawl a page and extract links
# def crawl_page(url):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for HTTP errors

#         soup = BeautifulSoup(response.content, "html.parser")

#         # Extract links and enqueue new URLs
#         links = []
#         for link in soup.find_all("a", href=True):
#             next_url = urljoin(url, link["href"])
#             links.append(next_url)

#         return links

#     except requests.exceptions.RequestException as e:
#         print(f"Error crawling {url}: {e}")
#         return []

# # Crawl the website
# while urls_to_visit:
#     current_url = urls_to_visit.pop(0)  # Dequeue the first URL

#     if current_url in visited_urls:
#         continue

#     print(f"Crawling: {current_url}")

#     new_links = crawl_page(current_url)
#     visited_urls.add(current_url)
#     urls_to_visit.extend(new_links)

# print("Crawling finished.")


import os
import json
import requests
from bs4 import BeautifulSoup

url = 'https://en.wikipedia.org/wiki/Main_Page'  # Replace with the website you want to crawl
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully fetched the webpage!")
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

# Parse the content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Print the parsed content
print(soup.prettify())  # To view the page structure

# Extract all links (anchor tags)
links = soup.find_all('a')

# Print all the links
for link in links:
    print(link.get('href'))

def save_page_to_json(url, content):
    # Create a directory to store JSON files if it doesn't exist
    os.makedirs("crawled_pages", exist_ok=True)

    # Generate a valid filename from the URL
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".json"
    filepath = os.path.join("crawled_pages", filename)

    # Save the content to a JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

# Function to crawl a webpage
def crawl(url, depth=2):
    if depth == 0:
        return  # Limit crawling depth to avoid infinite loops

    print(f"Crawling URL: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Save the current page content to a JSON file
    page_content = {
        "url": url,
        "html": soup.prettify(),
    }
    save_page_to_json(url, page_content)

    # Extract links from the current page
    links = soup.find_all('a', href=True)

    # Recursively crawl the linked pages
    for link in links:
        next_url = link.get('href')
        # Ensure the link is an absolute URL
        if not next_url.startswith('http'):
            next_url = url + next_url  # Handle relative links

        # Recurse to crawl further pages
        crawl(next_url, depth - 1)

# Start crawling from the homepage
crawl('https://en.wikipedia.org/wiki/Main_Page', depth=2)