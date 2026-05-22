"""Test dept router APIs."""

from starlette.testclient import TestClient

from tests.conftest import DataStore, login_headers
from tests.api.helpers import get_json, put_json, assert_ok, post_json, delete_json, assert_error
from tests.api.admin.sys.test_data_rule import data_rule_payload
from tests.api.admin.sys.test_user import user_payload


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
    rule_payload = data_rule_payload("API Dept Permission Rule") | {
        "operator": 0,
        "expression": 0,
        "value": "测试",
    }
    assert_ok(post_json(client, "/sys/data-rules", token_headers, rule_payload))
    rule_id = int(get_json(client, "/sys/data-rules", token_headers, name=rule_payload["name"])["data"]["items"][0]["id"])

    scope_payload = {"name": "API Dept Permission Scope", "status": 1}
    assert_ok(post_json(client, "/sys/data-scopes", token_headers, scope_payload))
    scope_id = int(get_json(client, "/sys/data-scopes", token_headers, name=scope_payload["name"])["data"]["items"][0]["id"])
    assert_ok(put_json(client, f"/sys/data-scopes/{scope_id}/rules", token_headers, {"rules": [rule_id]}))

    role_payload = {"name": "API Dept Permission Role", "status": 1, "is_filter_scopes": True, "remark": "api"}
    assert_ok(post_json(client, "/sys/roles", token_headers, role_payload))
    role_id = int(get_json(client, "/sys/roles", token_headers, name=role_payload["name"])["data"]["items"][0]["id"])
    assert_ok(put_json(client, f"/sys/roles/{role_id}/menus", token_headers, {"menus": [1, 2, 3, 53]}))
    assert_ok(put_json(client, f"/sys/roles/{role_id}/scopes", token_headers, {"scopes": [scope_id]}))

    user = user_payload("api_dept_permission_user") | {"roles": [role_id]}
    create_body = post_json(client, "/sys/users", token_headers, user)
    assert_ok(create_body)
    user_id = int(create_body["data"]["id"])
    headers = login_headers(client, "api_dept_permission_user", "123456")
    data_store.created["api_dept_permission_user_id"] = user_id

    depts = get_json(client, "/sys/depts", headers)
    assert_ok(depts)
    assert isinstance(depts["data"], list)
    assert [dept["name"] for dept in depts["data"]] == ["测试"]

    assert_ok(delete_json(client, f"/sys/users/{user_id}", token_headers))
    assert_ok(delete_json(client, "/sys/roles", token_headers, {"pks": [role_id]}))
    assert_ok(delete_json(client, "/sys/data-scopes", token_headers, {"pks": [scope_id]}))
    assert_ok(delete_json(client, "/sys/data-rules", token_headers, {"pks": [rule_id]}))


def test_dept_lifecycle(client: TestClient, token_headers: dict[str, str], data_store: DataStore) -> None:
    """Test department creation, update, and deletion."""
    payload = dept_payload()
    assert_ok(post_json(client, "/sys/depts", token_headers, payload))
    dept_id = int(get_json(client, "/sys/depts", token_headers, name=payload["name"])["data"][0]["id"])
    data_store.created["dept_id"] = dept_id

    assert_ok(get_json(client, f"/sys/depts/{dept_id}", token_headers))
    assert_ok(put_json(client, f"/sys/depts/{dept_id}", token_headers, payload | {"leader": "Tester Updated"}))
    assert_ok(delete_json(client, f"/sys/depts/{dept_id}", token_headers))


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
