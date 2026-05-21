from typing import Any
from datetime import datetime, timedelta
from collections.abc import Callable

class ParseException(Exception): ...  # noqa: N818

class schedule:  # noqa: N801
    run_every: timedelta

    def __init__(
        self,
        run_every: float | timedelta = ...,
        relative: bool = ...,
        nowfun: Callable[[], datetime] | None = ...,
        app: Any = ...,  # noqa: ANN401
    ) -> None: ...
    def is_due(self, last_run_at: datetime) -> tuple[bool, int | float]: ...

class crontab(schedule):  # noqa: N801
    _orig_minute: str
    _orig_hour: str
    _orig_day_of_week: str
    _orig_day_of_month: str
    _orig_month_of_year: str

    def __init__(
        self,
        minute: str = ...,
        hour: str = ...,
        day_of_week: str = ...,
        day_of_month: str = ...,
        month_of_year: str = ...,
        nowfun: Callable[[], datetime] | None = ...,
        app: Any = ...,  # noqa: ANN401
    ) -> None: ...
    def remaining_estimate(self, last_run_at: datetime) -> timedelta: ...
    def now(self) -> datetime: ...
    def is_due(self, last_run_at: datetime) -> tuple[bool, int | float]: ...

def schedstate(is_due: bool, next: float) -> tuple[bool, int | float]: ...  # noqa: A002
def maybe_schedule(s: Any) -> Any: ...  # noqa: ANN401
