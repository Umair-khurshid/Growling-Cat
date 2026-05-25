"""Tests for the ProgressExtension."""

import json
import os
from unittest.mock import MagicMock

import pytest

from extensions import ProgressExtension


@pytest.fixture
def extension() -> ProgressExtension:
    ext = ProgressExtension()
    return ext


def test_initial_state(extension: ProgressExtension) -> None:
    assert extension.total_requests == 0
    assert extension.completed_requests == 0
    assert extension.done is False


def test_spider_opened_resets_state(extension: ProgressExtension) -> None:
    extension.total_requests = 10
    extension.completed_requests = 5
    extension.items_scraped = 7
    extension.done = True

    extension.spider_opened(MagicMock())

    assert extension.total_requests == 0
    assert extension.completed_requests == 0
    assert extension.items_scraped == 0
    assert extension.done is False


def test_spider_closed_sets_done(extension: ProgressExtension) -> None:
    extension.spider_closed(MagicMock(), "finished")

    assert extension.done is True


def test_request_scheduled_increments(extension: ProgressExtension) -> None:
    extension.request_scheduled(MagicMock(), MagicMock())

    assert extension.total_requests == 1
    assert extension.completed_requests == 0


def test_response_received_increments(extension: ProgressExtension) -> None:
    extension.response_received(MagicMock(), MagicMock(), MagicMock())

    assert extension.completed_requests == 1


def test_request_dropped_increments(extension: ProgressExtension) -> None:
    extension.request_dropped(MagicMock(), MagicMock())

    assert extension.completed_requests == 1


def test_update_progress_file_writes_json(extension: ProgressExtension) -> None:
    extension.total_requests = 10
    extension.completed_requests = 3
    extension.done = False
    extension.update_progress_file()

    assert os.path.exists("progress.json")
    with open("progress.json") as f:
        data = json.load(f)

    assert data["total"] == 10
    assert data["completed"] == 3
    assert data["items_scraped"] == 0
    assert data["done"] is False

    os.remove("progress.json")


def test_from_crawler_connects_signals() -> None:
    crawler = MagicMock()
    ext = ProgressExtension.from_crawler(crawler)

    assert isinstance(ext, ProgressExtension)
    assert crawler.signals.connect.call_count == 6
