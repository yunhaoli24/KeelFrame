"""Database."""  # pragma: exclude file

from typing import Any, cast

from celery import states  # pyright: ignore[reportMissingModuleSource]
from sqlalchemy.orm import Session
from celery.exceptions import ImproperlyConfigured
from celery.utils.time import maybe_timedelta
from celery.backends.base import BaseBackend
from celery.backends.database import retry, session_cleanup

from backend.app.task.session import SessionManager
from backend.app.task.model.result import Task, TaskSet, TaskExtended


"""
重写 from celery.backends.database 内部 DatabaseBackend 类, 此类实现与模型配合不佳, 导致 fba 创建表和 alembic 迁移困难
"""


class DatabaseBackend(BaseBackend):
    """The database result backend."""

    # ResultSet.iterate should sleep this much between each pool,
    # to not bombard the database with queries.
    subpolling_interval = 0.5

    task_cls: type[Task] = Task
    taskset_cls: type[TaskSet] = TaskSet

    def __init__(
        self,
        dburi: str | None = None,
        engine_options: dict[str, Any] | None = None,
        url: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize database backend."""
        # The `url` argument was added later and is used by
        # the app to set backend by url (celery.app.backends.by_url)
        super().__init__(expires_type=maybe_timedelta, url=url, **kwargs)
        conf: Any = self.app.conf

        if self.extended_result:
            self.task_cls = TaskExtended

        self.url = url or dburi or conf.database_url
        database_engine_options = cast("dict[str, Any]", conf.database_engine_options or {})
        self.engine_options = dict(engine_options or {}, **database_engine_options)
        self.short_lived_sessions = kwargs.get("short_lived_sessions", conf.database_short_lived_sessions)

        schemas: dict[str, str | None] = cast("dict[str, str | None]", conf.database_table_schemas or {})
        tablenames: dict[str, str | None] = cast("dict[str, str | None]", conf.database_table_names or {})
        self.task_cls.configure(schema=schemas.get("task"), name=tablenames.get("task"))
        self.taskset_cls.configure(schema=schemas.get("group"), name=tablenames.get("group"))

        if not self.url:
            msg = "Missing connection string! Do you have the database_url setting set to a real value?"
            raise ImproperlyConfigured(
                msg,
            )

        self.session_manager = SessionManager()

        create_tables_at_setup = conf.database_create_tables_at_setup
        if create_tables_at_setup is True:
            self._create_tables()

    @property
    def extended_result(self) -> bool:
        """Check if extended result mode is enabled."""
        return self.app.conf.find_value_for_key("extended", "result")

    def _create_tables(self) -> None:
        """Create the task and taskset tables."""
        self.result_session()

    def result_session(self, session_manager: SessionManager | None = None) -> Session:
        """Get result session."""
        if session_manager is None:
            session_manager = self.session_manager
        return session_manager.session_factory(
            dburi=self.url,
            short_lived_sessions=self.short_lived_sessions,
            **self.engine_options,
        )

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _store_result(
        self,
        task_id: str,
        result: Any,  # noqa: ANN401
        state: str,
        traceback: str | None = None,
        request: Any = None,  # noqa: ANN401
        **_kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Store return value and state of an executed task."""
        session = self.result_session()
        with session_cleanup(session):
            task = session.query(self.task_cls).filter(cast("Any", self.task_cls.task_id) == task_id).first()
            if not task:
                task = self.task_cls(task_id)
                task.task_id = task_id
                session.add(task)
                session.flush()

            self._update_result(task, result, state, traceback=traceback, request=request)
            session.commit()

    def _update_result(
        self,
        task: Task | TaskExtended,
        result: Any,  # noqa: ANN401
        state: str,
        traceback: str | None = None,
        request: Any = None,  # noqa: ANN401
    ) -> None:
        meta = self._get_result_meta(
            result=result,
            state=state,
            traceback=traceback,
            request=request,
            format_date=False,
            encode=True,
        )

        # Exclude the primary key id and task_id columns
        # as we should not set it None
        columns = [column.name for column in self.task_cls.__table__.columns if column.name not in {"id", "task_id"}]

        # Iterate through the columns name of the table
        # to set the value from meta.
        # If the value is not present in meta, set None
        for column in columns:
            value = meta.get(column)
            setattr(task, column, value)

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _get_task_meta_for(self, task_id: str) -> dict[str, Any]:
        """Get task meta-data for a task by id."""
        session = self.result_session()
        with session_cleanup(session):
            task = session.query(self.task_cls).filter(cast("Any", self.task_cls.task_id) == task_id).first()
            if not task:
                task = self.task_cls(task_id)
                task.status = states.PENDING
                task.result = None
            data = task.to_dict()
            if data.get("args", None) is not None:
                data["args"] = self.decode(data["args"])
            if data.get("kwargs", None) is not None:
                data["kwargs"] = self.decode(data["kwargs"])
            return self.meta_from_decoded(data)

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _save_group(self, group_id: str, result: Any) -> Any:  # noqa: ANN401
        """Store the result of an executed group."""
        session = self.result_session()
        with session_cleanup(session):
            group = self.taskset_cls(group_id, result)
            session.add(group)
            session.flush()
            session.commit()
            return result

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _restore_group(self, group_id: str) -> dict[str, Any] | None:
        """Get meta-data for group by id."""
        session = self.result_session()
        with session_cleanup(session):
            group = (
                session.query(self.taskset_cls).filter(cast("Any", self.taskset_cls.taskset_id) == group_id).first()
            )
            if group:
                return group.to_dict()
            return None

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _delete_group(self, group_id: str) -> None:
        """Delete meta-data for group by id."""
        session = self.result_session()
        with session_cleanup(session):
            session.query(self.taskset_cls).filter(cast("Any", self.taskset_cls.taskset_id) == group_id).delete()
            session.flush()
            session.commit()

    @retry  # pyright: ignore[reportGeneralTypeIssues]
    def _forget(self, task_id: str) -> None:
        """Forget about result."""
        session = self.result_session()
        with session_cleanup(session):
            session.query(self.task_cls).filter(cast("Any", self.task_cls.task_id) == task_id).delete()
            session.commit()

    def cleanup(self) -> None:
        """Delete expired meta-data."""
        session = self.result_session()
        expires = self.expires
        now = self.app.now()
        with session_cleanup(session):
            session.query(self.task_cls).filter(cast("Any", self.task_cls.date_done) < (now - expires)).delete()
            session.query(self.taskset_cls).filter(cast("Any", self.taskset_cls.date_done) < (now - expires)).delete()
            session.commit()

    def __reduce__(
        self,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Reduce for pickling."""
        kwargs = kwargs or {}
        kwargs.update({"dburi": self.url, "expires": self.expires, "engine_options": self.engine_options})
        return super().__reduce__(args, kwargs)
