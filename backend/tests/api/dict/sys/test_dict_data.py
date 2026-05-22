"""Test dict-data router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore
from tests.api.helpers import get_json, put_json, assert_ok, post_json, delete_json, assert_error, find_created_id


def dict_data_payload(type_id: int, label: str = "API Dict Data") -> dict[str, object]:
    """Build a dict-data payload."""
    return {
        "type_id": type_id,
        "label": label,
        "value": "api",
        "color": "blue",
        "sort": 1,
        "status": 1,
        "remark": "api",
    }


def test_dict_data_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test dictionary data CRUD APIs."""
    type_payload = {"name": "API Dict For Data", "code": "api_dict_data", "remark": "api"}
    assert_ok(post_json(client, "/sys/dict-types", token_headers, type_payload))
    dict_type_id = find_created_id(client, "/sys/dict-types", token_headers, "code", type_payload["code"])
    data_store.created["dict_data_type_id"] = dict_type_id

    payload = dict_data_payload(dict_type_id)
    assert_ok(post_json(client, "/sys/dict-datas", token_headers, payload))
    dict_data_id = find_created_id(client, "/sys/dict-datas", token_headers, "label", payload["label"])
    data_store.created["dict_data_id"] = dict_data_id

    assert_ok(get_json(client, f"/sys/dict-datas/{dict_data_id}", token_headers))
    assert_ok(get_json(client, "/sys/dict-datas/type-codes/api_dict_data", token_headers))
    assert_ok(get_json(client, "/sys/dict-datas/all", token_headers))
    assert_ok(
        get_json(
            client,
            "/sys/dict-datas",
            token_headers,
            type_code="api_dict_data",
            label="API",
            value="api",
            status=1,
            type_id=dict_type_id,
        )
    )
    assert_ok(put_json(client, f"/sys/dict-datas/{dict_data_id}", token_headers, payload | {"value": "api2"}))
    assert_ok(delete_json(client, "/sys/dict-datas", token_headers, {"pks": [dict_data_id]}))
    assert_ok(delete_json(client, "/sys/dict-types", token_headers, {"pks": [dict_type_id]}))


def test_dict_data_missing(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test dict-data not-found responses."""
    for path in ("/sys/dict-datas/999999", "/sys/dict-datas/type-codes/missing"):
        response = client.get(path, headers=token_headers)
        assert response.status_code == 404
        assert_error(response.json(), 404)

    missing_type = client.post(
        "/sys/dict-datas",
        headers=token_headers,
        json=dict_data_payload(999999, "Missing Type Data"),
    )
    assert missing_type.status_code == 404
    assert_error(missing_type.json(), 404)

    type_payload = {"name": "API Dict Duplicate Data", "code": "api_dict_duplicate_data", "remark": "api"}
    assert_ok(post_json(client, "/sys/dict-types", token_headers, type_payload))
    dict_type_id = find_created_id(client, "/sys/dict-types", token_headers, "code", type_payload["code"])
    payload = dict_data_payload(dict_type_id, "Duplicate Dict Data")
    assert_ok(post_json(client, "/sys/dict-datas", token_headers, payload))
    dict_data_id = find_created_id(client, "/sys/dict-datas", token_headers, "label", payload["label"])
    duplicate = client.post("/sys/dict-datas", headers=token_headers, json=payload)
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_update = client.put("/sys/dict-datas/999999", headers=token_headers, json=payload)
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    missing_type_update = client.put(
        f"/sys/dict-datas/{dict_data_id}",
        headers=token_headers,
        json=payload | {"type_id": 999999},
    )
    assert missing_type_update.status_code == 404
    assert_error(missing_type_update.json(), 404)

    assert_ok(
        post_json(
            client,
            "/sys/dict-datas",
            token_headers,
            dict_data_payload(dict_type_id, "Duplicate Dict Data Target"),
        )
    )
    target_id = find_created_id(client, "/sys/dict-datas", token_headers, "label", "Duplicate Dict Data Target")
    duplicate_update = client.put(
        f"/sys/dict-datas/{dict_data_id}",
        headers=token_headers,
        json=payload | {"label": "Duplicate Dict Data Target"},
    )
    assert duplicate_update.status_code == 409
    assert_error(duplicate_update.json(), 409)

    delete_missing = client.request("DELETE", "/sys/dict-datas", headers=token_headers, json={"pks": [999999]})
    assert delete_missing.status_code == 200
    assert_error(delete_missing.json(), 400)
    assert_ok(delete_json(client, "/sys/dict-datas", token_headers, {"pks": [target_id]}))
    assert_ok(delete_json(client, "/sys/dict-datas", token_headers, {"pks": [dict_data_id]}))
    assert_ok(delete_json(client, "/sys/dict-types", token_headers, {"pks": [dict_type_id]}))
