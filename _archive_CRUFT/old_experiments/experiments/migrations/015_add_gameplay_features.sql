-- Migration: Add Gameplay Features
-- Date: 2025-12-24
-- Description: Emoji reactions, color challenges, and seasons system

-- ==================== PLOT REACTIONS (Emoji System) ====================
CREATE TABLE IF NOT EXISTS plot_reactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plot_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  emoji TEXT NOT NULL CHECK(emoji IN ('🔥', '💯', '😂', '👀', '❤️', '⭐', '🎯', '👏')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(plot_id, user_id, emoji)  -- One emoji type per user per plot
);

CREATE INDEX IF NOT EXISTS idx_plot_reactions_plot ON plot_reactions(plot_id);
CREATE INDEX IF NOT EXISTS idx_plot_reactions_user ON plot_reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_plot_reactions_emoji ON plot_reactions(emoji);

-- ==================== COLOR CHALLENGES ====================
CREATE TABLE IF NOT EXISTS color_challenges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  challenge_date DATE NOT NULL UNIQUE,
  target_mood TEXT NOT NULL,  -- e.g., "energetic", "calm", "mysterious"
  target_features JSON NOT NULL,  -- 12-element feature vector for comparison
  description TEXT NOT NULL,
  brand_slug TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (brand_slug) REFERENCES brands(slug) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_color_challenges_date ON color_challenges(challenge_date);
CREATE INDEX IF NOT EXISTS idx_color_challenges_brand ON color_challenges(brand_slug);

-- ==================== CHALLENGE SUBMISSIONS ====================
CREATE TABLE IF NOT EXISTS challenge_submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  challenge_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  plot_id INTEGER,  -- Optional: associate with a plot
  submitted_color TEXT NOT NULL,  -- hex color
  submitted_features JSON NOT NULL,  -- 12-element feature vector
  similarity_score REAL NOT NULL,  -- 0-100, how close to target
  reputation_earned INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (challenge_id) REFERENCES color_challenges(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE SET NULL,
  UNIQUE(challenge_id, user_id)  -- One submission per user per challenge
);

CREATE INDEX IF NOT EXISTS idx_challenge_submissions_challenge ON challenge_submissions(challenge_id);
CREATE INDEX IF NOT EXISTS idx_challenge_submissions_user ON challenge_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_submissions_score ON challenge_submissions(similarity_score DESC);

-- ==================== GAME SEASONS ====================
CREATE TABLE IF NOT EXISTS game_seasons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  season_number INTEGER NOT NULL,
  brand_slug TEXT NOT NULL,
  theme TEXT NOT NULL,  -- Season theme (e.g., "Winter Warriors", "Summer Showdown")
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  prize_pool TEXT,  -- Description of prizes
  winner_user_id INTEGER,
  status TEXT NOT NULL DEFAULT 'upcoming' CHECK(status IN ('upcoming', 'active', 'completed')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (brand_slug) REFERENCES brands(slug) ON DELETE CASCADE,
  FOREIGN KEY (winner_user_id) REFERENCES users(id) ON DELETE SET NULL,
  UNIQUE(season_number, brand_slug)
);

CREATE INDEX IF NOT EXISTS idx_game_seasons_brand ON game_seasons(brand_slug);
CREATE INDEX IF NOT EXISTS idx_game_seasons_status ON game_seasons(status);
CREATE INDEX IF NOT EXISTS idx_game_seasons_dates ON game_seasons(start_date, end_date);

-- ==================== SEASON RANKINGS ====================
CREATE TABLE IF NOT EXISTS season_rankings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  season_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  plot_id INTEGER,
  final_reputation INTEGER NOT NULL,
  final_rank INTEGER NOT NULL,
  prizes_won TEXT,  -- JSON array of prizes
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (season_id) REFERENCES game_seasons(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE SET NULL,
  UNIQUE(season_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_season_rankings_season ON season_rankings(season_id);
CREATE INDEX IF NOT EXISTS idx_season_rankings_rank ON season_rankings(final_rank);

-- Record migration
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('015', 'add_gameplay_features', CURRENT_TIMESTAMP);
