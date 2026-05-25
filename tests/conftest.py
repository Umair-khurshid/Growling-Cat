"""Shared fixtures and configuration for all tests."""

from __future__ import annotations

import http.server
import os
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from functools import partial
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Page

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DB_FILE = "growling_cat.db"
DB_JOURNAL = f"{DB_FILE}-journal"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

STREAMLIT_PORT = 8510
TEST_SERVER_PORT = 8779


def _find_streamlit() -> str | None:
    """Find the streamlit executable."""
    streamlit_path = shutil.which("streamlit")
    if streamlit_path:
        return streamlit_path
    for path in sys.path:
        candidate = os.path.join(path, "streamlit", "__main__.py")
        if os.path.exists(candidate):
            return candidate
    return None


@pytest.fixture(scope="module")
def test_server() -> Iterator[str]:
    """Start a local HTTP server serving the tests/ directory for crawling."""
    test_dir = os.path.dirname(__file__)
    handler = partial(
        http.server.SimpleHTTPRequestHandler, directory=test_dir
    )
    httpd = http.server.HTTPServer(("localhost", TEST_SERVER_PORT), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)
    yield f"http://localhost:{TEST_SERVER_PORT}"
    httpd.shutdown()


@pytest.fixture(scope="module")
def streamlit_base_url() -> Iterator[str]:
    """Start the Streamlit app as a subprocess and return its base URL."""
    port = STREAMLIT_PORT

    # Remove old DB before starting
    for f in (DB_FILE, DB_JOURNAL):
        if os.path.exists(f):
            os.remove(f)

    streamlit_exe = _find_streamlit()
    if streamlit_exe and os.path.sep in streamlit_exe and os.path.isfile(streamlit_exe):
        cmd = [sys.executable, streamlit_exe]
    else:
        cmd = [sys.executable, "-m", "streamlit"]

    cmd += [
        "run",
        os.path.join(PROJECT_ROOT, "app.py"),
        f"--server.port={port}",
        "--server.headless=true",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]

    log_file = os.path.join(PROJECT_ROOT, "streamlit_test.log")
    log_fh = open(log_file, "a", encoding="utf-8")  # pylint: disable=consider-using-with
    proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=log_fh,
        stderr=log_fh,
    )

    base_url = f"http://localhost:{port}"
    _wait_for_url(base_url, timeout=60)

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_fh.close()


def _wait_for_url(url: str, timeout: int = 60) -> None:
    """Poll a URL until it returns a successful response."""
    import urllib.error  # pylint: disable=import-outside-toplevel
    import urllib.request  # pylint: disable=import-outside-toplevel

    deadline = time.monotonic() + timeout
    health_url = f"{url}/_stcore/health"
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(health_url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:  # pylint: disable=unspecified-encoding
                if resp.status == 200:
                    time.sleep(1.0)  # Extra settling time for the UI
                    return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1.0)
    raise RuntimeError(f"Streamlit did not start within {timeout}s at {url}")


@pytest.fixture(scope="function")
def app_page(  # pylint: disable=redefined-outer-name,unused-argument
    page: Page,
    streamlit_base_url: str,
    clean_db: None,
) -> Page:
    """A Playwright page navigated to the Streamlit app, with a clean database."""
    page.set_default_timeout(30000)
    page.goto(streamlit_base_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture(scope="function", autouse=False)
def clean_db() -> None:
    """Remove the crawl database before and after each test."""
    for f in (DB_FILE, DB_JOURNAL):
        if os.path.exists(f):
            os.remove(f)
    yield
    for f in (DB_FILE, DB_JOURNAL):
        if os.path.exists(f):
            os.remove(f)
    progress = "progress.json"
    if os.path.exists(progress):
        os.remove(progress)
