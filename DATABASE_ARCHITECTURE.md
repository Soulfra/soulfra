# 🗄️ Database Architecture - What Database Has What

**Last Updated:** 2026-01-03

This documents which database files exist, what they contain, and which routes use them.

---

## 📊 Database Files

### `soulfra.db` (3.8 MB) - **MAIN DATABASE** ✅

**Purpose:** The primary database for the entire platform

**Size:** 3,891,200 bytes (3.8 MB)

**Used By:** Most routes (default database for `get_db()`)

**Tables (90+ tables):**

**Voice & AI Systems:**
- `simple_voice_recordings` (7 recordings with transcriptions)
- `voice_suggestions` (2 suggestions with AI-extracted ideas) ✅ **NEW**
- `voice_suggestion_responses` (SHA256-chained voice responses) ✅ **NEW**
- `ai_persona_stats`
- `ai_engagement_credits`
- `ai_workforce_tasks`

**User & Auth:**
- `users` (user accounts)
- `anonymous_sessions`
- `admin_activity_log`
- `api_keys`
- `api_usage`

**Content & Posts:**
- `posts`
- `comments`
- `subscribers`
- `brand_posts`
- `canvas_pairing`

**Branding & Themes:**
- `brands` (3 brands: soulfra, deathtodata, calriven)
- `brand_assets`
- `brand_licenses`
- `brand_sops`

**QR Codes & Galleries:**
- `qr_codes`
- `qr_vanity_codes`
- `qr_scans`
- `qr_galleries`
- `gallery_items`

**Business & Payments:**
- `affiliate_codes`
- `affiliate_clicks`
- `payment_tiers` (if exists - needs verification)

**Neural Networks:**
- `neural_networks` (4 trained models: calriven, theauditor, deathtodata, soulfra)
- `training_data`

**Other Systems:**
- `battle_sessions` (CringeProof battle system)
- `domain_suggestions`
- `kangaroo_court_cases`
- `learning_modules`
- `practice_rooms`

---

### `database.db` (131 KB) - **LEGACY/SEPARATE DATABASE**

**Purpose:** Separate database for voice domain/wordmap system

**Size:** 131,072 bytes (131 KB)

**Used By:** Voice domain creator routes (specific imports)

**Tables:**
- `simple_voice_recordings` (duplicate? needs migration)
- `user_wordmaps` (256-word voice signatures)
- `domain_wordmaps` (domain-specific wordmaps)
- `domain_contexts`
- `domain_ownership`
- `ownership_rewards`
- `chapter_diffs` (version control)
- `chapter_merge_requests`
- `chapter_snapshots`
- `chapter_version_views`
- `user_chapter_forks`
- `content_generations`
- `users` (separate user table?)

**Status:** Likely needs migration to `soulfra.db` or deprecation

---

### `soulfra_simple.db` (0 bytes) - **EMPTY**

**Purpose:** Unknown (probably test database)

**Status:** Delete this

---

### `test_integration.db` (0 bytes) - **EMPTY**

**Purpose:** Test database for integration tests

**Status:** Keep for testing, ignore in production

---

## 🔗 Which Routes Use Which Database?

### Routes Using `soulfra.db` (MAIN DATABASE)

**Default:** `get_db()` from `database.py` returns `soulfra.db`

```python
# database.py
DB_NAME = os.environ.get('SOULFRA_DB', 'soulfra.db')  # Default: soulfra.db
```

**Routes:**
- ✅ `/voice` - Voice recorder (simple_voice_recordings)
- ✅ `/suggestion-box` - Voice suggestion box (voice_suggestions)
- ✅ `/@<brand>/suggestions` - Brand-specific suggestions
- ✅ `/suggestion/<id>` - Suggestion detail thread
- ✅ `/chat` - AI chat (uses Ollama, no DB persistence)
- ✅ `/status` - System dashboard
- ✅ `/automation` - Automation control center
- ✅ `/admin/canvas` - Image generation
- ✅ `/qr/create` - QR code builder
- ✅ `/galleries` - QR galleries
- ✅ `/admin/docs` - Documentation browser
- All user login/auth routes
- All brand routes
- All QR redirect routes (`/v/<code>`)

---

### Routes Using `database.db` (SEPARATE DATABASE)

**Import Pattern:** Specific imports that override default DB

```python
# Some routes may import from voice_domain_creator or similar
# These likely use database.db explicitly
```

**Routes (suspected):**
- `/voice-domain-creator` routes (if they exist)
- Wordmap building routes (if separate)
- Chapter versioning routes

**Status:** Needs investigation - most routes should migrate to `soulfra.db`

---

## 🎨 Brand Colors & Payment Tiers

### Brand Colors (Implemented)

**Brand-specific gradients:**

```python
@soulfra:
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
  theme: Purple
  tone: Thoughtful, balanced, community-first

@deathtodata:
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)
  theme: Red
  tone: Rebellious, direct, anti-establishment

@calriven:
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%)
  theme: Blue
  tone: Logical, analytical, data-driven
```

**Where Applied:**
- `brand_suggestions.html` - Brand suggestion pages
- `suggestion_thread.html` - Suggestion detail pages
- Dynamic based on `brand.slug` or `thread.original.brand_slug`

---

### Payment Tiers (To Be Verified)

**Concept:** More $ = Slower, deeper, more thoughtful AI responses

**Database Table:** `payment_tiers` (needs verification if it exists in `soulfra.db`)

**Tier Structure (Proposed):**

```
Tier 0: Free (instant, shallow responses)
Tier 1: $5/mo (5-second AI thinking)
Tier 2: $20/mo (30-second deep analysis)
Tier 3: $100/mo (5-minute thoughtful responses)
```

**Implementation Status:** 🔧 Not yet implemented in UI

**Where It Should Show:**
- Badge on suggestion cards showing user's tier
- Color-coded tier indicators
- Response time estimates

**TODO:**
1. Check if `payment_tiers` table exists in `soulfra.db`
2. If not, create schema
3. Add tier badges to `suggestion_thread.html`
4. Add tier filtering/sorting

---

## 📋 Database Schema Access

### View All Tables in soulfra.db

```bash
sqlite3 soulfra.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
```

### View Table Schema

```bash
sqlite3 soulfra.db "PRAGMA table_info(voice_suggestions)"
```

### View Table Counts

```bash
sqlite3 soulfra.db "SELECT
  (SELECT COUNT(*) FROM simple_voice_recordings) as recordings,
  (SELECT COUNT(*) FROM voice_suggestions) as suggestions,
  (SELECT COUNT(*) FROM voice_suggestion_responses) as responses,
  (SELECT COUNT(*) FROM brands) as brands,
  (SELECT COUNT(*) FROM users) as users"
```

---

## 🚨 Known Issues & Confusions

### Issue 1: Duplicate `simple_voice_recordings` Table

**Problem:** `simple_voice_recordings` exists in BOTH:
- `soulfra.db` (7 recordings) ✅ Active
- `database.db` (unknown count) ⚠️ Legacy?

**Solution:** Needs migration or clarification of which is canonical

---

### Issue 2: database.db Purpose Unclear

**Problem:** Not clear why `database.db` exists separately from `soulfra.db`

**Hypothesis:**
- Early prototype used `database.db`
- Later migrated to `soulfra.db`
- Old routes may still reference `database.db`

**Solution:** Audit all imports and migrate to single database

---

### Issue 3: Payment Tiers Not Visible

**Problem:** No tier badges/colors showing on suggestion pages

**Reason:** Either:
1. No `payment_tiers` table exists
2. Table exists but no user tier assignments
3. Frontend not displaying tier data

**Solution:**
1. Check if table exists
2. If not, create schema
3. Add tier display to templates

---

## ✅ Current Working Data

**Voice Suggestions (in soulfra.db):**

```
Suggestion #1:
  Brand: @deathtodata
  Ideas: 3 (Authentic social media, Build trust, Social acceptance)
  SHA256: 5d234bfa76794ee55b83b1f9216957e4...
  Status: living
  Responses: 0

Suggestion #2:
  Brand: @deathtodata
  Ideas: 3 (same as #1 - duplicate)
  SHA256: 5d234bfa76794ee55b83b1f9216957e4...
  Status: living
  Responses: 0
```

**Voice Recordings (in soulfra.db):**

```
Recording #7: (the good one)
  Filename: test_cringeproof_voice.wav
  Transcription: "You know what I really hate? The cringe on social media..."
  Word count: ~559 chars
  Converted to: Suggestion #1, #2
```

---

## 🎯 Quick Reference

### Get Data from Main Database

```python
from database import get_db

db = get_db()  # Returns soulfra.db connection
recordings = db.execute('SELECT * FROM simple_voice_recordings').fetchall()
suggestions = db.execute('SELECT * FROM voice_suggestions').fetchall()
```

### Get Data from Separate Database

```python
import sqlite3

db = sqlite3.connect('database.db')
db.row_factory = sqlite3.Row
wordmaps = db.execute('SELECT * FROM user_wordmaps').fetchall()
```

---

## 🔧 TODO: Database Cleanup

1. **Audit database.db usage** - Find which routes use it
2. **Migrate to single database** - Move all data to `soulfra.db`
3. **Delete empty databases** - Remove `soulfra_simple.db`
4. **Document payment tiers** - Verify if table exists, create schema
5. **Add tier display** - Show tier badges on suggestion pages
6. **Create DATABASE_MIGRATION.md** - Document migration process

---

## 🔷 The Diamond Architecture & Database

**How voice suggestions flow through the database:**

```
Voice Recording (simple_voice_recordings)
        ↓
Transcription (Whisper)
        ↓
Idea Extraction (Ollama)
        ↓
Voice Suggestion (voice_suggestions)
        ↓ SHA256 hash
    ┌───────────────────┐
    │                   │
@soulfra          @deathtodata
(Purple)             (Red)
    │                   │
    └───────────────────┘
            ↓
    Community Responses
(voice_suggestion_responses)
            ↓
    SHA256 Chain Verification
```

**All stored in `soulfra.db` - the single source of truth.**

---

## 💡 Summary

**Use `soulfra.db` for everything** unless you have a specific reason to use `database.db`.

**Default assumption:** All routes use `soulfra.db` via `get_db()`.

**Payment tiers:** Concept exists, implementation pending.

**Brand colors:** ✅ Working (@soulfra purple, @deathtodata red, @calriven blue)

**Next steps:** Audit database.db, verify payment tiers, add tier display to UI.
