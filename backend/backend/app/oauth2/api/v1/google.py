"""Google OAuth2 API v1."""

import json
import uuid
from typing import Any, Annotated

from fastapi import Depends, Response, APIRouter, BackgroundTasks
from fastapi_oauth20 import FastAPIOAuth20  # pyright: ignore[reportMissingModuleSource]
from starlette.responses import RedirectResponse

from backend.core.conf import settings
from backend.database.db import CurrentSessionTransaction
from backend.database.redis import redis_client
from backend.app.oauth2.enums import UserSocialType, UserSocialAuthType
from backend.app.oauth2.clients import google_client
from backend.common.security.limiter import create_rate_limiter
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.app.oauth2.service.oauth2_service import oauth2_service


router = APIRouter()


@router.get("", summary="获取 google 授权链接")  # pyright: ignore[reportGeneralTypeIssues]
async def get_google_oauth2_url() -> ResponseSchemaModel[str]:
    """Get Google Oauth2 Url."""
    state = str(uuid.uuid4())

    await redis_client.setex(
        f"{settings.OAUTH2_STATE_REDIS_PREFIX}:{state}",
        settings.OAUTH2_STATE_EXPIRE_SECONDS,
        json.dumps({"type": UserSocialAuthType.login.value}),
    )

    auth_url = await google_client.get_authorization_url(redirect_uri=settings.OAUTH2_GOOGLE_REDIRECT_URI, state=state)
    return response_base.success(data=auth_url)


@router.get(
    "/callback",
    summary="google 授权自动重定向",
    description="google 授权后, 自动重定向到当前地址并获取用户信息, 通过用户信息自动创建系统用户",
    dependencies=[Depends(create_rate_limiter(limit=5, minutes=1))],
)  # pyright: ignore[reportGeneralTypeIssues]
async def google_oauth2_callback(  # noqa: ANN201
    db: CurrentSessionTransaction,
    response: Response,
    background_tasks: BackgroundTasks,
    oauth2: Annotated[
        tuple[dict[str, Any], str],
        Depends(FastAPIOAuth20(google_client, redirect_uri=settings.OAUTH2_GOOGLE_REDIRECT_URI)),
    ],
):
    """Google Oauth2 Callback."""
    token_data, state = oauth2
    access_token = token_data["access_token"]
    user = await google_client.get_userinfo(access_token)
    data = await oauth2_service.login_or_binding(
        db=db,
        response=response,
        background_tasks=background_tasks,
        user=user,
        social=UserSocialType.google,
        state=state,
    )

    # 绑定流程
    if data is None:
        return RedirectResponse(url=settings.OAUTH2_FRONTEND_BINDING_REDIRECT_URI)

    # 登录流程
    return RedirectResponse(
        url=f"{settings.OAUTH2_FRONTEND_LOGIN_REDIRECT_URI}?access_token={data.access_token}&session_uuid={data.session_uuid}",
    )
