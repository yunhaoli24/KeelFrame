"""Test S3 storage router APIs."""

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


def s3_storage_payload(name: str = "api-s3") -> dict[str, object]:
    """Build an S3 storage payload."""
    return {
        "name": name,
        "endpoint": "https://s3.example.com",
        "access_key": "access",
        "secret_key": "secret",
        "bucket": "bucket",
        "prefix": "prefix",
        "region": "us-east-1",
        "remark": "api",
    }


def test_s3_storage_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test S3 storage metadata CRUD APIs without touching object storage."""
    payload = s3_storage_payload()
    assert_page(get_json(client, "/s3/storages", token_headers))
    assert_ok(get_json(client, "/s3/storages/all", token_headers))
    assert_ok(post_json(client, "/s3/storages", token_headers, payload))
    storage_id = find_created_id(client, "/s3/storages", token_headers, "name", payload["name"])
    data_store.created["s3_storage_id"] = storage_id

    assert_ok(get_json(client, f"/s3/storages/{storage_id}", token_headers))
    assert_ok(put_json(client, f"/s3/storages/{storage_id}", token_headers, payload | {"remark": "updated"}))
    assert_ok(delete_json(client, "/s3/storages", token_headers, {"pks": [storage_id]}))


def test_s3_storage_missing(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test S3 storage not-found response."""
    response = client.get("/s3/storages/999999", headers=token_headers)
    assert response.status_code == 404
    assert_error(response.json(), 404)

    missing_delete = client.request("DELETE", "/s3/storages", headers=token_headers, json={"pks": [999999]})
    assert missing_delete.status_code == 200
    assert_error(missing_delete.json(), 400)

    missing_update = client.put("/s3/storages/999999", headers=token_headers, json=s3_storage_payload("missing-s3"))
    assert missing_update.status_code == 200
    assert_error(missing_update.json(), 400)
