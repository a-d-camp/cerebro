import os
import logging

logger = logging.getLogger(__name__)


def load(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def save(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    logger.debug("Profile saved to %s", path)
