from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastui import FastUI, prebuilt_html
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from src.model import JobInfo
from src.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    app.state.scheduler = scheduler
    scheduler.add_job(lambda: print("Hello, world!"), "cron", id="hello", day=1, name="hello")
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/ui/", response_model=FastUI, response_model_exclude_none=True)
async def ui():
    job = scheduler.get_job("hello")
    assert job
    job = JobInfo.model_validate(job)
    return [
        c.Page(
            components=[
                c.Heading(text="Jobs"),
                c.Table(
                    data=[job],
                    columns=[
                        DisplayLookup(field="id"),
                        DisplayLookup(field="name"),
                        DisplayLookup(field="trigger"),
                        DisplayLookup(field="next_run_time"),
                        DisplayLookup(field="action", on_click=GoToEvent(url="/ui/")),
                    ],
                ),
            ]
        )
    ]


@app.get("/{path:path}")
def index(path: str) -> HTMLResponse:
    print(path)
    return HTMLResponse(prebuilt_html(api_root_url="/ui"))


if __name__ == "__main__":
    print("Hello, world!")
