from __future__ import annotations

import logging
from typing import List, Dict

import anthropic

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def init(api_key: str) -> None:
    global _client
    _client = anthropic.Anthropic(api_key=api_key)
    logger.info("Anthropic client initialised")


def _get_client() -> anthropic.Anthropic:
    if _client is None:
        raise RuntimeError("LLM client not initialised. Call client.init() first.")
    return _client


def chat(
    messages: List[Dict[str, str]],
    system: str,
    model: str,
    max_tokens: int = 1024,
) -> str:
    client = _get_client()
    logger.debug("LLM call model=%s messages=%d", model, len(messages))
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    text = response.content[0].text
    logger.debug("LLM response tokens=%d", response.usage.output_tokens)
    return text


def quick(prompt: str, model: str, max_tokens: int = 200) -> str:
    """Single-turn utility call (classification, memory extraction)."""
    client = _get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
