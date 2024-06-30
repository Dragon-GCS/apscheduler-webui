from importlib import import_module, reload
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import fastui_form

from ..scheduler import scheduler
from ..schema import JobInfo, ModifyJobParam, NewJobParam
from ..shared import confirm_modal, frame_page

router = APIRouter(prefix="/job", tags=["job"])


@router.get("/", response_model=FastUI, response_model_exclude_none=True)
async def jobs():
    jobs = scheduler.get_jobs()

    return frame_page(
        c.Heading(text="Job"),
        c.Div(
            components=[c.Button(text="New Job", on_click=PageEvent(name="new_job"))],
            class_name="mb-3",
        ),
        c.Modal(
            title="New Job",
            open_trigger=PageEvent(name="new_job"),
            body=[
                c.ModelForm(
                    submit_url="/job/",
                    display_mode="default",
                    model=JobInfo,
                    initial={"id": uuid4().hex},
                ),
            ],
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


@router.post("/", response_model=FastUI, response_model_exclude_none=True)
async def new_job(job_info: Annotated[NewJobParam, fastui_form(NewJobParam)]):
    trigger = job_info.get_trigger()
    job = scheduler.add_job(
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
    return [
        c.Paragraph(text=f"Created new job(id={job.id})"),
        # TODO: GotoEvent will not refresh the page
        c.Button(text="Back Home", on_click=GoToEvent(url="/")),
    ]


@router.get("/detail/{id}", response_model=FastUI, response_model_exclude_none=True)
async def job_detail(id: str):
    job = scheduler.get_job(id)
    if not job:
        return [c.FireEvent(event=GoToEvent(url="/"))]
    job_model = JobInfo.model_validate(job)
    return frame_page(
        c.Link(components=[c.Text(text="Back")], on_click=BackEvent()),
        c.Heading(text="Job Detail"),
        c.Div(
            components=[
                # confirm model will be triggered by the underscored title of the modal
                c.Button(text="Pause", on_click=PageEvent(name="pause_job")),
                confirm_modal(title="Pause Job", submit_url=f"/pause/{id}"),
                c.Button(text="Resume", on_click=PageEvent(name="resume_job")),
                confirm_modal(title="Resume Job", submit_url=f"/resume/{id}"),
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
                c.Button(text="Reload", on_click=PageEvent(name="reload_job")),
                confirm_modal(title="Reload Job", submit_url=f"/reload/{id}"),
                c.Button(
                    text="Remove", on_click=PageEvent(name="remove_job"), named_style="warning"
                ),
                confirm_modal(title="Remove Job", submit_url=f"/remove/{id}"),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Details(data=job_model),
    )


@router.post("/modify/{id}", response_model=FastUI, response_model_exclude_none=True)
async def modify_job(id: str, job_info: Annotated[ModifyJobParam, fastui_form(ModifyJobParam)]):
    modify_kwargs = job_info.model_dump(exclude={"trigger", "trigger_params"})
    modify_kwargs["trigger"] = job_info.get_trigger()
    modify_kwargs = dict(filter(lambda x: x[1], modify_kwargs.items()))
    scheduler.modify_job(id, **modify_kwargs)

    return [
        c.Paragraph(text="Job config after modified"),
        c.Json(value=modify_kwargs),
        c.Button(text="Back Home", on_click=GoToEvent(url="/")),
    ]


@router.post("/{action}/{id}", response_model=FastUI, response_model_exclude_none=True)
async def pause_job(action: Literal["pause", "resume", "modify", "reload", "remove"], id: str):
    job = scheduler.get_job(id)
    assert job, f"Job({id=}) not found"

    match action:
        case "pause":
            scheduler.pause_job(id)
        case "resume":
            scheduler.resume_job(id)
        case "remove":
            scheduler.remove_job(id)
        case "reload":
            module = import_module(job.func.__module__)
            reload(module)
        case _:
            raise ValueError(f"Invalid action {action}")

    return [
        c.Paragraph(text=f"Job({id=}, name='{job.name}'), {action=} success."),
        c.Button(text="Back Home", on_click=GoToEvent(url="/")),
    ]
