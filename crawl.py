import sys
import logging
from scrapy.crawler import CrawlerProcess
from crawler import SEOCrawler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("crawl.log")
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
fh.setFormatter(formatter)
logger.addHandler(fh)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error(
            "Usage: python crawl.py <URL> [DEPTH_LIMIT] "
            "[DOWNLOAD_DELAY] [CONCURRENT_REQUESTS] [JS_RENDERING]"
        )
        sys.exit(1)

    url = sys.argv[1]
    depth_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    download_delay = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    concurrent_requests = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    js_rendering = sys.argv[5] if len(sys.argv) > 5 else "False"

    settings = {
        "LOG_LEVEL": "ERROR",
        "DOWNLOAD_TIMEOUT": 40,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 8,
        "RETRY_HTTP_CODES": [522, 500, 502, 503, 504, 408],
        "ROBOTSTXT_OBEY": False,
        "DEPTH_LIMIT": depth_limit,
        "DOWNLOAD_DELAY": download_delay,
        "CONCURRENT_REQUESTS": concurrent_requests,
        "DOWNLOADER_MIDDLEWARES": {
            "middlewares.RotatingUserAgentMiddleware": 543,
        },
        "EXTENSIONS": {
            "extensions.ProgressExtension": 500,
        },
    }

    process = CrawlerProcess(settings=settings)
    try:
        process.crawl(
            SEOCrawler,
            start_url=url,
            js_rendering=js_rendering
        )
        process.start()
    except Exception as e:
        logger.error(f"Error during crawling: {e}")

