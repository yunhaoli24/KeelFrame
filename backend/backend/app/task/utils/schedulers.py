"""Schedulers."""

from __future__ import annotations

import math
import heapq
import asyncio
from typing import TYPE_CHECKING, Any, cast
from builtins import min as builtin_min
from datetime import datetime, timedelta
from multiprocessing.util import Finalize

from celery import schedules, current_app  # pyright: ignore[reportMissingModuleSource]
from sqlalchemy import select
from celery.beat import Scheduler, ScheduleEntry, event_t
from celery.signals import beat_init
from sqlalchemy.exc import DatabaseError, InterfaceError
from celery.utils.log import get_logger

from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.utils._await import run_await
from backend.app.task.enums import PeriodType, TaskSchedulerType
from backend.database.redis import redis_client
from backend.utils.timezone import timezone
from backend.common.exception import errors
from backend.utils.serializers import select_as_dict
from backend.app.task.model.scheduler import TaskScheduler
from backend.app.task.utils.tzcrontab import TzAwareCrontab, crontab_verify
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam


if TYPE_CHECKING:
    from redis.asyncio.lock import Lock

# 此计划程序必须比常规的 5 分钟更频繁地唤醒，因为它需要考虑对计划的外部更改
DEFAULT_MAX_INTERVAL = 5  # seconds

# 计划锁时长，避免重复创建
DEFAULT_MAX_LOCK_TIMEOUT = DEFAULT_MAX_INTERVAL * 5  # seconds

logger = get_logger("fba.schedulers")


class ModelEntry(ScheduleEntry):
    """任务调度实体."""

    schedule: schedules.schedule | TzAwareCrontab
    last_run_at: datetime
    name: str

    def __init__(self, model: TaskScheduler, app: Any = None) -> None:  # noqa: ANN401
        """Initialize model entry."""
        super().__init__(
            app=app or current_app._get_current_object(),  # noqa: SLF001
            name=model.name,
            task=model.task,
        )
        try:
            if (
                model.type == TaskSchedulerType.INTERVAL
                and model.interval_every is not None
                and model.interval_period is not None
            ):
                self.schedule = schedules.schedule(timedelta(**{model.interval_period: model.interval_every}))
            elif model.type == TaskSchedulerType.CRONTAB and model.crontab is not None:
                crontab_split = model.crontab.split(" ")
                self.schedule = TzAwareCrontab(
                    minute=crontab_split[0],
                    hour=crontab_split[1],
                    day_of_week=crontab_split[2],
                    day_of_month=crontab_split[3],
                    month_of_year=crontab_split[4],
                )
            else:
                self._raise_not_found_error()
            # logger.debug('Schedule: {}'.format(self.schedule))
        except Exception:
            logger.exception("禁用计划为空的任务 %s", self.name)
            asyncio.create_task(self._disable(model))  # noqa: RUF006

        self.args = tuple(model.args) if model.args is not None else None
        self.kwargs = model.kwargs

        self.options = {}
        for option in ["queue", "exchange", "routing_key"]:
            value = getattr(model, option)
            if value is None:
                continue
            self.options[option] = value

        expires = getattr(model, "expires_", None)
        if expires:
            if isinstance(expires, int):
                self.options["expires"] = expires
            elif isinstance(expires, datetime):
                self.options["expires"] = timezone.from_datetime(expires)

        last_run_time = model.last_run_time
        if last_run_time is None:
            last_run_time = timezone.now()
            model.last_run_time = last_run_time
            if model.start_time:
                last_run_time = timezone.from_datetime(model.start_time) - timedelta(days=365)
                model.last_run_time = last_run_time

        self.last_run_at = timezone.from_datetime(last_run_time)
        self.options["periodic_task_name"] = model.name
        self.model = model

    def _raise_not_found_error(self) -> None:
        """Raise not found error."""
        raise errors.NotFoundError(msg=f"{self.name} 计划为空!")

    async def _disable(self, model: TaskScheduler) -> None:
        """禁用任务."""
        model.no_changes = True
        self.model.enabled = self.enabled = model.enabled = False
        async with async_db_session.begin():
            model.enabled = False

    def is_due(self) -> tuple[bool, int | float]:
        """任务到期状态."""
        if not self.model.enabled:
            # 重新启用时延迟 5 秒
            return schedules.schedstate(is_due=False, next=5)

        # 仅在 'start_time' 之后运行
        if self.model.start_time is not None:
            now = timezone.now()
            start_time = timezone.from_datetime(self.model.start_time)
            if now < start_time:
                delay = math.ceil((start_time - now).total_seconds())
                return schedules.schedstate(is_due=False, next=delay)

        # 一次性任务
        if self.model.one_off and self.model.enabled and self.model.total_run_count > 0:
            self.model.enabled = False
            self.model.total_run_count = 0
            self.model.no_changes = False
            save_fields = ("enabled",)
            run_await(self.save)(save_fields)
            return schedules.schedstate(is_due=False, next=1000000000)  # 高延迟，避免重新检查

        return self.schedule.is_due(self.last_run_at)  # ty: ignore[invalid-return-type]

    def __next__(self, last_run_at: datetime | None = None) -> ModelEntry:
        """Get next entry."""
        self.model.last_run_time = last_run_at or timezone.now()
        self.model.total_run_count += 1
        self.model.no_changes = True
        return self.__class__(self.model)

    next = __next__

    async def save(self, fields: tuple[str, ...] = ()) -> None:
        """保存任务状态字段.

        :param fields: 要保存的其他字段
        :return:
        """
        async with async_db_session.begin() as db:
            stmt = select(TaskScheduler).where(TaskScheduler.id == self.model.id).with_for_update()
            query = await db.execute(stmt)
            task = query.scalars().first()
            if task:
                for field in ["last_run_time", "total_run_count", "no_changes"]:
                    setattr(task, field, getattr(self.model, field))
                for field in fields:
                    setattr(task, field, getattr(self.model, field))
                logger.warning("任务 %s 不存在, 跳过更新", self.model.name)

    @classmethod
    async def from_entry(cls, name: str, app: Any = None, **entry: Any) -> ModelEntry:  # noqa: ANN401
        """保存或更新本地任务调度."""
        async with async_db_session.begin() as db:
            stmt = select(TaskScheduler).where(TaskScheduler.name == name)
            query = await db.execute(stmt)
            task = query.scalars().first()
            temp = await cls._unpack_fields(name, **entry)
            if not task:
                task = TaskScheduler(**temp)
                db.add(task)
            else:
                for key, value in temp.items():
                    setattr(task, key, value)
            return cls(task, app=app)

    @staticmethod
    async def to_model_schedule(name: str, task: str, schedule: schedules.schedule | TzAwareCrontab) -> TaskScheduler:
        """Convert to model schedule."""
        model_schedule = cast("schedules.schedule | TzAwareCrontab", schedules.maybe_schedule(schedule))

        async with async_db_session() as db:
            spec: dict[str, Any]
            if isinstance(model_schedule, schedules.crontab):
                crontab = f"{model_schedule._orig_minute} {model_schedule._orig_hour} {model_schedule._orig_day_of_week} {model_schedule._orig_day_of_month} {model_schedule._orig_month_of_year}"  # noqa: E501, SLF001
                crontab_verify(crontab)
                spec = {
                    "name": name,
                    "type": TaskSchedulerType.CRONTAB.value,
                    "crontab": crontab,
                }
                stmt = select(TaskScheduler).filter_by(**spec)
                query = await db.execute(stmt)
                obj = query.scalars().first()
                if not obj:
                    create_param = CreateTaskSchedulerParam.model_validate({"task": task, **spec})
                    obj = TaskScheduler(**create_param.model_dump())
            else:
                every = max(model_schedule.run_every.total_seconds(), 0)
                spec = {
                    "name": name,
                    "type": TaskSchedulerType.INTERVAL.value,
                    "interval_every": every,
                    "interval_period": PeriodType.SECONDS.value,
                }
                stmt = select(TaskScheduler).filter_by(**spec)
                query = await db.execute(stmt)
                obj = query.scalars().first()
                if not obj:
                    create_param = CreateTaskSchedulerParam.model_validate({"task": task, **spec})
                    obj = TaskScheduler(**create_param.model_dump())

            return obj

    @classmethod
    async def _unpack_fields(
        cls,
        name: str,
        task: str,
        schedule: schedules.schedule | TzAwareCrontab,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
        **entry: Any,  # noqa: ANN401
    ) -> dict[str, Any]:
        model_schedule = await cls.to_model_schedule(name, task, schedule)
        model_dict = select_as_dict(model_schedule)
        for k in ["id", "created_time", "updated_time"]:
            try:
                del model_dict[k]
            except KeyError:
                continue
        model_dict.update(
            args=args,
            kwargs=kwargs,
            **cls._unpack_options(**options or {}),
            **entry,
        )
        return model_dict

    @classmethod
    def _unpack_options(
        cls,
        queue: str | None = None,
        exchange: str | None = None,
        routing_key: str | None = None,
        start_time: datetime | None = None,
        expires: datetime | int | timedelta | None = None,
        expire_seconds: int | None = None,
        *,
        one_off: bool = False,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "queue": queue,
            "exchange": exchange,
            "routing_key": routing_key,
            "start_time": start_time,
            "expire_time": expires,
            "expire_seconds": expire_seconds,
            "one_off": one_off,
        }
        if expires:
            if isinstance(expires, int):
                data["expire_seconds"] = expires
            elif isinstance(expires, timedelta):
                data["expire_time"] = timezone.now() + expires
        return data


class DatabaseScheduler(Scheduler):
    """数据库调度程序."""

    Entry = ModelEntry

    _schedule: dict[str, ModelEntry] | None = None
    _last_update = None
    _initial_read = True
    _heap_invalidated = False
    _heap: list[ModelEntry] = []  # noqa: RUF012

    lock: Lock | None = None
    lock_key = f"{settings.CELERY_REDIS_PREFIX}:beat_lock"

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize scheduler."""
        self.app = kwargs["app"]
        self._dirty: set[str] = set()
        super().__init__(*args, **kwargs)
        self._finalize = Finalize(self, self.sync, exitpriority=5)
        self.max_interval = kwargs.get("max_interval") or self.app.conf.beat_max_loop_interval or DEFAULT_MAX_INTERVAL

    def install_default_entries(self, data: dict[str, Any]) -> None:
        """重写父函数."""
        _ = data
        entries: dict[str, Any] = {}
        if self.app.conf.result_expires:
            entries.setdefault(
                "celery.backend_cleanup",
                {
                    "task": "celery.backend_cleanup",
                    "schedule": schedules.crontab("0", "4", "*"),
                    "options": {"expire_seconds": 12 * 3600},
                },
            )
        self.update_from_dict(entries)

    def schedules_equal(self, *args: Any, **kwargs: Any) -> bool:  # noqa: ANN401
        """Check if schedules are equal."""
        if self._heap_invalidated:
            self._heap_invalidated = False
            return False
        return super().schedules_equal(*args, **kwargs)

    def reserve(self, entry: ModelEntry) -> ModelEntry:
        """重写父函数."""
        new_entry = next(entry)
        # 需要按名称存储条目，因为条目可能会发生变化
        self._dirty.add(new_entry.name)
        return new_entry

    def setup_schedule(self) -> None:
        """重写父函数."""
        logger.info("setup_schedule")
        tasks = self.schedule
        self.install_default_entries(tasks)
        self.update_from_dict(self.app.conf.beat_schedule)

    def sync(self) -> None:
        """重写父函数."""
        tried: set[str] = set()
        failed: set[str] = set()
        try:
            while self._dirty:
                name = self._dirty.pop()
                try:
                    tasks = self.schedule
                    run_await(tasks[name].save)()
                    logger.debug("保存任务 %s 最新状态到数据库", name)
                    tried.add(name)
                except KeyError:
                    logger.exception("保存任务 %s 最新状态失败", name)
                    failed.add(name)
        except DatabaseError:
            logger.exception("同步时出现数据库错误")
        except InterfaceError as e:
            logger.warning("DatabaseScheduler InterfaceError: %s, 等待下次调用时重试...", e)
        finally:
            # 请稍后重试（仅针对失败的）
            self._dirty |= failed

    def tick(
        self,
        event_t: Any = event_t,  # noqa: ANN401
        min: Any = builtin_min,  # noqa: A002, ANN401
        heappop: Any = heapq.heappop,  # noqa: ANN401
        heappush: Any = heapq.heappush,  # noqa: ANN401
    ) -> float:
        """重写父函数."""
        if self.lock:
            logger.debug("beat: Extending lock...")
            run_await(self.lock.extend)(DEFAULT_MAX_LOCK_TIMEOUT, replace_ttl=True)

        return super().tick(event_t=event_t, min=min, heappop=heappop, heappush=heappush)

    def close(self) -> None:
        """重写父函数."""
        if self.lock:
            logger.info("beat: Releasing lock")
            if run_await(self.lock.owned)():
                run_await(self.lock.release)()
            self.lock = None

        super().close()

    def update_from_dict(self, dict_: dict[str, dict[str, Any]]) -> None:
        """重写父函数."""
        s: dict[str, ModelEntry] = {}
        name: str | None = None

        try:
            for name, entry_fields in dict_.items():
                entry = run_await(self.Entry.from_entry)(name, app=self.app, **entry_fields)
                if entry.model.enabled:
                    s[name] = entry
        except Exception:
            logger.exception("添加任务 %s 到数据库失败", name)
            raise

        tasks = self.schedule
        tasks.update(s)

    def schedule_changed(self) -> bool | None:
        """任务调度变更状态."""
        now = timezone.now()
        last_update = run_await(redis_client.get)(f"{settings.CELERY_REDIS_PREFIX}:last_update")
        if not last_update:
            run_await(redis_client.set)(f"{settings.CELERY_REDIS_PREFIX}:last_update", timezone.to_str(now))
            return False

        last, ts = self._last_update, timezone.from_str(last_update)
        try:
            return bool(ts and ts > (last or ts))
        finally:
            self._last_update = now

    async def get_all_task_schedulers(self) -> dict[str, ModelEntry]:
        """获取所有任务调度."""
        async with async_db_session() as db:
            logger.debug("DatabaseScheduler: Fetching database schedule")
            stmt = select(TaskScheduler).where(TaskScheduler.enabled == True)  # noqa: E712
            query = await db.execute(stmt)
            schedulers = query.scalars().all()
            s: dict[str, ModelEntry] = {}
            for scheduler in schedulers:
                s[scheduler.name] = self.Entry(scheduler, app=self.app)
            return s

    @property
    def schedule(self) -> dict[str, ModelEntry]:
        """获取任务调度."""
        initial = update = False
        if self._initial_read:
            logger.debug("DatabaseScheduler: initial read")
            initial = update = True
            self._initial_read = False
        elif self.schedule_changed():
            logger.info("DatabaseScheduler: Schedule changed.")
            update = True

        if update:
            logger.debug("beat: Synchronizing schedule...")
            self.sync()
            self._schedule = run_await(self.get_all_task_schedulers)()
            # 计划已更改，使 Scheduler.tick 中的堆无效
            if not initial:
                self._heap = []
                self._heap_invalidated = True
            logger.debug(
                "Current schedule:\n%s",
                "\n".join(repr(entry) for entry in self._schedule.values()),
            )

        # logger.debug(self._schedule)
        if self._schedule is None:
            self._schedule = {}
        return self._schedule


@beat_init.connect  # pyright: ignore[reportGeneralTypeIssues]
def acquire_distributed_beat_lock(sender: Any = None, **_kwargs: Any) -> None:  # noqa: ANN401
    """尝试在启动时获取锁.

    :param sender: 接收方应响应的发送方
    :return:
    """
    if sender is None:
        return

    scheduler = sender.scheduler
    if not scheduler.lock_key:
        return

    logger.debug("beat: Acquiring lock...")
    lock = redis_client.lock(
        scheduler.lock_key,
        timeout=DEFAULT_MAX_LOCK_TIMEOUT,
        sleep=scheduler.max_interval,
    )

    run_await(lock.acquire)()
    logger.info("beat: Acquired lock")
    scheduler.lock = lock
