"""Test dict-type router APIs."""

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


def test_dict_type_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test dictionary type CRUD APIs."""
    payload = {"name": "API Dict", "code": "api_dict", "remark": "api"}
    assert_page(get_json(client, "/sys/dict-types", token_headers))
    assert_page(get_json(client, "/sys/dict-types", token_headers, name="测试", code="test"))
    assert_ok(get_json(client, "/sys/dict-types/all", token_headers))
    assert_ok(post_json(client, "/sys/dict-types", token_headers, payload))
    dict_type_id = find_created_id(client, "/sys/dict-types", token_headers, "code", payload["code"])
    data_store.created["dict_type_id"] = dict_type_id

    assert_ok(get_json(client, f"/sys/dict-types/{dict_type_id}", token_headers))
    assert_ok(
        put_json(client, f"/sys/dict-types/{dict_type_id}", token_headers, payload | {"name": "API Dict Updated"})
    )
    assert_ok(delete_json(client, "/sys/dict-types", token_headers, {"pks": [dict_type_id]}))


def test_dict_type_missing(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test dict-type not-found response."""
    response = client.get("/sys/dict-types/999999", headers=token_headers)
    assert response.status_code == 404
    assert_error(response.json(), 404)

    payload = {"name": "重复字典", "code": "api_duplicate_dict_type", "remark": "api"}
    assert_ok(post_json(client, "/sys/dict-types", token_headers, payload))
    duplicate = client.post("/sys/dict-types", headers=token_headers, json=payload)
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    assert_ok(
        post_json(
            client,
            "/sys/dict-types",
            token_headers,
            {"name": "重命名字典", "code": "api_rename_dict", "remark": "api"},
        )
    )
    rename_id = find_created_id(client, "/sys/dict-types", token_headers, "code", "api_rename_dict")
    duplicate_update = client.put(f"/sys/dict-types/{rename_id}", headers=token_headers, json=payload)
    assert duplicate_update.status_code == 409
    assert_error(duplicate_update.json(), 409)

    missing_update = client.put(
        "/sys/dict-types/999999",
        headers=token_headers,
        json={"name": "Missing", "code": "missing"},
    )
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    delete_missing = client.request("DELETE", "/sys/dict-types", headers=token_headers, json={"pks": [999999]})
    assert delete_missing.status_code == 200
    assert_error(delete_missing.json(), 400)
    empty_delete = client.request("DELETE", "/sys/dict-types", headers=token_headers, json={"pks": []})
    assert empty_delete.status_code == 200
    assert_error(empty_delete.json(), 400)
    assert_ok(delete_json(client, "/sys/dict-types", token_headers, {"pks": [rename_id]}))
