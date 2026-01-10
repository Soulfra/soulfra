-- Migration: Add Encrypted Columns to Database
-- Date: 2026-01-09
-- Purpose: Add encrypted versions of sensitive fields for AES-256-GCM encryption

-- This migration adds new encrypted columns while preserving existing plaintext columns.
-- After encrypting data, you can optionally drop plaintext columns (BACKUP FIRST!)

BEGIN TRANSACTION;

-- =====================================================
-- 1. soulfra_master_users - Add encrypted email
-- =====================================================

-- Check if column exists (SQLite doesn't have IF NOT EXISTS for columns)
-- Run this migration only once

-- Add encrypted email column
ALTER TABLE soulfra_master_users
ADD COLUMN email_encrypted TEXT DEFAULT NULL;

-- Create index on encrypted email (for lookups)
CREATE INDEX IF NOT EXISTS idx_soulfra_master_users_email_encrypted
ON soulfra_master_users(email_encrypted);

-- =====================================================
-- 2. professionals - Add encrypted phone and email
-- =====================================================

-- Add encrypted phone column
ALTER TABLE professionals
ADD COLUMN phone_encrypted TEXT DEFAULT NULL;

-- Add encrypted email column
ALTER TABLE professionals
ADD COLUMN email_encrypted TEXT DEFAULT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_professionals_phone_encrypted
ON professionals(phone_encrypted);

CREATE INDEX IF NOT EXISTS idx_professionals_email_encrypted
ON professionals(email_encrypted);

-- =====================================================
-- 3. messages - Add encrypted content
-- =====================================================

-- Add encrypted content column
ALTER TABLE messages
ADD COLUMN content_encrypted TEXT DEFAULT NULL;

-- Create index (for searching encrypted messages)
CREATE INDEX IF NOT EXISTS idx_messages_content_encrypted
ON messages(content_encrypted);

-- =====================================================
-- 4. users - Add encrypted email (if table exists)
-- =====================================================

-- Check if users table exists first
-- SQLite will error if table doesn't exist, so wrap in a conditional

-- Add encrypted email column
-- Uncomment if you have a 'users' table separate from soulfra_master_users
-- ALTER TABLE users
-- ADD COLUMN email_encrypted TEXT DEFAULT NULL;

-- CREATE INDEX IF NOT EXISTS idx_users_email_encrypted
-- ON users(email_encrypted);

-- =====================================================
-- 5. sessions - Add encrypted session tokens
-- =====================================================

-- If you have a sessions table with tokens
-- ALTER TABLE sessions
-- ADD COLUMN session_token_encrypted TEXT DEFAULT NULL;

-- CREATE INDEX IF NOT EXISTS idx_sessions_token_encrypted
-- ON sessions(session_token_encrypted);

-- =====================================================
-- 6. Create encryption metadata table
-- =====================================================

-- Track which tables/columns are encrypted and when
CREATE TABLE IF NOT EXISTS encryption_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    encrypted_column_name TEXT NOT NULL,
    encryption_algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    encrypted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    encryption_key_id TEXT DEFAULT NULL,  -- Reference to which key was used
    is_active BOOLEAN DEFAULT 1,  -- Whether encryption is currently active
    UNIQUE(table_name, column_name)
);

-- Insert metadata for encrypted columns
INSERT OR REPLACE INTO encryption_metadata (table_name, column_name, encrypted_column_name, encryption_algorithm)
VALUES
    ('soulfra_master_users', 'email', 'email_encrypted', 'AES-256-GCM'),
    ('professionals', 'phone', 'phone_encrypted', 'AES-256-GCM'),
    ('professionals', 'email', 'email_encrypted', 'AES-256-GCM'),
    ('messages', 'content', 'content_encrypted', 'AES-256-GCM');

-- =====================================================
-- 7. Create audit log for encrypted field access
-- =====================================================

CREATE TABLE IF NOT EXISTS encryption_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'encrypt', 'decrypt', 'read'
    user_id INTEGER,
    ip_address TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 1
);

-- Create index for audit log queries
CREATE INDEX IF NOT EXISTS idx_encryption_audit_log_timestamp
ON encryption_audit_log(accessed_at);

CREATE INDEX IF NOT EXISTS idx_encryption_audit_log_user
ON encryption_audit_log(user_id);

-- =====================================================
-- 8. Verification queries
-- =====================================================

-- To verify migration succeeded, run:
-- SELECT name, type FROM sqlite_master WHERE tbl_name IN ('soulfra_master_users', 'professionals', 'messages') AND type='table';
-- PRAGMA table_info(soulfra_master_users);
-- PRAGMA table_info(professionals);
-- PRAGMA table_info(messages);
-- SELECT * FROM encryption_metadata;

COMMIT;

-- =====================================================
-- Post-Migration Steps
-- =====================================================

-- After running this migration:
--
-- 1. Verify columns were added:
--    sqlite3 soulfra.db "PRAGMA table_info(soulfra_master_users);"
--
-- 2. Encrypt existing data:
--    python3 database_encryption.py --encrypt
--
-- 3. Verify encryption:
--    python3 database_encryption.py --test
--
-- 4. Update application code to use encrypted columns
--
-- 5. (OPTIONAL) Drop plaintext columns after backing up:
--    -- BACKUP DATABASE FIRST!
--    -- ALTER TABLE soulfra_master_users DROP COLUMN email;
--    -- ALTER TABLE professionals DROP COLUMN phone;
--    -- ALTER TABLE professionals DROP COLUMN email;
--    -- ALTER TABLE messages DROP COLUMN content;
--    -- (Note: SQLite doesn't support DROP COLUMN directly,
--    --  requires table recreation)

-- =====================================================
-- Rollback (if needed)
-- =====================================================

-- To rollback this migration (CAREFUL!):
--
-- BEGIN TRANSACTION;
-- ALTER TABLE soulfra_master_users DROP COLUMN email_encrypted;
-- ALTER TABLE professionals DROP COLUMN phone_encrypted;
-- ALTER TABLE professionals DROP COLUMN email_encrypted;
-- ALTER TABLE messages DROP COLUMN content_encrypted;
-- DROP TABLE encryption_metadata;
-- DROP TABLE encryption_audit_log;
-- COMMIT;
--
-- (Note: SQLite requires table recreation to drop columns)
