"""Test server monitor router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_ok


def test_server_monitor(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test server monitor API."""
    assert_ok(get_json(client, "/monitors/server", token_headers))

