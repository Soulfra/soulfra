-- Migration: Add Game Brands and Plots System
-- Date: 2025-12-23
-- Description: Add brand types (blog/game/community) and plots/community system

-- ==================== ADD BRAND TYPE ====================
-- Add brand_type column to distinguish game brands from blog brands
ALTER TABLE brands ADD COLUMN brand_type TEXT DEFAULT 'blog' CHECK(brand_type IN ('blog', 'game', 'community'));

-- Add emoji for game branding
ALTER TABLE brands ADD COLUMN emoji TEXT;

-- ==================== PLOTS/COMMUNITY SYSTEM ====================
-- Plots are user-owned spaces in the game world
CREATE TABLE IF NOT EXISTS plots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NOT NULL,
  town_name TEXT NOT NULL,
  plot_coordinates TEXT,              -- JSON: {"x": 10, "y": 5} or null
  qr_code TEXT UNIQUE NOT NULL,       -- Generated QR code for this plot
  reputation_points INTEGER DEFAULT 0,
  brand_slug TEXT NOT NULL,           -- Which game this plot belongs to
  metadata TEXT,                      -- JSON for extra game-specific data
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for fast lookups by owner
CREATE INDEX IF NOT EXISTS idx_plots_owner ON plots(owner_user_id);

-- Index for brand-specific queries
CREATE INDEX IF NOT EXISTS idx_plots_brand ON plots(brand_slug);

-- Index for QR code lookups
CREATE INDEX IF NOT EXISTS idx_plots_qr ON plots(qr_code);

-- ==================== PLOT ACTIVITIES ====================
-- Track activities/events that happen on plots
CREATE TABLE IF NOT EXISTS plot_activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plot_id INTEGER NOT NULL,
  activity_type TEXT NOT NULL,        -- 'build', 'defend', 'visit', 'trade', etc.
  description TEXT,
  reputation_change INTEGER DEFAULT 0,
  metadata TEXT,                      -- JSON for activity-specific data
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE
);

-- Index for plot timeline
CREATE INDEX IF NOT EXISTS idx_plot_activities_plot ON plot_activities(plot_id, created_at DESC);

-- ==================== UPDATE EXISTING BRANDS ====================
-- Mark ocean-dreams as a game brand
UPDATE brands SET brand_type = 'game', emoji = '🌊' WHERE slug = 'ocean-dreams';

-- ==================== SEED CRINGEPROOF BRAND ====================
INSERT OR IGNORE INTO brands (name, slug, brand_type, emoji, colors, personality, brand_values, tone, target_audience)
VALUES (
  'Cringeproof',
  'cringeproof',
  'game',
  '🎮',
  '["#FF6B6B", "#4ECDC4", "#FFE66D"]',
  'Competitive, playful, community-driven',
  '["competition", "creativity", "community"]',
  'Energetic and motivating',
  'Gamers and community builders'
);

-- ==================== SEED ROTATION CONTEXTS FOR CRINGEPROOF ====================
-- Add rotation state
INSERT OR IGNORE INTO domain_rotation_state
  (domain_slug, current_question_index, current_theme_index, current_profile_index)
VALUES
  ('cringeproof', 1, 1, 0);

-- Add rotating questions
INSERT OR IGNORE INTO domain_contexts
  (domain_slug, context_type, content, rotation_order, active)
VALUES
  ('cringeproof', 'question', 'What town are you defending today?', 1, 1),
  ('cringeproof', 'question', 'Ready to claim your reputation points?', 2, 1),
  ('cringeproof', 'question', 'What will you build in your plot?', 3, 1),
  ('cringeproof', 'question', 'Which challenge will you tackle next?', 4, 1);

-- Add rotating themes
INSERT OR IGNORE INTO domain_contexts
  (domain_slug, context_type, content, rotation_order, active)
VALUES
  ('cringeproof', 'theme', 'competition', 1, 1),
  ('cringeproof', 'theme', 'victory', 2, 1),
  ('cringeproof', 'theme', 'builder', 3, 1),
  ('cringeproof', 'theme', 'defender', 4, 1);

-- Record migration
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('013', 'add_game_brands_and_plots', CURRENT_TIMESTAMP);
