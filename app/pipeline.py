import base64
import os
import shutil
import subprocess
import tempfile
import logging

import httpx

from fireworks_client import FireworksClient
from prompts import STYLE_PROMPTS

logger = logging.getLogger(__name__)

NUM_FRAMES = 8


def _download_video(url, dest_path):
    logger.info("Downloading %s", url)
    with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
        resp = client.get(url)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
    logger.info("Downloaded %s (%d bytes)", url, os.path.getsize(dest_path))


def _probe_duration(video_path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            video_path,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    result.check_returncode()
    return float(result.stdout.strip())


def _extract_frames(video_path, work_dir):
    duration = _probe_duration(video_path)
    logger.info("Video duration: %.2f s", duration)

    frame_paths = []
    for i in range(NUM_FRAMES):
        t = (i + 0.5) * duration / NUM_FRAMES
        out = os.path.join(work_dir, f"frame_{i:03d}.jpg")
        subprocess.run(
            [
                "ffmpeg", "-ss", str(t), "-i", video_path,
                "-vframes", "1", "-q:v", "2", out, "-y",
            ],
            capture_output=True,
            timeout=30,
            check=True,
        )
        frame_paths.append(out)

    encoded = []
    for fp in frame_paths:
        with open(fp, "rb") as f:
            encoded.append(base64.b64encode(f.read()).decode("utf-8"))
        os.remove(fp)

    logger.info("Extracted %d frames", len(encoded))
    return encoded


def _extract_audio(video_path):
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", video_path, "-vn",
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                audio_path, "-y",
            ],
            capture_output=True,
            timeout=60,
            check=True,
        )
        with open(audio_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.warning("Audio extraction failed (non-fatal): %s", e)
        return None
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def process_clip(task, client):
    task_id = task["task_id"]
    video_url = task["video_url"]
    styles = task["styles"]

    logger.info("=== Task %s started ===", task_id)
    work_dir = tempfile.mkdtemp(prefix=f"clip_{task_id}_")

    try:
        video_path = os.path.join(work_dir, "video.mp4")
        _download_video(video_url, video_path)

        frames = _extract_frames(video_path, work_dir)

        transcript = None
        audio_bytes = _extract_audio(video_path)
        if audio_bytes:
            try:
                transcript = client.transcribe(audio_bytes)
                logger.info("Task %s: transcript (%d chars)", task_id, len(transcript))
            except Exception as e:
                logger.warning("Task %s: transcription failed (non-fatal): %s", task_id, e)

        logger.info("Task %s: Stage 1 (vision) …", task_id)
        stage1_output = client.vision_describe(frames, transcript=transcript)
        logger.info("Task %s: Stage 1 done (%d chars)", task_id, len(stage1_output))

        captions = {}
        for style in styles:
            if style not in STYLE_PROMPTS:
                logger.warning("Task %s: unknown style '%s'", task_id, style)
                captions[style] = f"[{style} caption not available]"
                continue
            try:
                caption = client.style_rewrite(stage1_output, STYLE_PROMPTS[style])
                captions[style] = caption
                logger.info("Task %s: style '%s' done (%d chars)", task_id, style, len(caption))
            except Exception as e:
                logger.error("Task %s: style '%s' failed: %s", task_id, style, e)
                captions[style] = f"[{style} caption unavailable due to processing error]"

        logger.info("=== Task %s complete ===", task_id)
        return {"task_id": task_id, "captions": captions}

    except Exception as e:
        logger.error("Task %s: unrecoverable error: %s", task_id, e)
        fallback = {}
        for style in styles:
            fallback[style] = f"[{style} caption unavailable]"
        return {"task_id": task_id, "captions": fallback}

    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.info("Task %s: cleaned up temp dir", task_id)
