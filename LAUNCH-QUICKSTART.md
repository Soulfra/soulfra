# Soulfra Launch Quickstart

**Created**: 2026-01-02
**Purpose**: Get from "localhost chaos" to "production deployed" in 2 hours

---

## TL;DR - What You Have & Where It Is

```
Your Mac (localhost):
├─ Flask App (port 5001)          ✅ Running (17 zombies!)
├─ Ollama (port 11434)            ✅ Running (1/4 ports)
├─ PostgreSQL (port 5432)         ✅ Running
├─ Content Tumbler                ❌ Not running (needs 4 Ollama ports)
├─ Domain Network (domains.txt)   ✅ Ready
├─ Projects (projects.txt)        ✅ Ready
├─ Affiliate System               ✅ Ready
└─ Database (soulfra.db)          ⚠️  Schema errors

Production:
└─ Nothing deployed yet! Everything is localhost only.
```

---

## Step-by-Step Launch (2 hours)

### Step 1: Diagnostic (5 minutes)

Run the diagnostic tool to see what's broken:

```bash
python3 deployment_diagnostic.py check-all
```

This shows:
- ✅ What's working
- ❌ What's broken
- ⚠️  What needs attention

---

### Step 2: Clean Up Zombies (2 minutes)

Kill all the Flask zombie processes:

```bash
python3 deployment_diagnostic.py kill-zombies
```

Wait 2 seconds, then start fresh:

```bash
python3 app.py
```

Verify it works:

```bash
curl http://localhost:5001/status
```

---

### Step 3: Fix Database (3 minutes)

Fix missing columns and schema issues:

```bash
python3 deployment_diagnostic.py fix-db
```

This adds:
- `users.role` column
- `api_usage` table
- `content_tumbles` table

---

### Step 4: Start Multi-Port Ollama (20 minutes)

Start all 4 Ollama ports for the tumbler system:

```bash
./start_tumbler_ollama.sh
```

This will:
- Start Ollama on ports 11434-11437
- Load models (llama3, mistral, codellama)
- Verify all ports are running

Check status:

```bash
./start_tumbler_ollama.sh status
```

---

### Step 5: Test Complete System (10 minutes)

Test everything works together:

```bash
# Test multi-port Ollama
python3 multi_port_ollama.py

# Test content tumbler
python3 content_tumbler.py spin --project cringeproof

# Test affiliate system
python3 debug_affiliate_system.py

# Test complete flow
python3 demo_complete_system.py
```

---

### Step 6: Deploy to Railway (30 minutes)

Get your Flask app on the public internet:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add PostgreSQL database
railway add

# Set environment variables
railway variables set BASE_URL=https://your-app.railway.app
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set FLASK_ENV=production

# Deploy
railway up

# Open in browser
railway open
```

Your app is now live at `https://your-app.railway.app`

---

### Step 7: GitHub Pages for Announcements (20 minutes)

Deploy static announcement pages:

```bash
# Build static site
python3 build.py

# Create GitHub repo (if needed)
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/soulfra.git
git push -u origin main
```

Enable GitHub Pages:
1. Go to repo Settings → Pages
2. Source: Deploy from branch `main`
3. Folder: `/` (root)
4. Save

Generate project announcements:

```bash
# Generate CringeProof announcement
python3 project_launcher.py launch cringeproof --type initial
```

Live at: `https://YOUR_USERNAME.github.io/soulfra/cringeproof`

---

### Step 8: Test in Production (10 minutes)

Verify everything works:

1. **Visit your Railway URL**: `https://your-app.railway.app`
2. **Test status endpoint**: `https://your-app.railway.app/status`
3. **Check multi-domain routing**: Works automatically
4. **Test GitHub Pages**: Visit announcement URLs

---

## Quick Commands Reference

### Diagnostic

```bash
python3 deployment_diagnostic.py check-all     # Full system check
python3 deployment_diagnostic.py check-db      # Database only
python3 deployment_diagnostic.py check-ports   # Port status
python3 deployment_diagnostic.py check-ollama  # Ollama status
```

### Fix Issues

```bash
python3 deployment_diagnostic.py kill-zombies  # Kill Flask zombies
python3 deployment_diagnostic.py fix-db        # Fix database schema
```

### Ollama

```bash
./start_tumbler_ollama.sh                      # Start all 4 ports
./start_tumbler_ollama.sh status               # Check status
./start_tumbler_ollama.sh stop                 # Stop all ports
./start_tumbler_ollama.sh restart              # Restart all
```

### Testing

```bash
python3 multi_port_ollama.py                   # Test multi-port
python3 content_tumbler.py spin --project cringeproof  # Generate content
python3 debug_affiliate_system.py              # Test affiliates
python3 demo_complete_system.py                # Test everything
```

### Deployment

```bash
railway up                                     # Deploy to Railway
railway open                                   # Open in browser
railway logs                                   # View logs
railway variables                              # Check env vars
```

---

## Where Everything Should Be

After deployment:

```
┌──────────────────────────────────────────────┐
│  PRODUCTION (Railway)                       │
│  https://soulfra.com                        │
│  - Flask app                                 │
│  - PostgreSQL database                       │
│  - Public-facing API                         │
└──────────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────────┐
│  LOCAL (Your Mac)                           │
│  http://localhost:5001                      │
│  - Ollama (4 ports)                          │
│  - Content generation                        │
│  - Development/testing                       │
└──────────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────────┐
│  GITHUB PAGES (Free)                        │
│  https://username.github.io/soulfra         │
│  - Project announcements                     │
│  - Static marketing pages                    │
└──────────────────────────────────────────────┘
```

---

## Common Issues & Fixes

### "Flask not responding"

```bash
pkill -9 -f "python3 app.py"
sleep 2
python3 app.py
```

### "Ollama connection refused"

```bash
./start_tumbler_ollama.sh restart
```

### "Database schema error"

```bash
python3 deployment_diagnostic.py fix-db
```

### "Railway deployment failed"

```bash
railway logs  # Check errors
railway variables set PORT=5001
railway up --detach
```

---

## What to Do Next

After completing all 8 steps above:

1. **Custom Domain** (optional)
   - Buy domain (soulfra.com)
   - Point to Railway
   - Configure in Railway settings

2. **GitHub Contributors**
   ```bash
   python3 contributor_rewards.py sync cringeproof
   python3 contributor_rewards.py ownership cringeproof
   ```

3. **Cross-Domain Partnerships**
   ```bash
   python3 project_launcher.py partner cringeproof deathtodata.com
   ```

4. **Generate Content**
   ```bash
   python3 content_tumbler.py spin --project cringeproof --type announcement
   python3 content_tumbler.py spin --project cringeproof --type readme
   python3 content_tumbler.py spin --project cringeproof --type blog_post
   ```

---

## Complete System Overview

You've built:

1. **Flask App** (18,434 lines!)
   - Multi-domain routing
   - Image generation
   - QR codes
   - Voice capsules
   - AI chat
   - Admin portal

2. **Content Tumbler**
   - 4-port Ollama setup
   - Parallel content generation
   - Auto-scoring
   - SHA-256 → UPC → QR tracking

3. **Domain Network**
   - 4 domains (domains.txt)
   - Tier progression system
   - GitHub star unlocking

4. **Project System**
   - 4 projects (projects.txt)
   - GitHub integration
   - Contributor rewards
   - Ownership tracking

5. **Affiliate System**
   - Referral tracking
   - Entry domain rewards (5%)
   - Direct referrer rewards (2.5%)

---

## Files Created

Diagnostic & deployment tools:

- `DEPLOYMENT-DIAGNOSTIC.md` - Complete deployment guide
- `deployment_diagnostic.py` - System diagnostic tool
- `start_tumbler_ollama.sh` - Multi-port Ollama startup
- `LAUNCH-QUICKSTART.md` - This file

Existing system files:

- `multi_port_ollama.py` - Multi-port Ollama manager
- `content_tumbler.py` - Content generation engine
- `debug_affiliate_system.py` - Affiliate flow tester
- `project_launcher.py` - Project management
- `contributor_rewards.py` - GitHub contributor tracking
- `demo_complete_system.py` - Complete system demo

---

## Time Estimate

- Diagnostic & cleanup: **10 minutes**
- Multi-port Ollama: **20 minutes**
- Testing locally: **10 minutes**
- Deploy to Railway: **30 minutes**
- GitHub Pages: **20 minutes**
- Test production: **10 minutes**
- **Total: ~2 hours**

---

## Success Criteria

You're done when:

- ✅ No Flask zombie processes
- ✅ Database schema fixed
- ✅ All 4 Ollama ports running
- ✅ Content tumbler generating
- ✅ Flask app live on Railway
- ✅ GitHub Pages deployed
- ✅ All tests passing

---

## Next Steps After Launch

1. Monitor logs: `railway logs --tail`
2. Set up automated backups
3. Add custom domain
4. Generate content for all projects
5. Invite contributors
6. Track ownership distribution
7. Scale as needed

---

**Ready? Start with Step 1!**

```bash
python3 deployment_diagnostic.py check-all
```
