"""Command-line interface for running the crawler."""

import logging

from crawl_runner import run_crawler_subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    file_handler = logging.FileHandler("main.log")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def run_crawler(
    url: str, depth: int, delay: float, concurrency: int, js_rendering: bool
) -> None:
    """Run the crawler with the specified parameters.

    Args:
        url: The starting URL to crawl.
        depth: Maximum crawl depth.
        delay: Delay between requests in seconds.
        concurrency: Number of concurrent requests.
        js_rendering: Whether to enable JavaScript rendering.
    """
    success, message = run_crawler_subprocess(
        url, depth, delay, concurrency, js_rendering
    )
    if success:
        logger.info("Crawler executed successfully for URL: %s", url)
    else:
        logger.error("Crawler process failed: %s", message)
