from typing import Literal

from fastapi import APIRouter
from fastui import FastUI
from fastui import components as c
from fastui.components.forms import FormField, FormFieldSelect, FormFieldSelectSearch
from fastui.events import GoToEvent

from ..config import LOG_PATH
from ..log import PARSE_PATTERN, logger
from ..shared import frame_page
from .api import get_available_job_logs

router = APIRouter(prefix="/job/log", tags=["job_log"])


def parse_log_message(text: str):
    messages = text.strip().split("\n", 1)
    if len(messages) > 1:
        return f"{messages[0]}\n```\n{messages[1]}\n```"
    return messages[0]


def log_content_to_markdown(log_name: str | None, level: str):
    if not (log_name and (LOG_PATH / log_name).exists()):
        return "Log not found"
    contents = "\n\n".join(
        [
            f"**[{line['pid']}] {line['time']}** *{line['level']}* "
            f"`{line['name']}:{line['line']}`: {parse_log_message(line['message'])}"
            for line in logger.parse(LOG_PATH / log_name, pattern=PARSE_PATTERN)
            if not level or level == line["level"]
        ][::-1]
    )
    return contents


@router.get("/{kind}", response_model=FastUI, response_model_exclude_none=True)
def get_log(kind: Literal["jobs", "scheduler"], log_file: str | None = None, level: str = ""):
    form_fields: list[FormField] = [
        FormFieldSelect(
            title="Level",
            name="level",
            placeholder="Filter by level",
            options=[
                {"value": level, "label": level}
                for level in logger._core.levels.keys()  # type: ignore
            ],
        )
    ]
    if kind == "jobs":
        field_initial = get_available_job_logs().options[0]
        if "options" in field_initial:
            field_initial = field_initial["options"][0]
        form_fields.append(
            FormFieldSelectSearch(
                title="Log File",
                name="log_file",
                search_url="/api/available-logs",
                initial=field_initial,
            ),
        )
        log_file = field_initial["value"]
    else:
        log_file = "scheduler.log"

    return frame_page(
        c.Heading(text="Logs"),
        c.LinkList(
            links=[
                c.Link(
                    components=[c.Text(text="Executor/Job/JobStore")],
                    on_click=GoToEvent(url="/log/jobs"),
                    active="/log/jobs",
                ),
                c.Link(
                    components=[c.Text(text="Scheduler")],
                    on_click=GoToEvent(url="/log/scheduler"),
                    active="/log/scheduler",
                ),
            ],
            mode="tabs",
            class_name="+ mb-4",
        ),
        c.Form(
            form_fields=form_fields,
            submit_url=".",
            method="GOTO",
            submit_on_change=True,
            display_mode="inline",
        ),
        c.Markdown(text=log_content_to_markdown(log_file, level), class_name="border rounded p-2"),
    )
