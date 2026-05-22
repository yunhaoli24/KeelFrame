"""Opera Log Middleware."""  # pragma: exclude file

import time
from typing import Any, cast
from asyncio import Queue

from fastapi import Response
from starlette.requests import Request
from starlette.datastructures import UploadFile
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.conf import settings
from backend.common.log import log
from backend.database.db import async_db_session
from backend.common.enums import StatusType, OperaLogCipherType
from backend.common.queue import batch_dequeue
from backend.utils.encrypt import AESCipher, Md5Cipher, ItsDCipher
from backend.common.context import ctx
from backend.utils.trace_id import get_request_trace_id
from backend.app.admin.schema.opera_log import CreateOperaLogParam
from backend.common.prometheus.instruments import (
    PROMETHEUS_REQUEST_COUNTER,
    PROMETHEUS_RESPONSE_COUNTER,
    PROMETHEUS_EXCEPTION_COUNTER,
    PROMETHEUS_REQUEST_IN_PROGRESS_GAUGE,
    PROMETHEUS_REQUEST_COST_TIME_HISTOGRAM,
)
from backend.common.response.response_code import StandardResponseCode
from backend.app.admin.service.opera_log_service import opera_log_service


class OperaLogMiddleware(BaseHTTPMiddleware):
    """操作日志中间件."""

    opera_log_queue: Queue[CreateOperaLogParam] = Queue(maxsize=100000)

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # noqa: ANN401
        """处理请求并记录操作日志.

        :param request: FastAPI 请求对象
        :param call_next: 下一个中间件或路由处理函数
        :return:
        """
        response: Response | None = None
        path = request.url.path

        if path in settings.OPERA_LOG_PATH_EXCLUDE or not path.startswith(f"{settings.FASTAPI_API_V1_PATH}"):
            response = await call_next(request)
        else:
            method = request.method
            args = await self.get_request_args(request)
            PROMETHEUS_REQUEST_IN_PROGRESS_GAUGE.labels(
                app_name=settings.GRAFANA_APP_NAME, method=method, path=path
            ).inc()
            PROMETHEUS_REQUEST_COUNTER.labels(app_name=settings.GRAFANA_APP_NAME, method=method, path=path).inc()

            # 执行请求
            code = 200
            msg = "Success"
            status = StatusType.enable
            error = None
            try:
                response = await call_next(request)
                elapsed = round((time.perf_counter() - ctx.perf_time) * 1000, 3)
                exception_keys = [
                    "__request_http_exception__",
                    "__request_validation_exception__",
                    "__request_assertion_error__",
                    "__request_custom_exception__",
                ]
                for exception_key in exception_keys:
                    exception = ctx.get(exception_key)
                    if exception:
                        code = exception.get("code")
                        msg = exception.get("msg")
                        log.error(f"请求异常: {msg}")
                        PROMETHEUS_EXCEPTION_COUNTER.labels(
                            app_name=settings.GRAFANA_APP_NAME,
                            method=method,
                            path=path,
                            exception_type=exception_key,
                        ).inc()
                        break
            except Exception as e:
                elapsed = round((time.perf_counter() - ctx.perf_time) * 1000, 3)
                code = getattr(e, "code", StandardResponseCode.HTTP_500)  # 兼容 SQLAlchemy 异常用法
                msg = getattr(e, "msg", str(e))  # 不建议使用 traceback 模块获取错误信息，会暴漏代码信息
                status = StatusType.disable
                error = e
                log.error(f"请求异常: {e!s}")
                PROMETHEUS_EXCEPTION_COUNTER.labels(
                    app_name=settings.GRAFANA_APP_NAME, method=method, path=path, exception_type=type(e).__name__
                ).inc()
            else:
                PROMETHEUS_REQUEST_COST_TIME_HISTOGRAM.labels(
                    app_name=settings.GRAFANA_APP_NAME, method=method, path=path
                ).observe(elapsed, exemplar={"TraceID": get_request_trace_id()})
            finally:
                PROMETHEUS_RESPONSE_COUNTER.labels(
                    app_name=settings.GRAFANA_APP_NAME, method=method, path=path, status_code=code
                ).inc()
                PROMETHEUS_REQUEST_IN_PROGRESS_GAUGE.labels(
                    app_name=settings.GRAFANA_APP_NAME, method=method, path=path
                ).dec()

            # 此信息只能在请求后获取
            route = request.scope.get("route")
            summary = route.summary or "" if route else ""

            try:
                # 此信息来源于 JWT 认证中间件
                username = request.user.username
            except AttributeError:
                username = None

            # 日志记录
            log.debug(f"接口摘要: [{summary}]")
            log.debug(f"请求地址: [{ctx.ip}]")
            log.debug(f"请求参数: {args}")
            log.info(f"{ctx.ip: <15} | {request.method: <8} | {code!s: <6} | {path} | {elapsed:.3f}ms")
            if request.method != "OPTIONS":
                log.debug("<-- 请求结束")

            # 日志创建
            opera_log_in = CreateOperaLogParam(
                trace_id=get_request_trace_id(),
                username=username,
                method=method,
                title=summary,
                path=path,
                ip=ctx.ip,
                country=ctx.country,
                region=ctx.region,
                city=ctx.city,
                user_agent=ctx.user_agent,
                os=ctx.os,
                browser=ctx.browser,
                device=ctx.device,
                args=args,
                status=status,
                code=str(code),
                msg=msg,
                cost_time=elapsed,  # 可能和日志存在微小差异（可忽略）
                opera_time=ctx.start_time,
            )
            await self.opera_log_queue.put(opera_log_in)

            # 错误抛出
            if error:
                raise error from None

        if response is None:
            msg = "response should not be None"
            raise RuntimeError(msg)
        return response

    async def get_request_args(self, request: Request) -> dict[str, Any] | None:
        """获取请求参数.

        :param request: FastAPI 请求对象
        :return:
        """
        args: dict[str, Any] = {}

        # 查询参数
        query_params = dict(request.query_params)
        if query_params:
            args["query_params"] = await self.desensitization(dict(query_params))

        # 路径参数
        path_params = request.path_params
        if path_params:
            args["path_params"] = await self.desensitization(dict(path_params))

        # Tip: .body() 必须在 .form() 之前获取
        # https://github.com/encode/starlette/discussions/1933
        content_type = request.headers.get("Content-Type", "").split(";")

        # 请求体
        body_data = await request.body()
        if body_data:
            # 注意：非 json 数据默认使用 data 作为键
            if "application/json" not in content_type:
                args["data"] = str(body_data)
            else:
                json_data = await request.json()
                if isinstance(json_data, dict):
                    json_dict = cast("dict[str, Any]", json_data)
                    args["json"] = await self.desensitization(json_dict)
                else:
                    args["data"] = str(body_data)

        # 表单参数
        form_data = await request.form()
        if len(form_data) > 0:
            form_payload: dict[str, Any] = {}
            for k, v in form_data.items():
                form_payload[k] = v.filename if isinstance(v, UploadFile) else str(v)
            if "multipart/form-data" not in content_type:
                args["x-www-form-urlencoded"] = await self.desensitization(form_payload)
            else:
                args["form-data"] = await self.desensitization(form_payload)

        return args or None

    @staticmethod
    async def desensitization(args: dict[str, Any]) -> dict[str, Any]:
        """脱敏处理.

        :param args: 需要脱敏的参数字典
        :return:
        """
        for key, value in args.items():
            if key in settings.OPERA_LOG_ENCRYPT_KEY_INCLUDE:
                match settings.OPERA_LOG_ENCRYPT_TYPE:
                    case OperaLogCipherType.aes:
                        args[key] = (AESCipher(settings.OPERA_LOG_ENCRYPT_SECRET_KEY).encrypt(value)).hex()
                    case OperaLogCipherType.md5:
                        args[key] = Md5Cipher.encrypt(value)
                    case OperaLogCipherType.itsdangerous:
                        args[key] = ItsDCipher(settings.OPERA_LOG_ENCRYPT_SECRET_KEY).encrypt(value)
                    case OperaLogCipherType.plan:
                        pass
                    case _:
                        args[key] = "******"

        return args

    @classmethod
    async def consumer(cls) -> None:
        """操作日志消费者."""
        while True:
            logs = await batch_dequeue(
                cls.opera_log_queue,
                max_items=settings.OPERA_LOG_QUEUE_BATCH_CONSUME_SIZE,
                timeout=settings.OPERA_LOG_QUEUE_TIMEOUT,
            )
            if logs:
                try:
                    if settings.DATABASE_ECHO:
                        log.info("自动执行【操作日志批量创建】任务...")
                    async with async_db_session.begin() as db:
                        await opera_log_service.bulk_create(db=db, objs=logs)
                finally:
                    if not cls.opera_log_queue.empty():
                        cls.opera_log_queue.task_done()
