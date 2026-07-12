# AMD Hackathon — Track 2: Video Captioning

Docker-based video captioning pipeline that reads a task list, generates four styled
captions per video clip (formal, sarcastic, humorous_tech, humorous_non_tech) using
Fireworks AI models, and writes results to a fixed JSON path.

## How it works

The container reads `/input/tasks.json`, processes each video clip through a
vision-capable Fireworks AI model to extract factual scene content, then generates
all four required caption styles from that grounded description. Clips are processed
in parallel (bounded by `MAX_CONCURRENCY`), with each clip's model calls run
sequentially. Results are written to `/output/results.json` in the required schema,
with one entry per task ID.

## AMD / Fireworks usage

- Caption generation runs entirely through the Fireworks AI API (vision + text models).
- The Fireworks API key is required at runtime — see "Run Docker container" below.

## Prerequisites

- Python 3.11+ (for local testing)
- Docker (for containerized deployment)
- A [Fireworks AI](https://fireworks.ai) API key

## Pull image

```bash
docker pull fusiondeve/video-captioning-agent:latest
```

## Run Docker container

```bash
docker run --rm \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  fusiondeve/video-captioning-agent:latest
echo "Exit code: $?"
```

The container reads task definitions from `/input/tasks.json` and writes results to
`/output/results.json`. Exit code `0` indicates a clean run.

## Output

`output/results.json` — a JSON array with one object per task, containing `task_id`
and a `captions` object with `formal`, `sarcastic`, `humorous_tech`, and
`humorous_non_tech` keys.

## Main code path

- `main.py` (or your actual entrypoint file) — orchestrates task loading, per-clip
  processing, and result writing.
- Entrypoint runs automatically on container start; no manual setup required.