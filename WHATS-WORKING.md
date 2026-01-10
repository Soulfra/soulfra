# What's Actually Working - Soulfra Simple Guide

**You're not stupid. You just have 328 files and no map.**

This is your map.

---

## The 6 Things You Actually Use

### 1. **Search** - Find Anything (NEW!)
**URL**: http://localhost:5001/search

**What it does**: AI-powered semantic search OR simple text search across all your posts

**How to use it**:
1. Type your query (e.g., "AI models", "privacy")
2. Choose mode:
   - **🧠 AI Semantic**: Uses Ollama to understand meaning (finds related concepts)
   - **📝 Text Match**: Simple keyword search (faster)
3. Click "Search"
4. See results with match scores

**Why it's cool**: Instead of typing SQL commands like `SELECT * FROM posts WHERE...`, just search like Google.

---

### 2. **Homepage** - Write & Publish Posts
**URL**: http://localhost:5001

**What it does**: Main interface for creating posts

**How to use it**:
- Click "New Post" or similar
- Write your content
- Click "Publish"
- Done

---

### 3. **Homebrew Lab** - Multi-AI Debate System
**URL**: http://localhost:5001/homebrew-lab

**What it does**: Record voice memo → Get 5 AI perspectives → Creates debate article

**How to use it**:
1. Go to "Multi-AI Debate" tab
2. Enter topic (e.g., "Should AI be open source?")
3. Click record button (or type your thoughts)
4. Click "Generate Debate"
5. Wait ~30 seconds
6. Article is created with 5 different AI perspectives

**What's working**:
- ✅ Voice recording
- ✅ 5 AI models (soulfra-model, deathtodata-model, calos-model, publishing-model, llama3.2:3b)
- ✅ Debate article generation
- ✅ Auto-save to database

---

### 3. **Admin Studio** - Content Management
**URL**: http://localhost:5001/admin/studio

**What it does**: Manage all your content (posts, brands, settings)

**How to use it**:
- View all posts
- Edit existing content
- Manage brands (Soulfra, DeathToData, Calriven, etc.)
- Configure settings

---

### 4. **Status Dashboard** - See What's Working
**URL**: http://localhost:5001/status

**What it does**: Shows system health, database stats, all routes

**What you see**:
- Database health (✅ or ❌)
- Post count (currently: 33)
- Comment count
- User count
- All available routes

**Pro tip**: This already HAS a frontend. You don't need to build one.

---

### 5. **Local Site Preview** - See Before Deploy
**URL**: http://localhost:5001/local-site/soulfra/

**What it does**: Shows exactly how your site will look on GitHub Pages

**How to use it**:
1. Write a post
2. Export: `python3 export_static.py --brand Soulfra`
3. Preview: http://localhost:5001/local-site/soulfra/
4. Click around, test navigation
5. If it looks good, deploy

---

## The Files That Matter

Out of 328 files, you only touch these:

### Core System
- `app.py` - Main Flask app (don't touch, it's working)
- `soulfra.db` - Your database (33 posts, all your data)
- `export_static.py` - Converts database → static HTML

### Content Folders
- `templates/` - 100+ HTML frontends (don't touch, working)
- `output/` - Exported static sites (soulfra, deathtodata, etc.)
- `static/` - CSS, images, assets

### What You Write
- Nothing directly. You use the web interface.
- Posts go into `soulfra.db`
- Export creates HTML in `output/`

---

## What You DON'T Need to Touch

### Already Working (Leave Alone)
- `whisper_transcriber.py` - Voice transcription (working)
- `voice_routes.py` - Voice endpoints (working)
- `voice_pipeline.py` - Audio processing (working)
- All 100+ HTML templates (working)
- All Flask routes (working)

### New Stuff (Optional, Ignore for Now)
- `publish_everywhere.py` - Cross-posting (needs API keys)
- `manage_subscribers.py` - Subscriber management (future use)
- `publish_ipfs.py` - IPFS hosting (needs IPFS installed)
- `publish_all.sh` - Master script (convenience)
- `.env.example` - API keys template (when you want cross-posting)
- `TRINITY-SETUP.md` - Phone sync guide (future setup)

### Broken/Unused (Ignore)
- Anything with `[ERROR]` in logs
- Old experimental code in `archive/`
- Scripts you don't recognize (probably experiments)

---

## Your Actual Workflow

### Write a Post (3 Ways)

**Way 1: Manual Post**
1. Go to http://localhost:5001
2. Click "New Post"
3. Write content
4. Publish
5. Done

**Way 2: Voice Memo → Multi-AI Debate**
1. Go to http://localhost:5001/homebrew-lab
2. Record voice memo about a topic
3. Click "Generate Debate"
4. 5 AI models analyze it
5. Debate article auto-created
6. Done

**Way 3: Command Line (Advanced)**
```bash
# Use voice-to-debate API
curl -X POST http://localhost:5001/api/voice-to-debate \
  -F "topic=Your Topic" \
  -F "text=Your thoughts here" \
  -F "brand=Soulfra"
```

### Publish to GitHub Pages

**Simple Way (Working Now)**
```bash
# 1. Export database → HTML
python3 export_static.py --brand Soulfra

# 2. Go to output folder
cd output/soulfra

# 3. Git commit + push
git add .
git commit -m "Update content"
git push

# 4. Wait ~1 minute
# 5. Live at: https://soulfra.github.io/soulfra/
```

**One-Click Way (If You Want)**
```bash
# Uses the Homebrew Lab auto-deploy endpoint
curl -X POST http://localhost:5001/api/auto-deploy \
  -H "Content-Type: application/json" \
  -d '{"brand": "soulfra"}'
```

---

## Database Basics

### Your Database: `soulfra.db`

**What's in it**:
- 33 posts (all your content)
- 5 brands (Soulfra, DeathToData, Calriven, HowToCookAtHome, Stpetepros)
- Users, comments, subscribers, etc.

### Quick Commands

```bash
# See all posts
sqlite3 soulfra.db "SELECT id, title FROM posts"

# Count posts
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts"

# See latest post
sqlite3 soulfra.db "SELECT title, published_at FROM posts ORDER BY id DESC LIMIT 1"

# List brands
sqlite3 soulfra.db "SELECT id, name FROM brands"

# Backup database
cp soulfra.db soulfra.db.backup
```

---

## URLs Cheat Sheet

### Local Development
| URL | What It Does |
|-----|--------------|
| http://localhost:5001 | Homepage (write posts) |
| http://localhost:5001/homebrew-lab | Multi-AI debate tool |
| http://localhost:5001/admin/studio | Content management |
| http://localhost:5001/status | System health dashboard |
| http://localhost:5001/local-site/soulfra/ | Preview exported site |
| http://localhost:5001/feed.xml | RSS feed |
| http://localhost:5001/sitemap.xml | Sitemap |

### Admin Tools
| URL | What It Does |
|-----|--------------|
| http://localhost:5001/admin?dev_login=true | Admin login bypass |
| http://localhost:5001/admin/canvas | WYSIWYG editor |
| http://localhost:5001/master-control | Master control panel |
| http://localhost:5001/status/routes | All available routes (JSON) |
| http://localhost:5001/status/schemas | Database structure (JSON) |

### Live Sites (After Deploy)
| URL | What It Is |
|-----|-----------|
| https://soulfra.github.io/soulfra/ | Live Soulfra site |
| https://soulfra.com | Custom domain (if DNS configured) |

---

## The Frontends You Already Have

### `/status/schemas` Doesn't Need a Frontend

When you go to http://localhost:5001/status/schemas, you see JSON because it's an **API endpoint**.

**It's SUPPOSED to be JSON.** That's how APIs work.

If you want to see it pretty, go to http://localhost:5001/status instead (it has a frontend).

### You Have 100+ Frontends Already

All these work right now:
- Homepage (posts feed)
- Post detail pages
- Admin studio
- Homebrew lab
- Status dashboard
- Master control panel
- Template browser
- Domain manager
- Brand workspace
- ...97 more

**You don't need to build frontends. They're already built.**

---

## What We Added Today (Optional)

### Cross-Posting System

**Files**:
- `publish_everywhere.py` - Post to all platforms at once
- `manage_subscribers.py` - Manage email/phone/Signal subscribers

**What it does**:
Write once → Auto-publish to:
- Substack (newsletter)
- Medium (blog)
- Email (SendGrid)
- WhatsApp (via Business API)
- Signal (via signal-cli)

**Status**: OPTIONAL - Needs API keys in `.env` file

**How to use** (when you want):
```bash
# 1. Copy .env.example to .env
cp .env.example .env

# 2. Add your API keys
nano .env

# 3. Test (dry run)
python3 publish_everywhere.py --latest --dry-run

# 4. Actually publish
python3 publish_everywhere.py --latest
```

### Decentralized Hosting

**File**: `publish_ipfs.py`

**What it does**: Publish to IPFS (decentralized web)

**Status**: OPTIONAL - Needs `brew install ipfs`

**When you need it**: Future (for true decentralization)

### Trinity Setup

**Files**: `TRINITY-SETUP.md`, `REAL-SOULFRA.md`

**What it is**: Guide for syncing laptop + 2 phones via Syncthing

**Status**: FUTURE - For when you want phone sync

**Don't worry about it yet.**

---

## Troubleshooting

### "I don't know where to start"
→ Go to http://localhost:5001/homebrew-lab
→ Record a voice memo about anything
→ Watch it create a multi-AI debate article

### "I see JSON everywhere"
→ You're looking at API endpoints
→ Go to http://localhost:5001/status instead
→ That has a proper frontend

### "Too many files, too confusing"
→ You only use 5 URLs (listed above)
→ The 328 files are the ENGINE
→ You don't drive by looking at the engine

### "What's actually broken?"
→ Check http://localhost:5001/status
→ If database shows ✅, everything's working
→ Ignore IPFS errors (it's optional)

### "Voice memo says 'Ollama unavailable'"
→ This was already fixed (changed `llama3.2` to `llama3.2:3b`)
→ Should work now

### "Can't find my post"
→ Check database: `sqlite3 soulfra.db "SELECT title FROM posts ORDER BY id DESC LIMIT 10"`
→ Export to HTML: `python3 export_static.py --brand Soulfra`
→ Preview: http://localhost:5001/local-site/soulfra/

---

## The Big Picture

### What You Have (Working Now)
1. Flask web app (http://localhost:5001)
2. Database with 33 posts
3. 5 brands (Soulfra, DeathToData, Calriven, HowToCookAtHome, Stpetepros)
4. 22 AI models via Ollama (running locally)
5. Multi-AI debate system (5 models analyze topics)
6. Voice transcription (local Whisper)
7. Static site export (database → HTML)
8. GitHub Pages deployment (manual git push)
9. 100+ HTML templates (all frontends working)
10. Admin tools (studio, master control, etc.)

### What We Just Added (Optional)
1. Cross-posting automation (Substack, Medium, Email, WhatsApp, Signal)
2. Subscriber management (unified across platforms)
3. IPFS publishing (decentralized hosting)
4. Trinity docs (laptop + phone sync guide)

### What You Actually Do
1. Write posts (web interface or voice)
2. Export to HTML (`python3 export_static.py`)
3. Push to GitHub (`git add . && git commit && git push`)
4. Live at https://soulfra.github.io/soulfra/

**That's it. 3 steps.**

---

## Quick Start (Right Now)

### Test Everything's Working

```bash
# 1. Start Flask (if not running)
python3 app.py

# 2. Check database
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts"
# Should show: 33

# 3. Open in browser
open http://localhost:5001/homebrew-lab

# 4. Record a voice memo or type a topic
# Topic: "What's the meaning of life?"

# 5. Click "Generate Debate"
# Wait ~30 seconds

# 6. See 5 AI perspectives combined into article

# 7. Check it worked
sqlite3 soulfra.db "SELECT title FROM posts ORDER BY id DESC LIMIT 1"
# Should show your new post

# 8. Export to HTML
python3 export_static.py --brand Soulfra

# 9. Preview
open http://localhost:5001/local-site/soulfra/

# 10. See your post live locally
```

**If all that worked: Everything's working.**

---

## What to Ignore

- Any `.example` files except `.env.example` (there's only one anyway)
- Anything in `archive/` folder
- Any script you didn't know existed
- IPFS errors (it's optional, not installed)
- Cross-posting errors (needs API keys you don't have yet)
- Trinity setup (future project)

---

## Summary

**Core Truth**: Out of 328 files, you use **5 URLs** and **1 command**.

**5 URLs**:
1. http://localhost:5001 (homepage)
2. http://localhost:5001/homebrew-lab (multi-AI debate)
3. http://localhost:5001/admin/studio (manage content)
4. http://localhost:5001/status (system health)
5. http://localhost:5001/local-site/soulfra/ (preview)

**1 Command**:
```bash
python3 export_static.py --brand Soulfra
```

**Everything else is just plumbing.**

You're not stupid. You just needed a map. This is your map.

---

**Next time you feel lost, read this file.**
