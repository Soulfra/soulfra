-- Brand Builder Database Schema
-- Tracks conversations with Ollama and generated brand concepts

-- Conversations: Track chat history with Ollama
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    user_email TEXT,
    current_step TEXT DEFAULT 'intro',
    context TEXT,  -- JSON storing conversation state
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_email ON conversations(user_email);

-- Conversation Messages: Individual chat messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON conversation_messages(conversation_id);

-- Brand Concepts: Generated brand ideas from conversations
CREATE TABLE IF NOT EXISTS brand_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    user_email TEXT,
    brand_name TEXT NOT NULL,
    brand_slug TEXT UNIQUE,
    tagline TEXT,
    description TEXT,
    target_audience TEXT,
    tone TEXT,
    color_primary TEXT,
    color_secondary TEXT,
    logo_concept TEXT,
    problem_solving TEXT,
    unique_value TEXT,
    selected BOOLEAN DEFAULT 0,
    vote_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_concepts_conversation ON brand_concepts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_concepts_slug ON brand_concepts(brand_slug);
CREATE INDEX IF NOT EXISTS idx_concepts_email ON brand_concepts(user_email);

-- Brand Votes: A/B testing votes
CREATE TABLE IF NOT EXISTS brand_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id INTEGER NOT NULL,
    voter_email TEXT,
    voter_ip TEXT,
    vote_type TEXT,  -- 'upvote' or 'comment'
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES brand_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_votes_concept ON brand_votes(concept_id);
