import os
import logging

logger = logging.getLogger(__name__)


def get_client():
    provider = os.environ.get("CAPTION_PROVIDER", "fireworks").strip().lower()

    if provider == "fireworks":
        from fireworks_client import FireworksClient

        if not os.environ.get("FIREWORKS_API_KEY"):
            raise RuntimeError(
                "CAPTION_PROVIDER=fireworks but FIREWORKS_API_KEY is not set"
            )
        logger.info("Using Fireworks client")
        return FireworksClient()

    elif provider == "groq":
        from groq_client import GroqClient

        if not os.environ.get("GROQ_API_KEY"):
            raise RuntimeError(
                "CAPTION_PROVIDER=groq but GROQ_API_KEY is not set"
            )
        logger.info("Using Groq client")
        return GroqClient()

    else:
        raise RuntimeError(
            f"Unknown CAPTION_PROVIDER '{provider}'. "
            f"Expected 'fireworks' or 'groq'."
        )
