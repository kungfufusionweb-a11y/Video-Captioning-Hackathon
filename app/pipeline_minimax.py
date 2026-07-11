import logging

from prompts import STYLE_PROMPTS

logger = logging.getLogger(__name__)


def process_clip_minimax(task, client):
    task_id = task["task_id"]
    video_url = task["video_url"]
    styles = task["styles"]

    logger.info("[MINIMAX] === Task %s started ===", task_id)

    try:
        logger.info("[MINIMAX] Task %s: Stage 1 (vision, video_url) …", task_id)
        stage1_output = client.vision_describe(video_url)
        logger.info("[MINIMAX] Task %s: Stage 1 done (%d chars)", task_id, len(stage1_output))

        captions = {}
        for style in styles:
            if style not in STYLE_PROMPTS:
                logger.warning("[MINIMAX] Task %s: unknown style '%s'", task_id, style)
                captions[style] = f"[{style} caption not available]"
                continue
            try:
                caption = client.style_rewrite(stage1_output, STYLE_PROMPTS[style])
                captions[style] = caption
                logger.info("[MINIMAX] Task %s: style '%s' done (%d chars)", task_id, style, len(caption))
            except Exception as e:
                logger.error("[MINIMAX] Task %s: style '%s' failed: %s", task_id, style, e)
                captions[style] = f"[{style} caption unavailable due to processing error]"

        logger.info("[MINIMAX] === Task %s complete ===", task_id)
        return {"task_id": task_id, "captions": captions}

    except Exception as e:
        logger.error("[MINIMAX] Task %s: unrecoverable error: %s", task_id, e)
        fallback = {}
        for style in styles:
            fallback[style] = f"[{style} caption unavailable]"
        return {"task_id": task_id, "captions": fallback}
