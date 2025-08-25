import logging
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import HtmlResponse

from items import PageItem

# Logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("crawler.log")
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
fh.setFormatter(formatter)
logger.addHandler(fh)


class SEOCrawler(scrapy.Spider):
    name = "seo_crawler"

    def __init__(self, start_url, depth_limit=5, js_rendering="False", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.js_rendering = js_rendering.lower() == "true"
        self.depth_limit = int(depth_limit)

        domain = urlparse(start_url).netloc
        self.allowed_domains = [domain]
        logger.info(
            "Initialized crawler with start URL: %s and allowed domain: %s",
            start_url, domain
        )

        if self.js_rendering:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized for JS rendering.")

    def parse(self, response):
        try:
            content_type = response.headers.get("Content-Type", b"").decode().lower()
            if not ("text/html" in content_type or "application/xhtml+xml" in content_type):
                logger.warning("Skipping non-HTML content: %s (Content-Type: %s)", response.url, content_type)
                return

            if self.js_rendering:
                self.driver.get(response.url)
                html = self.driver.page_source
                sel = scrapy.Selector(text=html)
            else:
                sel = response

            item = PageItem()
            item['url'] = response.url
            item['status_code'] = response.status
            item['title'] = sel.xpath("//title/text()").get(default="N/A").strip()
            item['meta_description'] = sel.xpath("//meta[@name='description']/@content").get(default="N/A").strip()
            item['canonical'] = sel.xpath("//link[@rel='canonical']/@href").get(default="N/A").strip()
            item['h1_tags'] = "; ".join(sel.xpath("//h1//text()").getall()).strip() or "N/A"
            item['h2_tags'] = "; ".join(sel.xpath("//h2//text()").getall()).strip() or "N/A"
            item['h3_tags'] = "; ".join(sel.xpath("//h3//text()").getall()).strip() or "N/A"
            item['image_alts'] = "; ".join(sel.xpath("//img[@alt]/@alt").getall()).strip() or "N/A"
            item['json_ld'] = "; ".join(sel.xpath("//script[@type='application/ld+json']/text()").getall()).strip() or "N/A"

            yield item

            current_depth = response.meta.get("depth", 0)
            if current_depth < self.depth_limit:
                parsed_start = urlparse(self.start_urls[0])
                for link in sel.css("a::attr(href)").getall():
                    full_url = urljoin(response.url, link)
                    parsed_link = urlparse(full_url)

                    if parsed_link.netloc == parsed_start.netloc:
                        yield response.follow(
                            full_url,
                            callback=self.parse,
                            errback=self.errback_handler,
                            meta={
                                "referrer": response.url,
                                "depth": current_depth + 1,
                            },
                        )

        except Exception as e:
            logger.error("Error parsing %s: %s", response.url, e)

    def errback_handler(self, failure):
        request = failure.request
        referrer = request.meta.get("referrer")
        logger.error(f"Broken link from {referrer}: {request.url} (Error: {failure.value})")
        # Here you could potentially yield an item for the broken link to be stored
        # For now, we just log it.

    def closed(self, reason):
        if self.js_rendering and hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("Selenium WebDriver closed.")
        logger.info(f"Crawler finished. Reason: {reason}")