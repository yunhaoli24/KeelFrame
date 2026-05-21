"""Dict Data API."""

from typing import Annotated

from fastapi import Path, Query, Depends, APIRouter

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.pagination import PageData, DependsPagination
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.app.dict.schema.dict_data import (
    GetDictDataDetail,
    CreateDictDataParam,
    DeleteDictDataParam,
    UpdateDictDataParam,
)
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.app.dict.service.dict_data_service import dict_data_service


router = APIRouter()


@router.get("/all", summary="获取所有字典数据", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_all_dict_datas(db: CurrentSession) -> ResponseSchemaModel[list[GetDictDataDetail]]:
    """Get all dict datas."""
    data = await dict_data_service.get_all(db=db)
    return response_base.success(data=data)


@router.get("/type-codes/{code}", summary="获取字典数据列表", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_dict_data_by_type_code(
    db: CurrentSession,
    code: Annotated[str, Path(description="字典类型编码")],
) -> ResponseSchemaModel[list[GetDictDataDetail]]:
    """Get dict data by type code."""
    data = await dict_data_service.get_by_type_code(db=db, code=code)
    return response_base.success(data=data)


@router.get("/{pk}", summary="获取字典数据详情", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_dict_data(
    db: CurrentSession,
    pk: Annotated[int, Path(description="字典数据 ID")],
) -> ResponseSchemaModel[GetDictDataDetail]:
    """Get dict data."""
    data = await dict_data_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.get(
    "",
    summary="分页获取所有字典数据",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_dict_datas_paginated(
    db: CurrentSession,
    type_code: Annotated[str | None, Query(description="字典类型编码")] = None,
    label: Annotated[str | None, Query(description="字典数据标签")] = None,
    value: Annotated[str | None, Query(description="字典数据键值")] = None,
    status: Annotated[int | None, Query(description="状态")] = None,
    type_id: Annotated[int | None, Query(description="字典类型 ID")] = None,
) -> ResponseSchemaModel[PageData[GetDictDataDetail]]:
    """Get dict datas paginated."""
    page_data = await dict_data_service.get_list(
        db=db,
        type_code=type_code,
        label=label,
        value=value,
        status=status,
        type_id=type_id,
    )
    return response_base.success(data=page_data)


@router.post(
    "",
    summary="创建字典数据",
    dependencies=[
        Depends(RequestPermission("dict:data:add")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def create_dict_data(db: CurrentSessionTransaction, obj: CreateDictDataParam) -> ResponseModel:
    """Create dict data."""
    await dict_data_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    "/{pk}",
    summary="更新字典数据",
    dependencies=[
        Depends(RequestPermission("dict:data:edit")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def update_dict_data(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description="字典数据 ID")],
    obj: UpdateDictDataParam,
) -> ResponseModel:
    """Update dict data."""
    count = await dict_data_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "",
    summary="批量删除字典数据",
    dependencies=[
        Depends(RequestPermission("dict:data:del")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def delete_dict_datas(db: CurrentSessionTransaction, obj: DeleteDictDataParam) -> ResponseModel:
    """Delete dict datas."""
    count = await dict_data_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()
