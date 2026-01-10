# Everything You Have - Complete Soulfra System Overview

**Date:** December 31, 2024
**Your Local IP:** 192.168.1.87

## 🎯 What's Actually Running RIGHT NOW

### Flask Server (Port 5001)
```
http://localhost:5001 (laptop)
http://192.168.1.87:5001 (iPhone)
```

**Features:**
- ✅ **Unified Dashboard** → `/dashboard`
- ✅ **AI Search** → `/search`
- ✅ **QR Faucet** → `/qr-search-gate`
- ✅ **AI Chat** → `/chat`
- ✅ **Canvas/Drawing** → `/draw`, `/admin/canvas`
- ✅ **Status Page** → `/status`
- ✅ **Generator** → `/generate`

**Database:** `soulfra.db` (150+ tables, all your data)

### Ollama (Port 11434)
```
http://localhost:11434
```

**Status:** ✅ Running
**Models:** llama3.2 + others

### Node.js Servers
- Port 3000: Logo generator + XP system
- Port unknown: Picture of Day voting

## 📱 iPhone Access URLs

**Main Dashboard (Start Here!):**
```
http://192.168.1.87:5001/dashboard
```

**All Features:**
| Feature | URL |
|---------|-----|
| Dashboard | http://192.168.1.87:5001/dashboard |
| Search | http://192.168.1.87:5001/search |
| QR Faucet | http://192.168.1.87:5001/qr-search-gate |
| Chat | http://192.168.1.87:5001/chat |
| Canvas | http://192.168.1.87:5001/admin/canvas |
| Drawing | http://192.168.1.87:5001/draw |
| Status | http://192.168.1.87:5001/status |

## 🌐 Deployed Sites (Live on GitHub Pages)

1. **Soulfra** - https://soulfra.github.io/soulfra/
   - The Soulfra Experiment (7 chapters)
   - Philosophy and story

2. **CalRiven** - https://soulfra.github.io/calriven/
   - Technical ownership philosophy (7 chapters)
   - Infrastructure and privacy

3. **DeathToData** - https://soulfra.github.io/deathtodata/
   - Privacy manifesto
   - Homebrew lab guides

4. **HowToCookAtHome** - https://soulfra.github.io/howtocookathome/
   - Cooking blog (3 recipes)
   - Ready for newsletter

## 📂 Folder Structure

```
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/

├── app.py                          ← Main Flask server (port 5001)
├── soulfra.db                      ← Main database (150+ tables)
├── templates/                      ← HTML templates
│   └── unified_dashboard.html      ← New dashboard (just added!)
├── output/                         ← Built static sites
│   ├── soulfra/                    ← Deployed to GitHub Pages
│   ├── calriven/                   ← Deployed to GitHub Pages
│   ├── deathtodata/                ← Deployed to GitHub Pages
│   ├── howtocookathome/            ← Deployed to GitHub Pages
│   └── calriven-search/            ← NEW! Ready to deploy
└── Soulfra/                        ← Triple-domain system (NEW!)
    ├── Soulfra.com/                ← Static landing
    ├── Soulfraapi.com/             ← Account API
    └── Soulfra.ai/                 ← AI chat

```

## 🆕 What We Just Built

### 1. Unified Dashboard
**File:** `templates/unified_dashboard.html`
**Route:** `/dashboard`
**URL:** http://192.168.1.87:5001/dashboard

**Features:**
- Shows all systems in one place
- Search box (AI-powered)
- Quick links to all features
- Stats (users, posts, QR scans)
- QR code for iPhone access
- Links to deployed sites
- Mobile-responsive

### 2. iPhone Test Guide
**File:** `IPHONE-TEST-GUIDE.md`

**Complete instructions for:**
- Accessing from iPhone
- Testing all features
- QR code generation
- Troubleshooting

### 3. CalRiven Search Page
**Folder:** `output/calriven-search/`
**File:** `index.html`

**Features:**
- Client-side search (no server)
- QR code to AI search
- Links to CalRiven posts
- Ready to deploy to GitHub Pages

### 4. Triple-Domain System
**Folder:** `Soulfra/`

**Complete system with:**
- soulfra.com (static landing + QR)
- soulfraapi.com (account creation API)
- soulfra.ai (AI chat interface)
- Helper scripts (START-ALL.sh, TEST-FLOW.sh, etc.)

## 💾 Your Database

**File:** `soulfra.db`
**Size:** Large (150+ tables)

**Key Tables:**
- `users` - User accounts
- `posts` - Blog posts
- `qr_codes` - QR code tracking
- `qr_scans` - Scan analytics
- `search_sessions` - Search history
- `qr_faucets` - Faucet QR codes
- `canvas_pairing` - Device pairing
- `domains` - Multi-domain management
- Many more...

**View in SQLite:**
```bash
sqlite3 /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db
.tables
.schema users
SELECT COUNT(*) FROM users;
```

## 🔍 Search & Faucet Features (Already Working!)

### AI Search
**URL:** http://192.168.1.87:5001/search

**Features:**
- Semantic search with Ollama
- Search across all brands
- Filters by brand
- QR-gated access option

### QR Faucet
**URL:** http://192.168.1.87:5001/qr-search-gate

**What It Does:**
- Generates QR codes that create content
- JSON payloads embedded in QR
- HMAC signatures for security
- Track who scans what

**Example Use Cases:**
- Blog post creation via QR
- Auth tokens
- Content transfer
- Offline-first data

## 🚀 How to Test Everything on iPhone

### Step 1: Make Sure Same WiFi
Laptop and iPhone must be on same WiFi network.

### Step 2: Open Dashboard
On iPhone Safari:
```
http://192.168.1.87:5001/dashboard
```

### Step 3: Bookmark It
Tap Share → Add to Home Screen → Name it "Soulfra"

### Step 4: Explore
- Try search
- Generate QR codes
- Chat with AI
- Draw on canvas
- Check status page

## 📊 System Status Check

```bash
# Check Flask
curl -I http://localhost:5001/dashboard

# Check Ollama
curl http://localhost:11434/api/tags

# Check database
sqlite3 soulfra.db "SELECT COUNT(*) FROM users;"

# Check deployed sites
curl -I https://soulfra.github.io/soulfra/
```

## 🎯 Next Steps (Optional)

### Deploy CalRiven Search
```bash
cd output/calriven-search
git init
git add .
git commit -m "Deploy CalRiven search"
gh repo create calriven-search --public --source=. --push
```

### Generate Dashboard QR Code
```bash
curl http://192.168.1.87:5001/api/qr/dashboard -o dashboard-qr.png
open dashboard-qr.png
```

### Start Triple-Domain System
```bash
cd Soulfra
bash START-ALL.sh
```

Then access:
- http://192.168.1.87:8001 (landing page)
- http://192.168.1.87:5002 (API)
- http://192.168.1.87:5003 (chat)

## 🔧 Troubleshooting

### Can't Access from iPhone

**Check same WiFi:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Should show: 192.168.1.87
```

**Restart Flask:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
pkill -f "python3 app.py"
python3 app.py
```

### Features Not Working

**Check what's running:**
```bash
ps aux | grep -E "python3.*app.py|ollama|npm"
```

**Check logs:**
```bash
# Flask logs
tail -f logs/*.log

# Or check background process
# Background Bash ID: 47cce2
```

## 📝 Key Documents

| File | What It Is |
|------|-----------|
| `EVERYTHING-YOU-HAVE.md` | This file - complete overview |
| `IPHONE-TEST-GUIDE.md` | iPhone testing instructions |
| `AUDIT-WHATS-ACTUALLY-DEPLOYED.md` | What's deployed vs localhost |
| `OWN-YOUR-STACK.md` | Self-hosting philosophy |
| `README-START-HERE.md` | Beginner's guide |
| `soulfra/README.md` | Triple-domain system docs |
| `output/calriven-search/README.md` | CalRiven search deployment |

## 💡 Summary

**You have TWO main systems:**

### System 1: Working Flask Server (Port 5001)
- ✅ Running right now
- ✅ Has search, QR faucet, chat, canvas
- ✅ Massive database with all your data
- ✅ 4 deployed GitHub Pages sites
- ✅ **NEW:** Unified dashboard
- ✅ **NEW:** iPhone-accessible

### System 2: Triple-Domain System (New Build)
- ✅ Separate folder (Soulfra/)
- ✅ Three domains (com, api, ai)
- ✅ QR-based account creation
- ✅ Ready to test

**Recommendation:** Start with System 1 (port 5001) on iPhone first!

**URL:** http://192.168.1.87:5001/dashboard

## 🎉 Bottom Line

Everything is built, organized, and documented.

**To test on iPhone RIGHT NOW:**
1. Open Safari on iPhone
2. Go to: http://192.168.1.87:5001/dashboard
3. Explore all the features
4. Scan QR codes
5. Chat with AI
6. Search content

**You're ready to go!**
