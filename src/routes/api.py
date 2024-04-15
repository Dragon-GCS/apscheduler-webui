from importlib import import_module

from fastapi import APIRouter
from fastui.forms import SelectOption, SelectSearchResponse

from ..config import LOG_PATH
from ..scheduler import scheduler

router = APIRouter(prefix="/api", tags=["job"])


@router.get("/job-stores", description="Get available job stores")
def get_job_stores() -> SelectSearchResponse:
    stores = [
        SelectOption(value=name, label=f"{name}({store.__class__.__name__})")
        for name, store in scheduler._jobstores.items()
    ]
    return SelectSearchResponse(options=stores)


@router.get("/executors", description="Get available job stores")
def get_executors() -> SelectSearchResponse:
    executors = [
        SelectOption(value=name, label=f"{name}({executor.__class__.__name__})")
        for name, executor in scheduler._executors.items()
    ]
    return SelectSearchResponse(options=executors)


@router.get("/available-job-stores", description="Get available job stores")
def get_available_job_stores() -> SelectSearchResponse:
    stores = [SelectOption(value="Memory", label="Memory")]
    for store in ["MongoDB", "Redis", "SQLAlchemy"]:
        try:
            import_module(f"apscheduler.jobstores.{store.lower()}")
            stores.append(SelectOption(value=store, label=f"{store}JobStore"))
        except ImportError as e:
            print(e)

    return SelectSearchResponse(options=stores)


@router.get("/available-logs", description="Get available log file")
def get_available_job_logs(q: str = "") -> SelectSearchResponse:
    logs = [
        SelectOption(value=file.name, label=file.name)
        for file in LOG_PATH.iterdir()
        if file.suffix == ".log" and file.name.startswith("jobs") and q in file.name
    ]
    return SelectSearchResponse(options=logs)
