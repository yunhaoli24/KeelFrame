"""Test notice router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore
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


def test_notice_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test notice CRUD APIs."""
    payload = {"title": "API Notice", "type": 0, "status": 1, "content": "notice body"}
    assert_page(get_json(client, "/sys/notices", token_headers))
    assert_page(get_json(client, "/sys/notices", token_headers, title="测试", notice_type=0, status=1))
    assert_ok(post_json(client, "/sys/notices", token_headers, payload))
    notice_id = find_created_id(client, "/sys/notices", token_headers, "title", payload["title"])
    data_store.created["notice_id"] = notice_id

    assert_ok(get_json(client, f"/sys/notices/{notice_id}", token_headers))
    assert_ok(put_json(client, f"/sys/notices/{notice_id}", token_headers, payload | {"content": "updated"}))
    assert_ok(delete_json(client, "/sys/notices", token_headers, {"pks": [notice_id]}))


def test_notice_missing(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test notice not-found response."""
    response = client.get("/sys/notices/999999", headers=token_headers)
    assert response.status_code == 404
    assert_error(response.json(), 404)

    missing_update = client.put(
        "/sys/notices/999999",
        headers=token_headers,
        json={"title": "Missing Notice", "type": 0, "status": 1, "content": "missing"},
    )
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    missing_delete = client.request("DELETE", "/sys/notices", headers=token_headers, json={"pks": [999999]})
    assert missing_delete.status_code == 200
    assert_error(missing_delete.json(), 400)

    empty_delete = client.request("DELETE", "/sys/notices", headers=token_headers, json={"pks": []})
    assert empty_delete.status_code == 200
    assert_error(empty_delete.json(), 400)
