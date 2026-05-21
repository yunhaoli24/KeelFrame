"""Admin model exports."""

from backend.app.admin.model.m2m import role_menu, user_role, data_scope_rule, role_data_scope
from backend.app.admin.model.dept import Dept
from backend.app.admin.model.menu import Menu
from backend.app.admin.model.role import Role
from backend.app.admin.model.user import User
from backend.app.admin.model.data_rule import DataRule
from backend.app.admin.model.login_log import LoginLog
from backend.app.admin.model.opera_log import OperaLog
from backend.app.admin.model.data_scope import DataScope
from backend.app.admin.model.user_password_history import UserPasswordHistory


__all__ = [
    "DataRule",
    "DataScope",
    "Dept",
    "LoginLog",
    "Menu",
    "OperaLog",
    "Role",
    "User",
    "UserPasswordHistory",
    "data_scope_rule",
    "role_data_scope",
    "role_menu",
    "user_role",
]
