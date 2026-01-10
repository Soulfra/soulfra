-- Add content_hash column to voice_article_pairings
-- Content hash = SHA256(audio_data + metadata + timestamp)
-- Makes each prediction content-addressable (like IPFS)

ALTER TABLE voice_article_pairings
ADD COLUMN content_hash TEXT;

-- Create index for fast lookup by hash
CREATE INDEX idx_pairings_content_hash ON voice_article_pairings(content_hash);

-- Add export metadata
ALTER TABLE voice_article_pairings
ADD COLUMN exported_at TIMESTAMP;

ALTER TABLE voice_article_pairings
ADD COLUMN export_path TEXT;

-- Comments
COMMENT ON COLUMN voice_article_pairings.content_hash IS 'SHA256 hash of (audio + metadata + timestamp) - content-addressable identifier';
COMMENT ON COLUMN voice_article_pairings.exported_at IS 'When this prediction was last exported to voice-archive/';
COMMENT ON COLUMN voice_article_pairings.export_path IS 'Path to exported files (e.g., voice-archive/a3b2c1d4/)';
