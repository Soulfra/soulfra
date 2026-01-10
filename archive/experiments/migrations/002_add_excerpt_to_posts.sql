-- Migration 002: Add Excerpt Field to Posts
-- Adds excerpt field for post previews on homepage and feeds

ALTER TABLE posts ADD COLUMN excerpt TEXT;
