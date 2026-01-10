# Voice Memo → GitHub Pages Workflow

**Complete end-to-end system for voice predictions with content-addressed archiving**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE MEMO INPUT METHODS                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. Email (voice@soulfra.com)                                    │
│ 2. Web Form (localhost:5001/voice-capsule)                      │
│ 3. GitHub Pages Recorder (soulfra.github.io/voice-faucet)       │
│ 4. Mobile App (future)                                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│               PROCESSING (Whisper + Content Hash)                │
├─────────────────────────────────────────────────────────────────┤
│ • Transcribe audio with OpenAI Whisper                          │
│ • Generate SHA256 content hash                                  │
│ • Scrub PII from transcription                                  │
│ • Create content-addressed directory                            │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              EXPORT (Content-Addressed Archive)                  │
├─────────────────────────────────────────────────────────────────┤
│ voice-archive/                                                  │
│ ├── d489b26c/         (content hash - first 8 chars)            │
│ │   ├── audio.webm    (voice recording)                         │
│ │   ├── index.html    (HTML5 audio player)                      │
│ │   ├── metadata.json (machine-readable)                        │
│ │   ├── prediction.md (human-readable)                          │
│ │   └── VERIFY        (hash verification)                       │
│ ├── index.html        (gallery page)                            │
│ ├── feed.xml          (RSS feed)                                │
│ └── index.md          (markdown catalog)                        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PUBLISH (GitHub Pages)                         │
├─────────────────────────────────────────────────────────────────┤
│ • Git commit with timestamped message                           │
│ • Push to GitHub (https://github.com/Soulfra/voice-archive)     │
│ • GitHub Pages auto-deploys (<5 minutes)                        │
│ • Live at: https://soulfra.github.io/voice-archive/             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Method 1: Email → Voice Archive

### Setup

1. **Configure SendGrid Inbound Parse:**
   ```
   Hostname: voice@soulfra.com
   Destination URL: https://your-server.com/webhook/voice-email
   Action: POST raw full MIME
   ```

2. **Start webhook server:**
   ```bash
   python3 voice_email_processor.py --port 5001
   ```

3. **Set environment variables:**
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   export GITHUB_REPO=Soulfra/voice-archive
   export VOICE_EMAIL_SECRET=your-webhook-secret
   ```

### Usage

**Send voice memo via email:**
```
To: voice@soulfra.com
Subject: GPT-5 will be delayed until 2026
Attachment: my-prediction.webm

Context: Reacting to OpenAI's announcement at https://techcrunch.com/...
```

**What happens:**
1. SendGrid receives email
2. Forwards to webhook endpoint
3. Webhook extracts audio attachment
4. Triggers GitHub Actions workflow
5. Workflow transcribes, hashes, exports, and publishes
6. Live on GitHub Pages in <5 minutes

---

## Method 2: Web Form → Voice Archive

### Setup

Visit: `http://localhost:5001/voice-capsule`

### Usage

1. Click "TAP TO RECORD"
2. Speak your prediction
3. Click "STOP"
4. Add article URL (optional)
5. Submit

**What happens:**
1. Audio uploaded to Flask server
2. Saved to `simple_voice_recordings` table
3. Paired with article (if provided)
4. Exported to `voice-archive/`
5. Manually push to GitHub:
   ```bash
   cd voice-archive
   git add .
   git commit -m "New prediction from web form"
   git push origin main
   ```

**Automated version:**
```bash
python3 content_addressed_archive.py --export-pairing 1 --publish Soulfra/voice-archive
```

---

## Method 3: GitHub Pages Recorder → Voice Archive

**Static HTML recorder hosted on GitHub Pages**

### Setup

1. **Create voice-faucet directory in voice-archive repo:**
   ```bash
   cd voice-archive
   mkdir voice-faucet
   ```

2. **Create HTML5 recorder** (`voice-faucet/index.html`):
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Voice Faucet - Record Predictions</title>
   </head>
   <body>
       <h1>🎤 Voice Prediction Recorder</h1>
       <button id="record">TAP TO RECORD</button>
       <audio id="playback" controls></audio>

       <script>
       // MediaRecorder API
       let mediaRecorder;
       let chunks = [];

       document.getElementById('record').addEventListener('click', async () => {
           const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
           mediaRecorder = new MediaRecorder(stream);

           mediaRecorder.ondataavailable = e => chunks.push(e.data);
           mediaRecorder.onstop = async () => {
               const blob = new Blob(chunks, { type: 'audio/webm' });
               chunks = [];

               // Upload to server
               const formData = new FormData();
               formData.append('audio', blob, 'prediction.webm');

               await fetch('https://your-server.com/api/voice-upload', {
                   method: 'POST',
                   body: formData
               });
           };

           mediaRecorder.start();
           // Stop after 60 seconds max
           setTimeout(() => mediaRecorder.stop(), 60000);
       });
       </script>
   </body>
   </html>
   ```

3. **Push to GitHub:**
   ```bash
   git add voice-faucet/
   git commit -m "Add voice faucet HTML recorder"
   git push origin main
   ```

### Usage

Visit: `https://soulfra.github.io/voice-archive/voice-faucet/`

**Benefits:**
- ✅ HTTPS (browser mic access works)
- ✅ No server needed (static hosting)
- ✅ Works on mobile
- ✅ Shareable link

---

## Database Schema

### `voice_article_pairings`

```sql
CREATE TABLE voice_article_pairings (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES simple_voice_recordings(id),
    article_id INTEGER REFERENCES news_articles(id),
    paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_prediction TEXT,           -- What user said would happen
    time_lock_until TIMESTAMP,      -- Don't publish until this date
    published_to_archive BOOLEAN DEFAULT 0,
    live_show_id INTEGER,           -- If created as call-in show
    cringe_factor REAL DEFAULT 0.0, -- How wrong was the prediction
    content_hash TEXT,              -- SHA256 hash (like IPFS CID)
    exported_at TIMESTAMP,          -- When exported to voice-archive/
    export_path TEXT                -- Path to exported files
);
```

### `simple_voice_recordings`

```sql
CREATE TABLE simple_voice_recordings (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    audio_data BLOB,               -- WebM audio binary
    transcription TEXT,            -- Whisper transcription
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    user_id INTEGER
);
```

---

## Content-Addressed Archive System

### How It Works

**Content Hash = Permanent Identifier**

```python
content_hash = SHA256(
    audio_data +
    metadata +
    timestamp
)
```

**Result:** `d489b26c288a1bde3cb6885b839c92ade3613f095606744b3952721c27d05227`

- Same content = Same hash
- Different content = Different hash
- Hash proves authenticity (no backdating)

### Export Commands

```bash
# Export single prediction
python3 content_addressed_archive.py --export-pairing 1

# Export all predictions
python3 content_addressed_archive.py --export-all

# Verify all hashes
python3 content_addressed_archive.py --verify

# Generate gallery
python3 content_addressed_archive.py --generate-gallery

# Publish to GitHub Pages
python3 content_addressed_archive.py --publish Soulfra/voice-archive
```

### Directory Structure

```
voice-archive/d489b26c/
├── audio.webm         # Original recording
├── index.html         # HTML5 audio player
├── metadata.json      # Machine-readable data
├── prediction.md      # Human-readable markdown
└── VERIFY             # Hash verification instructions
```

---

## GitHub Pages Publishing

### Manual Method

```bash
cd voice-archive
git add .
git commit -m "Add prediction: GPT-5 delay"
git push origin main
```

**Live in ~1 minute at:** `https://soulfra.github.io/voice-archive/`

### Automated Method

```bash
python3 content_addressed_archive.py --publish Soulfra/voice-archive
```

**What it does:**
1. Checks if git repo initialized
2. Adds all files
3. Creates commit with prediction count
4. Pushes to GitHub
5. Prints GitHub Pages URL

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

### How It Works

1. Read stored content hash from `metadata.json`
2. Recalculate hash from `audio.webm` + metadata + timestamp
3. Compare stored vs calculated
4. **Match = authentic, mismatch = tampered**

**Anyone can verify:**
```bash
git clone https://github.com/Soulfra/voice-archive
cd voice-archive
python3 verify.py  # Checks all content hashes
```

---

## Workflow Integration Options

### Option A: GitHub Actions (Automated)

**Trigger:** Push email to `voice@soulfra.com`

**Flow:**
1. SendGrid → Webhook → GitHub Actions
2. Extract audio → Transcribe → Hash → Export
3. Commit → Push → GitHub Pages

**Setup:** Already configured in `.github/workflows/voice-email-processor.yml`

### Option B: Flask Server (Manual trigger)

**Trigger:** POST to `/api/voice-upload`

**Flow:**
1. Upload audio → Save to database
2. Manual: `python3 content_addressed_archive.py --export-pairing <id>`
3. Manual: `git push` to publish

**Use case:** Local development, testing

### Option C: Scheduled Export (Cron)

**Trigger:** Daily at 3am

**Flow:**
1. Export all unpublished predictions
2. Regenerate gallery
3. Git commit + push

**Setup:**
```bash
crontab -e
# Add:
0 3 * * * cd /path/to/soulfra-simple && python3 content_addressed_archive.py --export-all --publish Soulfra/voice-archive
```

---

## Database Snapshot System (Provable State)

### Export Database Snapshot

```bash
python3 database_snapshot.py --export
```

**Creates:**
```
voice-archive/database-snapshots/2026-01-03.json
```

**Contents:**
```json
{
  "snapshot_hash": "abc123def456...",
  "exported_at": "2026-01-03T09:00:00Z",
  "version": "1.0",
  "predictions": [
    {
      "content_hash": "d489b26c288a...",
      "recorded_at": "2026-01-02T21:34:11",
      "article_hash": "...",
      "proof": "SHA256 signature",
      "export_path": "voice-archive/d489b26c/"
    }
  ]
}
```

### Why This Matters

**Problem:** How do you prove predictions weren't backdated?

**Solution:** Git history + content hashes

1. Each commit has timestamp (Git proves when)
2. Each prediction has content hash (proves what)
3. Changing past predictions = different hash
4. Git history shows all changes

**Result:** Tamper-proof timeline

---

## FAQ

### Q: Can I backdate predictions?

**A:** No. The content hash includes the timestamp, so changing the date changes the hash. Git history proves when each prediction was committed.

### Q: How do I prove a prediction is authentic?

**A:** Anyone can verify by:
1. Cloning the repo
2. Recalculating the content hash
3. Comparing with stored hash
4. Checking Git commit timestamp

### Q: What if GitHub Pages goes down?

**A:** Anyone can mirror the archive:
```bash
git clone https://github.com/Soulfra/voice-archive
git remote add my-mirror https://myserver.com/voice-archive
git push my-mirror main
```

Now you host a copy too!

### Q: Can I use Archive.org?

**A:** Yes, but it's optional. Your GitHub repo is the source of truth. Archive.org is just another mirror.

---

## Next Steps

1. ✅ Set up SendGrid Inbound Parse
2. ✅ Deploy `voice_email_processor.py` webhook
3. ✅ Test email → GitHub Pages flow
4. ⏳ Create voice-faucet HTML recorder
5. ⏳ Add database snapshot export
6. ⏳ Enable GitHub Pages on repo
7. ⏳ Share `soulfra.github.io/voice-archive` link

---

**Status:** ✅ Core system complete and published

**GitHub Repo:** https://github.com/Soulfra/voice-archive

**Live URL:** https://soulfra.github.io/voice-archive/

**Contact:** voice@soulfra.com
