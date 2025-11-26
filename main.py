from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastui import prebuilt_html

from src.routes.api import router as api_router
from src.routes.executor import router as executor_router
from src.routes.job import router as job_router
from src.routes.job_log import router as log_router
from src.routes.job_store import router as store_router
from src.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(executor_router)
app.include_router(store_router)
app.include_router(log_router)
app.include_router(job_router)  # this router has a wildcard path: /job/{action}/{id}
app.include_router(api_router)


@app.get("/{path:path}")
def index(path: str) -> HTMLResponse:
    return HTMLResponse(prebuilt_html(api_root_url="/job"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
