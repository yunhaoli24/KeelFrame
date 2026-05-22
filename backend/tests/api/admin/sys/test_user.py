"""Test user router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import get_json, put_json, assert_ok, post_json, assert_page, delete_json, assert_error


def user_payload(username: str = "api_user") -> dict[str, object]:
    """Build a user payload."""
    return {
        "username": username,
        "password": "123456",
        "nickname": "API User",
        "email": f"{username}@example.com",
        "phone": "13900000001",
        "dept_id": 1,
        "roles": [1],
    }


def test_current_user(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test current user API."""
    me = get_json(client, "/sys/users/me", token_headers)
    assert_ok(me)
    assert me["data"]["username"] == "admin"


def test_user_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded user query APIs."""
    users = get_json(client, "/sys/users", token_headers, username="admin")
    assert any(item["username"] == "admin" for item in assert_page(users))
    assert_page(get_json(client, "/sys/users", token_headers, dept=1, phone="13800138000", status=1))

    user_detail = get_json(client, "/sys/users/1", token_headers)
    assert_ok(user_detail)
    assert user_detail["data"]["username"] == "admin"

    user_roles = get_json(client, "/sys/users/1/roles", token_headers)
    assert_ok(user_roles)
    assert user_roles["data"]

    for path in ("/sys/users/999999", "/sys/users/999999/roles"):
        response = client.get(path, headers=token_headers)
        assert response.status_code == 404
        assert_error(response.json(), 404)


def test_user_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test user creation, update, permission toggles, password reset, and deletion."""
    username = "api_user"
    payload = user_payload(username)
    create_body = post_json(client, "/sys/users", token_headers, payload)
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])
    data_store.created["user_id"] = user_id

    assert_ok(get_json(client, f"/sys/users/{user_id}", token_headers))
    update_payload = payload | {"nickname": "API User Updated", "phone": "13900000002"}
    assert_ok(put_json(client, f"/sys/users/{user_id}", token_headers, update_payload))
    assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=staff", token_headers))
    new_password = "abc123"  # noqa: S105
    assert_ok(put_json(client, f"/sys/users/{user_id}/password", token_headers, {"password": new_password}))

    data_store.created["api_user_headers"] = login_headers(client, username, new_password)
    assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_admin_reset_password_success_keeps_existing_access_token(
    client: TestClient, token_headers: dict[str, str]
) -> None:
    """Test admin password reset success through public APIs."""
    username = "api_admin_reset_password_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        old_headers = login_headers(client, username, "123456")
        assert_ok(get_json(client, "/sys/users/me", old_headers))

        assert_ok(put_json(client, f"/sys/users/{user_id}/password", token_headers, {"password": "abc123"}))

        still_valid = get_json(client, "/sys/users/me", old_headers)
        assert_ok(still_valid)
        assert still_valid["data"]["username"] == username

        new_headers = login_headers(client, username, "abc123")
        me = get_json(client, "/sys/users/me", new_headers)
        assert_ok(me)
        assert me["data"]["username"] == username
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_created_normal_user_has_seed_role_read_access(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test a public-created normal user can use JWT-only read APIs."""
    username = "api_normal_rbac_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])
    data_store.created["api_normal_rbac_user_id"] = user_id

    try:
        headers = login_headers(client, username, "123456")
        me = get_json(client, "/sys/users/me", headers)
        assert_ok(me)
        assert me["data"]["username"] == username

        sidebar = get_json(client, "/sys/menus/sidebar", headers)
        assert_ok(sidebar)
        assert isinstance(sidebar["data"], list)
        assert sidebar["data"]

        depts = get_json(client, "/sys/depts", headers)
        assert_ok(depts)
        assert isinstance(depts["data"], list)

        forbidden = client.post("/sys/roles", headers=headers, json={"name": "Normal User Role", "status": 1})
        assert forbidden.status_code == 403
        assert_error(forbidden.json(), 403)
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_created_user_staff_and_superuser_permission_flow(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test public permission toggles promote a user from staff to superuser."""
    username = "api_promoted_admin"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])
    data_store.created["api_promoted_admin_id"] = user_id
    managed_user_id: int | None = None

    try:
        assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=staff", token_headers))
        staff_headers = login_headers(client, username, "123456")
        staff_forbidden = client.post("/sys/users", headers=staff_headers, json=user_payload("staff_forbidden_user"))
        assert staff_forbidden.status_code == 403
        assert_error(staff_forbidden.json(), 403)

        assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=superuser", token_headers))
        superuser_headers = login_headers(client, username, "123456")
        managed_user = post_json(client, "/sys/users", superuser_headers, user_payload("api_superuser_created_user"))
        assert_ok(managed_user)
        managed_user_id = int(managed_user["data"]["id"])

        detail = get_json(client, f"/sys/users/{managed_user_id}", superuser_headers)
        assert_ok(detail)
        assert detail["data"]["username"] == "api_superuser_created_user"
    finally:
        if managed_user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{managed_user_id}", token_headers))
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_user_permission_toggles(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test user permission toggles exposed by the public API."""
    username = "api_permission_user"
    payload = user_payload(username)
    create_body = post_json(client, "/sys/users", token_headers, payload)
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    for permission_type in ("staff", "status", "multi_login", "superuser"):
        assert_ok(
            put_json(client, f"/sys/users/{user_id}/permissions?permission_type={permission_type}", token_headers)
        )

    assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_user_status_toggle_rejects_existing_token(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test disabling a user rejects access with an existing token."""
    username = "api_status_toggle_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        headers = login_headers(client, username, "123456")
        assert_ok(get_json(client, "/sys/users/me", headers))

        assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=status", token_headers))
        disabled = client.get("/sys/users/me", headers=headers)
        assert disabled.status_code == 403
        assert_error(disabled.json(), 403)
    finally:
        detail = client.get(f"/sys/users/{user_id}", headers=token_headers)
        if detail.status_code == 200 and detail.json()["data"]["status"] == 0:
            assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type=status", token_headers))
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_user_multi_login_false_invalidates_old_token(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test a non-multi-login user's second login invalidates the old token."""
    username = "api_multi_login_token_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        first_headers = login_headers(client, username, "123456")
        assert_ok(get_json(client, "/sys/users/me", first_headers))

        second_headers = login_headers(client, username, "123456")
        assert_ok(get_json(client, "/sys/users/me", second_headers))

        stale = client.get("/sys/users/me", headers=first_headers)
        assert stale.status_code == 401
        assert_error(stale.json(), 401)
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_non_superuser_cannot_use_superuser_user_apis(client: TestClient, data_store: DataStore) -> None:
    """Test superuser-only user APIs reject a normal user."""
    headers = data_store.test_headers or login_headers(client, "test", "123456")
    create_response = client.post("/sys/users", headers=headers, json=user_payload("normal_forbidden"))
    assert create_response.status_code == 403
    assert_error(create_response.json(), 403)

    update_response = client.put("/sys/users/1", headers=headers, json=user_payload("normal_forbidden"))
    assert update_response.status_code == 403
    assert_error(update_response.json(), 403)

    reset_response = client.put("/sys/users/1/password", headers=headers, json={"password": "abc123"})
    assert reset_response.status_code == 403
    assert_error(reset_response.json(), 403)


def test_profile_update_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test current-user profile update APIs."""
    assert_ok(put_json(client, "/sys/users/me/nickname", token_headers, {"nickname": "用户666"}))
    assert_ok(put_json(client, "/sys/users/me/avatar", token_headers, {"avatar": "https://example.com/avatar.png"}))


def test_created_user_profile_update_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test created user can update own profile through public APIs."""
    username = "api_profile_update_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        headers = login_headers(client, username, "123456")
        assert_ok(put_json(client, "/sys/users/me/nickname", headers, {"nickname": "API Profile Updated"}))
        assert_ok(put_json(client, "/sys/users/me/avatar", headers, {"avatar": "https://example.com/profile.png"}))

        me = get_json(client, "/sys/users/me", headers)
        assert_ok(me)
        assert me["data"]["nickname"] == "API Profile Updated"
        assert me["data"]["avatar"] == "https://example.com/profile.png"
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_user_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test user router error branches."""
    empty_password = client.post(
        "/sys/users",
        headers=token_headers,
        json=user_payload("api_empty_password_user") | {"password": ""},
    )
    assert empty_password.status_code == 400
    assert_error(empty_password.json(), 400)

    missing_dept = client.post(
        "/sys/users",
        headers=token_headers,
        json=user_payload("api_missing_dept_user") | {"dept_id": 999999},
    )
    assert missing_dept.status_code == 404
    assert_error(missing_dept.json(), 404)

    duplicate = client.post("/sys/users", headers=token_headers, json=user_payload("admin"))
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_role = client.post(
        "/sys/users",
        headers=token_headers,
        json=user_payload("api_missing_role") | {"roles": [999999]},
    )
    assert missing_role.status_code == 404
    assert_error(missing_role.json(), 404)

    missing_update = client.put("/sys/users/999999", headers=token_headers, json=user_payload("missing_user_update"))
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    missing_reset = client.put("/sys/users/999999/password", headers=token_headers, json={"password": "abc123"})
    assert missing_reset.status_code == 404
    assert_error(missing_reset.json(), 404)

    self_permission = client.put("/sys/users/1/permissions?permission_type=staff", headers=token_headers)
    assert self_permission.status_code == 403
    assert_error(self_permission.json(), 403)

    missing_permission = client.put("/sys/users/999999/permissions?permission_type=staff", headers=token_headers)
    assert missing_permission.status_code == 404
    assert_error(missing_permission.json(), 404)

    missing_delete = client.request("DELETE", "/sys/users/999999", headers=token_headers)
    assert missing_delete.status_code == 404
    assert_error(missing_delete.json(), 404)

    captcha_response = client.post("/emails/captcha", headers=token_headers, json={"recipients": "api@example.com"})
    assert captcha_response.status_code == 200
    assert_ok(captcha_response.json())

    wrong_captcha = client.put(
        "/sys/users/me/email",
        headers=token_headers,
        json={"email": "api_email@example.com", "captcha": "000000"},
    )
    assert wrong_captcha.status_code == 400
    assert_error(wrong_captcha.json(), 40001)

    password_response = client.put(
        "/sys/users/me/password",
        headers=token_headers,
        json={"old_password": "wrong", "new_password": "abc123", "confirm_password": "abc123"},
    )
    assert password_response.status_code == 400
    assert_error(password_response.json(), 400)


def test_user_update_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test user update validation branches through the public API."""
    first_user_id: int | None = None
    second_user_id: int | None = None
    try:
        first = post_json(client, "/sys/users", token_headers, user_payload("api_update_source_user"))
        assert_ok(first)
        first_user_id = int(first["data"]["id"])

        second = post_json(client, "/sys/users", token_headers, user_payload("api_update_target_user"))
        assert_ok(second)
        second_user_id = int(second["data"]["id"])

        duplicate_username = client.put(
            f"/sys/users/{second_user_id}",
            headers=token_headers,
            json=user_payload("api_update_source_user"),
        )
        assert duplicate_username.status_code == 409
        assert_error(duplicate_username.json(), 409)

        missing_dept = client.put(
            f"/sys/users/{second_user_id}",
            headers=token_headers,
            json=user_payload("api_update_target_user") | {"dept_id": 999999},
        )
        assert missing_dept.status_code == 404
        assert_error(missing_dept.json(), 404)

        missing_role = client.put(
            f"/sys/users/{second_user_id}",
            headers=token_headers,
            json=user_payload("api_update_target_user") | {"roles": [999999]},
        )
        assert missing_role.status_code == 404
        assert_error(missing_role.json(), 404)
    finally:
        if second_user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{second_user_id}", token_headers))
        if first_user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{first_user_id}", token_headers))


def test_current_user_password_confirm_mismatch(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test current-user password confirmation validation through login token auth."""
    username = "api_password_confirm_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        headers = login_headers(client, username, "123456")
        response = client.put(
            "/sys/users/me/password",
            headers=headers,
            json={"old_password": "123456", "new_password": "abc123", "confirm_password": "abc124"},
        )
        assert response.status_code == 400
        assert_error(response.json(), 400)
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))


def test_current_user_password_update_success_invalidates_old_token(
    client: TestClient, token_headers: dict[str, str]
) -> None:
    """Test current-user password update success through public APIs."""
    username = "api_password_update_success_user"
    create_body = post_json(client, "/sys/users", token_headers, user_payload(username))
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])

    try:
        headers = login_headers(client, username, "123456")
        response = client.put(
            "/sys/users/me/password",
            headers=headers,
            json={"old_password": "123456", "new_password": "abc123", "confirm_password": "abc123"},
        )
        assert response.status_code == 200
        assert_ok(response.json())

        stale = client.get("/sys/users/me", headers=headers)
        assert stale.status_code == 401
        assert_error(stale.json(), 401)

        new_headers = login_headers(client, username, "abc123")
        me = get_json(client, "/sys/users/me", new_headers)
        assert_ok(me)
        assert me["data"]["username"] == username
    finally:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))
