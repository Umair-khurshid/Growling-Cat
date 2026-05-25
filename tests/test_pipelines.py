"""Tests for the SqlitePipeline."""

from unittest.mock import MagicMock

import pytest

from pipelines import SqlitePipeline


@pytest.fixture
def pipeline() -> SqlitePipeline:
    return SqlitePipeline()


def test_open_spider_creates_table(pipeline: SqlitePipeline) -> None:
    spider = MagicMock()
    pipeline.open_spider(spider)

    assert pipeline.connection is not None
    assert pipeline.cursor is not None

    pipeline.cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pages'"
    )
    assert pipeline.cursor.fetchone() is not None

    pipeline.close_spider(spider)


def test_process_item_inserts_data(pipeline: SqlitePipeline) -> None:
    spider = MagicMock()
    pipeline.open_spider(spider)

    item = {
        "url": "https://example.com",
        "status_code": 200,
        "title": "Test Title",
        "meta_description": "Test description",
        "canonical": "https://example.com",
        "h1_tags": "H1",
        "h2_tags": "H2",
        "h3_tags": "H3",
        "image_alts": "alt text",
        "json_ld": '{"@type": "WebSite"}',
        "broken_links": "N/A",
    }

    result = pipeline.process_item(item, spider)
    assert result == item

    pipeline.cursor.execute("SELECT * FROM pages WHERE url = ?", ("https://example.com",))
    row = pipeline.cursor.fetchone()
    assert row is not None
    assert row[2] == "Test Title"

    pipeline.close_spider(spider)


def test_process_item_handles_missing_broken_links(pipeline: SqlitePipeline) -> None:
    spider = MagicMock()
    pipeline.open_spider(spider)

    item = {
        "url": "https://example.com/no-broken",
        "status_code": 200,
        "title": "No Broken",
        "meta_description": "desc",
        "canonical": "",
        "h1_tags": "",
        "h2_tags": "",
        "h3_tags": "",
        "image_alts": "",
        "json_ld": "",
    }

    pipeline.process_item(item, spider)
    pipeline.cursor.execute(
        "SELECT broken_links FROM pages WHERE url = ?",
        ("https://example.com/no-broken",),
    )
    row = pipeline.cursor.fetchone()
    assert row is not None
    assert row[0] == "N/A"

    pipeline.close_spider(spider)


def test_process_item_handles_no_cursor(pipeline: SqlitePipeline) -> None:
    spider = MagicMock()
    item = {"url": "https://example.com"}
    result = pipeline.process_item(item, spider)
    assert result == item
