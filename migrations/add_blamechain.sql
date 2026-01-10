-- Blamechain: Immutable Message Edit History
--
-- This creates an accountability system where users can edit messages,
-- but the "chain" permanently records every edit with timestamps.
--
-- Use case: Tribunal can examine edit history as evidence

CREATE TABLE IF NOT EXISTS message_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Reference to original message
    message_id INTEGER NOT NULL,
    message_table TEXT NOT NULL,  -- 'messages', 'irc_messages', 'dm_messages', etc.

    -- Edit tracking
    version_number INTEGER NOT NULL,  -- 1 = original, 2 = first edit, etc.
    content TEXT NOT NULL,  -- Message content at this version

    -- Accountability
    edited_by_user_id INTEGER NOT NULL,
    edit_reason TEXT,  -- Optional: Why was this edited?

    -- Blamechain hash (SHA-256 of previous_hash + content + timestamp)
    content_hash TEXT NOT NULL,  -- Hash of this version's content
    previous_hash TEXT,  -- Links to previous version (NULL for v1)
    chain_hash TEXT NOT NULL UNIQUE,  -- Immutable proof: hash(previous_hash + content_hash + timestamp)

    -- Metadata
    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    editor_ip TEXT,  -- Optional: Track where edit came from
    editor_platform TEXT,  -- 'web', 'mobile', 'qr_chat', etc.

    -- Tribunal evidence flags
    flagged_for_tribunal BOOLEAN DEFAULT 0,
    tribunal_submission_id INTEGER,  -- Link to kangaroo_submissions if used as evidence

    FOREIGN KEY (edited_by_user_id) REFERENCES users(id),
    FOREIGN KEY (tribunal_submission_id) REFERENCES kangaroo_submissions(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_history_message
    ON message_history(message_table, message_id, version_number);

CREATE INDEX IF NOT EXISTS idx_message_history_editor
    ON message_history(edited_by_user_id);

CREATE INDEX IF NOT EXISTS idx_message_history_tribunal
    ON message_history(flagged_for_tribunal, tribunal_submission_id);

CREATE INDEX IF NOT EXISTS idx_message_history_chain
    ON message_history(chain_hash);


-- Add edit tracking columns to existing message tables
-- (These columns indicate if a message has been edited)

ALTER TABLE messages ADD COLUMN edited BOOLEAN DEFAULT 0;
ALTER TABLE messages ADD COLUMN edit_count INTEGER DEFAULT 0;
ALTER TABLE messages ADD COLUMN last_edited_at TIMESTAMP;

ALTER TABLE irc_messages ADD COLUMN edited BOOLEAN DEFAULT 0;
ALTER TABLE irc_messages ADD COLUMN edit_count INTEGER DEFAULT 0;
ALTER TABLE irc_messages ADD COLUMN last_edited_at TIMESTAMP;

ALTER TABLE dm_messages ADD COLUMN edited BOOLEAN DEFAULT 0;
ALTER TABLE dm_messages ADD COLUMN edit_count INTEGER DEFAULT 0;
ALTER TABLE dm_messages ADD COLUMN last_edited_at TIMESTAMP;


-- View: Get full edit history for any message
CREATE VIEW IF NOT EXISTS v_message_blamechain AS
SELECT
    mh.message_id,
    mh.message_table,
    mh.version_number,
    mh.content,
    mh.edited_by_user_id,
    u.username AS editor_username,
    mh.edit_reason,
    mh.edited_at,
    mh.content_hash,
    mh.previous_hash,
    mh.chain_hash,
    mh.flagged_for_tribunal,
    mh.tribunal_submission_id,
    -- Show if this edit was suspicious (quick edits, multiple versions, etc.)
    CASE
        WHEN mh.version_number > 3 THEN 'HIGH_EDIT_COUNT'
        WHEN mh.edit_reason IS NULL THEN 'NO_REASON_GIVEN'
        ELSE 'NORMAL'
    END AS suspicion_level
FROM message_history mh
LEFT JOIN users u ON mh.edited_by_user_id = u.id
ORDER BY mh.message_table, mh.message_id, mh.version_number;


-- Trigger: Auto-create initial history entry when message is created
-- (This ensures every message starts with version 1 in the blamechain)

-- Note: SQLite doesn't support triggers that insert into same table during INSERT,
-- so initial history entry must be created manually via API
