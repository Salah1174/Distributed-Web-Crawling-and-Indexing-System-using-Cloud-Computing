import boto3
import json
import hashlib
import time

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse


class CrawlingSpider(CrawlSpider):

    name = "mycrawler"
    download_delay = 1  # polite crawling

    rules = (
        Rule(LinkExtractor(), callback="parse_item", follow=True),
    )

    def __init__(self, start_url=None, extra_domains=None, depth=1, max_pages=None, *args, **kwargs):
        super(CrawlingSpider, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("You must provide a start_url")

        if max_pages is None:
        	max_pages = 5  # Default value for max_pages
        self.max_pages = int(max_pages)

        if depth is None:
            raise ValueError("You must provide depth")

        self.start_urls = [start_url]
        self.depth = int(depth)
        self.page_count = 0

        # Initialize AWS clients
        self.s3 = boto3.client("s3", region_name="us-east-1")
        self.sqs = boto3.client("sqs", region_name="us-east-1")
        self.s3_bucket = "webcrawlerstorage"
        self.output_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue"

        # Define the crawler_master_queue URL
        self.crawler_master_queue_url = 'https://sqs.us-east-1.amazonaws.com/608542499503/Crawler-Master-Queue'

        parsed_url = urlparse(start_url)
        base_domain = parsed_url.netloc.replace("www.", "")

        if extra_domains:
            additional = [d.strip() for d in extra_domains.split(",")]
            self.allowed_domains = [base_domain] + additional
        else:
            self.allowed_domains = [base_domain]

    def parse_item(self, response):
        if self.page_count >= 1:
            self.crawler.engine.close_spider(self, reason="max_pages limit reached")
            return

        current_depth = response.meta.get("depth", 0)
        self.logger.info(f"Page {self.page_count + 1}/{self.max_pages} | Depth {current_depth} | URL: {response.url}")
        self.page_count += 1

        if current_depth < self.depth:
            for link in response.css("a::attr(href)").getall():
                yield response.follow(link, self.parse_item, meta={"depth": current_depth + 1})

	# Collect discovered URLs and send only up to max_pages to the master node
        discovered_urls = []
        for link in response.css("a::attr(href)").getall():
            absolute_url = response.urljoin(link)
            if absolute_url != self.start_urls[0]:  # Exclude the seed URL
                discovered_urls.append(absolute_url)

        # Limit the number of URLs sent to the master node
        for url in discovered_urls[:self.max_pages]:
            try:
                self.sqs.send_message(
                    QueueUrl=self.crawler_master_queue_url,
                    MessageBody=json.dumps({"url": url})
                )
                self.logger.info(f"Sent discovered URL to MasterNode: {url}")
            except Exception as e:
                self.logger.error(f"Failed to send discovered URL to MasterNode: {e}")

        # Extract page data
        title = response.xpath('//title/text()').get()
        description = response.xpath('//meta[@name="description"]/@content').get()
        keywords = response.xpath('//meta[@name="keywords"]/@content').get()

        yielded_data = {
            "url": response.url,
            "title": title,
            "keywords": keywords,
            "description": description,
            "html_snippet": response.text[:500]
        }
        self.logger.info(f"Yielded data: {yielded_data}")
        yield yielded_data

        # Generate S3 key and upload HTML
        timestamp = int(time.time())
        hash_id = hashlib.md5(response.url.encode()).hexdigest()
        s3_key = f"{hash_id}_{timestamp}.html"

        try:
            self.s3.put_object(Bucket=self.s3_bucket, Key=s3_key, Body=response.text)
        except Exception as e:
            self.logger.error(f"Failed to upload to S3: {e}")
            return

        # Send message to output SQS with S3 reference
        try:
            self.sqs.send_message(
                QueueUrl=self.output_queue_url,
                MessageBody=json.dumps({
                    "url": response.url,
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "s3_key": s3_key,
                    "s3_bucket": self.s3_bucket
                })
            )
        except Exception as e:
            self.logger.error(f"Failed to send message to SQS: {e}")