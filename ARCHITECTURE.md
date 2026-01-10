# Soulfra System Architecture

**Last Updated:** 2026-01-09

## Overview

Soulfra is a voice-first IRC/Usenet messaging system with static site generation. Think dev.to meets Usenet meets voice memos, all deployed to GitHub Pages.

---

## Localhost Port Architecture

### Port 5001 - Main Soulfra App (`app.py`)

**Purpose:** Production Flask server for web interface and content generation

**Key Routes:**
- `/` - Homepage
- `/generator` - Domain/content generator interface
- `/inbox.html` - IRC/Usenet message viewer
- `/blog` - Blog rendering
- `/newsletter` - Newsletter subscription management
- `/stpetepros/*` - Real estate business routes

**What It Does:**
- Renders blog posts and newsletters from IRC messages
- User authentication and session management
- Domain management and routing
- Serves static templates
- Connects to shared `soulfra.db` SQLite database

**Running:** `python3 app.py` → https://192.168.1.87:5001

---

### Port 5002 - CringeProof API (`cringeproof_api.py`)

**Purpose:** Isolated microservice for heavy voice/AI processing

**Key Routes:**
- `POST /api/simple-voice/save` - Voice recording upload
- `POST /api/screenshot-text/save` - Screenshot OCR text upload
- `GET /api/ideas/list` - List all extracted ideas from voice
- `GET /api/ideas/<id>` - Get specific idea
- `/api/auth/*` - Authentication API (JSON endpoints)
- `/api/claim-slug` - Slug/username claiming
- `/<slug>` - User profile pages with wordmap CSS

**What It Does:**
- Processes voice recordings with Whisper
- Extracts ideas/bugs from voice using Ollama
- Handles screenshot OCR
- Isolated from main app so crashes don't affect production
- Connects to same shared `soulfra.db` database

**Why Separate?**
- Heavy processing (Whisper/Ollama) can crash without affecting main site
- Independent scaling
- Debugging tool stays up when main app restarts
- Clean API for CalRiven/DeathToData to access insights

**Running:** `python3 cringeproof_api.py` → https://192.168.1.87:5002

---

### Cloudflared Tunnels

Multiple `cloudflared` processes expose local ports to public internet:

```
cloudflared tunnel --url https://192.168.1.87:5002
cloudflared tunnel --url http://192.168.1.87:5002
```

**Why?** Allows GitHub Pages (static site) to call Flask APIs for dynamic features like comments, voice upload, etc.

---

## Data Flow Architecture

### 1. Voice → IRC Message Pipeline

```
User records voice
    ↓
CringeProof API (port 5002) receives audio
    ↓
Whisper transcription
    ↓
Stored in domain_messages table as IRC message
    ↓
RSS feed updated (generate_rss.py)
    ↓
Static site regenerated (generate_static_site.py)
    ↓
Deployed to GitHub Pages
```

### 2. IRC Message → Blog Post Pipeline

```
IRC message posted to alt.soulfra.blog
    ↓
Stored in domain_messages table
    ↓
generate_static_site.py reads messages
    ↓
Jinja2 template renders HTML with GitHub-style CSS
    ↓
Comments section polls Flask API (port 5002) via JavaScript
    ↓
Deployed to soulfra.github.io/soulfra/index.html
```

### 3. Comment Pipeline (Static Site → Flask API)

```
User types comment on GitHub Pages static blog
    ↓
JavaScript POSTs to https://192.168.1.87:5002/api/messages/{domain}/{post_id}/comments
    ↓
Flask stores comment in domain_messages table with parent_id
    ↓
JavaScript polls GET endpoint to refresh comments
    ↓
Threaded comment structure rendered client-side
```

---

## Database Architecture

**Single Database:** `soulfra.db` (SQLite)

**Shared by:**
- Main app (port 5001)
- CringeProof API (port 5002)
- All standalone scripts (`generate_static_site.py`, `generate_rss.py`, etc.)

**Key Tables:**
- `domain_messages` - IRC/Usenet messages, blog posts, comments (with `parent_id` for threading)
- `simple_voice_recordings` - Voice recording metadata + transcriptions
- `ideas` - Extracted ideas from voice/text via Ollama
- `users` - User accounts
- `subscribers` - Newsletter subscriptions

---

## Static Site Generation

### How It Works

1. **Data Source:** IRC messages in `domain_messages` table
2. **Generator:** `generate_static_site.py` with Jinja2 templates
3. **Templates Available:**
   - `blog` - GitHub-style blog with comments
   - `newspaper` - (TODO) 3-column news layout
   - `classified` - (TODO) Grid/card layout for services
4. **Output:** HTML files to `/Users/matthewmauer/Desktop/soulfra.github.io/{domain}/index.html`
5. **Deployment:** Manual git push or automated via deploy button

### Making Static Sites Interactive

**Problem:** GitHub Pages can't run server-side code for comments

**Solution:**
- Static HTML + JavaScript polling Flask API
- Comments stored in Flask backend (port 5002)
- JavaScript loads comments via AJAX on page load
- Best of both worlds: static hosting + dynamic features

---

## Template System (No Tailwind!)

**Philosophy:** Keep it simple and portable

**Current Approach:**
- Jinja2 templates (Python templating)
- Inline CSS (GitHub-inspired styling)
- No build tools, no npm, no Tailwind
- Pure HTML/CSS/JavaScript

**Why No Tailwind?**
- Adds complexity and build step
- Harder to customize for brand personas
- Inline CSS is more "view source friendly"
- Matches Usenet/old-school web aesthetic

**Future:** Could reverse-engineer Tailwind concepts into our own component system

---

## Ollama Integration

### Current State

- `ollama_connector_routes.py` provides API for connecting local Ollama
- Used for voice transcription analysis
- Idea extraction from debugging sessions

### Planned: Ollama Feed Watcher

**Daemon:** `ollama_feed_watcher.py` (TODO)

**What It Does:**
1. Polls RSS feeds every 60 seconds
2. Detects new voice recordings or IRC messages
3. Sends transcription to Ollama for content generation
4. Auto-generates blog post using `generate_static_site.py`
5. Optionally triggers newsletter via `simple_emailer.py`
6. Pushes to GitHub Pages automatically

**Use Case:** Record voice memo → Ollama writes blog post → Site auto-deploys

---

## Brand Persona System

### Existing Personas

1. **CalRiven** - Technical/code persona
2. **TheAuditor** - Validation/verification persona
3. **DeathToData** - Privacy/security persona
4. **CringeProof** - Debugging/voice persona
5. **StPetePros** - Real estate business persona

### Planned: Brand Router

**Auto-routing content to correct persona based on:**
- Keywords in voice transcription
- Domain/channel in IRC message
- Ollama classification

**Example:**
```
Voice memo: "Privacy concerns with cookie tracking"
    ↓
Router: DeathToData persona
    ↓
Published to alt.deathtodata.privacy channel
    ↓
Styled with DeathToData brand CSS
```

---

## Voice-Based Version Control

**Concept:** Git, but for voice debugging sessions

### How It Would Work

1. **Voice Recordings = Commits**
   - Each recording stored with `parent_id` (like comments)
   - Chain recordings together to form "branches"

2. **Timeline Viewer**
   - See all related debugging sessions
   - "Diff" between two voice recordings (compare transcriptions)
   - "Revert to voice recording #47"

3. **Export Chain**
   - "Play all related recordings" feature
   - Export voice chain to README
   - Generate written summary from voice timeline

### Use Case

Debugging multi-session problem:
```
Voice #1: "Bug found in auth system"
    ↓
Voice #2: "Tried fixing with JWT refresh"
    ↓
Voice #3: "Still broken, checking database"
    ↓
Voice #4: "Found it! Was a migration issue"
```

Timeline viewer shows progression, allows "jumping back" to earlier theories.

---

## QR Code & Landing Page System

### How QR Codes Fit In

1. **Content Generation:**
   - Every blog post, voice recording, or IRC message gets unique hash
   - Hash used to generate QR code

2. **Landing Pages:**
   - Scan QR → lands on `/{hash}` route
   - Route serves content based on hash
   - Tracks device fingerprint for analytics

3. **Use Cases:**
   - Physical business cards with QR → personal IRC channel
   - Podcast episodes with QR → show notes + voice-ins
   - Real estate listings with QR → property details + voice tour

---

## Email System (Pending Setup)

### Current State

- `simple_emailer.py` configured for Gmail SMTP
- Sends FROM `your-email@gmail.com` (not @soulfra.com domain)

### Needed

1. **Domain Email Setup:**
   - Configure Cloudflare Email Routing or SendGrid
   - Update `simple_emailer.py` with @soulfra.com SMTP credentials

2. **Email Compose UI:**
   - Add to `inbox.html` for sending IRC messages as emails

3. **Newsletter Templates:**
   - Newspaper layout (3-column)
   - Classified layout (grid/cards)
   - Wire to `simple_emailer.py`

---

## Deployment Flow

### Manual Deployment

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 generate_static_site.py --domain soulfra --template blog --deploy
cd /Users/matthewmauer/Desktop/soulfra.github.io
git add .
git commit -m "Update blog"
git push
```

### Planned: One-Click Deploy

**Phase 6 (TODO):**
1. Add `/api/deploy-site` endpoint to Flask app
2. Endpoint runs `generate_static_site.py` + git push
3. Add "Deploy My Site" button to inbox.html
4. Optional: Scheduled auto-deploy via cron or webhooks

---

## Service Discovery

### How to Check What's Running

```bash
# Check all Flask services
lsof -i :5001 -i :5002 -P -n | grep LISTEN

# Check cloudflared tunnels
ps aux | grep cloudflared

# Check background Python processes
ps aux | grep python3
```

### Typical Output

```
Python  5001  app.py              ← Main Soulfra app
Python  5002  cringeproof_api.py  ← CringeProof microservice
```

---

## Future Architecture Plans

### 1. Ollama Automation
- Feed watcher daemon monitoring RSS
- Auto-generate content from voice
- Schedule posts for optimal timing

### 2. Proximity Discovery
- Add geolocation/zip code to device fingerprint
- "Find people near you" using IRC channels
- Local meetups via voice announcements

### 3. Embeddable Widget
- `widget.js` for embedding IRC chat on external sites
- Widget customizer in inbox.html
- Works like Disqus but for IRC/voice

### 4. Voice Version Control
- Timeline viewer for debugging sessions
- Voice diff tool
- Export chains to documentation

### 5. Brand Persona Router
- Auto-classify content by persona
- Route to correct IRC channel
- Apply brand-specific CSS/styling

---

## Development Commands

### Start Services

```bash
# Main app
python3 app.py

# CringeProof API
python3 cringeproof_api.py

# Both in background
python3 app.py &
python3 cringeproof_api.py &
```

### Generate Static Site

```bash
# Blog template
python3 generate_static_site.py --domain soulfra --template blog --deploy

# Newspaper template (TODO)
python3 generate_static_site.py --domain soulfra --template newspaper --deploy

# Classified template (TODO)
python3 generate_static_site.py --domain soulfra --template classified --deploy
```

### Generate RSS

```bash
python3 generate_rss.py --domain soulfra
```

### Run Ollama Feed Watcher (TODO)

```bash
python3 ollama_feed_watcher.py --domain soulfra --interval 60
```

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Kill process on port 5002
lsof -ti:5002 | xargs kill -9
```

### Database Locked

```bash
# SQLite only allows one writer at a time
# Stop all Flask services, then restart
pkill -f "python3 app.py"
pkill -f "python3 cringeproof_api.py"
```

### Comments Not Loading on Static Site

1. Check Flask API is running: `curl https://192.168.1.87:5002/api/messages/soulfra/1/comments`
2. Check CORS headers in `cringeproof_api.py`
3. Check browser console for JavaScript errors
4. Check cloudflared tunnel is active

---

## Architecture Philosophy

**Voice-First:** Everything starts with voice recording or IRC message

**Static-First:** Deploy to GitHub Pages for free, fast, resilient hosting

**Microservices:** Separate concerns (main app vs heavy processing)

**No Build Tools:** Keep it simple - no webpack, no npm, no Tailwind

**Git as Database:** Content lives in IRC messages, deployed via git

**Usenet Aesthetic:** Embrace retro web, threaded conversations, RSS feeds

---

## Questions Answered

### Q: "What the fuck are these localhost ports?"

A: Port 5001 = main web app, Port 5002 = voice/AI processing microservice

### Q: "How does Ollama automation work?"

A: Daemon watches RSS feed → detects new content → Ollama generates blog → auto-deploys

### Q: "How do templates fit together?"

A: Jinja2 reads IRC messages from database → renders HTML with inline CSS → deploys to GitHub Pages

### Q: "What's this git but voice thing?"

A: Voice recordings linked with `parent_id` like git commits → timeline viewer shows debugging progression

### Q: "How do mascots/brands integrate?"

A: Router auto-assigns content to CalRiven/DeathToData/etc based on keywords → applies brand CSS
