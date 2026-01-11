-- Customer Discovery Database Schema
-- NO ORMs - Pure SQL following Bun/Zig/pot philosophy
-- Built from scratch, standard library only

-- ==============================================================================
-- USERS & AUTHENTICATION
-- ==============================================================================

-- Users table (linked to GitHub OAuth)
CREATE TABLE IF NOT EXISTS discovery_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_username TEXT UNIQUE NOT NULL,
    github_user_id INTEGER UNIQUE NOT NULL,
    email TEXT,
    api_key TEXT UNIQUE NOT NULL,
    tier INTEGER DEFAULT 1,  -- GitHub Faucet tier (1-4)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_discovery_users_api_key ON discovery_users(api_key);
CREATE INDEX idx_discovery_users_github_id ON discovery_users(github_user_id);

-- ==============================================================================
-- CUSTOMER DISCOVERY RESPONSES
-- ==============================================================================

-- Main responses table
CREATE TABLE IF NOT EXISTS discovery_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,  -- Browser session to group conversations
    question TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    bucket TEXT,  -- Auto-categorized bucket (pricing, features, pain_points, etc.)
    keywords TEXT,  -- JSON array of extracted keywords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES discovery_users(id)
);

CREATE INDEX idx_discovery_responses_user ON discovery_responses(user_id);
CREATE INDEX idx_discovery_responses_session ON discovery_responses(session_id);
CREATE INDEX idx_discovery_responses_bucket ON discovery_responses(bucket);
CREATE INDEX idx_discovery_responses_created ON discovery_responses(created_at);

-- ==============================================================================
-- WORD-BASED BUCKETS (Auto-categorization)
-- ==============================================================================

-- Bucket definitions (like mesh network wordmap)
CREATE TABLE IF NOT EXISTS discovery_buckets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,  -- e.g., "pricing_questions"
    display_name TEXT NOT NULL,  -- e.g., "Pricing Questions"
    keywords TEXT NOT NULL,  -- JSON array of trigger words
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pre-populate common buckets
INSERT OR IGNORE INTO discovery_buckets (name, display_name, keywords, description) VALUES
    ('pricing', 'Pricing Questions', '["price", "cost", "expensive", "cheap", "fee", "plan", "subscription", "payment"]', 'Questions about pricing and costs'),
    ('features', 'Feature Requests', '["feature", "capability", "can it", "does it", "support", "integration", "api"]', 'Questions about features and capabilities'),
    ('pain_points', 'Pain Points', '["problem", "issue", "difficult", "hard", "frustrating", "annoying", "slow", "broken"]', 'User pain points and frustrations'),
    ('competition', 'Competitive Intel', '["competitor", "alternative", "versus", "vs", "better than", "compared to", "similar to"]', 'Competitive comparisons'),
    ('use_cases', 'Use Cases', '["use case", "workflow", "process", "how to", "tutorial", "example", "demo"]', 'How users want to use the product'),
    ('technical', 'Technical Questions', '["technical", "architecture", "infrastructure", "deployment", "hosting", "security"]', 'Technical implementation questions'),
    ('onboarding', 'Onboarding', '["getting started", "setup", "install", "configure", "onboard", "tutorial"]', 'Onboarding and getting started'),
    ('feedback', 'General Feedback', '["feedback", "suggestion", "idea", "improvement", "love", "hate"]', 'General feedback and suggestions');

-- ==============================================================================
-- EMAIL NETWORK QUEUE
-- ==============================================================================

-- Queue for email notifications (decentralized network)
CREATE TABLE IF NOT EXISTS discovery_email_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    recipient TEXT NOT NULL,  -- Email address
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    sent INTEGER DEFAULT 0,  -- 0 = pending, 1 = sent
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(response_id) REFERENCES discovery_responses(id)
);

CREATE INDEX idx_discovery_email_queue_sent ON discovery_email_queue(sent);

-- ==============================================================================
-- ANALYTICS & INSIGHTS
-- ==============================================================================

-- Aggregate statistics per user
CREATE TABLE IF NOT EXISTS discovery_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_questions INTEGER DEFAULT 0,
    pricing_questions INTEGER DEFAULT 0,
    feature_requests INTEGER DEFAULT 0,
    pain_points INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES discovery_users(id)
);

CREATE INDEX idx_discovery_stats_user ON discovery_stats(user_id);

-- ==============================================================================
-- SESSION TRACKING
-- ==============================================================================

-- Track user sessions
CREATE TABLE IF NOT EXISTS discovery_sessions (
    id TEXT PRIMARY KEY,  -- UUID
    user_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    question_count INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES discovery_users(id)
);

CREATE INDEX idx_discovery_sessions_user ON discovery_sessions(user_id);
CREATE INDEX idx_discovery_sessions_started ON discovery_sessions(started_at);
