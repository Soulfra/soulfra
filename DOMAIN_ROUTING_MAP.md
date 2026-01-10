# Domain Routing Map - Soulfra Ecosystem

## Current State (What Exists)

### Live Domains
| Domain | Points To | Content | Backend |
|--------|-----------|---------|---------|
| cringeproof.com | GitHub Pages (Soulfra/voice-archive) | Voice memos interface | None (static) |
| soulfra.github.io | GitHub Pages (Soulfra/soulfra.github.io) | Portfolio hub | None (static) |
| soulfra.com | ??? | Unknown | ??? |

### Local Infrastructure
- **Flask API**: `cringeproof_api.py` at `https://192.168.1.87:5002`
- **Database**: `soulfra.db` (shared by all)
- **Repos**:
  - `~/Desktop/voice-archive` → Soulfra/voice-archive
  - `~/Desktop/soulfra.github.io` → Soulfra/soulfra.github.io
  - `~/Desktop/roommate-chat/soulfra-simple/` → Local dev environment

## Target Architecture (What We're Building)

```
┌─────────────────────────────────────────────────────────┐
│                   User's Browser                        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │           │
        ▼          ▼           ▼
   cringeproof  soulfra    alice.cringeproof.com
      .com       .com         (user slug)
        │          │           │
        │          │           │
        └──────────┴───────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   Flask API         │
        │   (Unified Backend) │
        │   Port 5002         │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   soulfra.db        │
        │   (Single Source)   │
        │                     │
        │  - users            │
        │  - wordmaps         │
        │  - domain_ownership │
        │  - qr_auth_tokens   │
        │  - recordings       │
        └─────────────────────┘
```

## Data Flow: GitHub README → Wordmap → Avatar

### 1. GitHub README as Content Source
```
github.com/soulfra/soulfra/README.md
  │
  │ (Parse on commit via webhook)
  ├──> Extract words
  ├──> Calculate frequencies
  │
  ▼
domain_wordmaps table
  │
  ├──> Generate CSS colors (already built!)
  ├──> Generate avatar from top words
  ├──> Generate favicon from primary color
  └──> Update QR rotation images
```

### 2. QR Pairing Flow (Laptop + Phone)
```
User visits soulfra.com on laptop (192.168.1.87)
  │
  ▼
Generate QR code → Insert into qr_auth_tokens table
  │
  │ (User scans with phone)
  ▼
Phone validates QR → Links to user account
  │
  ▼
Database records:
  - device_id (laptop)
  - device_id (phone)
  - ip_address (192.168.1.87)
  - paired: true
```

### 3. Cross-Domain Authentication
```
User logs in on cringeproof.com
  │
  ▼
Stores JWT in auth_tokens table
  │
  ▼
Token works on:
  - cringeproof.com
  - soulfra.com
  - alice.cringeproof.com
  - All subdomains

Because they all call same API!
```

## Domain Ownership Model

### Founder Domains (You)
- cringeproof.com
- soulfra.com
- calriven.com
- deathtodata.com

These are "parent domains" that others fork from.

### User Subdomains (Everyone Else)
- alice.cringeproof.com
- bob.soulfra.com
- crypto-nerd.deathtodata.com

Each inherits:
- Base CSS from parent
- Wordmap system
- QR rotation
- Database tables

Then customizes with their own content.

## Implementation Priority

### Phase 1: Unify Backend (Now)
- [x] Single Flask API handles all domains
- [x] Slug system for user pages
- [x] Wordmap → CSS generator
- [ ] Connect to GitHub README

### Phase 2: GitHub Integration
- [ ] Parse README.md on commit
- [ ] Store in domain_wordmaps
- [ ] Generate avatar from wordmap
- [ ] Generate favicon from primary color

### Phase 3: QR Pairing
- [ ] Generate QR codes
- [ ] Mobile scan handler
- [ ] Link devices in database
- [ ] Cross-domain session sync

### Phase 4: Deploy
- [ ] Point cringeproof.com API calls to production backend
- [ ] Point soulfra.com to production backend
- [ ] Wildcard DNS for *.cringeproof.com
- [ ] Test cross-domain auth

## Questions to Answer

1. **Where should soulfra.com point?**
   - Option A: Main portfolio/hub (like soulfra.github.io)
   - Option B: Your personal page (matt.soulfra.com auto-redirects)
   - Option C: Dashboard for all 4 domains

2. **How to handle competing repos?**
   - ~/Desktop/voice-archive vs ~/Desktop/roommate-chat/soulfra-simple/voice-archive
   - Solution: Use roommate-chat as "dev", Desktop as "production deploy"

3. **What's the QR rotation for?**
   - Avatars? Favicons? Both?
   - Needs clarification from you
