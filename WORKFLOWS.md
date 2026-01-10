# 🔄 Soulfra Workflows Explained

You're working with **3 separate workflows** - here's how they connect:

---

## Workflow A: **Local Development** (Edit → See Live)

**What**: Edit files locally and see changes instantly at `localhost:5001`

**How it works**:
1. Edit any file in `voice-archive/` (login.html, wall.html, etc.)
2. Flask auto-reloads when files change
3. Refresh `http://localhost:5001/login.html` → see your changes

**Example**:
```bash
# Edit the login page
code voice-archive/login.html

# Flask detects the change and reloads
# Visit http://localhost:5001/login.html → see your edits
```

**Current Status**: ✅ Working now (just added `/login.html` route)

---

## Workflow B: **GitHub Pages Deployment** (Push → Auto-Deploy)

**What**: Push to GitHub → Auto-deploys to `cringeproof.com` in 2 minutes

**How it works**:
1. Edit files in `voice-archive/` locally
2. Commit and push to GitHub: `git push origin main`
3. GitHub Actions builds and deploys to `cringeproof.com`
4. CNAME file points custom domain to GitHub Pages

**Example**:
```bash
# Make changes
code voice-archive/login.html

# Push to GitHub
git add voice-archive/login.html
git commit -m "Update login page"
git push origin main

# Wait 2 mins → https://cringeproof.com/login.html updated
```

**Current Status**: ✅ Already configured (GitHub Pages + CNAME)

---

## Workflow C: **Voice → Transcript → GitHub** (Record → Auto-Push)

**What**: Voice recordings → transcripts → GitHub repos

**How it works**:
1. **Record**: Use `/wall.html` or `/record-simple.html` to record voice
2. **Transcribe**: Flask backend sends to Whisper API → gets transcript
3. **Route**: `voice_to_repo.py` analyzes transcript with Ollama AI
   - Determines which domain/topic it belongs to (cringeproof, soulfra, etc.)
   - Creates a file in the appropriate GitHub repo
4. **Push**: Uses `gh` CLI (already authenticated on your terminal) to push to GitHub

**Example**:
```
You say: "I just built a cool login system for CringeProof"

→ Whisper transcribes it
→ Ollama analyzes: "This is about CringeProof project management"
→ voice_to_repo.py creates: cringeproof/logs/2026-01-04-login-system.md
→ Pushes to GitHub: Soulfra/voice-archive repo
```

**Current Status**: ✅ Working (you're already connected via `gh` CLI)

---

## Understanding Domains vs Repos

**domains.json has 16 domains** - but only **2 are real**:
- ✅ `cringeproof.com` (real domain, hosted on GitHub Pages)
- ✅ `soulfra.com` (real domain, your main site)
- ❌ Other 14 are **theoretical domains** for AI routing

**Why 14 fake domains?**
- `voice_to_repo.py` uses Ollama AI to categorize your voice recordings
- AI can route to: "gaming", "music", "meditation", "productivity", etc.
- These are **topics**, not actual websites
- They help organize your voice memos into logical GitHub folders

**Real setup**:
```
Soulfra/voice-archive/
├── cringeproof/     ← Real domain (cringeproof.com)
├── soulfra/         ← Real domain (soulfra.com)
├── gaming/          ← Fake domain (just a folder)
├── music/           ← Fake domain (just a folder)
└── ... 10 more theoretical domains
```

---

## Your Current Setup:

**GitHub Authentication**:
- ✅ Already authenticated via `gh` CLI (terminal)
- ✅ Can also OAuth via website (`/github/login`)

**You can**:
1. Edit `voice-archive/login.html` locally → see at `localhost:5001/login.html` ✅
2. Push to GitHub → auto-deploys to `cringeproof.com` ✅
3. Record voice → auto-pushed to GitHub repos ✅
4. Login with GitHub OAuth → see dashboard with tier/activity ✅

**You asked**:
> "im just trying to edit it and we can see it live like the popout or publish?"

**Answer**:
- **Live (localhost)**: Edit → save → refresh `localhost:5001` → see changes ✅
- **Publish (cringeproof.com)**: `git push` → wait 2 mins → live on internet ✅

---

## Quick Commands:

```bash
# Start Flask (local dev)
python3 app.py
# → Visit http://localhost:5001/login.html

# Edit and see changes live
code voice-archive/login.html
# → Save → refresh browser → see changes

# Publish to internet
git add .
git commit -m "Update login"
git push origin main
# → Wait 2 mins → https://cringeproof.com updated

# Record voice → GitHub (already working)
# Just visit /wall.html and record
# → Auto-transcribes → auto-pushes to GitHub
```

---

**Built on 2026-01-04** 🚀

Everything is connected now:
- ✅ Local dev workflow (edit → see live)
- ✅ GitHub Pages deployment (push → auto-deploy)
- ✅ Voice → GitHub workflow (record → auto-push)
- ✅ GitHub OAuth login (website → dashboard)
