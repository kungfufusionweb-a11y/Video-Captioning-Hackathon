# AMD Hackathon — Track 2: Video Captioning

Docker-based video captioning pipeline that reads a task list, generates four styled
captions per video clip (formal, sarcastic, humorous_tech, humorous_non_tech) using
Fireworks AI models, and writes results to a fixed JSON path.

## Prerequisites

- Python 3.11+ (for local testing)
- Docker (for containerized deployment)
- A [Fireworks AI](https://fireworks.ai) API key

## Setup

1. Set your API key:
   ```bash
   export FIREWORKS_API_KEY="your-api-key-here"
   ```

2. (Optional) Override model names via environment variables:
   - `FIREWORKS_MODEL_VISION` (default: `accounts/fireworks/models/llama-v3p2-90b-vision-instruct`)
   - `FIREWORKS_MODEL_TEXT` (default: `accounts/fireworks/models/llama-v3p1-8b-instruct`)
   - `FIREWORKS_WHISPER_MODEL` (default: `whisper-v3`)
   - `MAX_CONCURRENCY` (default: `3`)

## Local testing (outside Docker)

```bash
cd app
pip install -r requirements.txt
python main.py --input ../sample_tasks.json --output ../out.json
```

## Build Docker image

```bash
docker buildx build --platform linux/amd64 --tag video-captioning:latest .
```

## Run Docker container

```bash
docker run --rm \
  -e FIREWORKS_API_KEY="$FIREWORKS_API_KEY" \
  -v "$(pwd)/sample_tasks.json:/input/tasks.json" \
  -v "$(pwd)/output:/output" \
  video-captioning:latest
```

## Push to registry (for submission)

```bash
docker buildx build --platform linux/amd64 --tag <your-registry>/<name>:latest --push .
```

## Known limitations

- Audio transcription is best-effort; if extraction or transcription fails, the Stage 1
  vision model runs without a transcript.
- Videos that fail to download or process after retries get generic fallback captions
  rather than being dropped.
- The pipeline runs model calls sequentially per clip but processes clips in parallel
  (bounded by `MAX_CONCURRENCY`).
- All caption text is in English regardless of clip content.
