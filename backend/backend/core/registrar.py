"""Registrar."""

from typing import Any, cast
from asyncio import create_task
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import socketio
import prometheus_client
from fastapi import Depends, FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from starlette_context.plugins import RequestIdPlugin
from starlette_context.middleware import ContextMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from backend import __version__
from backend.core.conf import settings
from backend.common.log import setup_logging, set_custom_logfile
from backend.utils.otel import init_otel
from backend.utils.openapi import simplify_operation_ids
from backend.database.redis import redis_client
from backend.utils.trace_id import OtelTraceIdPlugin
from backend.utils.demo_site import demo_site
from backend.utils.serializers import MsgSpecJSONResponse
from backend.utils.health_check import ensure_unique_route_names
from backend.middleware.state_middleware import StateMiddleware
from backend.middleware.access_middleware import AccessMiddleware
from backend.common.response.response_code import StandardResponseCode
from backend.middleware.jwt_auth_middleware import JwtAuthMiddleware
from backend.middleware.opera_log_middleware import OperaLogMiddleware
from backend.common.exception.exception_handler import register_exception


@asynccontextmanager
async def register_init(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
    """启动初始化.

    :param app: FastAPI 应用实例
    :return:
    """
    # 初始化 redis
    await redis_client.open()

    # 创建操作日志任务
    task = create_task(OperaLogMiddleware.consumer())
    _ = task

    yield

    # 关闭 redis 连接
    await redis_client.aclose()


def register_app() -> FastAPI:
    """注册 FastAPI 应用."""
    app = FastAPI(
        title=settings.FASTAPI_TITLE,
        version=__version__,
        description=settings.FASTAPI_DESCRIPTION,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        default_response_class=MsgSpecJSONResponse,
        lifespan=register_init,
    )

    # 注册组件
    register_logger()
    register_socket_app(app)
    register_middleware(app)
    register_router(app)
    register_page(app)
    register_exception(app)

    if settings.GRAFANA_METRICS:
        register_metrics(app)

    return app


def register_logger() -> None:
    """注册日志."""
    setup_logging()
    set_custom_logfile()


def register_middleware(app: FastAPI) -> None:
    """注册中间件（执行顺序从下往上）.

    :param app: FastAPI 应用实例
    :return:
    """
    # Opera log
    app.add_middleware(OperaLogMiddleware)

    # State
    app.add_middleware(StateMiddleware)

    # JWT auth
    app.add_middleware(
        AuthenticationMiddleware,
        backend=JwtAuthMiddleware(),
        on_error=JwtAuthMiddleware.auth_exception_handler,
    )

    # Access log
    app.add_middleware(AccessMiddleware)

    # ContextVar
    plugins: list[Any] = [OtelTraceIdPlugin()] if settings.GRAFANA_METRICS else [RequestIdPlugin(validate=True)]
    app.add_middleware(
        ContextMiddleware,
        plugins=plugins,
        default_error_response=MsgSpecJSONResponse(
            content={"code": StandardResponseCode.HTTP_400, "msg": "BAD_REQUEST", "data": None},
            status_code=StandardResponseCode.HTTP_400,
        ),
    )

    # CORS
    # https://github.com/fastapi-practices/fastapi_best_architecture/pull/789/changes
    # https://github.com/open-telemetry/opentelemetry-python-contrib/issues/4031
    if settings.MIDDLEWARE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )


def register_router(app: FastAPI) -> None:
    """注册路由.

    :param app: FastAPI 应用实例
    :return:
    """
    dependencies = [Depends(demo_site)] if settings.DEMO_MODE else None

    # API
    from backend.app.router import router  # noqa: PLC0415

    app.include_router(router, dependencies=dependencies)

    # Extra
    ensure_unique_route_names(app)
    simplify_operation_ids(app)


def register_page(app: FastAPI) -> None:
    """注册分页查询功能.

    :param app: FastAPI 应用实例
    :return:
    """
    add_pagination(app)


def register_socket_app(app: FastAPI) -> None:
    """注册 Socket.IO 应用.

    :param app: FastAPI 应用实例
    :return:
    """
    from backend.common.socketio.server import sio  # noqa: PLC0415

    socket_app = socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=app,
        # 切勿删除此配置：https://github.com/pyropy/fastapi-socketio/issues/51
        socketio_path="/ws/socket.io",
    )
    app.mount("/ws", cast("Any", socket_app))


def register_metrics(app: FastAPI) -> None:
    """注册指标.

    :param app: FastAPI 应用实例
    :return:
    """
    prometheus = cast("Any", prometheus_client)
    metrics_app = prometheus.make_asgi_app()
    app.mount("/metrics", metrics_app)

    init_otel(app)
