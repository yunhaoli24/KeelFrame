"""Test opera-log router APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import get_json, assert_ok, assert_page, assert_error


def test_opera_log_read_and_delete_failure(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test opera-log list and delete failure branch."""
    assert_page(get_json(client, "/logs/opera", token_headers))

    response = client.request("DELETE", "/logs/opera", headers=token_headers, json={"pks": [999999]})
    assert response.status_code == 200
    assert_error(response.json(), 400)

    filtered = get_json(client, "/logs/opera", token_headers, username="admin", status=1, ip="127.0.0.1")
    assert_page(filtered)

    clear = client.request("DELETE", "/logs/opera/all", headers=token_headers)
    assert clear.status_code == 200
    assert_ok(clear.json())

