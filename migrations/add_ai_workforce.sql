-- AI Workforce System Database Migration
-- Creates tables for task management and credit tracking

-- Tasks assigned to AI personas
CREATE TABLE IF NOT EXISTS ai_workforce_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    task_type TEXT NOT NULL,  -- 'write_post', 'respond_comment', 'moderate'
    assigned_to_persona TEXT NOT NULL,  -- 'calriven', 'soulfra', 'deathtodata'
    prompt TEXT NOT NULL,
    keywords_target TEXT,  -- JSON array of target keywords
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'approved', 'rejected'
    output_content TEXT,  -- AI-generated content
    output_title TEXT,  -- Generated title
    output_slug TEXT,  -- URL slug
    credits_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    approved_at TIMESTAMP
);

-- Engagement tracking and credits
CREATE TABLE IF NOT EXISTS ai_engagement_credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona TEXT NOT NULL,  -- 'calriven', 'soulfra', 'deathtodata'
    content_id INTEGER,  -- post ID from posts table
    task_id INTEGER,  -- task ID from ai_workforce_tasks
    engagement_type TEXT NOT NULL,  -- 'view', 'like', 'laugh', 'comment', 'share'
    credits INTEGER NOT NULL,  -- Points earned
    user_identifier TEXT,  -- Optional: who engaged
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES ai_workforce_tasks(id)
);

-- CringeProof approval votes
CREATE TABLE IF NOT EXISTS content_approval_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    persona TEXT NOT NULL,  -- 'calriven', 'soulfra', 'deathtodata'
    vote TEXT NOT NULL,  -- 'approve', 'reject', 'needs_revision'
    reasoning TEXT,  -- Why this vote?
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES ai_workforce_tasks(id)
);

-- AI persona leaderboard (materialized view)
CREATE TABLE IF NOT EXISTS ai_persona_stats (
    persona TEXT PRIMARY KEY,
    total_credits INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    total_posts_published INTEGER DEFAULT 0,
    avg_approval_rate REAL DEFAULT 0.0,
    best_engagement_type TEXT,  -- 'laugh', 'share', etc.
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize persona stats
INSERT OR IGNORE INTO ai_persona_stats (persona) VALUES ('calriven');
INSERT OR IGNORE INTO ai_persona_stats (persona) VALUES ('soulfra');
INSERT OR IGNORE INTO ai_persona_stats (persona) VALUES ('deathtodata');

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON ai_workforce_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_persona ON ai_workforce_tasks(assigned_to_persona);
CREATE INDEX IF NOT EXISTS idx_tasks_domain ON ai_workforce_tasks(domain);
CREATE INDEX IF NOT EXISTS idx_credits_persona ON ai_engagement_credits(persona);
CREATE INDEX IF NOT EXISTS idx_credits_task ON ai_engagement_credits(task_id);
CREATE INDEX IF NOT EXISTS idx_votes_task ON content_approval_votes(task_id);

-- View: Leaderboard (real-time credit totals)
CREATE VIEW IF NOT EXISTS v_ai_leaderboard AS
SELECT
    persona,
    SUM(credits) as total_credits,
    COUNT(DISTINCT task_id) as tasks_contributed,
    COUNT(CASE WHEN engagement_type = 'laugh' THEN 1 END) as laughs_earned,
    COUNT(CASE WHEN engagement_type = 'share' THEN 1 END) as shares_earned
FROM ai_engagement_credits
GROUP BY persona
ORDER BY total_credits DESC;

-- View: Pending tasks
CREATE VIEW IF NOT EXISTS v_pending_tasks AS
SELECT
    id,
    domain,
    task_type,
    assigned_to_persona,
    prompt,
    keywords_target,
    created_at
FROM ai_workforce_tasks
WHERE status = 'pending'
ORDER BY created_at ASC;

-- View: Task performance
CREATE VIEW IF NOT EXISTS v_task_performance AS
SELECT
    t.id,
    t.domain,
    t.assigned_to_persona,
    t.output_title,
    t.status,
    SUM(e.credits) as total_credits_earned,
    COUNT(e.id) as total_engagements,
    GROUP_CONCAT(DISTINCT v.vote) as votes
FROM ai_workforce_tasks t
LEFT JOIN ai_engagement_credits e ON t.id = e.task_id
LEFT JOIN content_approval_votes v ON t.id = v.task_id
WHERE t.status IN ('approved', 'completed')
GROUP BY t.id
ORDER BY total_credits_earned DESC;
