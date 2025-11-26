FROM ghcr.io/astral-sh/uv:python3.10-trixie-slim

WORKDIR /app

COPY . /app/

RUN mkdir -p /app/logs

RUN uv sync --all-extras

# Expose application port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]