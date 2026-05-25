"""Tests for the crawl_runner module."""
# pylint: disable=missing-function-docstring

from subprocess import CalledProcessError
from unittest.mock import patch

from crawl_runner import run_crawler_subprocess


@patch("crawl_runner.subprocess.run")
def test_run_crawler_subprocess_success(mock_run) -> None:
    mock_run.return_value.returncode = 0

    success, message = run_crawler_subprocess(
        "https://example.com", 2, 0.5, 8, False
    )

    assert success is True
    assert message == ""


@patch("crawl_runner.subprocess.run")
def test_run_crawler_subprocess_failure(mock_run) -> None:
    mock_run.side_effect = CalledProcessError(
        returncode=1, cmd=[], stderr="connection refused"
    )

    success, message = run_crawler_subprocess(
        "https://example.com", 2, 0.5, 8, False
    )

    assert success is False
    assert "exit code 1" in message
    assert "connection refused" in message
