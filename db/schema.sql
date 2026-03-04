CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
    content     TEXT    NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at  REAL    NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

CREATE TABLE IF NOT EXISTS memory_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_text TEXT    NOT NULL,
    chroma_id   TEXT    NOT NULL,
    created_at  REAL    NOT NULL DEFAULT (strftime('%s', 'now'))
);
