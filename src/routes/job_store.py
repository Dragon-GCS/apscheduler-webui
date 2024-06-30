from typing import Annotated

from fastapi import APIRouter, Form
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.components.forms import FormFieldInput
from fastui.events import PageEvent
from fastui.forms import fastui_form

from ..scheduler import scheduler
from ..schema import JobStoreInfo
from ..shared import frame_page

router = APIRouter(prefix="/job/store", tags=["job_store"])


@router.get("", response_model=FastUI, response_model_exclude_none=True)
def store():
    job_stores = [
        JobStoreInfo.model_validate({"alias": alias, "store": store})
        for alias, store in scheduler._jobstores.items()
    ]

    return frame_page(
        c.Heading(text="Store"),
        c.Div(
            components=[
                c.Button(text="New Store", on_click=PageEvent(name="new_store")),
                c.Modal(
                    title="New Store",
                    body=[c.ModelForm(submit_url="/job/store/new", model=JobStoreInfo)],
                    open_trigger=PageEvent(name="new_store"),
                ),
                c.Button(
                    text="Remove Store",
                    on_click=PageEvent(name="remove_store"),
                    named_style="warning",
                ),
                c.Modal(
                    title="Remove Job Store",
                    body=[
                        c.Form(
                            form_fields=[
                                FormFieldInput(name="alias", title="Alias", required=True)
                            ],
                            submit_url="/job/store/remove",
                        )
                    ],
                    open_trigger=PageEvent(name="remove_store"),
                ),
            ],
            class_name="d-flex flex-start gap-3 mb-3",
        ),
        c.Table(
            data=job_stores,
            columns=[
                DisplayLookup(field="alias", table_width_percent=20),
                DisplayLookup(field="type_", table_width_percent=20),
                DisplayLookup(field="detail"),
            ],
        ),
    )


@router.post("/new", response_model=FastUI, response_model_exclude_none=True)
async def new_job_store(new_store: Annotated[JobStoreInfo, fastui_form(JobStoreInfo)]):
    alias = new_store.alias
    if new_store.alias in scheduler._jobstores:
        return c.Paragraph(text=f"Job store({alias=}) already exists")
    job_store = new_store.get_store()
    scheduler.add_jobstore(job_store, alias=alias)
    return c.Paragraph(text="New job store added successfully")


@router.post("/remove", response_model=FastUI, response_model_exclude_none=True)
async def remove_job_store(alias: str = Form()):
    if alias not in scheduler._jobstores:
        return c.Paragraph(text=f"Job store({alias=}) not exists")
    elif alias == "default":
        return c.Paragraph(text="Cannot remove default job store")
    scheduler.remove_jobstore(alias)
    return c.Paragraph(text=f"Job store({alias=}) removed successfully")
