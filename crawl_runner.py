"""Shared subprocess runner for the crawler."""

import subprocess
import sys


def run_crawler_subprocess(
    url: str, depth: int, delay: float, concurrency: int, js_rendering: bool
) -> tuple[bool, str]:
    """Launch run_crawl_process.py as a subprocess and wait for completion.

    Args:
        url: The starting URL to crawl.
        depth: Maximum crawl depth.
        delay: Delay between requests in seconds.
        concurrency: Number of concurrent requests.
        js_rendering: Whether to enable JavaScript rendering.

    Returns:
        A tuple of (success: bool, message: str).
    """
    command = [
        sys.executable,
        "run_crawl_process.py",
        url,
        str(depth),
        str(delay),
        str(concurrency),
        str(js_rendering),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        msg = f"Crawler process failed with exit code {e.returncode}.\n"
        msg += f"Stderr:\n{e.stderr}"
        return False, msg
