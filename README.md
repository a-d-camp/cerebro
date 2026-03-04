# Second Brain — Spec

## What This Is

A personal AI assistant accessible via Telegram. The user can share notes, log thoughts and feelings, and have ongoing conversations. Over time it builds a persistent memory of the user's life, personality, and goals — becoming more useful the more it's used. Single-user only.

---

## Core Requirements

- **Telegram interface** — the only input/output channel
- **Persistent memory** — important facts and context are stored and retrieved across sessions
- **Conversation history** — recent messages are included in each request for continuity
- **Dynamic system prompt** — each request is enriched with relevant memories and user profile data
- **Model routing** — use Haiku by default, escalate to Sonnet for complex or emotional conversations
- **Single-user security** — only respond to a whitelisted Telegram user ID

---

## Tech Stack

| Layer | Choice |
|---|---|
| Interface | Telegram Bot (`python-telegram-bot`) |
| LLM | Claude API — `claude-haiku-4-5` / `claude-sonnet-4-6` |
| Long-term memory | Chroma (local, file-backed vector DB) |
| Structured storage | SQLite |
| Language | Python 3.11+ |

---

## Model Routing

Default to **Haiku**. Escalate to **Sonnet** for emotionally complex messages, explicit advice-seeking, or when the user prefixes their message with `/think`. Claude Code should use its judgement on the best routing implementation approach.

## Out of Scope (for now)

- Reminders / scheduled proactive messages
- Voice transcription
- Web dashboard