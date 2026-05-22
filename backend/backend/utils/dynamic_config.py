# pragma: exclude file
"""Dynamic Config."""

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.conf import settings
from backend.database.db import async_engine
from backend.app.config.enums import ConfigType
from backend.utils.serializers import select_list_serialize
from backend.app.config.crud.crud_config import config_dao


_sys_config_table_exists: bool | None = None


async def check_sys_config_table_exists() -> bool:
    """检查 sys_config 表是否存在.

    :return:
    """
    global _sys_config_table_exists  # noqa: PLW0603
    if _sys_config_table_exists is None:

        def _has_sys_config_table(sync_conn: Connection) -> bool:
            return bool(inspect(sync_conn).has_table("sys_config", schema=None))

        async with async_engine.begin() as conn:
            _sys_config_table_exists = await conn.run_sync(_has_sys_config_table)
    return bool(_sys_config_table_exists)


async def load_user_security_config(db: AsyncSession) -> None:
    """获取用户安全配置.

    :param db: 数据库会话
    :return:
    """
    if not await check_sys_config_table_exists():
        return

    dynamic_config = await config_dao.get_all(db, ConfigType.user_security)

    if dynamic_config:
        security_config_status_key = "USER_SECURITY_CONFIG_STATUS"
        lock_threshold_key = "USER_LOCK_THRESHOLD"
        lock_seconds_key = "USER_LOCK_SECONDS"
        password_expiry_days_key = "USER_PASSWORD_EXPIRY_DAYS"  # noqa: S105
        password_reminder_days_key = "USER_PASSWORD_REMINDER_DAYS"  # noqa: S105
        password_history_check_count_key = "USER_PASSWORD_HISTORY_CHECK_COUNT"  # noqa: S105
        password_min_length_key = "USER_PASSWORD_MIN_LENGTH"  # noqa: S105
        password_max_length_key = "USER_PASSWORD_MAX_LENGTH"  # noqa: S105
        password_require_special_char_key = "USER_PASSWORD_REQUIRE_SPECIAL_CHAR"  # noqa: S105

        configs = {dc["key"]: dc["value"] for dc in select_list_serialize(dynamic_config)}
        if int(str(configs.get(security_config_status_key) or 0)):
            if lock_threshold_key in configs:
                settings.USER_LOCK_THRESHOLD = int(str(configs[lock_threshold_key]))
            if lock_seconds_key in configs:
                settings.USER_LOCK_SECONDS = int(str(configs[lock_seconds_key]))
            if password_expiry_days_key in configs:
                settings.USER_PASSWORD_EXPIRY_DAYS = int(str(configs[password_expiry_days_key]))
            if password_reminder_days_key in configs:
                settings.USER_PASSWORD_REMINDER_DAYS = int(str(configs[password_reminder_days_key]))
            if password_history_check_count_key in configs:
                settings.USER_PASSWORD_HISTORY_CHECK_COUNT = int(str(configs[password_history_check_count_key]))
            if password_min_length_key in configs:
                settings.USER_PASSWORD_MIN_LENGTH = int(str(configs[password_min_length_key]))
            if password_max_length_key in configs:
                settings.USER_PASSWORD_MAX_LENGTH = int(str(configs[password_max_length_key]))
            if password_require_special_char_key in configs:
                settings.USER_PASSWORD_REQUIRE_SPECIAL_CHAR = configs[password_require_special_char_key] == "true"


async def load_login_config(db: AsyncSession) -> None:
    """获取登录配置.

    :param db: 数据库会话
    :return:
    """
    if not await check_sys_config_table_exists():
        return

    dynamic_config = await config_dao.get_all(db, ConfigType.login)

    if dynamic_config:
        login_config_status_key = "LOGIN_CONFIG_STATUS"
        login_captcha_enabled_key = "LOGIN_CAPTCHA_ENABLED"

        configs = {dc["key"]: dc["value"] for dc in select_list_serialize(dynamic_config)}
        if int(str(configs.get(login_config_status_key) or 0)) and login_captcha_enabled_key in configs:
            settings.LOGIN_CAPTCHA_ENABLED = configs[login_captcha_enabled_key] == "true"


async def load_email_config(db: AsyncSession) -> None:
    """获取邮箱配置.

    :param db: 数据库会话
    :return:
    """
    if not await check_sys_config_table_exists():
        return

    dynamic_config = await config_dao.get_all(db, ConfigType.email)

    if dynamic_config:
        email_config_status_key = "EMAIL_CONFIG_STATUS"
        host_key = "EMAIL_HOST"
        port_key = "EMAIL_PORT"
        ssl_key = "EMAIL_SSL"
        username_key = "EMAIL_USERNAME"
        password_key = "EMAIL_PASSWORD"  # noqa: S105

        configs = {dc["key"]: dc["value"] for dc in select_list_serialize(dynamic_config)}
        if int(str(configs.get(email_config_status_key) or 0)):
            settings.EMAIL_HOST = str(configs[host_key])
        if configs.get(port_key):
            settings.EMAIL_PORT = int(str(configs[port_key]))
        if configs.get(ssl_key):
            settings.EMAIL_SSL = configs[ssl_key] == "true"
        if configs.get(username_key):
            settings.EMAIL_USERNAME = str(configs[username_key])
        if configs.get(password_key):
            settings.EMAIL_PASSWORD = str(configs[password_key])
