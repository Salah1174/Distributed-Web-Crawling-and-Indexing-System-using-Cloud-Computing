from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
def parse_item(self,response):

        yield {
            "title":response.css(".product_main h1::text").get(),
            "price":response.css(".price_color::text").get(),
            "availability":response.css(".availability::text")[1].get().strip()
        }
class CrawlingSpider(CrawlSpider):
    name = "mycrawler"
    allowed_domains = ["toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]
    PROXY_SERVER = "http://scrapingdog:Your-API-Key@proxy.scrapingdog.com:8081"
    
    download_delay = 1  # Set the delay to 1 second

    def parse_item(self,response):
        yield {
            "title":response.css(".product_main h1::text").get(),
            "price":response.css(".price_color::text").get(),
            "availability":response.css(".availability::text")[1].get().strip()
        }
        
    rules = (
       Rule(LinkExtractor(allow="catalogue", deny="category"), callback="parse_item"),
    )
    
