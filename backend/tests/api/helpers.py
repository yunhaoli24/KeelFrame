"""Shared helpers for black-box API tests."""

from typing import Any

from starlette.testclient import TestClient


def assert_ok(response_json: dict[str, Any]) -> None:
    """Assert a standard successful API response."""
    assert response_json["code"] == 200


def assert_page(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Assert a standard page response and return items."""
    assert_ok(response_json)
    data = response_json["data"]
    assert "items" in data
    assert "total" in data
    return list(data["items"])


def get_json(client: TestClient, path: str, headers: dict[str, str], **params: Any) -> dict[str, Any]:
    """GET a JSON API endpoint."""
    response = client.get(path, headers=headers, params={k: v for k, v in params.items() if v is not None})
    assert response.status_code == 200
    return response.json()


def post_json(client: TestClient, path: str, headers: dict[str, str], payload: Any) -> dict[str, Any]:
    """POST a JSON API endpoint."""
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()


def put_json(client: TestClient, path: str, headers: dict[str, str], payload: Any = None) -> dict[str, Any]:
    """PUT a JSON API endpoint."""
    response = client.put(path, headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()


def delete_json(client: TestClient, path: str, headers: dict[str, str], payload: Any = None) -> dict[str, Any]:
    """DELETE a JSON API endpoint."""
    response = client.request("DELETE", path, headers=headers, json=payload)
    assert response.status_code == 200
    return response.json()


def find_created_id(client: TestClient, path: str, headers: dict[str, str], key: str, value: Any) -> int:
    """Find a created resource ID by querying a paginated endpoint."""
    items = assert_page(get_json(client, path, headers, **{key: value}))
    matches = [item for item in items if item[key] == value]
    assert matches
    return int(matches[0]["id"])
