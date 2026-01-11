-- CringeProof Voting System for Voice Suggestions
-- Community validation of which ideas are authentic vs cringe

-- Votes on voice suggestions
CREATE TABLE IF NOT EXISTS suggestion_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK(vote_type IN ('upvote', 'downvote', 'cringe', 'authentic')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (suggestion_id) REFERENCES voice_suggestions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(suggestion_id, user_id)  -- One vote per user per suggestion
);

-- Votes on voice responses
CREATE TABLE IF NOT EXISTS response_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK(vote_type IN ('upvote', 'downvote', 'cringe', 'authentic')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (response_id) REFERENCES voice_suggestion_responses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(response_id, user_id)  -- One vote per user per response
);

-- CringeProof scores (calculated from votes)
CREATE TABLE IF NOT EXISTS cringeproof_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    cringe_votes INTEGER DEFAULT 0,
    authentic_votes INTEGER DEFAULT 0,
    cringeproof_score REAL DEFAULT 0,  -- 0-100, higher = more authentic
    last_calculated TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (suggestion_id) REFERENCES voice_suggestions(id) ON DELETE CASCADE,
    UNIQUE(suggestion_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_suggestion_votes_suggestion ON suggestion_votes(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_votes_user ON suggestion_votes(user_id);
CREATE INDEX IF NOT EXISTS idx_response_votes_response ON response_votes(response_id);
CREATE INDEX IF NOT EXISTS idx_response_votes_user ON response_votes(user_id);
CREATE INDEX IF NOT EXISTS idx_cringeproof_scores_suggestion ON cringeproof_scores(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_cringeproof_scores_score ON cringeproof_scores(cringeproof_score DESC);

-- View: Suggestions with vote counts
CREATE VIEW IF NOT EXISTS suggestions_with_votes AS
SELECT
    vs.*,
    COALESCE(sv_up.upvotes, 0) as upvotes,
    COALESCE(sv_down.downvotes, 0) as downvotes,
    COALESCE(sv_cringe.cringe_votes, 0) as cringe_votes,
    COALESCE(sv_auth.authentic_votes, 0) as authentic_votes,
    COALESCE(cs.cringeproof_score, 50.0) as cringeproof_score,
    (COALESCE(sv_up.upvotes, 0) - COALESCE(sv_down.downvotes, 0)) as vote_score
FROM voice_suggestions vs
LEFT JOIN (
    SELECT suggestion_id, COUNT(*) as upvotes
    FROM suggestion_votes
    WHERE vote_type = 'upvote'
    GROUP BY suggestion_id
) sv_up ON vs.id = sv_up.suggestion_id
LEFT JOIN (
    SELECT suggestion_id, COUNT(*) as downvotes
    FROM suggestion_votes
    WHERE vote_type = 'downvote'
    GROUP BY suggestion_id
) sv_down ON vs.id = sv_down.suggestion_id
LEFT JOIN (
    SELECT suggestion_id, COUNT(*) as cringe_votes
    FROM suggestion_votes
    WHERE vote_type = 'cringe'
    GROUP BY suggestion_id
) sv_cringe ON vs.id = sv_cringe.suggestion_id
LEFT JOIN (
    SELECT suggestion_id, COUNT(*) as authentic_votes
    FROM suggestion_votes
    WHERE vote_type = 'authentic'
    GROUP BY suggestion_id
) sv_auth ON vs.id = sv_auth.suggestion_id
LEFT JOIN cringeproof_scores cs ON vs.id = cs.suggestion_id;
