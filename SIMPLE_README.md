# Soulfra - What This Actually Is

**Stop reading 409 markdown files. Read this instead.**

---

## What Is This? (3 Sentences)

**Soulfra** is a self-hosted Flask app for managing multiple web projects with unified authentication.

It started as a voice memo platform (CringeProof) and evolved into a multi-domain system with professional directories (StPetePros), voice workflows, and AI integration.

Right now it runs on your laptop and friends can access it via your local network or internet tunnel.

---

## What Actually Works

### ✅ Currently Working Routes

| Route | What It Does |
|-------|-------------|
| `/` | Homepage |
| `/signup/professional` | Create professional account (requires Soulfra login) |
| `/professional/<id>` | Professional profile page |
| `/professional/inbox` | Message inbox for professionals |
| `/status` | System dashboard |
| `/voice` | Voice recorder |
| `/chat` | Chat interface with Ollama |

### 🔧 Partially Working

| Route | Status | Issue |
|-------|--------|-------|
| `/login` | ⚠️ Frontend works | OAuth not configured (needs CLIENT_IDs) |
| Voice transcription | ⚠️ Works if Whisper installed | Requires local Whisper setup |
| Ollama AI | ⚠️ Works if Ollama running | Needs `ollama serve` |

### ❌ Not Yet Working

- Payment processing (Stripe not configured)
- Email notifications (SMTP not configured)
- Google My Business reviews (API not configured)
- Most of the 2,533 routes (bloat from experimentation)

---

## What You Have

### Real Assets

**2 Live Domains:**
1. **cringeproof.com** - Static HTML on GitHub Pages (no backend deployed)
2. **soulfra.com** - Static HTML on GitHub Pages (no backend deployed)

**Local Backend:**
- Flask app with ~2,500 routes (most unused)
- SQLite database (soulfra.db)
- Voice recording/transcription
- Professional directory system
- Multi-domain routing
- Soulfra Master Auth (cross-domain login)

**NOT Real:**
- 14 other domains in config (calriven, deathtodata, etc.) - theoretical/future projects
- Most documentation (409 .md files - outdated)
- Production deployment (it's all localhost)

---

## File Structure (What Matters)

```
soulfra-simple/
├── app.py                          # Main Flask app (12,000 lines - needs cleanup)
├── soulfra.db                      # SQLite database (all user data)
├── domain_config/
│   ├── domains.yaml                # 9 domain configs (only 2 are real)
│   └── secrets.env                 # API keys, passwords (DON'T COMMIT!)
├── templates/
│   ├── stpetepros/                 # Professional directory templates
│   ├── auth/                       # Login/signup pages
│   └── (100+ other folders)
├── voice_encryption.py             # Voice memo encryption (AES-256-GCM)
├── voice_memo_dissector.py         # Extract ideas from voice memos
├── database_encryption.py          # Database field encryption
└── LOCAL_NETWORK_SETUP.md          # How to share with friends ← READ THIS

IGNORE THESE (Outdated docs):
├── 409 .md files                   # 95% outdated/theoretical
└── archive/                        # Old versions
```

---

## How to Use

### Start Flask

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

You'll see:
```
* Running on http://192.168.1.87:5001
```

### Access It

**On your laptop:**
```
http://localhost:5001
```

**On your phone (same WiFi):**
```
http://192.168.1.87:5001
```

**From internet (using ngrok):**
```bash
ngrok http 5001
# Share the https://xxx.ngrok.io URL
```

### Let Friends Access

See **LOCAL_NETWORK_SETUP.md** for 3 methods:
1. WiFi only (same network)
2. Ngrok tunnel (internet access)
3. Cloudflare tunnel (permanent URL)

---

## What This Project Is (Pick One)

You asked: "is this an OSS project or open core or marketplace or router for LLM?"

**Answer: It's all of them, but not deployed yet.**

### 1. OSS Project (Potential)

**What you have:**
- Open-source Flask code
- MIT-licensable
- Could be packaged and released

**What's missing:**
- Clean up bloated code (2,500 routes → 50 core routes)
- Remove personal info from database
- Write actual documentation
- Create `requirements.txt` that works
- Package it properly

**If you wanted to make this OSS:**
```bash
# Clean up repo
# Remove secrets
# Write docs
# Push to GitHub
# Add MIT license
```

### 2. Open Core (Potential)

**What you have:**
- Free tier: Voice recording, basic auth
- Premium features: Professional directory, inbox, encryption

**What's missing:**
- Payment processing (Stripe)
- Pricing tiers
- Feature flags

### 3. LLM Marketplace/Router (Exists!)

**What works NOW:**
- `mesh-router.js` - Routes to different AI models
- `voice_to_repo.py` - Analyzes voice memos, routes to domain
- Ollama integration for local AI

**Files:**
- `ollama_proxy.py` - Proxy to Ollama
- `ai_host.py` - AI narrative host
- `mesh-config.json` - Routing rules

**What's missing:**
- Multiple LLM backends (only Ollama configured)
- Load balancing
- Token tracking/billing

### 4. Multi-Domain Platform (Exists!)

**What works:**
- `domain_config/domains.yaml` - 9 domain configs
- `brand_router.py` - Detects domain, routes accordingly
- `auth_bridge.py` - Unified auth across domains

**Domains configured:**
1. soulfra.com - Master hub
2. stpetepros.com - Professional directory
3. cringeproof.com - Voice memos
4-9. (Theoretical domains)

---

## The Honest Truth

### What You Built

A **monolithic Flask experiment** with:
- Voice recording + transcription
- Professional directory (StPetePros)
- Multi-domain routing
- Database encryption
- QR code authentication
- AI integration (Ollama)
- GitHub workflows
- 2,500+ routes (mostly unused)

### Current State

- 🟢 **Works locally** - all features work on your laptop
- 🟡 **Partially deployed** - 2 static sites on GitHub Pages
- 🔴 **Not production ready** - backend only on localhost
- 📚 **Documentation hell** - 409 .md files confusing you

### What You Need

**Option A: Keep Experimenting**
- Keep building features
- Don't worry about deployment
- Share via ngrok when you want friends to test

**Option B: Deploy One Feature**
- Pick ONE thing (StPetePros OR CringeProof)
- Deploy just that to a VPS
- Ignore the other 2,499 routes

**Option C: Package as OSS**
- Clean up code drastically
- Remove 95% of routes
- Write clear docs
- Release on GitHub

**Option D: Self-Host for Friends**
- Run Flask on your laptop 24/7
- Use Cloudflare Tunnel for permanent URL
- Friends access via your domain
- See **LOCAL_NETWORK_SETUP.md**

---

## Quick Commands

```bash
# Start Flask
python3 app.py

# Check if running
curl http://localhost:5001/

# Share with friends (WiFi)
# They visit: http://192.168.1.87:5001

# Share with friends (Internet)
ngrok http 5001

# Check database
sqlite3 soulfra.db "SELECT * FROM soulfra_master_users;"

# Encrypt database
python3 database_encryption.py --encrypt

# Test voice encryption
python3 voice_encryption.py

# Check what's actually running
ps aux | grep python
ps aux | grep ollama
```

---

## Next Steps

**If you want to:**

### → Share with friends NOW
Read: **LOCAL_NETWORK_SETUP.md**

### → Understand how friends can add code
Read: **COLLABORATION_GUIDE.md** (creating next...)

### → Deploy to production
Read: **PRODUCTION_DEPLOYMENT.md** (but honestly, use ngrok first)

### → Clean up this mess
1. Archive 90% of .md files
2. Delete unused routes from app.py
3. Focus on ONE feature
4. Actually deploy it

### → Make this OSS
1. Create new repo: `soulfra-core`
2. Copy only working routes
3. Remove secrets
4. Write proper README
5. Add MIT license
6. Release

---

## Summary

**You have:** A powerful but bloated Flask app with tons of features that work locally.

**You want:** Friends to access it, contribute code, use Soulfra login.

**You need:** Pick ONE direction (self-host / deploy / OSS) and commit.

**Read next:** LOCAL_NETWORK_SETUP.md to share with friends RIGHT NOW.

---

**Stop overthinking. Start sharing.** 🚀
