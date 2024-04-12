import datetime
import json
from typing import Annotated, Literal, TypeAlias

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import HTTPException
from pydantic import BaseModel, Field, PlainSerializer, model_validator
from pydantic.json_schema import SkipJsonSchema

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

    def get_trigger(
        self, trigger: Literal["Cron", "Date", "Interval"], next_run_time: datetime.datetime | None
    ) -> AllTrigger:
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
            keys = ("year", "month", "day", "hour", "minute", "second")
            params = {}
            if next_run_time is not None:
                params.update(getattr(next_run_time, k) for k in keys if hasattr(next_run_time, k))
            params.update({k: int(getattr(self, k)) for k in keys if hasattr(self, k)})
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
        str,
        Field("default", title="Executor", json_schema_extra={"search_url": "/api/executors"}),
    ]
    jobstore: SkipJsonSchema[
        Annotated[
            str,
            Field(
                "default", title="Job Store", json_schema_extra={"search_url": "/api/job-stores"}
            ),
        ]
    ]
    trigger: Annotated[Literal["Cron", "Date", "Interval"], Field(title="Trigger")]
    trigger_params: Annotated[TriggerParam, Field(title="Trigger Params")]
    func: Annotated[
        str, Field(title="Function", description="String parsed by 'scheduler.add_job'.")
    ]
    args: Annotated[
        str, Field(default="[]", title="Arguments", description="List with json format")
    ]
    kwargs: Annotated[
        str, Field(default="{}", title="Keyword Arguments", description="Dict with json format")
    ]
    coalesce: Annotated[bool, Field(default=True, title="Coalesce")]
    max_instances: Annotated[int, Field(1, title="Max Instances")]
    misfire_grace_time: Annotated[int | None, Field(None, title="Misfire Grace Time")]

    @model_validator(mode="before")
    @classmethod
    def parse(cls, job: Job) -> dict:
        data = {name: getattr(job, name) for name in job.__slots__}
        executor = job.executor
        executor_class = scheduler._executors[executor].__class__
        data["executor"] = f"{executor_class.__name__}({executor})"

        job_store = job._jobstore_alias
        job_store_class = scheduler._jobstores[job_store].__class__
        data["jobstore"] = f"{job_store_class.__name__}({job_store})"

        data["func"] = f"{job.func.__module__}.{job.func.__qualname__}"
        data["args"] = json.dumps(job.args)
        data["kwargs"] = json.dumps(job.kwargs)
        data["trigger"] = job.trigger.__class__.__name__.removesuffix("Trigger")
        data["trigger_params"] = job.trigger
        return data


class ModifyJobParam(BaseModel):
    name: Annotated[str, Field(title="Name")]
    next_run_time: Annotated[datetime.datetime | None, Field(None, title="Next Run")]
    trigger: Annotated[Literal["Cron", "Date", "Interval"], Field(title="Trigger")]
    trigger_params: Annotated[TriggerParam, Field(title="Trigger Params")]
    args: Annotated[tuple, Field(tuple(), title="Arguments", description="List with json format")]
    kwargs: Annotated[
        dict, Field({}, title="Keyword Arguments", description="Dict with json format")
    ]
    coalesce: Annotated[bool, Field(True, title="Coalesce")]
    max_instances: Annotated[int, Field(1, title="Max Instances")]
    misfire_grace_time: Annotated[int | None, Field(None, title="Misfire Grace Time")]

    @model_validator(mode="before")
    @classmethod
    def parse(cls, params: dict) -> dict:
        params["args"] = tuple(json.loads(params.get("args", "[]")))
        params["kwargs"] = dict(json.loads(params.get("kwargs", "{}")))
        params["coalesce"] = params["coalesce"] == "on"
        params.setdefault("trigger_params", TriggerParam())  # type: ignore
        return params

    def get_trigger(self):
        trigger_params = self.trigger_params.model_dump(exclude_none=True)
        if not trigger_params:
            return
        return self.trigger_params.get_trigger(self.trigger, self.next_run_time)


class NewJobParam(ModifyJobParam, JobInfo):  # type: ignore
    pass


class JobStoreInfo(BaseModel):
    alias: Annotated[str, Field(title="Alias")]
    type_: Annotated[
        str,
        Field(
            title="Store Type",
            json_schema_extra={"search_url": "/api/available-job-stores"},
        ),
    ]
    detail: Annotated[
        str,
        Field(
            title="Detail",
            description="""SqlAlchemy: string of url.
            MongoDB: {"host": uri, "database": "database", "collection": "collection" }.
            Redis: {"host": "host", "port": port, "db": db}""",
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def parse(cls, job_store: dict) -> dict:
        # from post data
        if "store" not in job_store:
            return job_store
        store = job_store.pop("store")
        type_ = store.__class__.__name__.removesuffix("JobStore")
        if type_ == "Memory":
            job_store["detail"] = ""
        elif type_ == "SQLAlchemy":
            job_store["detail"] = str(store.engine.url)
        elif type_ == "MongoDB":
            collection = store.collection
            database = collection._Collection__database
            client = database.client
            try:
                from pymongo.errors import InvalidOperation

                _Exception = InvalidOperation
            except ImportError:
                _Exception = Exception
            try:
                uri = ":".join(map(str, client.address))
            except _Exception:
                uri = ",".join(":".join(map(str, client.nodes)))
            job_store["detail"] = json.dumps(
                {
                    "host": uri,
                    "database": database._Database__name,
                    "collection": collection._Collection__name,
                }
            )
        elif type_ == "Redis":
            pool_kwargs = store.redis.connection_pool.connection_kwargs
            job_store["detail"] = json.dumps({k: pool_kwargs[k] for k in ("host", "port", "db")})
        else:
            raise ValueError(f"Invalid job store: {store}")
        return {"type_": type_, **job_store}

    def get_store(self):
        try:
            if self.type_ == "Memory":
                from apscheduler.jobstores.memory import MemoryJobStore

                return MemoryJobStore()
            elif self.type_ == "SQLAlchemy":
                from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

                return SQLAlchemyJobStore(url=self.detail)
            elif self.type_ == "MongoDB":
                from apscheduler.jobstores.mongodb import MongoDBJobStore

                kwargs = json.loads(self.detail)
                return MongoDBJobStore(**kwargs)
            elif self.type_ == "Redis":
                from apscheduler.jobstores.redis import RedisJobStore

                kwargs = json.loads(self.detail)
                return RedisJobStore(**kwargs)
            else:
                raise ValueError(f"Invalid job store: {self.type_}")
        except ImportError as e:
            raise HTTPException(status_code=400, detail=e)


class ExecutorInfo(BaseModel):
    alias: Annotated[str, Field(title="Alias")]
    type_: Annotated[Literal["Asyncio", "ThreadPool", "ProcessPool"], Field(title="Executor Type")]
    max_worker: Annotated[int | None, Field(None, title="Max Worker")]

    @model_validator(mode="before")
    @classmethod
    def parse(cls, executor_info: dict) -> dict:
        if "executor" not in executor_info:
            return executor_info
        executor = executor_info.pop("executor")
        if isinstance(executor, AsyncIOExecutor):
            executor_info["type_"] = "Asyncio"
        else:
            executor_info["type_"] = executor.__class__.__name__.removesuffix("Executor")
            executor_info["max_worker"] = executor._pool._max_workers
        return executor_info

    def get_executor(self):
        if self.type_ == "Asyncio":
            return AsyncIOExecutor()
        kwargs = {}
        if self.max_worker is not None:
            kwargs["max_workers"] = self.max_worker
        if self.type_ == "ThreadPool":
            return ThreadPoolExecutor(**kwargs)
        elif self.type_ == "ProcessPool":
            return ProcessPoolExecutor(**kwargs)
        else:
            raise ValueError(f"Executor type {self.type_} not supported")
