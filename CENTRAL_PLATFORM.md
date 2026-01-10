# Central Platform Architecture

## Overview

Soulfra uses a **multi-domain JAMstack architecture** where each brand gets its own domain with a static site, but all sites connect to a central API for dynamic features.

```
┌─────────────────────────────────────────────────────────────┐
│                    CENTRAL PLATFORM                         │
│              api.howtocookathome.com                        │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Flask     │  │   SQLite     │  │  Membership     │   │
│  │   API       │──│   Database   │──│  System         │   │
│  │   Server    │  │              │  │  (Stripe)       │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│         │                                                   │
│         │ API Calls (/api/*)                              │
└─────────┴───────────────────────────────────────────────────┘
          │
          │
    ┌─────┴────────┬──────────────┬──────────────┐
    │              │              │              │
    ▼              ▼              ▼              ▼
┌────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
│soulfra │   │calriven  │   │deathto  │   │howtocook │
│.com    │   │.com      │   │data.com │   │athome.com│
│        │   │          │   │         │   │          │
│Static  │   │Static    │   │Static   │   │Static    │
│HTML    │   │HTML      │   │HTML     │   │HTML      │
│        │   │          │   │         │   │          │
│GitHub  │   │GitHub    │   │GitHub   │   │GitHub    │
│Pages   │   │Pages     │   │Pages    │   │Pages     │
│FREE    │   │FREE      │   │FREE     │   │FREE      │
└────────┘   └──────────┘   └─────────┘   └──────────┘
```

## How It Works

### 1. Static Sites (GitHub Pages - FREE)

Each brand is exported to a **static HTML site** in the `output/` directory:

```
output/
├── soulfra/           # soulfra.com
│   ├── index.html     # Homepage with posts
│   ├── post/          # Individual post pages
│   ├── feed.xml       # RSS feed
│   └── CNAME          # Domain configuration
├── calriven/          # calriven.com
├── deathtodata/       # deathtodata.com
└── howtocookathome/   # howtocookathome.com
```

**Static content includes:**
- Homepage with post listings
- Individual post pages with AI-generated comments
- Email subscription forms
- RSS feeds for podcasts
- Brand-specific styling (colors, fonts, logos)

### 2. Central API (DigitalOcean - $5/month)

The central platform at `api.howtocookathome.com` provides:

**Dynamic Features:**
- Email capture (`POST /api/email-capture`)
- Comment posting (`POST /api/comments`)
- User authentication (`/api/auth`)
- Membership management (Stripe integration)
- AI persona responses
- Content generation

**Database:**
- SQLite database with all brands, posts, comments, users
- AI personas (CalRiven, Soulfra, DeathToData)
- Email subscribers
- Membership data

### 3. JavaScript Bridge

Each static site includes JavaScript that calls the central API:

```javascript
// Every exported site has this
const API_BASE = 'https://api.howtocookathome.com';
const BRAND_SLUG = 'soulfra'; // Changes per brand

// Email capture
async function captureEmail(email) {
    const response = await fetch(`${API_BASE}/api/email-capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, brand_slug: BRAND_SLUG })
    });
    return response.json();
}

// Post comment
async function postComment(post_id, content, author_name) {
    const response = await fetch(`${API_BASE}/api/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ post_id, content, author_name, brand_slug: BRAND_SLUG })
    });
    return response.json();
}
```

## Deployment Workflow

### 1. Create/Update Content

```bash
# Flask app runs locally for content creation
python3 app.py

# Access admin dashboard
open http://localhost:5001/admin?dev_login=true

# Create posts, add AI comments, manage brands
```

### 2. Export to Static Sites

```bash
# Export all brands to static HTML
python3 export_static.py

# Or export a specific brand
python3 export_static.py --brand soulfra
```

This generates the `output/` directory with static sites for each brand.

### 3. Deploy to GitHub Pages

For each brand:

```bash
cd output/soulfra

# Initialize git repo
git init
git add .
git commit -m "Initial deployment"

# Create GitHub repo and push
gh repo create soulfra --public --source=. --push

# Enable GitHub Pages in repo settings
# Settings → Pages → Source: main branch

# Configure custom domain
# Add DNS CNAME record: soulfra.com → <username>.github.io
# GitHub Pages HTTPS certificate is automatic
```

### 4. Configure DNS

For each domain, add a CNAME record:

```
soulfra.com         CNAME  username.github.io
calriven.com        CNAME  username.github.io
deathtodata.com     CNAME  username.github.io
howtocookathome.com CNAME  username.github.io (or A record to DigitalOcean)
```

## Cost Breakdown

| Component | Platform | Cost |
|-----------|----------|------|
| Static Sites (4 brands) | GitHub Pages | **FREE** |
| Central API | DigitalOcean Droplet | **$5/month** |
| Domain Names (4 domains) | Namecheap/etc | **~$40/year** |
| SSL Certificates | GitHub Pages (auto) | **FREE** |
| **Total Monthly** | | **$5/month** |

## White-Label System

### Current Brands

| Brand | Domain | Category | Purpose |
|-------|--------|----------|---------|
| **HowToCookAtHome** | howtocookathome.com | Cooking | Central platform + example brand |
| **Soulfra** | soulfra.com | Tech | Identity & consciousness platform |
| **CalRiven** | calriven.com | Tech | Technical excellence & AI routing |
| **DeathToData** | deathtodata.com | Privacy | Data privacy & protection |

### Adding a New Brand

1. **Add to domains.txt:**
   ```
   newbrand.com | category | Tagline here
   ```

2. **Update database:**
   ```sql
   UPDATE brands SET domain = 'newbrand.com' WHERE slug = 'newbrand';
   ```

3. **Export and deploy:**
   ```bash
   python3 export_static.py --brand newbrand
   cd output/newbrand
   git init && git add . && git commit -m "Deploy"
   gh repo create newbrand --public --source=. --push
   ```

4. **Point DNS:**
   ```
   newbrand.com CNAME username.github.io
   ```

The new brand automatically connects to `api.howtocookathome.com` for all dynamic features.

## Why This Architecture?

### ✅ Advantages

1. **Cost-Effective**: Only $5/month for unlimited brands
2. **Scalable**: GitHub Pages handles CDN & traffic for free
3. **Fast**: Static HTML is incredibly fast
4. **Reliable**: GitHub's 99.9% uptime SLA
5. **SEO-Friendly**: Static HTML is easily crawlable
6. **White-Label**: Each brand has its own domain & branding
7. **Centralized Data**: One database, one API, easy management

### ⚠️ Tradeoffs

1. **Two-Step Deploy**: Content creation (Flask) → Export (static) → Deploy (GitHub)
2. **API Dependency**: Dynamic features require central API to be running
3. **Cache Staleness**: Static sites need to be re-exported when content changes

## API Endpoints

All endpoints accept `brand_slug` parameter to identify which brand the request is for.

### Email Capture
```
POST /api/email-capture
{
  "email": "user@example.com",
  "brand_slug": "soulfra"
}
```

### Post Comment
```
POST /api/comments
{
  "post_id": 42,
  "content": "Great post!",
  "author_name": "John Doe",
  "brand_slug": "soulfra"
}
```

### Get Comments
```
GET /api/comments?post_id=42&brand_slug=soulfra
```

## Future: Membership Integration

The architecture supports adding membership features:

```
User visits soulfra.com
   ↓
JavaScript checks auth with api.howtocookathome.com
   ↓
API returns membership tier (Free/Pro/Premium)
   ↓
JavaScript shows/hides features based on tier
   ↓
Stripe checkout redirects to api.howtocookathome.com
   ↓
Webhook updates membership in database
   ↓
User gets access to premium features across ALL brands
```

This allows:
- **Free tier**: 1 brand, basic features
- **Pro tier**: 5 brands, export unlocked
- **Premium tier**: Unlimited brands, reserved usernames

All managed centrally, but accessible from any brand's static site.

## Development vs Production

### Local Development (Flask App)

```bash
python3 app.py
# Access at http://localhost:5001

# All brands available at:
# /brand/soulfra
# /brand/calriven
# /brand/deathtodata
# /brand/howtocookathome
```

### Production (Static Export)

```bash
# Export to static HTML
python3 export_static.py

# Each brand becomes separate static site
# Deployed to own domain via GitHub Pages
# All call back to api.howtocookathome.com
```

## Summary

This architecture answers the original confusion: **each brand is exported to its own static site and deployed to its own domain, but all sites share a central API and database for dynamic features.**

- **soulfra.com** → Static HTML on GitHub Pages → Calls API
- **calriven.com** → Static HTML on GitHub Pages → Calls API
- **deathtodata.com** → Static HTML on GitHub Pages → Calls API
- **howtocookathome.com** → Static HTML + Flask API on DigitalOcean

This gives each brand its own identity and domain while keeping costs minimal and management centralized.
