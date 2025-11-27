# APScheduler-WebUI

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/downloads/release/python-380/) [![FastUI Version](https://img.shields.io/badge/FastUI-orange.svg)](https://fastui.fastapi.tiangolo.com/) [![APScheduler](https://img.shields.io/badge/APScheduler-3.x-blue.svg)](https://github.com/agronholm/apscheduler)

中文 | [English](README_en.md)

**APScheduler-WebUI** 是一个基于 [APScheduler](https://github.com/agronholm/apscheduler) 和 [FastUI](https://github.com/pydantic/FastUI) 构建的轻量级任务调度Web服务，旨在提供简洁直观的界面以管理和监控定时任务，同时利用 `APScheduler` 的强大功能实现灵活、高效的后台任务执行。

![screenshot](./pictures/screenshot.png)

## 目录

- [APScheduler-WebUI](#apscheduler-webui)
  - [目录](#目录)
  - [主要特性](#主要特性)
  - [快速开始](#快速开始)
    - [本地部署](#本地部署)
    - [Docker部署](#docker部署)
    - [任务管理](#任务管理)
    - [UV Script支持](#uv-script支持)
    - [Executor、JobStore管理](#executorjobstore管理)
    - [日志管理](#日志管理)
  - [许可证](#许可证)

## 主要特性

- 创建、编辑、暂停、启动、删除、重载任务
- 支持Cron、Interval、Date触发器
- 创建、删除Executor和JobStore
- 任务执行日志
- 查看脚本文件内容

## 快速开始

克隆本仓库

  ```bash
  git clone https://github.com/Dragon-GCS/apscheduler-webui
  ```

### 本地部署

1. 安装依赖

    推荐使用[uv](https://hellowac.github.io/uv-zh-cn/getting-started/installation/)

    > 如果你只需要使用sql/mongo/redis中的某一个作为持久化选项，可以只安装对应的依赖。默认安装全部依赖

    ```bash
    uv sync --extra all # or all = mongo+redis+sql
    ```

    或者使用`pip`

    ```bash
    python -m venv .venv # 创建虚拟环境（可选）
    pip install .[all]
    ```

2. 启动服务

    ```bash
    # use uv
    uv run uvicorn main:app
    # use python
    source .venv/bin/activate # 如果有虚拟环境
    uvicron main:app
    ```

### Docker部署

见[docker/DOCKER.md](docker/DOCKER.md)

### 任务管理

- 在你的脚本中使用apscheduler注册任务

```python
from src.scheduler import scheduler

scheduler.add_job(func, ...)
# or use decorator
@scheduler.scheduled_job(...)
def your_func(...):
    ...
```

- 使用WebUI（`/new`），通过字符串注册任务：`your_module:your_func`
  > 为了管理脚本，建议将脚本放在指定目录下（比如`scripts`）下并通过`scripts.your_module:your_func`注册任务

![job-detail](./pictures/job-detail.png)

### UV Script支持

如果环境中`uv`命令可用，通过将`func`设置为`uv_run`可以运行[uv脚本](https://docs.astral.sh/uv/guides/scripts/)，脚本内容通过`uv_script`字段传递，`args`和`kwargs`字段将作为位置参数和关键字参数传递给脚本

> [!NOTE]
> `uv_run`函数通过`subprocess`调用`uv run`命令来执行脚本，并将参数传递给脚本  
> `uv run {uv_script} {args0} {args1} ... {--key1=value1} {--key2=value2} ...`

### Executor、JobStore管理

- 在`src/config.py`中配置
- 通过WebUI(`/store`, `/executor`)管理（每次启动服务都会重置）

### 日志管理

![log-view](./pictures/log-view.png)

- WebUI(`/log/jobs`)可以解析并查看以特定格式记录的日志文件，日志分为两类：
  - `scheduler`日志：记录调度器所输出的日志信息
  - 任务日志：记录每个任务的输出日志信息
- WebUI使用[Loguru](https://github.com/Delgan/loguru)来记录和管理日志，并且修改了默认的日志格式以便于解析，因此脚本可以通过`from loguru import logger`来直接使用日志
  > WebUI通过设置环境变量`LOGURU_FORMAT`修改了`loguru`的默认格式，并在`src/log.py`中添加了sink将脚本日志输出到对应日期的文件中。  
- 日志保存在`logs/`目录下(可以在`config.py`中配置)，其中`scheduler.*log`保存`scheduler`日志，`job.YYYY-MM-DD.log`保存脚本输出的日志。

> [!IMPORTANT]
> 对于uv脚本，`subprocess`继承了环境变量，因此无需指定日志格式，但是如果希望在WebUI中查看日志，有以下两种方法：
>
> 1. 使用WebUI提供的server_log来记录日志
>
>    ```python
>    # 脚本的工作目录为项目的根目录，因此可以直接导入src模块
>    from src.log import server_log as logger
>    logger.info("This is a log message")
>    ```
>
> 2. 在脚本中手动添加sink将日志记录到文件中
>
>    ```python
>    from loguru import logger
>    from src.config import LOG_PATH
> 
>    server_log.add(
>      LOG_PATH / "jobs.{time:YYYY-MM-DD}.log", # 文件名可以自定义
>      rotation=datetime.time(0, 0),  # 如果文件名中包含{time}可以按天轮换
>    )
>    ```

## 许可证

本项目采用 MIT 许可证。
