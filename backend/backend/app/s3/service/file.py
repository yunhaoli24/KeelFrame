"""S3 file service."""

from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.s3.model import S3File
from backend.app.s3.crud.file import s3_file_dao
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.app.s3.schema.file import CreateS3FileParam
from backend.app.s3.service.object_storage import object_storage_service


class S3FileService:
    """S3 file service."""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> S3File:
        """获取 S3 文件."""
        s3_file = await s3_file_dao.get(db, pk)
        if not s3_file:
            raise errors.NotFoundError(msg="S3 文件不存在")
        return s3_file

    @staticmethod
    async def get_list(*, db: AsyncSession, user_id: int | None = None) -> dict[str, Any]:
        """获取 S3 文件列表."""
        s3_file_select = await s3_file_dao.get_select(user_id=user_id)
        return await paging_data(db, s3_file_select)

    @staticmethod
    async def create_from_upload(*, db: AsyncSession, user_id: int, file: UploadFile) -> S3File:
        """上传对象并记录文件归属."""
        original_filename = file.filename or ""
        content_type = file.content_type
        upload_result = await object_storage_service.upload_default_file(file)
        config = object_storage_service.get_default_config()
        obj = CreateS3FileParam(
            user_id=user_id,
            filename=upload_result.filename,
            original_filename=original_filename,
            content_type=content_type,
            size=upload_result.size,
            bucket=config.bucket,
            prefix=config.prefix,
            remark=None,
        )
        return await s3_file_dao.create(db, obj)


s3_file_service: S3FileService = S3FileService()
