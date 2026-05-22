"""Test S3 file router APIs."""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from starlette.testclient import TestClient

from tests.types import JsonObject
from tests.conftest import DataStore
from tests.api.helpers import assert_ok, post_json, delete_json, assert_error, post_multipart, find_created_id


def object_filename_from_backend_url(url: str) -> str:
    """Return the filename portion from a backend proxy URL."""
    path = unquote(urlparse(url).path.rstrip("/"))
    filename = PurePosixPath(path).name
    assert filename
    return filename


def api_path_from_backend_url(url: str, api_v1_path: str) -> str:
    """Return the TestClient path for a backend API URL."""
    assert url.startswith(api_v1_path)
    return url.removeprefix(api_v1_path)


def upload_url(response_json: JsonObject) -> str:
    """Return upload URL from a standard API response."""
    data = response_json["data"]
    assert isinstance(data, dict)
    url = data["url"]
    assert isinstance(url, str)
    return url


def test_s3_file_upload_against_rustfs(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test object upload through the S3 file API using a real RustFS backend."""
    backend_settings = data_store.backend_settings
    payload = {
        "name": "api-s3-rustfs",
        "endpoint": backend_settings["object_storage_default_endpoint"],
        "access_key": backend_settings["object_storage_default_access_key"],
        "secret_key": backend_settings["object_storage_default_secret_key"],
        "bucket": backend_settings["object_storage_default_bucket"],
        "prefix": "api-tests",
        "region": backend_settings["object_storage_default_region"],
        "remark": "api",
    }
    assert_ok(post_json(client, "/s3/storages", token_headers, payload))
    storage_id = find_created_id(client, "/s3/storages", token_headers, "name", payload["name"])
    data_store.created["s3_rustfs_storage_id"] = storage_id

    body = post_multipart(
        client,
        "/s3/files/upload",
        token_headers,
        params={"storage": storage_id},
        files={"file": ("report.txt", b"hello-rustfs", "text/plain")},
    )
    assert_ok(body)
    url = upload_url(body)
    api_v1_path = backend_settings["api_v1_path"]
    assert url.startswith(f"{api_v1_path}/s3/files/path/{storage_id}/report_")
    assert not url.startswith(("http://", "https://"))
    assert url.endswith(".txt")
    assert object_filename_from_backend_url(url).startswith("report_")
    response = client.get(api_path_from_backend_url(url, api_v1_path), headers=token_headers)
    assert response.status_code == 200
    assert response.content == b"hello-rustfs"
    assert_ok(delete_json(client, "/s3/storages", token_headers, {"pks": [storage_id]}))


def test_s3_file_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test S3 file API errors through public endpoints."""
    upload_missing_storage = client.post(
        "/s3/files/upload",
        headers=token_headers,
        params={"storage": 999999},
        files={"file": ("missing.txt", b"data", "text/plain")},
    )
    assert upload_missing_storage.status_code == 404
    assert_error(upload_missing_storage.json(), 404)

    download_missing_storage = client.get("/s3/files/path/999999/missing.txt", headers=token_headers)
    assert download_missing_storage.status_code == 404
    assert_error(download_missing_storage.json(), 404)

    empty_upload = client.post(
        "/sys/files/upload",
        headers=token_headers,
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty_upload.status_code == 400
    assert_error(empty_upload.json(), 400)
