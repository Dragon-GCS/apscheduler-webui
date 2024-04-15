# apscheduler-webui

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/downloads/release/python-380/) [![FastUI Version](https://img.shields.io/badge/FastUI-orange.svg)](https://fastui.fastapi.tiangolo.com/) [![Apscheduler](https://img.shields.io/badge/APScheduler-3.x-blue.svg)](https://github.com/agronholm/apscheduler)

**apscheduler-webui** is a lightweight task scheduling web service built upon [APScheduler](https://github.com/agronholm/apscheduler) and [FastUI](https://fastui.fastapi.tiangolo.com/), designed to provide a concise and intuitive interface for managing and monitoring scheduled tasks, while leveraging the powerful capabilities of `APScheduler` to execute background tasks in a flexible and efficient manner.

![screenshot](./pictures/screenshot.png)

[中文](README.md) | English

## Table of Contents

- [apscheduler-webui](#apscheduler-webui)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Quick Start](#quick-start)
    - [Mange jobs](#mange-jobs)
    - [Manger Executor and JobStore](#manger-executor-and-jobstore)
    - [View logs](#view-logs)
  - [License](#license)

## Features

- Create, modify, pause, resume and remove jobs
- Support for Cron, Interval, and Date triggers
- Create and delete Executors and JobStores
- Support for view your logs

## Quick Start

1. Clone the repository

    ```bash
    git clone https://github.com/Dragon-GCS/apscheduler-webui
    ```

2. Install dependencies

    Use [start](https://github.com/Dragon-GCS/start)(Recommended)

    ```bash
    start init  # Create virtual environment(Optional)
    start install
    ```

    Or use `pip`

    ```bash
    python -m venv .venv # Create virtual environment(Optional)
    pip install .
    ```

3. Start the server

    ```bash
    uvicron main:app --port <port>
    ```

### Mange jobs

- Register jobs on your scripts

```python
from src.scheduler import scheduler

scheduler.add_job(func, ...)
# or use decorator
@scheduler.scheduled_job(...)
def your_func(...):
    ...
```

- Use webui（`/new`），add new job with string: `your_module:your_func`
  > For manage jobs, you can put your jobs under some folder(e.g. `scripts`), and use `scripts.your_module:your_func` to add jobs.

### Manger Executor and JobStore

- Config in`src/config.py`

  ```python
  SCHEDULER_CONFIG = {
    "executors": {"default": AsyncIOExecutor()},
    "jobstores": {},
  }
  ```

- Use webui(`/store`, `/executor`)
  > Not recommended because it will be reset when you restart the server

### View logs

- You can use `loguru.logger` to record logs。
- Webui(`/log/jobs`) can check your logs which is start with `jobs` and saved in specified folder (default is `logs`, can be changed in `config.py`)

## License

This project is licensed under the MIT License.
