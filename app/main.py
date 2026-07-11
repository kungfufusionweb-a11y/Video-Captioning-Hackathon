import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from fireworks_client import FireworksClient
from pipeline import process_clip

MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", "3"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")


def load_tasks(path):
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    if not isinstance(tasks, list):
        raise ValueError("tasks.json must be a JSON array")
    return tasks


def write_results(path, results):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %d results to %s", len(results), path)


def _process_task(task, client):
    try:
        return process_clip(task, client)
    except Exception as e:
        logger.error("Unexpected error processing task %s: %s", task.get("task_id", "?"), e)
        return {
            "task_id": task.get("task_id", "unknown"),
            "captions": {s: f"[{s} caption unavailable]" for s in task.get("styles", [])},
        }


def main():
    tasks = load_tasks(INPUT_PATH)
    logger.info("Loaded %d tasks from %s", len(tasks), INPUT_PATH)

    client = FireworksClient()

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        future_to_idx = {
            executor.submit(_process_task, task, client): i
            for i, task in enumerate(tasks)
        }
        results = [None] * len(tasks)
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()

    write_results(OUTPUT_PATH, results)
    logger.info("Pipeline finished — exiting 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
