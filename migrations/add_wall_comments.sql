-- Wall Comments System - WordPress for AI Agents
-- Users can comment on Cal's voice posts with phone verification

-- Comments table
CREATE TABLE IF NOT EXISTS wall_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id INTEGER NOT NULL,
    user_id INTEGER,
    phone_hash TEXT,  -- For anonymous phone-verified users
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Verification tier (from phone_verification.py)
    verification_tier TEXT DEFAULT 'anonymous',  -- anonymous, phone, pc_phone, premium
    verification_badge TEXT DEFAULT '👤',  -- 👤, 📱, 💻📱, ⭐

    -- Moderation
    flagged INTEGER DEFAULT 0,
    deleted_at TIMESTAMP,

    FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_wall_comments_recording ON wall_comments(recording_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_wall_comments_user ON wall_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_wall_comments_phone ON wall_comments(phone_hash);

-- Comment rate limiting (prevent spam)
CREATE TABLE IF NOT EXISTS comment_rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_hash TEXT,
    user_id INTEGER,
    comments_this_hour INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(phone_hash, window_start),
    UNIQUE(user_id, window_start)
);
