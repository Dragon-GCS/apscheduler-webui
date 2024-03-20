from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastui import FastUI, prebuilt_html
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import SelectSearchResponse

from src.model import JobDetail, JobInfo
from src.scheduler import scheduler
from src.scripts import jobs_a
from src.shared import confirm_modal, frame_page


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    app.state.scheduler = scheduler
    scheduler.add_job(lambda: print("Hello, world!"), "cron", id="hello", day=1, name="hello")
    scheduler.add_job(jobs_a, "interval", id="jobs_a", days=1, weeks=1, name="jobs_a")
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
        c.Div(
            components=[
                c.Button(
                    text="Run",
                    on_click=PageEvent(name="run_job"),
                ),
                confirm_modal(
                    title="Run Job Now",
                    modal_name="run_job",
                    submit_url=f"/job/run/{id}",
                    submit_trigger_name="submit_run_job",
                ),
                c.Button(
                    text="Pause",
                    on_click=PageEvent(name="pause_job"),
                ),
                confirm_modal(
                    title="Pause Job",
                    modal_name="pause_job",
                    submit_url=f"/job/pause/{id}",
                    submit_trigger_name="submit_pause_job",
                ),
                c.Button(
                    text="Resume",
                    on_click=PageEvent(name="resume_job"),
                ),
                confirm_modal(
                    title="Pause Job",
                    modal_name="resume_job",
                    submit_url=f"/job/resume/{id}",
                    submit_trigger_name="submit_resume_job",
                ),
                c.Button(text="Modify", on_click=PageEvent(name="modify_job")),
                c.Modal(
                    title="Modify Job",
                    body=[
                        c.ModelForm(
                            submit_url=f"/job/modify/{id}",
                            model=JobDetail,
                            initial=job_detail.model_dump(),
                        )
                    ],
                    open_trigger=PageEvent(name="modify_job"),
                ),
                c.Button(
                    text="Remove",
                    named_style="warning",
                    on_click=PageEvent(name="remove_job"),
                ),
                confirm_modal(
                    title=f"Remove Job {id}?",
                    modal_name="remove_job",
                    submit_url=f"/job/remove/{id}",
                    submit_trigger_name="submit_remove_job",
                ),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Details(data=JobInfo.model_validate(job)),
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
