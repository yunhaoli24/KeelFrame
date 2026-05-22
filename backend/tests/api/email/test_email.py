"""Test email router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_ok


def test_email_captcha(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test email captcha through the public API."""
    response = client.post("/emails/captcha", headers=token_headers, json={"recipients": "api@example.com"})
    assert response.status_code == 200
    assert_ok(response.json())
