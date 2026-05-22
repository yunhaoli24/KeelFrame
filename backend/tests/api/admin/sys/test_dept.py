"""Test dept router APIs."""

import pytest
from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import get_json, put_json, assert_ok, post_json, delete_json, assert_error, find_created_id
from tests.api.rbac_helpers import (
    create_dept,
    cleanup_rbac,
    rbac_fixture,
    create_data_rule,
    create_rbac_role,
    create_rbac_user,
    create_data_scope,
    payload_from_fixture,
)
from tests.api.admin.sys.test_data_rule import data_rule_payload


def dept_payload(name: str = "API Dept") -> dict[str, object]:
    """Build a dept payload."""
    return {
        "name": name,
        "parent_id": None,
        "sort": 10,
        "leader": "Tester",
        "phone": "13900000003",
        "email": "api_dept@example.com",
        "status": 1,
    }


def test_dept_read_apis(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test seeded dept read APIs."""
    depts = get_json(client, "/sys/depts", token_headers)
    assert_ok(depts)
    assert depts["data"]

    filtered = get_json(client, "/sys/depts", token_headers, name="测试", status=1)
    assert_ok(filtered)
    assert filtered["data"]

    dept_detail = get_json(client, "/sys/depts/1", token_headers)
    assert_ok(dept_detail)
    assert dept_detail["data"]["name"] == "测试"

    missing = client.get("/sys/depts/999999", headers=token_headers)
    assert missing.status_code == 404
    assert_error(missing.json(), 404)


def test_dept_tree_for_normal_user(client: TestClient, data_store: DataStore) -> None:
    """Test data-permission filtering branch through a non-superuser public request."""
    headers = data_store.test_headers or login_headers(client, "test", "123456")
    depts = get_json(client, "/sys/depts", headers, name="测试", status=1)
    assert_ok(depts)
    assert isinstance(depts["data"], list)


def test_dept_tree_applies_custom_data_permission_scope(
    client: TestClient, token_headers: dict[str, str], data_store: DataStore
) -> None:
    """Test data-permission filtering with resources wired through public APIs."""
    username = "api_dept_permission_user"
    rule_payload = data_rule_payload("API Dept Permission Rule") | {
        "operator": 0,
        "expression": 0,
        "value": "测试",
    }
    assert_ok(post_json(client, "/sys/data-rules", token_headers, rule_payload))
    rule_id = find_created_id(client, "/sys/data-rules", token_headers, "name", rule_payload["name"])

    scope_payload = {"name": "API Dept Permission Scope", "status": 1}
    assert_ok(post_json(client, "/sys/data-scopes", token_headers, scope_payload))
    scope_id = find_created_id(client, "/sys/data-scopes", token_headers, "name", scope_payload["name"])
    role_id: int | None = None
    user_id: int | None = None

    try:
        assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}/rules", token_headers, {"rules": [rule_id]}))

        role_payload = {"name": "API Dept Permission Role", "status": 1, "is_filter_scopes": True, "remark": "api"}
        assert_ok(post_json(client, "/sys/roles", token_headers, role_payload))
        role_id = find_created_id(client, "/sys/roles", token_headers, "name", role_payload["name"])
        assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", token_headers, {"menus": [1, 2, 3, 53]}))
        assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", token_headers, {"scopes": [scope_id]}))

        user = {
            "username": username,
            "password": "123456",
            "nickname": "API User",
            "email": f"{username}@example.com",
            "phone": "13900000001",
            "dept_id": 1,
            "roles": [role_id],
        }
        create_body = post_json(client, "/sys/users", token_headers, user)
        assert_ok(create_body)
        user_id = int(create_body["data"]["id"])
        headers = login_headers(client, username, "123456")
        data_store.created["api_dept_permission_user_id"] = user_id

        depts = get_json(client, "/sys/depts", headers)
        assert_ok(depts)
        assert isinstance(depts["data"], list)
        assert [dept["name"] for dept in depts["data"]] == ["测试"]
    finally:
        if user_id is not None:
            assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))
        if role_id is not None:
            assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))
        assert_ok(delete_json(client, "/sys/data-scopes", token_headers, {"pks": [scope_id]}))
        assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))


def _create_rbac_depts(client: TestClient, headers: dict[str, str]) -> dict[str, int]:
    return {
        key: create_dept(client, headers, payload_from_fixture(rbac_fixture("depts"), key))
        for key in ("alpha", "beta", "gamma")
    }


def _visible_rbac_dept_names(client: TestClient, headers: dict[str, str]) -> set[str]:
    body = get_json(client, "/sys/depts", headers, name="API RBAC Dept")
    assert_ok(body)
    assert isinstance(body["data"], list)
    return {str(item["name"]) for item in body["data"] if isinstance(item, dict)}


def _create_scope_user_for_rules(
    client: TestClient,
    admin_headers: dict[str, str],
    *,
    rule_keys: list[str],
    role_key: str = "scope_filter",
    user_key: str = "scope_filter",
) -> tuple[list[int], int, int, int, dict[str, str]]:
    rule_fixtures = rbac_fixture("data_rules")
    rule_ids = [create_data_rule(client, admin_headers, payload_from_fixture(rule_fixtures, key)) for key in rule_keys]
    scope_id = create_data_scope(client, admin_headers, payload_from_fixture(rbac_fixture("data_scopes"), "filtered"))
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}/rules", admin_headers, {"rules": rule_ids}))
    role_id = create_rbac_role(client, admin_headers, role_key, scope_ids=[scope_id])
    user_id, headers = create_rbac_user(client, admin_headers, user_key, role_ids=[role_id])
    return rule_ids, scope_id, role_id, user_id, headers


@pytest.mark.parametrize(
    ("rule_key", "expected_names"),
    [
        ("eq_alpha", {"API RBAC Dept Alpha"}),
        ("ne_alpha", {"API RBAC Dept Beta", "API RBAC Dept Gamma"}),
        ("in_alpha_beta", {"API RBAC Dept Alpha", "API RBAC Dept Beta"}),
        ("not_in_alpha_beta", {"API RBAC Dept Gamma"}),
        ("gt_alpha", {"API RBAC Dept Beta", "API RBAC Dept Gamma"}),
        ("ge_beta", {"API RBAC Dept Beta", "API RBAC Dept Gamma"}),
        ("lt_gamma", {"API RBAC Dept Alpha", "API RBAC Dept Beta"}),
        ("le_beta", {"API RBAC Dept Alpha", "API RBAC Dept Beta"}),
    ],
)
def test_dept_data_permission_expressions(
    client: TestClient, token_headers: dict[str, str], rule_key: str, expected_names: set[str]
) -> None:
    """Test data-permission expression operators through Dept HTTP reads."""
    dept_ids: dict[str, int] = {}
    rule_ids: list[int] = []
    scope_id: int | None = None
    role_id: int | None = None
    user_id: int | None = None

    try:
        dept_ids = _create_rbac_depts(client, token_headers)
        rule_ids, scope_id, role_id, user_id, headers = _create_scope_user_for_rules(
            client, token_headers, rule_keys=[rule_key]
        )

        assert _visible_rbac_dept_names(client, headers) == expected_names
    finally:
        cleanup_rbac(
            client,
            token_headers,
            user_ids=[user_id] if user_id is not None else [],
            role_ids=[role_id] if role_id is not None else [],
            scope_ids=[scope_id] if scope_id is not None else [],
            rule_ids=rule_ids,
            dept_ids=dept_ids.values(),
        )


@pytest.mark.parametrize(
    ("rule_keys", "expected_names"),
    [
        (["and_ge_alpha", "and_le_beta"], {"API RBAC Dept Alpha", "API RBAC Dept Beta"}),
        (["or_eq_alpha", "or_eq_gamma"], {"API RBAC Dept Alpha", "API RBAC Dept Gamma"}),
    ],
)
def test_dept_data_permission_and_or_combinations(
    client: TestClient, token_headers: dict[str, str], rule_keys: list[str], expected_names: set[str]
) -> None:
    """Test AND and OR data-permission rule combinations through Dept HTTP reads."""
    dept_ids: dict[str, int] = {}
    rule_ids: list[int] = []
    scope_id: int | None = None
    role_id: int | None = None
    user_id: int | None = None

    try:
        dept_ids = _create_rbac_depts(client, token_headers)
        rule_ids, scope_id, role_id, user_id, headers = _create_scope_user_for_rules(
            client, token_headers, rule_keys=rule_keys
        )

        assert _visible_rbac_dept_names(client, headers) == expected_names
    finally:
        cleanup_rbac(
            client,
            token_headers,
            user_ids=[user_id] if user_id is not None else [],
            role_ids=[role_id] if role_id is not None else [],
            scope_ids=[scope_id] if scope_id is not None else [],
            rule_ids=rule_ids,
            dept_ids=dept_ids.values(),
        )


def test_dept_data_permission_disabled_role_filter_allows_all_fixture_depts(
    client: TestClient, token_headers: dict[str, str]
) -> None:
    """Test is_filter_scopes=false bypasses data-rule filtering."""
    dept_ids: dict[str, int] = {}
    rule_ids: list[int] = []
    scope_id: int | None = None
    role_id: int | None = None
    user_id: int | None = None

    try:
        dept_ids = _create_rbac_depts(client, token_headers)
        rule_ids, scope_id, role_id, user_id, headers = _create_scope_user_for_rules(
            client,
            token_headers,
            rule_keys=["eq_alpha"],
            role_key="scope_passthrough",
            user_key="scope_passthrough",
        )

        assert _visible_rbac_dept_names(client, headers) == {
            "API RBAC Dept Alpha",
            "API RBAC Dept Beta",
            "API RBAC Dept Gamma",
        }
    finally:
        cleanup_rbac(
            client,
            token_headers,
            user_ids=[user_id] if user_id is not None else [],
            role_ids=[role_id] if role_id is not None else [],
            scope_ids=[scope_id] if scope_id is not None else [],
            rule_ids=rule_ids,
            dept_ids=dept_ids.values(),
        )


def test_dept_data_permission_role_without_rules_allows_all_fixture_depts(
    client: TestClient, token_headers: dict[str, str]
) -> None:
    """Test a filtering role without data rules does not filter data."""
    dept_ids: dict[str, int] = {}
    role_id: int | None = None
    user_id: int | None = None

    try:
        dept_ids = _create_rbac_depts(client, token_headers)
        role_id = create_rbac_role(client, token_headers, "scope_filter")
        user_id, headers = create_rbac_user(client, token_headers, "scope_filter", role_ids=[role_id])

        assert _visible_rbac_dept_names(client, headers) == {
            "API RBAC Dept Alpha",
            "API RBAC Dept Beta",
            "API RBAC Dept Gamma",
        }
    finally:
        cleanup_rbac(
            client,
            token_headers,
            user_ids=[user_id] if user_id is not None else [],
            role_ids=[role_id] if role_id is not None else [],
            dept_ids=dept_ids.values(),
        )


def test_dept_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test department creation, update, and deletion."""
    payload = dept_payload()
    assert_ok(post_json(client, "/sys/depts", token_headers, payload))
    dept_id = int(get_json(client, "/sys/depts", token_headers, name=payload["name"])["data"][0]["id"])
    data_store.created["dept_id"] = dept_id

    assert_ok(get_json(client, f"/sys/depts/{dept_id}", token_headers))
    assert_ok(put_json(client, f"/sys/depts/{dept_id}", token_headers, payload | {"leader": "Tester Updated"}))
    assert_ok(delete_json(client, f"/sys/depts/{dept_id}", token_headers))


def test_dept_parent_child_delete_conflict(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test deleting a department with children is rejected."""
    parent_id: int | None = None
    child_id: int | None = None
    parent_payload = dept_payload("API Parent Dept")
    child_payload = dept_payload("API Child Dept")

    try:
        assert_ok(post_json(client, "/sys/depts", token_headers, parent_payload))
        parent_id = int(get_json(client, "/sys/depts", token_headers, name=parent_payload["name"])["data"][0]["id"])
        assert_ok(post_json(client, "/sys/depts", token_headers, child_payload | {"parent_id": parent_id}))
        child_id = int(get_json(client, "/sys/depts", token_headers, name=child_payload["name"])["data"][0]["id"])

        response = client.request("DELETE", f"/sys/depts/{parent_id}", headers=token_headers)
        assert response.status_code == 409
        assert_error(response.json(), 409)
    finally:
        if child_id is not None:
            assert_ok(delete_json(client, f"/sys/depts/{child_id}", token_headers))
        if parent_id is not None:
            assert_ok(delete_json(client, f"/sys/depts/{parent_id}", token_headers))


def test_dept_error_branches(client: TestClient, token_headers: dict[str, str]) -> None:
    """Test dept router error branches."""
    duplicate = client.post("/sys/depts", headers=token_headers, json=dept_payload("测试"))
    assert duplicate.status_code == 409
    assert_error(duplicate.json(), 409)

    missing_parent = client.post(
        "/sys/depts",
        headers=token_headers,
        json=dept_payload("API Missing Parent") | {"parent_id": 999999},
    )
    assert missing_parent.status_code == 404
    assert_error(missing_parent.json(), 404)

    missing_update = client.put("/sys/depts/999999", headers=token_headers, json=dept_payload("Missing Dept"))
    assert missing_update.status_code == 404
    assert_error(missing_update.json(), 404)

    assert_ok(post_json(client, "/sys/depts", token_headers, dept_payload("API Self Parent Dept")))
    self_parent_id = int(get_json(client, "/sys/depts", token_headers, name="API Self Parent Dept")["data"][0]["id"])
    self_parent = client.put(
        f"/sys/depts/{self_parent_id}",
        headers=token_headers,
        json=dept_payload("API Self Parent Dept") | {"parent_id": self_parent_id},
    )
    assert self_parent.status_code == 403
    assert_error(self_parent.json(), 403)
    assert_ok(delete_json(client, f"/sys/depts/{self_parent_id}", token_headers))

    seeded_delete = client.request("DELETE", "/sys/depts/1", headers=token_headers)
    assert seeded_delete.status_code == 409
    assert_error(seeded_delete.json(), 409)

    missing_delete = client.request("DELETE", "/sys/depts/999999", headers=token_headers)
    assert missing_delete.status_code == 404
    assert_error(missing_delete.json(), 404)
