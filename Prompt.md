Build a Docker-based video captioning pipeline for a hackathon submission. Follow this spec exactly.

## Goal
A container that reads a task list, generates 4 styled captions per video clip using
Fireworks AI models, and writes results to a fixed JSON path, then exits 0.

## I/O contract
- On startup, read /input/tasks.json, formatted as:
  [
    {"task_id": "v1", "video_url": "https://...clip1.mp4", "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]}
  ]
- Before exiting, write /output/results.json, formatted as:
  [
    {"task_id": "v1", "captions": {"formal": "...", "sarcastic": "...", "humorous_tech": "...", "humorous_non_tech": "..."}}
  ]
- Exit code 0 on success. Non-zero if any unrecoverable error occurs.
- Every task_id in the input must appear in the output with all requested styles filled in,
  even if a fallback/generic caption has to be used — never drop a task or a style silently.
- Total runtime for all tasks combined must stay under 10 minutes.
- Must be ready to start processing within 60 seconds of container start.

## Pipeline design (two-stage per clip)
Stage 1 — Neutral grounding pass (once per clip):
  1. Download the video from video_url to a temp path.
  2. Use ffmpeg to extract 6-10 evenly spaced frames across the clip duration
     (probe duration first with ffprobe, then compute timestamps).
  3. Optionally extract audio and transcribe with a Fireworks-hosted Whisper model
     if the clip is likely to contain speech; skip gracefully if extraction/transcription fails.
  4. Send the frames (base64 images) [+ transcript if available] to a Fireworks vision-language
     model with a neutral, factual description prompt (I'll supply exact prompt text separately —
     leave a clearly marked constant/config block for prompts so I can edit wording without touching logic).
  5. Store the single neutral description as an intermediate result.

Stage 2 — Style rewrite pass (four calls per clip, can run concurrently):
  For each requested style, call a Fireworks text (or same vision) model with a style-specific
  system/user prompt that takes the Stage 1 description as input and returns ONLY the caption text.
  Store prompt templates as named constants/config (formal, sarcastic, humorous_tech, humorous_non_tech)
  so I can edit the wording later without touching code logic.

## Requirements for the implementation
- Language: Python 3.11+.
- Use `requests` or `httpx` for Fireworks API calls (REST), configurable via env var FIREWORKS_API_KEY
  and FIREWORKS_MODEL_VISION / FIREWORKS_MODEL_TEXT (with sensible defaults, but overridable).
- Use ffmpeg/ffprobe (installed via apt in the Dockerfile) for frame/audio extraction — do not use
  a heavy Python video library if avoidable.
- Concurrency: process multiple clips and multiple styles within a clip in parallel
  (asyncio or thread pool), bounded by a MAX_CONCURRENCY env var, to stay inside the 10-minute
  and 30-second-per-request budgets.
- Timeouts: every external HTTP call (download, Fireworks API) must have an explicit timeout
  and a retry with backoff (max 2-3 retries) before falling back.
- Fallback behavior: if a clip fails to download, extract, or get captioned after retries,
  still emit an entry for that task_id with best-effort or clearly generic captions per style
  rather than omitting it — a missing style scores zero, but a wrong/generic one may still score partial credit.
- Logging: log progress to stdout/stderr (task started, stage completed, errors) for debugging,
  but do NOT write any log file to /output — only results.json belongs there.
- No hardcoded answers, no caching keyed off specific input URLs/hashes — every input must be
  processed live through the model calls (the eval set is hidden and unseen clips must generalize).
- Clean up temp video/frame files after each task to control disk usage.
- All caption text must be in English regardless of clip content.
- Code structure:
    /app
      main.py           # orchestrator: read tasks, dispatch, write results
      pipeline.py        # download, frame extraction, stage1, stage2 logic
      prompts.py         # all prompt templates as named constants
      fireworks_client.py # thin wrapper around Fireworks REST calls with retry/timeout
      requirements.txt
      Dockerfile
- Provide a local test entrypoint (e.g. `python main.py --input sample_tasks.json --output out.json`)
  so I can test outside Docker with the three example clip URLs before building the image.

## Dockerfile requirements
- Base image: python:3.11-slim (or similar minimal image).
- Install ffmpeg via apt-get.
- Copy app code, install requirements.txt.
- ENTRYPOINT should run main.py reading from /input/tasks.json and writing to /output/results.json
  with no required arguments (env vars only for API keys/model names).
- Must be buildable for linux/amd64 explicitly — remind me in the README to build with:
  docker buildx build --platform linux/amd64 --tag <name>:latest --push .
- Keep final image size well under 10GB — avoid unnecessary layers/caches, use --no-cache-dir
  for pip installs, clean apt cache after install.

## Deliverables
1. Full project source tree as described above.
2. A README with: how to set FIREWORKS_API_KEY, how to run locally against sample_tasks.json,
   how to build and push the amd64 image, and known limitations.
3. A sample_tasks.json using the three example clip URLs I'll provide, for local testing.

Ask me for the exact prompt wording for prompts.py before finalizing that file — I have specific
text for the neutral description prompt and the four style prompts.
