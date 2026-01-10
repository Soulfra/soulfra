# 🎨 Creative Onboarding + File Import + @Routing - Complete Flow

**Date Created:** 2025-12-28
**Status:** System Built & Ready

---

## 🎯 What This Is

A complete system that connects:
1. **GitHub OAuth** → API keys (github_faucet.py) ✅ BUILT
2. **Creative challenges** → Access tiers (custom_captcha.js) ✅ BUILT
3. **File imports** → txt/md/html/doc (file_importer.py) ⏳ NEXT
4. **@Routing** → Brand folders (folder_router.py) ⏳ NEXT
5. **Database flow** → Content pipeline (content_pipeline.py) ⏳ NEXT

---

## 📊 The Complete Flow

```
NEW USER ARRIVES
       ↓
┌──────────────────┐
│  Choose Method   │
└────────┬─────────┘
         │
         ├→ Option A: Connect GitHub
         │  1. Click "Connect GitHub"
         │  2. OAuth flow → GitHub → Back
         │  3. Faucet generates API key
         │  4. Tier based on repos/followers
         │  5. Access granted!
         │
         ├→ Option B: Creative Challenge
         │  1. Click "Creative Challenge"
         │  2. Choose challenge type:
         │     • Draw something (OCR)
         │     • Write poem (Ollama)
         │     • Solve puzzle (Ollama)
         │     • Upload file
         │  3. Submit answer
         │  4. AI validates
         │  5. Access granted!
         │
         ↓
┌────────────────────┐
│  ACCESS GRANTED    │
│  API Key: sk_xxx   │
│  Tier: 2           │
└─────────┬──────────┘
          │
          ├→ Import Files
          │  Supported: txt, md, mdx, html, htm, doc, docx, json, yaml, csv
          │
          │  Example: Upload privacy-guide.md
          │  ↓
          │  System:
          │  1. Detects markdown
          │  2. Parses frontmatter
          │  3. Extracts metadata
          │  4. Routes to @brand/category
          │  5. Saves to database
          │  6. Generates QR code
          │  7. Exports static site
          │
          ↓
┌──────────────────────────────┐
│  FILE SYSTEM                 │
│                              │
│  brands/                     │
│    @soulfra/                 │
│      blog/                   │
│        security.md           │
│      docs/                   │
│        api.html              │
│    @deathtodata/             │
│      privacy/                │
│        encryption.txt        │
│    @yourname/                │
│      guides/                 │
│        welcome.md            │
└──────────┬───────────────────┘
           │
           ├→ @ Routing
           │  @soulfra/blog/security → /brands/soulfra/blog/security
           │  @deathtodata/privacy → /brands/deathtodata/privacy
           │
           ↓
┌─────────────────────────┐
│  DATABASE               │
│                         │
│  posts:                 │
│    id=42                │
│    title="Guide"        │
│    route="@user/blog"   │
│                         │
│  file_routes:           │
│    route="@user/blog"   │
│    brand="deathtodata"  │
│    file_path="/..."     │
│                         │
│  api_keys:              │
│    key="sk_github_xxx"  │
│    tier=2               │
└──────────┬──────────────┘
           │
           ├→ Scripts Process
           │  1. md → HTML
           │  2. Generate QR codes
           │  3. Create pSEO pages
           │  4. Export static site
           │  5. Update sitemap
           │
           ↓
┌────────────────────┐
│  OUTPUT            │
│  • Live website    │
│  • Static export   │
│  • API endpoints   │
│  • QR galleries    │
└────────────────────┘
```

---

## 🔥 What's Been Built

### 1. GitHub Faucet (`github_faucet.py`) ✅ COMPLETE

**500+ lines** of GitHub OAuth integration.

**Features:**
- OAuth flow: Soulfra → GitHub → Back with token
- Fetch GitHub profile, repos, stars, followers
- Generate API keys: `sk_github_username_randomhex`
- Tier calculation based on activity
- Rate limiting: 1 key per GitHub account
- Key refresh: Every 30 days
- CLI tools for validation and listing

**Tiers:**
- **Tier 1**: <10 repos → Basic access
- **Tier 2**: 10-50 repos → File imports
- **Tier 3**: 50+ repos → API access
- **Tier 4**: 100+ repos + 50+ followers → Brand forking

**Database:**
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    api_key TEXT UNIQUE,
    github_username TEXT UNIQUE,
    github_email TEXT,
    github_repos INTEGER,
    github_followers INTEGER,
    tier INTEGER,
    created_at TIMESTAMP,
    is_active BOOLEAN
);
```

**Usage:**
```bash
# Initialize tables
python3 github_faucet.py --init

# Validate key
python3 github_faucet.py --validate sk_github_octocat_abc123

# List all keys
python3 github_faucet.py --list
```

---

### 2. Custom CAPTCHA (`custom_captcha.js`) ✅ COMPLETE

**650+ lines** of Ollama-powered CAPTCHA.

**Features:**
- Math challenges (addition, hex, etc.)
- Text challenges (colors, days, etc.)
- Logic challenges (sequences, patterns)
- Custom prompts from brand.json
- Ollama validates answers (flexible)
- No Google, no tracking
- Beautiful glassmorphism UI

**Challenge Types:**
```javascript
const challenges = {
  math: 'What is 5 + 7?',
  hex: 'What is 15 in hexadecimal?',
  color: 'Name a primary color',
  day: 'What day comes after Monday?',
  sequence: 'What comes next: 2, 4, 6, __?',
  custom: 'Your custom prompt from brand.json'
}
```

**Integration:**
```html
<!-- Include script -->
<script src="custom_captcha.js"></script>

<!-- Add container -->
<div id="challenge-captcha"></div>

<script>
// Initialize
const captcha = new OllamaCaptcha('challenge-captcha', {
    ollamaHost: 'http://localhost:11434',
    model: 'llama2',
    customPrompts: [
        "Draw 'privacy' and we'll verify with OCR",
        "Write a haiku about data",
        "What is 2+2 in hex?"
    ]
});

// Listen for validation
document.getElementById('challenge-captcha').addEventListener('captcha-validated', (e) => {
    console.log('Challenge completed!', e.detail);
    // Grant access, show next step, etc.
});
</script>
```

---

### 3. Static Chat (`static_chat.html`) ✅ COMPLETE

**520+ lines** of pure HTML/JS Ollama chat.

**Features:**
- No server needed (just open in browser)
- Direct Ollama API calls
- localStorage for history
- Model selector
- Context management
- Mobile-friendly
- Beautiful UI

**Usage:**
```bash
# Just open it!
open static_chat.html

# Or on phone (with start_flask_lan.sh running)
http://192.168.1.74:8080/static_chat.html
```

---

### 4. Brand Template (`brand_template/`) ✅ COMPLETE

**Self-contained deployable folder.**

**Structure:**
```
brand_template/
├── index.html       # Static chat interface
├── brand.json       # Configuration
├── start.sh         # LAN launch script
└── README.md        # Deployment guide
```

**Deploy to:**
- GitHub Pages (free)
- Netlify (free, drag & drop)
- Vercel (free, CLI)
- AWS S3 (~$0.50/month)
- Any static host

---

### 5. Federation Protocol (`federation_protocol.md`) ✅ COMPLETE

**500+ lines** of brand-to-brand communication spec.

**Features:**
- Like email: each brand independent
- REST API for brand communication
- Message signing & verification
- Peer whitelisting
- Knowledge sharing
- Consensus building

**Example:**
```
@soulfra/blog/security mentions @deathtodata/privacy/vpn

Soulfra server → DeathToData server
POST /api/federation/receive
{
  "from": "soulfra.com",
  "to": "deathtodata.org",
  "message": "How do I encrypt my files?",
  "signature": "..."
}

DeathToData's Ollama responds → Back to Soulfra → User
```

---

## 🏗️ What's Next To Build

### 6. File Importer (`file_importer.py`) ⏳ NEXT

**Purpose:** Import any file format into the system.

**Supported Formats:**
```python
FORMATS = {
    'text': ['txt', 'rtf'],
    'markdown': ['md', 'mdx', 'markdown'],
    'html': ['html', 'htm'],
    'doc': ['doc', 'docx'],  # Convert to markdown
    'data': ['json', 'yaml', 'toml', 'csv'],
    'code': ['py', 'js', 'ts', 'jsx', 'tsx']
}
```

**Process:**
1. User uploads file
2. Detect format
3. Convert to markdown (if needed)
4. Parse frontmatter metadata
5. Route to @brand/category
6. Save to database
7. Generate QR code
8. Export to static site

**API Endpoint:**
```python
POST /api/import

Body:
{
  "file": <file upload>,
  "brand": "deathtodata",
  "category": "privacy"
}

Response:
{
  "status": "success",
  "route": "@yourname/privacy/encryption",
  "url": "https://deathtodata.org/yourname/privacy/encryption",
  "qr_code": "data:image/png;base64,..."
}
```

---

### 7. Folder Router (`folder_router.py`) ⏳ NEXT

**Purpose:** Route files using @brand syntax.

**Route Format:**
```
@brand/category/subcategory/file.ext

Examples:
@soulfra/blog/security/encryption.md
@deathtodata/guides/vpn/setup.html
@calriven/architecture/databases/postgres.txt
```

**Database:**
```sql
CREATE TABLE file_routes (
    id INTEGER PRIMARY KEY,
    route TEXT UNIQUE,           -- @soulfra/blog/post.md
    brand TEXT,                  -- soulfra
    category TEXT,               -- blog
    subcategory TEXT,            -- NULL or subfolder
    filename TEXT,               -- post.md
    file_path TEXT,              -- /absolute/path/to/file
    owner_user_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);
```

**URL Rewriting:**
```
User types: @soulfra/blog/security
↓
System routes to: /brands/soulfra/blog/security
↓
Serves file: brands/soulfra/blog/security.html
```

---

### 8. Content Pipeline (`content_pipeline.py`) ⏳ NEXT

**Purpose:** Process imported files through full pipeline.

**Pipeline Steps:**
1. **Validate** - Check format, size, content
2. **Convert** - Normalize to markdown
3. **Enrich** - Add metadata, images, tags
4. **Route** - Assign @brand/category path
5. **Database** - Save metadata to posts table
6. **Generate** - QR codes, avatars, pSEO pages
7. **Export** - Static site, API endpoints

**Example:**
```python
from content_pipeline import ContentPipeline

pipeline = ContentPipeline()

# Process uploaded file
result = pipeline.process_file(
    file_path='uploads/privacy-guide.md',
    brand='deathtodata',
    category='privacy',
    owner_user_id=15
)

# Returns:
{
    'route': '@yourname/privacy/privacy-guide',
    'url': 'https://deathtodata.org/yourname/privacy/privacy-guide',
    'qr_code': '/static/qr/privacy-guide.png',
    'pseo_pages': 50,
    'static_export': '/output/deathtodata/yourname/privacy/privacy-guide.html'
}
```

---

## 🎨 Creative Onboarding Options

### Option 1: GitHub OAuth
```
1. User clicks "Connect GitHub"
2. Redirected to GitHub
3. Authorize Soulfra app
4. GitHub sends code → Soulfra
5. Soulfra exchanges code for token
6. Fetch GitHub profile
7. Generate API key
8. Calculate tier
9. Redirect to workspace
```

### Option 2: Draw Challenge
```
1. User clicks "Draw Challenge"
2. Prompt: "Draw the word PRIVACY"
3. User draws on canvas
4. Submit → OCR validates
5. If matches "privacy" → Access granted
6. Tier 1 access
```

### Option 3: Write Challenge
```
1. User clicks "Write Challenge"
2. Prompt: "Write a haiku about data"
3. User submits poem
4. Ollama judges creativity
5. If score > 7/10 → Access granted
6. Tier 1 access
```

### Option 4: Solve Puzzle
```
1. User clicks "Puzzle Challenge"
2. Ollama generates: "What is 2+2 in hexadecimal?"
3. User answers: "4" or "0x4"
4. Ollama validates (flexible)
5. If correct → Access granted
6. Tier 1 access
```

### Option 5: Upload File
```
1. User clicks "Upload to Join"
2. Upload any file (txt, md, html, etc.)
3. System validates format
4. If valid → Import file
5. Access granted + File in system
6. Tier 2 access (file importer unlocked)
```

---

## 📦 Database Schema

### api_keys (✅ Built)
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    api_key TEXT UNIQUE,
    github_username TEXT UNIQUE,
    github_email TEXT,
    github_repos INTEGER,
    github_followers INTEGER,
    tier INTEGER,
    created_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN
);
```

### file_routes (⏳ Next)
```sql
CREATE TABLE file_routes (
    id INTEGER PRIMARY KEY,
    route TEXT UNIQUE,
    brand TEXT,
    category TEXT,
    subcategory TEXT,
    filename TEXT,
    file_path TEXT,
    owner_user_id INTEGER,
    file_type TEXT,
    file_size INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);
```

### challenge_attempts (⏳ Next)
```sql
CREATE TABLE challenge_attempts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    challenge_type TEXT,  -- 'draw', 'write', 'puzzle', 'upload'
    challenge_prompt TEXT,
    user_answer TEXT,
    ai_score REAL,        -- 0-10
    passed BOOLEAN,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🚀 Quick Start Guide

### 1. Set Up GitHub OAuth

```bash
# Create GitHub OAuth App:
# https://github.com/settings/developers
# Get CLIENT_ID and CLIENT_SECRET

# Set environment variables
export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_client_secret
export GITHUB_REDIRECT_URI=http://localhost:5001/github/callback

# Initialize database
python3 github_faucet.py --init
```

### 2. Test GitHub Faucet

```bash
# Start Flask app
python3 app.py

# Visit: http://localhost:5001/github/connect
# Complete OAuth flow
# Get API key

# Validate key
python3 github_faucet.py --validate sk_github_username_abc123
```

### 3. Test Creative Challenges

```html
<!-- Open in browser -->
<script src="custom_captcha.js"></script>
<div id="test-challenge"></div>
<script>
const captcha = new OllamaCaptcha('test-challenge', {
    model: 'llama2',
    customPrompts: ['What is 2+2 in hex?']
});
</script>
```

### 4. Test Static Chat

```bash
# Make sure Ollama running
ollama serve

# Open static chat
open static_chat.html
```

### 5. Deploy Brand Template

```bash
# Copy template
cp -r brand_template/ mybrand/

# Edit brand.json
# Deploy to GitHub Pages/Netlify/Vercel

# Done!
```

---

## 📚 File Summary

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `github_faucet.py` | 500+ | ✅ Built | GitHub OAuth → API keys |
| `custom_captcha.js` | 650+ | ✅ Built | Ollama-powered challenges |
| `static_chat.html` | 520+ | ✅ Built | Pure HTML Ollama chat |
| `brand_template/` | Full | ✅ Built | Deployable brand folder |
| `federation_protocol.md` | 500+ | ✅ Built | Brand-to-brand comms |
| `file_importer.py` | TBD | ⏳ Next | Multi-format file import |
| `folder_router.py` | TBD | ⏳ Next | @brand routing system |
| `content_pipeline.py` | TBD | ⏳ Next | Process imported files |

---

## 🎯 Next Steps

1. **Build file_importer.py** - Import txt/md/html/doc files
2. **Build folder_router.py** - Route using @brand/path syntax
3. **Build content_pipeline.py** - Process files through database → scripts → output
4. **Add Flask routes** - /import, /github/oauth, /challenge
5. **Test end-to-end** - GitHub OAuth → Import file → @Route → Export

---

**Generated 2025-12-28 by Soulfra**

*"From GitHub keys to file imports to federated brands - all connected."*
