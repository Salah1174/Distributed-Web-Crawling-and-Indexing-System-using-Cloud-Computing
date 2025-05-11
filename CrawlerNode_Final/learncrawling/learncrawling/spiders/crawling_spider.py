import boto3
import json
import time
import hashlib
from urllib.parse import urlparse

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CrawlingSpider(CrawlSpider):
    name = "mycrawler"
    download_delay = 1

    rules = (
        Rule(LinkExtractor(), callback="parse_item", follow=True),
    )

    def __init__(self, start_url=None, extra_domains=None, depth=1, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("You must provide a start_url")

        self.start_urls = [start_url]
        self.depth = int(depth)
        self.max_pages = int(max_pages)
        self.page_count = 0

        # AWS setup
        self.s3 = boto3.client("s3", region_name="us-east-1")
        self.sqs = boto3.client("sqs", region_name="us-east-1")
        self.s3_bucket = "webcrawlerstorage"
        self.output_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/ResultQueue"
        self.crawler_master_queue_url = "https://sqs.us-east-1.amazonaws.com/608542499503/Crawler-Master-Queue"

        # Domain restriction
        parsed_url = urlparse(start_url)
        base_domain = parsed_url.netloc.replace("www.", "")
        if extra_domains:
            additional = [d.strip() for d in extra_domains.split(",")]
            self.allowed_domains = [base_domain] + additional
        else:
            self.allowed_domains = [base_domain]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        return super().from_crawler(crawler, *args, **kwargs)

    def parse_item(self, response):
        if self.page_count >= self.max_pages:
            self.logger.info("Reached max_pages limit. Closing spider.")
            self.crawler.engine.close_spider(
                self, reason="max_pages limit reached")
            return

        current_depth = response.meta.get("depth", 0)
        self.logger.info(
            f"Page {self.page_count + 1}/{self.max_pages} | Depth {current_depth} | URL: {response.url}")
        self.page_count += 1

        # Follow links if depth allows
        if current_depth < self.depth:
            for link in response.css("a::attr(href)").getall():
                yield response.follow(link, self.parse_item, meta={"depth": current_depth + 1})

        # Collect discovered URLs
        discovered_urls = [
            response.urljoin(link)
            for link in response.css("a::attr(href)").getall()
            if response.urljoin(link) != self.start_urls[0]
        ]

        for url in discovered_urls[:self.max_pages]:
            try:
                self.sqs.send_message(
                    QueueUrl=self.crawler_master_queue_url,
                    MessageBody=json.dumps(
                        {"url": url, "start_url": self.start_urls[0]})
                )
                self.logger.info(f"Sent discovered URL to MasterNode: {url}")
            except Exception as e:
                self.logger.error(
                    f"Failed to send discovered URL to MasterNode: {e}")

        # Extract metadata
        title = response.xpath('//title/text()').get()
        description = response.xpath(
            '//meta[@name="description"]/@content').get()
        keywords = response.xpath('//meta[@name="keywords"]/@content').get()

        if not keywords:
            content_text = response.xpath(
                '//article//text() | //main//text() | //div[@class="content"]//text()').getall()
            if not content_text:
                content_text = response.xpath('//p//text()').getall()
            if not content_text:
                content_text = response.xpath('//body//text()').getall()

            cleaned_text = [' '.join(text.strip().split())
                            for text in content_text if text and len(text.strip()) > 3]
            keywords = ', '.join(list(dict.fromkeys(cleaned_text))[
                                 :20]) if cleaned_text else "No meaningful keywords found"

        yielded_data = {
            "url": response.url,
            "title": title,
            "keywords": keywords,
            "description": description,
            "html_snippet": response.text[:500]
        }
        self.logger.info(f"Yielded data: {yielded_data}")
        yield yielded_data

        # Uncomment below if S3 upload and ResultQueue messaging is needed
        timestamp = int(time.time())
        hash_id = hashlib.md5(response.url.encode()).hexdigest()
        s3_key = f"{hash_id}_{timestamp}.html"

        try:
            self.s3.put_object(Bucket=self.s3_bucket,
                               Key=s3_key, Body=response.text)
        except Exception as e:
            self.logger.error(f"Failed to upload to S3: {e}")
            return

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
            self.logger.info("**SUCCESS: SENT TO RESULTQUEUE")
        except Exception as e:
            self.logger.error(f"Failed to send message to SQS: {e}")
