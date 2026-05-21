"""Test auth APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers


def assert_ok(response_json: dict) -> None:
    """Assert a standard successful API response."""
    assert response_json["code"] == 200


def test_swagger_login(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test swagger login."""
    assert token_headers["Authorization"].startswith("Bearer ")
    assert data_store.admin_user_id == 1


def test_login_with_wrong_password(client: TestClient) -> None:
    """Test login failure with a wrong password."""
    response = client.post("/auth/login/swagger", params={"username": "admin", "password": "wrong-password"})
    assert response.status_code == 403
    assert response.json()["code"] == 403


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


def test_test_user_can_login(client: TestClient, data_store: DataStore) -> None:
    """Test seeded non-superuser login."""
    data_store.test_headers = login_headers(client, "test", "123456")
    response = client.get("/sys/users/me", headers=data_store.test_headers)
    assert response.status_code == 200
    body = response.json()
    assert_ok(body)
    assert body["data"]["username"] == "test"
    data_store.test_user_id = body["data"]["id"]
