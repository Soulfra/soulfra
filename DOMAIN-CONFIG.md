# 🌐 Domain Configuration - How Multi-Domain Deployment Works

> **Your question**: "soulfra is the username lol. thats the confusing part like i want it all to go through my soulfra username on github or my soulfra.com website and then i have other domains i want to add as well?"

**Answer**: Here's how the pieces fit together.

---

## 🎯 The Three Layers

### Layer 1: Your GitHub Account
**Username**: `soulfra`

**Location**: https://github.com/soulfra

**What it is**: Your personal GitHub account where all repos live

---

### Layer 2: Brand Repositories
**Brands**: soulfra, calriven, deathtodata

**Repos**:
```
github.com/soulfra/soulfra       ← Soulfra brand
github.com/soulfra/calriven      ← Calriven brand
github.com/soulfra/deathtodata   ← Deathtodata brand
```

**What they are**: Static site exports (one repo per brand)

---

### Layer 3: Custom Domains
**Domains you own**:
```
soulfra.com       → Points to soulfra.github.io/soulfra
calriven.com      → Points to soulfra.github.io/calriven
deathtodata.com   → Points to soulfra.github.io/deathtodata
```

**What they are**: Your actual websites people visit

---

## 📊 Complete Mapping

| Brand | GitHub Repo | GitHub Pages Default URL | Custom Domain |
|-------|-------------|-------------------------|---------------|
| **soulfra** | `soulfra/soulfra` | `soulfra.github.io/soulfra` | `soulfra.com` |
| **calriven** | `soulfra/calriven` | `soulfra.github.io/calriven` | `calriven.com` |
| **deathtodata** | `soulfra/deathtodata` | `soulfra.github.io/deathtodata` | `deathtodata.com` |

---

## 🔄 How Deployment Works

### Step 1: Local Development
```
soulfra-simple/
├── brands/
│   ├── soulfra/        ← Brand config
│   ├── calriven/
│   └── deathtodata/
└── templates/          ← Shared templates
```

---

### Step 2: Static Export
```bash
python3 export_static.py --brand soulfra

# Creates:
output/
└── soulfra/
    ├── index.html
    ├── blog/
    │   └── my-post.html
    └── assets/
```

---

### Step 3: GitHub Deployment
```bash
python3 deploy_github.py --brand soulfra

# Does:
1. Exports brand to static HTML (output/soulfra/)
2. Initializes git in output/soulfra/
3. Creates repo: github.com/soulfra/soulfra
4. Pushes to GitHub
5. Enables GitHub Pages
6. Creates CNAME file with custom domain
```

**Result**: Live at `soulfra.github.io/soulfra`

---

### Step 4: Custom Domain Setup
**CNAME file** (auto-created in repo):
```
soulfra.com
```

**DNS configuration** (you do this at domain registrar):

**Option A: CNAME Record** (Recommended)
```
CNAME  @  soulfra.github.io
```

**Option B: A Records** (Root domain)
```
A  @  185.199.108.153
A  @  185.199.109.153
A  @  185.199.110.153
A  @  185.199.111.153
```

**Result**: `soulfra.com` → Shows GitHub Pages content

---

## 🎨 Brand-Specific Domains

### Soulfra (Main Brand)
**Domain**: `soulfra.com`

**GitHub Repo**: `soulfra/soulfra`

**Purpose**: Main platform, identity & security focused

**Deploy**:
```bash
python3 deploy_github.py --brand soulfra
```

**DNS**:
```
CNAME  @  soulfra.github.io
```

---

### Calriven (Secondary Brand)
**Domain**: `calriven.com`

**GitHub Repo**: `soulfra/calriven`

**Purpose**: Separate brand identity

**Deploy**:
```bash
python3 deploy_github.py --brand calriven
```

**DNS**:
```
CNAME  @  soulfra.github.io
```

**CNAME file contents**:
```
calriven.com
```

**Important**: Even though the repo is `soulfra/calriven`, the CNAME tells GitHub "serve this at calriven.com"

---

### Deathtodata (Third Brand)
**Domain**: `deathtodata.com`

**GitHub Repo**: `soulfra/deathtodata`

**Purpose**: Another brand identity

**Deploy**:
```bash
python3 deploy_github.py --brand deathtodata
```

**DNS**:
```
CNAME  @  soulfra.github.io
```

**CNAME file contents**:
```
deathtodata.com
```

---

## 🔧 How CNAME Files Work

### What is a CNAME file?
**CNAME** (Canonical Name) tells GitHub Pages what custom domain to use

**Location**: `output/brand/CNAME` (root of repo)

**Contents**: Just the domain name (one line)

```
soulfra.com
```

**Example for calriven**:
```
calriven.com
```

**GitHub reads this** and says: "Okay, when someone visits calriven.com, serve this repo's content"

---

## 🌍 The Complete Flow

### User visits `calriven.com`:

```
1. User types: calriven.com
   ↓
2. DNS lookup: calriven.com → CNAME → soulfra.github.io
   ↓
3. GitHub Pages receives request for "calriven.com"
   ↓
4. GitHub checks: Which repo has "calriven.com" in CNAME file?
   ↓
5. Found: soulfra/calriven repo
   ↓
6. GitHub serves: soulfra/calriven's index.html
   ↓
7. User sees: Calriven website at calriven.com
```

**Result**: Different domain, different repo, same GitHub account!

---

## 📝 Brand Configuration File

**Location**: `brand_domains.json` (root of project)

```json
{
  "soulfra": {
    "domain": "soulfra.com",
    "github_repo": "soulfra",
    "api_endpoint": "https://api.soulfra.com"
  },
  "calriven": {
    "domain": "calriven.com",
    "github_repo": "calriven",
    "api_endpoint": "https://api.soulfra.com"
  },
  "deathtodata": {
    "domain": "deathtodata.com",
    "github_repo": "deathtodata",
    "api_endpoint": "https://api.soulfra.com"
  }
}
```

**Key point**: All brands share the same `api_endpoint` (your central API server)

---

## 🚀 Deploy All Brands at Once

```bash
# Deploy all three brands
python3 deploy_github.py --all

# Output:
# ✅ Deployed soulfra to: soulfra.github.io/soulfra
# ✅ Deployed calriven to: soulfra.github.io/calriven
# ✅ Deployed deathtodata to: soulfra.github.io/deathtodata
#
# Next steps:
# 1. Configure DNS for soulfra.com
# 2. Configure DNS for calriven.com
# 3. Configure DNS for deathtodata.com
```

---

## 🔐 Central API Architecture

**Key concept**: All brands connect to ONE API server

```
soulfra.com       ─┐
calriven.com      ─┼─→  api.soulfra.com  ─→  Database
deathtodata.com   ─┘                          Ollama
                                              Stripe
```

**Why?**
- Centralized authentication
- Shared API keys
- Centralized billing
- Single point of control (your revenue!)

**Static sites** (GitHub Pages):
- HTML/CSS/JS only
- Fast & free
- Scalable (GitHub's CDN)

**Dynamic features** (Your API):
- Email capture → `api.soulfra.com/subscribe`
- Blog post generation → `api.soulfra.com/generate`
- Comments → `api.soulfra.com/comments`
- Stripe payment → `api.soulfra.com/checkout`

---

## 💰 Why This Setup Prints Money

### Open Source + Closed API = Profit

**Open source** (GitHub: `soulfra/soulfra-simple`):
- Anyone can clone and self-host
- Formula engine, templates, export scripts
- 100% free, MIT license

**Closed API** (`api.soulfra.com`):
- Required for all AI features
- Requires API keys from YOUR faucets
- Usage tracking, rate limiting
- Stripe billing for Pro/Enterprise

**Result**:
```
User self-hosts platform (free)
   ↓
Wants to generate blog posts with AI
   ↓
Needs API key from soulfra.com
   ↓
Free tier: 100 posts/month
   ↓
Wants unlimited? Pay $19/mo
   ↓
💰 You get paid!
```

**Even better**:
- User refers friend → 30% commission
- Friend refers another friend → Passive income
- Network effects = Exponential growth

---

## 📊 Deployment Checklist

### For Each Brand:

1. **Export static site**
   ```bash
   python3 export_static.py --brand soulfra
   ```

2. **Deploy to GitHub**
   ```bash
   python3 deploy_github.py --brand soulfra
   ```

3. **Check CNAME file**
   - Verify `output/soulfra/CNAME` contains `soulfra.com`

4. **Configure DNS**
   - Add CNAME record: `@ → soulfra.github.io`
   - Wait 5-60 minutes for propagation

5. **Test**
   - Visit `soulfra.github.io/soulfra` (should work immediately)
   - Visit `soulfra.com` (should work after DNS propagation)

6. **Enable HTTPS**
   - GitHub Pages auto-provisions SSL certificate
   - Wait 5-10 minutes after DNS propagation
   - Enforce HTTPS in repo settings

---

## ✅ Summary

**The confusion**:
- "soulfra" is BOTH your GitHub username AND a brand name

**The solution**:
- GitHub account: `soulfra` (personal account)
- Repos: `soulfra/soulfra`, `soulfra/calriven`, `soulfra/deathtodata`
- Domains: `soulfra.com`, `calriven.com`, `deathtodata.com`

**How it works**:
- Each brand → Separate repo under your account
- Each repo → CNAME file with custom domain
- Each domain → DNS points to `soulfra.github.io`
- GitHub Pages → Reads CNAME, serves correct repo

**All brands share**:
- Same GitHub account (soulfra)
- Same API endpoint (api.soulfra.com)
- Same billing system (Stripe)
- Same codebase (soulfra-simple)

**Your advantage**:
- Central control
- Unified billing
- Network effects
- Passive income from API usage

---

**Next**: See `OSS-STRATEGY.md` to understand the open source + closed API business model!
