from typing import List, Dict, Any

SYSTEM_BASE = """You are Cerebro, a personal AI assistant. You have persistent memory \
across conversations and grow more useful over time as you learn about the user's life, \
goals, and preferences.

Be concise, direct, and genuinely helpful. Adapt your tone to the conversation."""

CLASSIFICATION_PROMPT = """Classify the following message as SIMPLE or COMPLEX.

COMPLEX if: multi-step reasoning, code generation, analysis/synthesis, emotional weight, \
or explicit advice-seeking.
SIMPLE otherwise.

Respond with exactly one word: SIMPLE or COMPLEX

Message: {message}"""

MEMORY_WRITE_PROMPT = """Given this exchange, extract anything worth remembering about the user. \
Be selective — only save if genuinely useful. Write as a concise standalone statement.

Capture any of: facts, preferences, goals, reasoning patterns, \
emotional context, recurring themes, tensions or contradictions.

If nothing worth saving, respond: NOTHING

User: {user_message}
Assistant: {assistant_response}"""

PROFILE_UPDATE_PROMPT = """Maintain a profile of the user based on their conversations. \
Update it with new information from the exchange below.

Rules:
- Max 300 words
- Use sections: Identity, Preferences, Goals & Projects, Relationships, Other
- Preserve accurate existing info; add/update from new exchange; remove contradicted facts
- Return only the profile text, no preamble

Current profile:
{current_profile}

Recent exchange:
User: {user_message}
Assistant: {assistant_response}"""

SYNTHESIS_PROMPT = """You are building a deep model of a person from their conversation history. \
Below is everything known about them.

Synthesise this into observations about their patterns, tendencies, and recurring themes. \
These are hypotheses — hold them lightly and be specific, not generic.

Focus on:
- Recurring themes across different topics
- How they tend to reason and make decisions
- What seems to energise or drain them
- Tensions or contradictions worth noting
- Questions they seem to be living with, even if unasked

Max 400 words. Ground every observation in the evidence.

## Profile
{profile}

## All Memories
{memories}"""

MEMORY_MERGE_PROMPT = """Merge these two related memory fragments into one richer, \
more complete statement. Be concise.

Fragment 1: {existing}
Fragment 2: {new}

Return only the merged statement."""


def build_system(memories: List[Dict[str, Any]], profile: str = "", synthesis: str = "") -> str:
    parts = [SYSTEM_BASE]
    if profile:
        parts.append(f"## User Profile\n{profile}")
    if synthesis:
        parts.append(f"## Patterns & Hypotheses\n{synthesis}")
    if memories:
        memory_lines = "\n".join(f"- {m['document']}" for m in memories)
        parts.append(f"## Relevant Memories\n{memory_lines}")
    return "\n\n".join(parts)
