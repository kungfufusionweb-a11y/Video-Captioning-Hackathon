import os
import time
import logging

import httpx

from prompts import STAGE1_PROMPT

logger = logging.getLogger(__name__)

FIREWORKS_BASE = "https://api.fireworks.ai/inference/v1"

FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
FIREWORKS_MODEL_VISION = os.environ.get(
    "FIREWORKS_MODEL_VISION",
    "accounts/fireworks/models/kimi-k2p6",
)
FIREWORKS_MODEL_TEXT = os.environ.get(
    "FIREWORKS_MODEL_TEXT",
    "accounts/fireworks/models/gpt-oss-120b",
)
FIREWORKS_WHISPER_MODEL = os.environ.get(
    "FIREWORKS_WHISPER_MODEL",
    "whisper-v3",
)

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
REQUEST_TIMEOUT = 30.0


class FireworksClientError(Exception):
    pass


class FireworksClient:
    def __init__(self):
        self.api_key = FIREWORKS_API_KEY
        if not self.api_key:
            logger.warning("FIREWORKS_API_KEY is not set — all API calls will fail")

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
                        "Attempt %d/%d failed: %s. Retrying in %.1fs…",
                        attempt + 1, MAX_RETRIES, e, wait,
                    )
                    time.sleep(wait)
        raise FireworksClientError(
            f"All {MAX_RETRIES} attempts failed: {last_exc}"
        ) from last_exc

    def _chat_completion(self, messages, model, temperature=0.3, max_tokens=512, timeout=None, **payload_extras):
        url = f"{FIREWORKS_BASE}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        payload.update(payload_extras)
        effective_timeout = timeout if timeout is not None else REQUEST_TIMEOUT

        def do_call():
            with httpx.Client(timeout=httpx.Timeout(effective_timeout)) as client:
                resp = client.post(url, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                try:
                    message = data["choices"][0]["message"]
                    content = message.get("content")
                    if content is None:
                        logger.error("No 'content' in message. Full response: %s", data)
                        raise FireworksClientError(f"No content in response message: {message}")
                    return content.strip()
                except (KeyError, IndexError) as e:
                    logger.error("Malformed response structure: %s. Full response: %s", e, data)
                    raise FireworksClientError(f"Malformed response: {e}") from e

        return self._retry_with_backoff(do_call)

    def vision_describe(self, base64_frames, transcript=None):
        content = [{"type": "text", "text": STAGE1_PROMPT}]
        for frame in base64_frames:
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
        return self._chat_completion(
            messages, model=FIREWORKS_MODEL_VISION,
            thinking={"type": "disabled"},
            timeout=60.0,
        )

    def style_rewrite(self, stage1_output, style_prompt_template):
        prompt = style_prompt_template.format(stage1_output=stage1_output)
        messages = [{"role": "user", "content": prompt}]
        return self._chat_completion(messages, model=FIREWORKS_MODEL_TEXT)

    def transcribe(self, audio_bytes):
        url = f"{FIREWORKS_BASE}/audio/transcriptions"

        def do_call():
            with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
                resp = client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                    data={"model": FIREWORKS_WHISPER_MODEL},
                )
                resp.raise_for_status()
                return resp.json().get("text", "").strip()

        return self._retry_with_backoff(do_call)
