"""Test chat completions router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_error


def test_chat_completion_requires_model(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test chat completion validation through the public API."""
    response = client.post("/chat/completions", headers=token_headers, json={"messages": []})
    assert response.status_code == 400
    assert_error(response.json(), 400)
