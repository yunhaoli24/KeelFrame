"""Backend package initialization."""

import sqlalchemy as sa

from backend.app.s3.model import S3File, S3Storage
from backend.app.dict.model import DictData, DictType
from backend.app.task.model import TaskResult, TaskScheduler
from backend.app.admin.model import (
    Dept,
    Menu,
    Role,
    User,
    DataRule,
    LoginLog,
    OperaLog,
    DataScope,
    UserPasswordHistory,
    role_menu,
    user_role,
    data_scope_rule,
    role_data_scope,
)
from backend.app.config.model import Config
from backend.app.notice.model import Notice


ALL_MODELS: tuple[object, ...] = (
    Config,
    DataRule,
    DataScope,
    Dept,
    DictData,
    DictType,
    LoginLog,
    Menu,
    Notice,
    OperaLog,
    Role,
    S3File,
    S3Storage,
    TaskResult,
    TaskScheduler,
    User,
    UserPasswordHistory,
    data_scope_rule,
    role_data_scope,
    role_menu,
    user_role,
)

for cls in ALL_MODELS:
    if isinstance(cls, sa.Table):
        table_name = cls.name  # pyright: ignore[reportAttributeAccessIssue]
        if table_name not in globals():
            globals()[table_name] = cls
    else:
        class_name = getattr(cls, "__name__", None)
        if class_name and class_name not in globals():
            globals()[class_name] = cls


__version__ = "1.12.0"
