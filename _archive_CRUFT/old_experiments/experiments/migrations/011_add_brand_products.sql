-- Migration 011: Add Brand & Products System
-- Integrates brand-to-product pipeline into soulfra-simple
--
-- Creates:
-- - brands (Soulfra, DeathToData, CalRiven, etc.)
-- - products (merch, APIs, services)
-- - brand_posts (link posts to brands)

-- Brands table - 12 brands from brand-profiles.js
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    tagline TEXT,
    category TEXT,
    tier TEXT,  -- foundation, business, creative
    color_primary TEXT,
    color_secondary TEXT,
    color_accent TEXT,
    personality_tone TEXT,
    personality_traits TEXT,  -- JSON array
    ai_style TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table - generated merch, APIs, services
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    type TEXT NOT NULL,  -- merch, api, email, service
    name TEXT NOT NULL,
    description TEXT,
    design_text TEXT,  -- for merch: slogan/design
    endpoint TEXT,  -- for APIs: /api/soulfra/privacy-score
    price REAL,
    upc TEXT UNIQUE,  -- UPC-12 barcode
    sku TEXT UNIQUE,  -- Stock keeping unit
    ad_tier INTEGER,  -- 1=Google Ads, 2=Facebook, 3=Organic
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Brand-Post linking (many-to-many)
CREATE TABLE IF NOT EXISTS brand_posts (
    brand_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    relevance_score REAL DEFAULT 0.0,  -- 0-1, how relevant
    PRIMARY KEY (brand_id, post_id),
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
CREATE INDEX IF NOT EXISTS idx_products_tier ON products(ad_tier);
CREATE INDEX IF NOT EXISTS idx_brand_posts_brand ON brand_posts(brand_id);
CREATE INDEX IF NOT EXISTS idx_brand_posts_post ON brand_posts(post_id);

-- Insert 3 foundation brands (more can be added later)
INSERT OR IGNORE INTO brands (name, slug, tagline, category, tier, color_primary, color_secondary, color_accent, personality_tone, ai_style) VALUES
    ('Soulfra', 'soulfra', 'Your keys. Your identity. Period.', 'Identity & Security', 'foundation', '#3498db', '#2ecc71', '#e74c3c', 'Secure, trustworthy', 'formal, security-conscious, emphasizes privacy'),
    ('DeathToData', 'deathtodata', 'Search without surveillance. Deal with it, Google.', 'Privacy Search', 'foundation', '#e74c3c', '#c0392b', '#f39c12', 'Rebellious, defiant', 'edgy, confrontational, challenges status quo'),
    ('Calriven', 'calriven', 'Best AI for the job. Every time.', 'AI Platform', 'foundation', '#667eea', '#764ba2', '#61dafb', 'Intelligent, efficient', 'technical, helpful, focuses on best solutions');

-- Sample products for Soulfra (from generated data)
INSERT OR IGNORE INTO products (brand_id, type, name, description, design_text, price, ad_tier) VALUES
    (1, 'merch', 'Soulfra T-Shirt', 'Privacy-focused t-shirt', 'Your keys. Your identity. Period.', 25.00, 2),
    (1, 'merch', 'Soulfra Sticker', 'Logo sticker (blue/green)', 'Soulfra logo', 5.00, 3),
    (1, 'merch', 'Privacy Manifesto Poster', 'Privacy principles poster', 'Privacy manifesto', 15.00, 2),
    (1, 'api', 'Privacy Score API', 'Privacy risk scoring endpoint', NULL, 29.00, 1),
    (1, 'api', 'Encryption Recommender API', 'Encryption algorithm recommendations', NULL, 29.00, 1);
