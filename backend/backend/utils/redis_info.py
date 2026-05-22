# pragma: exclude file
"""Redis Info."""

from typing import Any, cast

from backend.database.redis import redis_client
from backend.utils.server_info import server_info


class RedisInfo:
    """Redis Info Service."""

    @staticmethod
    async def get_info() -> dict[str, str]:
        """获取 Redis 服务器信息."""
        # 获取原始信息
        info = cast("dict[str, Any]", await cast("Any", redis_client).info())

        # 格式化信息
        fmt_info: dict[str, str] = {}
        for key, value in info.items():
            if isinstance(value, dict):
                # 将字典格式化为字符串
                value_dict = cast("dict[str, Any]", value)
                fmt_info[key] = ",".join(f"{k}={v}" for k, v in value_dict.items())
            else:
                fmt_info[key] = str(value)

        # 添加数据库大小信息
        db_size = await cast("Any", redis_client).dbsize()
        fmt_info["keys_num"] = str(db_size)

        # 格式化运行时间
        uptime = int(fmt_info.get("uptime_in_seconds", "0"))
        fmt_info["uptime_in_seconds"] = server_info.fmt_seconds(uptime)

        return fmt_info

    @staticmethod
    async def get_stats() -> list[dict[str, str]]:
        """获取 Redis 命令统计信息."""
        # 获取命令统计信息
        command_stats = cast("dict[str, Any]", await cast("Any", redis_client).info("commandstats"))

        # 格式化统计信息
        stats_list: list[dict[str, str]] = []
        for key, value in command_stats.items():
            if not isinstance(value, dict):
                continue

            command_name = key.split("_")[-1]
            call_count = str(cast("dict[str, Any]", value).get("calls", "0"))
            stats_list.append({"name": command_name, "value": call_count})

        return stats_list


redis_info: RedisInfo = RedisInfo()
