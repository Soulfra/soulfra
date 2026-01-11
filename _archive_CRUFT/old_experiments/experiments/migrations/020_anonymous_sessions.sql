-- Migration 020: Anonymous Sessions & Account Linking
-- Enables anonymous gameplay → QR signup → claim results

-- ============================================================================
-- ANONYMOUS SESSIONS - Track non-logged-in users
-- ============================================================================

CREATE TABLE IF NOT EXISTS anonymous_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT UNIQUE NOT NULL,  -- 64-char hex token
    device_fingerprint TEXT,  -- SHA256 hash of IP + User-Agent + Language
    source TEXT DEFAULT 'cringeproof',  -- Which game/feature created session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,  -- 30 days from creation
    claimed_by_user_id INTEGER,  -- NULL until user claims
    claimed_at TIMESTAMP,
    FOREIGN KEY (claimed_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_token ON anonymous_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_claimed ON anonymous_sessions(claimed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_expires ON anonymous_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_source ON anonymous_sessions(source);

-- ============================================================================
-- UPDATE GAME_RESULTS - Add session token support
-- ============================================================================

-- Add session_token column to link anonymous results
ALTER TABLE game_results ADD COLUMN session_token TEXT;

-- Index for fast lookups by session token
CREATE INDEX IF NOT EXISTS idx_game_results_session ON game_results(session_token);

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- View: Session claim statistics
CREATE VIEW IF NOT EXISTS session_claim_stats AS
SELECT
    source,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN claimed_by_user_id IS NOT NULL THEN 1 ELSE 0 END) as claimed_sessions,
    SUM(CASE WHEN expires_at > CURRENT_TIMESTAMP AND claimed_by_user_id IS NULL THEN 1 ELSE 0 END) as active_sessions,
    SUM(CASE WHEN expires_at <= CURRENT_TIMESTAMP AND claimed_by_user_id IS NULL THEN 1 ELSE 0 END) as expired_sessions,
    ROUND(100.0 * SUM(CASE WHEN claimed_by_user_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as claim_rate
FROM anonymous_sessions
GROUP BY source;

-- View: Unclaimed results by session
CREATE VIEW IF NOT EXISTS unclaimed_results_summary AS
SELECT
    session_token,
    COUNT(*) as result_count,
    MIN(created_at) as first_result,
    MAX(created_at) as last_result
FROM game_results
WHERE session_token IS NOT NULL AND user_id IS NULL
GROUP BY session_token;

-- ============================================================================
-- CLEANUP PROCEDURE (Run periodically to remove old expired sessions)
-- ============================================================================

-- Delete expired unclaimed sessions older than 60 days
-- Run via: DELETE FROM anonymous_sessions WHERE expires_at < datetime('now', '-60 days') AND claimed_by_user_id IS NULL;
