"""
Scrapy extensions for progress tracking.
# pylint: disable=unused-argument
"""

import json

from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.spiders import Spider


class ProgressExtension:
    """Tracks scheduled vs completed requests and writes progress to a JSON file."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.completed_requests: int = 0
        self.items_scraped: int = 0
        self.done: bool = False

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "ProgressExtension":
        """Create extension instance and connect signals."""
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)
        crawler.signals.connect(ext._on_item_scraped, signal=signals.item_scraped)
        return ext

    def spider_opened(self, spider: Spider) -> None:  # noqa: ARG002
        """Reset counters when the spider opens."""
        self.total_requests = 0
        self.completed_requests = 0
        self.items_scraped = 0
        self.done = False
        self.update_progress_file()

    def spider_closed(self, spider: Spider, reason: str) -> None:  # noqa: ARG002
        """Mark crawl as done when the spider closes."""
        self.done = True
        self.update_progress_file()

    def request_scheduled(self, request: object, spider: Spider) -> None:  # noqa: ARG002
        """Increment total request count."""
        self.total_requests += 1
        self.update_progress_file()

    def _on_item_scraped(self, item: object, response: object, spider: Spider) -> None:  # noqa: ARG002
        """Increment items_scraped count when a PageItem is successfully processed."""
        self.items_scraped += 1
        self.update_progress_file()

    def response_received(
        self, response: object, request: object, spider: Spider
    ) -> None:  # noqa: ARG002
        """Increment completed request count on response."""
        self.completed_requests += 1
        self.update_progress_file()

    def request_dropped(self, request: object, spider: Spider) -> None:  # noqa: ARG002
        """Treat dropped requests as completed to keep progress accurate."""
        self.completed_requests += 1
        self.update_progress_file()

    def update_progress_file(self) -> None:
        """Write current progress to a JSON file so Streamlit can read it."""
        data = {
            "total": self.total_requests,
            "completed": self.completed_requests,
            "items_scraped": self.items_scraped,
            "done": self.done,
        }
        with open("progress.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
