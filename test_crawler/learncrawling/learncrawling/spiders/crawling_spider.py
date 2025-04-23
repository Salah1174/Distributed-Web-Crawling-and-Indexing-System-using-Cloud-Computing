
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

        self.start_urls = [start_url]
        self.depth = int(depth)
        self.max_pages = int(max_pages)
        self.page_count = 0

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

        title = response.xpath('//title/text()').get()
        description = response.xpath('//meta[@name="description"]/@content').get()
        keywords = response.xpath('//meta[@name="keywords"]/@content').get()
        yield {
            "url": response.url,
            "title": title,
            "description": description,
            "keywords": keywords,
            "html_snippet": response.text[:500]
        }

