import json
import logging
import os
import sys

from fireworks_client_minimax import FireworksMinimaxClient
from pipeline_minimax import process_clip_minimax

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

INPUT_PATH = os.environ.get("MINIMAX_INPUT_PATH", "/input/tasks_minimax.json")
OUTPUT_PATH = os.environ.get("MINIMAX_OUTPUT_PATH", "/output/results_minimax.json")


def load_tasks(path):
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    if not isinstance(tasks, list):
        raise ValueError("tasks_minimax.json must be a JSON array")
    return tasks


def write_results(path, results):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("[MINIMAX] Wrote %d results to %s", len(results), path)


def main():
    tasks = load_tasks(INPUT_PATH)
    logger.info("[MINIMAX] Loaded %d tasks from %s", len(tasks), INPUT_PATH)

    client = FireworksMinimaxClient()
    results = []

    for task in tasks:
        try:
            result = process_clip_minimax(task, client)
            results.append(result)
        except Exception as e:
            logger.error("[MINIMAX] Unexpected error processing task %s: %s", task.get("task_id", "?"), e)
            fallback = {
                "task_id": task.get("task_id", "unknown"),
                "captions": {s: f"[{s} caption unavailable]" for s in task.get("styles", [])},
            }
            results.append(fallback)

    write_results(OUTPUT_PATH, results)
    logger.info("[MINIMAX] Pipeline finished — exiting 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
