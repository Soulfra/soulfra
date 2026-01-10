-- Migration: Add Referral System
-- Date: 2025-12-24
-- Description: QR-based referral system with bonus points

-- ==================== REFERRALS TABLE ====================
CREATE TABLE IF NOT EXISTS referrals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  referrer_user_id INTEGER NOT NULL,
  referred_user_id INTEGER,
  referral_code TEXT UNIQUE NOT NULL,
  bonus_awarded BOOLEAN DEFAULT 0,
  referrer_bonus INTEGER DEFAULT 50,
  referred_bonus INTEGER DEFAULT 25,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  accepted_at TIMESTAMP,
  
  FOREIGN KEY (referrer_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (referred_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Index for fast lookups by code
CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code);

-- Index for user referral stats
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_user_id);

-- Record migration
INSERT INTO schema_migrations (version, name, applied_at)
VALUES ('014', 'add_referrals_system', CURRENT_TIMESTAMP);
