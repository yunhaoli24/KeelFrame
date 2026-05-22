"""Test task-result router APIs."""

import time

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_page, assert_error


def test_task_result_read_and_delete_failure(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test task-result list, detail not-found, and delete failure branch."""
    assert_page(get_json(client, "/task-results", token_headers))
    assert_page(get_json(client, "/task-results", token_headers, name="missing", task_id="missing-task"))

    missing = client.get("/task-results/999999", headers=token_headers)
    assert missing.status_code == 404
    assert_error(missing.json(), 404)

    response = client.request("DELETE", "/task-results", headers=token_headers, json={"pks": [999999]})
    assert response.status_code == 200
    assert_error(response.json(), 400)


def test_task_result_contains_beat_task(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test real Celery beat submits the test schedule to the real worker."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        items = assert_page(get_json(client, "/task-results", token_headers, name="task_demo_params"))
        for item in items:
            if item.get("status") == "SUCCESS" and item.get("name") == "task_demo_params":
                detail = get_json(client, f"/task-results/{item['id']}", token_headers)
                if detail["data"]["result"] == "beat-test":
                    return
        time.sleep(1)

    msg = "Celery beat did not create a successful task_demo_params result"
    raise AssertionError(msg)
