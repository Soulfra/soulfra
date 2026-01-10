# ReadTheDocs-Style Multi-Subdomain Architecture

**Soulfra Platform - Unified Account System with Brand Subdomains**

Inspired by ReadTheDocs.org's multi-subdomain architecture where different subdomains serve different purposes but share the same user accounts.

---

## Architecture Overview

```
deathtodata.com              ← Main Entry Point (Privacy/Encryption Focus)
  │
  ├── app.deathtodata.com    ← Interactive Application
  ├── ref.deathtodata.com    ← API Reference & Docs
  ├── org.deathtodata.com    ← Organization/About

soulfra.com                  ← Account & Faucet System
  │
  ├── faucet.soulfra.com     ← QR-based Signup/Login
  ├── profile.soulfra.com    ← User Profiles

calriven.com                 ← AI Agent Marketplace
  │
  ├── api.calriven.com       ← AI API Endpoints
  ├── marketplace.calriven.com ← Browse AI Agents
```

**All subdomains share:**
- Same user database (`users` table)
- Same session system (cross-subdomain cookies)
- Same keyring unlock system (permanent feature access)

---

## The Three Pillars

### 1. DeathToData - Entry Point
**Purpose**: Public-facing site, privacy focus, encryption advocacy

**Subdomains:**
- **`deathtodata.com`** - Main landing page
- **`app.deathtodata.com`** - Interactive tools
- **`ref.deathtodata.com`** - Documentation
- **`org.deathtodata.com`** - About/mission

**Content:**
- Encryption tiers explanation
- Privacy guides
- Blog posts about data ownership
- Entry to quiz/narrative game

### 2. Soulfra - Account System (Faucet)
**Purpose**: User accounts, QR signup, personality profiles

**Subdomains:**
- **`soulfra.com`** - Dashboard
- **`faucet.soulfra.com`** - QR code signup (like a crypto faucet)
- **`profile.soulfra.com`** - User profiles

**Features:**
- QR code authentication (passwordless)
- Personality quiz & AI friend assignment
- Keyring unlock system (permanent feature access)
- Email alias generation (`user@soulfra.com`)

### 3. CalRiven - AI Marketplace
**Purpose**: AI agent directory, API access, technical tools

**Subdomains:**
- **`calriven.com`** - Marketplace landing
- **`api.calriven.com`** - AI API endpoints
- **`marketplace.calriven.com`** - Browse agents

**Features:**
- AI persona directory (CalRiven, Soulfra, DeathToData, TheAuditor)
- API key management
- Webhook integrations
- Developer docs

---

## Keyring Unlock System (Runescape Style)

Like the Runescape keyring: **once you unlock something, it stays unlocked permanently**.

### How It Works

```python
# User completes quiz
unlock_quiz_completion(user_id=1, ai_friend='soulfra')
# Unlocks: 'personality_profile', 'soulfra_ai'

# User upgrades to premium
unlock_tier_upgrade(user_id=1, tier='premium', payment_id='stripe_123')
# Unlocks: 'premium_tier', 'custom_email', 'api_access'
```

### Unlockable Features

| Feature Key | Name | Category | How to Unlock |
|------------|------|----------|---------------|
| `personality_profile` | Personality Profile | Profile | Complete quiz |
| `soulfra_ai` | Soulfra AI Friend | AI | Complete quiz |
| `premium_tier` | Premium Tier | Tier | One-time payment |
| `pro_tier` | Pro Tier | Tier | One-time payment |
| `calriven_api` | CalRiven AI API | AI | Pro tier |
| `custom_email` | Custom Email | Communication | Premium tier |
| `api_access` | API Access | Developer | Premium tier |
| `deathtodata_encryption` | E2E Encryption | Encryption | Pro tier |

### Checking Unlocks

```python
from keyring_unlocks import has_unlocked, get_user_unlocks

# Check single feature
if has_unlocked(user_id=1, feature_key='calriven_api'):
    # User has access

# Get all unlocks
unlocks = get_user_unlocks(user_id=1)
for unlock in unlocks:
    print(f"{unlock['name']} - {'PERMANENT' if unlock['is_permanent'] else 'Expires'}")
```

---

## Subdomain Routing (Flask)

### Current Implementation

`subdomain_router.py` handles brand-based subdomains:

```python
# In app.py
from subdomain_router import setup_subdomain_routing
setup_subdomain_routing(app)
```

**How it works:**
1. Detects subdomain from `request.host`
2. Looks up brand by slug
3. Applies brand-specific theming (CSS overrides)
4. Makes brand context available in templates

### Local Testing

```bash
# Add to /etc/hosts (macOS/Linux)
127.0.0.1 deathtodata.localhost
127.0.0.1 app.deathtodata.localhost
127.0.0.1 ref.deathtodata.localhost
127.0.0.1 soulfra.localhost
127.0.0.1 faucet.soulfra.localhost
127.0.0.1 calriven.localhost
127.0.0.1 api.calriven.localhost

# Then visit:
http://deathtodata.localhost:5001
http://app.deathtodata.localhost:5001
http://faucet.soulfra.localhost:5001
```

### Production (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name deathtodata.com *.deathtodata.com;

    ssl_certificate /etc/letsencrypt/live/deathtodata.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/deathtodata.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## Unified Account Flow

### 1. New User Arrives

```
User → deathtodata.com
  ↓
Clicks "Get Started"
  ↓
Redirected to faucet.soulfra.com
  ↓
Scans QR code (passwordless signup)
  ↓
Account created in `users` table
  ↓
Session cookie set (works across all subdomains)
```

### 2. Complete Personality Quiz

```
User → app.deathtodata.com/cringeproof
  ↓
Complete narrative quiz
  ↓
Keyring unlocks: 'personality_profile', 'soulfra_ai'
  ↓
Profile built with AI friend assignment
  ↓
Welcome email sent to user@soulfra.com
```

### 3. Access CalRiven Marketplace

```
User → calriven.com/marketplace
  ↓
Browse AI agents
  ↓
Click "Get API Access"
  ↓
Check unlocks: has_unlocked(user_id, 'calriven_api')
  ↓
If unlocked: Generate API key
  ↓
If not: Redirect to upgrade page
```

---

## Cross-Subdomain Sessions

### Cookie Configuration

```python
# Flask session settings for cross-subdomain cookies
app.config['SESSION_COOKIE_DOMAIN'] = '.deathtodata.com'  # Leading dot = all subdomains
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

**Result**: User logs in at `faucet.soulfra.com` → session works at `app.deathtodata.com`

---

## Email System (Future Phase)

### Custom Email Aliases

**Goal**: Give users custom email addresses based on quiz results

```
username@soulfra.com        → Forwards to real_email@gmail.com
username@calriven.com       → Forwards to real_email@gmail.com
username@deathtodata.com    → Forwards to real_email@gmail.com
```

### Implementation Plan

1. **Postfix/Dovecot** mail server
2. **Virtual alias table**:
   ```sql
   CREATE TABLE email_aliases (
       alias_email TEXT PRIMARY KEY,  -- 'user@soulfra.com'
       forward_to TEXT,               -- 'real@gmail.com'
       user_id INTEGER,
       brand_slug TEXT,
       created_at TIMESTAMP
   )
   ```
3. **Postfix virtual map**:
   ```
   user@soulfra.com     real@gmail.com
   user@calriven.com    real@gmail.com
   ```

---

## API Architecture

### REF Subdomain (Docs)

`ref.deathtodata.com` → API reference documentation

```
GET https://ref.deathtodata.com/docs/api
GET https://ref.deathtodata.com/docs/webhooks
GET https://ref.deathtodata.com/docs/encryption-tiers
```

### API Subdomain (Endpoints)

`api.calriven.com` → Actual API endpoints

```
POST https://api.calriven.com/v1/chat
GET  https://api.calriven.com/v1/models
POST https://api.calriven.com/v1/judgment
```

**Authentication**: API keys from keyring unlock system

---

## Version Routing (Like ReadTheDocs)

**Future enhancement**: Version-specific docs

```
ref.deathtodata.com/latest/    → Latest documentation
ref.deathtodata.com/v1.0/      → Version 1.0 docs
ref.deathtodata.com/v2.0/      → Version 2.0 docs
```

### Implementation

```python
@app.route('/docs/<version>/<path:page>')
def docs_version(version, page):
    """Serve version-specific documentation"""
    docs_path = f'docs/{version}/{page}.md'
    # Render markdown to HTML
```

---

## Comparison to ReadTheDocs

| ReadTheDocs | Soulfra Platform |
|------------|------------------|
| `project.readthedocs.org` | `brand.deathtodata.com` |
| `docs.readthedocs.io` | `ref.deathtodata.com` |
| `about.readthedocs.com` | `org.deathtodata.com` |
| GitHub auth | QR code faucet |
| One account for all projects | One account for all brands |
| Version routing | Version routing (future) |
| Hosted docs | Hosted apps + docs |

---

## Implementation Checklist

### Phase 1: Broken Routes ✅
- [x] Move `ollama_discussion.py` from archive
- [x] Fix `/dashboard` network_name error
- [x] Add `/simple-test` route
- [x] Enable subdomain routing
- [x] Create keyring unlock system

### Phase 2: Subdomain Infrastructure
- [ ] Configure nginx for wildcard subdomains
- [ ] Set up SSL certificates (Let's Encrypt wildcard)
- [ ] Configure cross-subdomain cookies
- [ ] Test subdomain routing locally

### Phase 3: Email System
- [ ] Install Postfix/Dovecot
- [ ] Create `email_aliases` table
- [ ] Build alias generator (quiz completion → `user@soulfra.com`)
- [ ] Configure forwarding rules

### Phase 4: API & Docs
- [ ] Build `ref.` subdomain docs site
- [ ] Create `api.` subdomain endpoints
- [ ] API key generation from keyring unlocks
- [ ] Webhook system for integrations

---

## Testing Locally

### 1. Update /etc/hosts

```bash
sudo nano /etc/hosts

# Add:
127.0.0.1 deathtodata.localhost
127.0.0.1 app.deathtodata.localhost
127.0.0.1 ref.deathtodata.localhost
127.0.0.1 soulfra.localhost
127.0.0.1 faucet.soulfra.localhost
127.0.0.1 calriven.localhost
```

### 2. Start Flask

```bash
python3 app.py
# Server runs on port 5001
```

### 3. Test Subdomains

```bash
# Main entry
curl http://deathtodata.localhost:5001

# Faucet (signup)
curl http://faucet.soulfra.localhost:5001

# AI marketplace
curl http://calriven.localhost:5001
```

### 4. Check Keyring

```python
from keyring_unlocks import get_user_unlocks

unlocks = get_user_unlocks(user_id=1)
for unlock in unlocks:
    print(unlock['name'])
```

---

## Summary

**Soulfra Platform = ReadTheDocs-Style Multi-Brand Architecture**

- **DeathToData**: Front door (privacy/encryption focus)
- **Soulfra**: Account faucet (QR signup, profiles)
- **CalRiven**: AI marketplace (API access)

**Unified by:**
- Single user database
- Cross-subdomain sessions
- Keyring unlock system (Runescape style)
- Shared email/notification infrastructure

**Like ReadTheDocs but for:**
- AI agents instead of docs
- QR auth instead of GitHub
- Feature unlocks instead of project permissions
- Privacy/encryption focus instead of documentation hosting

---

**Next Steps**: Configure nginx wildcard SSL, test cross-subdomain cookies, build email alias system.
