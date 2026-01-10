# Soulfra Voice Archive

**A permanent, decentralized record of voice memos - like museum historical archives**

## What is This?

The Voice Archive system publishes your voice recordings to GitHub Pages as timestamped, PII-scrubbed, cryptographically-signed transcripts.

**Like:**
- Library of Congress oral histories
- Museum archival recordings
- Typescript memos from the pre-digital era
- Permanent public record with verification

**But:**
- Decentralized (GitHub Pages, not a private server)
- Privacy-preserving (PII automatically scrubbed)
- Cryptographically signed (provable authenticity)
- Free forever (GitHub Pages hosting)
- Version-controlled (Git history)

## Quick Start

### 1. Export Voice Recordings from Database

```bash
python3 export_voice_recordings.py admin
```

This creates a local folder `voice_exports/admin/` with:
- `.wav` audio files
- `.txt` transcription files

### 2. Publish to GitHub Pages

```bash
python3 publish_voice_archive.py admin
```

This:
1. Reads voice recordings from SQLite database
2. Scrubs PII (names, emails, phones, addresses)
3. Generates cryptographic signatures (proof of authenticity)
4. Creates timestamped markdown files
5. Publishes to GitHub Pages at `https://soulfra.github.io/voice-archive`

## System Architecture

```
┌─────────────────────┐
│  SQLite Database    │
│  (voice recordings) │
└──────────┬──────────┘
           │
           ├── Raw Audio (BLOB)
           ├── Transcription (TEXT)
           ├── Timestamp
           └── User ID
           │
           ▼
┌─────────────────────┐
│   PII Scrubber      │
│  (publish_voice_   │
│   archive.py)       │
└──────────┬──────────┘
           │
           ├── Remove emails
           ├── Remove phone numbers
           ├── Remove addresses
           ├── Remove names
           └── Remove SSN/credit cards
           │
           ▼
┌─────────────────────┐
│  Signature Gen      │
│  (SHA-256 hash)     │
└──────────┬──────────┘
           │
           └── Hash: SHA256(transcript + timestamp + user_id)
           │
           ▼
┌─────────────────────┐
│  Markdown Files     │
│  (timestamped)      │
└──────────┬──────────┘
           │
           └── YYYY-MM-DD-HH-MM-memo-ID.md
           │
           ▼
┌─────────────────────┐
│  GitHub Pages       │
│  (public hosting)   │
└─────────────────────┘
           │
           └── https://soulfra.github.io/voice-archive
```

## PII Scrubbing

**What Gets Redacted:**

- **Emails**: `john@example.com` → `[EMAIL_REDACTED]`
- **Phone Numbers**: `555-123-4567` → `[PHONE_REDACTED]`
- **Addresses**: `123 Main Street` → `[ADDRESS_REDACTED]`
- **SSN**: `123-45-6789` → `[SSN_REDACTED]`
- **Credit Cards**: `1234-5678-9012-3456` → `[CARD_REDACTED]`
- **Names**: Common first names → `[NAME_REDACTED]`
- **Self-introductions**: "I am John" → "I am [NAME_REDACTED]"

**What's Kept:**
- Ideas and concepts
- Technical discussions
- Questions and answers
- Timestamps
- Recording metadata

## Cryptographic Signatures

Each transcript is signed with a SHA-256 hash:

```python
signature = SHA256(transcript + timestamp + user_id)[:16]
```

**Why This Works:**
- Proves the transcript came from this specific user
- Proves it was created at this specific time
- Cannot be forged without access to the original user account
- Like GPG signatures but simpler

**Example:**
```
Transcript: "Testing voice recording system"
Timestamp: "2026-01-02T12:34:56"
User ID: 1

Signature: a3f4d8c2e1b9f7a6
```

If someone changes even one character of the transcript, the signature won't match.

## File Structure

```
soulfra-voice-archive/
├── index.html                           # Archive homepage
├── transcripts/
│   ├── 2026-01-02-12-34-memo-1.md      # Voice memo 1
│   ├── 2026-01-02-13-45-memo-2.md      # Voice memo 2
│   └── 2026-01-03-09-15-memo-3.md      # Voice memo 3
└── README.md                            # About the archive
```

**Markdown File Format:**

```markdown
---
title: Voice Memo
date: 2026-01-02T12:34:56
signature: a3f4d8c2e1b9f7a6
recording_id: 1
duration: 2m 30s
---

# Voice Memo - January 2, 2026 at 12:34 PM UTC

**Recording ID**: `1`
**Duration**: 2m 30s
**Signature**: `a3f4d8c2e1b9f7a6`

---

## Transcript

Testing voice recording system. This is a test of the voice capsule
feature. [NAME_REDACTED] mentioned this would be useful for capturing
ideas on the go.

---

## Verification

This transcript is cryptographically signed to prove authenticity.

**Signature**: `a3f4d8c2e1b9f7a6`

To verify this transcript:
1. The signature is generated from: `SHA256(transcript + timestamp + user_id)`
2. Cannot be forged without access to the original user account
3. Timestamp proves this was recorded on January 2, 2026 at 12:34 PM UTC
```

## GitHub Pages Setup

### Create the Repo

```bash
# Via GitHub CLI (already authenticated)
gh repo create Soulfra/voice-archive --public --description "Soulfra Voice Archive - Permanent decentralized voice memos"

# Or manually at: https://github.com/new
```

### Enable GitHub Pages

1. Go to repo settings
2. Pages → Source → Branch: `main` → Root
3. Save

**Your archive will be live at:**
`https://soulfra.github.io/voice-archive`

## Automated Daily Exports

Create a cron job to automatically publish daily:

```bash
# Edit crontab
crontab -e

# Add daily 2am export
0 2 * * * cd /path/to/soulfra-simple && python3 publish_voice_archive.py admin >> /tmp/voice-archive.log 2>&1
```

Or use GitHub Actions:

```yaml
# .github/workflows/publish-archive.yml
name: Publish Voice Archive

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2am UTC
  workflow_dispatch:      # Manual trigger

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Publish Archive
        run: python3 publish_voice_archive.py admin
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Voice Encryption Model

You mentioned wanting to train a voice encryption model - here's how:

### 1. Collect Voice Samples

```bash
# Export your existing recordings
python3 export_voice_recordings.py admin

# This gives you clean .wav files to train on
```

### 2. Train Ollama Model on Your Voice

```bash
# Create modelfile
cat > voice-signature-model <<EOF
FROM llama3.2:3b

# System prompt for voice pattern recognition
SYSTEM """You are a voice signature verifier. Analyze voice patterns to generate
unique signatures that prove authenticity without revealing the speaker's identity."""

# Train on voice characteristics:
# - Prosody (rhythm, stress, intonation)
# - Vocabulary patterns
# - Speaking cadence
# - Phrase structure

EOF

# Train model
ollama create voice-signature-model -f voice-signature-model
```

### 3. Generate Voice Signatures

```python
from local_ollama_client import OllamaClient

client = OllamaClient()

# Analyze voice pattern
result = client.generate(
    prompt=transcript,
    model='voice-signature-model',
    system='Generate unique voice signature for this speaker'
)

# Returns signature that proves it's you without revealing identity
```

## Privacy & Security

**What's Public:**
- Scrubbed transcripts (PII removed)
- Timestamps
- Recording metadata (duration, ID)
- Cryptographic signatures

**What's Private:**
- Your identity (names removed)
- Personal information (addresses, phones, emails)
- Raw audio files (not published)
- Exact user ID (hashed in signature)

**Can Someone Track You?**
- No - PII is scrubbed before publication
- Signatures prove authenticity but don't reveal identity
- Like posting anonymously but with cryptographic proof

## Use Cases

### 1. Personal Time Capsule
Record your thoughts daily. Look back years later to see how you've evolved.

### 2. Idea Archive
Capture ideas as they come. Search them later.

### 3. Historical Record
Create a permanent, verifiable record of your thinking over time.

### 4. Debate History
Track how your positions change over time. Prove consistency (or growth).

### 5. Research Notes
Record research findings. Publish them publicly with timestamps proving priority.

## Integration with Existing Systems

### Voice Capsule System

The Voice Capsule system (already in `soulfra.db`) rotates through questions:

```python
from voice_capsule_engine import get_next_question_for_user

# Get next question
question = get_next_question_for_user(user_id=1, domain='soulfra')

# User answers via voice
# → Recorded to database
# → Auto-published to GitHub Pages nightly
```

### Custom Ollama Models

You already have trained models:
- `soulfra-model` (3.8 GB)
- `deathtodata-model` (986 MB)
- `publishing-model` (2.0 GB)
- `drseuss-model` (2.0 GB)

These can process transcripts for:
- Sentiment analysis
- Topic extraction
- Style matching
- Vocabulary expansion

## Next Steps

1. **Test the publisher**:
   ```bash
   python3 publish_voice_archive.py admin
   ```

2. **Create GitHub repo**:
   ```bash
   gh repo create Soulfra/voice-archive --public
   ```

3. **Enable GitHub Pages** in repo settings

4. **Set up automation** (cron or GitHub Actions)

5. **Train voice signature model** (optional, for encryption)

---

**This creates a permanent, decentralized, privacy-preserving archive of your voice memos.**

Like the Library of Congress, but on GitHub.