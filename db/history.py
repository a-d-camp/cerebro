from __future__ import annotations

import sqlite3
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

_conn: sqlite3.Connection | None = None


def _get_conn(sqlite_path: str) -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        _conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _apply_schema(_conn)
    return _conn


def _apply_schema(conn: sqlite3.Connection) -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()


def init(sqlite_path: str) -> None:
    _get_conn(sqlite_path)
    logger.info("SQLite initialised at %s", sqlite_path)


def insert(sqlite_path: str, role: str, content: str) -> int:
    token_count = len(content) // 4
    conn = _get_conn(sqlite_path)
    cur = conn.execute(
        "INSERT INTO messages (role, content, token_count) VALUES (?, ?, ?)",
        (role, content, token_count),
    )
    conn.commit()
    logger.debug("Inserted %s message id=%d tokens=%d", role, cur.lastrowid, token_count)
    return cur.lastrowid


def get_window(sqlite_path: str, token_budget: int = 4000) -> List[Dict[str, str]]:
    conn = _get_conn(sqlite_path)
    rows = conn.execute(
        "SELECT id, role, content, token_count FROM messages ORDER BY created_at DESC LIMIT 200"
    ).fetchall()

    accumulated = 0
    kept = []
    for row in rows:
        accumulated += row["token_count"]
        if accumulated > token_budget:
            break
        kept.append({"role": row["role"], "content": row["content"]})

    kept.reverse()
    logger.debug("History window: %d messages, ~%d tokens", len(kept), accumulated)
    return kept


def count_user_messages(sqlite_path: str) -> int:
    conn = _get_conn(sqlite_path)
    row = conn.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'").fetchone()
    return row[0]


def log_memory(sqlite_path: str, memory_text: str, chroma_id: str) -> None:
    conn = _get_conn(sqlite_path)
    conn.execute(
        "INSERT INTO memory_log (memory_text, chroma_id) VALUES (?, ?)",
        (memory_text, chroma_id),
    )
    conn.commit()
