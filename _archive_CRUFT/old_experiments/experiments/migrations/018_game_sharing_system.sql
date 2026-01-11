-- Migration 018: Game Sharing & Peer Review System
-- "Send for Advice" - Share games with friends for feedback

-- ============================================================================
-- GAME SHARES - Track shared games sent to friends
-- ============================================================================

CREATE TABLE IF NOT EXISTS game_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_user_id INTEGER,  -- Who sent the game (can be NULL for anonymous)
    sender_name TEXT,  -- Name if not logged in
    sender_email TEXT,  -- Email if not logged in
    recipient_email TEXT NOT NULL,  -- Who they sent it to
    recipient_user_id INTEGER,  -- If recipient creates account
    game_type TEXT NOT NULL,  -- 'cringeproof', 'color_challenge', 'catchphrase_test', etc
    game_data TEXT NOT NULL,  -- JSON: their answers, scores, gameplay data
    share_code TEXT UNIQUE NOT NULL,  -- Unique link code (e.g., 'abc123xyz')
    message TEXT,  -- Personal message: "Hey can you review my answers?"
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'expired', 'revoked')),
    view_count INTEGER DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,  -- Optional expiration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_game_shares_code ON game_shares(share_code);
CREATE INDEX IF NOT EXISTS idx_game_shares_sender ON game_shares(sender_user_id);
CREATE INDEX IF NOT EXISTS idx_game_shares_recipient ON game_shares(recipient_email);
CREATE INDEX IF NOT EXISTS idx_game_shares_status ON game_shares(status);
CREATE INDEX IF NOT EXISTS idx_game_shares_created ON game_shares(created_at);

-- ============================================================================
-- GAME REVIEWS - Peer feedback on shared games
-- ============================================================================

CREATE TABLE IF NOT EXISTS game_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_share_id INTEGER NOT NULL,
    reviewer_user_id INTEGER,  -- If logged in
    reviewer_name TEXT,  -- If not logged in
    reviewer_email TEXT,  -- Contact info
    review_data TEXT NOT NULL,  -- JSON: ratings, feedback, answers to review questions
    review_type TEXT DEFAULT 'peer' CHECK(review_type IN ('peer', 'reference', 'mentor', 'self')),
    is_anonymous BOOLEAN DEFAULT 0,  -- Hide reviewer identity from sender
    overall_rating INTEGER CHECK(overall_rating >= 1 AND overall_rating <= 5),
    helpfulness_score REAL,  -- AI-calculated helpfulness (0.0 - 1.0)
    neural_classification TEXT,  -- JSON: neural network analysis results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_share_id) REFERENCES game_shares(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_game_reviews_share ON game_reviews(game_share_id);
CREATE INDEX IF NOT EXISTS idx_game_reviews_reviewer ON game_reviews(reviewer_user_id);
CREATE INDEX IF NOT EXISTS idx_game_reviews_created ON game_reviews(created_at);

-- ============================================================================
-- REVIEW ANALYSIS - AI-generated insights from peer reviews
-- ============================================================================

CREATE TABLE IF NOT EXISTS review_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_share_id INTEGER NOT NULL,
    review_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'self_awareness_gap', 'feedback_quality', 'action_items'
    analysis_data TEXT NOT NULL,  -- JSON: detailed analysis results
    confidence_score REAL,  -- How confident is the AI (0.0 - 1.0)
    network_name TEXT,  -- Which neural network generated this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_share_id) REFERENCES game_shares(id) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES game_reviews(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_share ON review_analysis(game_share_id);
CREATE INDEX IF NOT EXISTS idx_analysis_review ON review_analysis(review_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON review_analysis(analysis_type);

-- ============================================================================
-- SHARE NOTIFICATIONS - Track email/notification status
-- ============================================================================

CREATE TABLE IF NOT EXISTS share_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_share_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,  -- 'share_sent', 'review_received', 'reminder'
    recipient_email TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP,  -- Track email opens
    clicked_at TIMESTAMP,  -- Track link clicks
    template_used TEXT,  -- Which email template was used
    FOREIGN KEY (game_share_id) REFERENCES game_shares(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications_share ON share_notifications(game_share_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON share_notifications(notification_type);

-- ============================================================================
-- REVIEW QUESTIONS - Templates for review prompts
-- ============================================================================

CREATE TABLE IF NOT EXISTS review_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_type TEXT NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL,  -- 'rating', 'text', 'multiple_choice', 'comparison'
    order_index INTEGER DEFAULT 0,
    is_required BOOLEAN DEFAULT 1,
    metadata TEXT,  -- JSON: options for multiple choice, etc
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_questions_game ON review_questions(game_type);

-- ============================================================================
-- SEED DATA - Default review questions for cringeproof
-- ============================================================================

INSERT OR IGNORE INTO review_questions (id, game_type, question_text, question_type, order_index) VALUES
    (1, 'cringeproof', 'How self-aware does this person seem?', 'rating', 1),
    (2, 'cringeproof', 'Rate the honesty of their self-assessment', 'rating', 2),
    (3, 'cringeproof', 'What pattern did you notice that they might have missed?', 'text', 3),
    (4, 'cringeproof', 'Compared to how they rated themselves, I think they are...', 'multiple_choice', 4),
    (5, 'cringeproof', 'One thing they should work on:', 'text', 5),
    (6, 'cringeproof', 'One thing they do really well:', 'text', 6),
    (7, 'cringeproof', 'Overall helpfulness of their responses', 'rating', 7);

-- Multiple choice options stored in metadata
UPDATE review_questions
SET metadata = json('{"options": ["Much better than they think", "Slightly better", "About right", "Slightly worse", "Much worse"]}')
WHERE id = 4;

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- View: Top shared games
CREATE VIEW IF NOT EXISTS top_shared_games AS
SELECT
    game_type,
    COUNT(*) as share_count,
    AVG(review_count) as avg_reviews,
    AVG(view_count) as avg_views
FROM game_shares
GROUP BY game_type
ORDER BY share_count DESC;

-- View: Review completion rate
CREATE VIEW IF NOT EXISTS review_completion_rate AS
SELECT
    game_type,
    COUNT(*) as total_shares,
    SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) as completed_reviews,
    ROUND(100.0 * SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_rate
FROM game_shares
GROUP BY game_type;
