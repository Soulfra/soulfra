# Soulfra Publishing Workflow

**Created:** 2026-01-09
**Purpose:** Document how content flows from backend → local repos → GitHub → live sites

---

## Architecture Overview

```
Voice Recording → Flask Backend → Content Generation → Local Git Repo → GitHub → GitHub Pages → Live Site
```

### The Stack

1. **Backend** (Flask Apps)
   - Location: `~/Desktop/roommate-chat/soulfra-simple/`
   - Port 5001: `app.py` (main platform)
   - Port 5002: `cringeproof_api.py` (voice/AI processing)
   - Database: `soulfra.db` (SQLite)

2. **Local Working Repos**
   - Expected location: `~/Desktop/roommate-chat/github-repos/`
   - Current locations: scattered (Desktop, soulfra-simple/, github-repos/)

3. **GitHub Repos**
   - Organization: https://github.com/Soulfra
   - Total: 142 repos
   - Types: platforms, brand sites, infrastructure, portfolio

4. **Live Sites**
   - Hosting: GitHub Pages (free, CDN, version-controlled)
   - Domains: Custom CNAMEs (cringeproof.com, soulfra.com, etc.)

---

## Publishing Workflows

### 1. Voice → CringeProof (voice-archive)

**Current State (BROKEN):**
```
User records voice
    ↓
POST to cringeproof_api.py:5002/api/simple-voice/save
    ↓
Whisper transcription
    ↓
Ollama extracts ideas
    ↓
add_audio_page.py generates HTML
    ↓
Writes to soulfra-simple/voice-archive/   ← NESTED GIT REPO (problem!)
    ↓
git push (from nested repo)
    ↓
https://github.com/Soulfra/voice-archive
    ↓
GitHub Pages serves cringeproof.com
```

**Problems:**
- `soulfra-simple/voice-archive/` is a nested git repo (git-in-git conflict)
- Two copies exist: Desktop and nested (diverged git history)
- Scripts point to nested copy: `Path(__file__).parent / "voice-archive"`

**Fixed Workflow:**
```
User records voice
    ↓
POST to cringeproof_api.py:5002
    ↓
Whisper + Ollama processing
    ↓
add_audio_page.py (updated path)
    ↓
Writes to ~/Desktop/voice-archive/   ← CANONICAL (no nesting!)
    ↓
git push
    ↓
https://github.com/Soulfra/voice-archive → cringeproof.com
```

**Required Changes:**
- Update `add_audio_page.py`: `VOICE_ARCHIVE_DIR = Path.home() / "Desktop/voice-archive"`
- Remove nested `soulfra-simple/voice-archive/`
- Merge any unique work from nested → Desktop copy

---

### 2. Blog Posts → Brand Sites

**Workflow:**
```
Content created in soulfra.db
    ↓
publish_all_brands.py reads database
    ↓
Generates HTML from templates
    ↓
Writes to ~/Desktop/roommate-chat/github-repos/{brand}/
    ↓
git commit & push
    ↓
https://github.com/Soulfra/{brand-site}
    ↓
GitHub Pages serves {brand}.com
```

**Supported Brands:**
- soulfra → soulfra.com
- calriven → calriven.com
- deathtodata → deathtodata.com
- howtocookathome → howtocookathome.com
- dealordelete → dealordelete.com
- finishthisidea, finishthisrepo, mascotrooms, saveorsink, sellthismvp, shiprekt

**Script:** `publish_all_brands.py`
```python
GITHUB_REPOS_BASE = Path("/Users/matthewmauer/Desktop/roommate-chat/github-repos")
```

**Status:** This workflow is working correctly for the 9 repos in github-repos/

---

### 3. Static Site Updates → soulfra.github.io

**Workflow:**
```
Manual edits to HTML/CSS/JS
    ↓
Files in ~/Desktop/soulfra.github.io/
    ↓
git commit & push
    ↓
https://github.com/Soulfra/soulfra.github.io
    ↓
GitHub Pages serves soulfra.github.io
```

**Current State:**
- Also has nested copy: `soulfra-simple/soulfra.github.io/` (problem!)
- Desktop copy is canonical
- Nested copy has diverged

**Required Changes:**
- Remove nested copy: `soulfra-simple/soulfra.github.io/`
- Use Desktop copy only

---

## Database Schema

### Core Tables

**brands**
```sql
CREATE TABLE brands (
    id INTEGER PRIMARY KEY,
    name TEXT,
    slug TEXT UNIQUE,
    domain TEXT,
    tagline TEXT,
    color_primary TEXT,
    color_secondary TEXT,
    emoji TEXT
);
```

**posts**
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    brand_id INTEGER,
    title TEXT,
    content TEXT,
    slug TEXT,
    published_at DATETIME,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);
```

**voice_recordings** (cringeproof)
```sql
CREATE TABLE voice_recordings (
    id INTEGER PRIMARY KEY,
    title TEXT,
    transcription TEXT,
    audio_path TEXT,
    created_at DATETIME,
    published BOOLEAN
);
```

---

## File Structure

### Backend (soulfra-simple/)
```
soulfra-simple/
├── app.py                          # Port 5001 - Main platform
├── cringeproof_api.py              # Port 5002 - Voice processing
├── soulfra.db                      # SQLite database
├── publish_all_brands.py           # Multi-brand publisher
├── add_audio_page.py               # Voice → HTML generator
├── github_pages_publisher.py       # Generic publisher
├── core/
│   ├── publish_everywhere.py
│   ├── publish_to_github.py
│   └── publish_all_brands.py
├── templates/                      # Jinja2 templates
└── static/                         # CSS/JS assets
```

### Local Repos (Canonical Structure)
```
~/Desktop/
├── roommate-chat/                  # Git repo - main backend
│   ├── soulfra-simple/            # Flask apps
│   └── github-repos/              # Brand sites
│       ├── soulfra/
│       ├── calriven/
│       ├── deathtodata/
│       ├── dealordelete-site/
│       └── ... (7 more)
└── voice-archive/                  # Git repo - cringeproof.com
    ├── audio/                      # Audio files
    ├── index.html                  # Main page
    ├── CNAME                       # cringeproof.com
    └── README.md
```

**NOT nested in soulfra-simple/** (causes git conflicts!)

---

## Git Operations

### Publishing a Brand Site

```bash
cd ~/Desktop/roommate-chat/soulfra-simple

# Generate content from database
python3 publish_all_brands.py soulfra

# Result: Updates in github-repos/soulfra/
cd ~/Desktop/roommate-chat/github-repos/soulfra

# Push to GitHub
git add .
git commit -m "Update soulfra content"
git push origin main

# Live in ~30 seconds at soulfra.com
```

### Publishing Voice Recording to CringeProof

```bash
# Record via web interface → cringeproof_api.py processes

# Or manually add audio:
cd ~/Desktop/roommate-chat/soulfra-simple
python3 add_audio_page.py recording.wav "Title" "Transcription"

# Result: Updates in ~/Desktop/voice-archive/
cd ~/Desktop/voice-archive

# Push to GitHub
git add .
git commit -m "Add new voice recording"
git push origin main

# Live in ~30 seconds at cringeproof.com
```

---

## Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 5001 | app.py | Main Soulfra platform |
| 5002 | cringeproof_api.py | Voice/AI processing |
| 8888 | mesh-router.js | Mesh networking (optional) |
| 5002 | ipfs daemon | IPFS gateway (optional) |

---

## Environment Variables

### Required (.env in soulfra-simple/)

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx           # For git push

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx   # Claude API
OPENAI_API_KEY=sk-xxxxxxxxxxxxx          # OpenAI API (optional)

# Database
DATABASE_URL=sqlite:///soulfra.db        # Default local DB

# Deployment
CLOUDFLARE_TUNNEL_TOKEN=xxxxxxxxxxxxx    # For public access (optional)
```

---

## Current Issues & Fixes

### Issue 1: Nested Git Repos
**Problem:** `soulfra-simple/voice-archive/` and `soulfra-simple/soulfra.github.io/` are git repos inside the roommate-chat git repo

**Impact:**
- Git conflicts when committing in parent repo
- Confusing which copy is "real"
- Scripts point to nested copy

**Fix:**
1. Remove nested copies after merging unique work
2. Update scripts to point to Desktop copies
3. Add to `.gitignore` to prevent re-nesting

### Issue 2: Scattered Local Repos
**Problem:** 142 repos but only 9 in expected `github-repos/` location

**Impact:**
- Hard to find where to edit
- Publishing scripts fail for missing repos
- Duplicate repos in multiple locations

**Fix:**
1. Move all active repos to `github-repos/`
2. Keep only essential standalone (roommate-chat, voice-archive)
3. Update REPO_MAP.md as reference

### Issue 3: Diverged Copies
**Problem:** Desktop vs. nested voice-archive have different git histories

**Impact:**
- Risk of losing work
- Unclear which has latest changes
- Can't simply delete one

**Fix:**
1. Compare both copies
2. Merge unique content
3. Establish Desktop as canonical
4. Delete nested after verification

---

## Next Steps

### Phase 1: Fix Nested Repos (Critical)
- [ ] Check for unique work in nested `voice-archive/`
- [ ] Merge to Desktop `voice-archive/`
- [ ] Remove `soulfra-simple/voice-archive/`
- [ ] Remove `soulfra-simple/soulfra.github.io/`
- [ ] Add both to `soulfra-simple/.gitignore`

### Phase 2: Update Scripts
- [ ] Update `add_audio_page.py` path
- [ ] Test voice recording workflow
- [ ] Verify cringeproof.com updates

### Phase 3: Consolidate Repos
- [ ] Move active repos to `github-repos/`
- [ ] Update REPO_MAP.md
- [ ] Test publishing workflow

---

## Testing Checklist

### Test 1: Voice Recording to CringeProof
- [ ] Record voice at http://localhost:5002
- [ ] Verify transcription appears
- [ ] Check audio file in `~/Desktop/voice-archive/audio/`
- [ ] Commit and push changes
- [ ] Verify live at https://cringeproof.com

### Test 2: Blog Post to Brand Site
- [ ] Add post to soulfra.db
- [ ] Run `publish_all_brands.py soulfra`
- [ ] Check files in `github-repos/soulfra/`
- [ ] Commit and push changes
- [ ] Verify live at https://soulfra.com

### Test 3: Manual Site Update
- [ ] Edit file in `~/Desktop/soulfra.github.io/`
- [ ] Commit and push
- [ ] Verify live at https://soulfra.github.io

---

## Resources

- **GitHub Organization:** https://github.com/Soulfra
- **GitHub Pages Docs:** https://docs.github.com/en/pages
- **Flask Docs:** https://flask.palletsprojects.com/
- **SQLite Docs:** https://www.sqlite.org/docs.html

---

**Last Updated:** 2026-01-09
**Maintained By:** Matt
**See Also:** REPO_MAP.md, ARCHITECTURE.md
