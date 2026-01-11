-- Migration: Add Template Versioning System
-- Date: 2025-12-23
-- Description: Track template versions with changelogs, tests, and domain rotation contexts

-- ==================== TEMPLATE VERSIONS ====================
-- Track versions of each template similar to brand_versions
CREATE TABLE IF NOT EXISTS template_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_name TEXT NOT NULL,        -- 'signup', 'leaderboard', 'news_feed'
  version_number TEXT NOT NULL,       -- 'v1', 'v2', 'v3'
  ship_class TEXT NOT NULL,           -- 'dinghy', 'schooner', 'frigate', 'galleon'
  file_path TEXT NOT NULL,            -- 'templates/signup/v1_dinghy.html'
  changelog TEXT,                     -- Markdown changelog of what changed
  line_count INTEGER,                 -- Number of lines in template
  active BOOLEAN DEFAULT 1,           -- Is this version currently in use?
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,                    -- Who created this version

  UNIQUE(template_name, version_number)
);

-- Index for fast lookups of active templates
CREATE INDEX IF NOT EXISTS idx_template_versions_active
ON template_versions(template_name, active);

-- ==================== TEMPLATE TESTS ====================
-- Store test results for each template version
CREATE TABLE IF NOT EXISTS template_tests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_version_id INTEGER NOT NULL,
  test_name TEXT NOT NULL,            -- 'test_renders_without_error', 'test_has_submit_button'
  test_file TEXT NOT NULL,            -- 'tests/templates/signup/v1_dinghy_test.py'
  status TEXT NOT NULL,               -- 'pass', 'fail', 'pending'
  error_message TEXT,                 -- If failed, what was the error?
  run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (template_version_id) REFERENCES template_versions(id) ON DELETE CASCADE
);

-- Index for getting latest test results per template version
CREATE INDEX IF NOT EXISTS idx_template_tests_version
ON template_tests(template_version_id, run_at DESC);

-- ==================== DOMAIN CONTEXTS ====================
-- Rotating questions, themes, profiles for each domain
CREATE TABLE IF NOT EXISTS domain_contexts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain_slug TEXT NOT NULL,          -- 'ocean-dreams', 'cringeproof', 'soulfra'
  context_type TEXT NOT NULL,         -- 'question', 'theme', 'profile', 'style'
  content TEXT NOT NULL,              -- The actual question/theme/profile data
  rotation_order INTEGER DEFAULT 0,   -- Order in rotation cycle (1, 2, 3...)
  active BOOLEAN DEFAULT 1,           -- Is this context available for rotation?
  metadata TEXT,                      -- JSON with extra context data
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Multiple contexts of same type can exist for rotation
  UNIQUE(domain_slug, context_type, rotation_order)
);

-- Index for fast rotation lookups
CREATE INDEX IF NOT EXISTS idx_domain_contexts_rotation
ON domain_contexts(domain_slug, context_type, active, rotation_order);

-- ==================== DOMAIN ROTATION STATE ====================
-- Track current position in rotation for each domain
CREATE TABLE IF NOT EXISTS domain_rotation_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain_slug TEXT NOT NULL UNIQUE,   -- 'ocean-dreams', 'cringeproof'
  current_question_index INTEGER DEFAULT 0,
  current_theme_index INTEGER DEFAULT 0,
  current_profile_index INTEGER DEFAULT 0,
  last_rotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  rotation_interval_hours INTEGER DEFAULT 24  -- How often to rotate
);

-- ==================== SEED DATA ====================
-- Add initial template versions for existing templates
INSERT OR IGNORE INTO template_versions
  (template_name, version_number, ship_class, file_path, changelog, active)
VALUES
  ('signup', 'v1', 'dinghy', 'templates/signup/v1_dinghy.html', '## v1 - Initial Version\n- Basic signup form\n- Username, email, password fields', 1),
  ('leaderboard', 'v1', 'dinghy', 'templates/leaderboard/v1_dinghy.html', '## v1 - Initial Version\n- Simple reputation rankings\n- Top 10 users', 1),
  ('news_feed', 'v1', 'dinghy', 'templates/news_feed/v1_dinghy.html', '## v1 - Initial Version\n- Basic news list\n- Chronological ordering', 1);

-- Add domain rotation states for existing domains
INSERT OR IGNORE INTO domain_rotation_state
  (domain_slug, current_question_index, current_theme_index, current_profile_index)
VALUES
  ('ocean-dreams', 0, 0, 0),
  ('cringeproof', 0, 0, 0),
  ('soulfra', 0, 0, 0);

-- Add sample rotating contexts for ocean-dreams
INSERT OR IGNORE INTO domain_contexts
  (domain_slug, context_type, content, rotation_order, active)
VALUES
  ('ocean-dreams', 'question', 'What would you build if you had unlimited time?', 1, 1),
  ('ocean-dreams', 'question', 'What creative project have you been putting off?', 2, 1),
  ('ocean-dreams', 'question', 'What skill do you wish you had more time to learn?', 3, 1),
  ('ocean-dreams', 'theme', 'ocean', 1, 1),
  ('ocean-dreams', 'theme', 'sunset', 2, 1),
  ('ocean-dreams', 'theme', 'starlight', 3, 1);

-- Add sample rotating contexts for cringeproof
INSERT OR IGNORE INTO domain_contexts
  (domain_slug, context_type, content, rotation_order, active)
VALUES
  ('cringeproof', 'question', 'What town are you defending today?', 1, 1),
  ('cringeproof', 'question', 'Ready to claim your reputation points?', 2, 1),
  ('cringeproof', 'question', 'What challenge will you tackle next?', 3, 1),
  ('cringeproof', 'theme', 'game', 1, 1),
  ('cringeproof', 'theme', 'competition', 2, 1),
  ('cringeproof', 'theme', 'victory', 3, 1);

-- Record migration
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('012', 'add_template_versioning', CURRENT_TIMESTAMP);
