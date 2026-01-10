# 🚀 Soulfra Launch Guide - From Localhost to Live

**Status:** Ready to deploy sitemap.xml and robots.txt

---

## ✅ Phase 1 Complete: Missing Files Fixed

I just created the missing files that were causing 404 errors in your "View Live" tabs:

### What Was Created

1. **`docs/sitemap.xml`** - 25+ pages indexed
   - All blog posts (Soulfra Experiment + Calriven series)
   - Documentation pages
   - Homepage, About, RSS feed
   - Tells Google what content you have

2. **`docs/robots.txt`**
   - Allows all search engines to crawl your site
   - Points to sitemap.xml
   - Ready for SEO

---

## 📋 How to Deploy (2 minutes)

These files are already in your `docs/` folder. To make them live on soulfra.com:

### Option 1: GitHub Push (Recommended)

```bash
# Add the new files
git add docs/sitemap.xml docs/robots.txt

# Commit with a message
git commit -m "Add sitemap.xml and robots.txt for SEO"

# Push to GitHub
git push origin main
```

After 1-2 minutes, the files will be live at:
- https://soulfra.com/sitemap.xml
- https://soulfra.com/robots.txt

### Option 2: Test Locally First

```bash
# Serve the docs folder locally
cd docs && python3 -m http.server 8000

# In your browser, visit:
# http://localhost:8000/sitemap.xml
# http://localhost:8000/robots.txt
```

---

## 🔍 How to Test After Deployment

### 1. From Domain Manager

1. Go to http://localhost:5001/domains
2. Click **"View Live"** on soulfra.com
3. Click the **"Sitemap"** tab → Should show XML with all pages
4. Click the **"Robots"** tab → Should show robots.txt content

### 2. Direct URLs

After you push to GitHub:
- Visit https://soulfra.com/sitemap.xml
- Visit https://soulfra.com/robots.txt

---

## 📐 Understanding Your Architecture

You asked: **"how does this all work?"**

Here's your multi-domain setup:

### The Domains

```
┌──────────────────────────────────────────────────────────┐
│                    YOUR ECOSYSTEM                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  soulfra.com (The Faucet - Identity Hub)                │
│    ├─ Distributes QR keys for authentication            │
│    ├─ Central identity management                       │
│    └─ Uses: soulfra-model (Ollama)                      │
│                                                           │
│  calriven.com (Algorithm Processing)                     │
│    ├─ Runs code execution & AI tasks                    │
│    ├─ Processes complex algorithms                      │
│    └─ Uses: codellama:7b + calos-model (Ollama)         │
│                                                           │
│  deathtodata.com (Search & Ranking)                      │
│    ├─ Content discovery engine                          │
│    ├─ SEO and page ranking                              │
│    └─ Uses: deathtodata-model (Ollama)                  │
│                                                           │
│  stpetepros.com (First Production App)                   │
│    ├─ Professional services directory                   │
│    ├─ Uses shared auth from soulfra.com                 │
│    └─ Real business application                         │
│                                                           │
│  localhost:5001 (Development Sandbox)                    │
│    └─ Domain Manager - Control everything from here     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### The "Faucet" Concept

**Soulfra = The Faucet** means:
- It's the source that distributes identity "tokens" (QR codes)
- Other domains request authentication from soulfra
- Like a water faucet distributes water to different pipes

### How Content Flows

```
You edit locally → localhost:5001
       ↓
Build with build.py → docs/ folder
       ↓
Git push → GitHub
       ↓
GitHub Pages → soulfra.com (LIVE!)
```

---

## 🤖 Ollama Models You Have

You have **21 models**, including custom ones:

### Your Custom Models
- `soulfra-model` - For soulfra.com tasks
- `calos-model` - For calriven.com algorithms
- `deathtodata-model` - For search/ranking
- `codellama:7b` - For code generation

### Next: Model Routing (Phase 3)

I can build an `/api/models/route` endpoint that:
1. Takes a domain name → routes to the right Ollama model
2. Example: Chat on calriven.com → uses codellama:7b
3. Example: Chat on soulfra.com → uses soulfra-model

---

##  How to Edit Your Live Site

**Current workflow:**

1. **Edit HTML locally** - Change files in `docs/` folder
2. **Test locally** - `cd docs && python3 -m http.server 8000`
3. **Push to GitHub** - `git add docs/ && git commit -m "update" && git push`
4. **Wait 1-2 min** - GitHub Pages rebuilds
5. **View live** - https://soulfra.com

**Better workflow (Phase 4):**

I can build a **web-based editor** in the Domain Manager where you:
- Click "Edit" on any domain
- Change content in a wysiwyg editor
- Click "Deploy" → Auto pushes to GitHub
- See changes live in 2 minutes

---

## 🔐 SSL Certificate Issue

You noticed: **"soulfra.com doesn't have ssl and soulfra.github.io does"**

### What's Happening

- `soulfra.github.io` → Has valid GitHub SSL ✅
- `soulfra.com` → Certificate doesn't match domain ❌

### Fix (Phase 5)

**Option A: GitHub Pages + Custom Domain**
1. In your GitHub repo → Settings → Pages
2. Add Custom Domain: `soulfra.com`
3. Check "Enforce HTTPS"
4. GitHub provides free SSL

**Option B: Cloudflare (Free)**
1. Point soulfra.com DNS to Cloudflare
2. Cloudflare provides free SSL
3. Better caching + CDN

---

## 🎯 What to Do Next

You have **3 options** for next steps:

### A. Deploy the Files We Just Made (5 min)

```bash
git add docs/sitemap.xml docs/robots.txt
git commit -m "Add SEO files"
git push
```

Then test in Domain Manager → View Live → Sitemap tab

### B. Build AI Model Routing (Phase 3)

Create smart routing so:
- Questions about identity → soulfra-model
- Code questions → codellama
- Search questions → deathtodata-model

I'll build `/api/models/route` endpoint.

### C. Create Edit Workflow (Phase 4)

Build web-based content editor in Domain Manager:
- Edit soulfra.com content from browser
- Auto-deploy to GitHub with one click
- No more manual git commands

---

## ❓ Your Questions Answered

### "How do I edit soulfra.com content?"

**Right now:**
Edit files in `docs/` folder → git push

**Soon (Phase 4):**
Click "Edit" in Domain Manager → Save → Auto-deploy

### "What's the Preview vs View Live difference?"

- **Preview** = Shows localhost:5001 rendering (your local test)
- **View Live** = Scrapes actual soulfra.com (production)

### "How do I get codellama working with calriven?"

**Phase 3:** I'll build model routing that maps:
```
calriven.com/chat → codellama:7b
soulfra.com/chat → soulfra-model
deathtodata.com/chat → deathtodata-model
```

### "What database am I using?"

You're using **SQLite** (file: `soulfra.db`).

To view it:
```bash
sqlite3 soulfra.db "SELECT * FROM brands;"
```

You have 5 brands: soulfra, stpetepros, deathtodata, calriven, localhost

---

## 🚦 Next Steps

Tell me which phase you want to work on:

1. **Deploy sitemap/robots** (5 minutes) - Makes "View Live" tabs work
2. **Phase 2: Architecture docs** (Explain the system better)
3. **Phase 3: AI model routing** (codellama → calriven, etc.)
4. **Phase 4: Web editor** (Edit content from Domain Manager)
5. **Phase 5: Fix SSL** (Make soulfra.com secure)

Which one do you want to tackle first?
