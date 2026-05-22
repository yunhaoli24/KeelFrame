"""Test Redis monitor router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_ok


def test_redis_monitor(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test Redis monitor API."""
    assert_ok(get_json(client, "/monitors/redis", token_headers))
