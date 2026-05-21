"""Main."""

from rich.text import Text

from backend.utils.console import console
from backend.core.registrar import register_app
from backend.utils.timezone import timezone


_log_prefix = f"{timezone.to_str(timezone.now(), '%Y-%m-%d %H:%M:%S.%M0')} | {'INFO': <8} | - | "
console.print(Text(f"{_log_prefix}启动服务...", style="bold magenta"))

app = register_app()
