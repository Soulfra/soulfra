-- Migration 005: Add Images Table
-- From init_images_table.py
--
-- Database-first image storage - no file hosting needed

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,
    data BLOB NOT NULL,
    mime_type TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast hash lookups
CREATE INDEX IF NOT EXISTS idx_images_hash ON images(hash);
