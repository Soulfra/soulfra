-- Migration 003: Add Reasoning Platform Features
-- From migrate_reasoning.py
--
-- Creates:
-- - reasoning_threads (multi-step AI debates)
-- - reasoning_steps (individual reasoning actions)
-- - categories (post organization)
-- - tags (post metadata)
-- - post_categories (many-to-many)
-- - post_tags (many-to-many)

-- Reasoning threads - Track AI debate sessions
CREATE TABLE IF NOT EXISTS reasoning_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    initiator_user_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (initiator_user_id) REFERENCES users(id)
);

-- Reasoning steps - Individual AI reasoning actions
CREATE TABLE IF NOT EXISTS reasoning_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    parent_step_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES reasoning_threads(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_step_id) REFERENCES reasoning_steps(id) ON DELETE CASCADE
);

-- Categories - Post categories for organization
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags - Post tags for metadata
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Post-category relationship (many-to-many)
CREATE TABLE IF NOT EXISTS post_categories (
    post_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, category_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Post-tag relationship (many-to-many)
CREATE TABLE IF NOT EXISTS post_tags (
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reasoning_threads_post_id ON reasoning_threads(post_id);
CREATE INDEX IF NOT EXISTS idx_reasoning_steps_thread_id ON reasoning_steps(thread_id);
CREATE INDEX IF NOT EXISTS idx_reasoning_steps_user_id ON reasoning_steps(user_id);
CREATE INDEX IF NOT EXISTS idx_post_categories_post_id ON post_categories(post_id);
CREATE INDEX IF NOT EXISTS idx_post_categories_category_id ON post_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);

-- Insert default categories
INSERT OR IGNORE INTO categories (name, slug, description) VALUES
    ('Philosophy', 'philosophy', 'Philosophical discussions and debates'),
    ('Technology', 'technology', 'Technical architecture and systems'),
    ('Privacy', 'privacy', 'Privacy and surveillance topics'),
    ('Security', 'security', 'Security and encryption'),
    ('AI', 'ai', 'Artificial intelligence and machine learning'),
    ('Web3', 'web3', 'Decentralization and blockchain');

-- Insert default tags
INSERT OR IGNORE INTO tags (name, slug) VALUES
    ('ollama', 'ollama'),
    ('reasoning', 'reasoning'),
    ('debate', 'debate'),
    ('local-ai', 'local-ai'),
    ('oss', 'oss');
