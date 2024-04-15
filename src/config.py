from pathlib import Path

from apscheduler.executors.asyncio import AsyncIOExecutor

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "logs"

SCHEDULER_CONFIG = {
    "executors": {"default": AsyncIOExecutor()},
    "jobstores": {},
}
