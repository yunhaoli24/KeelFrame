"""Test config router APIs."""

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


def config_payload(key: str = "API_CONFIG_KEY") -> dict[str, object]:
    """Build a config payload."""
    return {
        "name": "API Config",
        "type": "api",
        "key": key,
        "value": "enabled",
        "is_frontend": False,
        "remark": "api",
    }


def test_config_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test config CRUD APIs."""
    payload = config_payload()
    assert_page(get_json(client, "/sys/configs", token_headers))
    assert_ok(get_json(client, "/sys/configs/all", token_headers))
    assert_ok(get_json(client, "/sys/configs/all", token_headers, config_type="api"))
    assert_ok(post_json(client, "/sys/configs", token_headers, payload))
    config_id = find_created_id(client, "/sys/configs", token_headers, "name", payload["name"])
    data_store.created["config_id"] = config_id

    assert_ok(get_json(client, f"/sys/configs/{config_id}", token_headers))
    updated = payload | {"value": "disabled", "remark": "updated"}
    assert_ok(put_json(client, f"/sys/configs/{config_id}", token_headers, updated))
    assert_ok(put_json(client, "/sys/configs", token_headers, [updated | {"id": config_id}]))
    assert_ok(delete_json(client, "/sys/configs", token_headers, [config_id]))


def test_config_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test config router error branches."""
    missing = client.get("/sys/configs/999999", headers=token_headers)
    assert missing.status_code == 404
    assert_error(missing.json(), 404)

    assert_ok(post_json(client, "/sys/configs", token_headers, config_payload("API_CONFIG_DUPLICATE")))
    duplicate = client.post("/sys/configs", headers=token_headers, json=config_payload("API_CONFIG_DUPLICATE"))
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_bulk = client.put(
        "/sys/configs",
        headers=token_headers,
        json=[config_payload("MISSING_CONFIG") | {"id": 999999}],
    )
    assert missing_bulk.status_code == 404
    assert_error(missing_bulk.json(), 404)

    assert_ok(post_json(client, "/sys/configs", token_headers, config_payload("API_CONFIG_RENAME_SOURCE")))
    source_id = find_created_id(client, "/sys/configs", token_headers, "key", "API_CONFIG_RENAME_SOURCE")
    conflict_update = client.put(
        f"/sys/configs/{source_id}",
        headers=token_headers,
        json=config_payload("API_CONFIG_DUPLICATE"),
    )
    assert conflict_update.status_code == 409
    assert_error(conflict_update.json(), 409)

    missing_update = client.put("/sys/configs/999999", headers=token_headers, json=config_payload("MISSING_UPDATE"))
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    bulk_conflict = client.put(
        "/sys/configs",
        headers=token_headers,
        json=[config_payload("API_CONFIG_DUPLICATE") | {"id": source_id}],
    )
    assert bulk_conflict.status_code == 409
    assert_error(bulk_conflict.json(), 409)

    empty_delete = client.request("DELETE", "/sys/configs", headers=token_headers, json=[])
    assert empty_delete.status_code == 200
    assert_error(empty_delete.json(), 400)
    assert_ok(delete_json(client, "/sys/configs", token_headers, [source_id]))
