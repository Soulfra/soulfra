#!/usr/bin/env python3
"""
QR Time Capsule - Track scan journey

Each QR code becomes a living artifact that tracks:
- Who scanned it
- When and where
- Chain of scans (like a physical object moving through space)
- Device and referrer

This creates a "time capsule" effect showing the QR's journey.
"""

from database import get_db


def init_qr_tracking():
    """Create tables for QR time capsule tracking"""
    db = get_db()
    
    # QR codes table (if doesn't exist from url_shortener)
    db.execute('''
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
        )
    ''')
    
    # Scan tracking table
    db.execute('''
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
        )
    ''')
    
    # Indexes for fast lookups
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_qr_scans_code
        ON qr_scans(qr_code_id, scanned_at DESC)
    ''')
    
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_qr_scans_chain
        ON qr_scans(previous_scan_id)
    ''')
    
    db.commit()
    db.close()
    
    print("✅ QR time capsule tables created")
    print("   • qr_codes - tracks QR code metadata")
    print("   • qr_scans - tracks each scan with chain links")


if __name__ == '__main__':
    init_qr_tracking()
