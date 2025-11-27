# cspell: words autoinit
import datetime
import inspect
import logging
import os
import re
from typing import TYPE_CHECKING

LOG_FORMAT = (
    "<green>[{process: >5}] {time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan>\t{message}"
)
os.environ["LOGURU_FORMAT"] = LOG_FORMAT

from loguru import logger as server_log

from .config import LOG_PATH

if TYPE_CHECKING:
    from loguru import Record

PARSE_PATTERN = re.compile(
    r"\[\s*(?P<pid>\d+)\] (?P<time>[\d\s:-]+) \| "
    # (?=\n\[|\Z): message match until next line start or end
    r"(?P<level>\w+)\s*\| (?P<name>.*?):(?P<line>\d+)\s(?P<message>.*?)(?=\n\[|\Z)",
    flags=re.S,  # match multiple lines
)


def filter_server_record(record: "Record") -> bool:
    """Filter apscheduler and WebUI logs."""

    return bool(record["name"] and record["name"].startswith(("apscheduler.", "src.")))


server_log.add(
    # Log file for WebUI and apscheduler
    LOG_PATH / "scheduler.log",
    diagnose=False,
    enqueue=True,
    filter=filter_server_record,
    rotation="100 MB",
)
server_log.add(
    # Log file for jobs (rotated daily)
    LOG_PATH / "jobs.{time:YYYY-MM-DD}.log",
    diagnose=False,
    enqueue=True,
    filter=lambda record: not filter_server_record(record),
    rotation=datetime.time(0, 0),
)


# Intercept standard logging messages to use Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        if not record.name.startswith("apscheduler."):
            return  # Ignore non-apscheduler logs
        level: str | int
        try:
            level = server_log.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        server_log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
