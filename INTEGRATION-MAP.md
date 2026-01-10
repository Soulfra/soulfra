# 🗺️ Soulfra Integration Map - How Everything Connects

**Created:** January 2, 2026
**Answer to:** *"its like in my head we're trying to pair siri up (or my website or github?) and then ollama and then whatever else? and apis?"*

---

## 📊 The Full System - Visual Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ENTRY POINTS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Website (browser)     Siri/Voice       GitHub OAuth           │
│       │                    │                  │                │
│       │                    │                  │                │
│       └────────────────────┴──────────────────┘                │
│                            │                                    │
│                            ▼                                    │
│                    ┌───────────────┐                           │
│                    │   Flask App   │                           │
│                    │  Port 5001    │                           │
│                    └───────┬───────┘                           │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Database   │    │    Ollama    │    │   GitHub     │
│  (SQLite)    │    │  (llama3.2)  │    │   Pages      │
│              │    │              │    │              │
│ • users      │    │ • Generate   │    │ • Publish    │
│ • brands     │    │ • Count      │    │ • Deploy     │
│ • api_keys   │    │   tokens     │    │ • Host       │
│ • posts      │    │ • Track      │    │              │
│ • token_usage│    │   usage      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🔄 Data Flow - How Information Moves

### Flow 1: User Signs Up (via GitHub OAuth)

```
1. User clicks "Login with GitHub" on /admin/join
   └─> Button: templates/join.html:241

2. Redirects to /github/connect
   └─> Route: onboarding_routes.py:83
   └─> Calls: github_faucet.get_auth_url()

3. Redirects to github.com (user approves)

4. GitHub sends user back to /github/callback?code=abc123
   └─> Route: onboarding_routes.py:100
   └─> Calls: github_faucet.process_callback()
   └─> Fetches GitHub profile
   └─> Calculates tier (based on commits/repos)
   └─> Generates API key: sk_github_username_abc123

5. Stores in database:
   INSERT INTO api_keys (api_key, user_id, tier)
   INSERT INTO users (github_username, email)

6. Returns API key to user
   └─> Displays on success page
   └─> User can now call /api/* endpoints
```

### Flow 2: User Creates Content (via Studio)

```
1. User visits /admin/studio
   └─> Route: app.py (admin routes)

2. User types topic: "What is privacy?"

3. Clicks "Generate with Multi-AI"
   └─> Calls: /api/generate-debate
   └─> Route: Uses multi_ai_debate.py

4. Flask calls Ollama:
   └─> ollama_client.generate(prompt, max_tokens=500)
   └─> Ollama returns: {response, tokens_prompt, tokens_generated}

5. Save token usage:
   INSERT INTO token_usage (user_id, tokens_used, brand_slug)

6. Save post:
   INSERT INTO posts (title, content_html, brand_id)

7. User clicks "Publish All"
   └─> Calls: /admin/automation/publish-all
   └─> Runs: git add . && git commit && git push
   └─> GitHub Pages deploys (auto, ~2 min)
```

### Flow 3: Automation Workflows

```
1. User clicks "Run Auto-Syndication"
   └─> POST /admin/automation/run-syndication

2. Flask calls:
   from automation_workflows import WorkflowAutomation
   automation.auto_syndicate_new_posts(hours_back=24)

3. Queries database:
   SELECT * FROM posts WHERE published_at >= 24_hours_ago

4. For each post:
   - Check if already syndicated
   - Cross-post to other brands
   - INSERT INTO network_posts

5. Returns results:
   {processed: 5, syndicated: 12, errors: []}

6. Flash message to user:
   "✅ Auto-syndication complete: 5 posts processed"
```

---

## 🧩 Component Connections

### 1. Flask ↔ Database

**Purpose:** Store and retrieve all data
**Files:**
- `database.py` - Connection helper
- `soulfra.db` - SQLite database (200+ tables)

**Key Operations:**
```python
db = get_db()
db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
db.commit()
db.close()
```

**Tables Used:**
- `users` - User accounts, GitHub profiles
- `brands` - Domain configurations (soulfra.com, calriven.com)
- `posts` - Blog posts
- `api_keys` - API authentication
- `token_usage` - Ollama token tracking
- `oauth_states` - OAuth security tokens

---

### 2. Flask ↔ Ollama

**Purpose:** AI content generation with token tracking
**Files:**
- `ollama_client.py` - Python client
- Ollama server (usually localhost:11434)

**Connection:**
```python
from ollama_client import OllamaClient

ollama = OllamaClient()
result = ollama.generate(
    prompt="Write a blog post about privacy",
    model='llama3.2',
    max_tokens=500
)

# Returns:
{
    'success': True,
    'response': 'Generated content...',
    'tokens_prompt': 120,      # Your input size
    'tokens_generated': 450,   # Output size
    'time_ms': 1250           # Generation time
}
```

**Token Tracking:**
```python
db.execute('''
    INSERT INTO token_usage (user_id, tokens_used, model, brand_slug)
    VALUES (?, ?, ?, ?)
''', (user_id, result['tokens_generated'], 'llama3.2', 'soulfra'))
```

---

### 3. Flask ↔ GitHub OAuth

**Purpose:** User authentication via GitHub
**Files:**
- `github_faucet.py` - OAuth handler
- `onboarding_routes.py` - Routes

**OAuth Flow:**
```python
from github_faucet import GitHubFaucet

faucet = GitHubFaucet()

# Step 1: Get auth URL
auth_url = faucet.get_auth_url(user_id=1)
# Returns: https://github.com/login/oauth/authorize?client_id=...

# Step 2: User approves on GitHub
# GitHub redirects back with code

# Step 3: Process callback
result = faucet.process_callback(code='abc123', state='xyz')
# Returns:
{
    'api_key': 'sk_github_johndoe_abc123',
    'tier': 2,
    'github_username': 'johndoe',
    'tokens': 100  # Free tokens
}
```

**Required Environment Variables:**
```bash
export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_secret
export GITHUB_REDIRECT_URI=http://localhost:5001/github/callback
```

---

### 4. Flask ↔ GitHub Pages

**Purpose:** Deploy static sites
**Files:**
- `output/soulfra/` - Built site (HTML/CSS)
- `output/calriven/` - Built site
- `output/deathtodata/` - Built site
- `output/howtocookathome/` - Built site

**Deployment Flow:**
```python
import subprocess

# Add changes
subprocess.run(['git', 'add', '.'], cwd='output/soulfra')

# Commit
subprocess.run(['git', 'commit', '-m', 'Auto-publish'], cwd='output/soulfra')

# Push to GitHub
subprocess.run(['git', 'push'], cwd='output/soulfra')

# GitHub Pages auto-deploys in ~2 minutes
# Site live at: https://soulfra.github.io/soulfra/
```

**Custom Domains (via CNAME):**
```
output/soulfra/CNAME contains: soulfra.com
→ DNS A records point to GitHub Pages IPs
→ Site accessible at https://soulfra.com
```

---

### 5. Flask ↔ Voice/Siri Integration

**Purpose:** Voice input for content creation
**Files:**
- `voice_routes.py` - Voice recording
- `voice_capsule_routes.py` - Voice time capsules
- `simple_voice_routes.py` - Simple recorder

**How It Works:**
```
1. User visits /voice (mobile browser)
2. Records voice memo
3. POSTs audio blob to /api/simple-voice/save
4. Flask saves to database:
   INSERT INTO voice_memos (user_id, audio_data)
5. Optional: Transcribe with Whisper (if installed)
6. Convert to blog post content
```

**Siri Integration (concept):**
```
1. Siri Shortcut → HTTP POST to /api/voice/create
2. Sends audio + metadata
3. Flask processes and creates post
4. Returns URL to new post
```

---

## 🎯 The Complete Picture

### What Connects to What:

```
USER INTERFACES:
├─ Browser (soulfra.com)
│  └─> Flask (port 5001)
│     ├─> Database (users, posts, brands)
│     ├─> Ollama (content generation)
│     └─> GitHub Pages (publish sites)
│
├─ Voice/Siri
│  └─> Flask /api/voice/*
│     └─> Database (voice_memos)
│     └─> Ollama (transcription/processing)
│
└─ GitHub OAuth
   └─> Flask /github/callback
      └─> Database (api_keys, users)
      └─> Return API key
```

### Data Storage Hierarchy:

```
DATABASE (soulfra.db)
├─ users (your account)
│  ├─ token_balance (how many tokens you have)
│  └─ api_keys (your API keys)
│
├─ brands (your websites)
│  ├─ domain (soulfra.com, calriven.com)
│  └─ posts (blog content)
│
└─ token_usage (Ollama tracking)
   ├─ tokens_used (how many per request)
   └─ brand_slug (which brand used them)
```

### API Flow:

```
External API Call:
curl -H "Authorization: Bearer sk_abc123" \
     https://api.soulfra.com/generate

↓

Flask validates API key:
SELECT * FROM api_keys WHERE api_key = 'sk_abc123'

↓

Checks token balance:
SELECT token_balance FROM users WHERE id = ?

↓

Calls Ollama:
ollama.generate(prompt)

↓

Deducts tokens:
UPDATE users SET token_balance = token_balance - 450

↓

Logs usage:
INSERT INTO token_usage (tokens_used, model)

↓

Returns result:
{response: "...", tokens_used: 450}
```

---

## 🚀 Quick Reference - URL Map

### User-Facing Pages:
```
http://localhost:5001/admin/join           → Sign up with GitHub
http://localhost:5001/admin/studio         → Create content
http://localhost:5001/admin/automation     → Run workflows
http://localhost:5001/admin/token-usage    → View Ollama usage
http://localhost:5001/voice                → Record voice memos
```

### API Endpoints:
```
POST /api/join                             → Email signup
POST /github/connect                       → GitHub OAuth
POST /api/generate-debate                  → Multi-AI content
POST /admin/automation/run-syndication     → Cross-post content
POST /admin/automation/publish-all         → Deploy to GitHub
GET  /api/tokens/balance                   → Check token balance
```

### Static Sites (GitHub Pages):
```
https://soulfra.github.io/soulfra/         → Soulfra blog
https://soulfra.github.io/calriven/        → CalRiven philosophy
https://soulfra.github.io/deathtodata/     → Privacy manifesto
https://soulfra.github.io/howtocookathome/ → Cooking blog
```

---

## 🔑 Environment Variables Needed

```bash
# GitHub OAuth (for user login)
export GITHUB_CLIENT_ID=your_github_client_id
export GITHUB_CLIENT_SECRET=your_github_secret
export GITHUB_REDIRECT_URI=http://localhost:5001/github/callback

# Optional: Claude API (for weekly summaries)
export ANTHROPIC_API_KEY=your_claude_api_key

# Database (defaults to soulfra.db if not set)
export SOULFRA_DB=soulfra.db

# Flask (development mode)
export FLASK_ENV=development
export FLASK_DEBUG=1
```

**How to set up GitHub OAuth:**
1. Go to: https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in:
   - Application name: Soulfra Local
   - Homepage URL: http://localhost:5001
   - Callback URL: http://localhost:5001/github/callback
4. Copy CLIENT_ID and CLIENT_SECRET
5. Add to your `.env` file or export in terminal

---

## 📝 Summary - The Big Picture

**Your System:**
```
┌─────────────────────────────────────────────────────┐
│  Soulfra = Multi-Brand Blog Network with AI        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Users sign up via GitHub OAuth                    │
│    ↓                                                │
│  Get API key + free tokens                         │
│    ↓                                                │
│  Create content in Studio (Ollama generates)       │
│    ↓                                                │
│  Auto-syndicate across brands                      │
│    ↓                                                │
│  Publish to GitHub Pages (one click)               │
│    ↓                                                │
│  Live on soulfra.com, calriven.com, etc.           │
│                                                     │
│  All tracked: tokens, usage, API calls             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**What's Now Connected:**
- ✅ GitHub OAuth → API keys
- ✅ Ollama → Token tracking
- ✅ Auto-syndication → Cross-posting
- ✅ Publish button → GitHub Pages
- ✅ Voice input → Database
- ✅ Admin panel → All features

**What You Can Now Do:**
1. Visit http://localhost:5001/admin/join
2. Click "Login with GitHub"
3. Get your API key
4. Create content in Studio
5. Click "Run Auto-Syndication"
6. Click "Publish to All Sites"
7. See your content live in 2 minutes

---

**Created:** January 2, 2026
**Status:** All systems wired and ready to use
**Next:** Set up GITHUB_CLIENT_ID and test OAuth flow
