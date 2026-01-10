# Soulfra Quick Start Guide

**Fixed:** "we're working all over the place but our workflows need to be sync'd"

Everything now syncs automatically with ONE command.

## Live Sites

- **CringeProof** - https://cringeproof.com (voice input portal)
- **Soulfra TV** - https://cringeproof.com/tv (live Cal/Arty chat)
- **Projects** - https://cringeproof.com/projects.html (GitHub dashboard)
- **Soulfra Hub** - https://soulfra.github.io (coming: soulfra.com)

## Daily Workflow

### 1. Record Voice Memo
Drop audio file here:
```bash
python3 import_voice_memo.py path/to/audio.webm
```

### 2. Publish & Sync
**Option A: Full Pipeline (Recommended)**
```bash
python3 publish_unified.py --voice-memo path/to/audio.webm
```
This does EVERYTHING:
- Transcribes with Whisper
- Analyzes with Ollama
- Routes to correct domain
- Publishes to GitHub
- Syncs all repos
- Live in 60 seconds

**Option B: Just Sync Content**
```bash
python3 publish_unified.py --sync-all
```

**Option C: Update TV Only**
```bash
python3 publish_unified.py --update-tv
```

### 3. Check Status
```bash
# Preview what would sync:
python3 publish_unified.py --dry-run --sync-all

# Verify live:
curl -I https://cringeproof.com/tv/
```

## Common Tasks

### Update TV Interface
```bash
# 1. Edit the master version:
vim soulfra.github.io/tv/index.html

# 2. Sync to all repos:
python3 publish_unified.py --update-tv
```

### Update Projects Dashboard
```bash
# 1. Edit master:
vim soulfra.github.io/projects.html

# 2. Sync:
python3 publish_unified.py --sync-all
```

## Key Files

- `UNIFIED_DEPLOYMENT.md` - Complete deployment architecture
- `CREATE_MISSING_REPOS.md` - How to create 8 domain repos
- `publish_unified.py` - Sync system
