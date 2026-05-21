"""User Service."""

import random
from typing import Any, cast
from collections.abc import Sequence

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.conf import settings
from backend.common.enums import UserPermissionType
from backend.common.context import ctx
from backend.database.redis import redis_client
from backend.app.admin.model import Role, User
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.utils.serializers import select_join_serialize
from backend.app.admin.model.m2m import user_role
from backend.app.admin.schema.user import (
    AddUserParam,
    UpdateUserParam,
    ResetPasswordParam,
)
from backend.app.admin.crud.crud_dept import dept_dao
from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.crud.crud_user import user_dao
from backend.common.response.response_code import CustomErrorCode
from backend.app.admin.utils.password_security import password_verify, validate_new_password
from backend.app.admin.schema.user_password_history import CreateUserPasswordHistoryParam
from backend.app.admin.service.user_password_history_service import password_security_service


class UserService:
    """用户服务类."""

    @staticmethod
    async def get_userinfo(*, db: AsyncSession, pk: int | None = None, username: str | None = None) -> User:
        """获取用户信息.

        :param db: 数据库会话
        :param pk: 用户 ID
        :param username: 用户名
        :return:
        """
        if pk:
            user = await user_dao.get(db, pk)
        else:
            user = await user_dao.get_by_username(db, username or "")
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        return user

    @staticmethod
    async def get_roles(*, db: AsyncSession, pk: int) -> Sequence[Role]:
        """获取用户所有角色.

        :param db: 数据库会话
        :param pk: 用户 ID
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        stmt = select(Role).join(user_role, Role.id == user_role.c.role_id).where(user_role.c.user_id == pk)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_userinfo_with_relations(*, db: AsyncSession, pk: int) -> dict[str, Any]:
        """获取用户关联信息."""
        user = await user_dao.get_join(db, user_id=pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        return cast("dict[str, Any]", user)

    @staticmethod
    async def get_list(
        *,
        db: AsyncSession,
        dept: int | None,
        username: str | None,
        phone: str | None,
        status: int | None,
    ) -> dict[str, Any]:
        """获取用户列表.

        :param db: 数据库会话
        :param dept: 部门 ID
        :param username: 用户名
        :param phone: 手机号
        :param status: 状态
        :return:
        """
        user_select = await user_dao.get_select(dept=dept, username=username, phone=phone, status=status)
        data = await paging_data(db, user_select)
        if data["items"]:
            serialized_items = select_join_serialize(data["items"], relationships=["User-m2o-Dept", "User-m2m-Role"])
            # 确保返回的是列表，即使只有一个元素
            data["items"] = [serialized_items] if not isinstance(serialized_items, list) else serialized_items
        return data

    @staticmethod
    async def create(*, db: AsyncSession, obj: AddUserParam) -> None:
        """创建用户.

        :param db: 数据库会话
        :param obj: 用户添加参数
        :return:
        """
        if await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg="用户名已注册")
        obj.nickname = obj.nickname or f"#{random.randrange(88888, 99999)}"  # noqa: S311
        if not obj.password:
            raise errors.RequestError(msg="密码不允许为空")
        if not await dept_dao.get(db, obj.dept_id):
            raise errors.NotFoundError(msg="部门不存在")
        for role_id in obj.roles:
            if not await role_dao.get(db, role_id):
                raise errors.NotFoundError(msg="角色不存在")
        await user_dao.add(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateUserParam) -> int:
        """更新用户信息.

        :param db: 数据库会话
        :param pk: 用户 ID
        :param obj: 用户更新参数
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        if obj.username != user.username and await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg="用户名已注册")
        if obj.dept_id and obj.dept_id != user.dept_id and not await dept_dao.get(db, dept_id=obj.dept_id):
            raise errors.NotFoundError(msg="部门不存在")
        for role_id in obj.roles:
            if not await role_dao.get(db, role_id):
                raise errors.NotFoundError(msg="角色不存在")
        count = await user_dao.update(db, user.id, obj)
        await redis_client.delete(f"{settings.JWT_USER_REDIS_PREFIX}:{user.id}")
        return count

    @staticmethod
    async def update_permission(
        *, db: AsyncSession, request: Request, pk: int, permission_type: UserPermissionType
    ) -> int:
        """更新用户权限.

        :param db: 数据库会话
        :param request: FastAPI 请求对象
        :param pk: 用户 ID
        :param permission_type: 权限类型
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        if pk == request.user.id:
            raise errors.ForbiddenError(msg="禁止修改自身权限")

        match permission_type:
            case UserPermissionType.superuser:
                count = await user_dao.set_super(db, pk, is_super=not user.is_superuser)
            case UserPermissionType.staff:
                count = await user_dao.set_staff(db, pk, is_staff=not user.is_staff)
            case UserPermissionType.status:
                count = await user_dao.set_status(db, pk, 0 if user.status == 1 else 1)
            case UserPermissionType.multi_login:
                new_multi_login = not user.is_multi_login
                count = await user_dao.set_multi_login(db, pk, multi_login=new_multi_login)
                if not new_multi_login:
                    key_prefix = f"{settings.TOKEN_REDIS_PREFIX}:{user.id}"
                    await redis_client.delete_prefix(key_prefix)
            case _:
                raise errors.RequestError(msg="权限类型不存在")

        await redis_client.delete(f"{settings.JWT_USER_REDIS_PREFIX}:{user.id}")
        return count

    @staticmethod
    async def reset_password(*, db: AsyncSession, pk: int, password: str) -> int:
        """重置用户密码.

        :param db: 数据库会话
        :param pk: 用户 ID
        :param password: 新密码
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")

        await validate_new_password(db, user.id, password)
        count = await user_dao.reset_password(db, user.id, password)

        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password or "")
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)

        key_prefix = [
            f"{settings.TOKEN_REDIS_PREFIX}:{user.id}",
            f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user.id}",
            f"{settings.JWT_USER_REDIS_PREFIX}:{user.id}",
        ]
        for prefix in key_prefix:
            await redis_client.delete(prefix)
        return count

    @staticmethod
    async def update_nickname(*, db: AsyncSession, user_id: int, nickname: str) -> int:
        """更新当前用户昵称.

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param nickname: 用户昵称
        :return:
        """
        count = await user_dao.update_nickname(db, user_id, nickname)
        await redis_client.delete(f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}")
        return count

    @staticmethod
    async def update_avatar(*, db: AsyncSession, user_id: int, avatar: str) -> int:
        """更新当前用户头像.

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param avatar: 头像地址
        :return:
        """
        count = await user_dao.update_avatar(db, user_id, avatar)
        await redis_client.delete(f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}")
        return count

    @staticmethod
    async def update_email(*, db: AsyncSession, user_id: int, captcha: str, email: str) -> int:
        """更新当前用户邮箱.

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param captcha: 邮箱验证码
        :param email: 邮箱
        :return:
        """
        captcha_code = await redis_client.get(f"{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{ctx.ip}")
        if not captcha_code:
            raise errors.RequestError(msg="验证码已失效, 请重新获取")
        if captcha != captcha_code:
            raise errors.CustomError(error=CustomErrorCode.CAPTCHA_ERROR)
        await redis_client.delete(f"{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{ctx.ip}")
        count = await user_dao.update_email(db, user_id, email)
        await redis_client.delete(f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}")
        return count

    @staticmethod
    async def update_password(*, db: AsyncSession, user_id: int, obj: ResetPasswordParam) -> int:
        """更新当前用户密码.

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param obj: 密码重置参数
        :return:
        """
        user = await user_dao.get(db, user_id)

        if user is None:
            raise errors.NotFoundError(msg="用户不存在")

        if user.password and not password_verify(obj.old_password, user.password):
            raise errors.RequestError(msg="原密码错误")

        if obj.new_password != obj.confirm_password:
            raise errors.RequestError(msg="两次密码输入不一致")

        await validate_new_password(db, user_id, obj.new_password)
        count = await user_dao.reset_password(db, user_id, obj.new_password)

        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password or "")
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)

        key_prefix = [
            f"{settings.TOKEN_REDIS_PREFIX}:{user_id}",
            f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}",
            f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}",
        ]
        for prefix in key_prefix:
            await redis_client.delete_prefix(prefix)
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """删除用户.

        :param db: 数据库会话
        :param pk: 用户 ID
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        count = await user_dao.delete(db, user.id)
        key_prefix = [
            f"{settings.TOKEN_REDIS_PREFIX}:{user.id}",
            f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user.id}",
        ]
        for key in key_prefix:
            await redis_client.delete_prefix(key)
        return count


user_service: UserService = UserService()
