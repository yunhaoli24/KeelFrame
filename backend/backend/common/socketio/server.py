# pragma: exclude file
"""Server."""

import urllib.parse
from typing import Any, cast

import socketio

from backend.core.conf import settings
from backend.common.log import log
from backend.database.redis import redis_client
from backend.common.security.jwt import jwt_authentication


# 创建 Socket.IO 服务器实例
sio = socketio.AsyncServer(  # pyright: ignore[reportGeneralTypeIssues]
    client_manager=socketio.AsyncRedisManager(  # pyright: ignore[reportGeneralTypeIssues]
        f"redis://:{urllib.parse.quote(settings.REDIS_PASSWORD)}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}",
    ),
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    cors_credentials=True,
    namespaces=["/ws"],
)


@sio.event  # pyright: ignore[reportGeneralTypeIssues]
async def connect(_sid: str, _environ: dict[str, Any], auth: dict[str, Any] | None) -> bool:
    """Socket 连接事件."""
    if not auth:
        log.error("WebSocket 连接失败: 无授权")
        return False

    session_uuid = auth.get("session_uuid")
    token = auth.get("token")
    if not token or not session_uuid:
        log.error("WebSocket 连接失败: 授权失败, 请检查")
        return False

    # 免授权直连
    if token == settings.WS_NO_AUTH_MARKER:
        await cast("Any", redis_client).sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
        return True

    try:
        await jwt_authentication(token)
    except Exception as e:
        log.info(f"WebSocket 连接失败: {e!s}")
        return False

    await cast("Any", redis_client).sadd(settings.TOKEN_ONLINE_REDIS_PREFIX, session_uuid)
    return True


@sio.event  # pyright: ignore[reportGeneralTypeIssues]
async def disconnect(_sid: str) -> None:
    """Socket 断开连接事件."""
    await cast("Any", redis_client).spop(settings.TOKEN_ONLINE_REDIS_PREFIX)
