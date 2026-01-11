-- Email Outbox Table
-- Stores emails BEFORE they're sent (internal mailbox/drafts)
-- Like Resend's test email system

CREATE TABLE IF NOT EXISTS email_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Email details
    to_address TEXT NOT NULL,
    from_address TEXT DEFAULT 'StPetePros <noreply@soulfra.com>',
    subject TEXT NOT NULL,
    body_html TEXT,
    body_text TEXT,

    -- Attachments (JSON array of {filename, content_base64, mime_type})
    attachments TEXT,

    -- Recovery code info (for StPetePros emails)
    professional_id INTEGER,
    recovery_code TEXT,

    -- Status tracking
    status TEXT DEFAULT 'draft',  -- 'draft', 'queued', 'sending', 'sent', 'failed'
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,

    -- Token cost (1 token = 1 email sent)
    token_cost INTEGER DEFAULT 1,
    sent_by_user_id INTEGER,

    FOREIGN KEY (professional_id) REFERENCES professionals(id),
    FOREIGN KEY (sent_by_user_id) REFERENCES users(id)
);

-- Index for querying by status
CREATE INDEX IF NOT EXISTS idx_email_outbox_status ON email_outbox(status);

-- Index for querying by professional
CREATE INDEX IF NOT EXISTS idx_email_outbox_professional ON email_outbox(professional_id);

-- Index for querying recent emails
CREATE INDEX IF NOT EXISTS idx_email_outbox_created ON email_outbox(created_at DESC);
