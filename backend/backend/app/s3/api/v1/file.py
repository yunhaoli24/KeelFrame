"""S3 File API v1."""

from typing import Annotated
from urllib.parse import quote

from fastapi import File, Depends, Request, APIRouter, UploadFile
from fastapi.responses import Response

from backend.core.conf import settings
from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.utils.file_ops import upload_file_verify
from backend.common.exception import errors
from backend.common.pagination import PageData, DependsPagination
from backend.app.s3.schema.file import GetS3FileDetail
from backend.common.dataclasses import UploadUrl
from backend.app.s3.service.file import s3_file_service
from backend.common.security.rbac import DependsRBAC
from backend.common.security.permission import RequestPermission
from backend.app.s3.service.object_storage import object_storage_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base


router = APIRouter()


def build_s3_file_download_url(file_id: int, filename: str) -> str:
    """Build the backend download URL returned to frontend clients."""
    return f"{settings.FASTAPI_API_V1_PATH}/s3/files/path/{file_id}/{quote(filename, safe='/')}"


def build_s3_file_detail(s3_file: GetS3FileDetail) -> dict[str, object]:
    """Build public S3 file response data."""
    data = s3_file.model_dump()
    data["url"] = build_s3_file_download_url(s3_file.id, s3_file.filename)
    return data


@router.post(
    "/upload",
    summary="S3 文件上传",
    dependencies=[
        Depends(RequestPermission("s3:file:upload")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def upload_s3_files(
    db: CurrentSessionTransaction,
    request: Request,
    file: Annotated[UploadFile, File()],
) -> ResponseSchemaModel[UploadUrl]:
    """Upload S3 Files."""
    upload_file_verify(file)
    s3_file = await s3_file_service.create_from_upload(db=db, user_id=request.user.id, file=file)
    return response_base.success(data={"url": build_s3_file_download_url(s3_file.id, s3_file.filename)})


@router.get(
    "",
    summary="分页获取当前用户 S3 文件",
    dependencies=[
        Depends(RequestPermission("s3:file:list")),
        DependsRBAC,
        DependsPagination,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_s3_files_paginated(
    db: CurrentSession, request: Request
) -> ResponseSchemaModel[PageData[GetS3FileDetail]]:
    """Get current user's S3 files paginated."""
    user_id = None if request.user.is_superuser else request.user.id
    page_data = await s3_file_service.get_list(db=db, user_id=user_id)
    page_data["items"] = [build_s3_file_detail(GetS3FileDetail.model_validate(item)) for item in page_data["items"]]
    return response_base.success(data=page_data)


@router.get(
    "/path/{file_id}/{filename:path}",
    summary="S3 文件路径代理",
    dependencies=[
        Depends(RequestPermission("s3:file:download")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def proxy_s3_file_path(
    db: CurrentSession,
    request: Request,
    file_id: int,
    filename: str,
) -> Response:
    """Proxy S3 File Path."""
    s3_file = await s3_file_service.get(db=db, pk=file_id)
    if s3_file.filename != filename:
        raise errors.NotFoundError(msg="S3 文件不存在")
    if not request.user.is_superuser and s3_file.user_id != request.user.id:
        raise errors.AuthorizationError
    return await object_storage_service.proxy_default_file(s3_file.filename)


@router.get(
    "/{pk}",
    summary="获取 S3 文件详情",
    dependencies=[
        Depends(RequestPermission("s3:file:detail")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def get_s3_file(db: CurrentSession, request: Request, pk: int) -> ResponseSchemaModel[GetS3FileDetail]:
    """Get S3 file detail."""
    s3_file = await s3_file_service.get(db=db, pk=pk)
    if not request.user.is_superuser and s3_file.user_id != request.user.id:
        raise errors.AuthorizationError
    return response_base.success(data=build_s3_file_detail(GetS3FileDetail.model_validate(s3_file)))
