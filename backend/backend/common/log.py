"""Log."""

import os
import re
import sys
import inspect
import logging
from typing import Any
from pathlib import Path

from loguru import logger as _logger

from backend.core.conf import settings
from backend.core.path_conf import LOG_DIR
from backend.utils.timezone import timezone
from backend.utils.trace_id import get_request_trace_id


logger: Any = _logger


class InterceptHandler(logging.Handler):
    """日志拦截处理器，用于将标准库的日志重定向到 loguru.

    参考：https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit."""
        # 获取对应的 Loguru 级别（如果存在）
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找记录日志消息的调用者
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def default_formatter(record: logging.LogRecord) -> str:
    """默认日志格式化程序."""
    # 重写 sqlalchemy echo 输出
    # https://github.com/sqlalchemy/sqlalchemy/discussions/12791
    record_name = getattr(record, "name", "") or ""
    if record_name.startswith("sqlalchemy"):
        record.msg = re.sub(r"\s+", " ", str(record.msg)).strip()

    return settings.LOG_FORMAT if settings.LOG_FORMAT.endswith("\n") else f"{settings.LOG_FORMAT}\n"


def request_id_filter(record: logging.LogRecord | dict[str, Any]) -> logging.LogRecord | dict[str, Any]:
    """请求 ID 过滤器."""
    rid = get_request_trace_id()
    if isinstance(record, logging.LogRecord):
        record.request_id = rid[: settings.TRACE_ID_LOG_LENGTH]
    else:
        record["request_id"] = rid[: settings.TRACE_ID_LOG_LENGTH]
    return record


def loguru_request_id_filter(record: dict[str, Any]) -> bool:
    """Loguru Request Id Filter."""
    request_id_filter(record)
    return True


def access_level_filter(record: dict[str, Any]) -> bool:
    """Access Level Filter."""
    level_no = getattr(record.get("level"), "no", 0)
    return bool(level_no <= 25)


def error_level_filter(record: dict[str, Any]) -> bool:
    """Error Level Filter."""
    level_no = getattr(record.get("level"), "no", 0)
    return bool(level_no >= 30)


def setup_logging() -> None:
    """设置日志处理器.

    参考：
    - https://github.com/benoitc/gunicorn/issues/1572#issuecomment-638391953
    - https://github.com/pawamoy/pawamoy.github.io/issues/17
    """
    # 设置根日志处理器和级别
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_STD_LEVEL)

    for name in logging.root.manager.loggerDict:
        # 清空所有默认日志处理器
        logging.getLogger(name).handlers = []

        # 配置日志传播规则
        if "uvicorn.access" in name or "watchfiles.main" in name:
            logging.getLogger(name).propagate = False
        else:
            logging.getLogger(name).propagate = True

        # Debug log handlers
        # logging.debug(f'{logging.getLogger(name)}, {logging.getLogger(name).propagate}')

    # 移除 loguru 默认处理器
    logger.remove()

    # 配置 loguru 处理器
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": settings.LOG_STD_LEVEL,
                "format": default_formatter,
                "filter": loguru_request_id_filter,
            },
        ],
    )


def set_custom_logfile() -> None:
    """设置自定义日志文件."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir()

    # 日志文件
    log_access_file = LOG_DIR / settings.LOG_ACCESS_FILENAME
    log_error_file = LOG_DIR / settings.LOG_ERROR_FILENAME

    # 日志压缩回调
    def compression(filepath: str) -> str:
        """Compression."""
        filename = filepath.rsplit(os.sep, maxsplit=1)[-1]
        original_filename = filename.split(".")[0]
        if "-" in original_filename:
            return str(LOG_DIR / f"{original_filename}.log")
        return str(LOG_DIR / f"{original_filename}_{timezone.now().strftime('%Y-%m-%d')}.log")

    def compression_handler(filepath: str) -> None:
        """Compression Handler."""
        Path(filepath).rename(compression(filepath))

    # 日志文件通用配置
    # https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
    log_config: dict[str, Any] = {
        "format": default_formatter,
        "enqueue": True,
        "rotation": "00:00",
        "retention": "7 days",
        "compression": compression_handler,
    }

    # 标准输出文件
    logger.add(
        str(log_access_file),
        level=settings.LOG_FILE_ACCESS_LEVEL,
        filter=access_level_filter,
        backtrace=False,
        diagnose=False,
        **log_config,
    )

    # 标准错误文件
    logger.add(
        str(log_error_file),
        level=settings.LOG_FILE_ERROR_LEVEL,
        filter=error_level_filter,
        backtrace=True,
        diagnose=True,
        **log_config,
    )


# 创建 logger 实例
log = logger
