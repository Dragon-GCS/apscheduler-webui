from typing import Annotated

from fastapi import APIRouter, Form
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.components.forms import FormFieldInput
from fastui.events import PageEvent
from fastui.forms import fastui_form

from ..scheduler import scheduler
from ..schema import ExecutorInfo
from ..shared import Components, frame_page

router = APIRouter(prefix="/job/executor", tags=["executor"])


@router.get("", response_model=FastUI, response_model_exclude_none=True)
def store() -> Components:
    executors = [
        ExecutorInfo.model_validate({"alias": alias, "executor": executor})
        for alias, executor in scheduler._executors.items()
    ]

    return frame_page(
        c.Heading(text="Executor"),
        c.Div(
            components=[
                c.Button(text="New Executor", on_click=PageEvent(name="new_executor")),
                c.Modal(
                    title="New Job Executor",
                    body=[c.ModelForm(submit_url="/job/executor/new", model=ExecutorInfo)],
                    open_trigger=PageEvent(name="new_executor"),
                ),
                c.Button(
                    text="Remove Executor",
                    on_click=PageEvent(name="remove_executor"),
                    named_style="warning",
                ),
                c.Modal(
                    title="Remove Executor",
                    body=[
                        c.Form(
                            form_fields=[
                                FormFieldInput(name="alias", title="Alias", required=True)
                            ],
                            submit_url="/job/executor/remove",
                        )
                    ],
                    open_trigger=PageEvent(name="remove_executor"),
                ),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Table(
            data=executors,
            columns=[
                DisplayLookup(field="alias", table_width_percent=20),
                DisplayLookup(field="type_", table_width_percent=20),
                DisplayLookup(field="max_worker"),
            ],
        ),
    )


@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
async def new_executor(
    new_executor: Annotated[ExecutorInfo, fastui_form(ExecutorInfo)],
) -> c.Paragraph:
    alias = new_executor.alias
    if new_executor.alias in scheduler._jobstores:
        return c.Paragraph(text=f"Executor({alias=}) already exists.")
    executor = new_executor.get_executor()
    scheduler.add_executor(executor, alias=new_executor.alias)
    return c.Paragraph(text=f"New executor({alias=}) added successfully.")


@router.post("/remove", response_model=FastUI, response_model_exclude_none=True)
async def remove_executor(alias: Annotated[str, Form()]) -> c.Paragraph:
    if alias not in scheduler._executors:
        return c.Paragraph(text=f"Executor({alias=}) not exists.")
    if alias == "default":
        return c.Paragraph(text="Cannot remove default executor.")
    scheduler.remove_executor(alias)
    return c.Paragraph(text=f"Executor({alias=}) removed successfully.")
