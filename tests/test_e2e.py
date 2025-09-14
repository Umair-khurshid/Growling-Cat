"""
End-to-end tests for the SEOCrawler spider.
"""
# pylint: disable=wrong-import-position,redefined-outer-name
import http.server
import os
import sys
import threading
from functools import partial

import pytest
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler import SEOCrawler
from items import PageItem

@pytest.fixture(scope="session")
def http_server():
    """
    Pytest fixture to start a local HTTP server in a background thread.
    The server serves files from the 'tests' directory.
    """
    # The server needs to run from the 'tests' directory to find sample.html
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Use partial to set the directory for the handler
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=test_dir)

    host = "localhost"
    port = 8000
    httpd = http.server.HTTPServer((host, port), handler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://{host}:{port}"

    httpd.shutdown()
    server_thread.join()

def test_e2e_crawl(http_server):
    """
    Run a full end-to-end crawl against a local server and verify the output.
    """
    scraped_items = []

    def item_scraped_handler(item, _response, _spider):
        """Signal handler to capture scraped items."""
        scraped_items.append(item)

    # Get default Scrapy settings
    settings = get_project_settings()
    # Disable any existing pipelines
    settings.set("ITEM_PIPELINES", {})

    process = CrawlerProcess(settings)

    # Connect the signal handler
    crawler = process.create_crawler(SEOCrawler)
    crawler.signals.connect(item_scraped_handler, signal=signals.item_scraped)

    # The URL for the crawler to start at
    start_url = f"{http_server}/sample.html"

    # Start the crawl
    process.crawl(crawler, start_url=start_url, depth_limit=0)
    process.start() # This call blocks until the crawl is finished

    # Assert that one item was scraped
    assert len(scraped_items) == 1

    # Assert the content of the scraped item
    item = scraped_items[0]
    assert isinstance(item, PageItem)
    assert item['title'] == "Sample Page Title"
    assert item['url'] == start_url
