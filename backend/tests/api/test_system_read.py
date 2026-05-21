"""Test read-only system APIs."""

from starlette.testclient import TestClient

from tests.api.helpers import assert_ok, assert_page, get_json


def test_current_user_and_permissions(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test current user and permission-code APIs."""
    me = get_json(client, "/sys/users/me", token_headers)
    assert_ok(me)
    assert me["data"]["username"] == "admin"

    codes = get_json(client, "/auth/codes", token_headers)
    assert_ok(codes)
    assert isinstance(codes["data"], list)
    assert codes["data"]
    assert "sys:user:del" in codes["data"]


def test_seeded_system_resources(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded system resource query APIs."""
    users = get_json(client, "/sys/users", token_headers, username="admin")
    assert any(item["username"] == "admin" for item in assert_page(users))

    user_detail = get_json(client, "/sys/users/1", token_headers)
    assert_ok(user_detail)
    assert user_detail["data"]["username"] == "admin"

    user_roles = get_json(client, "/sys/users/1/roles", token_headers)
    assert_ok(user_roles)
    assert user_roles["data"]

    roles = get_json(client, "/sys/roles", token_headers)
    assert_page(roles)

    role_detail = get_json(client, "/sys/roles/1", token_headers)
    assert_ok(role_detail)
    assert role_detail["data"]["name"] == "测试"

    assert_ok(get_json(client, "/sys/roles/all", token_headers))
    assert_ok(get_json(client, "/sys/roles/1/menus", token_headers))
    assert_ok(get_json(client, "/sys/roles/1/scopes", token_headers))


def test_seeded_tree_and_scope_resources(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded tree and data-scope query APIs."""
    menus = get_json(client, "/sys/menus", token_headers)
    assert_ok(menus)
    assert menus["data"]

    sidebar = get_json(client, "/sys/menus/sidebar", token_headers)
    assert_ok(sidebar)
    assert sidebar["data"]

    menu_detail = get_json(client, "/sys/menus/1", token_headers)
    assert_ok(menu_detail)
    assert menu_detail["data"]["title"] == "控制台"

    depts = get_json(client, "/sys/depts", token_headers)
    assert_ok(depts)
    assert depts["data"]

    dept_detail = get_json(client, "/sys/depts/1", token_headers)
    assert_ok(dept_detail)
    assert dept_detail["data"]["name"] == "测试"

    assert_ok(get_json(client, "/sys/data-rules/models", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/models/Dept/columns", token_headers))
    assert_page(get_json(client, "/sys/data-rules", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/all", token_headers))
    assert_ok(get_json(client, "/sys/data-rules/1", token_headers))

    assert_page(get_json(client, "/sys/data-scopes", token_headers))
    assert_ok(get_json(client, "/sys/data-scopes/all", token_headers))
    assert_ok(get_json(client, "/sys/data-scopes/1", token_headers))
    assert_ok(get_json(client, "/sys/data-scopes/1/rules", token_headers))


def test_logs_monitors_and_tasks(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test logs, monitors, and task read APIs."""
    assert_page(get_json(client, "/logs/login", token_headers))
    assert_page(get_json(client, "/logs/opera", token_headers))

    assert_ok(get_json(client, "/monitors/sessions", token_headers))
    assert_ok(get_json(client, "/monitors/redis", token_headers))
    assert_ok(get_json(client, "/monitors/server", token_headers))

    assert_page(get_json(client, "/schedulers", token_headers))
    assert_ok(get_json(client, "/schedulers/all", token_headers))
    assert_ok(get_json(client, "/schedulers/1", token_headers))
    assert_page(get_json(client, "/task-results", token_headers))
