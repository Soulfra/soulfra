-- Migration 006: Add Soul History (Git for Souls)
-- From soul_git.py
--
-- Version control for souls - tracks evolution over time

CREATE TABLE IF NOT EXISTS soul_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_hash TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    committed_at TEXT NOT NULL,
    commit_message TEXT,
    soul_pack TEXT NOT NULL,
    tag TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_soul_history_user ON soul_history(user_id, committed_at DESC);
CREATE INDEX IF NOT EXISTS idx_soul_history_tag ON soul_history(user_id, tag);
