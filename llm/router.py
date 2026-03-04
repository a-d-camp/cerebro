import logging

from llm import client as llm_client
from llm.prompts import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-4-6"


def classify(message: str) -> str:
    """Run Haiku pre-pass. Returns 'SIMPLE' or 'COMPLEX'."""
    prompt = CLASSIFICATION_PROMPT.format(message=message)
    try:
        result = llm_client.quick(prompt, model=HAIKU_MODEL, max_tokens=5)
        label = result.strip().upper()
        if label not in ("SIMPLE", "COMPLEX"):
            logger.warning("Unexpected classification result %r, defaulting to SIMPLE", result)
            label = "SIMPLE"
        logger.debug("Classification: %s", label)
        return label
    except Exception as e:
        logger.warning("Classification failed (%s), defaulting to SIMPLE", e)
        return "SIMPLE"


def select_model(message: str, force_sonnet: bool = False) -> str:
    """Return the model to use for this message."""
    if force_sonnet:
        logger.debug("model=sonnet (forced via /think)")
        return SONNET_MODEL

    label = classify(message)
    model = SONNET_MODEL if label == "COMPLEX" else HAIKU_MODEL
    logger.debug("model=%s (classification=%s)", model, label)
    return model
