# START HERE: cringeproof.com + soulfra.com

## Reality Check

**You Own 2 Live Domains:**
1. **cringeproof.com** - Anonymous voice memos wall
2. **soulfra.com** - AI routing infrastructure site

**What's Actually Deployed:**
- Both are **static HTML sites** on GitHub Pages
- DNS points to GitHub's servers (185.199.108.153)
- No backend is deployed publicly (Flask/IPFS/Ollama only run on localhost)

**What's Only on Localhost:**
- Flask backend (port 5001)
- IPFS daemon (ports 5002/8080)
- Ollama AI (port 11434 on 192.168.1.87)
- Mesh router (port 8888)

---

## The 16 Domain Confusion

**domains.json has 16 domains** - but only 2 are real:
- **cringeproof** ✅ Real domain
- **soulfra** ✅ Real domain
- **calriven, deathtodata, howtocookathome, mascotrooms, etc.** ❌ Not real (theoretical/future projects)

**Why they exist in domains.json:**
- For AI routing (voice_to_repo.py analyzes themes and assigns to domain)
- Folder color organization on your Mac
- Future expansion

**You can ignore the other 14** - focus on cringeproof and soulfra.

---

## Directory Structure

```
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/
│
├── voice-archive/              # CringeProof source code
│   ├── CNAME                   # "cringeproof.com"
│   ├── wall.html               # Main voice memo wall
│   ├── record-simple.html      # Voice recorder
│   ├── login.html              # Login page (OAuth buttons)
│   └── index.html              # Homepage
│
├── soulfra.github.io/          # Soulfra website source (if exists)
│   ├── CNAME                   # "soulfra.com"
│   └── index.html              # Homepage
│
├── app.py                      # Flask backend (localhost only)
├── database.py                 # SQLite database
├── voice_memos.db              # Voice memo storage
├── github_faucet.py            # GitHub auth integration
├── voice_to_repo.py            # AI routing pipeline
├── domains.json                # Domain manifest (16 domains)
├── mesh-router.js              # Express routing (port 8888)
├── .env                        # Secrets (GITHUB_TOKEN, etc.)
└── start-cringeproof.sh        # Launch script
```

---

## Domain 1: cringeproof.com

### What It Is
Anonymous voice memo wall where users record audio, transcribe with Whisper AI, and display on live feed.

### Live URL
https://cringeproof.com

### GitHub Repo
- **Source Code Repo**: `Soulfra/voice-archive`
- **GitHub Pages Repo**: `Soulfra/soulfra.github.io` (confusing - uses same repo for deployment)
- **CNAME**: `voice-archive/CNAME` → `cringeproof.com`

### Key Files
- `wall.html` - Main wall display (line 28: API_BASE = window.location.origin)
- `record-simple.html` - Voice recorder
- `login.html` - Login page (Google/GitHub/Apple buttons - **NOT WORKING** - needs OAuth CLIENT_IDs)
- `app.py` - Flask backend with `/api/wall/feed` endpoint

### How It Works
1. User visits cringeproof.com/record-simple.html
2. Records voice memo in browser
3. Audio sent to Flask backend (localhost:5001) via API
4. Whisper AI transcribes audio
5. Stored in SQLite database (voice_memos.db)
6. Displayed on wall.html via `/api/wall/feed` endpoint

### Current Workflow
**To edit and deploy:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive
# Edit files (wall.html, record-simple.html, etc.)
git add .
git commit -m "Update CringeProof"
git push origin main
# Auto-deploys to cringeproof.com via GitHub Pages
```

### What Works
- ✅ Static HTML pages (wall.html, record-simple.html)
- ✅ Domain DNS (cringeproof.com resolves)
- ✅ GitHub Pages deployment

### What Doesn't Work (Publicly)
- ❌ Voice recording (needs Flask backend deployed)
- ❌ Transcription (needs Whisper AI deployed)
- ❌ Login buttons (needs OAuth CLIENT_IDs in .env)
- ❌ Database feed (needs Flask `/api/wall/feed` deployed)

### The Gap
**Static site is deployed, backend is not.**

Users can visit cringeproof.com and see HTML, but can't record/transcribe/login because Flask only runs on your laptop (localhost:5001).

---

## Domain 2: soulfra.com

### What It Is
AI routing infrastructure - routes prompts to best AI model (OpenAI, Anthropic, Ollama, etc.).

### Live URL
https://soulfra.com

### GitHub Repo
- **Source Code Repo**: `Soulfra/soulfra` (main project)
- **GitHub Pages Repo**: `Soulfra/soulfra-site` (static site)
- **CNAME**: `soulfra.github.io/CNAME` → `soulfra.com`

### Key Files
- `soulfra-site/index.html` - Homepage
- `mesh-router.js` - Express server routing requests (port 8888)
- `mesh-config.json` - Routing configuration
- `github_faucet.py` - GitHub OAuth API key distribution

### How It Works
1. User sends prompt to Soulfra API
2. Mesh router analyzes prompt
3. Routes to best AI provider (OpenAI for code, Claude for analysis, Ollama for local)
4. Returns response

### Current Workflow
**To edit and deploy:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra-site
# Edit files
git add .
git commit -m "Update Soulfra site"
git push origin main
# Auto-deploys to soulfra.com via GitHub Pages
```

### What Works
- ✅ Static HTML site deployed
- ✅ Domain DNS (soulfra.com resolves)
- ✅ GitHub Pages deployment

### What Doesn't Work (Publicly)
- ❌ AI routing (mesh-router.js only runs on localhost:8888)
- ❌ API endpoints (not deployed)
- ❌ GitHub faucet (needs backend deployed)

### The Gap
Same as CringeProof - static site is live, backend is localhost-only.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WHAT'S DEPLOYED (GitHub Pages)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  cringeproof.com          soulfra.com                        │
│  ├── wall.html            ├── index.html                     │
│  ├── record-simple.html   └── (static HTML only)            │
│  └── login.html                                              │
│                                                              │
│  DNS: 185.199.108.153 (GitHub Pages)                         │
│  HTTPS: ✅ (GitHub auto-certificates)                        │
│  Backend: ❌ (no Flask/IPFS/AI deployed)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              WHAT'S ON LOCALHOST (Your Laptop)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  localhost:5001           Flask Backend                      │
│  ├── /api/wall/feed       Voice memo API                     │
│  ├── /auth/google         OAuth routes (broken - no CLIENTs)│
│  └── /github/status       GitHub auth                        │
│                                                              │
│  localhost:8888           Mesh Router (Express)              │
│  ├── /vault               Routing config                     │
│  └── /mesh-entry.html     Entry point                        │
│                                                              │
│  192.168.1.87:11434       Ollama (AI)                        │
│  └── /api/generate        Local LLM (llama2)                 │
│                                                              │
│  localhost:5002           IPFS Daemon                        │
│  └── /api/v0              Decentralized storage              │
│                                                              │
│  voice_memos.db           SQLite Database                    │
│  └── voice_memos table    Stored recordings                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Granular File Breakdown

### voice-archive/wall.html
**Purpose**: Display live feed of voice memos
**Lines of Interest**:
- Line 28: `const API_BASE = window.location.origin;` (changed from Cloudflare tunnel)
- Line 29: `const DOMAIN = 'cringeproof.com';`
- Line 30: `const REFRESH_INTERVAL = 30000;` (30 seconds)

**How it gets data**: Calls `${API_BASE}/api/wall/feed?domain=${DOMAIN}` every 30 seconds

**Problem**: API_BASE is `window.location.origin` which is `https://cringeproof.com` - but Flask is only on `http://localhost:5001`, so fetch fails when deployed.

**Fix**: Either:
1. Deploy Flask backend publicly (Fly.io, Railway, etc.)
2. Or change API_BASE to `https://your-backend-url.fly.dev`

---

### voice-archive/record-simple.html
**Purpose**: Voice recorder with Whisper AI transcription
**How it works**:
1. Captures audio from browser microphone
2. Converts to WAV format
3. POSTs to Flask `/api/transcribe` endpoint
4. Whisper AI transcribes
5. Displays text + saves to database

**Deployment Issue**: Requires Flask backend to handle transcription.

---

### app.py (Flask Backend)
**Purpose**: API server for CringeProof
**Key Routes**:
- Line 190: `@app.route('/api/wall/feed')` - Returns voice memos
- Line 198: `app.register_blueprint(github_auth_bp)` - GitHub OAuth
- Line 210: `@app.route('/api/transcribe')` - Whisper AI transcription

**Current Status**: Runs on localhost:5001 only (not deployed).

**Why it's not deployed**: No hosting configured (needs Fly.io/Railway/DigitalOcean/etc.).

---

### github_faucet.py
**Purpose**: Generate API keys from GitHub OAuth
**New Feature** (from previous conversation): `get_user_from_token()` method for single-user auth using your GitHub CLI token.

**How it works**:
1. User clicks "Connect GitHub" on website
2. OAuth flow redirects to GitHub
3. User authorizes
4. GitHub redirects back with code
5. Exchange code for access_token
6. Fetch GitHub profile (username, repos, commits)
7. Generate API key: `sk_github_{username}_{random}`
8. Store in database

**Current Status**: Code exists, but OAuth buttons on login.html don't work because GOOGLE_CLIENT_ID/GITHUB_CLIENT_ID not set in .env.

---

### voice_to_repo.py (AI Routing Pipeline)
**Purpose**: Voice → AI analysis → Auto-assign to domain → Generate component → Push to GitHub
**How it works**:
1. Takes voice transcript as input
2. Sends to Ollama AI for theme analysis
3. Matches against domains.json themes
4. Generates component/story/docs
5. Creates file in local repo
6. Sets macOS Finder folder color
7. Git commits and optionally pushes to GitHub

**Example**:
```bash
python3 voice_to_repo.py --transcript "I want to add star ratings to CringeProof wall"

# AI Output:
# Domain: cringeproof
# Type: component
# File: star-ratings.js
# Content: [Generated React component]
# Folder color → Pink
# Committed to: voice-archive/
# Push? y
# ✅ Live on GitHub
```

**Current Status**: Fully functional on localhost (requires Ollama running on 192.168.1.87:11434).

---

### domains.json
**Purpose**: Maps themes/keywords to domains for AI routing
**Structure**:
```json
{
  "domains": {
    "cringeproof": {
      "repo": "Soulfra/voice-archive",
      "theme": "voice memos, anonymous sharing, cringe protection",
      "color": "#ff006e",
      "finder_tag": "Pink",
      "prompts": ["What's the cringiest thing...", ...]
    },
    "soulfra": { ... },
    "calriven": { ... },  // NOT REAL (14 more like this)
  },
  "theme_keywords": {
    "voice": ["cringeproof", "soulfra"],
    "AI": ["soulfra", "agent-router"],
    ...
  }
}
```

**How AI uses it**: Analyzes voice transcript → Matches keywords → Routes to correct domain → Sets folder color.

---

## Simple Workflow: Edit → Deploy

### For CringeProof (cringeproof.com)

**Edit HTML/CSS/JS:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive
nano wall.html  # or use VS Code
```

**Deploy:**
```bash
git add .
git commit -m "Update wall design"
git push origin main
# Wait 1-2 minutes → Live on cringeproof.com
```

**Verify:**
```bash
open https://cringeproof.com
```

---

### For Soulfra (soulfra.com)

**Edit HTML/CSS/JS:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra-site
nano index.html
```

**Deploy:**
```bash
git add .
git commit -m "Update homepage"
git push origin main
# Wait 1-2 minutes → Live on soulfra.com
```

**Verify:**
```bash
open https://soulfra.com
```

---

## What You Can Do Right Now

### 1. Edit Static Sites
- Change text, colors, layout on cringeproof.com or soulfra.com
- Push to GitHub → Auto-deploys in 1-2 minutes

### 2. Run Full Stack Locally
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
./start-cringeproof.sh  # Starts Flask, IPFS, Mesh Router
open http://localhost:5001/wall.html  # Full features work
```

### 3. Use AI Voice Routing
```bash
python3 voice_to_repo.py --transcript "Add dark mode to CringeProof"
# AI analyzes → Creates component → Commits to repo → Optionally pushes to GitHub
```

---

## What You Can't Do Yet (Without Deploying Backend)

### 1. Public Voice Recording
- Users can't record on cringeproof.com because Flask isn't deployed
- **Fix**: Deploy Flask to Fly.io/Railway/DigitalOcean

### 2. Public Login (Google/GitHub Buttons)
- OAuth buttons on login.html don't work
- **Fix**: Get GOOGLE_CLIENT_ID and GITHUB_CLIENT_ID, add to .env, deploy Flask

### 3. Public AI Routing
- Mesh router (port 8888) only runs on localhost
- **Fix**: Deploy mesh-router.js to cloud server

---

## The 2 Deployment Options

### Option A: Keep It Simple (Static Sites Only)
- Just edit HTML/CSS/JS
- Push to GitHub → Deploys automatically
- No backend features (no voice recording, no AI, no login)
- **Good for**: Landing pages, portfolios, documentation

### Option B: Deploy Full Stack
- Deploy Flask backend (Fly.io/Railway)
- Deploy IPFS node (or use Pinata)
- Deploy mesh router (same server as Flask)
- Connect frontend to deployed backend
- **Good for**: Full CringeProof features (voice recording, transcription, AI routing)

---

## Next Steps

### To Simplify Your Mental Model:

1. **Ignore the 14 fake domains** in domains.json (calriven, deathtodata, etc.)
2. **Focus on 2 repos**:
   - `Soulfra/voice-archive` → cringeproof.com
   - `Soulfra/soulfra-site` → soulfra.com
3. **Remember the gap**: Static sites are live, backend is localhost-only

### To Get Login Buttons Working:

1. Register Google OAuth app: https://console.cloud.google.com/apis/credentials
2. Register GitHub OAuth app: https://github.com/settings/developers
3. Add CLIENT_IDs to .env
4. Restart Flask: `pkill -f app.py && python3 app.py`

### To Deploy Backend (Advanced):

1. Sign up for Fly.io: `brew install flyctl && fly auth signup`
2. Deploy Flask: `fly launch` (in soulfra-simple directory)
3. Update wall.html API_BASE to deployed URL
4. Push to GitHub → Full features work publicly

---

## Summary

**You Own**: 2 domains (cringeproof.com, soulfra.com)
**What's Live**: Static HTML sites on GitHub Pages
**What's Localhost**: Flask, IPFS, Ollama, Mesh Router
**The Gap**: Backend isn't deployed publicly
**How to Deploy**: Edit HTML → git push → auto-deploys in 1-2 min
**16 Domains Confusion**: Only 2 are real, ignore the rest

---

**Built on Bitcoin's Birthday 2026 🚀**
