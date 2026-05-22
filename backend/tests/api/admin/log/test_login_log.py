"""Test login-log router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_ok, assert_page, assert_error


def test_login_log_read_and_delete_failure(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test login-log list and delete failure branch."""
    assert_page(get_json(client, "/logs/login", token_headers))

    response = client.request("DELETE", "/logs/login", headers=token_headers, json={"pks": [999999]})
    assert response.status_code == 200
    assert_error(response.json(), 400)

    filtered = get_json(client, "/logs/login", token_headers, username="admin", status=1, ip="127.0.0.1")
    assert_page(filtered)

    clear = client.request("DELETE", "/logs/login/all", headers=token_headers)
    assert clear.status_code == 200
    assert_ok(clear.json())


def test_login_log_delete_existing_record(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test login-log delete success using a log created by a public login request."""
    response = client.post("/auth/login", json={"username": "admin", "password": "123456"})
    assert response.status_code == 200

    items = assert_page(get_json(client, "/logs/login", token_headers, username="admin", status=1))
    matches = [item for item in items if item["username"] == "admin" and item["status"] == 1]
    assert matches
    log_id = matches[0]["id"]
    assert isinstance(log_id, int)

    deleted = client.request("DELETE", "/logs/login", headers=token_headers, json={"pks": [log_id]})
    assert deleted.status_code == 200
    assert_ok(deleted.json())
