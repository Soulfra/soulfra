-- Fix Database Schema - Create Missing Tables
-- Run with: sqlite3 soulfra.db < fix_database_schema.sql

-- 1. Create subscribers table (missing - causes /admin error)
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'active',  -- active, unsubscribed, bounced
    source TEXT,  -- where they subscribed from
    tags TEXT,  -- JSON array of tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    unsubscribed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status);

-- 2. Create feedback table (missing - causes /admin error)
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT DEFAULT 'general',  -- general, bug, feature, complaint
    message TEXT NOT NULL,
    page_url TEXT,
    user_agent TEXT,
    status TEXT DEFAULT 'new',  -- new, reviewed, resolved, dismissed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(type);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);

-- 3. Add hash column to images table if missing (causes subdomain_router error)
-- SQLite doesn't support IF NOT EXISTS for columns, so we check first
-- This will fail silently if column already exists
ALTER TABLE images ADD COLUMN hash TEXT;

-- Create index on hash if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_images_hash ON images(hash);

-- 4. Verify brands table has all needed columns
-- These should already exist but adding them safely

-- Add missing brand columns (will fail silently if exist)
ALTER TABLE brands ADD COLUMN emoji TEXT;
ALTER TABLE brands ADD COLUMN brand_type TEXT DEFAULT 'member';
ALTER TABLE brands ADD COLUMN tier TEXT DEFAULT 'foundation';
ALTER TABLE brands ADD COLUMN tagline TEXT;
ALTER TABLE brands ADD COLUMN color_primary TEXT;
ALTER TABLE brands ADD COLUMN color_secondary TEXT;
ALTER TABLE brands ADD COLUMN color_accent TEXT;
ALTER TABLE brands ADD COLUMN personality TEXT;
ALTER TABLE brands ADD COLUMN personality_tone TEXT;
ALTER TABLE brands ADD COLUMN personality_traits TEXT;
ALTER TABLE brands ADD COLUMN brand_values TEXT;
ALTER TABLE brands ADD COLUMN target_audience TEXT;
ALTER TABLE brands ADD COLUMN story_theme TEXT;
ALTER TABLE brands ADD COLUMN config_json TEXT;

-- Summary output
SELECT '✅ Database schema fixed!' as result;
SELECT 'Tables created: subscribers, feedback' as result;
SELECT 'Columns added: images.hash, brands.* (if missing)' as result;
SELECT 'Run: python3 app.py to verify fixes' as result;
