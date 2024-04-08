from importlib import import_module

from fastapi import APIRouter
from fastui.forms import SelectSearchResponse

from ..scheduler import scheduler

router = APIRouter(prefix="/api", tags=["job"])


@router.get("/job-stores", description="Get available job stores")
def get_job_stores() -> SelectSearchResponse:
    stores = [
        {
            "value": name,
            "label": f"{name}({store.__class__.__name__})",
        }
        for name, store in scheduler._jobstores.items()
    ]
    return SelectSearchResponse(options=stores)  # type: ignore


@router.get("/executors", description="Get available job stores")
def get_executors() -> SelectSearchResponse:
    executors = [
        {
            "value": name,
            "label": f"{name}({executor.__class__.__name__})",
        }
        for name, executor in scheduler._executors.items()
    ]
    return SelectSearchResponse(options=executors)  # type: ignore


@router.get("/available-job-stores", description="Get available job stores")
def get_available_job_stores() -> SelectSearchResponse:
    stores = [{"value": "Memory", "label": "Memory"}]
    for store in ["MongoDB", "Redis", "SqlAlchemy"]:
        try:
            import_module(f"apscheduler.jobstores.{store.lower()}")
            stores.append({"value": store, "label": f"{store}JobStore"})
        except ImportError as e:
            print(e)

    return SelectSearchResponse(options=stores)  # type: ignore