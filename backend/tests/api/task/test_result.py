"""Test task-result router APIs."""

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
