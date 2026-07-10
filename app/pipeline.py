import base64
import hashlib
import os
import shutil
import subprocess
import tempfile
import logging

import httpx

from prompts import STYLE_PROMPTS

logger = logging.getLogger(__name__)

NUM_FRAMES = 8


def _num_frames_for_duration(duration_seconds: float) -> int:
    """Scale frame count with clip length so longer clips get denser sampling."""
    if duration_seconds <= 30:
        return 8
    elif duration_seconds <= 60:
        return 12
    elif duration_seconds <= 90:
        return 16
    else:
        return 20


def _download_video(url, dest_path):
    logger.info("Downloading %s", url)
    with httpx.Client(timeout=httpx.Timeout(120.0), follow_redirects=True) as client:
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


def _extract_frames(video_path, work_dir, keep_files=False):
    duration = _probe_duration(video_path)
    logger.info("Video duration: %.2f s", duration)

    num_frames = _num_frames_for_duration(duration)

    frame_paths = []
    for i in range(num_frames):
        t = (i + 0.5) * duration / num_frames
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
        if not keep_files:
            os.remove(fp)

    logger.info("Extracted %d frames", len(encoded))
    return encoded


def process_clip(task, client):
    task_id = task["task_id"]
    video_url = task["video_url"]
    styles = task["styles"]

    logger.info("=== Task %s started ===", task_id)
    work_dir = tempfile.mkdtemp(prefix=f"clip_{task_id}_")

    try:
        video_path = os.path.join(work_dir, "video.mp4")
        _download_video(video_url, video_path)

        debug_save = os.environ.get("DEBUG_SAVE_FRAMES", "false").lower() == "true"
        frames = _extract_frames(video_path, work_dir, keep_files=debug_save)

        if debug_save:
            output_base = os.path.dirname(os.environ.get("OUTPUT_PATH", "/output/results.json"))
            debug_dir = os.path.join(output_base, "debug_frames", task_id)
            os.makedirs(debug_dir, exist_ok=True)
            for i, _ in enumerate(frames):
                src = os.path.join(work_dir, f"frame_{i:03d}.jpg")
                if os.path.exists(src):
                    shutil.copy2(src, debug_dir)
            # Diagnostic hash of frames saved to disk
            concat = "".join(frames)
            frames_hash = hashlib.sha256(concat.encode("utf-8")).hexdigest()[:16]
            logger.info(
                "Task %s: debug frames saved to %s (%d frames, hash=%s)",
                task_id, debug_dir, len(frames), frames_hash,
            )

        logger.info("Task %s: Stage 1 (vision) …", task_id)
        stage1_output = client.vision_describe(frames, task_id=task_id)
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
