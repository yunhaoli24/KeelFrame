"""Notice API v1."""

from typing import Annotated

from fastapi import Path, Query, Depends, APIRouter

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.pagination import PageData, DependsPagination
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.common.security.permission import RequestPermission
from backend.app.notice.schema.notice import (
    GetNoticeDetail,
    CreateNoticeParam,
    DeleteNoticeParam,
    UpdateNoticeParam,
)
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.app.notice.service.notice_service import notice_service


router = APIRouter()


@router.get("/{pk}", summary="获取通知公告详情", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_notice(
    db: CurrentSession, pk: Annotated[int, Path(description="通知公告 ID")]
) -> ResponseSchemaModel[GetNoticeDetail]:
    """Get Notice."""
    notice = await notice_service.get(db=db, pk=pk)
    return response_base.success(data=notice)


@router.get(
    "",
    summary="分页获取所有通知公告",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_notices_paginated(
    db: CurrentSession,
    title: Annotated[str | None, Query(description="标题")] = None,
    notice_type: Annotated[int | None, Query(description="类型")] = None,
    status: Annotated[int | None, Query(description="状态")] = None,
) -> ResponseSchemaModel[PageData[GetNoticeDetail]]:
    """Get Notices Paginated."""
    page_data = await notice_service.get_list(db=db, title=title, notice_type=notice_type, status=status)
    return response_base.success(data=page_data)


@router.post(
    "",
    summary="创建通知公告",
    dependencies=[
        Depends(RequestPermission("sys:notice:add")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def create_notice(db: CurrentSessionTransaction, obj: CreateNoticeParam) -> ResponseModel:
    """Create Notice."""
    await notice_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    "/{pk}",
    summary="更新通知公告",
    dependencies=[
        Depends(RequestPermission("sys:notice:edit")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def update_notice(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description="通知公告 ID")], obj: UpdateNoticeParam
) -> ResponseModel:
    """Update Notice."""
    count = await notice_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "",
    summary="批量删除通知公告",
    dependencies=[
        Depends(RequestPermission("sys:notice:del")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def delete_notices(db: CurrentSessionTransaction, obj: DeleteNoticeParam) -> ResponseModel:
    """Delete Notices."""
    count = await notice_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()
