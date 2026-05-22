"""Shared helpers for black-box API tests."""

from starlette.testclient import TestClient

from tests.types import JsonValue, JsonObject, JsonPayload, QueryParamValue


def assert_ok(response_json: JsonObject) -> None:
    """Assert a standard successful API response."""
    assert response_json["code"] == 200


def assert_error(response_json: JsonObject, code: int) -> None:
    """Assert a standard error API response."""
    assert response_json["code"] == code
    assert isinstance(response_json["msg"], str)


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
        result.append(item)
    return result


def response_json(response: object) -> JsonObject:
    """Assert and return a JSON object response."""
    assert isinstance(response, dict)
    return {key: json_value(value) for key, value in response.items() if isinstance(key, str)}


def json_value(value: object) -> JsonValue:
    """Assert and return a JSON-compatible value."""
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items() if isinstance(key, str)}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    assert value is None or isinstance(value, str | int | float | bool)
    return value


def get_json(client: TestClient, path: str, headers: dict[str, str], **params: QueryParamValue) -> JsonObject:
    """GET a JSON API endpoint."""
    response = client.get(path, headers=headers, params={k: v for k, v in params.items() if v is not None})
    assert response.status_code == 200
    return response_json(response.json())


def post_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload) -> JsonObject:
    """POST a JSON API endpoint."""
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 200
    return response_json(response.json())


def put_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload = None) -> JsonObject:
    """PUT a JSON API endpoint."""
    response = client.put(path, headers=headers, json=payload)
    assert response.status_code == 200
    return response_json(response.json())


def delete_json(client: TestClient, path: str, headers: dict[str, str], payload: JsonPayload = None) -> JsonObject:
    """DELETE a JSON API endpoint."""
    response = client.request("DELETE", path, headers=headers, json=payload)
    assert response.status_code == 200
    return response_json(response.json())


def find_created_id(client: TestClient, path: str, headers: dict[str, str], key: str, value: object) -> int:
    """Find a created resource ID by querying a paginated endpoint."""
    assert value is None or isinstance(value, str | int | float | bool)
    items = assert_page(get_json(client, path, headers, **{key: value}))
    matches = [item for item in items if item[key] == value]
    assert matches
    created_id = matches[0]["id"]
    assert isinstance(created_id, str | int | float)
    return int(created_id)


def post_multipart(
    client: TestClient,
    path: str,
    headers: dict[str, str],
    *,
    files: dict[str, tuple[str, bytes, str]],
    params: dict[str, str | int] | None = None,
) -> JsonObject:
    """POST a multipart API endpoint."""
    response = client.post(path, headers=headers, params=params, files=files)
    assert response.status_code == 200
    return response_json(response.json())
