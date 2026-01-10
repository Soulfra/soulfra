-- Training Contributions Table
-- Unified storage for all multi-modal training data (voice, screenshot, drawing, text)
-- Tracks user ownership with GDPR compliance and cryptographic proof

CREATE TABLE IF NOT EXISTS training_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,

    -- Input modality
    modality TEXT NOT NULL,  -- 'voice', 'screenshot', 'drawing', 'text'

    -- Extracted content
    extracted_text TEXT,  -- Actual content extracted (Whisper, OCR, etc.)

    -- Cryptographic proof
    content_hash TEXT NOT NULL,  -- SHA-256 of content
    qr_verification_code TEXT,  -- Scannable proof of contribution
    upc_barcode TEXT,  -- UPC format (for physical/retail compatibility)
    bip39_hash TEXT,  -- Bitcoin BIP-39 mnemonic format
    ethereum_checksum TEXT,  -- Ethereum address format

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Privacy controls (GDPR compliance)
    user_can_export BOOLEAN DEFAULT 1,  -- Right to data portability
    user_can_delete BOOLEAN DEFAULT 1,  -- Right to erasure
    included_in_training BOOLEAN DEFAULT 1,  -- Opt-out flag

    -- Proof-of-work tracking
    snapshot_hash TEXT,  -- Which snapshot includes this?
    github_published BOOLEAN DEFAULT 0,

    -- Original source reference
    source_table TEXT,  -- 'simple_voice_recordings', 'screenshots', etc.
    source_id INTEGER,  -- ID in original table

    -- Metadata
    file_size INTEGER,  -- Original file size in bytes
    processing_method TEXT,  -- 'whisper', 'easyocr', 'manual', etc.
    quality_score REAL,  -- 0.0-1.0 confidence/quality rating

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_training_modality ON training_contributions(modality);
CREATE INDEX IF NOT EXISTS idx_training_user ON training_contributions(user_id);
CREATE INDEX IF NOT EXISTS idx_training_hash ON training_contributions(content_hash);
CREATE INDEX IF NOT EXISTS idx_training_included ON training_contributions(included_in_training);
CREATE INDEX IF NOT EXISTS idx_training_created ON training_contributions(created_at DESC);

-- User Lore Table
-- AI-generated personality profiles based on color choice + voice sentiment
CREATE TABLE IF NOT EXISTS user_lore (
    user_id INTEGER PRIMARY KEY,

    -- User branding choices
    color_choice TEXT,  -- Hex code (e.g., "#ff006e")
    secondary_color TEXT,  -- Optional accent color

    -- AI-generated personality
    personality_archetype TEXT,  -- "Rebellious Optimist", "Chaotic Scholar", etc.
    origin_story TEXT,  -- Long-form AI-generated backstory
    powers TEXT,  -- JSON list of traits/strengths
    weaknesses TEXT,  -- Humanizing flaws

    -- Custom theming
    css_theme_url TEXT,  -- Path to generated custom stylesheet
    custom_css TEXT,  -- Inline CSS overrides

    -- Sentiment analysis
    voice_sentiment_avg REAL,  -- Average sentiment score from voice memos
    voice_energy_level TEXT,  -- 'calm', 'energetic', 'intense'

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Activity Log Table
-- Tamper-proof logging with cryptographic proof
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Event details
    log_type TEXT NOT NULL,  -- 'user_login', 'voice_upload', 'screenshot_ocr', 'idea_saved', etc.
    user_id INTEGER,
    action_data TEXT,  -- JSON details of the action

    -- Request metadata
    ip_address TEXT,
    user_agent TEXT,
    endpoint TEXT,  -- API route that triggered this log

    -- Cryptographic proof
    proof_hash TEXT NOT NULL,  -- SHA-256 of log entry (tamper-proof)
    previous_log_hash TEXT,  -- Hash chain linking to previous log

    -- Result tracking
    success BOOLEAN DEFAULT 1,
    error_message TEXT,  -- If failed, why?

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for activity log
CREATE INDEX IF NOT EXISTS idx_activity_type ON activity_log(log_type);
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_hash ON activity_log(proof_hash);
