"""Test menu router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import get_json, put_json, assert_ok, post_json, delete_json, assert_error


def menu_payload(title: str = "API Menu") -> dict[str, object]:
    """Build a menu payload."""
    return {
        "title": title,
        "name": "ApiMenu",
        "path": "/api-menu",
        "parent_id": None,
        "sort": 99,
        "icon": "lucide:test-tube",
        "type": 1,
        "component": "/test/api-menu",
        "perms": "sys:api-menu:view",
        "status": 1,
        "display": 1,
        "cache": 1,
        "link": None,
        "remark": "api",
    }


def test_menu_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded menu read APIs."""
    menus = get_json(client, "/sys/menus", token_headers)
    assert_ok(menus)
    assert menus["data"]

    filtered = get_json(client, "/sys/menus", token_headers, title="控制台", status=1)
    assert_ok(filtered)
    assert filtered["data"]

    sidebar = get_json(client, "/sys/menus/sidebar", token_headers)
    assert_ok(sidebar)
    assert sidebar["data"]

    menu_detail = get_json(client, "/sys/menus/1", token_headers)
    assert_ok(menu_detail)
    assert menu_detail["data"]["title"] == "控制台"

    missing = client.get("/sys/menus/999999", headers=token_headers)
    assert missing.status_code == 404
    assert_error(missing.json(), 404)


def test_menu_sidebar_for_normal_user(client: TestClient, data_store: DataStore) -> None:
    """Test normal-user sidebar branch through the public API."""
    headers = data_store.test_headers or login_headers(client, "test", "123456")
    sidebar = get_json(client, "/sys/menus/sidebar", headers)
    assert_ok(sidebar)
    assert isinstance(sidebar["data"], list)


def test_menu_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test menu creation, update, and deletion."""
    payload = menu_payload()
    assert_ok(post_json(client, "/sys/menus", token_headers, payload))
    menus = get_json(client, "/sys/menus", token_headers, title=payload["title"])
    assert_ok(menus)
    matches = [item for item in menus["data"] if item["title"] == payload["title"]]
    assert matches
    menu_id = int(matches[0]["id"])
    data_store.created["menu_id"] = menu_id

    assert_ok(get_json(client, f"/sys/menus/{menu_id}", token_headers))
    assert_ok(put_json(client, f"/sys/menus/{menu_id}", token_headers, payload | {"title": "API Menu Updated"}))
    assert_ok(delete_json(client, f"/sys/menus/{menu_id}", token_headers))


def test_menu_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test menu router error branches."""
    duplicate = client.post("/sys/menus", headers=token_headers, json=menu_payload("控制台"))
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_parent = client.post(
        "/sys/menus",
        headers=token_headers,
        json=menu_payload("API Missing Parent") | {"parent_id": 999999},
    )
    assert missing_parent.status_code == 404
    assert_error(missing_parent.json(), 404)

    missing_update = client.put("/sys/menus/999999", headers=token_headers, json=menu_payload("Missing Menu"))
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    assert_ok(post_json(client, "/sys/menus", token_headers, menu_payload("API Self Parent Menu")))
    menu_id = int(get_json(client, "/sys/menus", token_headers, title="API Self Parent Menu")["data"][0]["id"])
    self_parent = client.put(
        f"/sys/menus/{menu_id}",
        headers=token_headers,
        json=menu_payload("API Self Parent Menu") | {"parent_id": menu_id},
    )
    assert self_parent.status_code == 403
    assert_error(self_parent.json(), 403)
    assert_ok(delete_json(client, f"/sys/menus/{menu_id}", token_headers))

    child_delete = client.request("DELETE", "/sys/menus/1", headers=token_headers)
    assert child_delete.status_code == 409
    assert_error(child_delete.json(), 409)

    missing_delete = client.request("DELETE", "/sys/menus/999999", headers=token_headers)
    assert missing_delete.status_code == 200
    assert_error(missing_delete.json(), 400)
