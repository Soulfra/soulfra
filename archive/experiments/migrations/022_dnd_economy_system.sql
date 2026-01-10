-- Migration: D&D Economy System (Stripe Memberships + In-Game Trading)
-- Date: 2025-12-25
-- Description: Add Stripe memberships, inventory, items, trading, and quests for D&D campaign

-- ==================== STRIPE MEMBERSHIPS ====================
CREATE TABLE IF NOT EXISTS memberships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  stripe_customer_id TEXT UNIQUE,
  tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free', 'premium', 'pro')),
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'expired', 'trialing')),
  stripe_subscription_id TEXT,
  current_period_end TIMESTAMP,
  cancel_at_period_end BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_stripe_customer ON memberships(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_memberships_status ON memberships(status);

-- ==================== ITEM DEFINITIONS ====================
-- Master list of all items that can be earned/traded
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  rarity TEXT NOT NULL CHECK(rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')),
  item_type TEXT NOT NULL CHECK(item_type IN ('weapon', 'armor', 'potion', 'scroll', 'material', 'quest_item')),
  earnable_by TEXT DEFAULT 'quest,battle,achievement',  -- Comma-separated
  tradeable BOOLEAN DEFAULT 1,
  stats TEXT,  -- JSON: {"damage": 10, "defense": 5, "magic": 3}
  required_level INTEGER DEFAULT 1,
  image_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type);

-- ==================== PLAYER INVENTORY ====================
-- Items owned by players
CREATE TABLE IF NOT EXISTS inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  quantity INTEGER DEFAULT 1,
  equipped BOOLEAN DEFAULT 0,
  earned_from TEXT,  -- 'quest:dragon_slayer', 'battle:goblin', 'trade:user_5'
  earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT,  -- JSON for item-specific data (enchantments, durability, etc.)

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_item ON inventory(item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_equipped ON inventory(user_id, equipped);

-- ==================== TRADING SYSTEM ====================
-- Player-to-player item trades
CREATE TABLE IF NOT EXISTS trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_user_id INTEGER NOT NULL,
  to_user_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'cancelled', 'completed')),
  offered_items TEXT NOT NULL,  -- JSON: [{"item_id": 1, "quantity": 2}, ...]
  requested_items TEXT NOT NULL,  -- JSON: [{"item_id": 3, "quantity": 1}, ...]
  message TEXT,  -- Optional message from trader
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  responded_at TIMESTAMP,
  completed_at TIMESTAMP,

  FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trades_from_user ON trades(from_user_id);
CREATE INDEX IF NOT EXISTS idx_trades_to_user ON trades(to_user_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);

-- Trade limits (enforce membership tiers)
CREATE TABLE IF NOT EXISTS trade_limits (
  user_id INTEGER PRIMARY KEY,
  trades_today INTEGER DEFAULT 0,
  last_trade_date DATE DEFAULT CURRENT_DATE,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== QUEST SYSTEM ====================
-- D&D campaign quests
CREATE TABLE IF NOT EXISTS quests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quest_slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  story TEXT,  -- Full quest narrative
  difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard', 'epic', 'legendary')),
  required_level INTEGER DEFAULT 1,
  required_items TEXT,  -- JSON: [item_id1, item_id2] (optional prerequisites)
  campaign_slug TEXT NOT NULL,  -- Which game/campaign this belongs to
  rewards TEXT NOT NULL,  -- JSON: {"items": [{"id": 1, "quantity": 2}], "reputation": 100, "xp": 50}
  max_party_size INTEGER DEFAULT 4,
  estimated_time_minutes INTEGER DEFAULT 30,
  is_repeatable BOOLEAN DEFAULT 0,
  active BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quests_campaign ON quests(campaign_slug);
CREATE INDEX IF NOT EXISTS idx_quests_difficulty ON quests(difficulty);
CREATE INDEX IF NOT EXISTS idx_quests_active ON quests(active);

-- Quest progress tracking
CREATE TABLE IF NOT EXISTS quest_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  quest_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed', 'failed', 'abandoned')),
  party_members TEXT,  -- JSON: [user_id1, user_id2] if multiplayer
  progress_data TEXT,  -- JSON: quest-specific progress (enemies defeated, items collected, etc.)
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (quest_id) REFERENCES quests(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quest_progress_user ON quest_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_quest_progress_quest ON quest_progress(quest_id);
CREATE INDEX IF NOT EXISTS idx_quest_progress_status ON quest_progress(user_id, status);

-- ==================== SEED FREE MEMBERSHIPS FOR EXISTING USERS ====================
-- Give all existing users free tier membership
INSERT OR IGNORE INTO memberships (user_id, tier, status)
SELECT id, 'free', 'active' FROM users;

-- ==================== SEED STARTER ITEMS ====================
-- Basic items that can be earned in the game
INSERT OR IGNORE INTO items (name, description, rarity, item_type, stats)
VALUES
  -- Weapons
  ('Wooden Sword', 'A basic training sword. Better than nothing!', 'common', 'weapon', '{"damage": 5, "durability": 50}'),
  ('Steel Sword', 'A reliable weapon for any adventurer.', 'uncommon', 'weapon', '{"damage": 15, "durability": 100}'),
  ('Dragon Slayer', 'Forged from dragon scales. Legends tell of its power.', 'legendary', 'weapon', '{"damage": 50, "fire_damage": 25, "durability": 300}'),

  -- Armor
  ('Leather Armor', 'Light armor for quick movement.', 'common', 'armor', '{"defense": 8, "weight": 10}'),
  ('Plate Armor', 'Heavy protection at the cost of mobility.', 'rare', 'armor', '{"defense": 35, "weight": 50}'),

  -- Potions
  ('Health Potion', 'Restores 50 HP instantly.', 'common', 'potion', '{"heal": 50}'),
  ('Greater Health Potion', 'Restores 150 HP instantly.', 'uncommon', 'potion', '{"heal": 150}'),
  ('Mana Potion', 'Restores 30 mana for spellcasting.', 'common', 'potion', '{"mana": 30}'),

  -- Scrolls
  ('Fireball Scroll', 'Cast a powerful fireball. Single use.', 'uncommon', 'scroll', '{"damage": 40, "aoe": 3}'),
  ('Teleport Scroll', 'Instantly teleport to a safe location.', 'rare', 'scroll', '{"range": "unlimited"}'),

  -- Materials
  ('Dragon Scale', 'Rare crafting material from dragons.', 'epic', 'material', '{"crafting_bonus": 20}'),
  ('Iron Ore', 'Basic crafting material.', 'common', 'material', '{"crafting_bonus": 5}'),

  -- Quest Items
  ('Ancient Key', 'Opens the gate to the Dragon''s Lair.', 'quest_item', 'quest_item', '{"opens": "dragon_lair"}');

-- ==================== SEED STARTER QUESTS ====================
-- D&D campaign quests
INSERT OR IGNORE INTO quests (quest_slug, name, description, story, difficulty, required_level, campaign_slug, rewards)
VALUES
  (
    'welcome_to_adventure',
    'Welcome to Adventure',
    'Learn the basics of questing and combat.',
    'The village elder needs your help! A pack of goblins has been stealing from the farms. Prove your worth by defeating them.',
    'easy',
    1,
    'dnd',
    '{"items": [{"id": 1, "quantity": 1}, {"id": 6, "quantity": 2}], "reputation": 10, "xp": 25}'
  ),
  (
    'goblin_caves',
    'Clear the Goblin Caves',
    'The goblins have a hideout in nearby caves. Clear them out!',
    'Following the goblin trail, you discover their cave hideout. The stench is overwhelming. You hear chittering voices deeper inside...',
    'medium',
    3,
    'dnd',
    '{"items": [{"id": 2, "quantity": 1}, {"id": 7, "quantity": 1}, {"id": 12, "quantity": 3}], "reputation": 50, "xp": 100}'
  ),
  (
    'dragon_slayer',
    'Slay the Ancient Dragon',
    'An ancient dragon terrorizes the kingdom. Only the bravest can face it.',
    'The dragon''s roar shakes the mountains. Its scales shimmer like molten gold. Legends say it guards a treasure hoard beyond imagination. Are you ready?',
    'legendary',
    10,
    'dnd',
    '{"items": [{"id": 3, "quantity": 1}, {"id": 11, "quantity": 5}, {"id": 10, "quantity": 1}], "reputation": 500, "xp": 1000}'
  ),
  (
    'lost_temple',
    'Explore the Lost Temple',
    'An ancient temple has been discovered in the jungle. What secrets does it hold?',
    'Vines cover crumbling stone walls. Strange symbols glow faintly in the darkness. You hear whispers... or is it just the wind?',
    'hard',
    7,
    'dnd',
    '{"items": [{"id": 5, "quantity": 1}, {"id": 9, "quantity": 2}, {"id": 13, "quantity": 1}], "reputation": 200, "xp": 400}'
  );

-- ==================== RECORD MIGRATION ====================
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('022', 'dnd_economy_system', CURRENT_TIMESTAMP);
