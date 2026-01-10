# Soulfra System Map - Current State

**Created**: 2026-01-02
**Status**: Everything localhost, ready to deploy

---

## Current Infrastructure (Localhost)

```
┌─────────────────────────────────────────────────────────────────────┐
│  YOUR MAC: 192.168.1.87                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  FLASK APP (Port 5001)                              │         │
│  │  Status: ✅ Running (17 zombie processes!)           │         │
│  │  Access: http://localhost:5001                       │         │
│  │          http://192.168.1.87:5001 (LAN)             │         │
│  │                                                      │         │
│  │  Features:                                           │         │
│  │  • Multi-domain routing (soulfra, stpetepros, etc.) │         │
│  │  • Image generation & QR codes                       │         │
│  │  • Voice capsules                                    │         │
│  │  • Unified chat with Ollama                          │         │
│  │  • Status dashboard (/status)                        │         │
│  │  • Admin portal (/admin)                             │         │
│  │  • 18,434 lines of code!                            │         │
│  └──────────────────────────────────────────────────────┘         │
│                           ↕                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  DATABASE (soulfra.db)                              │         │
│  │  Type: SQLite                                        │         │
│  │  Status: ⚠️  Schema errors (users.role missing)      │         │
│  │  Fix: python3 deployment_diagnostic.py fix-db        │         │
│  └──────────────────────────────────────────────────────┘         │
│                           ↕                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  OLLAMA (Multi-Port AI)                             │         │
│  │                                                      │         │
│  │  Port 11434 (Technical)    ✅ RUNNING - llama3      │         │
│  │  Port 11435 (Creative)     ❌ NOT STARTED            │         │
│  │  Port 11436 (Precise)      ❌ NOT STARTED            │         │
│  │  Port 11437 (Experimental) ❌ NOT STARTED            │         │
│  │                                                      │         │
│  │  Status: 1/4 ports running                           │         │
│  │  Fix: ./start_tumbler_ollama.sh                      │         │
│  └──────────────────────────────────────────────────────┘         │
│                           ↕                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  CONTENT TUMBLER                                    │         │
│  │  Status: ❌ Not running (needs 4 Ollama ports)       │         │
│  │                                                      │         │
│  │  Files:                                              │         │
│  │  • multi_port_ollama.py (411 lines)                 │         │
│  │  • content_tumbler.py (main engine)                 │         │
│  │                                                      │         │
│  │  What it does:                                       │         │
│  │  • Spins 4 AI models in parallel                    │         │
│  │  • Scores each variation                            │         │
│  │  • Picks best result                                │         │
│  │  • Generates SHA-256 → UPC → QR codes               │         │
│  └──────────────────────────────────────────────────────┘         │
│                           ↕                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  DOMAIN & PROJECT NETWORK                           │         │
│  │                                                      │         │
│  │  domains.txt (4 domains):                            │         │
│  │  • soulfra.com          (tech, Tier 0)              │         │
│  │  • deathtodata.com      (privacy, Tier 1)           │         │
│  │  • calriven.com         (tech, Tier 1)              │         │
│  │  • howtocookathome.com  (cooking, Tier 2)           │         │
│  │                                                      │         │
│  │  projects.txt (4 projects):                          │         │
│  │  • CringeProof          (soulfra.com)               │         │
│  │  • Data Privacy Toolkit (deathtodata.com)           │         │
│  │  • Code Quality Analyzer (calriven.com)             │         │
│  │  • Recipe Generator     (howtocookathome.com)       │         │
│  └──────────────────────────────────────────────────────┘         │
│                           ↕                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  AFFILIATE & CONTRIBUTOR SYSTEMS                    │         │
│  │                                                      │         │
│  │  Files:                                              │         │
│  │  • debug_affiliate_system.py (359 lines)            │         │
│  │  • contributor_rewards.py                            │         │
│  │  • project_launcher.py                               │         │
│  │                                                      │         │
│  │  Features:                                           │         │
│  │  • GitHub star tracking                             │         │
│  │  • Tier progression (0-4)                           │         │
│  │  • Referral rewards (5% + 2.5%)                     │         │
│  │  • Ownership tracking                               │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  OTHER SERVICES                                     │         │
│  │                                                      │         │
│  │  Port 3000  - Node.js (unknown)      ✅ Running     │         │
│  │  Port 5000  - Control Center         ✅ Running     │         │
│  │  Port 5432  - PostgreSQL             ✅ Running     │         │
│  │  Port 7000  - Control Center         ✅ Running     │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Production Infrastructure (Not Yet Deployed)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PRODUCTION (Railway/Vercel/VPS)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ❌ NOT DEPLOYED YET                                                │
│                                                                     │
│  You have configs ready for:                                        │
│  • Railway (railway.json, railway.toml, Procfile)                  │
│  • Vercel (vercel.json)                                            │
│  • Docker (Dockerfile, docker-compose.yml)                         │
│  • Heroku (Procfile)                                               │
│                                                                     │
│  To deploy: See LAUNCH-QUICKSTART.md                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Complete Data Flow

```
┌────────────────┐
│  USER REQUEST  │
└────────┬───────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  FLASK APP (port 5001)                         │
│  • Receives request                             │
│  • Routes by subdomain/domain                   │
│  • Checks tier (GitHub stars)                   │
└────────┬────────────────────────────────────────┘
         │
         ├─────────────────┬─────────────────┬─────────────────┐
         ▼                 ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  DATABASE   │   │   OLLAMA    │   │  GENERATOR  │   │  AFFILIATES │
│  soulfra.db │   │  (4 ports)  │   │  SHA→UPC→QR │   │  Tracking   │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  RESPONSE       │
                            │  • Content      │
                            │  • Tracking     │
                            │  • Attribution  │
                            └─────────────────┘
```

---

## Content Tumbler Flow (When All 4 Ports Running)

```
┌──────────────────────────────────────────────────────────┐
│  TUMBLER REQUEST                                        │
│  python3 content_tumbler.py spin --project cringeproof  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  CHECK USER TIER                                        │
│  • Tier 0: 1 port  (11434 only)                         │
│  • Tier 1: 2 ports (11434-11435)                        │
│  • Tier 2: 3 ports (11434-11436)                        │
│  • Tier 3: 4 ports (11434-11437) FULL TUMBLER!          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  SPIN THE TUMBLER (Parallel Generation)                │
│                                                          │
│  Port 11434 →  llama3    (temp 0.7) →  Technical       │
│  Port 11435 →  mistral   (temp 0.9) →  Creative        │
│  Port 11436 →  codellama (temp 0.5) →  Precise         │
│  Port 11437 →  llama3    (temp 1.2) →  Experimental    │
│                                                          │
│  All generate SIMULTANEOUSLY using ThreadPoolExecutor   │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  SCORE EACH VARIATION                                   │
│  • Length (200-1000 chars ideal)                        │
│  • Readability (sentences, paragraphs)                  │
│  • Markdown formatting                                   │
│  • Code blocks                                           │
│  • Lists                                                 │
│  Score: 0-100                                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PICK WINNER (Highest Score)                           │
│  Example: Port 11435 (mistral) - Score 87/100           │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  GENERATE TRACKING CODES                                │
│  content → SHA-256 → UPC → QR code                      │
│  • SHA-256: a3c7f9e8d2b1...                             │
│  • UPC: 123456789012                                     │
│  • QR: https://soulfra.com/tumble/xYz123                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  SAVE TO DATABASE                                       │
│  content_tumbles table:                                  │
│  • project_slug                                          │
│  • best_port, best_model, best_score                    │
│  • best_content                                          │
│  • tracking_codes (SHA, UPC, QR)                        │
│  • all_results (for comparison)                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  OPTIONAL: DEPLOY TO GITHUB PAGES                      │
│  • Generate HTML page                                    │
│  • Push to repo                                          │
│  • Live at: soulfra.github.io/soulfra/cringeproof       │
└──────────────────────────────────────────────────────────┘
```

---

## Problems Blocking Production Launch

### Critical (Must Fix)

1. **17 Flask Zombie Processes**
   - **Fix**: `python3 deployment_diagnostic.py kill-zombies`
   - **Then**: `python3 app.py` (clean start)

2. **Database Schema Errors**
   - Missing: `users.role` column
   - Missing: `api_usage` table
   - **Fix**: `python3 deployment_diagnostic.py fix-db`

3. **Multi-Port Ollama Not Running**
   - Only 1/4 ports active
   - **Fix**: `./start_tumbler_ollama.sh`

4. **Not Deployed to Production**
   - Everything localhost only
   - **Fix**: `railway up` (see LAUNCH-QUICKSTART.md)

### Non-Critical (Can Wait)

5. **No GitHub Pages Deployment**
   - Announcement pages not live
   - **Fix**: `python3 build.py` + enable GitHub Pages

6. **Environment Variables**
   - Using dev defaults
   - **Fix**: Set production env vars in Railway

---

## Available Commands (Quick Reference)

### Diagnostic
```bash
python3 deployment_diagnostic.py check-all
python3 deployment_diagnostic.py check-db
python3 deployment_diagnostic.py check-ports
python3 deployment_diagnostic.py check-ollama
```

### Fix
```bash
python3 deployment_diagnostic.py kill-zombies
python3 deployment_diagnostic.py fix-db
```

### Ollama
```bash
./start_tumbler_ollama.sh           # Start all 4 ports
./start_tumbler_ollama.sh status    # Check status
./start_tumbler_ollama.sh stop      # Stop all
```

### Testing
```bash
python3 multi_port_ollama.py
python3 content_tumbler.py spin --project cringeproof
python3 debug_affiliate_system.py
python3 demo_complete_system.py
```

### Deployment
```bash
railway up                          # Deploy to Railway
railway open                        # Open in browser
railway logs                        # View logs
```

---

## Next Steps (In Order)

1. ✅ **Read this document** - Understand current state
2. ⏳ **Run diagnostic** - `python3 deployment_diagnostic.py check-all`
3. ⏳ **Kill zombies** - `python3 deployment_diagnostic.py kill-zombies`
4. ⏳ **Fix database** - `python3 deployment_diagnostic.py fix-db`
5. ⏳ **Start Ollama** - `./start_tumbler_ollama.sh`
6. ⏳ **Test locally** - Run all test scripts
7. ⏳ **Deploy Railway** - `railway up`
8. ⏳ **Deploy GitHub Pages** - Enable in repo settings
9. ✅ **Launch complete!**

---

## Files Created Today

**Diagnostic & Launch Tools:**
- `DEPLOYMENT-DIAGNOSTIC.md` - Complete deployment guide (comprehensive)
- `deployment_diagnostic.py` - System diagnostic tool (automated checks)
- `start_tumbler_ollama.sh` - Multi-port Ollama startup script
- `LAUNCH-QUICKSTART.md` - Quick launch guide (2 hours to production)
- `SYSTEM-MAP-CURRENT.md` - This file (visual overview)

**Previously Created:**
- `TUMBLER-VISION.md` - Complete tumbler system documentation
- `CRINGEPROOF-LAUNCH-PLAN.md` - CringeProof project launch plan
- `multi_port_ollama.py` - Multi-port Ollama manager
- `content_tumbler.py` - Content generation engine
- `debug_affiliate_system.py` - Affiliate system tester
- `project_launcher.py` - Project management
- `contributor_rewards.py` - GitHub contributor tracking
- `demo_complete_system.py` - Complete system demo

---

## Summary

**Current State**: Everything working on localhost, but not deployed

**Blocking Issues**:
- 17 Flask zombies
- Database schema errors
- Only 1/4 Ollama ports running
- Not deployed to production

**Time to Fix**: ~2 hours following LAUNCH-QUICKSTART.md

**End State**: Production-ready Soulfra platform live on the internet

---

**Start Here**: `python3 deployment_diagnostic.py check-all`
