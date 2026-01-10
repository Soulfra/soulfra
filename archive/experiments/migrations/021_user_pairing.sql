-- Migration 021: User Pairing & Blending System
-- Enables Spotify Blend-style account pairing for personality comparisons

-- ============================================================================
-- USER CONNECTIONS - Track relationships between users
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id_1 INTEGER NOT NULL,  -- First user (requester)
    user_id_2 INTEGER NOT NULL,  -- Second user (recipient)
    connection_type TEXT DEFAULT 'blend',  -- 'blend', 'pair', 'compare'
    status TEXT DEFAULT 'pending',  -- 'pending', 'accepted', 'declined', 'blocked'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id_1) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id_2) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id_1, user_id_2, connection_type)  -- Prevent duplicate connections
);

CREATE INDEX IF NOT EXISTS idx_user_connections_user1 ON user_connections(user_id_1);
CREATE INDEX IF NOT EXISTS idx_user_connections_user2 ON user_connections(user_id_2);
CREATE INDEX IF NOT EXISTS idx_user_connections_status ON user_connections(status);
CREATE INDEX IF NOT EXISTS idx_user_connections_type ON user_connections(connection_type);

-- ============================================================================
-- CONNECTION BLENDS - Merged results and compatibility scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS connection_blends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL UNIQUE,  -- One blend per connection
    blend_data TEXT NOT NULL,  -- JSON with merged cringeproof results
    compatibility_score REAL DEFAULT 0.0,  -- 0-100 percentage
    insights TEXT,  -- JSON array of generated insights
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES user_connections(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_connection_blends_connection ON connection_blends(connection_id);
CREATE INDEX IF NOT EXISTS idx_connection_blends_score ON connection_blends(compatibility_score);

-- ============================================================================
-- BLEND ANALYTICS VIEWS
-- ============================================================================

-- View: Active connections summary
CREATE VIEW IF NOT EXISTS active_connections_summary AS
SELECT
    connection_type,
    status,
    COUNT(*) as connection_count,
    AVG(JULIANDAY(updated_at) - JULIANDAY(created_at)) as avg_days_to_accept
FROM user_connections
GROUP BY connection_type, status;

-- View: User pairing statistics
CREATE VIEW IF NOT EXISTS user_pairing_stats AS
SELECT
    u.id as user_id,
    u.username,
    COUNT(CASE WHEN uc.status = 'accepted' THEN 1 END) as active_pairs,
    COUNT(CASE WHEN uc.status = 'pending' THEN 1 END) as pending_requests,
    AVG(cb.compatibility_score) as avg_compatibility
FROM users u
LEFT JOIN user_connections uc ON (u.id = uc.user_id_1 OR u.id = uc.user_id_2)
LEFT JOIN connection_blends cb ON uc.id = cb.connection_id
GROUP BY u.id, u.username;

-- View: Top compatible pairs
CREATE VIEW IF NOT EXISTS top_compatible_pairs AS
SELECT
    u1.username as user1_name,
    u2.username as user2_name,
    cb.compatibility_score,
    uc.created_at
FROM connection_blends cb
JOIN user_connections uc ON cb.connection_id = uc.id
JOIN users u1 ON uc.user_id_1 = u1.id
JOIN users u2 ON uc.user_id_2 = u2.id
WHERE uc.status = 'accepted'
ORDER BY cb.compatibility_score DESC
LIMIT 100;

-- ============================================================================
-- EXAMPLE USAGE
-- ============================================================================

-- Create pairing request:
-- INSERT INTO user_connections (user_id_1, user_id_2, connection_type)
-- VALUES (1, 2, 'blend');

-- Accept pairing request:
-- UPDATE user_connections
-- SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
-- WHERE id = 1;

-- Create blend after acceptance:
-- INSERT INTO connection_blends (connection_id, blend_data, compatibility_score)
-- VALUES (1, '{"merged_scores": {...}}', 87.5);

-- Get user's active pairs:
-- SELECT * FROM user_pairing_stats WHERE username = 'alice';

-- Get pending requests for user:
-- SELECT u.username, uc.created_at
-- FROM user_connections uc
-- JOIN users u ON uc.user_id_1 = u.id
-- WHERE uc.user_id_2 = 2 AND uc.status = 'pending';
