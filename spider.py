import scrapy
import pandas as pd
import logging
from urllib.parse import urljoin, urlparse

# For Selenium integration
from scrapy.http import HtmlResponse

# Logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("crawler.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class SEOCrawler(scrapy.Spider):
    name = "seo_crawler"
    
    def __init__(self, start_url, depth_limit=5, js_rendering="False", *args, **kwargs):
        super(SEOCrawler, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.results = []
        self.broken_links_by_referrer = {}
        self.js_rendering = (js_rendering.lower() == "true")
        self.depth_limit = int(depth_limit)

        # Extract and set allowed domain
        domain = urlparse(start_url).netloc
        self.allowed_domains = [domain]
        logger.info(f"Initialized crawler with start URL: {start_url} and allowed domain: {domain}")

        # If JS rendering is enabled, initialize Selenium WebDriver.
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
            # If JS rendering is enabled, override response by fetching via Selenium.
            if self.js_rendering:
                self.driver.get(response.url)
                html = self.driver.page_source
                sel = scrapy.Selector(text=html)
            else:
                sel = response

            # Extract SEO elements
            title = sel.xpath('//title/text()').get()
            meta_desc = sel.xpath('//meta[@name="description"]/@content').get()
            canonical = sel.xpath('//link[@rel="canonical"]/@href').get()

            # Extract headers
            h1_tags = sel.xpath('//h1//text()').getall()
            h2_tags = sel.xpath('//h2//text()').getall()

            # Extract image alt texts
            image_alts = sel.xpath('//img[@alt]/@alt').getall()

            # Extract structured data (JSON-LD)
            json_ld_scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()

            result = {
                "URL": response.url,
                "Title": title.strip() if title else "N/A",
                "Meta Description": meta_desc.strip() if meta_desc else "N/A",
                "Canonical": canonical.strip() if canonical else "N/A",
                "H1 Tags": "; ".join(h1_tags) if h1_tags else "N/A",
                "H2 Tags": "; ".join(h2_tags) if h2_tags else "N/A",
                "Image Alts": "; ".join(image_alts) if image_alts else "N/A",
                "JSON-LD": "; ".join(json_ld_scripts) if json_ld_scripts else "N/A",
                "Broken Links": "N/A"
            }
            self.results.append(result)
            logger.info(f"Parsed URL: {response.url}")

            # Ensure proper internal link handling
            parsed_start = urlparse(self.start_urls[0])

            for link in sel.css('a::attr(href)').getall():
                full_url = urljoin(response.url, link)  # Convert relative URLs to absolute
                parsed_link = urlparse(full_url)

                if parsed_link.netloc == parsed_start.netloc:  # Ensure it's within the same domain
                    logger.debug(f"Following internal link: {full_url} from {response.url}")
                    yield response.follow(
                        full_url,
                        callback=self.parse,
                        errback=self.errback_handler,
                        meta={'referrer': response.url, 'depth': response.meta.get('depth', 0) + 1}
                    )
                else:
                    logger.debug(f"Skipping external link: {full_url}")
        except Exception as e:
            logger.error(f"Error parsing {response.url}: {e}")

    def errback_handler(self, failure):
        request = failure.request
        referrer = request.meta.get('referrer')
        error_msg = repr(failure.value)
        broken_info = f"{request.url} (Error: {error_msg})"
        
        if referrer:
            if referrer in self.broken_links_by_referrer:
                self.broken_links_by_referrer[referrer].append(broken_info)
            else:
                self.broken_links_by_referrer[referrer] = [broken_info]
        
        logger.error(f"Broken link from {referrer}: {request.url} | Error: {error_msg}")

    def closed(self, reason):
        try:
            # If JS rendering was enabled, quit the Selenium driver.
            if self.js_rendering:
                self.driver.quit()
                logger.info("Selenium WebDriver closed.")

            # Integrate broken links into each result entry.
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
            logger.error(f"Error closing crawler: {e}")
