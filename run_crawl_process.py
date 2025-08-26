import sys
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler import SEOCrawler

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_single_crawl(start_url, depth, delay, concurrency, js_rendering):
    """
    Configures and runs a single Scrapy crawl process.
    This function is designed to be called from a separate process.
    """
    try:
        # Consolidated Scrapy settings
        settings = {
            'DEPTH_LIMIT': depth,
            'DOWNLOAD_DELAY': delay,
            'CONCURRENT_REQUESTS': concurrency,
            'ITEM_PIPELINES': {
                'pipelines.SqlitePipeline': 300,
            },
            'LOG_LEVEL': 'INFO',
            "DOWNLOAD_TIMEOUT": 40,
            "RETRY_ENABLED": True,
            "RETRY_TIMES": 8,
            "RETRY_HTTP_CODES": [522, 500, 502, 503, 504, 408],
            "ROBOTSTXT_OBEY": False,
            "DOWNLOADER_MIDDLEWARES": {
                "middlewares.RotatingUserAgentMiddleware": 543,
            },
            "EXTENSIONS": {
                "extensions.ProgressExtension": 500,
            },
        }

        process = CrawlerProcess(settings)
        process.crawl(
            SEOCrawler,
            start_url=start_url,
            js_rendering=js_rendering
        )
        # The script will block here until the crawling is finished
        process.start()
        logger.info("Crawl process finished successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the crawl process: {e}")
        sys.exit(1) # Exit with an error code if something goes wrong

if __name__ == "__main__":
    # This block is executed when the script is run directly
    if len(sys.argv) != 6:
        print("Usage: python run_crawl_process.py <start_url> <depth> <delay> <concurrency> <js_rendering>")
        sys.exit(1)

    # Unpack command-line arguments
    _script_name, start_url, depth, delay, concurrency, js_rendering = sys.argv

    # Convert arguments to their correct types
    depth = int(depth)
    delay = float(delay)
    concurrency = int(concurrency)
    # js_rendering is already a string 'True' or 'False', which is handled by the crawler

    run_single_crawl(start_url, depth, delay, concurrency, js_rendering)
