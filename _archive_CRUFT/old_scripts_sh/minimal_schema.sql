-- Minimal CringeProof Database Schema
-- Clean start with only essential tables for customer export

-- Users table (simplified)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscribers table
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    confirmed BOOLEAN DEFAULT 0,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- QR codes table
CREATE TABLE IF NOT EXISTS qr_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    destination_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- QR scans table (customer tracking)
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
    FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id)
);

-- Products table (UPC tracking)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upc TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    qr_code_id INTEGER,
    scan_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id)
);

-- Product scans table (detailed tracking)
CREATE TABLE IF NOT EXISTS product_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    qr_scan_id INTEGER,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location_city TEXT,
    location_country TEXT,
    device_type TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (qr_scan_id) REFERENCES qr_scans(id)
);

-- Voice recordings table (for voice memo feature)
CREATE TABLE IF NOT EXISTS simple_voice_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT NOT NULL,
    transcription TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    duration_seconds REAL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_qr_scans_email ON qr_scans(scanned_by_email);
CREATE INDEX IF NOT EXISTS idx_qr_scans_date ON qr_scans(scanned_at);
CREATE INDEX IF NOT EXISTS idx_products_upc ON products(upc);
