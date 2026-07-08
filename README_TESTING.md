# Local Testing with Groq

## Prerequisites

1. Sign up at [console.groq.com](https://console.groq.com) and create an API key.
2. Export the key as an environment variable.

## Run with Groq

```bash
set CAPTION_PROVIDER=groq
set GROQ_API_KEY=gsk_your_key_here

# Run against the sample tasks
python app/main.py --input sample_tasks.json --output results.json
```

Run a single task by editing `sample_tasks.json` to keep only one entry, or implement a `--task-id` flag.

## Switch back to Fireworks

```bash
set CAPTION_PROVIDER=fireworks
set FIREWORKS_API_KEY=your_fireworks_key
python app/main.py --input sample_tasks.json --output results.json
```

Unset `CAPTION_PROVIDER` to fall back to the default (Fireworks):

```bash
set CAPTION_PROVIDER=
```

## Custom models (optional)

Override via environment variables:

| Variable | Default (Groq) | Notes |
|---|---|---|
| `GROQ_MODEL_VISION` | `meta-llama/llama-4-scout-17b-16e-instruct` | 5 images max per request; see caveats below |
| `GROQ_MODEL_TEXT` | `llama-3.3-70b-versatile` | |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3` | |

## Known caveats

- **Images per request**: Fireworks accepts all 8 frames in a single vision call. Groq caps at **5 images per request** (`MAX_VISION_IMAGES`). The Groq client automatically subsamples to 5 evenly-spaced frames before sending. This means slightly less temporal coverage — results may differ slightly between providers.
- **Rate limits**: Groq's free tier has model-specific RPM/IPD limits (e.g. ~30 RPM for Llama 3.3 70B). If you hit a rate limit, the built-in retry-with-backoff will handle transient errors, but sustained throughput may be lower than Fireworks.
- **Model availability**: Groq deprecates preview models frequently. If your vision call fails with a 404, check [console.groq.com/docs/models](https://console.groq.com/docs/models) for the current vision model ID and override via `GROQ_MODEL_VISION`.
- **Fireworks only at grading**: The Docker container will not include `groq_client.py` or `client_factory.py` unless you explicitly add them to the build. The default `CAPTION_PROVIDER` (unset) resolves to `fireworks`, matching graded behavior.
