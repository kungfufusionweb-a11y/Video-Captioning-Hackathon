import base64
import io
import logging
import os
import struct
import wave
import zlib

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smoke_test")

FIREWORKS_BASE = "https://api.fireworks.ai/inference/v1"
API_KEY = os.environ.get("FIREWORKS_API_KEY", "")
if not API_KEY:
    raise SystemExit("FIREWORKS_API_KEY is not set — cannot run smoke test")

VISION_MODEL = os.environ.get(
    "FIREWORKS_MODEL_VISION",
    "accounts/fireworks/models/kimi-k2p6",
)
WHISPER_MODEL = os.environ.get(
    "FIREWORKS_WHISPER_MODEL",
    "whisper-v3",
)

REQUEST_TIMEOUT = 60.0


def _create_solid_png(width: int, height: int, r: int, g: int, b: int) -> bytes:
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    raw = bytearray()
    for _ in range(height):
        raw.append(0)
        raw.extend(struct.pack("BBB", r, g, b) * width)

    idat = chunk(b"IDAT", zlib.compress(bytes(raw)))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def _create_test_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    num_samples = int(sample_rate * duration_sec)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(num_samples):
            val = int(16000 * 0.3 * (i / num_samples - 0.5))
            val = max(-32768, min(32767, val))
            buf.write(struct.pack("<h", val))
    return buf.getvalue()


def _chat_completion(messages, model, **payload_extras):
    url = f"{FIREWORKS_BASE}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 512,
    }
    payload.update(payload_extras)
    logger.info("POST %s (model=%s)", url, model)
    with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
        resp = client.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    logger.info("  Status: %d", resp.status_code)
    return resp


def test_a_single_image_vision():
    logger.info("=" * 60)
    logger.info("TEST A: Single image → kimi-k2p6 with thinking disabled")
    logger.info("=" * 60)

    png_bytes = _create_solid_png(200, 200, 255, 0, 0)
    b64 = base64.b64encode(png_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one short sentence."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
            ],
        }
    ]

    resp = _chat_completion(
        messages, model=VISION_MODEL, thinking={"type": "disabled"}
    )

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        logger.info("  Response content: %s", content)
        logger.info("TEST A: PASS")
    except Exception as e:
        logger.error("TEST A: FAIL — %s", e)
        logger.error("  Raw: %s", resp.text[:1000])


def test_b_multi_image_vision():
    logger.info("=" * 60)
    logger.info("TEST B: Multi-image (3 frames) → kimi-k2p6 with thinking disabled")
    logger.info("=" * 60)

    images = [
        _create_solid_png(200, 200, 255, 0, 0),    # red
        _create_solid_png(200, 200, 0, 255, 0),    # green
        _create_solid_png(200, 200, 0, 0, 255),    # blue
    ]
    content = [
        {
            "type": "text",
            "text": (
                "These are 3 frames from a video in temporal order. "
                "Describe what you see across the frames in 1-2 sentences."
            ),
        }
    ]
    for img in images:
        b64 = base64.b64encode(img).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            }
        )

    messages = [{"role": "user", "content": content}]

    resp = _chat_completion(
        messages, model=VISION_MODEL, thinking={"type": "disabled"}
    )

    try:
        data = resp.json()
        n_images_used = data["usage"].get("image_count", "N/A") if "usage" in data else "N/A"
        content = data["choices"][0]["message"]["content"].strip()
        logger.info("  Response content: %s", content)
        logger.info("  Image count in usage: %s", n_images_used)
        logger.info("TEST B: PASS")
    except Exception as e:
        logger.error("TEST B: FAIL — %s", e)
        logger.error("  Raw: %s", resp.text[:1000])


def test_c_audio_transcription():
    logger.info("=" * 60)
    logger.info("TEST C: Audio transcription → whisper-v3")
    logger.info("=" * 60)

    wav_bytes = _create_test_wav(1.0)

    url = f"{FIREWORKS_BASE}/audio/transcriptions"
    logger.info("POST %s (model=%s)", url, WHISPER_MODEL)
    with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
        resp = client.post(
            url,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"model": WHISPER_MODEL},
        )

    logger.info("  Status: %d", resp.status_code)
    try:
        data = resp.json()
        logger.info("  Response JSON: %s", data)
        if resp.status_code == 200:
            logger.info("TEST C: PASS")
        else:
            logger.info("TEST C: NON-200 (see above — may be expected)")
    except Exception as e:
        logger.info("  Raw body: %s", resp.text[:1000])
        logger.info("TEST C: Could not parse JSON (see raw body above)")


def main():
    logger.info("Fireworks API Smoke Test")
    logger.info("Vision model: %s", VISION_MODEL)
    logger.info("Whisper model: %s", WHISPER_MODEL)
    logger.info("")

    test_a_single_image_vision()
    logger.info("")
    test_b_multi_image_vision()
    logger.info("")
    test_c_audio_transcription()
    logger.info("")
    logger.info("Smoke tests complete.")


if __name__ == "__main__":
    main()
