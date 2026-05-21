"""Storage Service."""

from typing import Any
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.s3.model import S3Storage
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.app.s3.crud.storage import s3_storage_dao
from backend.app.s3.schema.storage import CreateS3StorageParam, DeleteS3StorageParam, UpdateS3StorageParam


class S3StorageService:
    """S3 Storage Service."""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> S3Storage:
        """获取 S3 存储.

        :param db: 数据库会话
        :param pk: S3 存储 ID
        :return:
        """
        s3_storage = await s3_storage_dao.get(db, pk)
        if not s3_storage:
            raise errors.NotFoundError(msg="S3 存储不存在")
        return s3_storage

    @staticmethod
    async def get_list(db: AsyncSession, name: str | None, region: str | None) -> dict[str, Any]:
        """获取 S3 存储列表.

        :param db: 数据库会话
        :param name: 存储名称
        :param region: 区域
        :return:
        """
        s3_storage_select = await s3_storage_dao.get_select(name, region)
        return await paging_data(db, s3_storage_select)

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[S3Storage]:
        """获取所有 S3 存储.

        :param db: 数据库会话
        :return:
        """
        return await s3_storage_dao.get_all(db)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateS3StorageParam) -> None:
        """创建 S3 存储.

        :param db: 数据库会话
        :param obj: 创建S3 存储参数
        :return:
        """
        await s3_storage_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateS3StorageParam) -> int:
        """更新 S3 存储.

        :param db: 数据库会话
        :param pk: S3 存储 ID
        :param obj: 更新S3 存储参数
        :return:
        """
        return await s3_storage_dao.update(db, pk, obj)

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteS3StorageParam) -> int:
        """删除 S3 存储.

        :param db: 数据库会话
        :param obj: S3 存储 ID 列表
        :return:
        """
        return await s3_storage_dao.delete(db, obj.pks)


s3_storage_service: S3StorageService = S3StorageService()
