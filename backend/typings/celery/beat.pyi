from typing import Any
from datetime import datetime

class event_t: ...  # noqa: N801

class ScheduleEntry:
    app: Any
    name: str
    task: str
    args: tuple[Any, ...] | None
    kwargs: dict[str, Any] | None
    options: dict[str, Any]
    schedule: Any
    last_run_at: datetime

    def __init__(self, app: Any = ..., name: str = ..., task: str = ...) -> None: ...  # noqa: ANN401
    def __next__(self, last_run_at: datetime | None = ...) -> ScheduleEntry: ...

class Scheduler:
    app: Any
    max_interval: float
    _heap: list[Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...  # noqa: ANN401
    def install_default_entries(self, data: dict[str, Any]) -> None: ...
    def schedules_equal(self, *args: Any, **kwargs: Any) -> bool: ...  # noqa: ANN401
    def reserve(self, entry: Any) -> Any: ...  # noqa: ANN401
    def setup_schedule(self) -> None: ...
    def sync(self) -> None: ...
    def tick(
        self,
        event_t: Any = ...,  # noqa: ANN401
        min: Any = ...,  # noqa: A002, ANN401
        heappop: Any = ...,  # noqa: ANN401
        heappush: Any = ...,  # noqa: ANN401
    ) -> float: ...
    def close(self) -> None: ...
    def update_from_dict(self, dict_: dict[str, dict[str, Any]]) -> None: ...
    @property
    def schedule(self) -> dict[str, Any]: ...
