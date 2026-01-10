-- Token Purchase System - Database Migration
-- Run this to add token purchase tracking to soulfra.db

-- Create purchases table for transaction history
CREATE TABLE IF NOT EXISTS purchases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('subscription', 'tokens', 'one_time')),
  amount REAL NOT NULL,  -- dollars (e.g., 10.00)
  tokens INTEGER,  -- token count if type='tokens'
  description TEXT,  -- e.g., "100 tokens", "Premium upgrade"
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_checkout_session_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed', 'refunded')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create index for faster queries by user
CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);

-- Add token balance to users table (if not exists)
-- This is a computed field that sums all token purchases
ALTER TABLE users ADD COLUMN token_balance INTEGER DEFAULT 0;

-- Create token_usage table to track spending
CREATE TABLE IF NOT EXISTS token_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  tokens_spent INTEGER NOT NULL,
  action TEXT NOT NULL,  -- 'import_domain', 'ai_analysis', 'export_data', etc.
  metadata TEXT,  -- JSON with additional context
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id);

-- Add test flag to brands table
ALTER TABLE brands ADD COLUMN is_test BOOLEAN DEFAULT 0;

-- Update existing brands to mark test domains
-- (Will be 0 for all real domains initially)
UPDATE brands SET is_test = 0 WHERE is_test IS NULL;

-- Example: Mark any test domains that exist
-- UPDATE brands SET is_test = 1 WHERE domain LIKE 'test%';
-- UPDATE brands SET is_test = 1 WHERE domain IN ('simpledinner.org', 'websolutions.io');
