import datetime
from typing import Annotated

from apscheduler.job import Job
from fastui import components as c
from pydantic import BaseModel, Field, model_validator

from .scheduler import scheduler


class JobInfo(BaseModel):
    id: Annotated[str, Field(title="ID")]
    name: Annotated[str, Field(title="Name")]
    next_run_time: Annotated[datetime.datetime, Field(title="Next Run Time")]
    trigger: Annotated[str, Field(title="Trigger")]
    action: Annotated[c.Button, Field(title="Action", default="详情")]
    func: Annotated[str, Field(title="Function")]
    args: Annotated[tuple, Field(title="Arguments")]
    kwargs: Annotated[dict, Field(title="Keyword Arguments")]
    job_store: Annotated[str, Field(title="Job Store")]
    executor: Annotated[str, Field(title="Executor")]
    coalesce: Annotated[bool, Field(title="Coalesce")]
    max_instances: Annotated[int, Field(title="Max Instances")]

    @model_validator(mode="before")
    @classmethod
    def check_card_number_omitted(cls, job: Job) -> dict:
        data = {name: getattr(job, name) for name in job.__slots__}
        job_store = data.pop("_jobstore_alias")
        data["job_store"] = f"{scheduler._jobstores[job_store]}({job_store})"
        executor = data.pop("executor")
        data["executor"] = f"{scheduler._executors[executor]}({executor})"
        data["func"] = f"{data['func'].__class__.__name__}"
        data["trigger"] = f"{data['trigger'].__class__.__name__}"
        return data
