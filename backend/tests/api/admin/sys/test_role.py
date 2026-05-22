"""Test role router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
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
from tests.api.admin.sys.test_user import user_payload


def test_role_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded role read APIs."""
    assert_page(get_json(client, "/sys/roles", token_headers))
    assert_page(get_json(client, "/sys/roles", token_headers, name="测试", status=1))

    role_detail = get_json(client, "/sys/roles/1", token_headers)
    assert_ok(role_detail)
    assert role_detail["data"]["name"] == "测试"

    assert_ok(get_json(client, "/sys/roles/all", token_headers))
    assert_ok(get_json(client, "/sys/roles/1/menus", token_headers))
    assert_ok(get_json(client, "/sys/roles/1/scopes", token_headers))

    for path in ("/sys/roles/999999", "/sys/roles/999999/menus", "/sys/roles/999999/scopes"):
        response = client.get(path, headers=token_headers)
        assert response.status_code == 404
        assert_error(response.json(), 404)


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


def test_role_rbac_rejects_non_staff(client: TestClient, data_store: DataStore) -> None:
    """Test RBAC non-staff rejection branch through public role APIs."""
    normal_headers = data_store.test_headers or login_headers(client, "test", "123456")
    non_staff = client.post("/sys/roles", headers=normal_headers, json={"name": "RBAC Non Staff", "status": 1})
    assert non_staff.status_code == 403
    assert_error(non_staff.json(), 403)


def test_created_role_menu_grants_read_access_only(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test a public-created role with menus grants read access without write access."""
    role_name = "API Menu Bound Role"
    assert_ok(post_json(client, "/sys/roles", token_headers, {"name": role_name, "status": 1, "remark": "api"}))
    role_id = find_created_id(client, "/sys/roles", token_headers, "name", role_name)
    username = "api_role_menu_user"
    user_id: int | None = None
    data_store.created["api_menu_bound_role_id"] = role_id

    try:
        assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", token_headers, {"menus": [1, 2, 3, 53]}))
        assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", token_headers, {"scopes": [1]}))
        create_body = post_json(client, "/sys/users", token_headers, user_payload(username) | {"roles": [role_id]})
        assert_ok(create_body)
        user_id = int(create_body["data"]["id"])

        headers = login_headers(client, username, "123456")
        sidebar = get_json(client, "/sys/menus/sidebar", headers)
        assert_ok(sidebar)
        assert isinstance(sidebar["data"], list)
        assert sidebar["data"]

        codes = get_json(client, "/auth/codes", headers)
        assert_ok(codes)
        assert isinstance(codes["data"], list)

        depts = get_json(client, "/sys/depts", headers)
        assert_ok(depts)
        assert isinstance(depts["data"], list)

        forbidden = client.post("/sys/roles", headers=headers, json={"name": "Menu Role Forbidden", "status": 1})
        assert forbidden.status_code == 403
        assert_error(forbidden.json(), 403)
    finally:
        if user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))
        assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))


def test_role_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test role router error branches."""
    duplicate = client.post("/sys/roles", headers=token_headers, json={"name": "测试", "status": 1, "remark": "api"})
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_update = client.put(
        "/sys/roles/999999",
        headers=token_headers,
        json={"name": "Missing Role", "status": 1, "is_filter_scopes": True, "remark": "api"},
    )
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    assert_ok(post_json(client, "/sys/roles", token_headers, {"name": "API Duplicate Update Role", "status": 1}))
    role_id = find_created_id(client, "/sys/roles", token_headers, "name", "API Duplicate Update Role")
    duplicate_update = client.put(
        f"/sys/roles/{role_id}",
        headers=token_headers,
        json={"name": "测试", "status": 1, "is_filter_scopes": True, "remark": "api"},
    )
    assert duplicate_update.status_code == 409
    assert_error(duplicate_update.json(), 409)
    assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))

    for path, payload in (
        ("/sys/roles/999999/menus", {"menus": [1]}),
        ("/sys/roles/999999/scopes", {"scopes": [1]}),
    ):
        response = client.put(path, headers=token_headers, json=payload)
        assert response.status_code == 404
        assert_error(response.json(), 404)

    missing_menu = client.put("/sys/roles/1/menus", headers=token_headers, json={"menus": [999999]})
    assert missing_menu.status_code == 404
    assert_error(missing_menu.json(), 404)

    missing_scope = client.put("/sys/roles/1/scopes", headers=token_headers, json={"scopes": [999999]})
    assert missing_scope.status_code == 404
    assert_error(missing_scope.json(), 404)

    missing_delete = client.request("DELETE", "/sys/roles", headers=token_headers, json={"pks": [999999]})
    assert missing_delete.status_code == 200
    assert_error(missing_delete.json(), 400)
