"""S3 file CRUD."""

from typing import Any, cast

from sqlalchemy import Select
from sqlalchemy_crud_plus import CRUDPlus
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.s3.model import S3File
from backend.app.s3.schema.file import CreateS3FileParam


class CRUDS3File(CRUDPlus[S3File]):
    """S3 file CRUD operations."""

    async def get(self, db: AsyncSession, pk: int) -> S3File | None:
        """获取 S3 文件."""
        return cast("S3File | None", await self.select_model(db, pk))

    async def get_select(self, user_id: int | None = None) -> Select[Any]:
        """获取 S3 文件列表查询表达式."""
        filters = {}
        if user_id is not None:
            filters["user_id"] = user_id
        return await cast("Any", self).select_order("id", "desc", **filters)

    async def create(self, db: AsyncSession, obj: CreateS3FileParam) -> S3File:
        """创建 S3 文件."""
        return await self.create_model(db, obj, flush=True)


s3_file_dao: CRUDS3File = CRUDS3File(S3File)
