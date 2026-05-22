"""Test task-control router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_error


def test_task_registered_requires_worker(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test registered-task API failure shape when worker is unavailable."""
    response = client.get("/tasks/registered", headers=token_headers)
    assert response.status_code in {200, 500}
    body = response.json()
    assert "code" in body
    assert "msg" in body


def test_task_revoke_requires_worker(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test task revoke failure shape when worker is unavailable."""
    response = client.request("DELETE", "/tasks/api-task-id/cancel", headers=token_headers)
    assert response.status_code == 500
    assert_error(response.json(), 500)
