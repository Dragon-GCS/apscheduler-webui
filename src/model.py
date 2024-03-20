import datetime
from enum import Enum
from typing import Annotated

from apscheduler.job import Job
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
        data["trigger"] = data["trigger"].__class__.__name__
        return data


class JobInfo(JobBase):
    id: Annotated[str, Field(title="ID")]
    name: Annotated[str, Field(title="Name")]
    next_run_time: Annotated[datetime.datetime, Field(title="Next Run")]
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

    trigger: Annotated[Trigger, Field(title="Trigger")]
    args: Annotated[str, Field(title="Arguments")]
    kwargs: Annotated[dict, Field(title="Keyword Arguments")]
    job_store: Annotated[
        str,
        Field(title="Job Store", json_schema_extra={"search_url": "/api/job-stores"}),
    ]
    coalesce: Annotated[bool, Field(title="Coalesce")]
    max_instances: Annotated[int, Field(title="Max Instances")]
