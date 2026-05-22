"""Control."""

from typing import Annotated

from fastapi import Path, Depends, APIRouter
from starlette.concurrency import run_in_threadpool

from backend.app.task import celery_app
from backend.common.exception import errors
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.app.task.schema.control import TaskRegisteredDetail
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base


router: APIRouter = APIRouter()
WORKER_PING_TIMEOUT = 2


@router.get("/health", summary="获取任务 Worker 健康状态", dependencies=[DependsJwtAuth])
async def get_task_worker_health() -> ResponseSchemaModel[bool]:
    """Get Task Worker Health."""
    workers = await run_in_threadpool(celery_app.control.ping, timeout=WORKER_PING_TIMEOUT)
    return response_base.success(data=bool(workers))


@router.get("/registered", summary="获取已注册的任务", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_task_registered() -> ResponseSchemaModel[list[TaskRegisteredDetail]]:
    """Get Task Registered."""
    inspector = celery_app.control.inspect(timeout=WORKER_PING_TIMEOUT)
    registered = await run_in_threadpool(inspector.registered)
    if not registered:
        raise errors.ServerError(msg="Celery Worker 暂不可用, 请稍后重试")
    task_registered: list[TaskRegisteredDetail] = []  # pragma: no cover
    celery_app_tasks = celery_app.tasks
    for tasks in registered.values():  # pragma: no cover
        for task in tasks:
            task_ins = celery_app_tasks.get(task)
            if task_ins:
                task_doc = task_ins.__doc__
                task_registered.append(TaskRegisteredDetail(name=task_doc or str(task_ins), task=str(task_ins)))
            else:
                task_registered.append(TaskRegisteredDetail(name=task, task=task))
    return response_base.success(data=task_registered)


@router.delete(
    "/{task_id}/cancel",
    summary="撤销任务",
    dependencies=[
        Depends(RequestPermission("sys:task:revoke")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def revoke_task(task_id: Annotated[str, Path(description="任务 UUID")]) -> ResponseModel:
    """Revoke Task."""
    workers = await run_in_threadpool(celery_app.control.ping, timeout=WORKER_PING_TIMEOUT)
    if not workers:
        raise errors.ServerError(msg="Celery Worker 暂不可用, 请稍后重试")
    celery_app.control.revoke(task_id)  # pragma: no cover
    return response_base.success()  # pragma: no cover
