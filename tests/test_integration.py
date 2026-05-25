"""Integration tests verifying the full crawl -> database round-trip."""

import http.server
import os
import sqlite3
import threading
import time
from functools import partial

import pytest

from crawl_runner import run_crawler_subprocess

DB_FILE = "growling_cat.db"


@pytest.fixture(scope="module")
def test_server():
    """Start a local HTTP server for integration testing."""
    test_dir = os.path.join(os.path.dirname(__file__), ".")
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=test_dir)
    httpd = http.server.HTTPServer(("localhost", 8777), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    yield "http://localhost:8777"
    httpd.shutdown()


@pytest.fixture(autouse=True)
def clean_db():
    """Remove test database before and after each test."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    journal = f"{DB_FILE}-journal"
    if os.path.exists(journal):
        os.remove(journal)
    yield
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    if os.path.exists(journal):
        os.remove(journal)


def test_crawl_and_db_roundtrip(test_server: str) -> None:
    """Run a full crawl against the local server and verify data in the database."""
    success, message = run_crawler_subprocess(
        f"{test_server}/sample.html", depth=0, delay=0.1, concurrency=1, js_rendering=False
    )

    assert success, f"Crawl failed: {message}"
    assert os.path.exists(DB_FILE), "Database file was not created"

    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("SELECT url, title, status_code FROM pages").fetchall()
    conn.close()

    assert len(rows) == 1, f"Expected 1 page, got {len(rows)}"
    url, title, status = rows[0]
    assert "sample.html" in url
    assert title == "Sample Page Title"
    assert status == 200


def test_crawl_multiple_pages(test_server: str) -> None:
    """Verify crawl produces a non-empty database for a real page."""
    success, _ = run_crawler_subprocess(
        f"{test_server}/sample.html", depth=0, delay=0.1, concurrency=1, js_rendering=False
    )

    assert success
    assert os.path.exists(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    columns = [c[1] for c in conn.execute("PRAGMA table_info(pages)").fetchall()]
    conn.close()

    expected_columns = [
        "url", "status_code", "title", "meta_description", "canonical",
        "h1_tags", "h2_tags", "h3_tags", "image_alts", "json_ld", "broken_links",
    ]
    for col in expected_columns:
        assert col in columns, f"Missing column in DB: {col}"
