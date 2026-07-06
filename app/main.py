import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from fireworks_client import FireworksClient
from pipeline import process_clip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

INPUT_PATH = os.environ.get("INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "/output/results.json")
MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", "3"))


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


def main():
    parser = argparse.ArgumentParser(
        description="Video captioning pipeline — Track 2: AMD Hackathon"
    )
    parser.add_argument(
        "--input", "-i",
        default=INPUT_PATH,
        help="Path to input tasks.json (default: %(default)s)",
    )
    parser.add_argument(
        "--output", "-o",
        default=OUTPUT_PATH,
        help="Path to write output results.json (default: %(default)s)",
    )
    args = parser.parse_args()

    tasks = load_tasks(args.input)
    logger.info("Loaded %d tasks from %s", len(tasks), args.input)

    client = FireworksClient()
    results = [None] * len(tasks)

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        future_map = {
            executor.submit(process_clip, task, client): idx
            for idx, task in enumerate(tasks)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.error("Unexpected error processing task index %d: %s", idx, e)
                task = tasks[idx]
                fallback = {
                    "task_id": task["task_id"],
                    "captions": {s: f"[{s} caption unavailable]" for s in task["styles"]},
                }
                results[idx] = fallback

    write_results(args.output, results)
    logger.info("Pipeline finished — exiting 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
