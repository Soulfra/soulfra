-- CringeProof Feed Database Schema (Fixed for existing tables)

-- Table for cringe votes
CREATE TABLE IF NOT EXISTS cringe_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    vote_type TEXT NOT NULL CHECK(vote_type IN ('cringe', 'based')),
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pairing_id, user_id),
    FOREIGN KEY (pairing_id) REFERENCES voice_article_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_cringe_votes_pairing ON cringe_votes(pairing_id);
CREATE INDEX IF NOT EXISTS idx_cringe_votes_user ON cringe_votes(user_id);

-- Check if voice_article_pairings exists, if not create it
CREATE TABLE IF NOT EXISTS voice_article_pairings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id INTEGER NOT NULL,
    article_id INTEGER,
    prediction_text TEXT,
    time_locked_until DATETIME,
    unlocked_at DATETIME,
    cringeproof_score REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
);

-- Table for user feed preferences
CREATE TABLE IF NOT EXISTS feed_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    preferred_topics TEXT,
    cringe_tolerance REAL DEFAULT 0.5,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table for content wordmaps
CREATE TABLE IF NOT EXISTS content_wordmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    keywords TEXT,
    embedding TEXT,
    cluster_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pairing_id) REFERENCES voice_article_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_wordmaps_pairing ON content_wordmaps(pairing_id);
CREATE INDEX IF NOT EXISTS idx_wordmaps_cluster ON content_wordmaps(cluster_id);

-- Table for feed views
CREATE TABLE IF NOT EXISTS feed_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pairing_id INTEGER NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    watch_duration INTEGER,
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (pairing_id) REFERENCES voice_article_pairings(id)
);

CREATE INDEX IF NOT EXISTS idx_feed_views_pairing ON feed_views(pairing_id);
CREATE INDEX IF NOT EXISTS idx_feed_views_user ON feed_views(user_id);
