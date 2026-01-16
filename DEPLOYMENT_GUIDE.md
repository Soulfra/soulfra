# Left On Read By God - Deployment Guide

## 🎯 What You Have

**Working Locally:**
- Daily quote generator (Ollama AI)
- Newsletter signup (email collection)
- Flask backend (APIs for quotes + signups)
- SQLite database (subscribers + quotes)

**Current Status:** Everything works on YOUR laptop at `localhost:5001`

**Goal:** Make it work for EVERYONE on the internet

---

## 📦 Your Infrastructure (Already Built!)

You already have `workspace/` folders for dev → staging → prod workflow!

Files ready to deploy:
- `workspace/staging/leftonreadbygod/index.html` - Daily quote PWA
- `quote_routes.py` - Quote API
- `newsletter_routes.py` - Newsletter API
- `newsletter_test_server.py` - Flask server

---

## 🚀 Simplest Deployment (15 minutes)

### Step 1: Deploy Frontend to GitHub Pages

```bash
# Copy production file to deployed-domains
mkdir -p deployed-domains/leftonreadbygod
cp workspace/staging/leftonreadbygod/index.html deployed-domains/leftonreadbygod/

# Create GitHub repo
cd deployed-domains/leftonreadbygod/
git init
git add index.html
git commit -m "Daily Quote PWA for leftonreadbygod.com"

# Push to GitHub (create repo at github.com first)
git remote add origin git@github.com:Soulfra/leftonreadbygod.git
git branch -M main
git push -u origin main

# Enable GitHub Pages in repo settings
# → Settings → Pages → Source: main branch → Save
```

**Result:** Site live at `https://soulfra.github.io/leftonreadbygod/`

### Step 2: Deploy Backend to Render.com

```bash
# Create render.yaml in project root
cat > render.yaml <<EOF
services:
  - type: web
    name: leftonreadbygod-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn newsletter_test_server:app"
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.0
EOF

# Make sure requirements.txt exists
pip freeze > requirements.txt

# Push to GitHub
git add render.yaml requirements.txt
git commit -m "Add Render deployment config"
git push

# Go to render.com
# → New Web Service
# → Connect GitHub repo
# → Deploy
```

**Result:** API live at `https://leftonreadbygod-api.onrender.com`

### Step 3: Update Frontend API URL

```bash
# Edit deployed-domains/leftonreadbygod/index.html
# Change this line:
#   const API_BASE = ... 'https://soulfra-api.onrender.com'
# To:
#   const API_BASE = ... 'https://leftonreadbygod-api.onrender.com'

# Push update
cd deployed-domains/leftonreadbygod/
git add index.html
git commit -m "Update API endpoint"
git push
```

### Done! Test it:
Visit `https://soulfra.github.io/leftonreadbygod/`

---

## 🎨 What Is a PWA?

**Progressive Web App = Website That Acts Like an App**

- Visit in mobile browser
- Click "Add to Home Screen"
- Now it's an app icon on your phone
- Opens without browser UI (looks native)
- **No App Store submission needed**

Users get an app-like experience without you paying $99/year to Apple!

---

## ❓ FAQs

**Q: What about React Native/Capacitor?**
A: You don't need them yet. PWA works on phones. Add later if you want App Store presence.

**Q: Custom domain?**
A: GitHub Pages is free at `soulfra.github.io/leftonreadbygod/`. Can add `leftonreadbygod.com` later.

**Q: How much does this cost?**
A: **$0/month** (GitHub Pages free + Render free tier)

**Q: Where's the database?**
A: SQLite lives on Render server. Upgrade to PostgreSQL if you scale.

---

## ✅ Summary

You're deploying a **Progressive Web App** with:
- Frontend on GitHub Pages (free)
- Backend on Render (free)
- Works on phones & desktop
- Users can "Add to Home Screen"
- No app store bullshit

The infrastructure you already built (`workspace/`, `deployed-domains/`) was set up for exactly this!
