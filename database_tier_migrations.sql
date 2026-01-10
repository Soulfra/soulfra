-- Database Tier Migrations - Multi-Tier Architecture
-- ====================================================
--
-- Adds support for:
-- 1. Images linked to posts (TIER 1: Binary)
-- 2. Neural "soul" ratings (TIER 3: AI)
-- 3. DM channels via QR scan (TIER 5: Distribution)
-- 4. Template outputs tracking (TIER 4: Templates)
--
-- Usage:
--     sqlite3 soulfra.db < database_tier_migrations.sql
--
-- Or run via Python:
--     python3 -c "from database import get_db; exec(open('database_tier_migrations.sql').read())"
--
-- Created: 2025-12-27
-- Purpose: Enable multi-tier architecture with QR galleries, soul ratings, DM via QR

-- =============================================================================
-- TIER 1: Binary/Media Layer
-- =============================================================================

-- Add post_id to images table (link images to posts)
ALTER TABLE images ADD COLUMN post_id INTEGER;

-- Add brand_id to images (link images to brands)
ALTER TABLE images ADD COLUMN brand_id INTEGER;

-- Add alt_text for accessibility
ALTER TABLE images ADD COLUMN alt_text TEXT;

-- Add image type (post_image, avatar, gallery, social_share, etc.)
ALTER TABLE images ADD COLUMN image_type TEXT DEFAULT 'post_image';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_post ON images(post_id);
CREATE INDEX IF NOT EXISTS idx_images_brand ON images(brand_id);
CREATE INDEX IF NOT EXISTS idx_images_type ON images(image_type);

-- =============================================================================
-- TIER 3: AI/Neural Network Layer - Soul Ratings
-- =============================================================================

-- Neural ratings table - stores AI "soul" scores for content
CREATE TABLE IF NOT EXISTS neural_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,  -- 'post', 'user', 'comment', 'brand'
    entity_id INTEGER NOT NULL,
    network_name TEXT NOT NULL,  -- 'soulfra_judge', 'calriven', 'theauditor', 'deathtodata'
    score REAL NOT NULL,  -- 0.0 - 1.0
    confidence REAL,  -- How confident the network is
    reasoning TEXT,  -- Why this score?
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_id, network_name)  -- One rating per network per entity
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_neural_ratings_entity ON neural_ratings(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_neural_ratings_network ON neural_ratings(network_name);
CREATE INDEX IF NOT EXISTS idx_neural_ratings_score ON neural_ratings(score DESC);

-- Composite soul scores - averaged across all networks
CREATE TABLE IF NOT EXISTS soul_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    composite_score REAL NOT NULL,  -- Average of all network scores
    tier TEXT,  -- 'Legendary', 'High', 'Moderate', 'Low', 'None'
    total_networks INTEGER,  -- How many networks rated this
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_id)
);

-- Index for fast soul score lookups
CREATE INDEX IF NOT EXISTS idx_soul_scores_entity ON soul_scores(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_soul_scores_tier ON soul_scores(tier);

-- =============================================================================
-- TIER 5: Distribution Layer - DM via QR Scan
-- =============================================================================

-- DM channels table - only created via in-person QR scan
CREATE TABLE IF NOT EXISTS dm_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_a_id INTEGER NOT NULL,
    user_b_id INTEGER NOT NULL,
    verified_in_person BOOLEAN DEFAULT FALSE,
    qr_scanned_at TIMESTAMP,
    qr_code_hash TEXT,  -- Hash of QR code that was scanned
    location_lat REAL,  -- Optional: GPS latitude
    location_lon REAL,  -- Optional: GPS longitude
    trust_score REAL DEFAULT 0.5,  -- 0.0-1.0, higher = more trusted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_a_id, user_b_id)  -- Only one channel per pair
);

-- Indexes for DM channels
CREATE INDEX IF NOT EXISTS idx_dm_channels_users ON dm_channels(user_a_id, user_b_id);
CREATE INDEX IF NOT EXISTS idx_dm_channels_trust ON dm_channels(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_dm_channels_verified ON dm_channels(verified_in_person);

-- DM messages table
CREATE TABLE IF NOT EXISTS dm_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(channel_id) REFERENCES dm_channels(id)
);

-- Indexes for DM messages
CREATE INDEX IF NOT EXISTS idx_dm_messages_channel ON dm_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_dm_messages_unread ON dm_messages(channel_id, read);

-- =============================================================================
-- TIER 4: Template Layer - Output Tracking
-- =============================================================================

-- Template outputs table - tracks what was generated from each post
CREATE TABLE IF NOT EXISTS template_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    output_type TEXT NOT NULL,  -- 'newsletter', 'website', 'gallery', 'social', 'rss', 'pdf'
    file_path TEXT,  -- Where the output was saved
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON: size, format, etc.
);

-- Index for template outputs
CREATE INDEX IF NOT EXISTS idx_template_outputs_post ON template_outputs(post_id);
CREATE INDEX IF NOT EXISTS idx_template_outputs_type ON template_outputs(output_type);

-- =============================================================================
-- TIER 5: QR Gallery System
-- =============================================================================

-- QR galleries table - enhanced QR codes that open galleries
CREATE TABLE IF NOT EXISTS qr_galleries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    gallery_slug TEXT UNIQUE NOT NULL,
    qr_code_path TEXT,  -- Path to QR code image
    qr_code_hash TEXT,  -- Hash for verification
    expires_at TIMESTAMP,  -- Optional expiration
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for QR galleries
CREATE INDEX IF NOT EXISTS idx_qr_galleries_post ON qr_galleries(post_id);
CREATE INDEX IF NOT EXISTS idx_qr_galleries_slug ON qr_galleries(gallery_slug);

-- =============================================================================
-- VIEWS for easier querying
-- =============================================================================

-- View: posts_with_soul_scores
-- Shows all posts with their composite soul scores
CREATE VIEW IF NOT EXISTS posts_with_soul_scores AS
SELECT
    p.id as post_id,
    p.title,
    p.slug,
    s.composite_score as soul_score,
    s.tier as soul_tier,
    s.total_networks as networks_rated,
    p.published_at
FROM posts p
LEFT JOIN soul_scores s ON s.entity_type = 'post' AND s.entity_id = p.id
WHERE p.published_at IS NOT NULL;

-- View: posts_with_images
-- Shows all posts with their associated images
CREATE VIEW IF NOT EXISTS posts_with_images AS
SELECT
    p.id as post_id,
    p.title,
    p.slug,
    COUNT(i.id) as image_count,
    GROUP_CONCAT(i.hash) as image_hashes
FROM posts p
LEFT JOIN images i ON i.post_id = p.id
WHERE p.published_at IS NOT NULL
GROUP BY p.id;

-- View: neural_rating_summary
-- Summary of neural ratings per post
CREATE VIEW IF NOT EXISTS neural_rating_summary AS
SELECT
    entity_type,
    entity_id,
    network_name,
    score,
    rated_at,
    CASE
        WHEN score >= 0.9 THEN 'Legendary Soul 🌟'
        WHEN score >= 0.7 THEN 'High Soul ⭐'
        WHEN score >= 0.5 THEN 'Moderate Soul ⚡'
        WHEN score >= 0.3 THEN 'Low Soul 💧'
        ELSE 'No Soul ❌'
    END as tier_label
FROM neural_ratings
ORDER BY entity_type, entity_id, score DESC;

-- View: dm_channels_verified
-- All DM channels verified via in-person QR scan
CREATE VIEW IF NOT EXISTS dm_channels_verified AS
SELECT
    dc.id as channel_id,
    dc.user_a_id,
    dc.user_b_id,
    u1.username as user_a_username,
    u2.username as user_b_username,
    dc.verified_in_person,
    dc.trust_score,
    dc.qr_scanned_at,
    dc.created_at
FROM dm_channels dc
JOIN users u1 ON dc.user_a_id = u1.id
JOIN users u2 ON dc.user_b_id = u2.id
WHERE dc.verified_in_person = TRUE;

-- =============================================================================
-- SAMPLE QUERIES
-- =============================================================================

-- Query 1: Get all posts with "Legendary Soul" rating
-- SELECT * FROM posts_with_soul_scores WHERE soul_tier = 'Legendary';

-- Query 2: Get all images for a specific post
-- SELECT * FROM images WHERE post_id = 29;

-- Query 3: Get neural ratings breakdown for a post
-- SELECT * FROM neural_rating_summary WHERE entity_type = 'post' AND entity_id = 29;

-- Query 4: Get all verified DM channels
-- SELECT * FROM dm_channels_verified;

-- Query 5: Get posts with most images
-- SELECT * FROM posts_with_images ORDER BY image_count DESC LIMIT 10;

-- =============================================================================
-- CLEANUP (if needed)
-- =============================================================================

-- To revert migrations:
--
-- DROP VIEW IF EXISTS dm_channels_verified;
-- DROP VIEW IF EXISTS neural_rating_summary;
-- DROP VIEW IF EXISTS posts_with_images;
-- DROP VIEW IF EXISTS posts_with_soul_scores;
-- DROP TABLE IF EXISTS qr_galleries;
-- DROP TABLE IF EXISTS template_outputs;
-- DROP TABLE IF EXISTS dm_messages;
-- DROP TABLE IF EXISTS dm_channels;
-- DROP TABLE IF EXISTS soul_scores;
-- DROP TABLE IF EXISTS neural_ratings;
--
-- DROP INDEX IF EXISTS idx_images_type;
-- DROP INDEX IF EXISTS idx_images_brand;
-- DROP INDEX IF EXISTS idx_images_post;
--
-- Note: Cannot drop columns in SQLite easily (would need to recreate table)

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify migrations were successful:
--
-- Check images table:
-- PRAGMA table_info(images);
--
-- Check neural_ratings table:
-- PRAGMA table_info(neural_ratings);
--
-- Check dm_channels table:
-- PRAGMA table_info(dm_channels);
--
-- Check views:
-- SELECT name FROM sqlite_master WHERE type='view';

-- =============================================================================
-- END OF MIGRATIONS
-- =============================================================================

-- Migration complete!
--
-- Next steps:
-- 1. Run: python3 neural_soul_scorer.py --all
-- 2. Generate galleries: python3 qr_gallery_system.py --all
-- 3. Test DM system: python3 dm_via_qr.py --demo
-- 4. Generate outputs: python3 template_orchestrator.py --all
