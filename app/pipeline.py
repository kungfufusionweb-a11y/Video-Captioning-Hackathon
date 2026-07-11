import logging

import httpx

from prompts import STYLE_PROMPTS

logger = logging.getLogger(__name__)

MAX_VIDEO_BYTES = 80 * 1024 * 1024  # 80 MB


class VideoSizeError(Exception):
    pass


def _check_video_size(video_url: str) -> None:
    logger.info("Checking video size: %s", video_url)
    try:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            resp = client.head(video_url, follow_redirects=True)
            resp.raise_for_status()
            content_length = resp.headers.get("Content-Length")
            if content_length is None:
                logger.warning(
                    "Cannot determine video size (no Content-Length header) — proceeding without guard"
                )
                return
            size = int(content_length)
            size_mb = size / (1024 * 1024)
            if size > MAX_VIDEO_BYTES:
                raise VideoSizeError(
                    f"Video exceeds size threshold for direct video_url ingestion: {size_mb:.1f}MB "
                    f"(limit: {MAX_VIDEO_BYTES / (1024 * 1024):.0f}MB) — url: {video_url}"
                )
            logger.info("Video size: %.1f MB (within %.0f MB limit)", size_mb, MAX_VIDEO_BYTES / (1024 * 1024))
    except VideoSizeError:
        raise
    except Exception as e:
        logger.warning("Failed to HEAD video URL (%s) — proceeding without size guard: %s", video_url, e)


def process_clip(task, client):
    task_id = task["task_id"]
    video_url = task["video_url"]
    styles = task["styles"]

    logger.info("=== Task %s started ===", task_id)

    try:
        logger.info("Task %s: Stage 1 (vision, video_url) …", task_id)
        _check_video_size(video_url)
        stage1_output = client.vision_describe(video_url)
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
