-- Chapter Version Control Schema
-- "Git for CalRiven" - Track changes to chapters without using Git

-- Chapter snapshots (like git commits)
CREATE TABLE IF NOT EXISTS chapter_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_num INTEGER NOT NULL,
    version_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- JSON: full chapter tutorial data
    commit_message TEXT,     -- What changed in this version
    created_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_snapshot_id INTEGER,  -- Previous version (like git parent commit)
    is_fork INTEGER DEFAULT 0,   -- 1 if this is a user's custom fork
    fork_source_id INTEGER,      -- Original snapshot this was forked from
    UNIQUE(chapter_num, version_num),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (parent_snapshot_id) REFERENCES chapter_snapshots(id),
    FOREIGN KEY (fork_source_id) REFERENCES chapter_snapshots(id)
);

-- Track individual changes between versions (like git diff)
CREATE TABLE IF NOT EXISTS chapter_diffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    parent_snapshot_id INTEGER,
    diff_type TEXT NOT NULL,  -- 'added', 'removed', 'modified'
    section TEXT NOT NULL,     -- Which part changed: 'title', 'step_0', 'step_1', etc.
    old_value TEXT,            -- Content before change
    new_value TEXT,            -- Content after change
    line_num INTEGER,          -- Line number in content (for display)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES chapter_snapshots(id),
    FOREIGN KEY (parent_snapshot_id) REFERENCES chapter_snapshots(id)
);

-- User chapter forks (Chapter 5: "Your first neural network clone")
CREATE TABLE IF NOT EXISTS user_chapter_forks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    fork_name TEXT NOT NULL,           -- User's custom name
    source_snapshot_id INTEGER NOT NULL,  -- Original chapter snapshot
    current_snapshot_id INTEGER,        -- Latest version of fork
    description TEXT,                   -- Why they forked it
    is_public INTEGER DEFAULT 0,        -- Share fork with others
    fork_count INTEGER DEFAULT 0,       -- How many times this was forked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (source_snapshot_id) REFERENCES chapter_snapshots(id),
    FOREIGN KEY (current_snapshot_id) REFERENCES chapter_snapshots(id)
);

-- Track which users are viewing which chapter versions (analytics)
CREATE TABLE IF NOT EXISTS chapter_version_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    snapshot_id INTEGER NOT NULL,
    chapter_num INTEGER NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_spent_seconds INTEGER DEFAULT 0,
    device_type TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (snapshot_id) REFERENCES chapter_snapshots(id)
);

-- Chapter merge requests (like GitHub pull requests)
CREATE TABLE IF NOT EXISTS chapter_merge_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_fork_id INTEGER NOT NULL,     -- User's fork
    to_snapshot_id INTEGER NOT NULL,   -- Official chapter to merge into
    title TEXT NOT NULL,
    description TEXT,
    created_by_user_id INTEGER NOT NULL,
    status TEXT DEFAULT 'open',        -- 'open', 'merged', 'rejected', 'closed'
    reviewed_by_user_id INTEGER,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_fork_id) REFERENCES user_chapter_forks(id),
    FOREIGN KEY (to_snapshot_id) REFERENCES chapter_snapshots(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshots_chapter ON chapter_snapshots(chapter_num);
CREATE INDEX IF NOT EXISTS idx_snapshots_version ON chapter_snapshots(chapter_num, version_num);
CREATE INDEX IF NOT EXISTS idx_snapshots_user ON chapter_snapshots(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_diffs_snapshot ON chapter_diffs(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_forks_user ON user_chapter_forks(user_id);
CREATE INDEX IF NOT EXISTS idx_forks_chapter ON user_chapter_forks(chapter_num);
CREATE INDEX IF NOT EXISTS idx_version_views_snapshot ON chapter_version_views(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_merge_requests_status ON chapter_merge_requests(status);
