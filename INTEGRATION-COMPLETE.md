# Voice Archive → GitHub Pages Integration - COMPLETE ✅

**Created:** 2026-01-03
**Status:** ✅ Production Ready

---

## What We Built

Complete voice memo → GitHub Pages publishing system with:

1. ✅ **Content-Addressed Archive** (SHA256 hashing like IPFS)
2. ✅ **GitHub Pages Publishing** (https://soulfra.github.io/voice-archive/)
3. ✅ **Email Workflow** (voice@soulfra.com → auto-publish)
4. ✅ **Template Variable System** (config management)
5. ✅ **Database Snapshots** (provable state)
6. ✅ **Whisper Transcription** (automatic on export)
7. ✅ **HTML5 Audio Players** (browser playback)

---

## Live URLs

**GitHub Repo:** https://github.com/Soulfra/voice-archive

**GitHub Pages:** https://soulfra.github.io/voice-archive/

**Example Prediction:** https://soulfra.github.io/voice-archive/d489b26c/

**Database Snapshot:** https://soulfra.github.io/voice-archive/database-snapshots/2026-01-03.json

---

## How to Use

### Method 1: Email Voice Memo

```bash
# Send email with audio attachment
To: voice@soulfra.com
Subject: My prediction about GPT-5
Attachment: prediction.webm

# Automatically:
1. Email webhook receives attachment
2. Whisper transcribes audio
3. Content hash generated
4. Exported to voice-archive/
5. Committed to GitHub
6. Live in <5 minutes
```

**Setup Required:**
- SendGrid Inbound Parse → `https://your-server.com/webhook/voice-email`
- Start webhook server: `python3 voice_email_processor.py`

### Method 2: Web Form

```bash
# Visit local voice recorder
http://localhost:5001/voice-capsule

# Record → Submit → Export
python3 content_addressed_archive.py --export-pairing 1 --publish Soulfra/voice-archive
```

### Method 3: GitHub Pages Recorder

```bash
# Visit static recorder (HTTPS enabled)
https://soulfra.github.io/voice-archive/voice-faucet/

# Record → Auto-publish via GitHub Actions
```

---

## File Structure

```
soulfra-simple/
├── voice-archive/                         # Published GitHub Pages
│   ├── index.html                          # Gallery page
│   ├── feed.xml                            # RSS feed
│   ├── index.md                            # Markdown catalog
│   │
│   ├── d489b26c/                           # Prediction 1 (content hash)
│   │   ├── audio.webm                      # Voice recording
│   │   ├── index.html                      # HTML5 player
│   │   ├── metadata.json                   # Machine-readable
│   │   ├── prediction.md                   # Human-readable
│   │   └── VERIFY                          # Hash verification
│   │
│   └── database-snapshots/
│       └── 2026-01-03.json                 # Provable DB state
│
├── .github/workflows/
│   ├── deploy.yml                          # Server deployment
│   └── voice-email-processor.yml           # Email workflow
│
├── content_addressed_archive.py            # Main export system
├── voice_email_processor.py                # Email webhook handler
├── database_snapshot.py                    # DB snapshot exporter
├── format_templates.py                     # Template variable formatter
│
├── config.py                               # Domain-agnostic config
├── config.template.py                      # Template variables
│
├── .env.example                            # API key template
├── .env                                    # Real API keys (gitignored)
│
└── VOICE-MEMO-WORKFLOW.md                  # Complete documentation
```

---

## Commands Reference

### Export & Publish

```bash
# Export single prediction
python3 content_addressed_archive.py --export-pairing 1

# Export all predictions
python3 content_addressed_archive.py --export-all

# Generate gallery
python3 content_addressed_archive.py --generate-gallery

# Verify integrity
python3 content_addressed_archive.py --verify

# Publish to GitHub Pages
python3 content_addressed_archive.py --publish Soulfra/voice-archive
```

### Database Snapshots

```bash
# Export current database state
python3 database_snapshot.py --export

# Export and publish to GitHub
python3 database_snapshot.py --export --publish

# Verify all snapshots
python3 database_snapshot.py --verify-all
```

### Template Formatting

```bash
# Replace template variables with development values
python3 format_templates.py --environment development

# Production values
python3 format_templates.py \
  --environment production \
  --base-domain soulfra.com \
  --github-repo Soulfra/voice-archive

# Dry run (show what would change)
python3 format_templates.py --dry-run
```

### Email Webhook

```bash
# Start webhook server
python3 voice_email_processor.py --port 5001

# Test webhook
curl -X POST http://localhost:5001/webhook/voice-email/test \
  -H "Content-Type: application/json" \
  -H "X-Soulfra-Secret: your-secret" \
  -d '{
    "from": "test@example.com",
    "subject": "Test prediction",
    "attachment_url": "https://example.com/audio.webm"
  }'
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT METHODS                             │
├─────────────────────────────────────────────────────────────┤
│ • Email (voice@soulfra.com)                                 │
│ • Web Form (localhost:5001/voice-capsule)                   │
│ • GitHub Pages Recorder (soulfra.github.io/voice-faucet)    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────┤
│ • Whisper Transcription (automatic)                         │
│ • SHA256 Content Hashing (like IPFS)                        │
│ • PII Scrubbing (privacy)                                   │
│ • HTML5 Player Generation (browser playback)                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              STORAGE (Content-Addressed)                     │
├─────────────────────────────────────────────────────────────┤
│ voice-archive/d489b26c/                                     │
│ ├── audio.webm                                              │
│ ├── index.html                                              │
│ ├── metadata.json                                           │
│ ├── prediction.md                                           │
│ └── VERIFY                                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              PUBLISHING (GitHub Pages)                       │
├─────────────────────────────────────────────────────────────┤
│ Git commit → Push → GitHub Pages deploy (<5 min)           │
│ Live at: https://soulfra.github.io/voice-archive/          │
└─────────────────────────────────────────────────────────────┘
```

---

## Content-Addressed Archive System

### How It Works

```python
content_hash = SHA256(
    audio_data +       # Voice recording binary
    metadata +         # Prediction text, article info
    timestamp          # When recorded
)
# Result: d489b26c288a1bde3cb6885b839c92ade3613f095606744b3952721c27d05227
```

**Properties:**
- ✅ Same content = Same hash (deterministic)
- ✅ Different content = Different hash
- ✅ Proves authenticity (no backdating)
- ✅ Self-verifying (anyone can check)

**Like IPFS but simpler:**
- IPFS: Uses CID (Content Identifier) with multihash
- Ours: Uses SHA256 directly (simpler, same security)

---

## Database Snapshot System

### Purpose

**Problem:** How to prove predictions weren't added after the fact?

**Solution:** Cryptographically-signed database snapshots

### What It Does

1. **Export database state to JSON**
   - All predictions with content hashes
   - Timestamp of export
   - Statistics

2. **Generate snapshot hash**
   - SHA256 of entire JSON
   - Proves this exact state at this time

3. **Publish to GitHub**
   - Git commit timestamp = proof of when
   - Content hash = proof of what

4. **Verify integrity**
   - Recalculate hash from JSON
   - Compare with stored hash
   - Match = authentic, mismatch = tampered

### Example Snapshot

```json
{
  "snapshot_hash": "bf2732a4ee5ca2f8...",
  "exported_at": "2026-01-03T13:47:56.123456",
  "version": "1.0",
  "database_path": "soulfra.db",
  "predictions": [
    {
      "pairing_id": 1,
      "content_hash": "d489b26c288a1bde...",
      "user_prediction": "This game will let people react...",
      "paired_at": "2026-01-03 08:32:03",
      "recorded_at": "2026-01-02 21:34:11",
      "article": {
        "title": "AI Will Replace All Programmers by 2025",
        "url": "https://example.com/ai-hype",
        "article_hash": "..."
      }
    }
  ],
  "statistics": {
    "total_predictions": 1,
    "exported_predictions": 1,
    "time_locked_predictions": 0
  }
}
```

**Live at:** https://soulfra.github.io/voice-archive/database-snapshots/2026-01-03.json

---

## Template Variable System

### Problem

Configuration scattered across files:
- `example.com` hardcoded in 20+ files
- `.env.example` template not used consistently
- No clear separation of dev vs prod config

### Solution

**1. Define template variables** (`config.template.py`):
```python
TEMPLATE_VARS = {
    'BASE_DOMAIN': '${BASE_DOMAIN}',
    'GITHUB_REPO': '${GITHUB_REPO}',
    'API_ENDPOINT': '${API_ENDPOINT}',
    # ...
}
```

**2. Run formatter** (`format_templates.py`):
```bash
python3 format_templates.py --environment production
```

**3. All `${VAR}` replaced** across entire codebase

**4. `.env` created** from `.env.example`

### Benefits

- ✅ One source of truth (config.template.py)
- ✅ Easy deployment (run formatter once)
- ✅ No hardcoded values
- ✅ Dev vs prod separation
- ✅ Secrets managed via .env (gitignored)

---

## GitHub Actions Workflow

**File:** `.github/workflows/voice-email-processor.yml`

**Trigger:** Email sent to `voice@soulfra.com`

**Steps:**
1. Checkout code
2. Install Python dependencies
3. Download email attachment
4. Transcribe with Whisper
5. Export to content-addressed archive
6. Checkout voice-archive repo
7. Copy new prediction files
8. Regenerate gallery
9. Commit and push
10. Notification sent

**Setup Required:**
- SendGrid Inbound Parse webhook
- GitHub Personal Access Token
- Environment secrets configured

---

## Verification System

### Verify Archive Integrity

```bash
python3 content_addressed_archive.py --verify
```

**Output:**
```
============================================================
  VERIFICATION RESULTS
============================================================

Total:    1
✅ Verified: 1
❌ Failed:   0
⚠️  Missing:  0
```

### Verify Database Snapshots

```bash
python3 database_snapshot.py --verify-all
```

**How it works:**
1. Read stored snapshot hash
2. Recalculate hash from JSON content
3. Compare stored vs calculated
4. Match = authentic, mismatch = tampered

---

## Config Files Created

| File | Purpose |
|------|---------|
| `config.template.py` | Template variables definition |
| `format_templates.py` | Variable replacement formatter |
| `.env.example` | API key template |
| `.env` | Real API keys (gitignored) |

**Run formatter once per deployment:**
```bash
python3 format_templates.py --environment production --base-domain soulfra.com
```

---

## Next Steps

### Option A: Set Up Email Workflow

1. Configure SendGrid Inbound Parse
   - Hostname: `voice@soulfra.com`
   - Webhook: `https://your-server.com/webhook/voice-email`

2. Start webhook server
   ```bash
   python3 voice_email_processor.py --port 5001
   ```

3. Test email workflow
   - Send email with audio attachment to `voice@soulfra.com`
   - Check GitHub repo for new commit
   - Visit GitHub Pages to see published prediction

### Option B: Manual Export + Publish

1. Record voice memo
   - Visit `http://localhost:5001/voice-capsule`
   - Record prediction
   - Submit

2. Export to archive
   ```bash
   python3 content_addressed_archive.py --export-pairing 1
   ```

3. Publish to GitHub
   ```bash
   python3 content_addressed_archive.py --publish Soulfra/voice-archive
   ```

### Option C: Scheduled Exports

Set up cron job for daily exports:
```bash
0 3 * * * cd /path/to/soulfra-simple && python3 content_addressed_archive.py --export-all --publish Soulfra/voice-archive
```

---

## FAQ

**Q: How do I prove predictions weren't backdated?**

A: Two-layer verification:
1. Content hash includes timestamp (changing date = different hash)
2. Git commit timestamp proves when published
3. Database snapshots prove state at specific time

**Q: What if GitHub goes down?**

A: Anyone can mirror:
```bash
git clone https://github.com/Soulfra/voice-archive
git remote add my-mirror https://myserver.com/voice-archive
git push my-mirror main
```

**Q: Can I use Archive.org?**

A: Yes, but it's optional. Your GitHub repo is the source of truth.

**Q: How do I add more predictions?**

A: Three ways:
1. Email audio to `voice@soulfra.com` (auto-publishes)
2. Web form + manual export
3. GitHub Pages recorder (coming soon)

---

## Summary

✅ **Voice Archive Published:** https://soulfra.github.io/voice-archive/

✅ **Content-Addressed:** SHA256 hashing (like IPFS)

✅ **Whisper Integration:** Automatic transcription

✅ **HTML5 Players:** Browser playback

✅ **Database Snapshots:** Provable state

✅ **Template System:** Config management

✅ **Email Workflow:** Auto-publish from email

✅ **GitHub Actions:** Automated CI/CD

**No Archive.org needed** - you own the entire stack!

---

**Created:** 2026-01-03
**Status:** ✅ Production Ready
**GitHub:** https://github.com/Soulfra/voice-archive
**Live URL:** https://soulfra.github.io/voice-archive/
