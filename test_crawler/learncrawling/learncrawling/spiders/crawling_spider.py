from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse

class CrawlingSpider(CrawlSpider):
    name = "mycrawler"

    def __init__(self, depth=1, *args, **kwargs):
        super(CrawlingSpider, self).__init__(*args, **kwargs)
        self.depth = int(depth)  # Convert depth to an integer

    download_delay = 1  # polite crawling

    rules = (
        Rule(LinkExtractor(allow="catalogue", deny="category"), callback="parse_item", follow=True),
    )

    def __init__(self, start_url=None, extra_domains=None, depth=1, *args, **kwargs):
        super(CrawlingSpider, self).__init__(*args, **kwargs)
        self.depth = int(depth)  # Convert depth to an integer

        if not start_url:
            raise ValueError("You must provide a start_url")

        self.start_urls = [start_url]
        # Extract domain from the start_url
        parsed_url = urlparse(start_url)
        base_domain = parsed_url.netloc.replace("www.", "")
        # Combine with optional extra domains
        if extra_domains:
            additional = [d.strip() for d in extra_domains.split(",")]
            self.allowed_domains = [base_domain] + additional
        else:
            self.allowed_domains = [base_domain]

    def parse_item(self, response):
        current_depth = response.meta.get("depth", 0)
        self.logger.info(f"Current depth: {current_depth} | URL: {response.url}")
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