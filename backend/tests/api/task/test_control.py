"""Test task-control router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_ok


def test_task_worker_health(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test task worker health API with the real test worker."""
    response = client.get("/tasks/health", headers=token_headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert body["data"] is True


def test_task_registered_with_worker(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test registered-task API with the real test worker."""
    response = client.get("/tasks/registered", headers=token_headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert any(item["task"] == "task_demo_params" for item in body["data"])


def test_task_revoke_with_worker(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test task revoke API with the real test worker."""
    response = client.request("DELETE", "/tasks/api-task-id/cancel", headers=token_headers)
    assert response.status_code == 200
    assert_ok(response.json())
