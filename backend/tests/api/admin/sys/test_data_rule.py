"""Test data-rule router APIs."""

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


def data_rule_payload(name: str = "API Data Rule") -> dict[str, object]:
    """Build a data-rule payload."""
    return {
        "name": name,
        "model": "Dept",
        "column": "name",
        "operator": 0,
        "expression": 0,
        "value": "测试",
    }


def test_data_rule_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded data-rule read APIs."""
    assert_ok(get_json(client, "/sys/data-rules/models", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/models/Dept/columns", token_headers))
    assert_page(get_json(client, "/sys/data-rules", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/all", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/1", token_headers))

    missing = client.get("/sys/data-rules/999999", headers=token_headers)
    assert missing.status_code == 404
    assert_error(missing.json(), 404)

    missing_model = client.get("/sys/data-rules/models/MissingModel/columns", headers=token_headers)
    assert missing_model.status_code == 404
    assert_error(missing_model.json(), 404)


def test_data_rule_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test data-rule write APIs."""
    payload = data_rule_payload()
    assert_ok(post_json(client, "/sys/data-rules", token_headers, payload))
    rule_id = find_created_id(client, "/sys/data-rules", token_headers, "name", payload["name"])
    data_store.created["data_rule_id"] = rule_id
    assert_ok(get_json(client, f"/sys/data-rules/{rule_id}", token_headers))
    assert_ok(put_json(client, f"/sys/data-rules/{rule_id}", token_headers, payload | {"value": "API"}))
    assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))


def test_data_rule_update_and_readback(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test data-rule update returns the changed rule through public reads."""
    rule_id: int | None = None
    try:
        payload = data_rule_payload("API Data Rule Readback")
        assert_ok(post_json(client, "/sys/data-rules", token_headers, payload))
        rule_id = find_created_id(client, "/sys/data-rules", token_headers, "name", payload["name"])
        updated = payload | {"operator": 1, "expression": 6, "value": "测试,API"}
        assert_ok(put_json(client, f"/sys/data-rules/{rule_id}", token_headers, updated))

        detail = get_json(client, f"/sys/data-rules/{rule_id}", token_headers)
        assert_ok(detail)
        data = detail["data"]
        assert isinstance(data, dict)
        assert data["operator"] == 1
        assert data["expression"] == 6
        assert data["value"] == "测试,API"
    finally:
        if rule_id is not None:
            assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))


def test_data_rule_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test data-rule write error branches."""
    duplicate_payload = data_rule_payload("API Duplicate Data Rule")
    assert_ok(post_json(client, "/sys/data-rules", token_headers, duplicate_payload))
    duplicate_id = find_created_id(client, "/sys/data-rules", token_headers, "name", duplicate_payload["name"])

    duplicate = client.post("/sys/data-rules", headers=token_headers, json=duplicate_payload)
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_update = client.put(
        "/sys/data-rules/999999",
        headers=token_headers,
        json=data_rule_payload("Missing Rule"),
    )
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    assert_ok(post_json(client, "/sys/data-rules", token_headers, data_rule_payload("API Rule Rename Target")))
    rename_id = find_created_id(client, "/sys/data-rules", token_headers, "name", "API Rule Rename Target")
    duplicate_update = client.put(
        f"/sys/data-rules/{rename_id}",
        headers=token_headers,
        json=data_rule_payload("API Duplicate Data Rule"),
    )
    assert duplicate_update.status_code == 409
    assert_error(duplicate_update.json(), 409)

    delete_missing = client.request("DELETE", "/sys/data-rules", headers=token_headers, json={"pks": [999999]})
    assert delete_missing.status_code == 200
    assert_error(delete_missing.json(), 400)
    assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [duplicate_id, rename_id]}))
