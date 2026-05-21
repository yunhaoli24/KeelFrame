"""Cli."""

import sys
import asyncio
import contextlib
import subprocess
from typing import Any, Literal, TypeVar, Annotated, cast
from dataclasses import dataclass
from collections.abc import Callable

import cappa
import granian
from alembic import command as alembic_command
from rich.text import Text
from rich.panel import Panel
from watchfiles import PythonFilter
from cappa.output import error_format
from alembic.config import Config as AlembicConfig

from backend import __version__
from backend.core.conf import settings
from backend.utils.console import console
from backend.core.path_conf import ALEMBIC_DIR, ALEMBIC_INI


output_help = '\n更多信息, 尝试 "[cyan]--help[/]"'
CommandClassT = TypeVar("CommandClassT")


def typed_cappa_command(*args: object, **kwargs: object) -> Callable[[type[CommandClassT]], type[CommandClassT]]:
    """Provide a typed wrapper for cappa.command class decorators."""
    command = cast("Any", cappa.command)
    return cast("Callable[[type[CommandClassT]], type[CommandClassT]]", command(*args, **kwargs))


class CustomReloadFilter(PythonFilter):
    """自定义重载过滤器."""

    def __init__(self) -> None:
        """Init  ."""
        super().__init__(extra_extensions=[".json", ".yaml", ".yml"])


def get_alembic_config() -> AlembicConfig:
    """Get Alembic config rooted at the backend package directory."""
    config = AlembicConfig(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    return config


def migrate_database(revision: str = "head") -> None:
    """Apply database migrations."""
    alembic_command.upgrade(get_alembic_config(), revision)


def run(host: str, port: int, reload: bool, workers: int) -> None:  # noqa: FBT001
    """Run."""
    url = f"http://{host}:{port}"
    docs_url = url + settings.FASTAPI_DOCS_URL
    redoc_url = url + settings.FASTAPI_REDOC_URL
    openapi_url = url + (settings.FASTAPI_OPENAPI_URL or "")

    panel_content = Text()
    panel_content.append("Python 版本:", style="bold cyan")
    panel_content.append(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", style="white")

    panel_content.append("\nAPI 请求地址: ", style="bold cyan")
    panel_content.append(f"{url}{settings.FASTAPI_API_V1_PATH}", style="blue")

    panel_content.append("\n\n环境模式:", style="bold green")
    env_style = "yellow" if settings.ENVIRONMENT == "dev" else "green"
    panel_content.append(f"{settings.ENVIRONMENT.upper()}", style=env_style)

    if settings.ENVIRONMENT == "dev":
        panel_content.append(f"\n\n📖 Swagger 文档: {docs_url}", style="bold magenta")
        panel_content.append(f"\n📚 Redoc   文档: {redoc_url}", style="bold magenta")
        panel_content.append(f"\n📡 OpenAPI JSON: {openapi_url}", style="bold magenta")

    panel_content.append("\n🌐 架构官方文档: ", style="bold magenta")
    panel_content.append("https://fastapi-practices.github.io/fastapi_best_architecture_docs/")

    console.print(Panel(panel_content, title=f"fba v{__version__}", border_style="purple", padding=(1, 2)))
    granian.Granian(
        target="backend.main:app",
        interface=cast("Any", "asgi"),
        address=host,
        port=port,
        reload=reload,
        reload_filter=CustomReloadFilter,
        workers=workers,
    ).serve()


def run_celery_worker(log_level: Literal["info", "debug"]) -> None:
    """Run Celery Worker."""
    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run(  # noqa: S603
            ["celery", "-A", "backend.app.task.celery", "worker", "-l", f"{log_level}", "-P", "gevent"],  # noqa: S607
            check=False,
        )


def run_celery_beat(log_level: Literal["info", "debug"]) -> None:
    """Run Celery Beat."""
    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run(  # noqa: S603
            ["celery", "-A", "backend.app.task.celery", "beat", "-l", f"{log_level}"],  # noqa: S607
            check=False,
        )


def run_celery_flower(port: int, basic_auth: str) -> None:
    """Run Celery Flower."""
    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run(  # noqa: S603
            [  # noqa: S607
                "celery",
                "-A",
                "backend.app.task.celery",
                "flower",
                f"--port={port}",
                f"--basic-auth={basic_auth}",
            ],
            check=False,
        )


@typed_cappa_command(help="执行数据库迁移并应用基线数据", default_long=True)
@dataclass
class Migrate:
    """执行数据库迁移并应用基线数据."""

    revision: Annotated[
        str,
        cappa.Arg(default="head", help="目标 Alembic revision"),
    ]

    async def __call__(self) -> None:
        """Call  ."""
        await asyncio.to_thread(migrate_database, self.revision)


@typed_cappa_command(help="运行 API 服务", default_long=True)
@dataclass
class Run:
    """运行 API 服务."""

    host: Annotated[
        str,
        cappa.Arg(
            default="127.0.0.1",
            help="提供服务的主机 IP 地址, 对于本地开发, 请使用 `127.0.0.1`."
            "要启用公共访问, 例如在局域网中, 请使用 `0.0.0.0`",
        ),
    ]
    port: Annotated[
        int,
        cappa.Arg(default=8080, help="提供服务的主机端口号"),
    ]
    reload: Annotated[
        bool,
        cappa.Arg(default=True, help="禁用在(代码)文件更改时自动重新加载服务器"),
    ]
    workers: Annotated[
        int,
        cappa.Arg(default=1, help="使用多个工作进程, 必须与 `--reload` 同时使用"),
    ]

    def __call__(self) -> None:
        """Call  ."""
        run(host=self.host, port=self.port, reload=self.reload, workers=self.workers)


@typed_cappa_command(help="从当前主机启动 Celery worker 服务", default_long=True)
@dataclass
class Worker:
    """从当前主机启动 Celery worker 服务."""

    log_level: Annotated[
        Literal["info", "debug"],
        cappa.Arg(short="-l", default="info", help="日志输出级别"),
    ]

    def __call__(self) -> None:
        """Call  ."""
        run_celery_worker(log_level=self.log_level)


@typed_cappa_command(help="从当前主机启动 Celery beat 服务", default_long=True)
@dataclass
class Beat:
    """从当前主机启动 Celery beat 服务."""

    log_level: Annotated[
        Literal["info", "debug"],
        cappa.Arg(short="-l", default="info", help="日志输出级别"),
    ]

    def __call__(self) -> None:
        """Call  ."""
        run_celery_beat(log_level=self.log_level)


@typed_cappa_command(help="从当前主机启动 Celery flower 服务", default_long=True)
@dataclass
class Flower:
    """从当前主机启动 Celery flower 服务."""

    port: Annotated[
        int,
        cappa.Arg(default=8555, help="提供服务的主机端口号"),
    ]
    basic_auth: Annotated[
        str,
        cappa.Arg(default="admin:123456", help="页面登录的用户名和密码"),
    ]

    def __call__(self) -> None:
        """Call  ."""
        run_celery_flower(port=self.port, basic_auth=self.basic_auth)


@typed_cappa_command(help="运行 Celery 服务")
@dataclass
class Celery:
    """运行 Celery 服务."""

    subcmd: cappa.Subcommands[Worker | Beat | Flower]


@typed_cappa_command(help="一个高效的 fba 命令行界面", default_long=True)
@dataclass
class FbaCli:
    """一个高效的 fba 命令行界面."""

    subcmd: cappa.Subcommands[Migrate | Run | Celery | None] = None


def main() -> None:
    """运行主程序."""
    output = cappa.Output(error_format=f"{error_format}\n{output_help}")
    asyncio.run(cappa.invoke_async(FbaCli, version=__version__, output=output))
