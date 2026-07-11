import logging
import os

from fireworks_client import FireworksClient

logger = logging.getLogger(__name__)


def get_client():
    if not os.environ.get("FIREWORKS_API_KEY"):
        raise RuntimeError(
            "FIREWORKS_API_KEY is not set — cannot create Fireworks client"
        )
    logger.info("Using Fireworks client (MiniMax M3)")
    return FireworksClient()
