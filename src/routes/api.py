from fastapi import APIRouter
from fastui.forms import SelectSearchResponse

from ..scheduler import scheduler

router = APIRouter(prefix="/api", tags=["job"])


@router.get("/job-stores", description="Get available job stores")
def job_stores() -> SelectSearchResponse:
    stores = [
        {
            "value": store.__class__.__name__,
            "label": f"{name}({store.__class__.__name__})",
        }
        for name, store in scheduler._jobstores.items()
    ]
    return SelectSearchResponse(options=stores)  # type: ignore
