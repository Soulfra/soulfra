# Soulfra Deployment Diagnostic & Launch Guide

**Created**: 2026-01-02
**Purpose**: Map current infrastructure and provide clear path to production deployment

---

## Current Infrastructure Map

### Services Running Locally

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR MAC (Local Development)                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Port 11434  →  Ollama (AI)              ✅ ALIVE          │
│  Port 5001   →  Flask App (main)         ✅ RUNNING*       │
│  Port 5432   →  PostgreSQL               ✅ RUNNING        │
│  Port 3000   →  Node.js (unknown)        ✅ RUNNING        │
│  Port 5000   →  Control Center           ✅ RUNNING        │
│  Port 7000   →  Control Center           ✅ RUNNING        │
│                                                             │
│  *WARNING: 17+ Flask zombie processes detected!            │
│                                                             │
│  Network Access:                                            │
│  - Localhost:      http://127.0.0.1:5001                   │
│  - LAN:           http://192.168.1.87:5001                 │
│  - Public:        ❌ NOT DEPLOYED                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What's NOT Running (But Configured)

You have deployment configs for:
- ✅ **Railway** (`railway.json`, `railway.toml`, `Procfile`)
- ✅ **Vercel** (`vercel.json`)
- ✅ **Docker** (`Dockerfile`, `docker-compose.yml`)
- ✅ **Heroku** (`Procfile`)

**Status**: NONE are deployed to production! Everything is localhost only.

---

## The Complete System You Built

### 1. Flask App (Main Platform)
- **Location**: `app.py` (18,434 lines!)
- **Port**: 5001
- **Features**:
  - Multi-domain routing (soulfra, stpetepros, etc.)
  - Image generation & QR codes
  - Voice capsules
  - Unified chat with Ollama
  - Status dashboard at `/status`
  - Admin portal at `/admin`

### 2. Ollama (AI Generation)
- **Location**: Port 11434 (default)
- **Status**: ✅ Running
- **Models**: You have models loaded
- **Multi-Port Setup**: Ports 11435-11437 NOT started yet

### 3. Content Tumbler System
- **Location**: `content_tumbler.py`, `multi_port_ollama.py`
- **Purpose**: Generate content variations across 4 AI models
- **Status**: ❌ Not running (needs 4 Ollama instances)

### 4. Domain/Project Network
- **Domains**: `domains.txt` (4 domains)
- **Projects**: `projects.txt` (4 projects)
- **GitHub Faucet**: Tier-based access system
- **Affiliates**: Referral tracking system

### 5. Database
- **Type**: SQLite (`soulfra.db`)
- **Location**: Working directory
- **Size**: Unknown (check with diagnostic)
- **Issues**: Missing columns (`role`, `tokens_used`)

---

## Problems Preventing Production Launch

### Critical Issues

1. **17+ Zombie Flask Processes**
   - Multiple background processes running
   - Consuming resources
   - Potential port conflicts
   - **Fix**: Kill all and start clean

2. **Database Schema Errors**
   - Missing `users.role` column
   - Missing `tokens_used` tracking
   - Some admin routes failing
   - **Fix**: Run schema migration

3. **No Public Deployment**
   - Everything on localhost only
   - Not accessible from internet
   - **Fix**: Deploy to Railway/Vercel/VPS

4. **Multi-Port Ollama Not Started**
   - Only port 11434 running
   - Tumbler system needs 4 ports
   - **Fix**: Start 3 additional instances

### Non-Critical Issues

5. **Environment Variables**
   - Using dev defaults
   - No production secrets set
   - **Fix**: Configure `.env` file

6. **Static Build**
   - No GitHub Pages deployment yet
   - CringeProof announcement page not live
   - **Fix**: Run `build.py` and deploy to GitHub Pages

---

## Where Everything Should Be Hosted

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PRODUCTION ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. MAIN APP (Flask)                                        │
│     Platform: Railway or VPS                                │
│     URL:      https://soulfra.com                          │
│     Purpose:  Main platform + API                          │
│                                                             │
│  2. STATIC SITES (GitHub Pages)                            │
│     Platform: GitHub Pages                                  │
│     URLs:     https://soulfra.github.io/soulfra/           │
│               https://soulfra.github.io/soulfra/cringeproof│
│     Purpose:  Announcements, marketing pages               │
│                                                             │
│  3. AI/OLLAMA                                              │
│     Platform: VPS or local (keep localhost)                │
│     Ports:    11434-11437                                  │
│     Purpose:  Content generation (tumbler)                 │
│                                                             │
│  4. DATABASE                                                │
│     Platform: Railway PostgreSQL or local SQLite           │
│     Purpose:  Main data storage                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Options Comparison

| Platform | Best For | Cost | Setup Time | Your Config |
|----------|----------|------|------------|-------------|
| **Railway** | Full Flask app + DB | Free tier → $5/mo | 10 min | ✅ Ready |
| **Vercel** | Static sites only | Free | 5 min | ✅ Ready |
| **Heroku** | Full app (legacy) | $5-7/mo | 15 min | ✅ Ready |
| **VPS (DigitalOcean)** | Full control | $6-12/mo | 1-2 hours | ⚠️ Need nginx config |
| **GitHub Pages** | Static only (free) | Free | 5 min | ⚠️ Need build |
| **Docker** | Any platform | Varies | 20 min | ✅ Ready |

---

## Launch Strategy (Step-by-Step)

### Phase 1: Clean Up Local Environment (15 minutes)

**Goal**: Get localhost working perfectly before deploying

1. **Kill Zombie Processes**
   ```bash
   # Kill all Flask processes
   pkill -9 -f "python3 app.py"

   # Verify they're gone
   ps aux | grep -E "(flask|python3 app)" | grep -v grep
   ```

2. **Fix Database Schema**
   ```bash
   # Run diagnostic
   python3 deployment_diagnostic.py check-db

   # Fix missing columns
   python3 deployment_diagnostic.py fix-db
   ```

3. **Start Fresh Flask Instance**
   ```bash
   # Start clean
   python3 app.py

   # Test it works
   curl http://localhost:5001/status
   ```

4. **Test Core Features**
   - Visit http://localhost:5001/
   - Test multi-domain routing
   - Verify Ollama connection
   - Check database connectivity

---

### Phase 2: Deploy to Railway (30 minutes)

**Goal**: Get Soulfra live on public internet

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Create Railway Project**
   ```bash
   railway init
   railway add  # Add PostgreSQL database
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set BASE_URL=https://your-app.railway.app
   railway variables set SECRET_KEY=$(openssl rand -hex 32)
   railway variables set FLASK_ENV=production
   ```

4. **Deploy**
   ```bash
   railway up
   railway open
   ```

5. **Verify Deployment**
   - Visit your Railway URL
   - Check logs: `railway logs`
   - Test `/status` endpoint

---

### Phase 3: GitHub Pages for Announcements (20 minutes)

**Goal**: Deploy static announcement pages for projects

1. **Build Static Site**
   ```bash
   python3 build.py
   ```

2. **Create GitHub Repo (if needed)**
   ```bash
   # Create repo at github.com/your-username/soulfra
   git init
   git add .
   git commit -m "Initial Soulfra static site"
   git branch -M main
   git remote add origin https://github.com/your-username/soulfra.git
   git push -u origin main
   ```

3. **Enable GitHub Pages**
   - Go to repo Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/` (root) or `/docs` if you built there
   - Save

4. **Create Project Announcements**
   ```bash
   # Generate CringeProof announcement
   python3 project_launcher.py launch cringeproof --type initial

   # This creates: /soulfra/cringeproof/index.html
   # Live at: https://your-username.github.io/soulfra/cringeproof
   ```

---

### Phase 4: Multi-Port Ollama (Tumbler System) (30 minutes)

**Goal**: Run 4 Ollama instances for content tumbler

1. **Start Additional Ollama Instances**
   ```bash
   # Port 11435 (Creative)
   OLLAMA_HOST=0.0.0.0:11435 ollama serve &

   # Port 11436 (Precise)
   OLLAMA_HOST=0.0.0.0:11436 ollama serve &

   # Port 11437 (Experimental)
   OLLAMA_HOST=0.0.0.0:11437 ollama serve &
   ```

2. **Load Models on Each Port**
   ```bash
   # Default port (11434) already has llama3

   # Load mistral on 11435
   OLLAMA_HOST=http://localhost:11435 ollama pull mistral

   # Load codellama on 11436
   OLLAMA_HOST=http://localhost:11436 ollama pull codellama

   # Load llama3 on 11437 (for high-temp experiments)
   OLLAMA_HOST=http://localhost:11437 ollama pull llama3
   ```

3. **Test Multi-Port Setup**
   ```bash
   # Check all ports alive
   python3 multi_port_ollama.py
   ```

4. **Run Content Tumbler**
   ```bash
   # Generate announcement for CringeProof
   python3 content_tumbler.py spin --project cringeproof
   ```

---

### Phase 5: Full System Integration (20 minutes)

**Goal**: Connect all pieces together

1. **Test Complete Flow**
   ```bash
   # Run complete system demo
   python3 demo_complete_system.py
   ```

2. **Test Affiliate System**
   ```bash
   # Debug affiliate flow
   python3 debug_affiliate_system.py
   ```

3. **Sync GitHub Contributors**
   ```bash
   # Sync contributors from GitHub
   python3 contributor_rewards.py sync cringeproof

   # View ownership distribution
   python3 contributor_rewards.py ownership cringeproof
   ```

4. **Create Cross-Domain Partnerships**
   ```bash
   # Partner CringeProof with DeathToData
   python3 project_launcher.py partner cringeproof deathtodata.com --type promotion
   ```

---

## Production Launch Checklist

### Pre-Launch

- [ ] Kill all zombie Flask processes
- [ ] Fix database schema errors
- [ ] Set production environment variables
- [ ] Test localhost thoroughly
- [ ] Backup database (`cp soulfra.db soulfra-backup-$(date +%Y%m%d).db`)

### Deployment

- [ ] Deploy Flask app to Railway/VPS
- [ ] Configure custom domain (soulfra.com)
- [ ] Enable SSL/HTTPS
- [ ] Deploy static site to GitHub Pages
- [ ] Test all routes in production

### Post-Launch

- [ ] Monitor logs for errors
- [ ] Test multi-domain routing
- [ ] Verify Ollama connectivity
- [ ] Test affiliate tracking
- [ ] Run content tumbler generation

### Ongoing

- [ ] Set up automated backups
- [ ] Monitor disk usage
- [ ] Track error rates
- [ ] Scale if needed

---

## Commands Reference

### Diagnostic Commands

```bash
# Check what's running
lsof -i -P | grep LISTEN

# Check Flask processes
ps aux | grep "python3 app.py"

# Test Flask
curl http://localhost:5001/status

# Check Ollama
curl http://localhost:11434/api/tags

# Check database size
ls -lh soulfra.db
```

### Cleanup Commands

```bash
# Kill all Flask
pkill -9 -f "python3 app.py"

# Kill all Ollama
pkill -9 ollama

# Fresh start
python3 app.py
```

### Testing Commands

```bash
# Test multi-port Ollama
python3 multi_port_ollama.py

# Test content tumbler
python3 content_tumbler.py spin --project cringeproof

# Test affiliate system
python3 debug_affiliate_system.py

# Test complete system
python3 demo_complete_system.py
```

---

## What to Deploy Where

### Keep Local (Localhost)

- ✅ **Ollama (AI models)** - Too resource-intensive for cloud
- ✅ **Development database** - Use for testing
- ✅ **Testing scripts** - Run locally

### Deploy to Cloud

- ✅ **Flask app** → Railway/Heroku/VPS
- ✅ **Production database** → Railway PostgreSQL or managed DB
- ✅ **Static sites** → GitHub Pages
- ✅ **CDN assets** → Cloudflare/CDN (optional)

### Hybrid Approach (Recommended)

```
┌─────────────────────────────────────────────┐
│  CLOUD (Railway)                           │
│  - Flask app (public-facing)               │
│  - PostgreSQL database                      │
│  - Domain: soulfra.com                     │
└─────────────────────────────────────────────┘
              ↕ API calls
┌─────────────────────────────────────────────┐
│  LOCAL (Your Mac)                          │
│  - Ollama (4 ports for tumbler)            │
│  - Content generation                       │
│  - Testing/development                      │
└─────────────────────────────────────────────┘
              ↕ Webhooks/API
┌─────────────────────────────────────────────┐
│  GITHUB PAGES (Free)                       │
│  - Project announcements                    │
│  - Static landing pages                     │
│  - Marketing content                        │
└─────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Flask not responding on localhost:5001"

**Cause**: Zombie processes or port conflict

**Fix**:
```bash
pkill -9 -f "python3 app.py"
lsof -ti:5001 | xargs kill -9
sleep 2
python3 app.py
```

### "Ollama connection refused"

**Cause**: Ollama not running

**Fix**:
```bash
ollama serve  # Start default port 11434
# Or for multi-port:
OLLAMA_HOST=0.0.0.0:11435 ollama serve &
```

### "Database schema error (missing column)"

**Cause**: Database out of sync with code

**Fix**:
```bash
python3 deployment_diagnostic.py fix-db
# Or manually:
sqlite3 soulfra.db "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'"
```

### "Railway deployment failed"

**Cause**: Missing environment variables or build error

**Fix**:
```bash
railway logs  # Check error logs
railway variables  # Verify env vars
# Common fix:
railway variables set PORT=5001
railway up --detach
```

---

## Summary: Where Everything Lives

**Current State**:
- Everything on localhost
- 17+ zombie Flask processes
- Only 1 Ollama port running
- Database schema errors
- Not deployed to public internet

**Target State**:
- Flask app on Railway (public)
- Static sites on GitHub Pages
- Ollama on localhost (4 ports)
- Clean database with proper schema
- All systems integrated and working

**Next Steps**:
1. Run `deployment_diagnostic.py` (I'll create this next)
2. Kill zombies and clean up
3. Deploy to Railway
4. Set up GitHub Pages
5. Start multi-port Ollama
6. Test complete system

**Estimated Time**: 2-3 hours total
