"""S3 File API v1."""

from typing import Annotated
from urllib.parse import quote

from fastapi import File, Query, Depends, APIRouter, UploadFile
from fastapi.responses import Response

from backend.core.conf import settings
from backend.database.db import CurrentSession
from backend.utils.file_ops import upload_file_verify
from backend.common.exception import errors
from backend.common.dataclasses import UploadUrl
from backend.app.s3.crud.storage import s3_storage_dao
from backend.common.security.rbac import DependsRBAC
from backend.app.s3.utils.file_ops import write_file, proxy_s3_get, build_s3_object_url
from backend.common.security.permission import RequestPermission
from backend.common.response.response_schema import ResponseSchemaModel, response_base


router = APIRouter()


def build_s3_file_download_url(storage: int, filename: str) -> str:
    """Build the backend download URL returned to frontend clients."""
    return f"{settings.FASTAPI_API_V1_PATH}/s3/files/path/{storage}/{quote(filename, safe='/')}"


async def proxy_s3_file(s3_storage_id: int, s3_storage_filename: str, db: CurrentSession) -> Response:
    """Proxy a configured S3 file through the backend."""
    s3_storage = await s3_storage_dao.get(db, s3_storage_id)
    if not s3_storage:
        raise errors.NotFoundError(msg="S3 存储不存在")
    url = build_s3_object_url(
        endpoint=s3_storage.endpoint,
        bucket=s3_storage.bucket,
        prefix=s3_storage.prefix,
        filename=s3_storage_filename,
    )
    return await proxy_s3_get(url)


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
    return response_base.success(data={"url": build_s3_file_download_url(storage, filename)})


@router.get(
    "/path/{storage}/{filename:path}",
    summary="S3 文件路径代理",
    dependencies=[
        Depends(RequestPermission("s3:file:download")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def proxy_s3_file_path(
    db: CurrentSession,
    storage: int,
    filename: str,
) -> Response:
    """Proxy S3 File Path."""
    return await proxy_s3_file(storage, filename, db)
