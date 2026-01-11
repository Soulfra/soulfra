-- Migration 016: Catchphrase A/B Testing System
-- For CalRiven to test brand catchphrases and ideas

CREATE TABLE IF NOT EXISTS catchphrases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_slug TEXT NOT NULL,
    text TEXT NOT NULL,
    variant_label TEXT,  -- e.g., "A", "B", "C" for A/B/C testing
    category TEXT,  -- e.g., "greeting", "tagline", "mission"
    context TEXT,  -- JSON with additional context
    creator TEXT,  -- Who created this catchphrase
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_slug) REFERENCES brands(slug)
);

CREATE TABLE IF NOT EXISTS catchphrase_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catchphrase_id INTEGER NOT NULL,
    user_id INTEGER,
    plot_id INTEGER,
    reaction_type TEXT NOT NULL,  -- "love", "like", "meh", "dislike", "cringe"
    reaction_emoji TEXT,  -- Actual emoji used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (catchphrase_id) REFERENCES catchphrases(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plot_id) REFERENCES plots(id)
);

CREATE INDEX IF NOT EXISTS idx_catchphrases_brand ON catchphrases(brand_slug);
CREATE INDEX IF NOT EXISTS idx_catchphrases_active ON catchphrases(is_active);
CREATE INDEX IF NOT EXISTS idx_catchphrase_reactions_phrase ON catchphrase_reactions(catchphrase_id);
CREATE INDEX IF NOT EXISTS idx_catchphrase_reactions_user ON catchphrase_reactions(user_id);

-- Insert test catchphrases for CalRiven (only if not already present)
INSERT OR IGNORE INTO catchphrases (brand_slug, text, variant_label, category, creator) VALUES
    ('calriven', 'Building the future, one line of code at a time', 'A', 'tagline', 'CalRiven'),
    ('calriven', 'Where innovation meets execution', 'B', 'tagline', 'CalRiven'),
    ('calriven', 'Code with purpose, ship with confidence', 'C', 'tagline', 'CalRiven'),
    ('calriven', 'What are you building today?', 'A', 'greeting', 'CalRiven'),
    ('calriven', 'Ready to ship something amazing?', 'B', 'greeting', 'CalRiven'),
    ('calriven', 'Technical excellence, human impact', 'A', 'mission', 'CalRiven');
