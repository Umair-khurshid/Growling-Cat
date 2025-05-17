import logging
from urllib.parse import urljoin, urlparse

import pandas as pd
import scrapy
from scrapy.http import HtmlResponse  # For Selenium integration

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
        self.results = []
        self.broken_links_by_referrer = {}
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

            title = sel.xpath("//title/text()").get()
            meta_desc = sel.xpath("//meta[@name='description']/@content").get()
            canonical = sel.xpath("//link[@rel='canonical']/@href").get()

            h1_tags = sel.xpath("//h1//text()").getall()
            h2_tags = sel.xpath("//h2//text()").getall()
            h3_tags = sel.xpath("//h3//text()").getall()
            image_alts = sel.xpath("//img[@alt]/@alt").getall()
            json_ld_scripts = sel.xpath(
                "//script[@type='application/ld+json']/text()"
            ).getall()

            result = {
                "URL": response.url,
                "Title": title.strip() if title else "N/A",
                "Meta Description": meta_desc.strip() if meta_desc else "N/A",
                "Canonical": canonical.strip() if canonical else "N/A",
                "H1 Tags": "; ".join(h1_tags) if h1_tags else "N/A",
                "H2 Tags": "; ".join(h2_tags) if h2_tags else "N/A",
                "H3 Tags": "; ".join(h3_tags) if h3_tags else "N/A",
                "Image Alts": "; ".join(image_alts) if image_alts else "N/A",
                "JSON-LD": "; ".join(json_ld_scripts) if json_ld_scripts else "N/A",
                "Broken Links": "N/A",
            }

            self.results.append(result)
            logger.info("Parsed URL: %s", response.url)

            parsed_start = urlparse(self.start_urls[0])
            for link in sel.css("a::attr(href)").getall():
                full_url = urljoin(response.url, link)
                parsed_link = urlparse(full_url)

                if parsed_link.netloc == parsed_start.netloc:
                    logger.debug(
                        "Following internal link: %s from %s", full_url, response.url
                    )
                    yield response.follow(
                        full_url,
                        callback=self.parse,
                        errback=self.errback_handler,
                        meta={
                            "referrer": response.url,
                            "depth": response.meta.get("depth", 0) + 1,
                        },
                    )
                else:
                    logger.debug("Skipping external link: %s", full_url)

        except Exception as e:
            logger.error("Error parsing %s: %s", response.url, e)

    def errback_handler(self, failure):
        request = failure.request
        referrer = request.meta.get("referrer")
        error_msg = repr(failure.value)
        broken_info = f"{request.url} (Error: {error_msg})"

        if referrer:
            if referrer in self.broken_links_by_referrer:
                self.broken_links_by_referrer[referrer].append(broken_info)
            else:
                self.broken_links_by_referrer[referrer] = [broken_info]

        logger.error(
            "Broken link from %s: %s | Error: %s",
            referrer, request.url, error_msg
        )

    def closed(self, reason):
        try:
            if self.js_rendering:
                self.driver.quit()
                logger.info("Selenium WebDriver closed.")

            for result in self.results:
                url = result.get("URL")
                broken_links = self.broken_links_by_referrer.get(url, [])
                result["Broken Links"] = "; ".join(broken_links) if broken_links else "N/A"

            if self.results:
                df = pd.DataFrame(self.results)
                df.to_csv("output.csv", index=False)
                logger.info("Crawling finished. Results saved to output.csv")
            else:
                logger.warning("No data collected. output.csv not written.")

        except Exception as e:
            logger.error("Error closing crawler: %s", e)
