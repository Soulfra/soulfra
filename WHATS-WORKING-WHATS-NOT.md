# What's Working vs What's Not - Complete System Map

**Created:** December 31, 2024
**Purpose:** Clear explanation of your TWO SEPARATE systems and how they work together

---

## TL;DR - You Have 2 Systems

```
┌───────────────────────────────────────────────────┐
│ System 1: soulfra-simple (CONTROL PANEL)         │
│ Port: 5001                                         │
│ Status: ✅ WORKING RIGHT NOW                      │
│ Purpose: Manage 200+ domains, research, APIs      │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ System 2: Soulfra/ (3-DOMAIN AUTH SYSTEM)        │
│ Ports: 8001, 5002, 5003                          │
│ Status: ❌ FILES EXIST, NOT RUNNING               │
│ Purpose: QR auth, static sites, AI chat          │
└───────────────────────────────────────────────────┘
```

**These are SEPARATE. They don't conflict. Both can run at the same time.**

---

## System 1: Control Panel (Port 5001)

### What It Is:
Your **domain management headquarters**. This is where you:
- Research domains with Ollama (DNS, website scraping, AI suggestions)
- Create/edit/delete domains in database
- Chat with AI about each domain
- Generate content ideas
- Manage 200+ domains from one place

### Status: ✅ WORKING

**URLs that work RIGHT NOW:**
```bash
# Admin UI
http://localhost:5001/admin/domains
# Manage all domains in one place

# API Documentation
http://localhost:5001/api/docs
# Interactive API docs (HTML page)

# Domain List API
http://localhost:5001/api/domains/list
# Returns JSON: {"domains": [...]}

# Domain Research API
curl -X POST http://localhost:5001/api/domains/research \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'
# Ollama analyzes domain, suggests content
```

### Database Structure:

**SQLite file:** `soulfra.db`

**Tables:**
```sql
-- All your domains
brands (id, name, slug, domain, category, tier, emoji, brand_type, tagline)

-- AI conversations per domain
domain_conversations (id, brand_id, role, message, created_at, metadata)

-- Ollama suggestions per domain
domain_suggestions (id, brand_id, suggestion_type, title, description, status)
```

**Your current domains (6 in database):**
1. Test (test.com) - Technology
2. Stpetepros (stpetepros.com) - Home Services
3. Soulfra (soulfra.com) - Identity & Security
4. DeathToData (deathtodata.com) - Privacy Search
5. Calriven (calriven.com) - AI Platform
6. HowToCookAtHome (howtocookathome.com) - Cooking

### How It Works:

```
User → http://localhost:5001/admin/domains
      → Enter domain "example.com"
      → Click "Research with Ollama"
      ↓
soulfra-simple calls domain_researcher.py
      → DNS lookup (check if domain exists)
      → Fetch website HTML (scrape content)
      → Extract metadata (title, description, keywords)
      → Send to Ollama for AI analysis
      ↓
Ollama suggests:
      → Category (cooking, tech, privacy, etc.)
      → Emoji (🍳, 💻, 🔒)
      → Tagline ("Quick recipes for busy parents")
      → Target audience
      → Purpose/strategy
      ↓
User reviews suggestions → Approve → Domain added to database
```

---

## System 2: 3-Domain Auth System (Ports 8001, 5002, 5003)

### What It Is:
**QR-based authentication** across 3 domains:

```
soulfra.com (Port 8001)
    ↓ User scans QR code
soulfraapi.com (Port 5002)
    ↓ Creates account, session token
soulfra.ai (Port 5003)
    ↓ Authenticated AI chat
```

### Status: ❌ FILES EXIST, NOT RUNNING

**Files are ready in:** `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/Soulfra/`

**To start it:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/Soulfra
bash START-ALL.sh
```

**This will start:**
```
✅ soulfra.com (port 8001)        - Static landing page with QR code
✅ soulfraapi.com (port 5002)     - Account creation API (SQLite)
✅ soulfra.ai (port 5003)         - AI chat interface (Ollama)
```

### How It Works (The Triple QR Flow):

```
Step 1: User visits soulfra.com
┌─────────────────────────────┐
│  http://localhost:8001      │
│                             │
│  🧠 Soulfra                 │
│  "AI that knows you"        │
│                             │
│  [QR CODE]                  │
│  "Scan to create account"   │
└─────────────────────────────┘

Step 2: User scans QR with iPhone
QR encodes: http://localhost:5002/qr-signup?ref=landing

Soulfraapi.com receives request:
  → Creates user account (SQLite: users table)
  → Generates session token (32 random bytes)
  → Stores in sessions table (24-hour expiry)
  → Redirects to: http://localhost:5003/?session=TOKEN123

Step 3: User lands on soulfra.ai
┌─────────────────────────────┐
│  http://localhost:5003      │
│  ?session=TOKEN123          │
│                             │
│  💬 Chat Interface          │
│                             │
│  You: "Hello AI"            │
│  AI: "Hi! How can I help?"  │
└─────────────────────────────┘
```

### Database Structure (Soulfraapi.com):

**SQLite file:** `Soulfraapi.com/soulfraapi.db` (SEPARATE from main soulfra.db!)

**Tables:**
```sql
-- User accounts created via QR
users (id, username, email, created_at, ref_source, is_active)

-- Session tokens (24-hour expiry)
sessions (id, user_id, token, created_at, expires_at, device_fingerprint)
```

---

## How The Two Systems Connect (They Don't!)

**System 1 (Control Panel):** You manage domains
**System 2 (3-Domain Auth):** Users sign up and use AI

```
You (domain owner):
  → Use System 1 to manage 200+ domains
  → Research, create content, chat with Ollama per domain
  → Export static HTML sites for each domain

Your users (visitors):
  → Visit System 2 (soulfra.com landing page)
  → Scan QR to create account
  → Get AI chat access
```

**They run simultaneously, different ports, different purposes.**

---

## What You're Trying to Build Next:

Based on your questions, here's what you want:

### 1. Blogs for 3 Soulfra Domains

**Goal:** Each domain needs blog posts/content

**Current state:**
- soulfra.com has landing page (index.html) ✅
- soulfra.ai has chat interface (chat.html) ✅
- soulfraapi.com is API only (no UI) ✅

**What's missing:**
- `/blog/` folder for each domain ❌
- Blog post templates ❌
- Ollama-generated content ❌

**Plan:**
```
Soulfra.com/
├── index.html (landing page) ✅
├── style.css ✅
├── qr-code.png ✅
└── blog/  ← ADD THIS
    ├── index.html (blog homepage)
    ├── posts/
    │   ├── 2024-12-31-why-privacy-matters.html
    │   └── 2025-01-01-how-ollama-works.html
    └── style.css
```

### 2. Cringeproof Game

**Current state:**
- Files exist in `archive/experiments/` ✅
- Not integrated into main system ❌

**Plan:**
- Move to `Soulfra.com/game/cringeproof/`
- Add link from main landing page
- Make it playable standalone HTML/JS

### 3. Subscription Tiers (Free vs Paid)

**The "Open Core" Model:**

**Free Tier (Open Source):**
```
User clones: github.com/soulfra/soulfra-simple
Runs locally:
  - Domain management UI ✅
  - Ollama integration (local AI) ✅
  - Static site export ✅
  - SQLite database (local) ✅

Cost: $0/month
Limitations: Must run own Ollama, no cloud features
```

**Paid Tier (Hosted API):**
```
User pays: $5-20/month
Gets access to:
  - api.soulfra.com (hosted Ollama) 💰
  - Faster AI responses 💰
  - Advanced features (multi-model routing) 💰
  - Analytics & tracking 💰
  - Premium templates 💰

Cost: $5-20/month
Benefit: No self-hosting required
```

**HTML/JavaScript works for BOTH:**
```html
<!-- Free tier: User runs own Ollama -->
<script>
const OLLAMA_URL = "http://localhost:11434/api/generate";
</script>

<!-- Paid tier: Use api.soulfra.com -->
<script>
const OLLAMA_URL = "https://api.soulfra.com/api/generate";
const API_KEY = "user_api_key_here";
</script>
```

Same HTML, different API endpoint!

### 4. Database "Snippets" / Brands

**You asked: "how the databases are being streamed or viewed for different snippets or binary or brands"**

**Answer:** Each domain is a "brand" in the database.

```sql
-- Example: howtocookathome.com
SELECT * FROM brands WHERE slug = 'howtocookathome';

Returns:
{
  "id": 4,
  "name": "HowToCookAtHome",
  "slug": "howtocookathome",
  "domain": "howtocookathome.com",
  "category": "cooking",
  "tier": "foundation",
  "emoji": "🍳",
  "brand_type": "blog",
  "tagline": "Simple recipes for home cooks 🍳"
}

-- Get AI conversation for this brand
SELECT * FROM domain_conversations WHERE brand_id = 4;

-- Get Ollama suggestions for this brand
SELECT * FROM domain_suggestions WHERE brand_id = 4;
```

**"Snippets" = Individual records/rows in database**
**"Brands" = Domains you manage**
**"Binary" = Static HTML files exported from database**

**Workflow:**
```
1. You chat with Ollama about "howtocookathome.com"
2. Conversation saved to domain_conversations table
3. Ollama suggests: "Write article about quick breakfasts"
4. Suggestion saved to domain_suggestions table
5. You approve → Generate HTML from template
6. Export to static file: howtocookathome.com/blog/quick-breakfasts.html
7. Deploy to GitHub Pages or hosting
```

---

## Debug Mode vs Production

**You asked: "this is the debugg and whatever else right?"**

**Answer:**

**Debug mode (development):**
```python
# app.py - Current default
app.run(host='0.0.0.0', debug=True, port=5001)

What this does:
  - Interactive Python console on errors (SECURITY RISK!)
  - Full stack traces with code shown
  - Auto-reload on file changes
  - Werkzeug debugger PIN (like bank PIN)

Never use in production!
```

**Production mode (secure):**
```bash
export FLASK_ENV=production
python app.py

# Now runs:
app.run(host='0.0.0.0', debug=False, port=5001)

What this does:
  - No interactive debugger (secure)
  - Generic error pages
  - No code shown
  - No PIN needed
```

**The "debugg" you see is just Flask warning you it's in debug mode.**

---

## Summary - What Works, What Doesn't

### ✅ WORKING RIGHT NOW:

**System 1 (Port 5001):**
- `/admin/domains` - Domain management UI
- `/api/docs` - API documentation
- `/api/domains/list` - Domain list API
- `/api/domains/research` - Ollama research
- `/api/domains/create` - Create domain
- SQLite database with 6 domains
- Domain conversations with AI
- Ollama suggestions per domain

### ❌ NOT RUNNING (But Files Exist):

**System 2 (Ports 8001, 5002, 5003):**
- `Soulfra.com` - Landing page with QR
- `Soulfraapi.com` - Auth API
- `Soulfra.ai` - AI chat

**To start:** `cd Soulfra && bash START-ALL.sh`

### ❌ NOT BUILT YET:

- Blogs for 3 domains
- Cringeproof game integration
- Subscription tier implementation
- Static HTML export automation

---

## Next Steps

**1. Start the 3-domain system:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/Soulfra
bash START-ALL.sh
# Opens ports 8001, 5002, 5003
```

**2. Test the QR flow:**
```bash
# Visit landing page
open http://localhost:8001

# Simulate QR scan
curl -L http://localhost:5002/qr-signup?ref=test
# Should redirect to: http://localhost:5003/?session=TOKEN
```

**3. Build blogs:**
- Create `blog/` folders
- Use templates from main system
- Generate content with Ollama

**4. Integrate cringeproof:**
- Move from archive to active system
- Add to soulfra.com

**5. Document tiers:**
- Free vs paid features
- HTML/JavaScript examples
- API key system

---

**Bottom line:** You have a working control panel (port 5001) and a ready-to-start 3-domain system (ports 8001, 5002, 5003). The "debugg" is just Flask's development mode. Everything is MIT licensed "open core" ready to monetize via API access.
