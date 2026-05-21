"""Test task APIs that do not require a running Celery worker."""

from starlette.testclient import TestClient

from tests.conftest import DataStore
from tests.api.helpers import assert_ok, assert_page, get_json, put_json, post_json, delete_json, find_created_id


def test_scheduler_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test scheduler metadata CRUD APIs."""
    payload = {
        "name": "api-scheduler",
        "task": "backend.app.task.tasks.tasks.demo_task",
        "args": [],
        "kwargs": {},
        "queue": None,
        "exchange": None,
        "routing_key": None,
        "start_time": None,
        "expire_time": None,
        "expire_seconds": None,
        "type": 0,
        "interval_every": 10,
        "interval_period": "seconds",
        "crontab": "* * * * *",
        "one_off": False,
        "remark": "api",
    }
    assert_page(get_json(client, "/schedulers", token_headers))
    assert_ok(post_json(client, "/schedulers", token_headers, payload))
    scheduler_id = find_created_id(client, "/schedulers", token_headers, "name", payload["name"])
    data_store.created["scheduler_id"] = scheduler_id

    assert_ok(get_json(client, f"/schedulers/{scheduler_id}", token_headers))
    assert_ok(put_json(client, f"/schedulers/{scheduler_id}", token_headers, payload | {"remark": "updated"}))
    assert_ok(put_json(client, f"/schedulers/{scheduler_id}/status", token_headers))
    assert_ok(delete_json(client, f"/schedulers/{scheduler_id}", token_headers))


def test_task_registered_requires_worker(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test registered-task API failure shape when worker is unavailable."""
    response = client.get("/tasks/registered", headers=token_headers)
    assert response.status_code in {200, 500}
    body = response.json()
    assert "code" in body
    assert "msg" in body
