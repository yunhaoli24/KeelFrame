"""Test write system APIs through the public HTTP boundary."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import assert_ok, get_json, put_json, post_json, delete_json, find_created_id


def test_user_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test user creation, update, permission toggles, password reset, and deletion."""
    username = "api_user"
    payload = {
        "username": username,
        "password": "123456",
        "nickname": "API User",
        "email": "api_user@example.com",
        "phone": "13900000001",
        "dept_id": 1,
        "roles": [1],
    }
    create_body = post_json(client, "/sys/users", token_headers, payload)
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])
    data_store.created["user_id"] = user_id

    assert_ok(get_json(client, f"/sys/users/{user_id}", token_headers))
    update_payload = payload | {"nickname": "API User Updated", "phone": "13900000002"}
    assert_ok(put_json(client, f"/sys/users/{user_id}", token_headers, update_payload))
    assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=staff", token_headers))
    new_password = "abc123"
    assert_ok(put_json(client, f"/sys/users/{user_id}/password", token_headers, {"password": new_password}))

    data_store.created["api_user_headers"] = login_headers(client, username, new_password)
    assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_profile_update_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test current-user profile update APIs."""
    assert_ok(put_json(client, "/sys/users/me/nickname", token_headers, {"nickname": "用户666"}))
    assert_ok(put_json(client, "/sys/users/me/avatar", token_headers, {"avatar": "https://example.com/avatar.png"}))


def test_role_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test role creation, relation updates, and deletion."""
    name = "API Role"
    assert_ok(post_json(client, "/sys/roles", token_headers, {"name": name, "status": 1, "remark": "api"}))
    role_id = find_created_id(client, "/sys/roles", token_headers, "name", name)
    data_store.created["role_id"] = role_id

    assert_ok(get_json(client, f"/sys/roles/{role_id}", token_headers))
    assert_ok(
        put_json(
            client,
            f"/sys/roles/{role_id}",
            token_headers,
            {"name": "API Role Updated", "status": 1, "is_filter_scopes": True, "remark": "api updated"},
        )
    )
    assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", token_headers, {"menus": [1, 2]}))
    assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", token_headers, {"scopes": [1]}))
    assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))


def test_menu_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test menu creation, update, and deletion."""
    title = "API Menu"
    payload = {
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
    assert_ok(post_json(client, "/sys/menus", token_headers, payload))
    menus = get_json(client, "/sys/menus", token_headers, title=title)
    assert_ok(menus)
    matches = [item for item in menus["data"] if item["title"] == title]
    assert matches
    menu_id = int(matches[0]["id"])
    data_store.created["menu_id"] = menu_id

    assert_ok(get_json(client, f"/sys/menus/{menu_id}", token_headers))
    assert_ok(put_json(client, f"/sys/menus/{menu_id}", token_headers, payload | {"title": "API Menu Updated"}))
    assert_ok(delete_json(client, f"/sys/menus/{menu_id}", token_headers))


def test_dept_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test department creation, update, and deletion."""
    payload = {
        "name": "API Dept",
        "parent_id": None,
        "sort": 10,
        "leader": "Tester",
        "phone": "13900000003",
        "email": "api_dept@example.com",
        "status": 1,
    }
    assert_ok(post_json(client, "/sys/depts", token_headers, payload))
    dept_id = int(get_json(client, "/sys/depts", token_headers, name="API Dept")["data"][0]["id"])
    data_store.created["dept_id"] = dept_id

    assert_ok(get_json(client, f"/sys/depts/{dept_id}", token_headers))
    assert_ok(put_json(client, f"/sys/depts/{dept_id}", token_headers, payload | {"leader": "Tester Updated"}))
    assert_ok(delete_json(client, f"/sys/depts/{dept_id}", token_headers))


def test_data_rule_and_scope_lifecycle(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test data rule and data scope write APIs."""
    rule_payload = {
        "name": "API Data Rule",
        "model": "Dept",
        "column": "name",
        "operator": 0,
        "expression": 0,
        "value": "测试",
    }
    assert_ok(post_json(client, "/sys/data-rules", token_headers, rule_payload))
    rule_id = find_created_id(client, "/sys/data-rules", token_headers, "name", rule_payload["name"])
    data_store.created["data_rule_id"] = rule_id
    assert_ok(get_json(client, f"/sys/data-rules/{rule_id}", token_headers))
    assert_ok(put_json(client, f"/sys/data-rules/{rule_id}", token_headers, rule_payload | {"value": "API"}))

    scope_payload = {"name": "API Data Scope", "status": 1}
    assert_ok(post_json(client, "/sys/data-scopes", token_headers, scope_payload))
    scope_id = find_created_id(client, "/sys/data-scopes", token_headers, "name", scope_payload["name"])
    data_store.created["data_scope_id"] = scope_id
    assert_ok(get_json(client, f"/sys/data-scopes/{scope_id}", token_headers))
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}", token_headers, scope_payload | {"name": "API Scope"}))
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}/rules", token_headers, {"rules": [rule_id]}))
    assert_ok(delete_json(client, "/sys/data-scopes", token_headers, {"pks": [scope_id]}))
    assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))
