# Tech & Features — Video Captioning Pipeline

## 1. Tech Stack

| Category | Technology | Evidence |
|---|---|---|
| **Language** | Python 3.11+ | `Dockerfile:1` — `FROM python:3.11-slim` |
| **Runtime** | Docker (linux/amd64) | `Dockerfile:1-18`; README build/push instructions |
| **HTTP client** | `httpx` 0.27+ | `app/requirements.txt:1`; used in `fireworks_client.py:76-77`, `pipeline.py:20-22` |
| **Video processing** | `ffmpeg` + `ffprobe` (via `subprocess`) | `Dockerfile:4` (apt-get install); `pipeline.py:29-41` (ffprobe), `pipeline.py:52-60` (ffmpeg frame extraction), `pipeline.py:76-84` (ffmpeg audio extraction) |
| **AI API** | Fireworks AI REST API | `fireworks_client.py:11` — base URL `https://api.fireworks.ai/inference/v1` |
| **Vision model** | Llama 3.2 90B Vision Instruct | `fireworks_client.py:16` — default model |
| **Text model** | Llama 3.1 8B Instruct | `fireworks_client.py:20` — default model |
| **Transcription** | Fireworks-hosted Whisper v3 | `fireworks_client.py:24` — `whisper-v3`; `fireworks_client.py:106-117` |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` | `main.py:60-64` — max_workers from `MAX_CONCURRENCY` env var (default 3) |
| **Database** | None | No database imports, connections, or files |
| **Frontend** | None | No HTML, JS, CSS, or framework files |
| **Cloud / third-party** | Fireworks AI (only external dependency) | No AWS, GCP, Azure, or other cloud SDKs |
| **Configuration** | Environment variables | `FIREWORKS_API_KEY`, `FIREWORKS_MODEL_VISION`, `FIREWORKS_MODEL_TEXT`, `FIREWORKS_WHISPER_MODEL`, `MAX_CONCURRENCY`, `INPUT_PATH`, `OUTPUT_PATH` |

### Audio/Video Processing Libraries
- **ffmpeg** — frame extraction (`pipeline.py:52-60`), audio extraction (`pipeline.py:76-84`)
- **ffprobe** — duration probing (`pipeline.py:29-41`)
- **No audio cleaning/noise reduction library exists anywhere in the codebase**

---

## 2. Audio Processing Pipeline (detailed)

### Flow
1. **Audio extraction** (`pipeline.py:73-93`):
   - ffmpeg command: `ffmpeg -i <video> -vn -acodec pcm_s16le -ar 16000 -ac 1 <output.wav> -y`
   - Extracts mono 16-bit PCM at 16 kHz sample rate
   - Written to `video_path` with `.wav` extension, read into memory, then deleted
   - **If extraction fails** (exception), returns `None` silently (`pipeline.py:88-90`)

2. **Transcription** (`fireworks_client.py:105-117`):
   - HTTP POST to `https://api.fireworks.ai/inference/v1/audio/transcriptions`
   - Multipart upload: `file` = extracted WAV bytes, `model` = `whisper-v3` (default, overridable via `FIREWORKS_WHISPER_MODEL`)
   - Response parsed: `resp.json().get("text", "").strip()`
   - Retry up to 3 times with exponential backoff
   - **If transcription fails** (exception), logged as warning, `transcript` remains `None` (`pipeline.py:114-117`)

3. **Transcript injection** (`fireworks_client.py:91-95`):
   - If transcript is non-None, appended as `"Audio transcript: {transcript}"` to the vision model's message content

### Noise Reduction / Cleaning
**There is no noise reduction, noise cancellation, or audio cleaning step anywhere in the code.** The raw ffmpeg extraction outputs PCM without any filtering. No library like `noisereduce`, `webrtcvad`, `sox`, or similar is used.

### Language Detection / Multilingual Handling
**None.** The pipeline has no language detection logic. All prompts instruct the model to output English captions. The transcript is passed raw with no language tag or normalization.

### Transcription Model
- **Model**: Fireworks-hosted OpenAI Whisper v3 (`accounts/fireworks/models/whisper-v3`)
- **API**: POST `https://api.fireworks.ai/inference/v1/audio/transcriptions`
- **Format**: Raw audio bytes, filename `audio.wav`, MIME `audio/wav`
- **No language parameter set** — Whisper will auto-detect

---

## 3. Features (Core)

| Feature | Implementation (File:Line) |
|---|---|
| Read task list from JSON | `main.py:23-28` — `load_tasks()` |
| Write results to JSON | `main.py:31-35` — `write_results()` |
| Download video from URL | `pipeline.py:18-25` — `_download_video()` |
| Probe video duration via ffprobe | `pipeline.py:28-41` — `_probe_duration()` |
| Extract 8 evenly-spaced frames as base64 JPEG | `pipeline.py:44-70` — `_extract_frames()` |
| Extract audio as 16-bit 16kHz mono WAV | `pipeline.py:73-93` — `_extract_audio()` |
| Stage 1: Neutral visual description via vision LLM | `pipeline.py:119-121` — `process_clip()` calling `client.vision_describe()` |
| Stage 2: Style-specific rewrites (4 styles) | `pipeline.py:123-135` — `process_clip()` iterating styles and calling `client.style_rewrite()` |
| Formal caption style | `prompts.py:12-18` — `STYLE_PROMPTS["formal"]` |
| Sarcastic caption style | `prompts.py:19-27` — `STYLE_PROMPTS["sarcastic"]` |
| Humorous-tech caption style | `prompts.py:28-36` — `STYLE_PROMPTS["humorous_tech"]` |
| Humorous-non-tech caption style | `prompts.py:37-45` — `STYLE_PROMPTS["humorous_non_tech"]` |
| Fallback captions on per-task failure | `main.py:70-76` — full task failure fallback |
| Fallback captions on per-style failure | `pipeline.py:125-135` — per-style error handling |
| Fallback captions on per-clip unrecoverable error | `pipeline.py:140-145` — top-level exception handler |
| Retry with exponential backoff (3 attempts) | `fireworks_client.py:48-64` — `_retry_with_backoff()` |
| CLI argument parsing (`--input` / `--output`) | `main.py:38-52` — argparse setup |
| Concurrent clip processing (thread pool) | `main.py:60-64` — `ThreadPoolExecutor` |
| Docker containerization | `Dockerfile:1-18` |
| Configurable model selection via env vars | `fireworks_client.py:13-25` |
| Temp directory cleanup after each clip | `pipeline.py:147-149` — `shutil.rmtree()` in `finally` |

---

## 4. AI/ML Features Specifically

### 4a. Stage 1 — Visual Description (Vision LLM)
- **Model**: `accounts/fireworks/models/llama-v3p2-90b-vision-instruct` (overridable via `FIREWORKS_MODEL_VISION`)
- **API**: `POST /chat/completions`
- **Input**:
  - 8 base64-encoded JPEG frames (sent as `image_url` with `data:image/jpeg;base64,...`)
  - Optional transcript text appended as `"Audio transcript: {transcript}"`
  - Prompt: `STAGE1_PROMPT` from `prompts.py:1-9`
- **Output**: 3–5 factual sentences (neutral description)
- **Parameters**: `temperature=0.3`, `max_tokens=512`
- **Pre-processing**: Frame extraction from video (ffmpeg), base64 encoding, transcript extraction
- **Post-processing**: `.strip()` on response text
- **Location**: `fireworks_client.py:84-98` — `vision_describe()`

### 4b. Stage 2 — Style Rewrites (Text LLM)
- **Model**: `accounts/fireworks/models/llama-v3p1-8b-instruct` (overridable via `FIREWORKS_MODEL_TEXT`)
- **API**: `POST /chat/completions`
- **Input**: `STYLE_PROMPTS[style].format(stage1_output=...)` from `prompts.py:12-45`
- **Output**: 1–2 sentence styled caption
- **Parameters**: `temperature=0.3`, `max_tokens=512`
- **Pre-processing**: String formatting with stage1 output
- **Post-processing**: `.strip()` on response text
- **Location**: `fireworks_client.py:100-103` — `style_rewrite()`

### 4c. Audio Transcription (Whisper)
- **Model**: `whisper-v3` (overridable via `FIREWORKS_WHISPER_MODEL`)
- **API**: `POST /audio/transcriptions` (multipart form)
- **Input**: Raw WAV bytes (16-bit, 16kHz, mono)
- **Output**: Transcribed text string
- **Pre-processing**: FFmpeg audio extraction (PCM s16le, 16kHz, mono)
- **Post-processing**: `.get("text", "").strip()`
- **Location**: `fireworks_client.py:105-117` — `transcribe()`

---

## 5. Known Bugs & Issues

### 5a. Frame Timestamp Calculation Bias (`pipeline.py:50`)
```python
t = (i + 0.5) * duration / NUM_FRAMES
```
This places frames at midpoints of `NUM_FRAMES` equal segments, which is reasonable but worth noting: with `NUM_FRAMES=8`, frames are at `t = (0.5/8, 1.5/8, ..., 7.5/8) * duration`. The first frame is at 6.25% into the clip and the last at 93.75%. First/last moments are never sampled.

### 5b. Literal `[optionally:` Text Sent to Model (`prompts.py:2-3`)
The prompt string contains the literal text `[optionally: plus a transcript of any spoken audio]` — this is a note-to-self from the prompt design phase, not conditional logic. The model receives this bracketed instruction as-is, regardless of whether a transcript was actually provided. This is confusing to the model when no transcript is present.

### 5c. No Input Validation (`main.py:23-28`, `pipeline.py:96-99`)
- `load_tasks()` only checks that the JSON root is a list — it does not validate that each item has `task_id`, `video_url`, or `styles` keys.
- Missing or malformed fields will crash with unhelpful `KeyError` stack traces (e.g., `pipeline.py:98` if `task["video_url"]` is missing).
- `styles` could be a non-list, a list of non-strings, or empty — none of these are checked.

### 5d. REQUEST_TIMEOUT Might Be Too Tight for Vision Calls (`fireworks_client.py:29`, `fireworks_client.py:66`)
`REQUEST_TIMEOUT = 30.0` seconds applies identically to all API calls. Vision model calls (large base64 payloads, heavy inference) can easily exceed 30 seconds, causing silent retries and eventual failure. The retry mechanism (`fireworks_client.py:48-64`) would retry, consuming up to ~90+ seconds total, but the cumulative effect across 8+ concurrent clips may degrade throughput or cause unexpected fallbacks.

### 5e. Style Rewrites Are Sequential Per Clip (Not Concurrent as Spec'd)
`pipeline.py:123-135` iterates over styles sequentially in a `for` loop. The `Prompt.md:34` spec requested concurrent style rewrites within a clip: *"Stage 2 — Style rewrite pass (four calls per clip, can run concurrently)"*. This is a missed optimization.

### 5f. Video Download Has No Content-Type Validation (`pipeline.py:18-25`)
`_download_video()` does not check the HTTP response `Content-Type` header. If the URL redirects to an HTML page or non-video content, it will write whatever bytes were returned and proceed to ffprobe/ffmpeg, which will fail with an opaque error.

### 5g. `.ipynb` Empty File in Project Root
The file `.ipynb` is an empty 0-byte file at the project root with no extension or content. It appears to be an accidental artifact.

### 5h. All Captions Forced to English
Despite the `STAGE1_PROMPT` asking for a "neutral, objective description" and style rewrite prompts targeting English output, there is no enforcement mechanism. If the input video contains non-English speech, the Whisper transcription may produce non-English text, and the downstream models may partially follow that language.

### 5i. No HTTP Timeout on Video Download (`pipeline.py:20-22`)
While `httpx.Client(timeout=httpx.Timeout(120.0))` is set, there is no **connect timeout** and no **read timeout** differentiation. If the server accepts the connection but never sends data, this will hang for up to 120 seconds.

### 5j. No Path Traversal Protection (`main.py:23-34`)
`load_tasks()` and `write_results()` use user-provided file paths directly. In a containerized environment this is low risk, but `--input` / `--output` CLI args are not sanitized.

---

## 6. Architecture Overview

```
                     ┌──────────────────────┐
                     │   /input/tasks.json   │
                     │  (CLI arg --input)    │
                     └──────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      main.py          │
                    │  ThreadPoolExecutor   │
                    │  (max 3 concurrent)   │
                    └──────────┬───────────┘
                               │ per task
                    ┌──────────▼───────────┐
                    │    pipeline.py        │
                    │   process_clip()      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Download     │  │ Extract      │  │ Extract      │
     │ video from   │  │ 8 frames     │  │ audio (WAV   │
     │ URL (httpx)  │  │ (ffmpeg)     │  │ 16kHz mono)  │
     └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
            │                 │                  │
            ▼                 ▼                  ▼
            └─────────────────┬──────────────────┘
                              │
                    ┌─────────▼────────┐
                    │  Fireworks AI    │
                    │  Whisper v3      │
                    │  (transcription) │
                    └─────────┬────────┘
                              │ transcript (optional)
                    ┌─────────▼────────┐
                    │  Fireworks AI    │
                    │  Llama 3.2 90B   │
                    │  Vision (Stage1) │
                    └─────────┬────────┘
                              │ neutral description
                    ┌─────────▼────────┐
                    │  Fireworks AI    │
                    │  Llama 3.1 8B    │
                    │  Text (Stage2)   │
                    │  × 4 styles      │
                    └─────────┬────────┘
                              │ styled captions
                    ┌─────────▼────────┐
                    │   merge result   │
                    │   per task       │
                    └──────────────────┘

                    ┌──────────────────────┐
                    │  /output/results.json │
                    │  (CLI arg --output)   │
                    └──────────────────────┘
```

- **Style**: Batch CLI pipeline, no web server, no real-time streaming
- **Concurrency**: Thread pool across clips; sequential within a clip
- **Temp files**: Per-clip temp directory created via `tempfile.mkdtemp()`, cleaned up in `finally`
- **Error isolation**: Each clip is independently processed; one failure does not block others
- **Logging**: All output to stderr; no log files written

---

## 7. Gaps & Extension Opportunities

### 7a. Features Not Yet Implemented
- **Concurrent style rewrites within a clip** — Stage 2 styles are processed sequentially but could be parallelized with `ThreadPoolExecutor` or `asyncio`
- **Audio noise reduction** — No audio cleaning step before Whisper transcription
- **Language detection** — No detection of video audio language; no language-aware prompting
- **Video format validation** — No check that downloaded content is a valid video before processing
- **Robustness metrics / quality scoring** — No automated assessment of caption quality
- **Progress/resume support** — No checkpointing for long batch runs; crash restarts from scratch
- **Health check endpoint** — No HTTP server; container has no health check for orchestration
- **Unit/integration tests** — No test files exist
- **CI/CD pipeline** — No GitHub Actions or similar
- **Input schema validation** — No Pydantic model or JSON schema validation for `tasks.json`
- **Rate limiting awareness** — No tracking of Fireworks API rate limits / token usage

### 7b. Technical Improvements for Bugs (from Section 5)
- Fix `[optionally:` text in prompt to be conditionally included only when transcript is present
- Add input validation with descriptive error messages for missing/wrong fields
- Increase `REQUEST_TIMEOUT` for vision API calls or make it configurable per call type
- Parallelize style rewrites within each clip
- Add `Content-Type` header check after video download
- Add read timeout and connect timeout differentiation for video downloads
- Remove the empty `.ipynb` file
- Add language parameter to Whisper transcription request for non-English speech
- Validate `styles` list contents against known keys before processing

---

## 8. File Structure Map

```
E:\Video Captioning Hackathon\
├── .git/                          # Git repository data
├── .ipynb                         # Empty 0-byte file, likely accidental artifact
├── app/                           # Application source code
│   ├── __pycache__/               # Python bytecode cache (generated)
│   ├── fireworks_client.py        # Fireworks AI REST API wrapper with retry/backoff
│   ├── main.py                    # Entry point: argument parsing, task loading, orchestration, output
│   ├── pipeline.py                # Core pipeline: download, frame/audio extraction, Stage 1 & 2 processing
│   ├── prompts.py                 # All prompt templates as named constants
│   └── requirements.txt           # Python dependencies (httpx only)
├── Dockerfile                     # Container build: python:3.11-slim + ffmpeg + app code
├── Prompt.md                      # Original prompt spec (requirements document)
├── Prompts.md                     # Exact prompt wording + sample URLs (supplementary spec)
├── README.md                      # Usage instructions, build/run commands, known limitations
├── sample_tasks.json              # 3 example tasks for local testing
├── Tree.md                        # Analysis/documentation task spec (this file's generator)
└── tech&features.md               # ← This file (generated analysis)
```

### Structural Inconsistencies
1. **Mixed naming conventions**: `Prompts.md` (capital P) vs `Prompt.md` (capital P, singular) — inconsistent and ambiguous purpose overlap. Two files with near-identical names in the root.
2. **Orphan artifact**: `.ipynb` is an empty 0-byte file with no known purpose — likely accidentally created.
3. **No tests directory**: Even a minimal project would benefit from a `tests/` directory.
4. **`__pycache__/` committed?** If the `.gitignore` does not exclude `__pycache__/`, the compiled `.pyc` files may be tracked.

---

## 9. Component Inventory

This project has no React components. It is a pure Python backend application with no frontend framework.

For completeness, the four Python modules are inventoried below:

| Module | File Path | Purpose | Lines | Notes |
|---|---|---|---|---|
| `main` | `app/main.py` | CLI entry point: argument parsing, task loading, concurrent dispatch via ThreadPoolExecutor, results output | 84 | Under 300 lines — no split needed |
| `pipeline` | `app/pipeline.py` | Core logic: video download, ffprobe duration probing, ffmpeg frame/audio extraction, Stage 1 vision call, Stage 2 style iterations | 150 | Under 300 lines — no split needed |
| `fireworks_client` | `app/fireworks_client.py` | Thin wrapper around Fireworks AI REST API: vision chat, text chat, audio transcription, retry with exponential backoff | 119 | Under 300 lines — no split needed |
| `prompts` | `app/prompts.py` | Named string constants for all prompt templates (Stage 1 neutral + 4 style prompts) | 46 | Under 300 lines — no split needed |

### Refactoring Notes
- **No prop drilling** — not applicable (no frontend/React components)
- **No concern-mixing** — modules are reasonably separated: I/O (pipeline), API calls (fireworks_client), prompts (prompts), orchestration (main). However, `pipeline.py` mixes:
  - Video download (HTTP I/O) — `_download_video()`
  - Frame/audio extraction (subprocess/ffmpeg) — `_extract_frames()`, `_extract_audio()`
  - Business logic orchestration — `process_clip()`
  This is acceptable at the current scale but could be split if the project grows.

### Candidates for Future Refactoring
- `pipeline.py` `process_clip()` (150 lines) — the longest single function; has nested error handling for transcription, Stage 1, and Stage 2. Could split into smaller helper methods.
- `main.py` `main()` — orchestrates loading, dispatching, and writing; could be split into `dispatch_tasks()` and `aggregate_results()` for testability.
