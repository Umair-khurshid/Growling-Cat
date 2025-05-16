import json
import os
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
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)
        return ext

    def spider_opened(self, spider):
        self.total_requests = 0
        self.completed_requests = 0
        self.done = False
        self.update_progress_file()

    def spider_closed(self, spider, reason):
        self.done = True
        self.update_progress_file()

    def request_scheduled(self, request, spider):
        self.total_requests += 1
        self.update_progress_file()

    def response_received(self, response, request, spider):
        self.completed_requests += 1
        self.update_progress_file()

    def request_dropped(self, request, spider):
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
