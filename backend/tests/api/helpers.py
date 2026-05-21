"""Shared helpers for black-box API tests."""

from starlette.testclient import TestClient

from tests.types import JsonObject, JsonPayload, QueryParamValue


def assert_ok(response_json: JsonObject) -> None:
    """Assert a standard successful API response."""
    assert response_json["code"] == 200


def assert_page(response_json: JsonObject) -> list[JsonObject]:
    """Assert a standard page response and return items."""
    assert_ok(response_json)
    data = response_json["data"]
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    items = data["items"]
    assert isinstance(items, list)
    result: list[JsonObject] = []
    for item in items:
        assert isinstance(item, dict)
        result.append(JsonObject(item))
    return result


def get_json(client: TestClient, path: str, headers: dict[str, str], **params: QueryParamValue) -> JsonObject:
    """GET a JSON API endpoint."""
    response = client.get(path, headers=headers, params={k: v for k, v in params.items() if v is not None})
    assert response.status_code == 200
    return JsonObject(response.json())


def post_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload) -> JsonObject:
    """POST a JSON API endpoint."""
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 200
    return JsonObject(response.json())


def put_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload = None) -> JsonObject:
    """PUT a JSON API endpoint."""
    response = client.put(path, headers=headers, json=payload)
    assert response.status_code == 200
    return JsonObject(response.json())


def delete_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload = None) -> JsonObject:
    """DELETE a JSON API endpoint."""
    response = client.request("DELETE", path, headers=headers, json=payload)
    assert response.status_code == 200
    return JsonObject(response.json())


def find_created_id(client: TestClient, path: str, headers: dict[str, str], key: str, value: object) -> int:
    """Find a created resource ID by querying a paginated endpoint."""
    assert value is None or isinstance(value, str | int | float | bool)
    items = assert_page(get_json(client, path, headers, **{key: value}))
    matches = [item for item in items if item[key] == value]
    assert matches
    created_id = matches[0]["id"]
    assert isinstance(created_id, str | int | float)
    return int(created_id)
