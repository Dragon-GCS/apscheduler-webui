FROM python:3.10-slim

WORKDIR /app

COPY . /app/

RUN mkdir -p /app/logs

RUN pip install --no-cache-dir -e .

# Expose application port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]