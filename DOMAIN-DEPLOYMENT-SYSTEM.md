# Multi-Domain Deployment System

You now have a complete visual interface to manage and deploy all your domains from one place.

## What You Have

### 1. **Visual Admin Dashboard**
```
http://localhost:5001/admin/domains
```

**Features:**
- ✅ Add/edit/delete domains via web form
- ✅ AI research with Ollama (auto-suggests category/tagline/colors)
- ✅ CSV bulk import for 10+ domains
- ✅ Search & filter table
- ✅ Deploy button for each domain
- ✅ Status checker with real-time deployment info
- ✅ Currently managing 9 domains

### 2. **Database Admin Panel**
```
http://localhost:5001/admin/database
```

**Features:**
- ✅ SharePoint-like interface
- ✅ View/export all tables
- ✅ SQL query runner
- ✅ Email list export for mailing lists
- ✅ CSV exports for all data

### 3. **Deployment System**

#### Option A: Visual UI (Recommended)
1. Go to `http://localhost:5001/admin/domains`
2. Find domain in table
3. Click "🚀 Deploy" button
4. Confirm deployment
5. Optionally deploy to GitHub Pages

#### Option B: Command Line
```bash
# Deploy locally (creates 40+ files from CringeProof template)
python3 domain_deployer.py cringeproof

# Check deployment status
python3 domain_deployer.py cringeproof --status

# Deploy to GitHub Pages
python3 domain_deployer.py cringeproof --github
```

#### Option C: API
```bash
# Deploy domain locally
curl -X POST http://localhost:5001/api/domains/cringeproof/deploy \
  -H "Content-Type: application/json" \
  -d '{"backend_url": "https://your-backend.com"}'

# Check status
curl http://localhost:5001/api/domains/cringeproof/status

# Deploy to GitHub
curl -X POST http://localhost:5001/api/domains/cringeproof/deploy-github \
  -H "Content-Type: application/json" \
  -d '{"create_repo": true}'

# Verify domain ownership
curl -X POST http://localhost:5001/api/domains/cringeproof/verify \
  -H "Content-Type: application/json" \
  -d '{"method": "dns"}'
```

## How Deployment Works

### Local Deployment
1. Reads domain config from `soulfra.db` → `brands` table
2. Copies entire `voice-archive/` structure (CringeProof template)
3. Generates `config.js` with:
   - Domain slug
   - Brand name
   - Tagline
   - Theme colors
   - Backend URL
4. Generates `theme.css` with CSS variables from database colors
5. Updates `manifest.json` with domain branding
6. Creates 40+ files in `deployed-domains/<slug>/`

### GitHub Deployment (Optional)
1. Initializes git repo in deployed folder
2. Creates GitHub repo via `gh` CLI
3. Pushes all files to `main` branch
4. Enables GitHub Pages
5. Returns GitHub Pages URL: `https://soulfra.github.io/<slug>-site`

## Current Domains

All 9 domains in database:
1. **soulfra.com** - Hub (Identity & Security)
2. **cringeproof.com** - Community (Zero Performance Anxiety)
3. **deathtodata.com** - Privacy Search
4. **calriven.com** - AI Platform
5. **howtocookathome.com** - Cooking Blog
6. **stpetepros.com** - Home Services (Tampa Bay)
7. **hollowtown.com** - Gaming Mysteries
8. **oofbox.com** - Gaming
9. **niceleak.com** - Gaming

**Status:** All domains unverified (`verified = 0`)

## Domain Verification

To verify domain ownership:

### Method 1: DNS TXT Record
1. Add TXT record to your domain's DNS:
   ```
   Name: _soulfra-verification
   Value: <slug>
   ```
2. Wait for DNS propagation (5-30 minutes)
3. Click "Verify" in admin UI or run:
   ```bash
   curl -X POST http://localhost:5001/api/domains/<slug>/verify \
     -H "Content-Type: application/json" \
     -d '{"method": "dns"}'
   ```

### Method 2: File Upload
1. Create file: `.well-known/soulfra-verify.txt`
2. Content: `<slug>`
3. Upload to domain root
4. Visit: `https://yourdomain.com/.well-known/soulfra-verify.txt`
5. Should show just the slug
6. Click "Verify" in admin UI

## Deployment Output

Each deployed domain gets:
```
deployed-domains/
  └── cringeproof/
      ├── config.js           # Auto-generated domain config
      ├── theme.css           # Auto-generated theme from DB colors
      ├── manifest.json       # PWA manifest with branding
      ├── index.html          # Landing page
      ├── record-simple.html  # Voice recorder
      ├── wordmap.html        # Wordmap visualization
      ├── wall.html           # Voice wall
      ├── screenshot.html     # OCR extractor
      ├── login.html          # OAuth login
      ├── account.html        # User account
      └── ... (35 more files from CringeProof template)
```

## Backend Configuration

Each domain's `config.js` auto-detects environment:

```javascript
API_BACKEND_URL: (() => {
    const hostname = window.location.hostname;

    // Local testing
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:5001';
    }

    // Production - your deployed backend
    return 'https://your-backend.com';  // Set via deployment
})()
```

## Next Steps

### 1. Deploy All Domains Locally
```bash
for domain in soulfra deathtodata calriven howtocookathome stpetepros hollowtown oofbox niceleak; do
  python3 domain_deployer.py $domain
done
```

### 2. Set Up Permanent Backend URL

Choose one:

#### Option A: Tailscale Funnel (Free, Permanent)
```bash
brew install tailscale
sudo tailscale up
tailscale funnel --bg --https=443 https://localhost:5001

# Gets permanent URL: https://your-laptop.tailscale-funnel.com
```

#### Option B: Named Cloudflare Tunnel (Free, Permanent)
```bash
cloudflared tunnel login
cloudflared tunnel create soulfra-backend
cloudflared tunnel route dns soulfra-backend api.soulfra.com

# Run tunnel
cloudflared tunnel run soulfra-backend

# Gets permanent URL: https://api.soulfra.com
```

#### Option C: VPS Deployment ($4/mo, 100% uptime)
You already have GitHub Actions setup in `.github/workflows/deploy.yml`
- Push to `main` branch → auto-deploys to VPS
- Railway.app or Render.com (both have $5/mo tiers)

### 3. Update Backend URLs
After choosing backend option, update deployments:

```bash
# Example: Using Tailscale
python3 domain_deployer.py cringeproof \
  --backend-url https://your-laptop.tailscale-funnel.com
```

Or edit `deployed-domains/<slug>/config.js` manually.

### 4. Deploy to GitHub Pages

For each domain:
```bash
python3 domain_deployer.py cringeproof --github
```

This creates GitHub repo and enables Pages at:
```
https://soulfra.github.io/cringeproof-site
```

### 5. Connect Custom Domains

In GitHub repo settings:
1. Go to Settings → Pages
2. Custom domain: `cringeproof.com`
3. Add CNAME record in your DNS:
   ```
   CNAME  @  soulfra.github.io.
   ```
4. Wait 5-10 minutes for SSL cert
5. Visit `https://cringeproof.com`

### 6. Verify All Domains

For production credibility:
```bash
python3 domain-manager.py verify soulfra
python3 domain-manager.py verify cringeproof
# ... etc
```

Updates `brands.verified` = 1 in database.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP (Control Hub)                 │
│                                                              │
│  ┌────────────────┐   ┌─────────────────┐                  │
│  │  soulfra.db    │   │   Flask Backend │                  │
│  │  (9 domains)   │◄──│   localhost:5001│                  │
│  └────────────────┘   └─────────────────┘                  │
│                              │                               │
│                              │                               │
│  ┌────────────────────────────────────────┐                │
│  │      Deployed Domains (Local)           │                │
│  │  deployed-domains/                      │                │
│  │    ├── cringeproof/  (41 files)        │                │
│  │    ├── soulfra/      (41 files)        │                │
│  │    └── ...                              │                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ git push
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Pages                          │
│                                                              │
│  https://soulfra.github.io/cringeproof-site/                │
│  https://soulfra.github.io/deathtodata-site/                │
│  https://soulfra.github.io/calriven-site/                   │
│  ... (9 domains)                                            │
│                                                              │
│  ▼ CNAME to custom domains                                  │
│                                                              │
│  https://cringeproof.com  ──► GitHub Pages                  │
│  https://deathtodata.com  ──► GitHub Pages                  │
│  https://calriven.com     ──► GitHub Pages                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ API calls
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Choose One)                      │
│                                                              │
│  Option 1: Tailscale Funnel (Free)                          │
│    https://your-laptop.tailscale-funnel.com                 │
│                                                              │
│  Option 2: Cloudflare Tunnel (Free)                         │
│    https://api.soulfra.com                                  │
│                                                              │
│  Option 3: VPS ($4/mo)                                       │
│    https://api.soulfra.com (Railway/Render)                 │
└─────────────────────────────────────────────────────────────┘
```

## Domain Management Workflow

### Add New Domain
1. Go to `http://localhost:5001/admin/domains`
2. Enter domain in "Quick Add - AI Research" form
3. Ollama analyzes and suggests category/tagline/colors
4. Review and confirm
5. Domain saved to database

### Deploy Domain
1. Click "🚀 Deploy" button
2. Creates 41 files in `deployed-domains/<slug>/`
3. Optionally push to GitHub Pages
4. Optionally set up custom domain

### Check All Domain Statuses
```bash
python3 domain-manager.py status
```

Shows:
- ✅/❌ Verified
- ✅/❌ Live (HTTP 200)
- ✅/❌ Backend Connected
- ✅/❌ Theme Applied

## Cost Breakdown

**Current Setup (100% Free):**
- ✅ Flask backend (localhost)
- ✅ GitHub Pages (unlimited sites)
- ✅ Tailscale Funnel (free tier)
- ✅ SQLite database (local)
- ✅ Ollama AI (local)

**Upgrade Options:**
- VPS Backend: $4-5/mo (Railway, Render, Fly.io)
- Custom Domain: $12/year (Namecheap, Cloudflare)
- PostgreSQL Database: Free (Supabase) or $5/mo (Railway)

**Total to run unlimited domains:**
- Minimum: $0/mo (laptop online)
- Recommended: $4/mo (VPS for 24/7 uptime)
- Premium: $9/mo (VPS + better database)

## Files You Created

1. **domain-manager.py** - CLI tool for domain management
2. **domain_deployer.py** - Deployment engine using CringeProof template
3. **domains.json** - Exported manifest of all 9 domains
4. **API routes in app.py** (lines 9420-9583):
   - `POST /api/domains/<slug>/deploy`
   - `POST /api/domains/<slug>/deploy-github`
   - `GET /api/domains/<slug>/status`
   - `POST /api/domains/<slug>/verify`
5. **UI updates in templates/admin/domains.html**:
   - Deploy button
   - Status button
   - JavaScript deployment functions

## Troubleshooting

### Port 5001 in use
```bash
# Kill existing Flask
lsof -ti:5001 | xargs kill -9

# Restart Flask
python3 app.py
```

### GitHub CLI not installed
```bash
brew install gh
gh auth login
```

### Deployment fails
```bash
# Check database has domain
sqlite3 soulfra.db "SELECT name, domain FROM brands WHERE slug='cringeproof'"

# Check template exists
ls -la voice-archive/

# Run deployment with verbose output
python3 -u domain_deployer.py cringeproof
```

### Backend not accessible
```bash
# Test Flask is running
curl http://localhost:5001/api/health

# Test Tailscale Funnel
curl https://your-laptop.tailscale-funnel.com/api/health
```

## Summary

You now have:
- ✅ Visual admin UI at `localhost:5001/admin/domains`
- ✅ Database admin at `localhost:5001/admin/database`
- ✅ Deployment system that clones CringeProof template
- ✅ Auto-generated themes from database colors
- ✅ CLI tools for batch operations
- ✅ API endpoints for programmatic deployment
- ✅ Domain verification system
- ✅ GitHub Pages deployment automation

**Next action:** Go to `http://localhost:5001/admin/domains` and click "🚀 Deploy" on any domain!
