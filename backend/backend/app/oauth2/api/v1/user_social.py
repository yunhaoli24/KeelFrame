"""User Social."""

from fastapi import Request, APIRouter

from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.common.security.jwt import DependsJwtAuth
from backend.app.oauth2.enums import UserSocialType
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.app.oauth2.service.user_social_service import user_social_service


router = APIRouter()


@router.get("/me/bindings", summary="获取用户已绑定的社交账号", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_user_bindings(db: CurrentSession, request: Request) -> ResponseSchemaModel[list[str]]:
    """Get User Bindings."""
    bindings = await user_social_service.get_bindings(db=db, user_id=request.user.id)
    return response_base.success(data=bindings)


@router.get("/me/binding", summary="获取绑定授权链接", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def get_binding_auth_url(request: Request, source: UserSocialType) -> ResponseSchemaModel[str]:
    """Get Binding Auth Url."""
    binding_url = await user_social_service.get_binding_auth_url(user_id=request.user.id, source=source)
    return response_base.success(data=binding_url)


@router.delete("/me/unbinding", summary="解绑用户社交账号", dependencies=[DependsJwtAuth])  # pyright: ignore[reportGeneralTypeIssues]
async def unbinding_user(db: CurrentSessionTransaction, request: Request, source: UserSocialType) -> ResponseModel:
    """Unbinding User."""
    await user_social_service.unbinding(db=db, user_id=request.user.id, source=source)
    return response_base.success()
