# 🚀 START HERE - Complete System Guide

**Last Updated:** January 11, 2026

## Quick Answer: Where Do I Go?

### For Local Development (Flask Server)

```bash
# Start Flask server
python3 app.py

# Open browser to:
http://localhost:5001/tools          # Dashboard (all tools in one place)
http://localhost:5001/voice-to-graph # Voice-to-graph debugger
```

### For Live Site (soulfra.com) - NO SERVER NEEDED!

```bash
# Generate and deploy reports
./deploy-tools.sh

# Then visit (works on iPhone!):
https://soulfra.com/debug.html                # Debug dashboard
https://soulfra.com/tools/debug/              # System reports
https://soulfra.com/tools/brand/              # Brand analysis
https://soulfra.com/tools/ccna/               # CCNA graphs
```

**You can debug the live site from your iPhone!** All reports are static HTML - no Flask server required.

---

---

## The Big Confusion: Email Systems

### You Asked: "How did this guy build SPAM? Is it MAPS?"

**Short answer:** You don't "build SPAM". SPAM is junk mail. You BUILD with SMTP.

Here's what each term means:

| Term | What It Is | Like... |
|------|------------|---------|
| **SMTP** | Simple Mail Transfer Protocol - HOW emails are SENT | The postal service (delivers mail) |
| **IMAP/POP3** | How emails are RECEIVED | Your mailbox (receives mail) |
| **SPAM** | Unwanted junk mail | Junk flyers in your mailbox |
| **MAPS** | Mail Abuse Prevention System - blacklist of spammers | List of known junk mailers |

**What YOU have:**
```python
# email_sender.py sends emails via:
1. Resend API (SMTP service) ← Professional
2. macOS sendmail (local SMTP) ← Testing
3. File fallback (save HTML) ← Backup
```

**You're NOT building spam.** You're sending legit recovery codes to professionals who signed up.

---

## The Build System: Templates vs Static vs Cache

You have **3 separate build systems** that do different things:

### System 1: Flask Templates (Dynamic)

```
User visits → app.py loads → templates/*.html → renders with data → shows page
```

**Where:** `templates/` folder
**How:** Jinja2 templates
**When:** Every request (real-time)
**Caching:** None (always fresh)

Example:
```html
<!-- templates/dashboard.html -->
<h1>Welcome {{ user.name }}!</h1>  ← Filled at runtime
```

---

### System 2: Static Blog (Pre-built HTML)

```
blog/posts/*.html → Already built → Deploy to GitHub Pages
```

**Where:** `blog/posts/` folder
**How:** Plain HTML files
**When:** Pre-built (manually created)
**Caching:** None (files already exist)

Example:
```html
<!-- blog/posts/my-post.html -->
<h1>My Blog Post</h1>  ← Static, never changes
```

---

### System 3: Voice-to-Graph Pipeline (Smart Rebuild)

```
Voice memo → content/*.md → build-content.py → dist/*.html → GitHub Pages
                                    ↓
                              .cache/ (Merkle tree)
```

**Where:** `content/` (source) → `dist/` (output)
**How:** Markdown → HTML conversion with SHA-256 caching
**When:** On-demand (`python3 build-content.py`)
**Caching:** Merkle tree (only rebuilds changed files)

**This is the NEW system we just built!**

---

## How Caching Works (Merkle Tree Explained Simply)

### What's a Merkle Tree?

Think of it like **Git for content**. It knows what changed.

```json
// .cache/content_hashes.json
{
  "content/post1.md": "abc123...",  ← SHA-256 hash of file
  "content/post2.md": "def456..."
}
```

**First run:**
```bash
$ python3 build-content.py
🔨 Building: post1.md  ← Builds and saves hash
🔨 Building: post2.md  ← Builds and saves hash
✅ Built 2 files
```

**Second run (no changes):**
```bash
$ python3 build-content.py
⏭️  Skipped (cached): post1.md  ← Hash matches, skip!
⏭️  Skipped (cached): post2.md  ← Hash matches, skip!
✅ Built 0 files (skipped 2 cached)
```

**Third run (edited post1.md):**
```bash
$ python3 build-content.py
🔨 Building: post1.md  ← Hash changed, rebuild!
⏭️  Skipped (cached): post2.md  ← Hash matches, skip!
✅ Built 1 file (skipped 1 cached)
```

**How it works:**
1. Hash file content with SHA-256 (like `git hash-object`)
2. Compare to cached hash
3. If same → skip (10x faster!)
4. If different → rebuild

---

## Regeneration / Rehydration

**"How do we rehydrate or regenerate?"**

### Option 1: Smart Rebuild (Fast)

Rebuilds ONLY changed files:

```bash
python3 build-content.py
```

### Option 2: Force Rebuild (Slow but Safe)

Rebuilds EVERYTHING, ignoring cache:

```bash
python3 build-content.py --force
```

### Option 3: Nuclear Option (From Scratch)

Delete all caches and outputs, rebuild from source:

```bash
# Delete built files
rm -rf dist/ .cache/

# Rebuild from content/*.md
python3 build-content.py

# Everything regenerates!
```

**When to use each:**
- **Smart rebuild:** Daily workflow (auto-skips unchanged)
- **Force rebuild:** Something looks wrong (rebuild all)
- **Nuclear option:** Total corruption, start fresh

---

## Folder Structure (Max Depth 3)

```
soulfra-simple/                    ← Root (depth 0)
│
├── app.py                         ← Main Flask server
├── soulfra.db                     ← SQLite database
│
├── content/                       ← SOURCE (depth 1)
│   ├── voice-memo-123.md          ← Write here
│   └── blog-post.md               ← Markdown files
│
├── dist/                          ← OUTPUT (depth 1)
│   ├── index.html                 ← Auto-generated
│   ├── feed.xml                   ← RSS feed
│   └── voice-memo-123.html        ← Built from .md
│
├── .cache/                        ← CACHE (depth 1)
│   └── content_hashes.json        ← Merkle tree
│
├── blog/                          ← OLD STATIC (depth 1)
│   └── posts/*.html               ← Pre-built HTML
│
├── templates/                     ← FLASK TEMPLATES (depth 1)
│   ├── dashboard.html             ← Dynamic pages
│   └── admin/                     ← Admin templates (depth 2)
│       └── dashboard.html         ← Depth 3 (STOP!)
│
├── core/                          ← CORE CODE (depth 1)
│   ├── content_parser.py          ← Voice → graph
│   └── canvas_visualizer.py       ← Graph renderer
│
├── data/                          ← DEBUG OUTPUT (depth 1)
│   ├── brand_analysis/            ← Brand reports (depth 2)
│   ├── ccna_study/                ← CCNA graphs (depth 2)
│   └── system_debug/              ← System graphs (depth 2)
│
└── email_sender.py                ← Standalone scripts (depth 0)
```

**Rule:** Never go deeper than depth 3!

---

## The Complete Pipeline (What We Just Built)

### Voice Memo → Blog Post

```
1. Record voice memo on iPhone
   ↓
2. Transcribe with Whisper
   ↓
3. Save to content/voice-memo-{timestamp}.md
   ↓
4. Run: python3 build-content.py
   ↓
5. HTML generated in dist/voice-memo-{timestamp}.html
   ↓
6. Deploy to GitHub Pages
   ↓
7. Live at soulfra.com/voice-memo-{timestamp}.html
```

### Debug System → Knowledge Graph

```
1. Run: python3 debug_system.py --routes
   ↓
2. Parses app.py (407 routes, 1,548 nodes)
   ↓
3. Generates data/system_debug/routes.html
   ↓
4. Open in browser → interactive graph!
```

### Brand Analysis → Strategy Report

```
1. Run: python3 brand_mapper.py
   ↓
2. Compares wordmaps across 7 domains
   ↓
3. Generates data/brand_analysis/brand_comparison.html
   ↓
4. Shows overlap matrix (soulfra 95% similar to howtocookathome!)
```

### CCNA Study → Concept Graph

```
1. Take CCNA notes in content/ccna-notes.md
   ↓
2. Run: python3 ccna_study.py --file content/ccna-notes.md
   ↓
3. Generates data/ccna_study/ccna_concept_graph.html
   ↓
4. Generates flashcards: data/ccna_study/ccna_flashcards.json
```

---

## Where to Go (All Your Tools)

### Flask Server (Dynamic Tools)

```bash
python3 app.py
```

Then open browser to:

| URL | What It Does |
|-----|--------------|
| `http://localhost:5001/` | Main homepage |
| `http://localhost:5001/tools` | **Dashboard (all tools!)** |
| `http://localhost:5001/voice-to-graph` | Voice-to-graph debugger |
| `http://localhost:5001/admin` | Admin panel |
| `http://localhost:5001/signup/professional` | StPetePros signup |

### Generated Reports (Static HTML)

Open these files directly in browser:

| File | What It Shows |
|------|---------------|
| `data/system_debug/routes.html` | Flask routes graph (407 routes) |
| `data/brand_analysis/brand_comparison.html` | Brand overlap (7 domains) |
| `data/ccna_study/ccna_concept_graph.html` | CCNA networking concepts |
| `dist/index.html` | Blog post index |

### CLI Tools (Run from Terminal)

```bash
# System debugger
python3 debug_system.py --routes     # Analyze Flask routes
python3 debug_system.py --domains    # Analyze domain routing

# Brand strategy
python3 brand_mapper.py              # Compare all domains

# CCNA study
python3 ccna_study.py                # Demo CCNA graph
python3 ccna_study.py --compare      # Map CCNA to your system

# Static site builder
python3 build-content.py             # Build all content
python3 build-content.py --force     # Force rebuild
python3 build-content.py --deploy    # Deploy to GitHub Pages
```

---

## Quick Demos

### 1. Test Email System

```bash
python3 test_email.py YOUR_EMAIL@gmail.com
```

Check your inbox for recovery code!

### 2. Generate Voice Graph

```bash
# Record voice memo → saves to content/
# Then build:
python3 build-content.py
```

### 3. See All Your Brands

```bash
python3 brand_mapper.py

# Open: data/brand_analysis/brand_analysis_REPORT.md
# Shows: soulfra.com vs calriven.com vs deathtodata.com
```

### 4. Debug Your Flask App

```bash
python3 debug_system.py --routes

# Open: data/system_debug/routes.html
# Shows: 407 routes, which call get_db() most (187 times)
```

---

## What You Have vs What We Built

### Before (What You Had)

```
✅ Flask app with 407 routes
✅ Email system (SMTP via Resend/sendmail)
✅ BIP-39 recovery codes for StPetePros
✅ 7 domains (soulfra, calriven, deathtodata, etc)
✅ Blog posts in blog/posts/*.html (static)
✅ SQLite database (soulfra.db)
```

### After (What We Added)

```
✨ Voice-to-graph debugger UI (http://localhost:5001/voice-to-graph)
✨ System debugger (analyzes Flask routes, shows graphs)
✨ Brand strategy analyzer (compares wordmaps across domains)
✨ CCNA study tool (networking concepts → knowledge graphs)
✨ Smart build system (Merkle caching, only rebuilds changed files)
✨ RSS feed generator (feed.xml)
✨ Sitemap generator (sitemap.xml for SEO)
```

---

## Common Questions

### Q: "How do samesite cookies work across domains?"

**A:** They don't! That's the point.

- `SameSite=Strict` = Cookie ONLY works on soulfra.com (not calriven.com)
- `SameSite=None; Secure` = Cookie works across domains (requires HTTPS)

Your solution: **BIP-39 recovery codes** = master password that works everywhere.

```
User logs in on soulfra.com → gets recovery code
User enters code on calriven.com → verified via database
No cookies needed!
```

### Q: "How do I build from scratch?"

**A:**
```bash
# Delete outputs
rm -rf dist/ .cache/

# Rebuild
python3 build-content.py

# Deploy
python3 build-content.py --deploy
```

### Q: "What's the difference between templates/ and content/?"

**A:**
- `templates/` = Flask templates (dynamic, server-rendered)
- `content/` = Markdown source (static, pre-built to HTML)
- `blog/` = Old static HTML (already built, no source)

### Q: "Why are soulfra and howtocookathome 95% similar?"

**A:** They're using the same base template! Run:

```bash
python3 brand_mapper.py

# See: data/brand_analysis/brand_analysis_REPORT.md
# Shows unique words per brand
```

Fix: Give each domain unique content.

---

## Next Steps

1. ✅ **Read this guide** (you're here!)

2. 🚀 **Start Flask server:**
   ```bash
   python3 app.py
   ```

3. 🌐 **Open dashboard:**
   ```
   http://localhost:5001/tools
   ```

4. 🎤 **Try voice-to-graph:**
   ```
   http://localhost:5001/voice-to-graph
   ```

5. 📊 **Run brand analysis:**
   ```bash
   python3 brand_mapper.py
   ```

6. 🏗️ **Build content:**
   ```bash
   python3 build-content.py
   ```

---

## Support

**Still confused?**
- Read: `EMAIL_SETUP_GUIDE.md` for email details
- Read: `PROJECT_FILE_MAP.md` for folder structure
- Read: `BIP39_STPETEPROS_SYSTEM.md` for recovery codes

**Found a bug?**
- Check `data/system_debug/routes.html` for route analysis
- Run `python3 debug_system.py --routes` to investigate

**Want to contribute?**
- All tools are in root directory (max depth 3)
- Code is in `core/` folder
- Tests go in `tests/` folder (create if missing)

---

---

## Debugging the Live Site (soulfra.com)

### The Problem

- **soulfra.com is live** (GitHub Pages)
- **It's static HTML** (no Flask backend)
- **Can't run localhost tools** on the live site
- **Want to debug from iPhone** (mobile-friendly)

### The Solution

**Text-first, static debugging** - all reports are HTML files you can view without a server:

```bash
# 1. Generate all reports locally
./deploy-tools.sh

# 2. Reports are copied to output/soulfra/tools/
# 3. Git push triggers GitHub Pages deployment
# 4. Visit soulfra.com/debug.html (live in ~30 seconds!)
```

### What Gets Deployed

| Local File | Deployed To | What It Shows |
|------------|-------------|---------------|
| `data/system_debug/routes.html` | `soulfra.com/tools/debug/routes.html` | Flask routes graph |
| `data/brand_analysis/brand_comparison.html` | `soulfra.com/tools/brand/brand_comparison.html` | Brand overlap |
| `data/ccna_study/ccna_concept_graph.html` | `soulfra.com/tools/ccna/ccna_concept_graph.html` | CCNA concepts |
| `dist/index.html` | `soulfra.com/blog/index.html` | Blog posts index |

### Mobile Debugging (iPhone Workflow)

1. **On laptop:**
   ```bash
   ./deploy-tools.sh
   ```

2. **On iPhone:**
   - Open Safari
   - Visit `soulfra.com/debug.html`
   - Tap any report link
   - Interactive graphs work on touchscreen!

3. **Bookmark it:**
   - Add `soulfra.com/debug.html` to home screen
   - Debug on the go

### Text-First = Accessible

All reports are:
- ✅ Static HTML (no JavaScript required for basic viewing)
- ✅ Mobile-responsive (works on iPhone/iPad)
- ✅ Works offline (once loaded)
- ✅ No backend needed (GitHub Pages serves static files)
- ✅ Shareable URLs (send links to team)

---

**You're ready to go! 🚀**

**Local development:** `python3 app.py` → Open `http://localhost:5001/tools`

**Live site debugging:** `./deploy-tools.sh` → Visit `soulfra.com/debug.html`
