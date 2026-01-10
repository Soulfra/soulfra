-- CringeProof Feed Database Schema
-- Supports TikTok-style voting and recommendations

-- Table for cringe votes
CREATE TABLE IF NOT EXISTS cringe_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    vote_type TEXT NOT NULL CHECK(vote_type IN ('cringe', 'based')),
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pairing_id, user_id),
    FOREIGN KEY (pairing_id) REFERENCES article_voice_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_cringe_votes_pairing ON cringe_votes(pairing_id);
CREATE INDEX IF NOT EXISTS idx_cringe_votes_user ON cringe_votes(user_id);

-- Add cringeproof_score to article_voice_pairings if not exists
-- (Score: 0.0 = all based, 1.0 = all cringe)
ALTER TABLE article_voice_pairings
ADD COLUMN cringeproof_score REAL DEFAULT 0.0;

-- Table for user feed preferences (for recommendations)
CREATE TABLE IF NOT EXISTS feed_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    preferred_topics TEXT, -- JSON array: ["ai", "crypto"]
    cringe_tolerance REAL DEFAULT 0.5, -- 0.0 = only based, 1.0 = only cringe
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table for content wordmaps (semantic clustering)
CREATE TABLE IF NOT EXISTS content_wordmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    keywords TEXT, -- JSON array of extracted keywords
    embedding TEXT, -- JSON array of embedding vector (for similarity)
    cluster_id INTEGER, -- Cluster assignment
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pairing_id) REFERENCES article_voice_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_wordmaps_pairing ON content_wordmaps(pairing_id);
CREATE INDEX IF NOT EXISTS idx_wordmaps_cluster ON content_wordmaps(cluster_id);

-- Table for feed item views (analytics)
CREATE TABLE IF NOT EXISTS feed_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    watch_duration INTEGER, -- Seconds watched
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (pairing_id) REFERENCES article_voice_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_feed_views_pairing ON feed_views(pairing_id);
CREATE INDEX IF NOT EXISTS idx_feed_views_user ON feed_views(user_id);
