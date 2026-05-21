"""S3 File API v1."""

from typing import Annotated

from fastapi import File, Query, Depends, APIRouter, UploadFile

from backend.database.db import CurrentSession
from backend.utils.file_ops import upload_file_verify
from backend.common.exception import errors
from backend.common.dataclasses import UploadUrl
from backend.app.s3.crud.storage import s3_storage_dao
from backend.common.security.rbac import DependsRBAC
from backend.app.s3.utils.file_ops import write_file
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseSchemaModel, response_base


router = APIRouter()


@router.post(
    "/upload",
    summary="S3 文件上传",
    dependencies=[
        Depends(RequestPermission("s3:file:upload")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def upload_s3_files(
    db: CurrentSession, file: Annotated[UploadFile, File()], storage: Annotated[int, Query(description="S3 存储 ID")]
) -> ResponseSchemaModel[UploadUrl]:
    """Upload S3 Files."""
    s3_storage = await s3_storage_dao.get(db, storage)
    if not s3_storage:
        raise errors.NotFoundError(msg="S3 存储不存在")
    upload_file_verify(file)
    filename = await write_file(s3_storage, file)

    bucket_path = f"/{s3_storage.bucket}"
    if s3_storage.prefix:
        prefix = s3_storage.prefix if s3_storage.prefix.startswith("/") else f"/{s3_storage.prefix}"
        root = f"{bucket_path}{prefix}"
    else:
        root = bucket_path

    url = f"{root.rstrip('/')}/{filename}"
    return response_base.success(data={"url": url})
