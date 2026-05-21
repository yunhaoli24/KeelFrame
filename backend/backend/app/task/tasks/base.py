"""Base."""

import asyncio
from typing import Any

from celery import Task  # pyright: ignore[reportMissingModuleSource]
from sqlalchemy.exc import SQLAlchemyError

from backend.core.conf import settings
from backend.common.socketio.actions import task_notification


class TaskBase(Task):
    """Celery 任务基类."""

    autoretry_for = (SQLAlchemyError,)
    max_retries = settings.CELERY_TASK_MAX_RETRIES

    async def before_start(self, task_id: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        """任务开始前执行钩子.

        :param task_id: 任务 ID
        :return:
        """
        _ = args, kwargs
        await task_notification(msg=f"任务 {task_id} 开始执行")

    async def on_success(
        self,
        retval: Any,  # noqa: ANN401
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """任务成功后执行钩子.

        :param task_id: 任务 ID
        :return:
        """
        _ = retval, args, kwargs
        await task_notification(msg=f"任务 {task_id} 执行成功")

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,  # noqa: ANN401
    ) -> None:
        """任务失败后执行钩子.

        :param task_id: 任务 ID
        :return:
        """
        _ = exc, args, kwargs, einfo
        asyncio.create_task(task_notification(msg=f"任务 {task_id} 执行失败"))  # noqa: RUF006
