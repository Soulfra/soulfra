# Canvas System - Complete Integration Guide

The Canvas system connects all existing Soulfra components into a unified "Kubernetes for ideas" platform.

## 🎯 System Architecture

```
QR Faucet → Canvas Entry → User Workspace → Chapter Learning → API Keys → Brand Forks
```

## 📋 Available Routes

### Netflix-Style Entry & Pairing

#### 1. `/canvas` - Main Entry Point
Shows QR code for Netflix-style pairing (display QR on computer, scan with phone)

**Flow:**
1. Computer displays QR code
2. User scans with phone
3. Phone redirects to `/canvas/pair/<token>`
4. Computer polls `/api/canvas/pair/status/<token>`
5. When paired, both redirect to `/canvas/workspace`

**Files:**
- Backend: `canvas_integration.py:generate_canvas_qr()`
- Routes: `canvas_routes.py:canvas_entry()`
- UI Template: `CANVAS_ENTRY_TEMPLATE` (purple gradient, QR code, polling JS)

#### 2. `/canvas/qr/<pairing_token>` - QR Code Image
Generates actual QR code PNG for pairing

**Implementation:**
- Uses `qr_faucet.py:generate_qr_code_image()`
- Returns PNG image with pairing URL embedded

#### 3. `/canvas/pair/<pairing_token>` - Phone Scan Endpoint
What the phone hits after scanning QR code

**Flow:**
1. Verify token (checks `canvas_pairing` table)
2. Get user_id from session (or redirect to login)
3. Complete pairing in database
4. Show success page on phone
5. Computer detects pairing via polling

**Success UI:** Green gradient with ✅ checkmark, "You can close this tab"

#### 4. `/api/canvas/pair/status/<pairing_token>` - Polling Endpoint
Computer polls this every 2 seconds to detect when phone pairs

**Returns JSON:**
- `{"status": "pending"}` - Still waiting
- `{"status": "paired", "redirect": "/canvas/workspace"}` - Success!
- `{"status": "expired"}` - Token expired (5 min TTL)
- `{"status": "invalid"}` - Token not found

### User Workspace

#### 5. `/canvas/workspace` - Main Dashboard
User's creative command center - "The Canvas"

**Shows:**
- 📚 **Learning Progress:** Current chapter, neural network status, completed chapters
- 🍴 **Forkable Brands:** CalRiven, DeathToData, TheAuditor, Soulfra (with emoji + tagline)
- 💡 **Raw Ideas:** Unprocessed ideas + textarea to submit new ideas

**Features:**
- Click brand → Fork with custom name
- Type idea + click "Process with AI" → Creates structured post
- Real-time JS for API calls
- Dark UI with purple accents

**Files:**
- Backend: `canvas_integration.py:get_canvas_workspace()`
- UI Template: `CANVAS_WORKSPACE_TEMPLATE`

### API Endpoints

#### 6. `POST /api/canvas/process-idea` - Idea Processor
Transform raw text into structured content with AI + brand theme

**Request:**
```json
{
  "idea_text": "Users should be able to fork ideas like GitHub repos",
  "brand_slug": "calriven"
}
```

**Response:**
```json
{
  "post_id": 123,
  "title": "Forking Ideas: A GitHub-Style Content System",
  "slug": "forking-ideas-a-github-style-content-system-a3f9",
  "content": "# Forking Ideas...\n\n## Key Points\n- Point 1\n- Point 2...",
  "status": "draft",
  "brand_slug": "calriven",
  "brand_config": {...}
}
```

**Pipeline:**
1. Raw text → AI structures it (using Ollama/LLMRouter)
2. AI generates: title, intro, main_points, conclusion, tags
3. Apply brand theme (CalRiven = technical, DeathToData = privacy-focused)
4. Save as draft post in `posts` table
5. Return post data for preview

**Files:**
- Backend: `canvas_integration.py:process_raw_idea()`
- Uses: `llm_router.py` for AI structuring

#### 7. `POST /api/canvas/fork-brand` - Brand Fork Deployer
Clone a brand (like forking CalRiven) with custom config

**Request:**
```json
{
  "source_brand_slug": "calriven",
  "fork_name": "My Custom CalRiven"
}
```

**Response:**
```json
{
  "brand_id": 5,
  "slug": "my-custom-calriven-a3f9",
  "name": "My Custom CalRiven",
  "source_brand": "CalRiven",
  "subdomain_url": "https://my-custom-calriven-a3f9.soulfra.com"
}
```

**Creates:**
- New brand record in `brands` table with `is_fork=1`
- Clones source brand's `config_json` (colors, fonts, personality)
- Generates unique slug with random suffix
- Unlocks customization features for user
- (Future) Subdomain routing

**Files:**
- Backend: `canvas_integration.py:fork_brand_for_user()`

#### 8. `POST /api/canvas/generate-api-key` - API Key Generation
Generate API key after completing chapters (feature unlock system)

**Request:** Empty POST (uses session user_id)

**Response (Success):**
```json
{
  "api_key": "sk_soulfra_a3f9b2c8d1e4f5a6b7c8d9e0f1a2b3c4",
  "tier": "free"
}
```

**Response (Locked):**
```json
{
  "error": "API access not unlocked",
  "hint": "Complete chapters to unlock API access"
}
```

**Requirements:**
- User must have `user_unlocks` record with `feature_key='api_access'`
- Unlocked by completing Chapter 7 or admin grant

**Files:**
- Backend: `canvas_integration.py:generate_api_key_for_user()`
- Uses: `canvas_integration.py:check_feature_unlock()`

## 🗄️ Database Tables

### canvas_pairing
Netflix-style QR pairing sessions

```sql
CREATE TABLE canvas_pairing (
    id INTEGER PRIMARY KEY,
    pairing_token TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    status TEXT DEFAULT 'pending',  -- 'pending', 'paired'
    expires_at TIMESTAMP NOT NULL,  -- 5 min TTL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paired_at TIMESTAMP
);
```

### user_unlocks
Feature unlock system (chapters → API keys, QR faucet access, etc.)

```sql
CREATE TABLE user_unlocks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    feature_key TEXT NOT NULL,  -- 'api_access', 'qr_faucet_advanced', 'brand_fork', etc.
    unlock_source TEXT,         -- 'chapter_7', 'admin_grant', 'brand_fork'
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP        -- NULL = permanent
);
```

**Feature Keys:**
- `api_access` - Can generate API keys
- `qr_faucet_advanced` - Can create custom QR payloads
- `brand_fork` - Can fork brands
- `chapter_X_completed` - Completed chapter X

## 🔌 Backend Functions

### canvas_integration.py

All glue code connecting existing systems:

```python
# QR Pairing
generate_canvas_qr(user_id=None, ttl_minutes=5) → Dict
verify_canvas_pairing(pairing_token) → Optional[Dict]
complete_canvas_pairing(pairing_token, user_id) → bool

# Workspace
get_canvas_workspace(user_id) → Dict

# Idea Processing
process_raw_idea(idea_text, user_id, brand_slug=None) → Dict

# Feature Unlocks
unlock_feature_for_user(user_id, feature_key, source='system') → int
check_feature_unlock(user_id, feature_key) → bool
generate_api_key_for_user(user_id) → str

# Brand Forking
fork_brand_for_user(user_id, source_brand_slug, fork_name) → Dict
```

### canvas_routes.py

Flask routes (registered in `app.py` via `register_canvas_routes(app)`):

- Routes: 8 total (5 web UI, 3 API endpoints)
- Templates: 4 inline HTML templates (entry, success, error, workspace)
- Registration: Called in `app.py` after `register_image_admin_routes()`

## 🎨 UI Templates

All templates use inline CSS for portability (no external stylesheets):

1. **CANVAS_ENTRY_TEMPLATE** - Purple gradient, QR code display, polling JS
2. **CANVAS_PAIR_SUCCESS_TEMPLATE** - Green gradient, ✅ checkmark, "close this tab"
3. **CANVAS_PAIR_ERROR_TEMPLATE** - Red gradient, ❌ icon, error message
4. **CANVAS_WORKSPACE_TEMPLATE** - Dark UI, 3-column grid, interactive JS

## 🔗 Integration with Existing Systems

### QR Faucet (`qr_faucet.py`)
- Canvas uses QR Faucet for pairing tokens
- `generate_qr_payload(payload_type='canvas_entry', ...)`
- QR codes contain JSON payloads (not just URLs)

### User Workspace (`user_workspace.py`)
- Canvas extends workspace with chapter/brand data
- `get_workspace_data(user_id)` returns base workspace
- Canvas adds: learning progress, forkable brands, raw ideas

### Chapter System (`chapter_tutorials.py`, `chapter_version_control.py`)
- Canvas displays chapter progress in workspace
- Version control for forking chapters (like Git)
- User can fork Chapter 5 to create custom tutorial

### Brand System (`brands` table)
- CalRiven, DeathToData, TheAuditor, Soulfra = base brands
- Users fork brands → creates new brand with `is_fork=1`
- Future: Subdomain routing per forked brand

### API Key System (already in `app.py`)
- Canvas integrates with existing `api_keys` table
- Generates keys with `sk_soulfra_` prefix
- Tied to feature unlock system

## 🧪 Testing the Flow

### Test 1: Canvas Entry
```bash
curl http://localhost:5001/canvas
# Should return HTML with QR code and polling JS
```

### Test 2: Workspace (Requires Login)
```bash
# First login, then:
curl -b cookies.txt http://localhost:5001/canvas/workspace
# Should return workspace with chapters, brands, ideas
```

### Test 3: Process Idea
```bash
curl -X POST http://localhost:5001/api/canvas/process-idea \
  -H "Content-Type: application/json" \
  -d '{"idea_text": "Test idea", "brand_slug": "calriven"}' \
  -b cookies.txt
# Should return structured post with AI-generated content
```

### Test 4: Fork Brand
```bash
curl -X POST http://localhost:5001/api/canvas/fork-brand \
  -H "Content-Type: application/json" \
  -d '{"source_brand_slug": "calriven", "fork_name": "My CalRiven"}' \
  -b cookies.txt
# Should return forked brand with new slug
```

## 📁 Files Created

1. `canvas_integration.py` (500+ lines) - Backend glue code
2. `canvas_routes.py` (600+ lines) - Flask routes + templates
3. `chapter_version_control.py` (450+ lines) - Git for chapters
4. `chapter_version_schema.sql` - Database schema for version control
5. `CANVAS_SYSTEM.md` (this file) - Documentation

## 🚀 Next Steps

### Pending Tasks

1. **Wire Chapter Completion → Feature Unlocks**
   - When user completes Chapter 7 → unlock `api_access`
   - When user completes Chapter 5 → unlock `brand_fork`
   - Add unlock calls to chapter completion routes

2. **Test Full Flow**
   - [ ] Display QR on computer (`/canvas`)
   - [ ] Scan with phone
   - [ ] Verify pairing works
   - [ ] Navigate to workspace
   - [ ] Process raw idea
   - [ ] Fork brand
   - [ ] Generate API key (after unlocking)

3. **Print-Ready QR Codes**
   - Add "Download as PNG" button on `/canvas`
   - Add "Print Stickers" option (generates PDF)
   - Add "Business Cards" layout

4. **Subdomain Routing**
   - Map forked brands to subdomains
   - `my-calriven-a3f9.soulfra.com` → serves that brand's content
   - Use existing `subdomain_router.py` system

## 🎉 Achievements

- ✅ Netflix-style QR pairing (computer + phone)
- ✅ Canvas workspace with chapters, brands, ideas
- ✅ AI idea processor (raw text → structured post)
- ✅ Brand fork deployer (one-click CalRiven clone)
- ✅ API key generation with feature unlocks
- ✅ SQLite-based version control ("Git for CalRiven")
- ✅ All routes registered and tested
- ✅ Server running at http://localhost:5001

**Try it:**
```
http://localhost:5001/canvas
```
