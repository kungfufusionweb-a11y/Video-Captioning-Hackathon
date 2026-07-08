import os
import time
import logging

import httpx

from prompts import STAGE1_PROMPT

logger = logging.getLogger(__name__)

GROQ_BASE = "https://api.groq.com/openai/v1"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL_VISION = os.environ.get(
    "GROQ_MODEL_VISION",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)
GROQ_MODEL_TEXT = os.environ.get(
    "GROQ_MODEL_TEXT",
    "llama-3.3-70b-versatile",
)
GROQ_WHISPER_MODEL = os.environ.get(
    "GROQ_WHISPER_MODEL",
    "whisper-large-v3",
)

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
REQUEST_TIMEOUT = 30.0
MAX_VISION_IMAGES = 5


class GroqClientError(Exception):
    pass


class GroqClient:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set — all API calls will fail")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _retry_with_backoff(self, func):
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                return func()
            except Exception as e:
                last_exc = e
                if attempt < MAX_RETRIES - 1:
                    wait = INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "Attempt %d/%d failed: %s. Retrying in %.1fs\u2026",
                        attempt + 1, MAX_RETRIES, e, wait,
                    )
                    time.sleep(wait)
        raise GroqClientError(
            f"All {MAX_RETRIES} attempts failed: {last_exc}"
        ) from last_exc

    def _chat_completion(self, messages, model, temperature=0.3, max_tokens=512):
        url = f"{GROQ_BASE}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        def do_call():
            with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
                resp = client.post(url, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

        return self._retry_with_backoff(do_call)

    def _select_frames(self, base64_frames, max_images=MAX_VISION_IMAGES):
        if len(base64_frames) <= max_images:
            return base64_frames
        step = len(base64_frames) / max_images
        indices = [min(int(i * step), len(base64_frames) - 1) for i in range(max_images)]
        return [base64_frames[i] for i in indices]

    def vision_describe(self, base64_frames, transcript=None):
        frames = self._select_frames(base64_frames)
        content = [{"type": "text", "text": STAGE1_PROMPT}]
        for frame in frames:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame}"},
            })
        if transcript:
            content.append({
                "type": "text",
                "text": f"Audio transcript: {transcript}",
            })

        messages = [{"role": "user", "content": content}]
        return self._chat_completion(messages, model=GROQ_MODEL_VISION)

    def style_rewrite(self, stage1_output, style_prompt_template):
        prompt = style_prompt_template.format(stage1_output=stage1_output)
        messages = [{"role": "user", "content": prompt}]
        return self._chat_completion(messages, model=GROQ_MODEL_TEXT)

    def transcribe(self, audio_bytes):
        url = f"{GROQ_BASE}/audio/transcriptions"

        def do_call():
            with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
                resp = client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                    data={"model": GROQ_WHISPER_MODEL},
                )
                resp.raise_for_status()
                return resp.json().get("text", "").strip()

        return self._retry_with_backoff(do_call)
