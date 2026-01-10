-- Migration: Character Aging System
-- Date: 2025-12-25
-- Description: Add character aging mechanics to D&D campaign

-- ==================== ADD CHARACTER AGE TO USERS ====================
-- Track character's age (starts at 20, increases with quests)
ALTER TABLE users ADD COLUMN character_age INTEGER DEFAULT 20;

-- Track total years aged through gameplay
ALTER TABLE users ADD COLUMN total_years_aged INTEGER DEFAULT 0;

-- ==================== ADD AGING TO QUESTS ====================
-- Each quest ages your character by X years
ALTER TABLE quests ADD COLUMN aging_years INTEGER DEFAULT 0;

-- Update existing quests with aging values
UPDATE quests SET aging_years = 2 WHERE quest_slug = 'welcome_to_adventure';  -- Easy quest: 2 years
UPDATE quests SET aging_years = 5 WHERE quest_slug = 'goblin_caves';  -- Medium quest: 5 years
UPDATE quests SET aging_years = 10 WHERE quest_slug = 'dragon_slayer';  -- Legendary quest: 10 years
UPDATE quests SET aging_years = 7 WHERE quest_slug = 'lost_temple';  -- Hard quest: 7 years

-- ==================== TRACK ATTRIBUTE SNAPSHOTS ====================
-- Store character attributes at different ages (for history/replay)
CREATE TABLE IF NOT EXISTS character_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  age INTEGER NOT NULL,
  agility REAL NOT NULL,
  wisdom REAL NOT NULL,
  strength REAL NOT NULL,
  charisma REAL NOT NULL,
  intelligence REAL NOT NULL,
  constitution REAL NOT NULL,
  snapshot_reason TEXT,  -- 'quest_complete', 'level_up', 'item_equip'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_character_snapshots_user ON character_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_character_snapshots_age ON character_snapshots(user_id, age);

-- ==================== AGING MILESTONES ====================
-- Track major life events in character's aging journey
CREATE TABLE IF NOT EXISTS aging_milestones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  age_reached INTEGER NOT NULL,
  milestone_type TEXT NOT NULL,  -- 'peak_agility', 'wisdom_unlock', 'strength_decline'
  title TEXT NOT NULL,
  description TEXT,
  unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_aging_milestones_user ON aging_milestones(user_id);

-- ==================== SEED AGING MILESTONES ====================
-- Create milestone templates that trigger at certain ages
INSERT OR IGNORE INTO aging_milestones (user_id, age_reached, milestone_type, title, description)
SELECT id, 25, 'peak_agility', 'Peak Physical Condition', 'Your agility reaches its maximum potential!'
FROM users WHERE character_age < 25;

INSERT OR IGNORE INTO aging_milestones (user_id, age_reached, milestone_type, title, description)
SELECT id, 40, 'wisdom_unlock', 'Sage Wisdom', 'Years of experience grant you profound wisdom.'
FROM users WHERE character_age < 40;

INSERT OR IGNORE INTO aging_milestones (user_id, age_reached, milestone_type, title, description)
SELECT id, 50, 'strength_decline', 'Waning Strength', 'Your body begins to show its age, but your mind is sharper than ever.'
FROM users WHERE character_age < 50;

-- ==================== RECORD MIGRATION ====================
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('023', 'character_aging_system', CURRENT_TIMESTAMP);
