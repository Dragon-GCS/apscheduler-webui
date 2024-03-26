from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastui import prebuilt_html

from src.routes.job import router as job_router
from src.routes.job_store import router as store_router
from src.routes.api import router as api_router
from src.scheduler import scheduler
from src.scripts import jobs_a


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    app.state.scheduler = scheduler
    scheduler.add_job(lambda: print("Hello, world!"), "cron", id="hello", day=1, name="hello")
    scheduler.add_job(jobs_a, "interval", id="jobs_a", days=1, weeks=1, name="jobs_a")
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(job_router)
app.include_router(store_router)
app.include_router(api_router)


@app.get("/{path:path}")
def index(path: str) -> HTMLResponse:
    print(f"{path=}")
    return HTMLResponse(prebuilt_html(api_root_url="/job"))


if __name__ == "__main__":
    print("Hello, world!")
