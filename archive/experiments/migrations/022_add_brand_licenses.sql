-- Migration 022: Add Brand Licensing System
-- Creates brand_licenses table for managing brand licensing (CC0, CC-BY, proprietary, etc.)
-- Like a "buff system" in games - each license type gives different permissions

CREATE TABLE IF NOT EXISTS brand_licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    license_type TEXT NOT NULL DEFAULT 'cc0', -- cc0, cc-by, cc-by-sa, cc-by-nc, proprietary, public
    requires_attribution BOOLEAN DEFAULT 0,
    allows_commercial BOOLEAN DEFAULT 1,
    allows_derivatives BOOLEAN DEFAULT 1,
    allows_sharing BOOLEAN DEFAULT 1,
    license_text TEXT,
    license_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_brand_licenses_brand_id ON brand_licenses(brand_id);
CREATE INDEX IF NOT EXISTS idx_brand_licenses_type ON brand_licenses(license_type);

-- Insert default licenses for existing brands
INSERT INTO brand_licenses (brand_id, license_type, requires_attribution, allows_commercial, allows_derivatives, allows_sharing, license_text, license_url)
SELECT
    id as brand_id,
    'cc0' as license_type,
    0 as requires_attribution,
    1 as allows_commercial,
    1 as allows_derivatives,
    1 as allows_sharing,
    'CC0 1.0 Universal - Public Domain Dedication' as license_text,
    'https://creativecommons.org/publicdomain/zero/1.0/' as license_url
FROM brands
WHERE NOT EXISTS (
    SELECT 1 FROM brand_licenses WHERE brand_licenses.brand_id = brands.id
);
