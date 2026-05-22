"""Helpers for RBAC black-box API fixtures."""

from collections.abc import Iterable

from starlette.testclient import TestClient

from tests.types import JsonObject
from tests.conftest import login_headers
from tests.api.helpers import get_json, put_json, assert_ok, post_json, delete_json, load_fixture, find_created_id


def rbac_fixture(name: str) -> dict[str, JsonObject]:
    """Load an RBAC fixture object keyed by scenario name."""
    fixture = load_fixture(f"rbac/{name}.json")
    return {key: value for key, value in fixture.items() if isinstance(value, dict)}


def payload_from_fixture(fixture: dict[str, JsonObject], key: str) -> dict[str, object]:
    """Return a mutable payload copy for a fixture entry."""
    return dict(fixture[key])


def flatten_tree(items: object) -> list[JsonObject]:
    """Flatten a response tree."""
    if not isinstance(items, list):
        return []
    result: list[JsonObject] = []
    stack = [item for item in items if isinstance(item, dict)]
    while stack:
        item = stack.pop()
        result.append(item)
        children = item.get("children")
        if isinstance(children, list):
            stack.extend(child for child in children if isinstance(child, dict))
    return result


def find_tree_id_by_key(
    client: TestClient, path: str, headers: dict[str, str], *, lookup_key: str, lookup_value: object
) -> int:
    """Find an ID in a tree endpoint response."""
    body = get_json(client, path, headers, **{lookup_key: lookup_value})
    matches = [item for item in flatten_tree(body["data"]) if item.get(lookup_key) == lookup_value]
    assert matches
    item_id = matches[0]["id"]
    assert isinstance(item_id, str | int | float)
    return int(item_id)


def create_menu(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a menu through HTTP and return its ID."""
    assert_ok(post_json(client, "/sys/menus", headers, payload))
    return find_tree_id_by_key(client, "/sys/menus", headers, lookup_key="title", lookup_value=payload["title"])


def create_dept(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a dept through HTTP and return its ID."""
    assert_ok(post_json(client, "/sys/depts", headers, payload))
    return find_tree_id_by_key(client, "/sys/depts", headers, lookup_key="name", lookup_value=payload["name"])


def create_role(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a role through HTTP and return its ID."""
    assert_ok(post_json(client, "/sys/roles", headers, payload))
    return find_created_id(client, "/sys/roles", headers, "name", payload["name"])


def create_data_rule(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a data rule through HTTP and return its ID."""
    assert_ok(post_json(client, "/sys/data-rules", headers, payload))
    return find_created_id(client, "/sys/data-rules", headers, "name", payload["name"])


def create_data_scope(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a data scope through HTTP and return its ID."""
    assert_ok(post_json(client, "/sys/data-scopes", headers, payload))
    return find_created_id(client, "/sys/data-scopes", headers, "name", payload["name"])


def create_user(client: TestClient, headers: dict[str, str], payload: dict[str, object]) -> int:
    """Create a user through HTTP and return its ID."""
    response = post_json(client, "/sys/users", headers, payload)
    assert_ok(response)
    data = response["data"]
    assert isinstance(data, dict)
    user_id = data["id"]
    assert isinstance(user_id, str | int | float)
    return int(user_id)


def toggle_user_permission(client: TestClient, headers: dict[str, str], user_id: int, permission_type: str) -> None:
    """Toggle a user permission through HTTP."""
    assert_ok(put_json(client, f"/sys/users/{user_id}/permissions?permission_type={permission_type}", headers))


def create_rbac_menus(client: TestClient, headers: dict[str, str], *keys: str) -> dict[str, int]:
    """Create RBAC fixture menus and return IDs by key."""
    fixtures = rbac_fixture("menus")
    created: dict[str, int] = {}
    for key in keys:
        payload = payload_from_fixture(fixtures, key)
        if key in {"role_menu", "no_perms_menu"} and "directory" in created:
            payload["parent_id"] = created["directory"]
        if key.endswith("_button") and "role_menu" in created:
            payload["parent_id"] = created["role_menu"]
        created[key] = create_menu(client, headers, payload)
    return created


def create_rbac_role(
    client: TestClient,
    headers: dict[str, str],
    role_key: str,
    *,
    menu_ids: Iterable[int] = (),
    scope_ids: Iterable[int] = (),
) -> int:
    """Create an RBAC fixture role and optionally bind menus/scopes."""
    role_id = create_role(client, headers, payload_from_fixture(rbac_fixture("roles"), role_key))
    menu_id_list = list(menu_ids)
    if menu_id_list:
        assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", headers, {"menus": menu_id_list}))
    scope_id_list = list(scope_ids)
    if scope_id_list:
        assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", headers, {"scopes": scope_id_list}))
    return role_id


def create_rbac_user(
    client: TestClient,
    headers: dict[str, str],
    user_key: str,
    *,
    role_ids: Iterable[int],
    staff: bool = False,
    superuser: bool = False,
    multi_login: bool | None = None,
) -> tuple[int, dict[str, str]]:
    """Create an RBAC fixture user, apply permission toggles, and return login headers."""
    payload = payload_from_fixture(rbac_fixture("users"), user_key)
    payload["roles"] = list(role_ids)
    user_id = create_user(client, headers, payload)
    if staff:
        toggle_user_permission(client, headers, user_id, "staff")
    if superuser:
        toggle_user_permission(client, headers, user_id, "superuser")
    if multi_login is not None:
        user_detail = get_json(client, f"/sys/users/{user_id}", headers)
        data = user_detail["data"]
        assert isinstance(data, dict)
        if data["is_multi_login"] is not multi_login:
            toggle_user_permission(client, headers, user_id, "multi_login")
    return user_id, login_headers(client, str(payload["username"]), str(payload["password"]))


def cleanup_rbac(
    client: TestClient,
    headers: dict[str, str],
    *,
    user_ids: Iterable[int] = (),
    role_ids: Iterable[int] = (),
    scope_ids: Iterable[int] = (),
    rule_ids: Iterable[int] = (),
    dept_ids: Iterable[int] = (),
    menu_ids: Iterable[int] = (),
) -> None:
    """Clean RBAC fixture data in dependency order."""
    for user_id in user_ids:
        assert_ok(delete_json(client, f"/sys/users/{user_id}", headers))
    role_id_list = list(role_ids)
    if role_id_list:
        assert_ok(delete_json(client, "/sys/roles", headers, {"pks": role_id_list}))
    scope_id_list = list(scope_ids)
    if scope_id_list:
        assert_ok(delete_json(client, "/sys/data-scopes", headers, {"pks": scope_id_list}))
    rule_id_list = list(rule_ids)
    if rule_id_list:
        assert_ok(delete_json(client, "/sys/data-rules", headers, {"pks": rule_id_list}))
    for dept_id in dept_ids:
        assert_ok(delete_json(client, f"/sys/depts/{dept_id}", headers))
    for menu_id in reversed(list(menu_ids)):
        assert_ok(delete_json(client, f"/sys/menus/{menu_id}", headers))
