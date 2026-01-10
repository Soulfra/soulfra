-- Migration 004: Add QR Code Tracking
-- From init_qr_tracking.py
--
-- Creates:
-- - qr_codes (QR code metadata)
-- - qr_scans (scan tracking with chain links)

-- QR codes table
CREATE TABLE IF NOT EXISTS qr_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_type TEXT NOT NULL,
    code_data TEXT NOT NULL,
    target_url TEXT NOT NULL,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_scans INTEGER DEFAULT 0,
    last_scanned_at TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Scan tracking table
CREATE TABLE IF NOT EXISTS qr_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_code_id INTEGER NOT NULL,
    scanned_by_name TEXT,
    scanned_by_email TEXT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    location_city TEXT,
    location_country TEXT,
    device_type TEXT,
    user_agent TEXT,
    referrer TEXT,
    previous_scan_id INTEGER,
    FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id),
    FOREIGN KEY (previous_scan_id) REFERENCES qr_scans(id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_qr_scans_code ON qr_scans(qr_code_id, scanned_at DESC);
CREATE INDEX IF NOT EXISTS idx_qr_scans_chain ON qr_scans(previous_scan_id);
