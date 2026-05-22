"""Test scheduler router APIs."""

import psycopg
from starlette.testclient import TestClient

from tests.conftest import TEST_SQLALCHEMY_DATABASE_URL, DataStore, login_headers
from tests.api.helpers import (
    get_json,
    put_json,
    assert_ok,
    post_json,
    assert_page,
    delete_json,
    assert_error,
    find_created_id,
)


def scheduler_payload(name: str = "api-scheduler") -> dict[str, object]:
    """Build a scheduler payload."""
    return {
        "name": name,
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


def test_scheduler_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test scheduler metadata CRUD APIs."""
    payload = scheduler_payload()
    assert_page(get_json(client, "/schedulers", token_headers))
    assert_ok(get_json(client, "/schedulers/all", token_headers))
    assert_ok(get_json(client, "/schedulers/1", token_headers))
    assert_page(get_json(client, "/schedulers", token_headers, name="测试", scheduler_type=1))
    assert_ok(post_json(client, "/schedulers", token_headers, payload))
    scheduler_id = find_created_id(client, "/schedulers", token_headers, "name", payload["name"])
    data_store.created["scheduler_id"] = scheduler_id

    assert_ok(get_json(client, f"/schedulers/{scheduler_id}", token_headers))
    assert_ok(put_json(client, f"/schedulers/{scheduler_id}", token_headers, payload | {"remark": "updated"}))
    assert_ok(put_json(client, f"/schedulers/{scheduler_id}/status", token_headers))
    assert_ok(delete_json(client, f"/schedulers/{scheduler_id}", token_headers))


def test_scheduler_crontab_update_and_conflict(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test scheduler crontab update and update-conflict branches."""
    source = scheduler_payload("api-crontab-source") | {
        "type": 1,
        "interval_every": None,
        "interval_period": None,
        "crontab": "*/5 * * * *",
    }
    target = scheduler_payload("api-crontab-target")
    assert_ok(post_json(client, "/schedulers", token_headers, source))
    assert_ok(post_json(client, "/schedulers", token_headers, target))
    source_id = find_created_id(client, "/schedulers", token_headers, "name", source["name"])
    target_id = find_created_id(client, "/schedulers", token_headers, "name", target["name"])

    assert_ok(put_json(client, f"/schedulers/{source_id}", token_headers, source | {"crontab": "10 * * * *"}))

    conflict = client.put(f"/schedulers/{source_id}", headers=token_headers, json=source | {"name": target["name"]})
    assert conflict.status_code == 409
    assert_error(conflict.json(), 409)

    invalid_update = client.put(f"/schedulers/{source_id}", headers=token_headers, json=source | {"crontab": "bad"})
    assert invalid_update.status_code == 400
    assert_error(invalid_update.json(), 400)

    assert_ok(delete_json(client, f"/schedulers/{source_id}", token_headers))
    assert_ok(delete_json(client, f"/schedulers/{target_id}", token_headers))


def test_scheduler_execute_existing_task(
    client: TestClient,
    token_headers: dict[str, str],
    data_store: DataStore,
) -> None:
    """Test manual execution submits an existing scheduler to the test Celery worker."""
    payload = scheduler_payload("api-executable-scheduler") | {
        "task": "task_demo_params",
        "args": ["hello"],
        "kwargs": {"world": "-api"},
    }
    assert_ok(post_json(client, "/schedulers", token_headers, payload))
    scheduler_id = find_created_id(client, "/schedulers", token_headers, "name", payload["name"])
    data_store.created["executable_scheduler_id"] = scheduler_id

    try:
        assert_ok(post_json(client, f"/schedulers/{scheduler_id}/execute", token_headers, None))
    finally:
        assert_ok(delete_json(client, f"/schedulers/{scheduler_id}", token_headers))


def test_scheduler_missing(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test scheduler not-found responses."""
    for method, path in (
        ("GET", "/schedulers/999999"),
        ("PUT", "/schedulers/999999/status"),
        ("DELETE", "/schedulers/999999"),
    ):
        response = client.request(method, path, headers=token_headers)
        assert response.status_code == 404
        assert_error(response.json(), 404)

    missing_update = client.put("/schedulers/999999", headers=token_headers, json=scheduler_payload("missing"))
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    duplicate_payload = scheduler_payload("api-scheduler-duplicate")
    assert_ok(post_json(client, "/schedulers", token_headers, duplicate_payload))
    duplicate = client.post("/schedulers", headers=token_headers, json=duplicate_payload)
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    invalid_crontab = scheduler_payload("api-invalid-crontab") | {"type": 1, "crontab": "bad"}
    crontab_response = client.post("/schedulers", headers=token_headers, json=invalid_crontab)
    assert crontab_response.status_code == 400
    assert_error(crontab_response.json(), 400)

    execute_missing = client.post("/schedulers/999999/execute", headers=token_headers)
    assert execute_missing.status_code == 404
    assert_error(execute_missing.json(), 404)

    bad_args_name = "api-bad-execute-args"
    bad_args: dict[str, object] = scheduler_payload(bad_args_name) | {
        "args": "not-json",
        "kwargs": dict[str, str](),
    }
    bad_args_create = client.post("/schedulers", headers=token_headers, json=bad_args)
    assert bad_args_create.status_code == 422
    assert_error(bad_args_create.json(), 422)

    bad_args = scheduler_payload(bad_args_name) | {"args": list[str](), "kwargs": dict[str, str]()}
    assert_ok(post_json(client, "/schedulers", token_headers, bad_args))
    bad_args_id = find_created_id(client, "/schedulers", token_headers, "name", bad_args_name)
    test_database_url = TEST_SQLALCHEMY_DATABASE_URL.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(test_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE task_scheduler SET args = '\"not-json\"'::jsonb WHERE id = %s", (bad_args_id,))
        conn.commit()
    execute_bad_args = client.post(f"/schedulers/{bad_args_id}/execute", headers=token_headers)
    assert execute_bad_args.status_code == 400
    assert_error(execute_bad_args.json(), 400)
    assert_ok(delete_json(client, f"/schedulers/{bad_args_id}", token_headers))


def test_scheduler_write_apis_reject_normal_user(client: TestClient, data_store: DataStore) -> None:
    """Test scheduler write APIs reject a normal authenticated user."""
    headers = data_store.test_headers or login_headers(client, "test", "123456")
    create_response = client.post("/schedulers", headers=headers, json=scheduler_payload("normal-scheduler"))
    assert create_response.status_code == 403
    assert_error(create_response.json(), 403)

    update_response = client.put("/schedulers/1", headers=headers, json=scheduler_payload("normal-scheduler"))
    assert update_response.status_code == 403
    assert_error(update_response.json(), 403)

    status_response = client.put("/schedulers/1/status", headers=headers)
    assert status_response.status_code == 403
    assert_error(status_response.json(), 403)

    execute_response = client.post("/schedulers/1/execute", headers=headers)
    assert execute_response.status_code == 403
    assert_error(execute_response.json(), 403)

    delete_response = client.request("DELETE", "/schedulers/1", headers=headers)
    assert delete_response.status_code == 403
    assert_error(delete_response.json(), 403)
