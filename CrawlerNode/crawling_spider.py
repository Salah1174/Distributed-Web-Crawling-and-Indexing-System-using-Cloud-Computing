
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
            raise ValueError("You must provide max_pages")
        if depth is None:
            raise ValueError("You must provide depth")

        self.start_urls = [start_url]
        self.depth = int(depth)
        self.max_pages = int(max_pages)
        self.page_count = 0

        # Initialize AWS clients
        self.s3 = boto3.client("s3", region_name="us-east-1")
        self.sqs = boto3.client("sqs", region_name="us-east-1")
        self.s3_bucket = "webcrawlerstorage"
        self.output_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue"

        parsed_url = urlparse(start_url)
        base_domain = parsed_url.netloc.replace("www.", "")
        if extra_domains:
            additional = [d.strip() for d in extra_domains.split(",")]
            self.allowed_domains = [base_domain] + additional
        else:
            self.allowed_domains = [base_domain]
    def parse_item(self, response):
        if self.page_count >= self.max_pages:
            self.crawler.engine.close_spider(self, reason="max_pages limit reached")
            return

        current_depth = response.meta.get("depth", 0)
        self.logger.info(f"Page {self.page_count + 1}/{self.max_pages} | Depth {current_depth} | URL: {response.url}")
        self.page_count += 1

        if current_depth < self.depth:
            for link in response.css("a::attr(href)").getall():
                yield response.follow(link, self.parse_item, meta={"depth": current_depth + 1})

        # Extract page data
        title = response.xpath('//title/text()').get()
        description = response.xpath('//meta[@name="description"]/@content').get()
        keywords = response.xpath('//meta[@name="keywords"]/@content').get()

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


