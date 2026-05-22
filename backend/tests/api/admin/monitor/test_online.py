"""Test online-session router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_ok


def test_online_sessions(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test online session list APIs."""
    assert_ok(get_json(client, "/monitors/sessions", token_headers))
    assert_ok(get_json(client, "/monitors/sessions", token_headers, username="admin"))


def test_delete_online_session(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test force-offline API with a harmless missing session UUID."""
    response = client.request(
        "DELETE",
        "/monitors/sessions/1",
        headers=token_headers,
        params={"session_uuid": "missing"},
    )
    assert response.status_code == 200
    assert_ok(response.json())
