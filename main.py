from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastui import FastUI, prebuilt_html
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import SelectSearchResponse

from src.model import JobDetail, JobInfo
from src.scheduler import scheduler
from src.shared import frame_page
from src.scripts import jobs_a


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    app.state.scheduler = scheduler
    scheduler.add_job(lambda: print("Hello, world!"), "cron", id="hello", day=1, name="hello")
    scheduler.add_job(jobs_a, "interval", id="jobs_a", days=1, name="jobs_a")
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/job/", response_model=FastUI, response_model_exclude_none=True)
async def jobs():
    jobs = scheduler.get_jobs()

    return frame_page(
        c.Div(
            components=[
                c.Button(
                    text="New Job",
                    on_click=GoToEvent(url="/new"),
                    class_name="+ ms-2",
                    named_style="secondary",
                ),
                c.Button(
                    text="Stop All",
                    on_click=GoToEvent(url="/"),
                    named_style="secondary",
                    class_name="+ ms-2",
                ),
            ],
            class_name="my-3",
        ),
        c.Table(
            data=[JobInfo.model_validate(job) for job in jobs],
            columns=[
                DisplayLookup(field="id", on_click=GoToEvent(url="/{id}")),
                DisplayLookup(field="name"),
                DisplayLookup(field="executor"),
                DisplayLookup(field="trigger"),
                DisplayLookup(field="next_run_time"),
            ],
        ),
    )


@app.get("/job/store", response_model=FastUI, response_model_exclude_none=True)
def store():
    return frame_page(c.Heading(text="Store"))


@app.get("/api/job-stores")
def job_stores() -> SelectSearchResponse:
    stores = [
        {
            "value": store.__class__.__name__,
            "label": f"{name}({store.__class__.__name__})",
        }
        for name, store in scheduler._jobstores.items()
    ]
    return SelectSearchResponse(options=stores)  # type: ignore


@app.get("/job/{id}", response_model=FastUI, response_model_exclude_none=True)
async def job_detail(id: str):
    job = scheduler.get_job(id)
    assert job
    job_detail = JobDetail.model_validate(job)
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Job Detail"),
        c.Details(data=JobInfo.model_validate(job)),
        c.ModelForm(
            model=JobDetail,
            submit_url=f"/job/modify/{id}",
            initial=job_detail.model_dump(),
            display_mode="page",
        ),
    )


@app.post("/job/modify/{id}", response_model=FastUI, response_model_exclude_none=True)
def modify_job(id: str, **kwargs: Annotated[str, Form()]):
    print(kwargs)
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Modify Job"),
        c.Text(text=f"Modify job {id}"),
    )


@app.get("/{path:path}")
def index(path: str) -> HTMLResponse:
    return HTMLResponse(prebuilt_html(api_root_url="/job"))


if __name__ == "__main__":
    print("Hello, world!")
