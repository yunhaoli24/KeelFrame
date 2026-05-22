"""S3 Storage API v1."""

from typing import Annotated

from fastapi import Path, Depends, APIRouter
from fastapi.params import Query

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.pagination import PageData, DependsPagination
from backend.common.security.rbac import DependsRBAC
from backend.app.s3.schema.storage import (
    GetS3StorageDetail,
    CreateS3StorageParam,
    DeleteS3StorageParam,
    UpdateS3StorageParam,
)
from backend.app.s3.service.storage import s3_storage_service
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base


router = APIRouter()


@router.get(
    "/all",
    summary="获取所有 S3 存储详情",
    dependencies=[
        Depends(RequestPermission("s3:storage:query")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_all_s3_storages(db: CurrentSession) -> ResponseSchemaModel[list[GetS3StorageDetail]]:
    """Get All S3 Storages."""
    s3_storage = await s3_storage_service.get_all(db=db)
    return response_base.success(data=s3_storage)


@router.get(
    "/{pk}",
    summary="获取 S3 存储详情",
    dependencies=[
        Depends(RequestPermission("s3:storage:query")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_s3_storage(
    db: CurrentSession, pk: Annotated[int, Path(description="S3 存储 ID")]
) -> ResponseSchemaModel[GetS3StorageDetail]:
    """Get S3 Storage."""
    s3_storage = await s3_storage_service.get(db=db, pk=pk)
    return response_base.success(data=s3_storage)


@router.get(
    "",
    summary="分页获取所有 S3 存储",
    dependencies=[
        Depends(RequestPermission("s3:storage:query")),
        DependsRBAC,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_s3_storages_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description="存储名称")] = None,
    region: Annotated[str | None, Query(description="区域")] = None,
) -> ResponseSchemaModel[PageData[GetS3StorageDetail]]:
    """Get S3 Storages Paginated."""
    page_data = await s3_storage_service.get_list(db=db, name=name, region=region)
    return response_base.success(data=page_data)


@router.post(
    "",
    summary="创建 S3 存储",
    dependencies=[
        Depends(RequestPermission("s3:storage:add")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def create_s3_storage(db: CurrentSessionTransaction, obj: CreateS3StorageParam) -> ResponseModel:
    """Create S3 Storage."""
    await s3_storage_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    "/{pk}",
    summary="更新 S3 存储",
    dependencies=[
        Depends(RequestPermission("s3:storage:edit")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def update_s3_storage(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description="S3 存储 ID")], obj: UpdateS3StorageParam
) -> ResponseModel:
    """Update S3 Storage."""
    count = await s3_storage_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "",
    summary="批量删除 S3 存储",
    dependencies=[
        Depends(RequestPermission("s3:storage:del")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def delete_s3_storages(db: CurrentSessionTransaction, obj: DeleteS3StorageParam) -> ResponseModel:
    """Delete S3 Storages."""
    count = await s3_storage_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()
