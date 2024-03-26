from fastapi import APIRouter
from fastui import FastUI
from fastui import components as c

from ..shared import frame_page

router = APIRouter(prefix="/job/store", tags=["job_store"])


@router.get("", response_model=FastUI, response_model_exclude_none=True)
def store():
    return frame_page(c.Heading(text="Store"))
