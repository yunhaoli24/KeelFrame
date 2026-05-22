"""Default object storage service."""

from fastapi import UploadFile
from opendal import AsyncOperator
from fastapi.responses import Response

from backend.core.conf import settings
from backend.utils.file_ops import build_filename
from backend.common.exception import errors
from backend.app.s3.utils.file_ops import proxy_s3_get, build_s3_object_url
from backend.app.s3.schema.object_storage import ObjectUploadResult, ObjectStorageConfig


class ObjectStorageService:
    """Upload files to the configured default object storage."""

    @staticmethod
    def get_default_config() -> ObjectStorageConfig:
        """Resolve the default object storage configuration from settings."""
        return ObjectStorageConfig(
            endpoint=settings.OBJECT_STORAGE_DEFAULT_ENDPOINT,
            access_key=settings.OBJECT_STORAGE_DEFAULT_ACCESS_KEY,
            secret_key=settings.OBJECT_STORAGE_DEFAULT_SECRET_KEY,
            bucket=settings.OBJECT_STORAGE_DEFAULT_BUCKET,
            prefix=settings.OBJECT_STORAGE_DEFAULT_PREFIX.strip("/"),
            region=settings.OBJECT_STORAGE_DEFAULT_REGION,
        )

    @staticmethod
    def get_operator(config: ObjectStorageConfig) -> AsyncOperator:
        """Create an async S3-compatible operator."""
        root = f"/{config.prefix}" if config.prefix else "/"
        return AsyncOperator(
            "s3",
            endpoint=config.endpoint,
            access_key_id=config.access_key,
            secret_access_key=config.secret_key,
            bucket=config.bucket,
            root=root,
            region=config.region,
        )

    @classmethod
    async def upload_default_file(cls, file: UploadFile) -> ObjectUploadResult:
        """Upload a file to the default object storage and return object metadata."""
        filename = build_filename(file)
        config = cls.get_default_config()
        operator = cls.get_operator(config)
        contents = await file.read()
        if not contents:
            raise errors.RequestError(msg="上传文件不能为空")
        await operator.write(filename, contents)
        await file.close()
        return ObjectUploadResult(filename=filename, size=len(contents))

    @classmethod
    async def read_default_file(cls, filename: str) -> bytes:
        """Read a file from the default object storage."""
        config = cls.get_default_config()
        operator = cls.get_operator(config)
        return bytes(await operator.read(filename))  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]

    @classmethod
    async def proxy_default_file(cls, filename: str) -> Response:
        """Forward a default object storage file download through the backend."""
        config = cls.get_default_config()
        url = build_s3_object_url(
            endpoint=config.endpoint,
            bucket=config.bucket,
            prefix=config.prefix,
            filename=filename,
        )
        return await proxy_s3_get(url)


object_storage_service = ObjectStorageService()
