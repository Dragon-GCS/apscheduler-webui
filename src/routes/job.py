from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import fastui_form

from ..scheduler import scheduler
from ..schema import JobInfo, ModifyJobParam, NewJobParam
from ..shared import confirm_modal, frame_page, operate_finish, operate_result

router = APIRouter(prefix="/job", tags=["job"])


@router.get("/", response_model=FastUI, response_model_exclude_none=True)
async def jobs():
    jobs = scheduler.get_jobs()

    return frame_page(
        c.Heading(text="Job"),
        c.Div(
            components=[c.Button(text="New Job", on_click=GoToEvent(url="/new"))],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Table(
            data=[JobInfo.model_validate(job) for job in jobs],
            data_model=JobInfo,
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
    job_model = JobInfo.model_validate(job)
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Job Detail"),
        c.Div(
            components=[
                c.Button(text="Pause", on_click=PageEvent(name="pause_job")),
                confirm_modal(
                    title="Pause Job", modal_name="pause_job", submit_url=f"/job/pause/{id}"
                ),
                c.Button(text="Resume", on_click=PageEvent(name="resume_job")),
                confirm_modal(
                    title="Resume Job", modal_name="resume_job", submit_url=f"/job/resume/{id}"
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
                    text="Remove", named_style="warning", on_click=PageEvent(name="remove_job")
                ),
                confirm_modal(
                    title="Remove Job?", modal_name="remove_job", submit_url=f"/job/remove/{id}"
                ),
                operate_finish(),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Details(data=job_model),
    )


@router.get("/new", response_model=FastUI, response_model_exclude_none=True)
async def create_job():
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Create Job"),
        c.ModelForm(
            display_mode="page", submit_url="/job/new", model=JobInfo, initial={"id": uuid4().hex}
        ),
    )


@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
async def new_job(job_info: Annotated[NewJobParam, fastui_form(NewJobParam)]):
    trigger = job_info.get_trigger()
    scheduler.add_job(
        job_info.func,
        trigger=trigger,
        args=job_info.args,
        kwargs=job_info.kwargs,
        coalesce=job_info.coalesce,
        max_instances=job_info.max_instances,
        misfire_grace_time=job_info.misfire_grace_time,
        name=job_info.name,
        id=job_info.id,
        executor=job_info.executor,
        jobstore=job_info.jobstore,
    )
    return [c.FireEvent(event=GoToEvent(url="/"))]


@router.post("/pause/{id}", response_model=FastUI, response_model_exclude_none=True)
async def pause_job(id: str):
    scheduler.pause_job(id)
    return operate_result("pause_job")


@router.post("/resume/{id}", response_model=FastUI, response_model_exclude_none=True)
async def resume_job(id: str):
    scheduler.resume_job(id)
    return operate_result("resume_job")


@router.post("/modify/{id}", response_model=FastUI, response_model_exclude_none=True)
async def modify_job(id: str, job_info: Annotated[ModifyJobParam, fastui_form(ModifyJobParam)]):
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
