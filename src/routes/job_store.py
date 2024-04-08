from typing import Annotated
from fastapi import APIRouter
from fastui import FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import PageEvent
from fastui.forms import fastui_form

from ..scheduler import scheduler
from ..schema import JobStoreInfo
from ..shared import frame_page, operate_finish, operate_result

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
                c.Button(
                    text="New Store",
                    on_click=PageEvent(name="new_store"),
                    class_name="+ ms-2",
                    named_style="secondary",
                )
            ],
            class_name="my-3",
        ),
        c.Modal(
            title="New Job Store",
            body=[
                c.ModelForm(
                    submit_url="/job/store/new",
                    model=JobStoreInfo,
                )
            ],
            open_trigger=PageEvent(name="new_store"),
        ),
        c.Table(
            data=job_stores,
            columns=[
                DisplayLookup(field="alias", table_width_percent=20),
                DisplayLookup(field="type_", table_width_percent=20),
                DisplayLookup(field="detail"),
            ],
        ),
        operate_finish(),
    )


@router.post("/new")
async def new_job_store(new_store: Annotated[JobStoreInfo, fastui_form(JobStoreInfo)]):
    job_store = new_store.get_store()
    scheduler.add_jobstore(job_store, alias=new_store.alias)
    return operate_result("new_store")
