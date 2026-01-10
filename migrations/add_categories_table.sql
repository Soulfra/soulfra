-- Expandable Categories System Migration
-- Adds support for dynamic categories and silos across domains
--
-- Run with: sqlite3 soulfra.db < migrations/add_categories_table.sql

-- Categories table - stores all available categories across all domains
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    domain_slug TEXT NOT NULL,  -- Which domain this category belongs to
    silo_type TEXT,  -- 'professionals', 'creators', 'educators', etc.
    icon TEXT,  -- Icon name or emoji
    requires_verification BOOLEAN DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for professionals with multiple categories
CREATE TABLE IF NOT EXISTS professional_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professional_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,  -- One primary category per professional
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(professional_id, category_id)
);

-- Silo types table - defines different content types
CREATE TABLE IF NOT EXISTS silo_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    requires_verification BOOLEAN DEFAULT 0,
    has_inbox BOOLEAN DEFAULT 1,
    has_ratings BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default silo types
INSERT OR IGNORE INTO silo_types (slug, name, description, icon, requires_verification, has_inbox, has_ratings)
VALUES
    ('professionals', 'Professionals', 'Verified service professionals', 'briefcase', 1, 1, 1),
    ('creators', 'Creators', 'Content creators and artists', 'microphone', 0, 1, 1),
    ('educators', 'Educators', 'Teachers and instructors', 'graduation-cap', 1, 1, 1),
    ('developers', 'Developers', 'Software developers', 'code', 0, 1, 0),
    ('streamers', 'Streamers', 'Live streamers', 'video', 0, 1, 1),
    ('writers', 'Writers', 'Content writers and bloggers', 'pen', 0, 1, 0);

-- Insert default StPetePros categories
INSERT OR IGNORE INTO categories (slug, name, description, domain_slug, silo_type, requires_verification, sort_order)
VALUES
    ('plumbing', 'Plumbing', 'Licensed plumbers and drain services', 'stpetepros', 'professionals', 1, 1),
    ('electrical', 'Electrical', 'Licensed electricians', 'stpetepros', 'professionals', 1, 2),
    ('hvac', 'HVAC', 'Heating, ventilation, and air conditioning', 'stpetepros', 'professionals', 1, 3),
    ('roofing', 'Roofing', 'Roofing contractors and repair', 'stpetepros', 'professionals', 1, 4),
    ('legal', 'Legal Services', 'Attorneys and legal professionals', 'stpetepros', 'professionals', 1, 5),
    ('landscaping', 'Landscaping', 'Lawn care and landscaping services', 'stpetepros', 'professionals', 0, 6),
    ('cleaning', 'Cleaning', 'House cleaning and maid services', 'stpetepros', 'professionals', 0, 7),
    ('pest-control', 'Pest Control', 'Pest control and extermination', 'stpetepros', 'professionals', 1, 8),
    ('painting', 'Painting', 'Interior and exterior painting', 'stpetepros', 'professionals', 0, 9),
    ('pool-service', 'Pool Service', 'Pool cleaning and maintenance', 'stpetepros', 'professionals', 0, 10),
    ('real-estate', 'Real Estate', 'Real estate agents and brokers', 'stpetepros', 'professionals', 1, 11),
    ('auto-repair', 'Auto Repair', 'Auto mechanics and repair shops', 'stpetepros', 'professionals', 0, 12),
    ('contracting', 'General Contracting', 'General contractors and builders', 'stpetepros', 'professionals', 1, 13),
    ('handyman', 'Handyman Services', 'General handyman and repairs', 'stpetepros', 'professionals', 0, 14),
    ('home-inspection', 'Home Inspection', 'Home inspectors', 'stpetepros', 'professionals', 1, 15);

-- Insert CringeProof categories
INSERT OR IGNORE INTO categories (slug, name, description, domain_slug, silo_type, sort_order)
VALUES
    ('voice-ideas', 'Voice Ideas', 'Share ideas via voice recording', 'cringeproof', 'creators', 1),
    ('storytelling', 'Storytelling', 'Voice storytellers', 'cringeproof', 'creators', 2),
    ('comedy', 'Comedy', 'Comedy and humor creators', 'cringeproof', 'creators', 3);

-- Insert CalRiven categories
INSERT OR IGNORE INTO categories (slug, name, description, domain_slug, silo_type, requires_verification, sort_order)
VALUES
    ('real-estate-agents', 'Real Estate Agents', 'Licensed real estate professionals', 'calriven', 'professionals', 1, 1),
    ('market-analysts', 'Market Analysts', 'Real estate market analysts', 'calriven', 'professionals', 0, 2);

-- Insert HowToCookAtHome categories
INSERT OR IGNORE INTO categories (slug, name, description, domain_slug, silo_type, sort_order)
VALUES
    ('home-chefs', 'Home Chefs', 'Home cooking enthusiasts', 'howtocookathome', 'creators', 1),
    ('cooking-instructors', 'Cooking Instructors', 'Professional cooking teachers', 'howtocookathome', 'educators', 2),
    ('recipe-bloggers', 'Recipe Bloggers', 'Food and recipe bloggers', 'howtocookathome', 'writers', 3);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_categories_domain ON categories(domain_slug);
CREATE INDEX IF NOT EXISTS idx_categories_silo ON categories(silo_type);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);
CREATE INDEX IF NOT EXISTS idx_professional_categories_pro ON professional_categories(professional_id);
CREATE INDEX IF NOT EXISTS idx_professional_categories_cat ON professional_categories(category_id);

-- Migrate existing professionals to use categories table
-- Link existing professionals to their categories in the new system
INSERT OR IGNORE INTO professional_categories (professional_id, category_id, is_primary)
SELECT
    p.id,
    c.id,
    1  -- Mark as primary category
FROM professionals p
INNER JOIN categories c ON c.slug = p.category AND c.domain_slug = 'stpetepros'
WHERE p.category IS NOT NULL;

-- Add notes column for migration tracking
ALTER TABLE professionals ADD COLUMN category_migration_notes TEXT;

-- Success message (shown when migration completes)
-- ✅ Categories system migrated successfully
-- - Created categories, professional_categories, and silo_types tables
-- - Migrated existing professionals to new category system
-- - Added 15 StPetePros categories
-- - Added 3 CringeProof categories
-- - Added 2 CalRiven categories
-- - Added 3 HowToCookAtHome categories
