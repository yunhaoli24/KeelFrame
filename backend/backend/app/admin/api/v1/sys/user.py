"""User."""

from typing import Annotated

from fastapi import Body, Path, Query, Depends, Request, APIRouter

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.enums import UserPermissionType
from backend.common.pagination import PageData, DependsPagination
from backend.common.security.jwt import DependsJwtAuth, DependsSuperUser
from backend.common.security.rbac import DependsRBAC
from backend.app.admin.schema.role import GetRoleDetail
from backend.app.admin.schema.user import (
    AddUserParam,
    UpdateUserParam,
    GetUserInfoDetail,
    ResetPasswordParam,
    GetUserInfoWithRelationDetail,
    GetCurrentUserInfoWithRelationDetail,
)
from backend.common.security.permission import RequestPermission
from backend.app.admin.service.user_service import user_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base


router: APIRouter = APIRouter()


@router.get("/me", summary="获取当前用户信息", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_current_user(request: Request) -> ResponseSchemaModel[GetCurrentUserInfoWithRelationDetail]:
    """Get Current User."""
    data = request.user.model_dump()
    return response_base.success(data=data)


@router.get("/{pk}", summary="获取用户信息", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_userinfo(
    db: CurrentSession,
    pk: Annotated[int, Path(description="用户 ID")],
) -> ResponseSchemaModel[GetUserInfoWithRelationDetail]:
    """Get Userinfo."""
    data = await user_service.get_userinfo_with_relations(db=db, pk=pk)
    return response_base.success(data=data)


@router.get("/{pk}/roles", summary="获取用户所有角色", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_user_roles(
    db: CurrentSession, pk: Annotated[int, Path(description="用户 ID")]
) -> ResponseSchemaModel[list[GetRoleDetail]]:
    """Get User Roles."""
    data = await user_service.get_roles(db=db, pk=pk)
    return response_base.success(data=data)


@router.get(
    "",
    summary="分页获取所有用户",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_users_paginated(
    db: CurrentSession,
    dept: Annotated[int | None, Query(description="部门 ID")] = None,
    username: Annotated[str | None, Query(description="用户名")] = None,
    phone: Annotated[str | None, Query(description="手机号")] = None,
    status: Annotated[int | None, Query(description="状态")] = None,
) -> ResponseSchemaModel[PageData[GetUserInfoWithRelationDetail]]:
    """Get Users Paginated."""
    page_data = await user_service.get_list(db=db, dept=dept, username=username, phone=phone, status=status)
    return response_base.success(data=page_data)


@router.post("", summary="创建用户", dependencies=[DependsSuperUser])  # pyright: ignore[reportGeneralTypeIssues]
async def create_user(db: CurrentSessionTransaction, obj: AddUserParam) -> ResponseSchemaModel[GetUserInfoDetail]:
    """Create User."""
    await user_service.create(db=db, obj=obj)
    await db.flush()
    data = await user_service.get_userinfo(db=db, username=obj.username)
    return response_base.success(data=GetUserInfoDetail.model_validate(data))


@router.put("/{pk}", summary="更新用户信息", dependencies=[DependsSuperUser])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description="用户 ID")],
    obj: UpdateUserParam,
) -> ResponseModel:
    """Update User."""
    count = await user_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/{pk}/permissions", summary="更新用户权限", dependencies=[DependsSuperUser])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user_permission(
    db: CurrentSessionTransaction,
    request: Request,
    pk: Annotated[int, Path(description="用户 ID")],
    permission_type: Annotated[UserPermissionType, Query(description="权限类型")],
) -> ResponseModel:
    """Update User Permission."""
    count = await user_service.update_permission(db=db, request=request, pk=pk, permission_type=permission_type)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/me/password", summary="更新当前用户密码", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user_password(
    db: CurrentSessionTransaction, request: Request, obj: ResetPasswordParam
) -> ResponseModel:
    """Update User Password."""
    count = await user_service.update_password(db=db, user_id=request.user.id, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/{pk}/password", summary="重置用户密码", dependencies=[DependsSuperUser])  # pyright: ignore[reportGeneralTypeIssues]
async def reset_user_password(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description="用户 ID")],
    password: Annotated[str, Body(embed=True, description="新密码")],
) -> ResponseModel:
    """Reset User Password."""
    count = await user_service.reset_password(db=db, pk=pk, password=password)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/me/nickname", summary="更新当前用户昵称", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user_nickname(
    db: CurrentSessionTransaction,
    request: Request,
    nickname: Annotated[str, Body(embed=True, description="用户昵称")],
) -> ResponseModel:
    """Update User Nickname."""
    count = await user_service.update_nickname(db=db, user_id=request.user.id, nickname=nickname)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/me/avatar", summary="更新当前用户头像", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user_avatar(
    db: CurrentSessionTransaction,
    request: Request,
    avatar: Annotated[str, Body(embed=True, description="用户头像地址")],
) -> ResponseModel:
    """Update User Avatar."""
    count = await user_service.update_avatar(db=db, user_id=request.user.id, avatar=avatar)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put("/me/email", summary="更新当前用户邮箱", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def update_user_email(
    db: CurrentSessionTransaction,
    request: Request,
    captcha: Annotated[str, Body(embed=True, description="邮箱验证码")],
    email: Annotated[str, Body(embed=True, description="用户邮箱")],
) -> ResponseModel:
    """Update User Email."""
    count = await user_service.update_email(db=db, user_id=request.user.id, captcha=captcha, email=email)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    path="/{pk}",
    summary="删除用户",
    dependencies=[
        Depends(RequestPermission("sys:user:del")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def delete_user(db: CurrentSessionTransaction, pk: Annotated[int, Path(description="用户 ID")]) -> ResponseModel:
    """Delete User."""
    count = await user_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
