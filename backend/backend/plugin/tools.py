"""Tools."""

import os
import sys
import json
import warnings
import contextlib
import subprocess
from typing import Any, cast
from pathlib import Path
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, distribution

import anyio
import rtoml
from fastapi import Depends, Request, APIRouter
from starlette.concurrency import run_in_threadpool
from packaging.requirements import Requirement

from backend.core.conf import settings
from backend.common.log import log
from backend.common.enums import StatusType, DataBaseType
from backend.utils._await import run_await
from backend.core.path_conf import PLUGIN_DIR
from backend.database.redis import RedisCli, redis_client
from backend.common.exception import errors
from backend.utils.import_parse import get_model_objects, import_module_cached


class PluginConfigError(Exception):
    """插件信息错误."""


class PluginInjectError(Exception):
    """插件注入错误."""


class PluginInstallError(Exception):
    """插件安装错误."""


@lru_cache
def get_plugins() -> list[str]:
    """获取插件列表."""
    plugin_packages: list[str] = []

    # 遍历插件目录
    for item in PLUGIN_DIR.iterdir():
        item_path = PLUGIN_DIR / item.name
        if not item_path.is_dir() and item.name == "__pycache__":
            continue

        # 检查是否为目录且包含 __init__.py 文件
        if item_path.is_dir() and "__init__.py" in [f.name for f in item_path.iterdir()]:
            plugin_packages.append(item.name)

    return plugin_packages


def get_plugin_models() -> list[object]:
    """获取插件所有模型类."""
    objs: list[object] = []

    for plugin in get_plugins():
        module_path = f"backend.plugin.{plugin}.model"
        model_objs = get_model_objects(module_path)
        if model_objs:
            objs.extend(model_objs)

    return objs


async def get_plugin_sql(plugin: str, _db_type: DataBaseType) -> str | None:
    """获取插件 SQL 文件.

    :param plugin: 插件名称
    :param _db_type: 数据库类型
    :return:
    """
    postgresql_dir = PLUGIN_DIR / plugin / "sql" / "postgresql"
    sql_file = postgresql_dir / "init.sql"

    path = anyio.Path(sql_file)
    if not await path.exists():
        return None

    return str(sql_file)


def load_plugin_config(plugin: str) -> dict[str, Any]:
    """加载插件配置.

    :param plugin: 插件名称
    :return:
    """
    toml_path = PLUGIN_DIR / plugin / "plugin.toml"
    if not toml_path.exists():
        msg = f"插件 {plugin} 缺少 plugin.toml 配置文件, 请检查插件是否合法"
        raise PluginInjectError(msg)

    with toml_path.open(encoding="utf-8") as f:
        return rtoml.load(f)


def parse_plugin_config() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """解析插件配置."""
    extend_plugins: list[dict[str, Any]] = []
    app_plugins: list[dict[str, Any]] = []

    plugins = get_plugins()

    # 使用独立单例，避免与主线程冲突
    current_redis_client = RedisCli()

    # 清理未知插件信息
    run_await(current_redis_client.delete_prefix)(
        settings.PLUGIN_REDIS_PREFIX,
        exclude=[f"{settings.PLUGIN_REDIS_PREFIX}:{key}" for key in plugins],
    )

    for plugin in plugins:
        data = load_plugin_config(plugin)

        plugin_info = data.get("plugin")
        if not plugin_info:
            msg = f"插件 {plugin} 配置文件缺少 plugin 配置"
            raise PluginConfigError(msg)

        required_fields = ["summary", "version", "description", "author"]
        missing_fields = [field for field in required_fields if field not in plugin_info]
        if missing_fields:
            msg = f"插件 {plugin} 配置文件缺少必要字段: {', '.join(missing_fields)}"
            raise PluginConfigError(msg)

        if data.get("api"):
            if not data.get("app", {}).get("extend"):
                msg = f"扩展级插件 {plugin} 配置文件缺少 app.extend 配置"
                raise PluginConfigError(msg)
            extend_plugins.append(data)
        else:
            if not data.get("app", {}).get("router"):
                msg = f"应用级插件 {plugin} 配置文件缺少 app.router 配置"
                raise PluginConfigError(msg)
            app_plugins.append(data)

        # 补充插件信息
        plugin_cache_info = run_await(current_redis_client.get)(f"{settings.PLUGIN_REDIS_PREFIX}:{plugin}")
        if plugin_cache_info:
            data["plugin"]["enable"] = json.loads(plugin_cache_info)["plugin"]["enable"]
        else:
            data["plugin"]["enable"] = str(StatusType.enable.value)
        data["plugin"]["name"] = plugin

        # 缓存最新插件信息
        run_await(current_redis_client.set)(
            f"{settings.PLUGIN_REDIS_PREFIX}:{plugin}",
            json.dumps(data, ensure_ascii=False),
        )

    # 重置插件变更状态
    run_await(current_redis_client.delete)(f"{settings.PLUGIN_REDIS_PREFIX}:changed")

    # 关闭连接
    run_await(current_redis_client.aclose)()

    return extend_plugins, app_plugins


def inject_extend_router(plugin: dict[str, Any]) -> None:
    """扩展级插件路由注入.

    :param plugin: 插件名称
    :return:
    """
    plugin_name: str = plugin["plugin"]["name"]
    plugin_api_path = PLUGIN_DIR / plugin_name / "api"
    if not plugin_api_path.exists():
        msg = f"插件 {plugin} 缺少 api 目录, 请检查插件文件是否完整"
        raise PluginConfigError(msg)

    for root, _, api_files in os.walk(plugin_api_path):
        for file in api_files:
            if not (file.endswith(".py") and file != "__init__.py"):
                continue

            # 解析插件路由配置
            file_config = plugin["api"][file[:-3]]
            prefix = file_config["prefix"]
            tags = file_config["tags"]

            # 获取插件路由模块
            file_path = os.path.join(root, file)  # noqa: PTH118
            path_to_module_str = os.path.relpath(file_path, PLUGIN_DIR).replace(os.sep, ".")[:-3]
            module_path = f"backend.plugin.{path_to_module_str}"

            try:
                module = import_module_cached(module_path)
                plugin_router = getattr(module, "router", None)
                if not plugin_router:
                    warnings.warn(
                        f"扩展级插件 {plugin_name} 模块 {module_path} 中没有有效的 router, 请检查插件文件是否完整",
                        FutureWarning,
                        stacklevel=2,
                    )
                    continue

                # 获取目标 app 路由
                relative_path = os.path.relpath(root, plugin_api_path)
                app_name = plugin.get("app", {}).get("extend")
                target_module_path = f"backend.app.{app_name}.api.{relative_path.replace(os.sep, '.')}"
                target_module = import_module_cached(target_module_path)
                target_router = getattr(target_module, "router", None)

                if not target_router or not isinstance(target_router, APIRouter):
                    msg = f"扩展级插件 {plugin_name} 模块 {module_path} 中没有有效的 router, 请检查插件文件是否完整"
                    raise PluginInjectError(msg)  # noqa: TRY301

                # 将插件路由注入到目标路由中
                target_router.include_router(
                    router=plugin_router,
                    prefix=prefix,
                    tags=[tags] if tags else [],
                    dependencies=[Depends(PluginStatusChecker(plugin_name))],
                )
            except Exception as e:
                msg = f"扩展级插件 {plugin_name} 路由注入失败: {e!s}"
                raise PluginInjectError(msg) from e


def inject_app_router(plugin: dict[str, Any], target_router: APIRouter) -> None:
    """应用级插件路由注入.

    :param plugin: 插件名称
    :param target_router: FastAPI 路由器
    :return:
    """
    plugin_name: str = plugin["plugin"]["name"]
    module_path = f"backend.plugin.{plugin_name}.api.router"
    try:
        module = import_module_cached(module_path)
        routers = cast("list[str] | None", plugin["app"]["router"])
        if not routers:
            msg = f"应用级插件 {plugin_name} 配置文件存在错误, 请检查"
            raise PluginConfigError(msg)  # noqa: TRY301

        for router in routers:
            plugin_router = getattr(module, router, None)
            if not plugin_router or not isinstance(plugin_router, APIRouter):
                msg = f"应用级插件 {plugin_name} 模块 {module_path} 中没有有效的 router, 请检查插件文件是否完整"
                raise PluginInjectError(msg)  # noqa: TRY301

            # 将插件路由注入到目标路由中
            target_router.include_router(plugin_router, dependencies=[Depends(PluginStatusChecker(plugin_name))])
    except Exception as e:
        msg = f"应用级插件 {plugin_name} 路由注入失败: {e!s}"
        raise PluginInjectError(msg) from e


def build_final_router() -> APIRouter:
    """构建最终路由."""
    from backend.app.router import router as main_router  # noqa: PLC0415

    extend_plugins, app_plugins = parse_plugin_config()

    for plugin in extend_plugins:
        inject_extend_router(plugin)

    for plugin in app_plugins:
        inject_app_router(plugin, main_router)

    return main_router


def _ensure_pip_available() -> bool:
    """确保 pip 在虚拟环境中可用."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    # 尝试使用 ensurepip
    try:
        subprocess.check_call(
            [sys.executable, "-m", "ensurepip", "--default-pip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    # 尝试下载并安装
    try:
        import tempfile  # noqa: PLC0415

        import httpx  # noqa: PLC0415

        try:
            with (
                tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f,
                httpx.Client(timeout=3) as client,
            ):
                get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
                response = client.get(get_pip_url)
                response.raise_for_status()
                f.write(response.text)
                temp_file = f.name
        except Exception:
            return False

        try:
            subprocess.check_call([sys.executable, temp_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        finally:
            with contextlib.suppress(OSError):
                Path(temp_file).unlink()
    except Exception as e:
        log.warning(f"Failed to install pip: {e!s}")

    return False


def install_requirements(plugin: str | None) -> None:
    """安装插件依赖.

    :param plugin: 指定插件名，否则检查所有插件
    :return:
    """
    plugin_list = [plugin] if plugin else get_plugins()

    for plugin_item in plugin_list:
        requirements_file = PLUGIN_DIR / plugin_item / "requirements.txt"
        missing_dependencies = False
        if requirements_file.exists():
            with requirements_file.open(encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith("#"):
                        continue
                    try:
                        req = Requirement(stripped_line)
                        dependency = req.name.lower()
                    except Exception as e:
                        msg = f"插件 {plugin_item} 依赖 {stripped_line} 格式错误: {e!s}"
                        raise PluginInstallError(msg) from e
                    try:
                        distribution(dependency)
                    except PackageNotFoundError:
                        missing_dependencies = True

        if missing_dependencies:
            try:
                if not _ensure_pip_available():
                    msg = f"pip 安装失败, 无法继续安装插件 {plugin_item} 依赖"
                    raise PluginInstallError(msg)

                pip_install = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
                if settings.PLUGIN_PIP_CHINA:
                    pip_install.extend(["-i", settings.PLUGIN_PIP_INDEX_URL])

                max_retries = settings.PLUGIN_PIP_MAX_RETRY
                for attempt in range(max_retries):
                    try:
                        subprocess.check_call(  # noqa: S603
                            pip_install,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        break
                    except subprocess.TimeoutExpired as err:
                        if attempt == max_retries - 1:
                            msg = f"插件 {plugin_item} 依赖安装超时"
                            raise PluginInstallError(msg) from err
                        continue
                    except subprocess.CalledProcessError as e:
                        if attempt == max_retries - 1:
                            msg = f"插件 {plugin_item} 依赖安装失败: {e}"
                            raise PluginInstallError(msg) from e
                        continue
            except subprocess.CalledProcessError as e:
                msg = f"插件 {plugin_item} 依赖安装失败: {e}"
                raise PluginInstallError(msg) from e


def uninstall_requirements(plugin: str) -> None:
    """卸载插件依赖.

    :param plugin: 插件名称
    :return:
    """
    requirements_file = PLUGIN_DIR / plugin / "requirements.txt"
    if requirements_file.exists():
        try:
            pip_uninstall = [sys.executable, "-m", "pip", "uninstall", "-r", str(requirements_file), "-y"]
            subprocess.check_call(pip_uninstall, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
        except subprocess.CalledProcessError as e:
            msg = f"插件 {plugin} 依赖卸载失败: {e}"
            raise PluginInstallError(msg) from e


async def install_requirements_async(plugin: str | None = None) -> None:
    """异步安装插件依赖.

    由于 Windows 平台限制，无法实现完美的全异步方案，详情：
    https://stackoverflow.com/questions/44633458/why-am-i-getting-notimplementederror-with-async-and-await-on-windows
    """
    await run_in_threadpool(install_requirements, plugin)


async def uninstall_requirements_async(plugin: str) -> None:
    """异步卸载插件依赖.

    :param plugin: 插件名称
    :return:
    """
    await run_in_threadpool(uninstall_requirements, plugin)


class PluginStatusChecker:
    """插件状态检查器."""

    def __init__(self, plugin: str) -> None:
        """初始化插件状态检查器.

        :param plugin: 插件名称
        :return:
        """
        self.plugin = plugin

    async def __call__(self, _request: Request) -> None:
        """验证插件状态.

        :param _request: FastAPI 请求对象
        :return:
        """
        plugin_info = await redis_client.get(f"{settings.PLUGIN_REDIS_PREFIX}:{self.plugin}")
        if not plugin_info:
            log.error("插件状态未初始化或丢失, 需重启服务自动修复")
            msg = "插件状态未初始化或丢失, 请联系系统管理员"
            raise PluginInjectError(msg)

        if not int(json.loads(plugin_info)["plugin"]["enable"]):
            raise errors.ServerError(msg=f"插件 {self.plugin} 未启用, 请联系系统管理员")
