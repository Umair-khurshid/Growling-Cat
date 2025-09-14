"""
This module contains Scrapy extensions.
"""
import json
from scrapy import signals


class ProgressExtension:
    """
    Tracks how many requests have been scheduled vs. completed.
    Writes progress info to 'progress.json' so Streamlit can display a real progress bar.
    """

    def __init__(self):
        self.total_requests = 0
        self.completed_requests = 0
        self.done = False

    @classmethod
    def from_crawler(cls, crawler):
        """
        This method is used by Scrapy to create your extension.
        """
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)
        return ext

    def spider_opened(self, _spider):
        """
        Called when the spider is opened.
        """
        self.total_requests = 0
        self.completed_requests = 0
        self.done = False
        self.update_progress_file()

    def spider_closed(self, _spider, _reason):
        """
        Called when the spider is closed.
        """
        self.done = True
        self.update_progress_file()

    def request_scheduled(self, _request, _spider):
        """
        Called when a request is scheduled.
        """
        self.total_requests += 1
        self.update_progress_file()

    def response_received(self, _response, _request, _spider):
        """
        Called when a response is received.
        """
        self.completed_requests += 1
        self.update_progress_file()

    def request_dropped(self, _request, _spider):
        """
        If a request is dropped (e.g., filtered by dupefilter),
        treat it as completed so the progress doesn't stall.
        """
        self.completed_requests += 1
        self.update_progress_file()

    def update_progress_file(self):
        """
        Write current progress to a JSON file so Streamlit can read it.
        """
        data = {
            "total": self.total_requests,
            "completed": self.completed_requests,
            "done": self.done,
        }
        with open("progress.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
