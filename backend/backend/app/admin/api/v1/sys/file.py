"""File."""

from typing import Annotated
from urllib.parse import quote

from fastapi import File, Depends, APIRouter, UploadFile
from fastapi.responses import Response

from backend.core.conf import settings
from backend.utils.file_ops import upload_file_verify
from backend.common.dataclasses import UploadUrl
from backend.common.security.rbac import DependsRBAC
from backend.common.security.permission import RequestPermission
from backend.app.s3.service.object_storage import object_storage_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base


router: APIRouter = APIRouter()


def build_system_file_download_url(filename: str) -> str:
    """Build the backend download URL returned to frontend clients."""
    return f"{settings.FASTAPI_API_V1_PATH}/sys/files/path/{quote(filename, safe='/')}"


@router.post(
    "/upload",
    summary="本地文件上传",
    dependencies=[
        Depends(RequestPermission("sys:file:upload")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def upload_files(file: Annotated[UploadFile, File()]) -> ResponseSchemaModel[UploadUrl]:
    """Upload Files."""
    upload_file_verify(file)
    filename = await object_storage_service.upload_default_file(file)
    return response_base.success(data={"url": build_system_file_download_url(filename)})


@router.get(
    "/path/{filename:path}",
    summary="系统文件路径代理",
    dependencies=[
        Depends(RequestPermission("sys:file:download")),
        DependsRBAC,
    ],
)  # pyright: ignore[reportGeneralTypeIssues]
async def proxy_file_path(filename: str) -> Response:
    """Proxy File Path."""
    return await object_storage_service.proxy_default_file(filename)
