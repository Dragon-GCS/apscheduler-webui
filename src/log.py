# cspell: words autoinit
import datetime
import inspect
import logging
import os
import re
import sys
from typing import TYPE_CHECKING

os.environ.setdefault("LOGURU_AUTOINIT", "False")

from loguru import logger

from .config import LOG_PATH

if TYPE_CHECKING:
    from loguru import Record


LOG_FORMAT = (
    "<green>[{process: >5}] {time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan>\t{message}"
)


PARSE_PATTERN = re.compile(
    r"\[\s*(?P<pid>\d+)\] (?P<time>[\d\s:-]+) \| "
    # (?=\n\[|\Z): message match until next line start or end
    r"(?P<level>\w+)\s*\| (?P<name>.*?):(?P<line>\d+)\s(?P<message>.*?)(?=\n\[|\Z)",
    flags=re.S,  # match multiple lines
)


def filter_server_record(record: "Record") -> bool:
    return record["extra"] == {"server": True}


logger.add(sys.stderr, format=LOG_FORMAT)
logger.add(
    LOG_PATH / "scheduler.log",
    format=LOG_FORMAT,
    diagnose=False,
    enqueue=True,
    filter="apscheduler",
)
logger.add(
    LOG_PATH / "jobs.{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    diagnose=False,
    enqueue=True,
    filter=filter_server_record,
    rotation=datetime.time(0, 0),
)

server_log = logger.bind(server=True)


# Intercept standard logging messages to use Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
