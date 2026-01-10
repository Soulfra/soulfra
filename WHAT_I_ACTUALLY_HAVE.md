# WHAT I ACTUALLY HAVE - SOULFRA ECOSYSTEM

**Generated:** 2026-01-09
**Status:** WORKING but confusing AF

---

## 🌐 LIVE DOMAINS

### soulfra.com (LIVE ✅)
- **Points to:** GitHub Pages
- **Working pages:**
  - `/blog/` - Blog listing
  - `/about.html` - About page
  - Other pages exist but need mapping

### github.com/Soulfra/* (Your GitHub Org)
- `soulfra.github.io` - Main hub repo
- Other repos TBD (need GitHub API scan)

---

## 🖥️ LOCAL SERVERS RUNNING

### Port 5001 - Flask App (`app.py`)
**Location:** `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/app.py`
**Status:** ✅ RUNNING (2 processes: PID 1323, 40247)

**Key Routes Working:**
- `GET /` - Homepage
- `GET /me` - Personal dashboard
- `GET /domains` - Domain management
- `GET /my-domains` - Your domains
- `GET /waitlist` - Waitlist page
- `GET /<domain_slug>` - Dynamic domain pages
- `GET /<domain_slug>/blog` - Domain-specific blogs
- `GET /post/<slug>` - Blog posts
- `POST /post/<slug>/comment` - Comments
- `GET /search` - Search functionality
- `GET /train` - AI training interface
- `POST /train/predict` - AI predictions
- `GET /qr-search-gate` - QR code gated search
- `POST /api/ollama/search-github` - GitHub search via Ollama
- Many more (50+ routes total)

### Port 3002 - Node.js (`unified-server.js`)
**Location:** `/Users/matthewmauer/Desktop/cringeproof-vertical/api/unified-server.js`
**Status:** ✅ RUNNING (multiple background processes)
**Purpose:** Cringeproof voice API server

---

## 🗄️ DATABASE (soulfra.db)

**Location:** `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db`

### Core Tables (20 total)
1. `users` - User accounts
   - **Existing users:** soulfra, deathtodata, calriven, cringeproof, stpetepros
   - **NO ALICE YET** (you thought she existed, but she doesn't)

2. `posts` - Blog content
3. `comments` - Post comments
4. `subscribers` - Newsletter signups
5. `user_profiles` - Extended user info
6. `voice_qa_sessions` - Voice Q&A data
7. `voice_qa_answers` - Voice responses
8. `ai_agents` - AI agent configs
9. `collaboration_people` - People/contact list
10. `collaboration_graph` - Network connections
11. `minesweeper_board` - Game state (wtf?)
12. `cookie_graveyard` - Deleted cookies tracking
13. `void_visitors` - Anonymous visitors
14. `soul_documents` - Document storage
15. `vibe_ratings` - Content ratings
16. `soul_votes` - Voting system
17. `cringe_flags` - Content flagging
18. `agent_votes` - AI agent votes
19. `voice_suggestions` - Voice feedback
20. `star_stories` - Featured content

### Missing Tables (We just added these, not in DB yet)
- `domain_launches` - Waitlist domains
- `waitlist` - Signup tracking
- `custom_domains` - User domains

---

## 📁 KEY FILES & DIRECTORIES

### Built & Ready (Not Deployed)
- `./output/waitlist/` - 5 HTML files (EN, ES, JA, ZH, FR) + 6 JSON APIs
- `./output/domains/` - Domain manager UI
- `/Users/matthewmauer/Desktop/soulfra.github.io/waitlist/` - Copied, ready to push
- `/Users/matthewmauer/Desktop/soulfra.github.io/domains/` - Copied, ready to push

### Python Scripts
- `app.py` - Main Flask server (21,300+ lines!)
- `database.py` - DB schema & helpers
- `build_waitlist.py` - Static waitlist builder
- `build_domains_manager.py` - Domain UI builder
- `deploy_all.py` - Multi-repo deployment
- `domain_randomizer.py` - Smart domain assignment
- `launch_calculator.py` - Launch date logic
- `test_full_flow.py` - Integration test (incomplete)

### CSV Data
- `voice-archive/users.csv` - Test users including:
  - alice@example.com (Alice's Voice Lab) 🎙️
  - bob@example.com (Bob's Audio Diary) 📻
  - calriven@soulfra.ai (CalRiven Research Lab) 🔬
  - deathtodata@soulfra.ai (DeathToData Roast Zone) 🔥

---

## 🎯 WHAT ACTUALLY WORKS RIGHT NOW

### ✅ Fully Working
1. **soulfra.com/blog/** - Live blog
2. **soulfra.com/about.html** - Live about page
3. **localhost:5001/** - Flask app with 50+ routes
4. **localhost:5001/me** - Personal dashboard
5. **localhost:5001/domains** - Domain list
6. **localhost:3002/** - Cringeproof voice API

### ⚠️ Built But Not Deployed
1. **Waitlist** - Built static site, ready to push
2. **Domain Manager** - Built UI, ready to push
3. **Multi-language support** - 5 languages ready

### 🚧 Half-Built / Broken
1. **Alice test user** - Exists in CSV, NOT in database
2. **Waitlist database** - Tables don't exist yet (need `init_db()`)
3. **localhost:5001/my-domains** - Route exists but returns what?
4. **GitHub repo mapping** - Need to scan github.com/Soulfra/*

### ❌ Completely Missing
1. **Custom domain API** - `/api/domains/add` endpoint
2. **Alice's VM/subdomain** - Concept only
3. **User authentication** - How to log in as Alice?
4. **Domain DNS config** - How domains route to repos

---

## 🤔 THE BIG CONFUSION

### What you THOUGHT you had:
- Alice signed up for waitlist
- Domains auto-routing users
- VM/API endpoints per user
- Everything connected and working

### What you ACTUALLY have:
- Massive Flask app with tons of routes
- Static sites built but not deployed
- Database missing waitlist tables
- Alice exists in CSV but not as real user
- No clear "start here" path

---

## 🎬 NEXT STEPS (REAL TALK)

### Option 1: Deploy What's Ready
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 deploy_all.py --push
```
**Result:** Waitlist + Domain Manager live at soulfra.github.io

### Option 2: Test Locally First
```bash
# Initialize waitlist database
python3 database.py

# Create Alice user
python3 -c "from database import get_db; db = get_db(); db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', ('alice', 'alice@example.com', 'test123hash')); db.commit()"

# Run test
python3 test_full_flow.py

# Check localhost:5001/me
open http://localhost:5001/me
```

### Option 3: Map Everything First
```bash
# Scan GitHub repos
gh repo list Soulfra --limit 100

# Check all running services
lsof -i -P | grep LISTEN

# List all local projects
ls -d /Users/matthewmauer/Desktop/*/ | grep -E "(soulfra|calriven|death|cringe)"
```

---

## 💡 RECOMMENDATIONS

1. **STOP building new features** until you understand what exists
2. **Pick ONE user flow** to make work end-to-end (e.g., Alice signs up → sees dashboard)
3. **Document as you go** - update this file whenever something works
4. **Delete broken/unused code** - 21k line `app.py` is insane
5. **Use version control** - commit working states

---

## 📞 SUPPORT YOURSELF

When confused, run:
```bash
# What's running?
lsof -i -P | grep LISTEN

# What's in the database?
sqlite3 soulfra.db ".tables"

# What routes exist?
grep "@app.route\|@.*_bp.route" app.py | wc -l

# Is Alice real?
sqlite3 soulfra.db "SELECT * FROM users WHERE username='alice'"
```

---

**TL;DR:** You have WAY more than you think, but it's not connected. Focus on ONE path: Build → Test → Deploy → Repeat.
