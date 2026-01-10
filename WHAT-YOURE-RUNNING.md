# 🗺️ What You're Actually Running - Complete Map

**Created:** January 2, 2026
**Purpose:** Understand ALL your services and how they connect

---

## 📊 Current Reality - FOUR Flask Apps Running

You currently have **FOUR separate Flask applications** running simultaneously on your laptop:

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP                               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App 1: MAIN (port 5001)                            │    │
│  │  Location: /roommate-chat/soulfra-simple/app.py     │    │
│  │  Purpose: Everything - Studio, automation, admin   │    │
│  │  Size: ~10,000+ lines of code                       │    │
│  │  Database: soulfra.db                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App 2: soulfra.com (port 8001)                     │    │
│  │  Location: /Soulfra/Soulfra.com/app.py              │    │
│  │  Purpose: Landing page with QR codes                │    │
│  │  Size: Small Flask app                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App 3: soulfraapi.com (port 5002)                  │    │
│  │  Location: /Soulfra/Soulfraapi.com/app.py           │    │
│  │  Purpose: API for QR-based account creation         │    │
│  │  Size: Medium Flask app                             │    │
│  │  Database: soulfraapi.db (separate!)                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App 4: soulfra.ai (port 5003)                      │    │
│  │  Location: /Soulfra/Soulfra.ai/app.py               │    │
│  │  Purpose: AI chat interface                         │    │
│  │  Size: Small Flask app                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Ollama (port 11434)                                │    │
│  │  Purpose: AI model server (llama3.2)                │    │
│  │  Used by: All 4 Flask apps can talk to it          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🤔 The Big Question: Do You Need All Four?

**Short answer: NO**

Your **MAIN app (port 5001)** already has:
- ✅ QR authentication (qr_auth.py)
- ✅ Studio for content creation
- ✅ Ollama integration
- ✅ Admin panel
- ✅ API endpoints
- ✅ Automation
- ✅ Everything!

The other 3 apps were **experiments** for the triple-domain QR flow. You can probably consolidate.

---

## 🎯 What Each App Actually Does

### App 1: MAIN (port 5001) - **THE WORKHORSE**

**File:** `app.py` (10,000+ lines)

**What it does:**
```python
# Content creation
/admin/studio                  # Write posts with Ollama
/admin/automation              # Auto-publish workflows
/admin/token-usage             # Track Ollama usage

# Authentication
/login                         # Username/password login
/login-qr                      # QR code passwordless login
/admin/join                    # Create account

# API
/api/domains/list              # List all your domains
/api/tokens/balance            # Check token balance
/api/studio/ollama-chat        # Generate content with AI

# Publishing
/magic-publish                 # Publish to GitHub Pages
```

**Database:** `soulfra.db` (main database with everything)

**This is the ONE you actually use!**

---

### App 2: soulfra.com (port 8001) - Landing Page

**File:** `Soulfra/Soulfra.com/app.py`

**What it does:**
- Shows a static landing page
- Displays QR code for signup
- Minimal Flask routes
- Mostly just serves `index.html`

**Purpose:** Experimental QR-based signup flow

**Do you need it?** Probably not - your main app has QR auth already

---

### App 3: soulfraapi.com (port 5002) - API Backend

**File:** `Soulfra/Soulfraapi.com/app.py`

**What it does:**
```python
/qr-signup?ref=TOKEN           # QR-based account creation
# Creates user, generates session token
# Redirects to soulfra.ai with session
```

**Database:** `soulfraapi.db` (separate database!)

**Purpose:** Account creation via QR scan

**Do you need it?** Probably not - your main app has user creation

---

### App 4: soulfra.ai (port 5003) - AI Chat

**File:** `Soulfra/Soulfra.ai/app.py`

**What it does:**
```python
/                              # Chat interface
/?session=TOKEN                # Validate session and show chat
/api/chat                      # Send messages to Ollama
```

**Purpose:** AI chat interface after QR signup

**Do you need it?** Probably not - your main app has Studio with Ollama

---

## 🔄 How They're Supposed to Work Together

The **triple domain flow** was designed like this:

```
1. User visits soulfra.com (port 8001)
   └─> Sees QR code on landing page

2. User scans QR with phone
   └─> Opens URL: soulfraapi.com/qr-signup?ref=TOKEN

3. soulfraapi.com (port 5002):
   └─> Creates user account
   └─> Generates session token
   └─> Redirects to: soulfra.ai/?session=TOKEN

4. soulfra.ai (port 5003):
   └─> Validates session
   └─> Shows AI chat interface
   └─> User can chat with Ollama
```

**The idea:** Passwordless signup via QR → instant AI chat

**The reality:** Your main app already does this better!

---

## 💡 Recommendation: Consolidate

### Option 1: Use Only Main App (SIMPLE)

**Stop the 3 extra apps, use only port 5001:**

```bash
# Stop the triple domain system
cd Soulfra
bash STOP-ALL.sh

# Keep only main app running
cd ..
python3 app.py
```

**Everything you need is in the main app:**
- QR login: `http://localhost:5001/login-qr`
- Studio: `http://localhost:5001/admin/studio`
- Automation: `http://localhost:5001/admin/automation`

### Option 2: Keep Triple Domain for Specific Use Case

**Only if you REALLY want the QR signup → AI chat flow:**

Keep all 4 running for the specific flow described above.

### Option 3: Merge the Best Parts

Take the landing page from soulfra.com and AI chat from soulfra.ai, add them as routes to your main app.

---

## 🌐 How GitHub Pages Fits In

**Completely separate from Flask apps!**

```
GitHub Pages (FREE hosting):
├─ soulfra.com                 → https://soulfra.github.io/soulfra/
├─ calriven.com                → https://soulfra.github.io/calriven/
└─ deathtodata.com             → https://soulfra.github.io/deathtodata/

These are STATIC HTML files.
NO Flask server needed!
```

**How it works:**
1. You write content in Studio (main app, port 5001)
2. Magic Publish generates HTML files → `output/soulfra/`
3. Git push to GitHub
4. GitHub Pages serves the HTML
5. People visit soulfra.com (points to GitHub Pages)

**Flask is only for CREATING content, not serving it!**

---

## 🗺️ Complete System Map

```
┌─────────────────────────────────────────────────────────────────┐
│                       THE FULL PICTURE                          │
└─────────────────────────────────────────────────────────────────┘

LOCAL (Your Laptop):
  ┌─────────────┐
  │ Main Flask  │ ─> Create content, manage everything
  │  (port 5001)│
  └──────┬──────┘
         │
         ├──> Ollama (11434) ─> Generate AI content
         │
         ├──> soulfra.db ─> Store posts, users, data
         │
         └──> output/soulfra/ ─> Generate HTML files
                    │
                    ↓
                 Git push
                    │
                    ↓
GITHUB:
  ┌──────────────────────┐
  │ github.com/Soulfra/  │
  │        soulfra       │ ─> Git repository
  └──────────┬───────────┘
             │
             ├──> GitHub Actions (auto-deploy)
             │
             ↓
GITHUB PAGES:
  ┌──────────────────────┐
  │ soulfra.github.io/   │
  │      soulfra/        │ ─> Static HTML hosting (FREE)
  └──────────┬───────────┘
             │
             ↓
DNS:
  soulfra.com ──> Points to GitHub Pages
  (via CNAME record)

PUBLIC INTERNET:
  http://soulfra.com ─> Anyone can visit!
```

---

## 📱 Phone Access

Your phone can access TWO different things:

### 1. Local Flask Apps (Same WiFi)
```
Phone → Same WiFi → Laptop IP → Flask apps

http://192.168.1.87:5001  ← Main app
http://192.168.1.87:8001  ← soulfra.com app
http://192.168.1.87:5002  ← API app
http://192.168.1.87:5003  ← AI chat app
```

**Only works on same WiFi!**

### 2. GitHub Pages (Internet)
```
Phone → Internet → soulfra.com → GitHub Pages

http://soulfra.com  ← Works from ANYWHERE
```

**Works from anywhere with internet!**

---

## 🔑 Which Port Does What?

| Port | Service | Purpose | Do You Need It? |
|------|---------|---------|-----------------|
| **5001** | Main Flask app | Studio, automation, everything | ✅ YES |
| 8001 | soulfra.com app | Landing page | ⚠️ Maybe (merge into main?) |
| 5002 | soulfraapi.com | QR signup API | ⚠️ Maybe (main app has this) |
| 5003 | soulfra.ai | AI chat | ⚠️ Maybe (main app has Studio) |
| **11434** | Ollama | AI model server | ✅ YES |

**Minimum to run Soulfra:**
- ✅ Port 5001 (main app)
- ✅ Port 11434 (Ollama)
- ✅ soulfra.db (database)

That's it!

---

## 🧹 Cleanup Plan

If you want to simplify and use just the main app:

### Step 1: Stop Extra Apps
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/Soulfra
bash STOP-ALL.sh
```

### Step 2: Verify Main App Running
```bash
# Check port 5001
lsof -i :5001

# If not running, start it
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

### Step 3: Test Everything Works
```bash
# Visit main app
curl http://localhost:5001/admin/studio

# Test QR login
curl http://localhost:5001/login-qr

# Test automation
curl http://localhost:5001/admin/automation
```

### Step 4: Keep Publishing to GitHub Pages
```bash
# This still works!
curl http://soulfra.com

# Magic publish from main app
http://localhost:5001/magic-publish
```

---

## 📊 Database Situation

You have **TWO separate databases:**

1. **soulfra.db** (main) - Used by port 5001
   - Has everything: posts, users, brands, tokens, QR codes
   - This is the important one!

2. **soulfraapi.db** - Used by port 5002
   - Separate database for QR signup flow
   - Probably has different users than main db
   - May cause confusion!

**Recommendation:** Consolidate to just `soulfra.db` if you stop using the triple domain system.

---

## 🎯 TL;DR - What You're Running

**The Essential:**
- Main Flask app (5001) - Your workhorse
- Ollama (11434) - AI generation
- soulfra.db - Your database
- GitHub Pages - Public website (soulfra.com)

**The Experimental:**
- soulfra.com app (8001) - Landing page
- soulfraapi.com (5002) - QR signup
- soulfra.ai (5003) - AI chat
- These form the "triple domain QR flow"

**The Question:**
Do you need the triple domain flow? Or can you consolidate to just the main app?

**For most use cases: Just use the main app!**

---

## 🚀 Next Steps

1. **Test everything:** Use `SIMPLE-TEST-NOW.md`
2. **Decide:** Keep all 4 apps, or consolidate to main app?
3. **Deploy:** See `DEPLOYMENT-SIMPLIFIED.md` for going live
4. **Domains:** See `DOMAINS-EXPLAINED.md` for DNS setup

---

**Bottom Line:** You're running 4 Flask apps when you probably only need 1 (the main app on port 5001). The other 3 were experiments for a specific QR-based signup flow. Your main app already has everything you need!
