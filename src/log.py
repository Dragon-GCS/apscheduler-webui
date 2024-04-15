# cspell: words autoinit
import os
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

PARSE_PATTERN = (
    r"\[\s*(?P<pid>\d+)\] (?P<time>[\d\s:-]+) \| "
    r"(?P<level>\w+)\s*\| (?P<name>.*?):(?P<line>\d+)\s(?P<message>.*)\n?"
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
    rotation="1 day",
)

server_log = logger.bind(server=True)
