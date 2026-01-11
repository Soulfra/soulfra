-- Migration 007: Add URL Shortener
-- From url_shortener.py
--
-- Short URLs for QR codes, marketing, and social media

CREATE TABLE IF NOT EXISTS url_shortcuts (
    short_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    UNIQUE(username)
);
