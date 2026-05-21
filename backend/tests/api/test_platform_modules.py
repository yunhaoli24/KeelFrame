"""Test platform module APIs through HTTP."""

from starlette.testclient import TestClient

from tests.conftest import DataStore
from tests.api.helpers import get_json, put_json, assert_ok, post_json, assert_page, delete_json, find_created_id


def test_config_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test config CRUD APIs."""
    payload = {
        "name": "API Config",
        "type": "api",
        "key": "API_CONFIG_KEY",
        "value": "enabled",
        "is_frontend": False,
        "remark": "api",
    }
    assert_page(get_json(client, "/sys/configs", token_headers))
    assert_ok(get_json(client, "/sys/configs/all", token_headers))
    assert_ok(post_json(client, "/sys/configs", token_headers, payload))
    config_id = find_created_id(client, "/sys/configs", token_headers, "name", payload["name"])
    data_store.created["config_id"] = config_id

    assert_ok(get_json(client, f"/sys/configs/{config_id}", token_headers))
    updated = payload | {"value": "disabled", "remark": "updated"}
    assert_ok(put_json(client, f"/sys/configs/{config_id}", token_headers, updated))
    assert_ok(put_json(client, "/sys/configs", token_headers, [updated | {"id": config_id}]))
    assert_ok(delete_json(client, "/sys/configs", token_headers, [config_id]))


def test_dict_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test dictionary CRUD APIs."""
    type_payload = {"name": "API Dict", "code": "api_dict", "remark": "api"}
    assert_page(get_json(client, "/sys/dict-types", token_headers))
    assert_ok(get_json(client, "/sys/dict-types/all", token_headers))
    assert_ok(post_json(client, "/sys/dict-types", token_headers, type_payload))
    dict_type_id = find_created_id(client, "/sys/dict-types", token_headers, "code", type_payload["code"])
    data_store.created["dict_type_id"] = dict_type_id

    assert_ok(get_json(client, f"/sys/dict-types/{dict_type_id}", token_headers))
    assert_ok(
        put_json(
            client,
            f"/sys/dict-types/{dict_type_id}",
            token_headers,
            type_payload | {"name": "API Dict Updated"},
        )
    )

    data_payload = {
        "type_id": dict_type_id,
        "label": "API Dict Data",
        "value": "api",
        "color": "blue",
        "sort": 1,
        "status": 1,
        "remark": "api",
    }
    assert_ok(post_json(client, "/sys/dict-datas", token_headers, data_payload))
    dict_data_id = find_created_id(client, "/sys/dict-datas", token_headers, "label", data_payload["label"])
    data_store.created["dict_data_id"] = dict_data_id

    assert_ok(get_json(client, f"/sys/dict-datas/{dict_data_id}", token_headers))
    assert_ok(get_json(client, "/sys/dict-datas/type-codes/api_dict", token_headers))
    assert_ok(put_json(client, f"/sys/dict-datas/{dict_data_id}", token_headers, data_payload | {"value": "api2"}))
    assert_ok(delete_json(client, "/sys/dict-datas", token_headers, {"pks": [dict_data_id]}))
    assert_ok(delete_json(client, "/sys/dict-types", token_headers, {"pks": [dict_type_id]}))


def test_notice_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test notice CRUD APIs."""
    payload = {"title": "API Notice", "type": 0, "status": 1, "content": "notice body"}
    assert_page(get_json(client, "/sys/notices", token_headers))
    assert_ok(post_json(client, "/sys/notices", token_headers, payload))
    notice_id = find_created_id(client, "/sys/notices", token_headers, "title", payload["title"])
    data_store.created["notice_id"] = notice_id

    assert_ok(get_json(client, f"/sys/notices/{notice_id}", token_headers))
    assert_ok(put_json(client, f"/sys/notices/{notice_id}", token_headers, payload | {"content": "updated"}))
    assert_ok(delete_json(client, "/sys/notices", token_headers, {"pks": [notice_id]}))


def test_s3_storage_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test S3 storage metadata CRUD APIs without touching object storage."""
    payload = {
        "name": "api-s3",
        "endpoint": "https://s3.example.com",
        "access_key": "access",
        "secret_key": "secret",
        "bucket": "bucket",
        "prefix": "prefix",
        "region": "us-east-1",
        "remark": "api",
    }
    assert_page(get_json(client, "/s3/storages", token_headers))
    assert_ok(post_json(client, "/s3/storages", token_headers, payload))
    storage_id = find_created_id(client, "/s3/storages", token_headers, "name", payload["name"])
    data_store.created["s3_storage_id"] = storage_id

    assert_ok(get_json(client, f"/s3/storages/{storage_id}", token_headers))
    assert_ok(put_json(client, f"/s3/storages/{storage_id}", token_headers, payload | {"remark": "updated"}))
    assert_ok(delete_json(client, "/s3/storages", token_headers, {"pks": [storage_id]}))
