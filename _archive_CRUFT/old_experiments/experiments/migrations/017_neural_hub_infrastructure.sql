-- Migration 017: Neural Hub Infrastructure
-- Forum, IRC Relay, and Neural Hub routing tables

-- ============================================================================
-- NEURAL HUB CORE TABLES
-- ============================================================================

-- Central hub messages table (stores ALL messages from ALL channels)
CREATE TABLE IF NOT EXISTS hub_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source TEXT NOT NULL,  -- email, blog, forum, irc, relay
    metadata TEXT,  -- JSON: {from, to, subject, etc}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hub_messages_source ON hub_messages(source);
CREATE INDEX IF NOT EXISTS idx_hub_messages_created ON hub_messages(created_at);

-- Routing decisions log (tracks where messages were sent)
CREATE TABLE IF NOT EXISTS hub_routing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    target_channels TEXT NOT NULL,  -- JSON array: ["blog", "email", "forum"]
    classifications TEXT,  -- JSON: neural network classification results
    reason TEXT,  -- Why this routing decision was made
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES hub_messages(id)
);

CREATE INDEX IF NOT EXISTS idx_routing_log_message ON hub_routing_log(message_id);
CREATE INDEX IF NOT EXISTS idx_routing_log_created ON hub_routing_log(created_at);

-- Classification cache (avoid re-classifying same content)
CREATE TABLE IF NOT EXISTS hub_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL UNIQUE,  -- SHA256 of content
    network_name TEXT NOT NULL,
    score REAL NOT NULL,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_classifications_hash ON hub_classifications(content_hash);

-- ============================================================================
-- FORUM TABLES
-- ============================================================================

-- Forum categories (e.g., "Technical", "Privacy", "General")
CREATE TABLE IF NOT EXISTS forum_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    brand_id INTEGER,  -- Optional: category belongs to a brand
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Forum threads
CREATE TABLE IF NOT EXISTS forum_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    user_id INTEGER,  -- Can be NULL for system/neural-generated threads
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT 0,
    is_locked BOOLEAN DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    last_reply_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES forum_categories(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_forum_threads_category ON forum_threads(category_id);
CREATE INDEX IF NOT EXISTS idx_forum_threads_user ON forum_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_forum_threads_created ON forum_threads(created_at);
CREATE INDEX IF NOT EXISTS idx_forum_threads_slug ON forum_threads(slug);

-- Forum posts (replies to threads)
CREATE TABLE IF NOT EXISTS forum_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    user_id INTEGER,  -- Can be NULL for neural-generated posts
    content TEXT NOT NULL,
    parent_post_id INTEGER,  -- For nested replies
    is_accepted_answer BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES forum_threads(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_post_id) REFERENCES forum_posts(id)
);

CREATE INDEX IF NOT EXISTS idx_forum_posts_thread ON forum_posts(thread_id);
CREATE INDEX IF NOT EXISTS idx_forum_posts_user ON forum_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_forum_posts_created ON forum_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_forum_posts_parent ON forum_posts(parent_post_id);

-- ============================================================================
-- IRC RELAY TABLES
-- ============================================================================

-- IRC channels configuration
CREATE TABLE IF NOT EXISTS irc_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- #soulfra, #calriven, etc.
    server TEXT NOT NULL,  -- irc.freenode.net, etc.
    brand_id INTEGER,  -- Optional: channel belongs to a brand
    is_active BOOLEAN DEFAULT 1,
    auto_join BOOLEAN DEFAULT 1,
    relay_to_hub BOOLEAN DEFAULT 1,  -- Should messages be sent to neural hub?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- IRC messages (archive of IRC conversations)
CREATE TABLE IF NOT EXISTS irc_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    nickname TEXT NOT NULL,
    message TEXT NOT NULL,
    message_type TEXT DEFAULT 'chat',  -- chat, join, part, quit, action
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    relayed_to_hub BOOLEAN DEFAULT 0,
    hub_message_id INTEGER,  -- Link to hub_messages if relayed
    FOREIGN KEY (channel_id) REFERENCES irc_channels(id),
    FOREIGN KEY (hub_message_id) REFERENCES hub_messages(id)
);

CREATE INDEX IF NOT EXISTS idx_irc_messages_channel ON irc_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_irc_messages_timestamp ON irc_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_irc_messages_relayed ON irc_messages(relayed_to_hub);

-- IRC relay configuration (which channels relay to which other platforms)
CREATE TABLE IF NOT EXISTS relay_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,  -- irc, forum, email, blog
    source_id INTEGER,  -- ID in source table
    target_type TEXT NOT NULL,  -- irc, forum, email, blog
    target_id INTEGER,  -- ID in target table
    is_bidirectional BOOLEAN DEFAULT 0,  -- Should it relay both ways?
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_relay_configs_source ON relay_configs(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_relay_configs_target ON relay_configs(target_type, target_id);

-- ============================================================================
-- SEED DATA - Initial Setup
-- ============================================================================

-- Create default forum categories
INSERT OR IGNORE INTO forum_categories (id, name, slug, description, order_index) VALUES
    (1, 'Technical', 'technical', 'Programming, code reviews, and technical discussions', 1),
    (2, 'Privacy & Security', 'privacy', 'Data privacy, security, and self-hosting', 2),
    (3, 'General', 'general', 'General discussions about anything', 3),
    (4, 'Validation & Testing', 'validation', 'Code reviews, testing, and quality assurance', 4);

-- Create default IRC channels (not auto-joined by default)
INSERT OR IGNORE INTO irc_channels (id, name, server, auto_join, relay_to_hub) VALUES
    (1, '#soulfra', 'irc.libera.chat', 0, 1),
    (2, '#calriven-dev', 'irc.libera.chat', 0, 1);

-- Example relay config: IRC #soulfra ↔ Forum "General" category
INSERT OR IGNORE INTO relay_configs (source_type, source_id, target_type, target_id, is_bidirectional) VALUES
    ('irc', 1, 'forum', 3, 1);  -- IRC channel 1 ↔ Forum category 3
