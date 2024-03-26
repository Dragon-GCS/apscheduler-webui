import datetime
from enum import Enum
from typing import Annotated

from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field, model_validator

from .scheduler import scheduler


class JobBase(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def parse_job(cls, job: Job) -> dict:
        data = {name: getattr(job, name) for name in job.__slots__}
        executor = data.pop("executor")
        executor_class = scheduler._executors[executor].__class__
        job_store = data.pop("_jobstore_alias")
        job_store_class = scheduler._jobstores[job_store].__class__
        data["args"] = ",".join(data["args"])
        data["executor"] = f"{executor_class.__name__}({executor})"
        data["job_store"] = f"{job_store}({job_store_class.__name__})"
        data["func"] = f"{data['func'].__module__}.{data['func'].__qualname__}"
        data["date"] = data["trigger"]
        data["trigger"] = data["trigger"].__class__.__name__
        return data


class TriggerDate(BaseModel):
    year: Annotated[str, Field(title="Year", description="Available for all trigger")]
    month: Annotated[str, Field(title="Month", description="Available for all trigger")]
    week: Annotated[
        str, Field(title="Week", description="Available for CronTrigger & IntervalTrigger")
    ]
    day: Annotated[
        str,
        Field(title="Day", description="Available for all trigger, day of month for CronTrigger"),
    ]
    day_of_week: Annotated[str, Field(title="Day Of Week", description="Available for CronTrigger")]
    hour: Annotated[str, Field(title="Hour", description="Available for all trigger")]
    minute: Annotated[str, Field(title="Minute", description="Available for all trigger")]
    second: Annotated[str, Field(title="Second", description="Available for all trigger")]
    start_date: Annotated[
        datetime.datetime | None,
        Field(title="Start Date", description="Available for IntervalTrigger & CronTrigger"),
    ]
    end_date: Annotated[
        datetime.datetime | None,
        Field(title="End Date", description="Available for IntervalTrigger & CronTrigger"),
    ]

    @model_validator(mode="before")
    @classmethod
    def parse_date(cls, trigger: CronTrigger | DateTrigger | IntervalTrigger) -> dict:
        date_info = {
            "year": "",
            "month": "",
            "week": "",
            "day": "",
            "day_of_week": "",
            "hour": "",
            "minute": "",
            "second": "",
            "start_date": None,
            "end_date": None,
        }
        if isinstance(trigger, DateTrigger):
            date: datetime.datetime = trigger.run_date  # type: ignore
            date_info.update(
                {k: getattr(date, f"_{k}") for k in date_info if hasattr(date, f"_{k}")}
            )
        elif isinstance(trigger, CronTrigger):
            date_info.update(
                {field.name: str(field) for field in trigger.fields}
                | {"start_date": trigger.start_date, "end_date": trigger.end_date}
            )
        elif isinstance(trigger, IntervalTrigger):
            date_info.update(
                {k: str(getattr(trigger.interval, f"{k}s", "")) for k in date_info}
                | {"start_date": trigger.start_date, "end_date": trigger.end_date}
            )
        else:
            raise ValueError(f"Invalid trigger: {trigger}(type: {type(trigger)}")
        return date_info


class JobInfo(JobBase):
    id: Annotated[str, Field(title="ID")]
    name: Annotated[str, Field(title="Name")]
    next_run_time: Annotated[datetime.datetime | None, Field(title="Next Run")]
    executor: Annotated[str, Field(title="Executor")]
    job_store: Annotated[str, Field(title="Job Store")]
    trigger: Annotated[str, Field(title="Trigger")]
    func: Annotated[str, Field(title="Function")]


class Trigger(Enum):
    date = "DateTrigger"
    cron = "CronTrigger"
    interval = "IntervalTrigger"


class JobDetail(JobBase):
    """Job detail model for modifying jobs."""

    name: Annotated[str, Field(title="Name")]
    args: Annotated[str, Field(title="Arguments")]
    kwargs: Annotated[dict, Field(title="Keyword Arguments")]
    job_store: Annotated[
        str,
        Field(title="Job Store", json_schema_extra={"search_url": "/api/job-stores"}),
    ]
    coalesce: Annotated[bool, Field(title="Coalesce")]
    max_instances: Annotated[int, Field(title="Max Instances")]
    trigger: Annotated[Trigger, Field(title="Trigger")]
    date: Annotated[TriggerDate, Field(title="Date", description="Available for DateTrigger")]
