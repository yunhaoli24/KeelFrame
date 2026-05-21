"""Config."""

from typing import Annotated

from fastapi import Body, Path, Query, Depends, APIRouter

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.pagination import PageData, DependsPagination
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.app.config.schema.config import (
    GetConfigDetail,
    CreateConfigParam,
    UpdateConfigParam,
    UpdateConfigsParam,
)
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.app.config.service.config_service import config_service


router = APIRouter()


@router.get("/all", summary="获取所有参数配置", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_all_configs(
    db: CurrentSession,
    config_type: Annotated[str | None, Query(description="参数配置类型")] = None,
) -> ResponseSchemaModel[list[GetConfigDetail]]:
    """Get All Configs."""
    configs = await config_service.get_all(db=db, config_type=config_type)
    return response_base.success(data=configs)


@router.get("/{pk}", summary="获取参数配置详情", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_config(
    db: CurrentSession, pk: Annotated[int, Path(description="参数配置 ID")]
) -> ResponseSchemaModel[GetConfigDetail]:
    """Get Config."""
    config = await config_service.get(db=db, pk=pk)
    return response_base.success(data=config)


@router.get(
    "",
    summary="分页获取所有参数配置",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_configs_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description="参数配置名称")] = None,
    config_type: Annotated[str | None, Query(description="参数配置类型")] = None,
) -> ResponseSchemaModel[PageData[GetConfigDetail]]:
    """Get Configs Paginated."""
    page_data = await config_service.get_list(db=db, name=name, config_type=config_type)
    return response_base.success(data=page_data)


@router.post(
    "",
    summary="创建参数配置",
    dependencies=[
        Depends(RequestPermission("sys:config:add")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def create_config(db: CurrentSessionTransaction, obj: CreateConfigParam) -> ResponseModel:
    """Create Config."""
    await config_service.create(db=db, obj=obj)
    return response_base.success()


@router.put("", summary="批量更新参数配置", dependencies=[Depends(RequestPermission("sys.config.edits")), DependsRBAC])  # pyright: ignore[reportGeneralTypeIssues]
async def bulk_update_config(db: CurrentSessionTransaction, objs: list[UpdateConfigsParam]) -> ResponseModel:
    """Bulk Update Config."""
    count = await config_service.bulk_update(db=db, objs=objs)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put(
    "/{pk}",
    summary="更新参数配置",
    dependencies=[
        Depends(RequestPermission("sys:config:edit")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def update_config(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description="参数配置 ID")], obj: UpdateConfigParam
) -> ResponseModel:
    """Update Config."""
    count = await config_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "",
    summary="批量删除参数配置",
    dependencies=[
        Depends(RequestPermission("sys:config:del")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def delete_configs(
    db: CurrentSessionTransaction, pks: Annotated[list[int], Body(description="参数配置 ID 列表")]
) -> ResponseModel:
    """Delete Configs."""
    count = await config_service.delete(db=db, pks=pks)
    if count > 0:
        return response_base.success()
    return response_base.fail()
