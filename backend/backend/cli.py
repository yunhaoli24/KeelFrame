"""Cli."""

import sys
import asyncio
import contextlib
import subprocess
from typing import Any, Literal, TypeVar, Annotated, cast
from dataclasses import dataclass
from collections.abc import Callable

import anyio
import cappa
import granian
from alembic import command as alembic_command
from rich.text import Text
from rich.panel import Panel
from sqlalchemy import text
from watchfiles import PythonFilter
from rich.prompt import Prompt
from cappa.output import error_format
from alembic.config import Config as AlembicConfig

from backend import __version__
from backend.core.conf import settings
from backend.database.db import drop_tables, async_db_session
from backend.common.enums import DataBaseType
from backend.plugin.tools import get_plugins, get_plugin_sql
from backend.utils.console import console
from backend.core.path_conf import BASE_PATH, ALEMBIC_DIR, ALEMBIC_INI
from backend.database.redis import redis_client
from backend.utils.file_ops import parse_sql_script, install_git_plugin, install_zip_plugin
from backend.common.exception.errors import BaseExceptionError


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


async def init() -> None:
    """Init."""
    panel_content = Text()
    panel_content.append("【数据库配置】", style="bold green")
    panel_content.append("\n\n  • 类型: ")
    panel_content.append(f"{settings.DATABASE_TYPE}", style="yellow")
    panel_content.append("\n  • 数据库:")
    panel_content.append(f"{settings.DATABASE_SCHEMA}", style="yellow")
    panel_content.append("\n\n【Redis 配置】", style="bold green")
    panel_content.append("\n\n  • 数据库:")
    panel_content.append(f"{settings.REDIS_DATABASE}", style="yellow")
    plugins = get_plugins()
    panel_content.append("\n\n【已安装插件】", style="bold green")
    panel_content.append("\n\n  • ")
    if plugins:
        panel_content.append(f"{', '.join(plugins)}", style="yellow")
    else:
        panel_content.append("无", style="dim")

    console.print(Panel(panel_content, title=f"fba v{__version__} 初始化", border_style="cyan", padding=(1, 2)))
    ok = Prompt.ask(
        "即将[red]重建数据库表[/red]并[red]执行所有 SQL 脚本[/red], 确认继续吗?", choices=["y", "n"], default="n"
    )

    if ok.lower() == "y":
        console.print("开始初始化...", style="white")
        try:
            console.print("丢弃数据库表", style="white")
            await drop_tables()
            console.print("丢弃 Redis 缓存", style="white")
            await redis_client.delete_prefix(settings.JWT_USER_REDIS_PREFIX)
            await redis_client.delete_prefix(settings.TOKEN_EXTRA_INFO_REDIS_PREFIX)
            await redis_client.delete_prefix(settings.TOKEN_REDIS_PREFIX)
            await redis_client.delete_prefix(settings.TOKEN_REFRESH_REDIS_PREFIX)
            console.print("创建数据库表", style="white")
            await drop_alembic_version_table()
            await asyncio.to_thread(migrate_database)
            console.print("执行 SQL 脚本", style="white")
            sql_scripts = await get_sql_scripts()
            for sql_script in sql_scripts:
                console.print(f"正在执行: {sql_script}", style="white")
                await execute_sql_scripts(sql_script, is_init=True)
            console.print("初始化成功", style="green")
            console.print("\n快试试 [bold cyan]fba run[/bold cyan] 启动服务吧~")
        except Exception as e:
            msg = f"初始化失败: {e}"
            raise cappa.Exit(msg, code=1) from None
    else:
        console.print("已取消初始化", style="yellow")


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

    plugins = get_plugins()
    panel_content.append("\n已安装插件:", style="bold green")
    if plugins:
        panel_content.append(f"{', '.join(plugins)}", style="yellow")
    else:
        panel_content.append("无", style="white")

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


async def install_plugin(
    path: str | None,
    repo_url: str | None,
    no_sql: bool,  # noqa: FBT001
    db_type: DataBaseType,
) -> None:
    """Install Plugin."""
    if not path and not repo_url:
        msg = "path 或 repo_url 必须指定其中一项"
        raise cappa.Exit(msg, code=1)
    if path and repo_url:
        msg = "path 和 repo_url 不能同时指定"
        raise cappa.Exit(msg, code=1)

    plugin_name = None
    console.print("开始安装插件...", style="bold cyan")

    try:
        if path:
            plugin_name = await install_zip_plugin(file=path)
        if repo_url:
            plugin_name = await install_git_plugin(repo_url=repo_url)

        if plugin_name is None:
            msg = "插件安装失败"
            raise cappa.Exit(msg, code=1) from None  # noqa: TRY301

        console.print(f"插件 {plugin_name} 安装成功", style="bold green")

        sql_file = await get_plugin_sql(plugin_name, db_type)
        if sql_file and not no_sql:
            console.print("开始自动执行插件 SQL 脚本...", style="bold cyan")
            await execute_sql_scripts(sql_file)

    except Exception as e:
        raise cappa.Exit(e.msg if isinstance(e, BaseExceptionError) else str(e), code=1) from e


async def get_sql_scripts() -> list[str]:
    """Get Sql Scripts."""
    sql_scripts: list[str] = []
    db_dir = BASE_PATH / "sql" / "postgresql"
    main_sql_file = db_dir / "init_test_data.sql"

    main_sql_path = anyio.Path(main_sql_file)
    if await main_sql_path.exists():
        sql_scripts.append(str(main_sql_file))

    plugins = get_plugins()
    for plugin in plugins:
        plugin_sql = await get_plugin_sql(plugin, DataBaseType(settings.DATABASE_TYPE))
        if plugin_sql:
            sql_scripts.append(str(plugin_sql))

    return sql_scripts


async def execute_sql_scripts(sql_scripts: str, *, is_init: bool = False) -> None:
    """Execute Sql Scripts."""
    async with async_db_session.begin() as db:
        try:
            stmts = await parse_sql_script(sql_scripts)
            for stmt in stmts:
                await db.execute(text(stmt))
        except Exception as e:
            msg = f"SQL 脚本执行失败: {e}"
            raise cappa.Exit(msg, code=1) from e

    if not is_init:
        console.print("SQL 脚本已执行完成", style="bold green")


async def drop_alembic_version_table() -> None:
    """Drop Alembic version state for destructive project initialization."""
    async with async_db_session.begin() as db:
        await db.execute(text("DROP TABLE IF EXISTS alembic_version"))


@typed_cappa_command(help="初始化 fba 项目", default_long=True)
@dataclass
class Init:
    """初始化 fba 项目."""

    async def __call__(self) -> None:
        """Call  ."""
        await init()


@typed_cappa_command(help="执行数据库迁移", default_long=True)
@dataclass
class Migrate:
    """执行数据库迁移."""

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


@typed_cappa_command(help="新增插件", default_long=True)
@dataclass
class Add:
    """新增插件."""

    path: Annotated[
        str | None,
        cappa.Arg(help="ZIP 插件的本地完整路径"),
    ]
    repo_url: Annotated[
        str | None,
        cappa.Arg(help="Git 插件的仓库地址"),
    ]
    no_sql: Annotated[
        bool,
        cappa.Arg(default=False, help="禁用插件 SQL 脚本自动执行"),
    ]
    db_type: Annotated[
        DataBaseType,
        cappa.Arg(default="postgresql", help="执行插件 SQL 脚本的数据库类型"),
    ]

    async def __call__(self) -> None:
        """Call  ."""
        await install_plugin(self.path, self.repo_url, self.no_sql, self.db_type)


@typed_cappa_command(help="一个高效的 fba 命令行界面", default_long=True)
@dataclass
class FbaCli:
    """一个高效的 fba 命令行界面."""

    sql: Annotated[
        str,
        cappa.Arg(value_name="PATH", default="", show_default=False, help="在事务中执行 SQL 脚本"),
    ]
    subcmd: cappa.Subcommands[Init | Migrate | Run | Celery | Add | None] = None

    async def __call__(self) -> None:
        """Call  ."""
        if self.sql:
            await execute_sql_scripts(self.sql)


def main() -> None:
    """运行主程序."""
    output = cappa.Output(error_format=f"{error_format}\n{output_help}")
    asyncio.run(cappa.invoke_async(FbaCli, version=__version__, output=output))
