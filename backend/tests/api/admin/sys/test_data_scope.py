"""Test data-scope router APIs."""

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
from tests.api.admin.sys.test_data_rule import data_rule_payload


def test_data_scope_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded data-scope read APIs."""
    assert_page(get_json(client, "/sys/data-scopes", token_headers))
    assert_page(get_json(client, "/sys/data-scopes", token_headers, name="测试", status=1))
    assert_ok(get_json(client, "/sys/data-scopes/all", token_headers))
    assert_ok(get_json(client, "/sys/data-scopes/1", token_headers))
    assert_ok(get_json(client, "/sys/data-scopes/1/rules", token_headers))

    for path in ("/sys/data-scopes/999999", "/sys/data-scopes/999999/rules"):
        response = client.get(path, headers=token_headers)
        assert response.status_code == 404
        assert_error(response.json(), 404)


def test_data_scope_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test data-scope write APIs."""
    rule_payload = data_rule_payload("API Scope Rule")
    assert_ok(post_json(client, "/sys/data-rules", token_headers, rule_payload))
    rule_id = find_created_id(client, "/sys/data-rules", token_headers, "name", rule_payload["name"])
    data_store.created["data_scope_rule_id"] = rule_id

    scope_payload = {"name": "API Data Scope", "status": 1}
    assert_ok(post_json(client, "/sys/data-scopes", token_headers, scope_payload))
    scope_id = find_created_id(client, "/sys/data-scopes", token_headers, "name", scope_payload["name"])
    data_store.created["data_scope_id"] = scope_id
    assert_ok(get_json(client, f"/sys/data-scopes/{scope_id}", token_headers))
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}", token_headers, scope_payload | {"name": "API Scope"}))
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}/rules", token_headers, {"rules": [rule_id]}))
    assert_ok(delete_json(client, "/sys/data-scopes", token_headers, {"pks": [scope_id]}))
    assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))


def test_data_scope_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test data-scope write error branches."""
    scope_payload = {"name": "API Duplicate Data Scope", "status": 1}
    assert_ok(post_json(client, "/sys/data-scopes", token_headers, scope_payload))
    scope_id = find_created_id(client, "/sys/data-scopes", token_headers, "name", scope_payload["name"])

    duplicate = client.post("/sys/data-scopes", headers=token_headers, json=scope_payload)
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_update = client.put(
        "/sys/data-scopes/999999",
        headers=token_headers,
        json={"name": "Missing Scope", "status": 1},
    )
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    assert_ok(post_json(client, "/sys/data-scopes", token_headers, {"name": "API Scope Rename Target", "status": 1}))
    rename_id = find_created_id(client, "/sys/data-scopes", token_headers, "name", "API Scope Rename Target")
    duplicate_update = client.put(f"/sys/data-scopes/{rename_id}", headers=token_headers, json=scope_payload)
    assert duplicate_update.status_code == 409
    assert_error(duplicate_update.json(), 409)

    delete_missing = client.request("DELETE", "/sys/data-scopes", headers=token_headers, json={"pks": [999999]})
    assert delete_missing.status_code == 200
    assert_error(delete_missing.json(), 400)
    assert_ok(delete_json(client, "/sys/data-scopes", token_headers, {"pks": [scope_id, rename_id]}))
