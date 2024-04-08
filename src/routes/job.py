from typing import Annotated

from fastapi import APIRouter, Depends
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent

from src.deps import parse_form
from src.scheduler import scheduler
from src.schema import JobInfo, ModifyJobParam
from src.shared import confirm_modal, frame_page

router = APIRouter(prefix="/job", tags=["job"])


@router.get("/", response_model=FastUI, response_model_exclude_none=True)
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
                DisplayLookup(field="id", on_click=GoToEvent(url="/detail/{id}")),
                DisplayLookup(field="name"),
                DisplayLookup(field="executor"),
                DisplayLookup(field="trigger"),
                DisplayLookup(field="next_run_time"),
            ],
        ),
    )


@router.get("/detail/{id}", response_model=FastUI, response_model_exclude_none=True)
async def job_detail(id: str):
    job = scheduler.get_job(id)
    assert job
    job_model = JobInfo.model_validate(job)
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Job Detail"),
        c.Div(
            components=[
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
                            model=JobInfo,
                            initial=job_model.model_dump(exclude_defaults=True),
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
                c.Modal(
                    title="Operation finish",
                    body=[
                        c.Button(text="OK", on_click=GoToEvent(url="/")),
                    ],
                    open_trigger=PageEvent(name="operate_finish"),
                ),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Details(data=job_model),
    )


def operate_result(clear_modal: str):
    return [
        c.FireEvent(event=PageEvent(name=clear_modal, clear=True)),
        c.FireEvent(event=PageEvent(name="operate_finish")),
    ]


@router.post("/pause/{id}", response_model=FastUI, response_model_exclude_none=True)
async def pause_job(id: str):
    scheduler.pause_job(id)
    return operate_result("pause_job")


@router.post("/resume/{id}", response_model=FastUI, response_model_exclude_none=True)
async def resume_job(id: str):
    scheduler.resume_job(id)
    return operate_result("resume_job")


@router.post("/modify/{id}", response_model=FastUI, response_model_exclude_none=True)
async def modify_job(
    id: str, job_info: Annotated[ModifyJobParam, Depends(parse_form(ModifyJobParam))]
):
    modify_kwargs = job_info.model_dump(exclude={"trigger", "trigger_params"})
    modify_kwargs["trigger"] = job_info.get_trigger()
    modify_kwargs = dict(filter(lambda x: x[1], modify_kwargs.items()))
    scheduler.modify_job(id, **modify_kwargs)

    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Modify Job"),
        c.Text(text=f"Modify job {id}"),
    )


@router.post("/remove/{id}", response_model=FastUI, response_model_exclude_none=True)
async def remove_job(id: str):
    scheduler.remove_job(id)
    return operate_result("remove_job")
