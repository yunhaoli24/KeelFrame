"""Test captcha router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_ok


def test_captcha(client: TestClient) -> None:
    """Test captcha API."""
    response = client.get("/auth/captcha")
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert "is_enabled" in body["data"]
