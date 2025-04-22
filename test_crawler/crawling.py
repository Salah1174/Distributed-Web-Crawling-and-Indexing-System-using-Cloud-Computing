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

    # Extract links from the current page
    links = soup.find_all('a', href=True)

    # Print links on the page
    for link in links:
        print(link.get('href'))

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