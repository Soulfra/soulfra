-- Migration 010: Add Public Feedback System
-- From init_feedback.py
--
-- Allow users to report bugs WITHOUT logging in

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    component TEXT,
    message TEXT NOT NULL,
    url TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',
    admin_notes TEXT
);

-- Index for admin queries
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status, created_at DESC);
