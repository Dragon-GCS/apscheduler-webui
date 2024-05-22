from functools import partial
from typing import Literal

from apscheduler.events import (
    EVENT_EXECUTOR_ADDED,
    EVENT_EXECUTOR_REMOVED,
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_MODIFIED,
    EVENT_JOB_REMOVED,
    EVENT_JOB_SUBMITTED,
    EVENT_JOBSTORE_ADDED,
    EVENT_JOBSTORE_REMOVED,
    JobEvent,
    JobExecutionEvent,
    JobSubmissionEvent,
    SchedulerEvent,
)
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import SCHEDULER_CONFIG
from .log import server_log, logger

scheduler = AsyncIOScheduler(**SCHEDULER_CONFIG, logger=logger)


def listen_executor_or_jobstore_event(
    event: SchedulerEvent,
    mapper: dict,
    action: Literal["Add executor", "Remove executor", "Add job store", "Remove job store"],
):
    obj = f"{event.alias}[{mapper[event.alias]}]" if event.alias in mapper else event.alias
    server_log.debug(f"{action} {obj}")


def listen_job_event(
    event: JobEvent, action: Literal["Add job", "Remove job", "Modify job", "Submit job"]
):
    job: Job | None = scheduler.get_job(event.job_id)
    server_log.debug(f"{action}: {job.name if job else ''}[{event.job_id}]")


def listen_job_execution_event(
    event: JobExecutionEvent,
    action: Literal["Executed job", "Missed job", "Error job"],
):
    message = f"{action}: {event.job_id}[{scheduler.get_job(event.job_id)}]"
    if event.exception:
        server_log.opt(exception=event.exception).error(message)
    else:
        server_log.debug(message)


def listen_job_submission_event(event: JobSubmissionEvent):
    job: Job | None = scheduler.get_job(event.job_id)
    if not job:
        return
    server_log.debug(f"Submit job: {job.name}[{event.job_id}], next run at {job.next_run_time}")


listener = {
    EVENT_EXECUTOR_ADDED: partial(
        listen_executor_or_jobstore_event, mapper=scheduler._executors, action="Add executor"
    ),
    EVENT_EXECUTOR_REMOVED: partial(
        listen_executor_or_jobstore_event, mapper=scheduler._executors, action="Remove executor"
    ),
    EVENT_JOBSTORE_ADDED: partial(
        listen_executor_or_jobstore_event, mapper=scheduler._jobstores, action="Add job store"
    ),
    EVENT_JOBSTORE_REMOVED: partial(
        listen_executor_or_jobstore_event, mapper=scheduler._jobstores, action="Remove job store"
    ),
    EVENT_JOB_ADDED: partial(listen_job_event, action="Add job"),
    EVENT_JOB_REMOVED: partial(listen_job_event, action="Remove job"),
    EVENT_JOB_MODIFIED: partial(listen_job_event, action="Modify job"),
    EVENT_JOB_EXECUTED: partial(listen_job_execution_event, action="Executed job"),
    EVENT_JOB_ERROR: partial(listen_job_execution_event, action="Error job"),
    EVENT_JOB_MISSED: partial(listen_job_execution_event, action="Missed job"),
    EVENT_JOB_SUBMITTED: listen_job_submission_event,
}


scheduler.add_listener(lambda event: listener.get(event.code, lambda _: None)(event))
