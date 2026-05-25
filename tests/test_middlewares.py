"""Tests for the RotatingUserAgentMiddleware."""
# pylint: disable=missing-function-docstring

from unittest.mock import MagicMock

from middlewares import RotatingUserAgentMiddleware


def test_process_request_sets_user_agent() -> None:
    middleware = RotatingUserAgentMiddleware()
    request = MagicMock()
    request.headers = {}
    spider = MagicMock()

    middleware.process_request(request, spider)

    assert "User-Agent" in request.headers
    ua = request.headers["User-Agent"]
    assert ua in RotatingUserAgentMiddleware.USER_AGENTS


def test_user_agent_rotates() -> None:
    middleware = RotatingUserAgentMiddleware()
    request = MagicMock()
    spider = MagicMock()

    agents: set[str] = set()
    for _ in range(50):
        request.headers = {}
        middleware.process_request(request, spider)
        agents.add(request.headers["User-Agent"])

    # With 10 agents and 50 trials, we expect to see at least 5 different ones
    assert len(agents) >= 5
