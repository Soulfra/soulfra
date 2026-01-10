# Multi-Domain Platform - Quick Start

## TL;DR
You now have a visual admin interface to manage all your domains from one place. Input domains, deploy them instantly, and manage everything from `localhost:5001/admin/domains`.

## What Just Got Built

### 1. Visual Admin UI (Your Main Interface)
```
http://localhost:5001/admin/domains
```

**What you can do:**
- ✅ Add new domains (manual or AI-assisted with Ollama)
- ✅ Click "🚀 Deploy" to create full site from CringeProof template
- ✅ Click "📊 Status" to check deployment status
- ✅ Edit domain colors, tagline, category
- ✅ Delete domains
- ✅ Bulk import from CSV

### 2. Database Admin (Data Management)
```
http://localhost:5001/admin/database
```

**What you can do:**
- ✅ View all 9 domains in database
- ✅ Export to CSV (for mailing lists, backups)
- ✅ Run SQL queries
- ✅ Export email lists

### 3. Deployment System (Behind the Scenes)

**What it does when you click "Deploy":**
1. Reads domain from database (colors, name, tagline)
2. Copies all 41 files from `voice-archive/` (CringeProof template)
3. Generates custom `config.js` with your branding
4. Generates custom `theme.css` from your colors
5. Creates everything in `deployed-domains/<slug>/`
6. Optionally pushes to GitHub Pages

## Your 9 Domains

All in database, ready to deploy:

| Domain | Category | Status | Colors |
|--------|----------|--------|--------|
| soulfra.com | Identity & Security | Hub | Blue/Green/Red |
| cringeproof.com | Social | ✅ Deployed | Pink/Purple/Black |
| deathtodata.com | Privacy Search | Not deployed | Red/Orange |
| calriven.com | AI Platform | Not deployed | Purple/Blue |
| howtocookathome.com | Cooking | Not deployed | Orange/Red |
| stpetepros.com | Home Services | Not deployed | - |
| hollowtown.com | Gaming | Not deployed | Brown/Orange |
| oofbox.com | Gaming | Not deployed | Brown/Orange |
| niceleak.com | Gaming | Not deployed | Dark/Pink |

## How to Use

### Option 1: Visual UI (Easiest)

1. **Start Flask:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 app.py
   ```

2. **Open Admin:**
   ```
   http://localhost:5001/admin/domains
   ```

3. **Deploy a Domain:**
   - Find domain in table
   - Click "🚀 Deploy"
   - Confirm popup
   - Wait 5-10 seconds
   - See success message with file count
   - Optionally deploy to GitHub Pages

4. **Check Status:**
   - Click "📊 Status"
   - See deployment info:
     - ✅ Deployed Locally
     - ✅ Has Git Repo
     - ✅ GitHub Pages Live
     - ✅ Backend Accessible

### Option 2: Command Line

```bash
# Deploy one domain
python3 domain_deployer.py cringeproof

# Deploy all domains
for domain in soulfra deathtodata calriven howtocookathome stpetepros hollowtown oofbox niceleak; do
  python3 domain_deployer.py $domain
done

# Check status
python3 domain_deployer.py cringeproof --status

# Deploy to GitHub
python3 domain_deployer.py cringeproof --github
```

### Option 3: API

```bash
# Deploy via API
curl -X POST http://localhost:5001/api/domains/cringeproof/deploy \
  -H "Content-Type: application/json" \
  -d '{}'

# Check status
curl http://localhost:5001/api/domains/cringeproof/status
```

## What Gets Created

When you deploy `cringeproof`:

```
deployed-domains/cringeproof/
├── config.js              # Auto-generated with branding
├── theme.css              # Auto-generated from DB colors
├── manifest.json          # PWA manifest
├── index.html             # Landing page
├── record-simple.html     # Voice recorder
├── wordmap.html           # Wordmap viz
├── wall.html              # Voice wall
├── screenshot.html        # OCR extractor
├── login.html             # OAuth login
├── account.html           # User account
└── ... (31 more files)
```

**Total: 41 files per domain**

## Architecture Flow

```
YOU
 │
 ├─► Input domain at http://localhost:5001/admin/domains
 │
 ├─► Ollama suggests category/tagline/colors (optional)
 │
 ├─► Click "Save" → Stores in soulfra.db
 │
 ├─► Click "🚀 Deploy"
 │      │
 │      ├─► Reads from database
 │      ├─► Copies voice-archive/* template
 │      ├─► Generates config.js with branding
 │      ├─► Generates theme.css from colors
 │      └─► Creates deployed-domains/<slug>/
 │
 └─► Optionally: Deploy to GitHub Pages
       │
       ├─► git init in deployed folder
       ├─► gh repo create <slug>-site
       ├─► git push to GitHub
       └─► Enables Pages → https://soulfra.github.io/<slug>-site
```

## Backend Setup (Optional)

Your domains need a backend to process voice memos. Three options:

### Option A: Keep Laptop Running (Free)
- Flask runs on `localhost:5001`
- Laptop online = works, laptop offline = queued
- Already set up via `connection-monitor.js` + `queue-manager.js`

### Option B: Tailscale Funnel (Free, Permanent URL)
```bash
brew install tailscale
sudo tailscale up
tailscale funnel --bg --https=443 https://localhost:5001

# Gives you: https://your-laptop.tailscale-funnel.com
```

Update deployments:
```bash
python3 domain_deployer.py cringeproof \
  --backend-url https://your-laptop.tailscale-funnel.com
```

### Option C: VPS ($4/mo, 24/7 uptime)
- Railway.app or Render.com
- You already have `.github/workflows/deploy.yml` set up
- Push to GitHub → auto-deploys to VPS

## Files You Have

**Management:**
- `domain-manager.py` - CLI for managing domains
- `domain_deployer.py` - Deployment engine
- `domains.json` - Exported manifest
- `DOMAIN-DEPLOYMENT-SYSTEM.md` - Full documentation

**Database:**
- `soulfra.db` - All 9 domains stored here
- Table: `brands` (9 rows)

**Template:**
- `voice-archive/` - CringeProof template (41 files)

**Output:**
- `deployed-domains/` - All deployed sites
  - `cringeproof/` - ✅ Deployed (41 files)
  - (8 more ready to deploy)

## Next Steps

### 1. Deploy All 9 Domains Locally
```bash
for domain in soulfra deathtodata calriven howtocookathome stpetepros hollowtown oofbox niceleak; do
  echo "Deploying $domain..."
  python3 domain_deployer.py $domain
done
```

### 2. Choose Backend Option
- Keep laptop running (free)
- Tailscale Funnel (free, permanent)
- VPS ($ 4/mo, 24/7)

### 3. Deploy to GitHub Pages
```bash
for domain in cringeproof soulfra deathtodata calriven; do
  python3 domain_deployer.py $domain --github
done
```

### 4. Set Up Custom Domains
For each domain:
1. GitHub repo settings → Pages → Custom domain
2. Add CNAME in DNS: `CNAME @ soulfra.github.io.`
3. Wait 5-10 minutes for SSL
4. Visit `https://yourdomain.com`

## Common Tasks

### Add New Domain
```bash
# Open admin
open http://localhost:5001/admin/domains

# Enter domain → Ollama suggests → Save → Deploy
```

### Bulk Import Domains
```bash
# Create CSV:
# name,domain,category,tier,emoji,brand_type,tagline

# Upload via:
open http://localhost:5001/admin/domains
# → CSV Import section
```

### Check All Domain Statuses
```bash
python3 domain-manager.py status
```

### Verify Domain Ownership
1. Add DNS TXT record: `_soulfra-verification = <slug>`
2. Run:
   ```bash
   python3 domain-manager.py verify <slug>
   ```

### Export All Domains
```bash
python3 domain-manager.py export domains.json
```

## Troubleshooting

### Flask won't start
```bash
# Kill existing process
lsof -ti:5001 | xargs kill -9

# Restart
python3 app.py
```

### Deployment fails
```bash
# Check domain exists in DB
sqlite3 soulfra.db "SELECT * FROM brands WHERE slug='cringeproof'"

# Check template exists
ls -la voice-archive/

# Run with verbose output
python3 -u domain_deployer.py cringeproof
```

### GitHub deployment fails
```bash
# Install GitHub CLI
brew install gh

# Login
gh auth login

# Retry
python3 domain_deployer.py cringeproof --github
```

## Summary

**What you built:**
- ✅ Visual domain manager (no more CLI for common tasks)
- ✅ One-click deployment (clones CringeProof template)
- ✅ Auto-generated themes from database colors
- ✅ GitHub Pages automation
- ✅ Domain verification system
- ✅ Real-time deployment status

**What you can do now:**
1. Go to `http://localhost:5001/admin/domains`
2. Click "🚀 Deploy" on any domain
3. Watch it create 41 files instantly
4. Optionally push to GitHub Pages
5. Access at `https://soulfra.github.io/<slug>-site`

**Cost to run:**
- Free (laptop only)
- $4/mo (VPS for 24/7 uptime)
- $12/year per domain (custom domains)

**Next action:**
```bash
python3 app.py
open http://localhost:5001/admin/domains
```

Then click "🚀 Deploy" on any domain!
