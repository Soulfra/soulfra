# 🗺️ CringeProof / Soulfra Deployment Architecture Map

**Date:** January 4, 2026
**Problem:** Multiple repos, unclear deployment flow, login.html not working
**Goal:** Single source of truth for development and deployment

---

## 📁 Your 3 Repositories

### 1. `~/Desktop/roommate-chat/soulfra-simple/` ⭐ MAIN FLASK BACKEND
**Git Remote:** `https://github.com/Soulfra/roommate-chat.git`
**Purpose:** Flask backend + voice-archive static files (local dev)
**Port:** 5001 (localhost)

**What's Inside:**
```
soulfra-simple/
├── app.py                      → Flask server (5001)
├── voice-archive/              → Static frontend files
│   ├── login.html             → CringeProof login page
│   ├── wall.html              → Voice memo wall
│   ├── record-simple.html     → Voice recorder
│   └── index.html             → Homepage
├── github_auth_routes.py      → GitHub OAuth
├── github_faucet.py           → API key tier system
├── voice_to_repo.py           → Voice → GitHub automation
├── domains.json               → 16 domains (2 real, 14 theoretical)
├── templates/
│   ├── dashboard.html         → User dashboard
│   └── admin_dashboard.html   → Admin panel
└── WORKFLOWS.md               → This helps explain workflows
```

**Flask Routes (Relevant to CringeProof):**
- `/login.html` → `voice-archive/login.html` (NEW - just added)
- `/wall.html` → `voice-archive/wall.html`
- `/record-simple.html` → `voice-archive/record-simple.html`
- `/index.html` or `/` → `voice-archive/index.html`
- `/dashboard` → User dashboard (after GitHub OAuth login)
- `/admin` → Admin dashboard (tier 4 users only)
- `/github/login` → GitHub OAuth flow
- `/github/callback` → OAuth callback
- `/github/logout` → Logout

**Current Problem:**
- ❌ Flask server stuck in restart loop (port 5001 occupied)
- ❌ `/login.html` route added but server never fully restarted
- ❌ Can't access `http://localhost:5001/login.html` yet

**What This Repo Does:**
- Serves Flask API backend (voice upload, transcription, GitHub integration)
- Serves voice-archive HTML files for LOCAL DEVELOPMENT
- Does NOT deploy to public internet (only localhost)
- GitHub repo is for version control, not deployment

---

### 2. `~/Desktop/soulfra.github.io/` 📡 GITHUB PAGES DEPLOYMENT
**Git Remote:** `https://github.com/Soulfra/soulfra.github.io.git`
**Purpose:** Public static site (GitHub Pages)
**Domain:** soulfra.com (CNAME file)
**Auto-deploys:** Yes (GitHub Pages automatically serves this repo)

**What's Inside:**
```
soulfra.github.io/
├── CNAME                      → soulfra.com
├── index.html                 → Root homepage (soulfra.com)
├── cringeproof-qr/            → QR code generator
├── cringeproof-purple/        → GME/DRS vertical
├── cringeproof-crypto/        → Crypto vertical
├── cringeproof-sports/        → Sports vertical
└── ... (other projects)
```

**Live URLs:**
```
✅ https://soulfra.com (root index.html)
✅ https://soulfra.github.io/cringeproof-qr/
✅ https://soulfra.github.io/cringeproof-purple/
✅ https://soulfra.github.io/cringeproof-crypto/
✅ https://soulfra.github.io/cringeproof-sports/

❌ https://soulfra.com/cringeproof-qr/ (404 - CNAME only applies to root)
```

**Current Situation:**
- Contains STATIC sites only (no backend)
- Does NOT contain `voice-archive/` files
- Does NOT contain login.html
- Separate from your Flask backend

**GitHub Pages Quirk:**
- CNAME file (`soulfra.com`) only applies to ROOT directory
- Subdirectories (`cringeproof-qr/`) must use `.github.io` URL
- OR you need subdomain CNAMEs (qr.soulfra.com, crypto.soulfra.com)

---

### 3. `~/Desktop/cringeproof-vertical/` 🎮 SEPARATE CRINGEPROOF PROJECT
**Git Remote:** Unknown (need to check)
**Purpose:** Standalone CringeProof backend (Node.js/Express?)
**Port:** 3001 (localhost)

**What's Inside:**
- Separate backend for CringeProof predictions/debate app
- Has its own deployment docs (DEPLOYMENT-GUIDE.md, EVERYTHING-THATS-LIVE.md)
- Seems to be an alternative to the Flask backend
- Contains QR code generation, referral tracking, voice upload

**Routes (from EVERYTHING-THATS-LIVE.md):**
- `/health`
- `/r/:code` (redirect handler)
- `/ref/:code` (referral tracker)
- `/api/voice/upload`
- `/api/qr/generate`
- `/api/predictions`
- `/api/debate/topics`

**Current Status:**
- Not actively used? (you're working in soulfra-simple instead)
- Possible old version or parallel project

---

## 🔀 The Confusion (Explained)

### What You Asked:
> "i built a cringeproof.com folder on my desktop. maybe we should try and figure out the way to debug this and mirror it properly like a single deployment"

**The Problem:**
You have **3 separate projects** that all relate to CringeProof:

1. **soulfra-simple/voice-archive/** - Flask backend serves these files locally
2. **soulfra.github.io/** - Public GitHub Pages site (different repo!)
3. **cringeproof-vertical/** - Separate Node.js backend (port 3001)

**They are NOT synced!**
- Editing `voice-archive/login.html` only affects localhost:5001
- Does NOT update soulfra.github.io
- Does NOT update cringeproof-vertical

---

## 🎯 Single Deployment Strategy (3 Options)

### Option A: voice-archive as Source of Truth ⭐ RECOMMENDED
**Use:** `soulfra-simple/voice-archive/` as your main frontend
**Deploy:** Push to GitHub Pages when ready

**Workflow:**
1. Edit `voice-archive/login.html` locally
2. Test at `http://localhost:5001/login.html` (Flask serves it)
3. When ready to deploy:
   ```bash
   cd ~/Desktop/soulfra.github.io/
   cp -r ~/Desktop/roommate-chat/soulfra-simple/voice-archive/* ./cringeproof/
   git add .
   git commit -m "Update CringeProof from voice-archive"
   git push origin main
   # Wait 2 mins → Live at https://soulfra.github.io/cringeproof/
   ```

**Pros:**
- Single source (`voice-archive/`) for all frontend files
- Flask backend handles OAuth, API keys, voice processing
- GitHub Pages handles public static hosting

**Cons:**
- Manual copy/paste to deploy
- Need sync script to automate

---

### Option B: GitHub Pages as Source of Truth
**Use:** `soulfra.github.io/cringeproof/` as main frontend
**Backend:** Flask only for API routes

**Workflow:**
1. Edit files in `~/Desktop/soulfra.github.io/cringeproof/`
2. git push → Auto-deploys to `https://soulfra.github.io/cringeproof/`
3. Flask backend (`soulfra-simple/app.py`) handles:
   - `/github/login` (OAuth)
   - `/api/voice/upload` (Voice processing)
   - `/dashboard` (User dashboard)
   - `/admin` (Admin panel)

**Pros:**
- Direct push to GitHub Pages
- Clear separation: frontend (GitHub Pages) + backend (Flask)

**Cons:**
- Need to point login.html API_URL to deployed Flask backend
- Flask backend needs public URL (Fly.io, Railway, etc.)
- Local dev requires running both servers

---

### Option C: cringeproof.com Custom Domain
**Use:** Setup cringeproof.com as separate GitHub Pages repo
**Deploy:** Create `Soulfra/cringeproof` repo with CNAME

**Workflow:**
1. Create new repo: `github.com/Soulfra/cringeproof`
2. Copy `voice-archive/*` files there
3. Add CNAME file: `cringeproof.com`
4. Point DNS: `cringeproof.com` → GitHub Pages
5. Push → Auto-deploys to `https://cringeproof.com`

**Pros:**
- Clean custom domain (cringeproof.com)
- Separate from soulfra.com
- Each project has its own repo

**Cons:**
- Need to configure DNS
- Requires purchasing domain or using subdomain

---

## 🚦 Recommended Next Steps

### Immediate (Today):
1. **Fix Flask Server**
   - Kill all processes on port 5001
   - Start Flask cleanly
   - Test `http://localhost:5001/login.html` works

2. **Document Current Setup**
   - ✅ Done (this file!)
   - Decide on deployment strategy

3. **Choose Deployment Option**
   - Option A (voice-archive → GitHub Pages) is simplest
   - Create sync script if needed

### Short-term (This Week):
1. **Deploy Flask Backend Publicly**
   - Option: Fly.io, Railway, Heroku
   - Get public URL for OAuth callbacks
   - Update login.html API_URL to point to deployed backend

2. **Sync voice-archive to GitHub Pages**
   - Create sync script or GitHub Action
   - Auto-deploy when you push to roommate-chat repo

3. **Test Full OAuth Flow**
   - Visit public login page
   - Click GitHub OAuth button
   - Verify redirect to dashboard works
   - Check admin panel for tier 4 users

### Long-term (Future):
1. **Custom Domain for CringeProof**
   - Register cringeproof.com or use subdomain
   - Point to GitHub Pages
   - Clean public-facing URL

2. **Consolidate or Archive cringeproof-vertical**
   - Is it still needed?
   - Merge functionality into Flask backend?
   - Or keep as separate project?

---

## 📊 Comparison Table

| Feature | soulfra-simple | soulfra.github.io | cringeproof-vertical |
|---------|---------------|-------------------|---------------------|
| **Type** | Flask backend | Static GitHub Pages | Node.js backend |
| **Port** | 5001 | N/A (GitHub serves) | 3001 |
| **Purpose** | API + local dev | Public deployment | Predictions app |
| **Contains login.html** | ✅ Yes (voice-archive/) | ❌ No | Unknown |
| **GitHub OAuth** | ✅ Yes | ❌ Static only | Unknown |
| **Voice Processing** | ✅ Yes | ❌ No | ✅ Yes |
| **Tier System** | ✅ Yes (github_faucet.py) | ❌ No | Unknown |
| **Public URL** | ❌ Localhost only | ✅ soulfra.github.io | ❌ Localhost only |
| **Auto-deploys** | ❌ No | ✅ GitHub Pages | ❌ No |
| **Current Status** | 🔄 Active (debugging) | ✅ Working | ❓ Unclear |

---

## 🔧 Debugging Checklist

### Flask Server Issues:
- [x] Identified duplicate processes on port 5001
- [ ] Successfully kill all Flask processes
- [ ] Start Flask cleanly without watchdog issues
- [ ] Test `/login.html` route works
- [ ] Test `/github/login` OAuth flow works

### Deployment Issues:
- [x] Documented all 3 repos and their purposes
- [ ] Decide on single source of truth
- [ ] Create sync script (if needed)
- [ ] Deploy Flask backend publicly (if needed)
- [ ] Test end-to-end login → dashboard flow

---

## 💡 Key Insights

1. **voice-archive/ is NOT deployed to internet**
   - It's served by Flask on localhost:5001
   - GitHub repo `roommate-chat` is for version control only
   - NOT the same as GitHub Pages deployment

2. **soulfra.github.io is your public site**
   - Separate repo from roommate-chat
   - Auto-deploys when you push
   - Does NOT contain voice-archive files

3. **You need to COPY files to deploy**
   - Edit in `voice-archive/`
   - Test on localhost:5001
   - Copy to `soulfra.github.io/cringeproof/` when ready
   - Push to deploy publicly

4. **cringeproof-vertical seems redundant**
   - You have Flask backend (soulfra-simple)
   - You have Node backend (cringeproof-vertical)
   - Decide which one to use long-term

---

## 📝 Summary

**Your Setup:**
- 3 separate projects (Flask, GitHub Pages, Node backend)
- Not synced or mirrored
- login.html exists in voice-archive/ but not deployed publicly
- Flask server issues preventing local testing

**Solution:**
1. Fix Flask server (kill processes, restart clean)
2. Choose deployment strategy (Option A recommended)
3. Create sync workflow (manual or automated)
4. Deploy Flask backend publicly (for OAuth)
5. Test full login → dashboard → admin flow

**Next Command:**
```bash
# Kill all Flask processes
lsof -ti:5001 | xargs kill -9

# Start Flask cleanly
cd ~/Desktop/roommate-chat/soulfra-simple
python3 app.py

# Test login page
open http://localhost:5001/login.html
```

---

**Created:** 2026-01-04
**Status:** Documentation complete, Flask debugging in progress
