"""SEOCrawler spider for crawling websites and extracting SEO data."""

import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Response
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from twisted.python.failure import Failure

from items import PageItem

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    fh = logging.FileHandler("crawler.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)


class SEOCrawler(scrapy.Spider):
    """A Scrapy spider that crawls a website and extracts SEO-related data from each page."""

    name: str = "seo_crawler"

    def __init__(
        self,
        *args: Any,
        start_url: str,
        depth_limit: int = 5,
        js_rendering: str = "False",
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.js_rendering = js_rendering.lower() == "true"
        self.depth_limit = depth_limit
        self.broken_links: dict[str, list[str]] = {}

        domain = urlparse(start_url).netloc.split(":")[0]
        self.allowed_domains = [domain]
        logger.info(
            "Initialized crawler with start URL: %s and allowed domain: %s",
            start_url,
            domain,
        )

        self.driver: webdriver.Chrome | None = None
        if self.js_rendering:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized for JS rendering.")

    def parse(self, response: Response, **_kwargs: Any) -> Any:
        """Parse the response, extract SEO data, and follow internal links."""
        try:
            content_type = (
                (response.headers.get("Content-Type") or b"").decode().lower()
            )
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                logger.warning(
                    "Skipping non-HTML content: %s (Content-Type: %s)",
                    response.url,
                    content_type,
                )
                return

            if self.js_rendering and self.driver:
                self.driver.get(response.url)
                html = self.driver.page_source
                sel: Selector | Response = scrapy.Selector(text=html)
            else:
                sel = response

            item = PageItem()
            item["url"] = response.url
            item["status_code"] = response.status
            item["title"] = sel.xpath("//title/text()").get(default="N/A").strip()
            item["meta_description"] = (
                sel.xpath("//meta[@name='description']/@content").get(default="N/A").strip()
            )
            item["canonical"] = (
                sel.xpath("//link[@rel='canonical']/@href").get(default="N/A").strip()
            )
            item["h1_tags"] = (
                "; ".join(sel.xpath("//h1//text()").getall()).strip() or "N/A"
            )
            item["h2_tags"] = (
                "; ".join(sel.xpath("//h2//text()").getall()).strip() or "N/A"
            )
            item["h3_tags"] = (
                "; ".join(sel.xpath("//h3//text()").getall()).strip() or "N/A"
            )
            item["image_alts"] = (
                "; ".join(sel.xpath("//img[@alt]/@alt").getall()).strip() or "N/A"
            )
            item["json_ld"] = (
                "; ".join(
                    sel.xpath("//script[@type='application/ld+json']/text()").getall()
                ).strip()
                or "N/A"
            )
            item["broken_links"] = (
                "; ".join(self.broken_links.get(response.url, [])) or "N/A"
            )

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

        except (AttributeError, TypeError) as e:
            logger.error("Error parsing %s: %s", response.url, e)
            raise
        except Exception as e:
            logger.error("Error parsing %s: %s", response.url, e)

    def errback_handler(self, failure: Failure) -> None:
        """Handle request errors and track broken links per page."""
        request = failure.request  # type: ignore[attr-defined]
        referrer = request.meta.get("referrer")
        if referrer:
            self.broken_links.setdefault(referrer, []).append(
                f"{request.url} ({failure.value})"
            )
        logger.error(
            "Broken link from %s: %s (Error: %s)", referrer, request.url, failure.value
        )

    def closed(self, _reason: str) -> None:
        """Called when the spider is closed. Clean up resources."""
        if self.js_rendering and self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed.")
        logger.info("Crawler finished. Reason: %s", _reason)
