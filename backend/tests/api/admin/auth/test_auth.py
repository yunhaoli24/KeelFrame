"""Test auth APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import put_json, assert_error
from tests.api.helpers import assert_ok as assert_standard_ok
from tests.api.rbac_helpers import cleanup_rbac, create_rbac_role, create_rbac_user, create_rbac_menus


def assert_ok(response_json: dict) -> None:
    """Assert a standard successful API response."""
    assert response_json["code"] == 200


def test_swagger_login(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test swagger login."""
    assert token_headers["Authorization"].startswith("Bearer ")
    assert data_store.admin_user_id == 1


def test_auth_codes(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test permission-code API."""
    response = client.get("/auth/codes", headers=token_headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert isinstance(body["data"], list)
    assert "sys:user:del" in body["data"]


def test_auth_codes_for_normal_user(client: TestClient, data_store: DataStore) -> None:
    """Test permission-code API for a non-superuser."""
    headers = data_store.test_headers or login_headers(client, "test", "123456")
    response = client.get("/auth/codes", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert isinstance(body["data"], list)


def test_auth_codes_reflect_created_role_menu_permissions(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test auth codes for a created non-superuser come from bound menus."""
    menu_ids: dict[str, int] = {}
    role_id: int | None = None
    user_id: int | None = None

    try:
        menu_ids = create_rbac_menus(client, token_headers, "directory", "role_menu", "menu_add_button")
        role_id = create_rbac_role(
            client,
            token_headers,
            "menu_add",
            menu_ids=[menu_ids["directory"], menu_ids["role_menu"], menu_ids["menu_add_button"]],
        )
        user_id, headers = create_rbac_user(client, token_headers, "menu_add", role_ids=[role_id], staff=True)

        response = client.get("/auth/codes", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert_ok(body)
        assert set(body["data"]) == {"sys:role:query", "sys:menu:add"}
    finally:
        cleanup_rbac(
            client,
            token_headers,
            user_ids=[user_id] if user_id is not None else [],
            role_ids=[role_id] if role_id is not None else [],
            menu_ids=menu_ids.values(),
        )


def test_login_with_wrong_password(client: TestClient) -> None:
    """Test login failure with a wrong password."""
    response = client.post("/auth/login/swagger", params={"username": "admin", "password": "wrong-password"})
    assert response.status_code == 403
    assert response.json()["code"] == 403


def test_login_failures_do_not_lock_before_threshold(client: TestClient) -> None:
    """Test login failure accounting still allows a later successful login."""
    for _ in range(2):
        response = client.post("/auth/login/swagger", params={"username": "test", "password": "wrong-password"})
        assert response.status_code == 403
        assert_error(response.json(), 403)

    success = client.post("/auth/login/swagger", params={"username": "test", "password": "123456"})
    assert success.status_code == 200
    body = success.json()
    assert body["access_token"]


def test_login_with_missing_user(client: TestClient) -> None:
    """Test login failure with a missing username."""
    response = client.post("/auth/login/swagger", params={"username": "missing-user", "password": "123456"})
    assert response.status_code == 404
    assert_error(response.json(), 404)


def test_login_validation_errors(client: TestClient) -> None:
    """Test auth request validation failures."""
    missing_password = client.post("/auth/login/swagger", params={"username": "admin"})
    assert missing_password.status_code == 422
    assert_error(missing_password.json(), 422)

    missing_body_field = client.post("/auth/login", json={"username": "admin"})
    assert missing_body_field.status_code == 422
    assert_error(missing_body_field.json(), 422)


def test_json_login_requires_captcha_when_enabled(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test JSON login captcha branches through public config and auth APIs."""
    config = {
        "name": "验证码开关",
        "type": "LOGIN",
        "key": "LOGIN_CAPTCHA_ENABLED",
        "value": "true",
        "is_frontend": False,
        "remark": None,
    }
    try:
        assert_standard_ok(put_json(client, "/sys/configs/17", token_headers, config))

        missing_captcha = client.post("/auth/login", json={"username": "admin", "password": "123456"})
        assert missing_captcha.status_code == 400
        assert_error(missing_captcha.json(), 400)

        expired_captcha = client.post(
            "/auth/login",
            json={"username": "admin", "password": "123456", "uuid": "missing-captcha", "captcha": "000000"},
        )
        assert expired_captcha.status_code == 400
        assert_error(expired_captcha.json(), 400)
    finally:
        config["value"] = "false"
        assert_standard_ok(put_json(client, "/sys/configs/17", token_headers, config))


def test_refresh_requires_cookie(client: TestClient) -> None:
    """Test refresh-token failure without a refresh cookie."""
    response = client.post("/auth/refresh")
    assert response.status_code == 400
    assert_error(response.json(), 400)


def test_refresh_with_invalid_cookie(client: TestClient) -> None:
    """Test refresh-token failure with an invalid refresh cookie."""
    response = client.post("/auth/refresh", cookies={"fba_refresh_token": "invalid-token"})
    assert response.status_code == 401
    assert_error(response.json(), 401)


def test_regular_login_and_refresh(client: TestClient, data_store: DataStore) -> None:
    """Test login and refresh-token APIs."""
    response = client.post("/auth/login", json={"username": "admin", "password": "123456"})
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert body["data"]["access_token"]
    assert body["data"]["session_uuid"]

    refresh_response = client.post("/auth/refresh", cookies=response.cookies)
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert_ok(refresh_body)
    assert refresh_body["data"]["access_token"]
    data_store.admin_headers = {"Authorization": f"Bearer {body['data']['access_token']}"}


def test_captcha(client: TestClient) -> None:
    """Test captcha API."""
    response = client.get("/auth/captcha")
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert "is_enabled" in body["data"]


def test_logout(client: TestClient) -> None:
    """Test logout."""
    response = client.post("/auth/logout", headers=login_headers(client, "admin", "123456"))
    assert response.status_code == 200
    assert_ok(response.json())

    no_token = client.post("/auth/logout")
    assert no_token.status_code == 200
    assert_ok(no_token.json())


def test_authentication_errors(client: TestClient) -> None:
    """Test protected APIs with missing, malformed, and invalid tokens."""
    missing = client.get("/sys/users/me")
    assert missing.status_code == 401

    malformed = client.get("/sys/users/me", headers={"Authorization": "Basic token"})
    assert malformed.status_code == 401

    invalid = client.get("/sys/users/me", headers={"Authorization": "Bearer invalid-token"})
    assert invalid.status_code == 401
    assert_error(invalid.json(), 401)


def test_test_user_can_login(client: TestClient, data_store: DataStore) -> None:
    """Test seeded non-superuser login."""
    data_store.test_headers = login_headers(client, "test", "123456")
    response = client.get("/sys/users/me", headers=data_store.test_headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert body["data"]["username"] == "test"
    data_store.test_user_id = body["data"]["id"]
