# 🏢 GitHub Organization Plan - Soulfra Network

## The Problem You Identified

> "it's all the same fucking name. that's why cringeproof is suppose to be the QR filter or whatever and the getpaidtojoin.com is the marketplace"

**You're right!** Everything being called "Soulfra" is confusing. Let's fix that with clear GitHub organization structure.

## Current Confusion

```
❌ BEFORE (Confusing):
- Soulfra = the org?
- Soulfra = the main site?
- Soulfra = the database?
- Soulfra = the codebase?
- StPetePros uses soulfra.com domain?
```

## Proposed Structure

```
✅ AFTER (Clear):

GitHub Organization: Soulfra
├── soulfra.com          → Hub (login, dashboard, star balance)
├── calriven.com         → Technical/developer tools
├── deathtodata.com      → Privacy-focused tools
├── howtocookathome.com  → Recipe/cooking content
├── cringeproof.com      → QR verification/filter
├── getpaidtojoin.com    → Marketplace (buy/sell with stars)
└── soulfra-platform     → Backend codebase (this repo)
```

## Step-by-Step: Creating the GitHub Organization

### Step 1: Create Organization (Free!)

1. Go to: https://github.com/organizations/plan
2. Click "Create organization"
3. Choose "Free" plan
4. Org name: **Soulfra**
5. Contact email: your email
6. Organization belongs to: "My personal account"

**Cost:** $0/month for public repos

### Step 2: Transfer Existing Repo

Current setup:
```bash
# Your deployed site
output/soulfra/.git → https://github.com/Soulfra/soulfra.git
```

This already uses "Soulfra" as the account! Check if it's:
- Personal account named "Soulfra"
- OR already an organization

**To check:**
```bash
# Visit: https://github.com/Soulfra
# If you see "Organization" badge → already an org!
# If you see profile picture → personal account
```

**If personal account, convert to org:**
1. https://github.com/settings/organizations
2. "Convert Soulfra to an organization"
3. Choose a new personal account name for yourself

### Step 3: Create Repos for Each Domain

```bash
# Create these repos in Soulfra org:
github.com/Soulfra/soulfra              ← Main hub site
github.com/Soulfra/calriven             ← Developer tools
github.com/Soulfra/deathtodata          ← Privacy tools
github.com/Soulfra/howtocookathome      ← Recipe site
github.com/Soulfra/cringeproof          ← QR filter
github.com/Soulfra/getpaidtojoin        ← Marketplace
github.com/Soulfra/soulfra-platform     ← Backend (private)
```

**For each repo:**
1. Click "New repository" in org
2. Name it (e.g., "calriven")
3. Description: "CalRiven - Technical resources and developer tools"
4. Public (except soulfra-platform = private)
5. Add README: Yes
6. Add .gitignore: None (we have one)
7. Choose license: MIT

### Step 4: Setup GitHub Pages for Each

Each repo needs Pages enabled:

1. Go to repo → Settings → Pages
2. Source: "Deploy from a branch"
3. Branch: `main` / `docs` (or root)
4. Custom domain: calriven.com
5. Enforce HTTPS: Yes

**Example for CalRiven:**
```
Repo: github.com/Soulfra/calriven
Pages: calriven.com
CNAME file: calriven.com
```

## Domain → Repo Mapping

| Domain | GitHub Repo | Purpose | Tier |
|--------|-------------|---------|------|
| soulfra.com | Soulfra/soulfra | Main hub, dashboard | 0 (free) |
| calriven.com | Soulfra/calriven | Developer tools, API | 1 (5 stars) |
| deathtodata.com | Soulfra/deathtodata | Privacy guides | 1 (5 stars) |
| howtocookathome.com | Soulfra/howtocookathome | Recipes | 2 (15 stars) |
| cringeproof.com | Soulfra/cringeproof | QR verification | 3 (30 stars) |
| getpaidtojoin.com | Soulfra/getpaidtojoin | Marketplace | 4 (50 stars) |

## GitHub Projects - One Per Domain

Each repo gets a Project board for planning.

### Example: CalRiven Project

**Create project:**
1. Go to org: https://github.com/orgs/Soulfra/projects
2. Click "New project"
3. Template: "Roadmap"
4. Name: "CalRiven Development"
5. Description: "Technical resource platform - Q1 2026"

**Roadmap view:**
```
Q1 2026:
- [ ] Launch MVP (calriven.com live)
- [ ] API documentation
- [ ] Code snippet library
- [ ] GitHub star integration

Q2 2026:
- [ ] Developer tutorials
- [ ] Interactive coding playground
- [ ] OAuth integration
```

### Example: CringeProof Project

**Roadmap:**
```
Q1 2026:
- [ ] QR code generator
- [ ] Scan-to-verify system
- [ ] Reputation scoring
- [ ] Earn 1 star per verified scan

Q2 2026:
- [ ] Anti-bot detection
- [ ] Whitelist/blacklist
- [ ] API for third-party integration
```

### Example: GetPaidToJoin Project

**Roadmap:**
```
Q1 2026:
- [ ] Star wallet system
- [ ] List items for sale
- [ ] Buy with stars
- [ ] Transfer stars between users

Q2 2026:
- [ ] Escrow system
- [ ] Reputation-based pricing
- [ ] Featured listings (cost 10 stars)
```

## Organization Settings

### Members & Roles

**Owner (you):**
- Full access to all repos
- Billing
- Org settings

**Members (future collaborators):**
- Read access (can view public repos)
- Write access (can push to specific repos)
- Maintain access (can manage issues/PRs)

### Teams (Optional)

You can create teams later:
- **@Soulfra/core** - Core maintainers
- **@Soulfra/contributors** - Community contributors
- **@Soulfra/moderators** - Content moderators

### Repository Defaults

Set org-wide defaults:
1. Go to: https://github.com/organizations/Soulfra/settings/repository-defaults
2. Default branch: `main`
3. Default .gitignore: Python
4. Default license: MIT
5. Allow forking: Yes
6. Discussions: Enable

## Branding the Organization

### Profile Setup
1. Upload logo (Soulfra icon)
2. Display name: "Soulfra Network"
3. Description: "Multi-domain platform with GitHub star economy"
4. Website: https://soulfra.com
5. Twitter: @soulfra (if you have it)

### README.md in Org Profile

Create `Soulfra/.github/profile/README.md`:

```markdown
# Welcome to Soulfra Network 🌐

A multi-domain platform where GitHub stars unlock features.

## Our Domains

- [soulfra.com](https://soulfra.com) - Main hub
- [calriven.com](https://calriven.com) - Developer tools
- [deathtodata.com](https://deathtodata.com) - Privacy guides
- [cringeproof.com](https://cringeproof.com) - QR verification
- [getpaidtojoin.com](https://getpaidtojoin.com) - Marketplace

## How It Works

⭐ **Star our repos to unlock features**
- 0 stars: Free tier (soulfra.com only)
- 5 stars: Tier 1 (+ calriven.com)
- 15 stars: Tier 2 (+ deathtodata.com)
- 30 stars: Tier 3 (+ cringeproof.com)
- 50 stars: Tier 4 (ALL domains)

## Get Started

1. Star [Soulfra/soulfra](https://github.com/Soulfra/soulfra)
2. Visit [soulfra.com](https://soulfra.com)
3. Login with GitHub
4. See your star count and unlocked domains
```

## DNS Configuration for All Domains

Once repos are created, configure DNS:

### soulfra.com (Already Working)
```
Type: A
Name: @
Value: 185.199.108.153
TTL: 300
```

### calriven.com (New)
```
Type: A
Name: @
Value: 185.199.108.153
TTL: 300

Type: CNAME
Name: www
Value: Soulfra.github.io
TTL: 300
```

### Repeat for All Domains
- deathtodata.com
- howtocookathome.com
- cringeproof.com
- getpaidtojoin.com

## Alternative: Self-Hosted (Instead of GitHub Pages)

If you want ONE server for all domains:

### Get VPS ($5/month)
- DigitalOcean, Linode, Vultr
- 1GB RAM, 25GB SSD
- Ubuntu 22.04
- Public IP: e.g., 123.45.67.89

### Point All DNS to Your VPS
```
soulfra.com          A    123.45.67.89
calriven.com         A    123.45.67.89
deathtodata.com      A    123.45.67.89
cringeproof.com      A    123.45.67.89
getpaidtojoin.com    A    123.45.67.89
```

### Caddy Routes by Domain
```caddy
soulfra.com {
    reverse_proxy localhost:5001
    # Flask app detects "soulfra.com" and shows hub
}

calriven.com {
    reverse_proxy localhost:5001
    # Same Flask app, but shows CalRiven content
}

cringeproof.com {
    reverse_proxy localhost:5001
    # Same Flask app, but shows CringeProof content
}
```

**Benefit:** Dynamic sites with database backend
**Cost:** $5/month VPS

## Hybrid Approach (Recommended)

Use BOTH GitHub Pages AND self-hosted:

```
GitHub Pages (Static Sites):
- soulfra.com         → Landing page, marketing
- calriven.com        → Blog, documentation

Self-Hosted (Dynamic Apps):
- app.soulfra.com     → Dashboard, user accounts
- api.soulfra.com     → API endpoints
- pay.getpaidtojoin.com → Marketplace transactions
```

## Migration Checklist

- [ ] Create Soulfra organization on GitHub
- [ ] Transfer soulfra.git to org (if not already there)
- [ ] Create repos for each domain
- [ ] Enable GitHub Pages for each repo
- [ ] Add CNAME files
- [ ] Configure DNS for new domains
- [ ] Create Projects for each domain
- [ ] Write roadmaps in each project
- [ ] Add README files explaining each domain's purpose
- [ ] Build star economy integration (github_integration.py)

## What This Solves

### Before (Confusing):
- "Everything is called Soulfra"
- "I don't know which repo is which"
- "Are these separate or one thing?"

### After (Clear):
- **Soulfra** = GitHub org (container for all domains)
- **soulfra.com** = Main hub (login, dashboard)
- **calriven.com** = Developer tools (separate site)
- **cringeproof.com** = QR filter (separate app)
- **getpaidtojoin.com** = Marketplace (separate feature)
- **soulfra-platform** = Backend code (private repo)

Each domain has its own:
- Git repository
- GitHub Project (roadmap)
- Purpose/niche
- Tier requirement
- Independent deployment

But all connected through:
- Same GitHub org
- Star economy
- Shared user accounts
- Cross-linking

## Next Steps

1. **Create the org** (5 minutes)
2. **Move repos** (10 minutes)
3. **Setup Projects** (30 minutes per domain)
4. **Write roadmaps** (1 hour per domain)
5. **Build star integration** (see github_integration.py plan)

Ready to execute? Start with Step 1: Create Organization!
