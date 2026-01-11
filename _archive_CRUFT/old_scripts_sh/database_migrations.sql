-- Database Migrations for Comment→Post Expansion
-- =================================================
--
-- Adds fields needed for self-sustaining content loop:
-- 1. comments.expanded_to_post_id - Links comment to post it created
-- 2. comments.expansion_quality - Quality score (0.0-1.0) of expansion
-- 3. posts.source_comment_id - Links post back to source comment
--
-- Usage:
--     sqlite3 soulfra.db < database_migrations.sql
--
-- Or run via Python:
--     python3 comment_to_post.py migrate
--
-- Created: 2025-12-27
-- Purpose: Enable comment→post expansion for infinite content generation

-- =============================================================================
-- MIGRATION: Add comment→post linking fields
-- =============================================================================

-- Add expanded_to_post_id to comments table
-- This tracks which post was created from this comment
ALTER TABLE comments ADD COLUMN expanded_to_post_id INTEGER;

-- Add expansion_quality to comments table
-- Quality score (0.0-1.0) for the expansion
-- Used to identify which comments expanded well
ALTER TABLE comments ADD COLUMN expansion_quality REAL DEFAULT 0.0;

-- Add source_comment_id to posts table
-- Links post back to the comment it was created from
ALTER TABLE posts ADD COLUMN source_comment_id INTEGER;

-- =============================================================================
-- INDEXES for performance
-- =============================================================================

-- Index for finding posts created from comments
CREATE INDEX IF NOT EXISTS idx_comments_expansion
ON comments(expanded_to_post_id);

-- Index for finding source comments of posts
CREATE INDEX IF NOT EXISTS idx_posts_source
ON posts(source_comment_id);

-- Index for finding high-quality expansions
CREATE INDEX IF NOT EXISTS idx_comments_quality
ON comments(expansion_quality DESC)
WHERE expansion_quality IS NOT NULL;

-- =============================================================================
-- VIEWS for easier querying
-- =============================================================================

-- View: expanded_comments
-- Shows all comments that have been expanded to posts
CREATE VIEW IF NOT EXISTS expanded_comments AS
SELECT
    c.id as comment_id,
    c.content as comment_content,
    c.expanded_to_post_id,
    c.expansion_quality,
    u.username as commenter,
    p.id as post_id,
    p.title as post_title,
    p.slug as post_slug
FROM comments c
JOIN users u ON c.user_id = u.id
LEFT JOIN posts p ON c.expanded_to_post_id = p.id
WHERE c.expanded_to_post_id IS NOT NULL;

-- View: posts_from_comments
-- Shows all posts that were created from comments
CREATE VIEW IF NOT EXISTS posts_from_comments AS
SELECT
    p.id as post_id,
    p.title,
    p.slug,
    p.source_comment_id,
    c.id as comment_id,
    c.content as source_comment,
    u.username as original_commenter
FROM posts p
JOIN comments c ON p.source_comment_id = c.id
JOIN users u ON c.user_id = u.id
WHERE p.source_comment_id IS NOT NULL;

-- View: content_genealogy
-- Shows the full lineage of comment→post→comment→post
CREATE VIEW IF NOT EXISTS content_genealogy AS
WITH RECURSIVE genealogy AS (
    -- Base case: original posts (not from comments)
    SELECT
        p.id as post_id,
        p.title,
        p.slug,
        p.source_comment_id,
        0 as generation,
        p.id as root_post_id
    FROM posts p
    WHERE p.source_comment_id IS NULL

    UNION ALL

    -- Recursive case: posts created from comments
    SELECT
        p.id as post_id,
        p.title,
        p.slug,
        p.source_comment_id,
        g.generation + 1,
        g.root_post_id
    FROM posts p
    JOIN comments c ON p.source_comment_id = c.id
    JOIN genealogy g ON c.post_id = g.post_id
)
SELECT * FROM genealogy
ORDER BY root_post_id, generation;

-- =============================================================================
-- TRIGGERS for data integrity
-- =============================================================================

-- Trigger: prevent_circular_expansion
-- Prevents a comment from being expanded multiple times
-- (Though we allow this in code, this is a safety check)
CREATE TRIGGER IF NOT EXISTS prevent_double_expansion
BEFORE UPDATE ON comments
WHEN NEW.expanded_to_post_id IS NOT NULL
AND OLD.expanded_to_post_id IS NOT NULL
AND NEW.expanded_to_post_id != OLD.expanded_to_post_id
BEGIN
    SELECT RAISE(ABORT, 'Comment already expanded to a different post');
END;

-- Trigger: auto_update_expansion_timestamp
-- Update a timestamp when comment is expanded (if we add that field later)
-- For now, just a placeholder

-- =============================================================================
-- SAMPLE QUERIES
-- =============================================================================

-- Query 1: Find unexpanded AI comments (ready for expansion)
-- SELECT c.id, c.content, u.username, LENGTH(c.content) as length
-- FROM comments c
-- JOIN users u ON c.user_id = u.id
-- WHERE LENGTH(c.content) > 200
-- AND u.is_ai_persona = 1
-- AND c.expanded_to_post_id IS NULL
-- ORDER BY LENGTH(c.content) DESC;

-- Query 2: Show content generation chain
-- SELECT * FROM content_genealogy
-- WHERE generation > 0
-- ORDER BY generation DESC;

-- Query 3: Top quality expansions
-- SELECT * FROM expanded_comments
-- WHERE expansion_quality > 0.7
-- ORDER BY expansion_quality DESC
-- LIMIT 10;

-- Query 4: Find posts that need AI comments
-- SELECT p.id, p.title,
--        (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
-- FROM posts p
-- WHERE published_at IS NOT NULL
-- HAVING comment_count = 0
-- ORDER BY published_at DESC
-- LIMIT 10;

-- =============================================================================
-- CLEANUP (if needed)
-- =============================================================================

-- To revert this migration:
--
-- DROP VIEW IF EXISTS content_genealogy;
-- DROP VIEW IF EXISTS posts_from_comments;
-- DROP VIEW IF EXISTS expanded_comments;
-- DROP INDEX IF EXISTS idx_comments_quality;
-- DROP INDEX IF EXISTS idx_posts_source;
-- DROP INDEX IF EXISTS idx_comments_expansion;
-- DROP TRIGGER IF EXISTS prevent_double_expansion;
--
-- ALTER TABLE comments DROP COLUMN expanded_to_post_id;
-- ALTER TABLE comments DROP COLUMN expansion_quality;
-- ALTER TABLE posts DROP COLUMN source_comment_id;
--
-- Note: SQLite doesn't support DROP COLUMN directly.
-- You'd need to recreate the tables without those columns.

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify migration was successful:
--
-- Check comments table:
-- PRAGMA table_info(comments);
--
-- Check posts table:
-- PRAGMA table_info(posts);
--
-- Check indexes:
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='comments';
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='posts';
--
-- Check views:
-- SELECT name FROM sqlite_master WHERE type='view';

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================

-- Migration complete!
--
-- Next steps:
-- 1. Run: python3 comment_to_post.py check
-- 2. Expand comments: python3 comment_to_post.py auto
-- 3. View results: SELECT * FROM expanded_comments;
