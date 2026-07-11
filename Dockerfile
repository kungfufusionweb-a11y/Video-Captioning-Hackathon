FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV INPUT_PATH=/input/tasks.json
ENV OUTPUT_PATH=/output/results.json
ENV MAX_CONCURRENCY=3

ENTRYPOINT ["python", "main.py"]
