"""Test system file router APIs."""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from starlette.testclient import TestClient

from tests.types import JsonObject
from tests.conftest import DataStore
from tests.api.helpers import assert_ok, post_multipart


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


def test_system_file_upload_uses_default_object_storage(
    client: TestClient,
    token_headers: dict[str, str],
    data_store: DataStore,
) -> None:
    """Test system file upload through the default RustFS-backed object storage."""
    body = post_multipart(
        client,
        "/sys/files/upload",
        token_headers,
        files={"file": ("avatar.png", b"fake-png-bytes", "image/png")},
    )
    assert_ok(body)
    url = upload_url(body)
    api_v1_path = data_store.backend_settings["api_v1_path"]
    assert url.startswith(f"{api_v1_path}/sys/files/path/avatar_")
    assert not url.startswith(("http://", "https://"))
    assert url.endswith(".png")
    assert object_filename_from_backend_url(url).startswith("avatar_")
    response = client.get(api_path_from_backend_url(url, api_v1_path), headers=token_headers)
    assert response.status_code == 200
    assert response.content == b"fake-png-bytes"
