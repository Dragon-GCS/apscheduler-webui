# Docker Deployment Guide

This document provides instructions for deploying APScheduler WebUI using Docker.

## Using docker run

From pre-built image

```bash
docker pull drag0nz/apscheduler-webui:latest
```

Or build by yourself

```bash
# Execute in the project root directory
docker build -t drag0nz/apscheduler-webui -f docker/Dockerfile .
```

If you want to change some config, export config file to current directory

```bash
docker run -i --rm drag0nz/apscheduler-webui:latest cat /app/src/config.py > config.py
```

Run the container

```bash
docker run \
  -d \
  --name apscheduler-webui \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v config.py:/app/src/config.py \
  drag0nz/apscheduler-webui:latest
```

## Using Docker Compose

```bash
# Starting the Service
# Execute in the project root directory
docker-compose -f docker/docker-compose.yml up -d
# Stopping the Service
docker-compose -f docker/docker-compose.yml down
# Viewing Logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Configuration Instructions

### Port Configuration

By default, the application runs on port 8000 inside the container and is mapped to port 8000 on the host. If you need to change the host port, modify the port mapping in the `docker-compose.yml` file:

```yaml
ports:
  - "custom_port:8000"
```

or in the `docker run` command:

```bash
docker run ... -p <custom_port>:8000 ... apscheduler-webui
```

### Data Persistence

The application's log files are persisted to the `./logs` directory on the host. If using SQLite as job storage, you can persist the database file by uncommenting the relevant lines in `docker-compose.yml`.

### Using MongoDB or Redis as Job Storage

If you need to use MongoDB or Redis as job storage, uncomment the relevant service configurations in the `docker-compose.yml` file. Then, you need to modify the application's configuration to use these services.

#### MongoDB Configuration Example

Uncomment the MongoDB service configuration in `docker-compose.yml` and ensure the application configuration includes MongoDB as job storage:

```python
# Modify SCHEDULER_CONFIG in src/config.py
from pymongo import MongoClient
from apscheduler.jobstores.mongodb import MongoDBJobStore

client = MongoClient('mongodb://admin:password@mongodb:27017/')

SCHEDULER_CONFIG = {
    "executors": {"default": AsyncIOExecutor()},
    "jobstores": {
        "default": MongoDBJobStore(client=client)
    },
}
```

#### Redis Configuration Example

Uncomment the Redis service configuration in `docker-compose.yml` and ensure the application configuration includes Redis as job storage:

```python
# Modify SCHEDULER_CONFIG in src/config.py
from apscheduler.jobstores.redis import RedisJobStore

SCHEDULER_CONFIG = {
    "executors": {"default": AsyncIOExecutor()},
    "jobstores": {
        "default": RedisJobStore(host='redis', port=6379)
    },
}
```

## Accessing the Application

After deployment, you can access the application via a browser:

```url
http://localhost:8000
```

## Environment Variables

You can configure the application's behavior through environment variables. Add the required environment variables in the `environment` section of the `docker-compose.yml` file:

```yaml
environment:
  - TZ=Asia/Shanghai
  # Add other environment variables
```
