# Soulfra System Inventory

Complete system inventory and health status for the Soulfra platform.

**Generated:** 2025-12-25
**Status:** ✅ Operational

---

## Quick Summary

This document provides a complete inventory of what's real vs test data, which templates work, and how the system is organized.

### The TL;DR:
- **You are the only real user** (`admin`)
- **4 core AI personas** are real (calriven, deathtodata, theauditor, soulfra)
- **10 test users** are fake and can be cleaned up
- **78 templates** total: 69 in use, 12 unused, 3 missing
- **81+ routes** organized across the platform
- **Plugin system** working with auto-discovery

---

## Real vs Fake Data

### ✅ REAL USERS (Keep These)
| Username | Type | Created | Purpose |
|----------|------|---------|---------|
| admin | Human | 2025-12-20 | Your account (the only real person) |
| calriven | AI | 2025-12-20 | Core AI persona |
| deathtodata | AI | 2025-12-20 | Core AI persona |
| theauditor | AI | 2025-12-21 | Core AI persona |
| soulfra | AI | 2025-12-20 | Core AI persona |

### ❌ FAKE USERS (Test Data - Can Delete)
| Username | Type | Created | Content |
|----------|------|---------|---------|
| alice | Human | 2025-12-21 | 4 posts, 1 comment |
| philosopher_king | Human | 2025-12-22 | 2 posts, 0 comments |
| data_skeptic | Human | 2025-12-22 | 2 posts, 0 comments |
| science_explorer | Human | 2025-12-22 | 1 post, 0 comments |
| culture_critic | Human | 2025-12-22 | 1 post, 0 comments |
| freedom_builder | Human | 2025-12-22 | 1 post, 0 comments |
| ocean-dreams | AI | 2025-12-22 | 3 posts, 0 comments |
| ollama | AI | 2025-12-22 | 1 post, 0 comments |
| soulassistant | AI | 2025-12-23 | 0 posts, 1 comment |
| testbrand-auto | AI | 2025-12-23 | 0 posts, 0 comments |

**Total Fake Content:**
- 15 posts
- 2 comments
- 10 user accounts

**After Cleanup:**
- 5 users (you + 4 AI personas)
- 23 posts
- 35 comments

### How to Clean Up Test Data

```bash
# See what would be deleted (safe)
python3 clean_test_data.py --dry-run

# Actually delete test data (requires confirmation)
python3 clean_test_data.py

# Keep all AI personas, only delete human test users
python3 clean_test_data.py --keep-all-ai
```

---

## Template Health Status

**Overall Health:** ⚠️ Warning (3 missing templates)

| Metric | Count |
|--------|-------|
| Total Templates | 78 |
| Used Templates | 69 |
| Unused Templates | 12 |
| Missing Templates | 3 |

### ❌ Missing Templates (Need to Create)
These templates are referenced in code but don't exist:

1. `ai_network_visualize.html` - Used in `ai_network_visualize()` at app.py:2099
2. `ai_persona_detail.html` - Used in `ai_persona_detail()` at app.py:2137
3. `brand_qr_stats.html` - Used in `brand_qr_stats()` at app.py:2193

### ⚪ Unused Templates (May be Legacy)
These templates exist but aren't being used:

1. `admin_api_keys.html`
2. `admin_brands.html`
3. `admin_dashboard.html`
4. `admin_emails.html`
5. `admin_subscribers.html`
6. `signup.html`
7. `status.html`
8. `cringeproof/results.html`
9. `games/analysis_results_v1_dinghy.html`
10. `games/review_game_v1_dinghy.html`
11. `games/share_button_v1_dinghy.html`
12. `base.html` (false positive - used via {% extends %})

### How to Check Template Health

```bash
# Full health check
python3 check_templates.py

# Show only unused templates
python3 check_templates.py --unused

# Brief summary
python3 check_templates.py --summary
```

---

## Current Database State

**Last Updated:** 2025-12-25

| Metric | Count |
|--------|-------|
| Total Users | 15 |
| Human Users | 7 |
| AI Personas | 8 |
| Total Posts | 38 |
| Total Comments | 37 |
| API Calls (30d) | 211 |
| Newsletter Subscribers | 0 |

---

## Routes & Features

**Total Routes:** ~81 endpoints

### Main Feature Categories:

1. **Content & Posts** - Blog posts, categories, tags, live feed
2. **Theme System** - Shipyard, brands, tier progression
3. **Users & Souls** - Profiles, souls, similar users
4. **AI & Machine Learning** - Training, predictions, reasoning
5. **Brand Builder** - Conversational brand creation
6. **Admin** - Dashboard, subscribers, automation
7. **API** - Health check, posts, reasoning threads
8. **Utilities** - RSS, sitemap, QR codes

See `ROUTES_MAP.md` for complete route documentation.

---

## Plugin System

**Status:** ✅ Working

Plugins are auto-loaded from the `features/` directory.

### How Plugin System Works:
1. Create folder in `features/<plugin_name>/`
2. Add `__init__.py` that exports `blueprint`
3. Add `feature.yaml` with metadata
4. Plugin auto-registers on app startup
5. Appears in Hub if `visible_in_hub: true`
6. Appears in nav if `visible_in_nav: true`

### Plugin Metadata Example:
```yaml
name: My Cool Feature
description: What this feature does
icon: 🎮
category: Games
url_prefix: /my-feature
visible_in_hub: true
visible_in_nav: true
author: Your Name
version: 1.0.0
```

### View Loaded Plugins:
- `/features` - Plugin dashboard with metadata table
- `/hub` - Hub showing all features including plugins

---

## System Health Pages

### Visual Dashboards:
- **`/sitemap`** - Interactive route map with health status
- **`/hub`** - Unified feature hub with stats
- **`/features`** - Plugin metadata dashboard
- **`/dashboard`** - Live AI predictions
- **`/status`** - System health metrics

### Documentation:
- **`ROUTES_MAP.md`** - Complete route reference
- **`SYSTEM_INVENTORY.md`** - This file (system overview)

---

## Your "Roommate" Concept

Each user gets their own blog-like space:

- **`/user/admin`** - Your profile and posts
- **`/user/calriven`** - Calriven's profile and posts
- **`/user/deathtodata`** - Deathtodata's profile and posts
- etc.

The "roommates" are the AI personas. Each one:
- Has their own user profile
- Generates content in their voice
- Has a "soul" (personality visualization)
- Can be queried via API

---

## What Works Right Now

### ✅ Fully Functional:
- User profiles (`/user/<username>`)
- Blog posts and comments
- AI comment generation
- Brand system and marketplace
- Plugin auto-loading
- API endpoints with authentication
- Admin dashboard
- Newsletter system
- RSS feeds
- Theme system

### ⚠️ Needs Attention:
- 3 missing templates (see above)
- Test data needs cleanup
- Some unused templates to review

### 📚 Well Documented:
- `/sitemap` - Visual map
- `ROUTES_MAP.md` - Complete route reference
- `clean_test_data.py` - Data cleanup tool
- `check_templates.py` - Template health checker

---

## Next Steps (If Desired)

### Immediate (Fix Warnings):
1. Create 3 missing templates OR remove routes that reference them
2. Run `python3 clean_test_data.py` to remove fake users
3. Review 12 unused templates - delete or use them

### Short Term (Enhancements):
1. Add more AI personas with unique voices
2. Create more content under your admin account
3. Build custom plugins in `features/` directory
4. Set up newsletter automation

### Long Term (Growth):
1. Invite real users (each gets their own `/user/<username>` space)
2. Train ML models on real data
3. Export and share brands
4. Build API ecosystem with freelancers

---

## How to Navigate Your System

```bash
# View system health
open http://localhost:5001/sitemap

# View all features
open http://localhost:5001/hub

# View loaded plugins
open http://localhost:5001/features

# Your profile
open http://localhost:5001/user/admin

# AI persona profiles
open http://localhost:5001/user/calriven
open http://localhost:5001/user/deathtodata
open http://localhost:5001/user/theauditor
open http://localhost:5001/user/soulfra

# Admin dashboard
open http://localhost:5001/admin

# Check templates
python3 check_templates.py

# Clean test data
python3 clean_test_data.py --dry-run
```

---

## Summary

**You have a working AI-powered blog platform where:**
- You (admin) are the only real human
- 4 AI personas generate content in different voices
- Each user/persona has their own profile page
- Plugins auto-load from `features/` directory
- Templates and routes are health-checked
- Test data can be cleaned up with one command

**The system is operational but has:**
- 10 fake test users that can be deleted
- 3 missing templates that need to be created
- 12 unused templates to review

**Everything is documented in:**
- `ROUTES_MAP.md` - All routes
- `SYSTEM_INVENTORY.md` - This file
- `/sitemap` - Visual interface
- `/hub` - Feature hub

---

**Need help?** Check the documentation pages or run the health check scripts.
