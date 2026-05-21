"""Router."""

from fastapi import APIRouter

from backend.core.conf import settings
from backend.app.s3.api.v1.file import router as file_router
from backend.app.s3.api.v1.storage import router as business_router


v1 = APIRouter(prefix=f"{settings.FASTAPI_API_V1_PATH}/s3", tags=["S3"])

v1.include_router(business_router, prefix="/storages")
v1.include_router(file_router, prefix="/files")
