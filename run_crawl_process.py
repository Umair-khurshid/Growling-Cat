"""Entry point for running the Scrapy crawler as a subprocess."""

import logging
import sys

from scrapy.crawler import CrawlerProcess

from crawler import SEOCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_single_crawl(
    start_url: str,
    depth: int,
    delay: float,
    concurrency: int,
    js_rendering: str,
) -> None:
    """Configure and run a single Scrapy crawl.

    Args:
        start_url: The URL to start crawling from.
        depth: Maximum crawl depth.
        delay: Delay between requests in seconds.
        concurrency: Number of concurrent requests.
        js_rendering: 'True' or 'False' string for JS rendering.
    """
    try:
        settings: dict[str, object] = {
            "DEPTH_LIMIT": depth,
            "DOWNLOAD_DELAY": delay,
            "CONCURRENT_REQUESTS": concurrency,
            "ITEM_PIPELINES": {
                "pipelines.SqlitePipeline": 300,
            },
            "LOG_LEVEL": "INFO",
            "DOWNLOAD_TIMEOUT": 40,
            "RETRY_ENABLED": True,
            "RETRY_TIMES": 8,
            "RETRY_HTTP_CODES": [522, 500, 502, 503, 504, 408],
            "ROBOTSTXT_OBEY": False,
            "USER_AGENT": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                " AppleWebKit/537.36 (KHTML, like Gecko)"
                " Chrome/121.0.0.0 Safari/537.36"
            ),
            "DOWNLOADER_MIDDLEWARES": {
                "middlewares.RotatingUserAgentMiddleware": 400,
            },
            "EXTENSIONS": {
                "extensions.ProgressExtension": 500,
            },
        }

        process = CrawlerProcess(settings)
        process.crawl(SEOCrawler, start_url=start_url, js_rendering=js_rendering)
        process.start()
        logger.info("Crawl process finished successfully.")

    except Exception as e:
        logger.error("An error occurred during the crawl process: %s", e)
        sys.exit(1)


def main() -> None:
    """Parse CLI arguments and start the crawl."""
    if len(sys.argv) != 6:
        usage = (
            "Usage: python run_crawl_process.py <start_url> <depth> <delay> "
            "<concurrency> <js_rendering>"
        )
        print(usage)
        sys.exit(1)

    _script_name, start_url_arg, depth_arg, delay_arg, concurrency_arg, js_rendering_arg = (
        sys.argv
    )

    depth = int(depth_arg)
    delay = float(delay_arg)
    concurrency = int(concurrency_arg)

    run_single_crawl(start_url_arg, depth, delay, concurrency, js_rendering_arg)


if __name__ == "__main__":
    main()
