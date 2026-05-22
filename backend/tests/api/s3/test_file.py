"""Test S3 file router APIs."""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from starlette.testclient import TestClient

from tests.types import JsonObject
from tests.conftest import DataStore, login_headers
from tests.api.helpers import (
    get_json,
    put_json,
    assert_ok,
    post_json,
    assert_page,
    delete_json,
    assert_error,
    post_multipart,
)


API_V1_PATH = "/api/v1"


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


def file_id_from_backend_url(url: str, api_v1_path: str) -> int:
    """Return file record ID from a backend proxy URL."""
    parts = api_path_from_backend_url(url, api_v1_path).split("/")
    return int(parts[4])


def s3_permission_menu_payload(index: int, permission: str) -> dict[str, object]:
    """Build a hidden button menu payload for S3 file permissions."""
    suffix = permission.rsplit(":", maxsplit=1)[-1]
    return {
        "title": f"API S3 File {suffix.title()}",
        "name": f"ApiS3File{suffix.title()}{index}",
        "path": None,
        "parent_id": 1,
        "sort": 0,
        "icon": None,
        "type": 2,
        "component": None,
        "perms": permission,
        "status": 1,
        "display": 0,
        "cache": 1,
        "link": None,
        "remark": "api",
    }


def create_s3_permission_role(client: TestClient, token_headers: dict[str, str]) -> tuple[int, list[int]]:
    """Create a role with S3 file permissions."""
    permissions = ["s3:file:upload", "s3:file:list", "s3:file:detail", "s3:file:download"]
    menu_ids: list[int] = []
    for index, permission in enumerate(permissions, start=1):
        payload = s3_permission_menu_payload(index, permission)
        assert_ok(post_json(client, "/sys/menus", token_headers, payload))
        menu = get_json(client, "/sys/menus", token_headers, title=payload["title"])
        matches = [item for item in menu["data"] if item["title"] == payload["title"]]
        assert matches
        menu_ids.append(int(matches[0]["id"]))

    role_payload = {"name": "API S3 File Role", "status": 1, "is_filter_scopes": True, "remark": "api"}
    assert_ok(post_json(client, "/sys/roles", token_headers, role_payload))
    roles = assert_page(get_json(client, "/sys/roles", token_headers, name=role_payload["name"]))
    matches = [item for item in roles if item["name"] == role_payload["name"]]
    assert matches
    role_id = int(matches[0]["id"])
    assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", token_headers, {"menus": menu_ids}))
    assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", token_headers, {"scopes": [1]}))
    return role_id, menu_ids


def test_s3_file_upload_against_rustfs(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test object upload through the S3 file API using login-token authorization."""
    backend_settings = data_store.backend_settings
    body = post_multipart(
        client,
        "/s3/files/upload",
        token_headers,
        files={"file": ("report.txt", b"hello-rustfs", "text/plain")},
    )
    assert_ok(body)
    url = upload_url(body)
    api_v1_path = backend_settings["api_v1_path"]
    assert url.startswith(f"{api_v1_path}/s3/files/path/")
    assert not url.startswith(("http://", "https://"))
    assert url.endswith(".txt")
    assert object_filename_from_backend_url(url).startswith("report_")

    files = assert_page(get_json(client, "/s3/files", token_headers))
    uploaded = [item for item in files if item["url"] == url]
    assert uploaded
    assert uploaded[0]["user_id"] == data_store.admin_user_id
    assert uploaded[0]["original_filename"] == "report.txt"
    assert uploaded[0]["content_type"] == "text/plain"
    assert uploaded[0]["size"] == len(b"hello-rustfs")
    file_id = file_id_from_backend_url(url, api_v1_path)
    detail = get_json(client, f"/s3/files/{file_id}", token_headers)
    assert_ok(detail)
    assert detail["data"]["url"] == url

    response = client.get(api_path_from_backend_url(url, api_v1_path), headers=token_headers)
    assert response.status_code == 200
    assert response.content == b"hello-rustfs"


def test_s3_file_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test S3 file API errors through public endpoints."""
    empty_upload = client.post(
        "/sys/files/upload",
        headers=token_headers,
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty_upload.status_code == 400
    assert_error(empty_upload.json(), 400)

    download_missing_file = client.get("/s3/files/path/999999/missing.txt", headers=token_headers)
    assert download_missing_file.status_code == 404
    assert_error(download_missing_file.json(), 404)

    body = post_multipart(
        client,
        "/s3/files/upload",
        headers=token_headers,
        files={"file": ("mismatch.txt", b"data", "text/plain")},
    )
    url = upload_url(body)
    file_id = file_id_from_backend_url(url, API_V1_PATH)
    mismatch = client.get(f"/s3/files/path/{file_id}/wrong.txt", headers=token_headers)
    assert mismatch.status_code == 404
    assert_error(mismatch.json(), 404)

    missing_detail = client.get("/s3/files/999999", headers=token_headers)
    assert missing_detail.status_code == 404
    assert_error(missing_detail.json(), 404)


def test_s3_file_owner_isolation(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test S3 file detail and download require file ownership for normal users."""
    username = "api_s3_file_owner"
    other_username = "api_s3_file_other"
    role_id: int | None = None
    menu_ids: list[int] = []
    user_id: int | None = None
    other_user_id: int | None = None

    try:
        role_id, menu_ids = create_s3_permission_role(client, token_headers)
        create_user = post_json(
            client,
            "/sys/users",
            token_headers,
            {
                "username": username,
                "password": "123456",
                "nickname": "API S3 Owner",
                "email": f"{username}@example.com",
                "phone": "13900000001",
                "dept_id": 1,
                "roles": [role_id],
            },
        )
        assert_ok(create_user)
        user_id = int(create_user["data"]["id"])
        assert_ok(client.put(f"/sys/users/{user_id}/permissions?permission_type=staff", headers=token_headers).json())
        owner_headers = login_headers(client, username, "123456")
        upload = post_multipart(
            client,
            "/s3/files/upload",
            owner_headers,
            files={"file": ("owned.txt", b"owned-by-user", "text/plain")},
        )
        url = upload_url(upload)
        file_id = file_id_from_backend_url(url, data_store.backend_settings["api_v1_path"])

        owner_detail = get_json(client, f"/s3/files/{file_id}", owner_headers)
        assert_ok(owner_detail)
        assert owner_detail["data"]["user_id"] == user_id

        owner_files = assert_page(get_json(client, "/s3/files", owner_headers))
        assert any(item["id"] == file_id for item in owner_files)

        other_user = post_json(
            client,
            "/sys/users",
            token_headers,
            {
                "username": other_username,
                "password": "123456",
                "nickname": "API S3 Other",
                "email": f"{other_username}@example.com",
                "phone": "13900000002",
                "dept_id": 1,
                "roles": [role_id],
            },
        )
        assert_ok(other_user)
        other_user_id = int(other_user["data"]["id"])
        assert_ok(
            client.put(f"/sys/users/{other_user_id}/permissions?permission_type=staff", headers=token_headers).json()
        )
        other_headers = login_headers(client, other_username, "123456")
        forbidden_detail = client.get(f"/s3/files/{file_id}", headers=other_headers)
        assert forbidden_detail.status_code == 403
        assert_error(forbidden_detail.json(), 403)

        forbidden_download = client.get(api_path_from_backend_url(url, API_V1_PATH), headers=other_headers)
        assert forbidden_download.status_code == 403
        assert_error(forbidden_download.json(), 403)
    finally:
        if other_user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{other_user_id}", token_headers))
        if user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))
        if role_id is not None:
            assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))
        for menu_id in menu_ids:
            assert_ok(delete_json(client, f"/sys/menus/{menu_id}", token_headers))
