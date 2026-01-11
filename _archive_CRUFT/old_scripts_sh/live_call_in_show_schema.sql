-- Live Call-In Show System Database Schema
-- Like NPR call-in shows + podcast sponsorships

-- Main show episodes (host reads news article, takes call-ins)
CREATE TABLE IF NOT EXISTS live_shows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    article_url TEXT,
    article_text TEXT NOT NULL,
    article_source TEXT,
    host_user_id INTEGER NOT NULL,
    status TEXT DEFAULT 'accepting_calls', -- accepting_calls, closed, published
    total_reactions INTEGER DEFAULT 0,
    approved_reactions INTEGER DEFAULT 0,
    total_sponsors INTEGER DEFAULT 0,
    intro_bookend_id INTEGER,  -- Voice recording ID for intro
    outro_bookend_id INTEGER,  -- Voice recording ID for outro
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_user_id) REFERENCES users(id),
    FOREIGN KEY (intro_bookend_id) REFERENCES simple_voice_recordings(id),
    FOREIGN KEY (outro_bookend_id) REFERENCES simple_voice_recordings(id)
);

-- Voice reactions/call-ins from listeners
CREATE TABLE IF NOT EXISTS show_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    recording_id INTEGER NOT NULL,
    user_id INTEGER,  -- NULL if anonymous
    caller_name TEXT,  -- "John from Tampa"
    reaction_type TEXT DEFAULT 'comment',  -- comment, question, story, counterpoint
    transcription TEXT,
    approval_status TEXT DEFAULT 'pending',  -- pending, approved, rejected, aired
    timestamp_in_show INTEGER,  -- Seconds into final show where this appears
    ad_pairing_id INTEGER,  -- Which sponsor is paired with this
    approved_by INTEGER,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES live_shows(id),
    FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (ad_pairing_id) REFERENCES show_sponsors(id)
);

-- Sponsors/advertisers for shows
CREATE TABLE IF NOT EXISTS show_sponsors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    sponsor_name TEXT NOT NULL,
    sponsor_type TEXT,  -- product, service, affiliate, brand
    sponsor_url TEXT,
    sponsor_logo_path TEXT,
    ad_script TEXT,  -- Pre-written ad copy
    keywords_json TEXT,  -- ["privacy", "security"] - for pairing
    placement_type TEXT DEFAULT 'reaction',  -- bookend, reaction, midroll
    cpc_estimate REAL,  -- Cost per click estimate
    total_mentions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES live_shows(id)
);

-- Bookend segments (intro/outro with sponsor mentions)
CREATE TABLE IF NOT EXISTS show_bookends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    bookend_type TEXT NOT NULL,  -- intro, outro
    recording_id INTEGER,  -- Voice recording of bookend
    generated_script TEXT,  -- AI-generated script
    sponsor_ids_json TEXT,  -- [1, 2, 3] - sponsors mentioned
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES live_shows(id),
    FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id)
);

-- Mapping reactions to specific ad placements
CREATE TABLE IF NOT EXISTS reaction_ad_pairings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reaction_id INTEGER NOT NULL,
    sponsor_id INTEGER NOT NULL,
    pairing_score REAL,  -- 0-100 relevance score
    pairing_reason TEXT,  -- Why AI paired these
    placement_style TEXT DEFAULT 'before',  -- before, after, split
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reaction_id) REFERENCES show_reactions(id),
    FOREIGN KEY (sponsor_id) REFERENCES show_sponsors(id)
);

-- Analytics for show performance
CREATE TABLE IF NOT EXISTS show_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,  -- total_listens, avg_listen_duration, sponsor_clicks
    metric_value REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES live_shows(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_show_reactions_show_id ON show_reactions(show_id);
CREATE INDEX IF NOT EXISTS idx_show_reactions_status ON show_reactions(approval_status);
CREATE INDEX IF NOT EXISTS idx_show_sponsors_show_id ON show_sponsors(show_id);
CREATE INDEX IF NOT EXISTS idx_live_shows_status ON live_shows(status);
CREATE INDEX IF NOT EXISTS idx_live_shows_host ON live_shows(host_user_id);
