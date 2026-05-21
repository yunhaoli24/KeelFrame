"""Router."""

from fastapi import APIRouter

from backend.app.s3.api.router import v1 as s3_v1
from backend.app.task.api.router import v1 as task_v1
from backend.app.admin.api.router import v1 as admin_v1
from backend.app.email.api.router import v1 as email_v1
from backend.app.oauth2.api.router import v1 as oauth2_v1


router: APIRouter = APIRouter()

router.include_router(admin_v1)
router.include_router(task_v1)
router.include_router(oauth2_v1)
router.include_router(email_v1)
router.include_router(s3_v1)
