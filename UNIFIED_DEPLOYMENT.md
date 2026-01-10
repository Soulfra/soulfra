# Unified Deployment System

**Problem Solved:** "we're working all over the place but our workflows need to be sync'd and matched like continuous batching or messaging"

This system ensures all repos stay synchronized automatically, preventing the 404 errors and scattered workflow issues.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Voice Input (Any Device)              │
│              Drop audio into import_voice_memo.py       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              publish_unified.py (THIS FILE)              │
│    Single command updates ALL repos simultaneously      │
└─────┬───────────────────────────────────────────────┬───┘
      │                                               │
      ▼                                               ▼
┌─────────────────┐                         ┌──────────────────┐
│  voice-archive  │                         │ soulfra.github.io│
│ (CringeProof)   │                         │   (Soulfra Hub)  │
│ cringeproof.com │                         │  soulfra.com     │
└─────────────────┘                         └──────────────────┘
      │                                               │
      ├─ /tv (Live Cal/Arty chat)                   ├─ /tv
      ├─ /projects.html (Dashboard)                 ├─ /projects.html
      ├─ /voice-recorder.html                       ├─ /index.html
      └─ /u/{user} profiles                         └─ /calriven, /deathtodata, etc.
```

## Why This Matters

### Before (Broken Workflow)
```bash
# Work happens all over the place:
cd soulfra.github.io
vim tv/index.html
git add . && git commit -m "Update TV"
git push
# Result: 404 at soulfra.github.io/tv because wrong repo!

cd ../voice-archive
# Manually copy files... forget steps... desync happens
```

### After (Unified Workflow)
```bash
# Single command syncs EVERYTHING:
python3 publish_unified.py --sync-all

# Or update just TV:
python3 publish_unified.py --update-tv

# Or process voice memo (does everything):
python3 publish_unified.py --voice-memo audio.webm
```

## Usage

### 1. Sync All Content
Updates TV page, projects dashboard, and shared content across all repos:
```bash
python3 publish_unified.py --sync-all
```

**What it does:**
- Copies `/tv` from soulfra.github.io → voice-archive
- Copies `/projects.html` from soulfra.github.io → voice-archive
- Commits to both repos with unified message
- Pulls latest to avoid conflicts
- Pushes to GitHub
- Deploys to both cringeproof.com and soulfra.com

### 2. Update TV Only
Quick update just for TV broadcasting page:
```bash
python3 publish_unified.py --update-tv
```

### 3. Process Voice Memo (Full Pipeline)
Complete end-to-end: transcribe → analyze → publish → sync:
```bash
python3 publish_unified.py --voice-memo path/to/audio.webm
```

**Full pipeline:**
1. Whisper transcribes audio
2. Ollama analyzes and routes to domain
3. Creates markdown post in {domain}-content repo
4. Syncs to all destination repos
5. Commits and pushes everything
6. Live on all sites within 60 seconds

### 4. Dry Run (Preview Changes)
See what would happen without actually doing it:
```bash
python3 publish_unified.py --sync-all --dry-run
```

## Content Sync Targets

### TV Broadcasting (`/tv`)
- **Source:** `soulfra.github.io/tv/`
- **Destinations:**
  - `voice-archive/tv/` → https://cringeproof.com/tv
- **Purpose:** Live Cal/Arty chat feed, Twitch-style UI

### Projects Dashboard (`/projects.html`)
- **Source:** `soulfra.github.io/projects.html`
- **Destinations:**
  - `voice-archive/projects.html` → https://cringeproof.com/projects.html
- **Purpose:** Live GitHub project explorer

### Soulfra Hub (`/index.html`)
- **Source:** `soulfra.github.io/index.html`
- **Destinations:**
  - `voice-archive/soulfra-hub.html` → https://cringeproof.com/soulfra-hub.html
- **Purpose:** Main brand hub (renamed to avoid conflict with CringeProof's index)

## Repo Roles

### voice-archive (CringeProof)
- **Domain:** cringeproof.com (via CNAME)
- **Purpose:** Input portal - where users record voice memos
- **Content:**
  - Voice recorder interface
  - User profiles (/u/{username})
  - Synced content from Soulfra (TV, projects)
  - RSS feeds (/feeds/)

### soulfra.github.io (Soulfra Hub)
- **Domain:** soulfra.com (needs CNAME setup)
- **Purpose:** Main brand hub and content distribution
- **Content:**
  - Master versions of TV, projects, index
  - Domain landing pages (/calriven, /deathtodata, /cringeproof, /soulfra)
  - Project documentation

### Domain-Specific Repos
- **calriven-content** - Blog posts generated from voice
- **calriven-data** - Voice transcripts, AI prompts
- **cringeproof-content** - Anti-cringe guides
- **cringeproof-data** - Cringe detection datasets
- **deathtodata-content** - Privacy guides
- **deathtodata-data** - Privacy metrics
- **soulfra-content** - QR guides, voice navigation
- **soulfra-data** - Authentication examples

## Automation Options

### Option A: Manual (Current)
Run `publish_unified.py` whenever you update content:
```bash
# After editing any file
python3 publish_unified.py --sync-all
```

### Option B: Git Hook (Automatic)
Auto-sync on every commit:
```bash
# In soulfra.github.io/.git/hooks/post-commit
#!/bin/bash
python3 ../publish_unified.py --sync-all
```

### Option C: GitHub Actions (Cloud)
Auto-sync when changes pushed to main:
```yaml
# .github/workflows/unified-sync.yml
name: Unified Sync
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync to all repos
        run: python3 publish_unified.py --sync-all
```

### Option D: Cron Job (Scheduled)
Sync every hour automatically:
```bash
# Add to crontab: crontab -e
0 * * * * cd /path/to/soulfra-simple && python3 publish_unified.py --sync-all
```

## Troubleshooting

### TV Page 404s
```bash
# Check which repos have it:
ls -la ~/Desktop/roommate-chat/voice-archive/tv/
ls -la ~/Desktop/roommate-chat/soulfra-simple/soulfra.github.io/tv/

# Force sync:
python3 publish_unified.py --update-tv
```

### Git Push Rejected
Script automatically handles this by pulling before pushing. If still fails:
```bash
# Manually resolve:
cd voice-archive
git pull --rebase origin main
cd ../soulfra.github.io
git pull --rebase origin main

# Then retry sync:
python3 publish_unified.py --sync-all
```

### Content Out of Sync
```bash
# See what would change:
python3 publish_unified.py --sync-all --dry-run

# Force full sync:
python3 publish_unified.py --sync-all
```

## Future Enhancements

### Phase 2: Cross-Domain Publishing
Extend to publish to all domain repos automatically:
```python
SYNC_TARGETS = {
    "calriven_posts": {
        "source": BASE_DIR / "content/calriven",
        "destinations": [
            CALRIVEN_CONTENT / "posts",
            SOULFRA_GH_IO / "calriven/posts"
        ]
    }
}
```

### Phase 3: Real-Time WebSocket
Replace polling with WebSockets for instant updates:
```javascript
// In tv/index.html
const ws = new WebSocket('wss://api.soulfra.com/ws');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  renderMessage(msg);
};
```

### Phase 4: Multi-Platform Posting
Auto-post to YouTube/Twitch/X when new content published:
```python
publisher.post_to_youtube(video_path)
publisher.post_to_twitch(stream_url)
publisher.post_to_twitter(text, video)
```

## Related Files

- `import_voice_memo.py` - Transcribes audio with Whisper
- `publish_voice.py` - Routes transcripts to domains
- `CREATE_MISSING_REPOS.md` - How to create 8 domain repos
- `CRINGEPROOF_SOULFRA_CALRIVEN_ARCHITECTURE.md` - 3-part system
- `llm-emoji-map.js` - Emoji → LLM pipeline decoder

## Success Metrics

✅ **Before this system:**
- TV page 404'd at soulfra.github.io/tv
- Manual file copying required
- Frequent desync between repos
- Confusion about which repo powers which domain

✅ **After this system:**
- TV live at https://cringeproof.com/tv
- Single command updates everything
- Repos stay synchronized
- Clear workflow: edit once, deploy everywhere

## Quick Reference

```bash
# Most common commands:
python3 publish_unified.py --sync-all         # Sync everything
python3 publish_unified.py --update-tv         # Update TV only
python3 publish_unified.py --voice-memo audio  # Full pipeline
python3 publish_unified.py --dry-run --sync-all # Preview changes

# Check sync status:
git -C voice-archive status
git -C soulfra.github.io status

# Verify live sites:
curl -I https://cringeproof.com/tv/
curl -I https://soulfra.github.io/tv/  # (once CNAME added)
```
