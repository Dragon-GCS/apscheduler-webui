import datetime
import json
from calendar import week
from typing import Annotated, Literal, TypeAlias

from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import (
    BaseModel,
    Field,
    PlainSerializer,
    model_validator,
)

from .scheduler import scheduler

AllTrigger: TypeAlias = CronTrigger | DateTrigger | IntervalTrigger


def format_date(date: datetime.datetime | datetime.date | None):
    if date is None:
        return None
    return date.strftime("%Y-%m-%d %H:%M:%S")


class TriggerParam(BaseModel):
    year: Annotated[str | None, Field(None, title="Year", description="Available for Cron & Date")]
    month: Annotated[
        str | None, Field(None, title="Month", description="Available for Cron & Date")
    ]
    week: Annotated[
        str | None, Field(None, title="Week", description="Available for Cron & Interval")
    ]
    day: Annotated[
        str | None, Field(None, title="Day of Month", description="Available for all trigger")
    ]
    day_of_week: Annotated[
        str | None, Field(None, title="Day Of Week", description="Available for Cron")
    ]
    hour: Annotated[str | None, Field(None, title="Hour", description="Available for all trigger")]
    minute: Annotated[
        str | None, Field(None, title="Minute", description="Available for all trigger")
    ]
    second: Annotated[
        str | None, Field(None, title="Second", description="Available for all trigger")
    ]
    start_date: Annotated[
        datetime.datetime | None,
        Field(None, title="Start Date", description="Available for Cron & Interval"),
        PlainSerializer(format_date),
    ]
    end_date: Annotated[
        datetime.datetime | None,
        Field(None, title="End Date", description="Available for Cron & Interval"),
        PlainSerializer(format_date),
    ]

    @model_validator(mode="before")
    @classmethod
    def parse_date(cls, trigger: AllTrigger | dict) -> dict:
        if isinstance(trigger, DateTrigger):
            date: datetime.datetime = trigger.run_date  # type: ignore
            trigger_param = {k: str(getattr(date, k)) for k in cls.model_fields if hasattr(date, k)}
        elif isinstance(trigger, CronTrigger):
            trigger_param = {field.name: str(field) for field in trigger.fields} | {
                "start_date": trigger.start_date,
                "end_date": trigger.end_date,
            }
        elif isinstance(trigger, IntervalTrigger):
            trigger_param = {
                k: str(getattr(trigger.interval, f"{k}s"))
                for k in cls.model_fields
                if hasattr(trigger.interval, f"{k}s")
            } | {
                "start_date": trigger.start_date,
                "end_date": trigger.end_date,
            }
        elif isinstance(trigger, dict):
            trigger_param = dict(filter(lambda i: i[1], trigger.items()))
        else:
            raise ValueError(f"Invalid trigger: {trigger}(type: {type(trigger)}")
        return trigger_param

    def get_trigger(self, trigger: Literal["Cron", "Date", "Interval"]) -> AllTrigger:
        if trigger == "Cron":
            return CronTrigger(
                year=self.year,
                month=self.month,
                week=self.week,
                day=self.day,
                day_of_week=self.day_of_week,
                hour=self.hour,
                minute=self.minute,
                second=self.second,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        elif trigger == "Date":
            params = {
                k: int(v)
                for k, v in self.model_dump(
                    exclude_none=True, include={"year", "month", "day", "hour", "minute", "second"}
                )
            }
            return DateTrigger(run_date=datetime.datetime(**params))  # type: ignore
        elif trigger == "Interval":
            return IntervalTrigger(
                weeks=int(self.week or 0),
                days=int(self.day or 0),
                hours=int(self.hour or 0),
                minutes=int(self.minute or 0),
                seconds=int(self.second or 0),
                start_date=self.start_date,
                end_date=self.end_date,
            )
        else:
            raise ValueError(f"Invalid trigger: {trigger}")


class JobInfo(BaseModel):
    id: Annotated[str, Field(title="ID")]
    name: Annotated[str, Field(title="Name")]
    next_run_time: Annotated[
        datetime.datetime | None, Field(title="Next Run"), PlainSerializer(format_date)
    ]
    executor: Annotated[
        str | None,
        Field(None, title="Executor", json_schema_extra={"search_url": "/api/executors"}),
    ]
    job_store: Annotated[
        str | None,
        Field(None, title="Job Store", json_schema_extra={"search_url": "/api/job-stores"}),
    ]
    trigger: Annotated[Literal["Cron", "Date", "Interval"], Field(title="Trigger")]
    trigger_params: Annotated[TriggerParam, Field(title="Trigger Params")]
    func: Annotated[str, Field(title="Function")]
    args: Annotated[
        str, Field(default="[]", title="Arguments", description="List with json format")
    ]
    kwargs: Annotated[
        str, Field(default="{}", title="Keyword Arguments", description="Dict with json format")
    ]
    coalesce: Annotated[bool, Field(default=True, title="Coalesce")]
    max_instances: Annotated[int, Field(title="Max Instances")]
    misfire_grace_time: Annotated[int | None, Field(title="Misfire Grace Time")]

    @model_validator(mode="before")
    @classmethod
    def parse_job(cls, job: Job) -> dict:
        data = {name: getattr(job, name) for name in job.__slots__}
        executor = job.executor
        executor_class = scheduler._executors[executor].__class__
        data["executor"] = f"{executor_class.__name__}({executor})"

        job_store = job._jobstore_alias
        job_store_class = scheduler._jobstores[job_store].__class__
        data["job_store"] = f"{job_store_class.__name__}({job_store})"

        data["func"] = f"{job.func.__module__}.{job.func.__qualname__}"
        data["args"] = json.dumps(job.args)
        data["kwargs"] = json.dumps(job.kwargs)
        data["trigger"] = job.trigger.__class__.__name__.removesuffix("Trigger")
        data["trigger_params"] = job.trigger
        return data


class ModifyJobParam(BaseModel):
    name: Annotated[str, Field(title="Name")]
    job_stores: Annotated[str | None, Field(None, title="Job Stores")]
    executor: Annotated[str | None, Field(None, title="Executor")]
    trigger: Annotated[Literal["Cron", "Date", "Interval"], Field(title="Trigger")]
    trigger_params: Annotated[TriggerParam, Field(title="Trigger Params")]
    args: Annotated[tuple, Field(tuple(), title="Arguments", description="List with json format")]
    kwargs: Annotated[
        dict, Field({}, title="Keyword Arguments", description="Dict with json format")
    ]
    coalesce: Annotated[bool, Field(True, title="Coalesce")]
    max_instances: Annotated[int, Field(title="Max Instances")]
    misfire_grace_time: Annotated[int, Field(title="Misfire Grace Time")]

    @model_validator(mode="before")
    @classmethod
    def parse_params(cls, params: dict) -> dict:
        params["args"] = tuple(json.loads(params.get("args", "[]")))
        params["kwargs"] = dict(json.loads(params.get("kwargs", "{}")))
        params["coalesce"] = params["coalesce"] == "on"
        return params

    def get_trigger(self):
        trigger_params = self.trigger_params.model_dump(exclude_none=True)
        if not trigger_params:
            return
        return self.trigger_params.get_trigger(self.trigger)
