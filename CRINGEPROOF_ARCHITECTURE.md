# 🏗️ CringeProof Complete Architecture

## The Big Picture

CringeProof is a **hybrid web app** with:
- **Frontend:** Static HTML on GitHub Pages (cringeproof.com)
- **Backend:** Python Flask on your Mac (port 5002)
- **Processing:** Whisper + Ollama (local AI)
- **Database:** SQLite (soulfra.db)

---

## Component Breakdown

### 1. Frontend (GitHub Pages)

**Location:** `voice-archive/` repo → cringeproof.com

**Files:**
- `record.html` - Voice recorder interface
- `screenshot.html` - Screenshot OCR interface
- `index.html` - Voice archive homepage
- `ideas/` - Static generated ideas hub
- `css/soulfra.css` - Styling

**Technology:**
- Pure HTML/CSS/JavaScript
- MediaRecorder API (for voice)
- Tesseract.js (for OCR)
- No server, no backend, no database

**How it works:**
1. User visits cringeproof.com/record.html
2. Browser loads static HTML
3. JavaScript uses microphone
4. Creates audio blob
5. POSTs to 192.168.1.87:5002 (your Mac)

---

### 2. Backend API (Your Mac)

**Location:** `cringeproof_api.py` (296 lines)

**Port:** 5002

**Technology:**
- Python 3.13
- Flask web framework
- Flask-CORS (cross-origin requests)
- SSL/HTTPS (self-signed cert)

**Endpoints:**
```
GET  /                        - Landing page with status
GET  /health                  - Health check (PM2 monitoring)
POST /api/simple-voice/save   - Upload voice recording
POST /api/screenshot-text/save - Upload OCR text
GET  /api/ideas/list          - List all ideas
GET  /api/ideas/<id>          - Get specific idea
GET  /favicon.ico             - Prevent 404 logs
```

**Process Flow:**
```python
1. Receive audio blob (WebM format)
2. Save to database (simple_voice_recordings table)
3. Transcribe with Whisper → text
4. Extract ideas with Ollama → structured insights
5. Save ideas (voice_ideas table)
6. Return success + idea_id
```

---

### 3. AI Processing

**Whisper (Speech-to-Text):**
- Model: Runs locally on your Mac
- Speed: ~3-5 seconds for 30-second audio
- Accuracy: 95%+ for clear English
- Privacy: Never leaves your Mac

**Ollama (Idea Extraction):**
- Model: llama3.2:3b (2GB)
- Prompt: Extract top 3-5 ideas with titles, scores, insights
- Output: JSON with title, text, score (0-100), insight
- Fallback: If Ollama unavailable, uses first sentence as title

**Example:**
```
Audio: "I hate cringe on social media. Everyone's so fake..."

Whisper transcription:
"I hate cringe on social media everyone's so fake..."

Ollama extraction:
{
  "title": "Authentic Social Interaction",
  "text": "Build genuine connection without validation game",
  "score": 78,
  "insight": "Focus on real community and vulnerability over performance"
}
```

---

### 4. Database (SQLite)

**Location:** `soulfra.db` (shared with Soulfra platform)

**Key Tables:**

**simple_voice_recordings:**
- id, filename, audio_data (BLOB)
- transcription, transcription_method
- file_size, user_id, created_at

**voice_ideas:**
- id, title, description
- score, ai_insight, status
- recording_id (FK), user_id, created_at

**Why shared database?**
- CringeProof is part of larger Soulfra ecosystem
- Ideas can be referenced by other Soulfra features
- Single source of truth for all voice content

---

### 5. PM2 Process Manager

**Why PM2?**
- Auto-restart on crash
- Log management
- Environment variables
- Resource monitoring
- Production-ready

**Configuration:**
```javascript
// ecosystem.config.cjs
{
  name: 'cringeproof-api',
  script: 'cringeproof_api.py',
  interpreter: 'python3',
  autorestart: true,
  max_memory_restart: '500M',
  error_file: './logs/cringeproof-error.log',
  out_file: './logs/cringeproof-out.log'
}
```

**Commands:**
```bash
pm2 start ecosystem.config.cjs    # Start all services
pm2 status                         # Check status
pm2 logs cringeproof-api          # View logs
pm2 restart cringeproof-api       # Restart service
pm2 stop cringeproof-api          # Stop service
```

---

## Network Flow

### Same WiFi (Current Setup)

```
iPhone (192.168.1.X)
    ↓ WiFi
Router (192.168.1.1)
    ↓ WiFi
Mac (192.168.1.87)
    ↓ Port 5002
CringeProof API (Flask)
    ↓
Whisper + Ollama
    ↓
soulfra.db
```

**Limitations:**
- Only works on same WiFi
- SSL cert warning on each device
- Can't share with friends remotely

### With Tailscale (Future)

```
iPhone (anywhere)
    ↓ Internet
Tailscale VPN
    ↓
Mac (100.x.x.x Tailscale IP)
    ↓ Port 5002
CringeProof API
```

**Benefits:**
- Works from anywhere
- Real SSL cert (*.ts.net)
- Secure encrypted tunnel
- Share with authorized users

---

## The 4 Services Explained

**1. roommate-chat (port 3000)**
- Node.js WebSocket server
- Multi-domain platform
- NOT related to CringeProof
- Can ignore for voice archive

**2. soulfra-flask (port 5001)**
- Main Soulfra platform
- Blog, profiles, QR codes
- NOT related to CringeProof
- Shares same database

**3. cringeproof-api (port 5002)**
- **THIS IS CRINGEPROOF**
- Voice/screenshot intake
- Whisper + Ollama processing

**4. cringeproof.com (GitHub Pages)**
- **THIS IS CRINGEPROOF FRONTEND**
- Static HTML/JS
- No server

**Only #3 and #4 matter for CringeProof!**

---

## Security Model

### Current (No Auth)

**Pros:**
- Simple, no login needed
- Fast to use
- Works offline (same WiFi)

**Cons:**
- Anyone on WiFi can POST
- No user tracking
- Can't share publicly

### With API Key (Recommended)

**Add to cringeproof_api.py:**
```python
API_KEY = os.environ.get('CRINGEPROOF_API_KEY')

@app.route('/api/simple-voice/save')
def save_voice():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    # ... rest of code
```

**Update iOS Shortcut:**
Add header: `X-API-Key: your-secret-key`

### With QR Auth (Advanced)

**Use existing Soulfra QR system:**
1. Scan QR code on Mac screen
2. Generate session token
3. Store in `qr_auth_tokens` table
4. Include in all requests
5. Expires after 24 hours

---

## Deployment Options

### Option 1: Local (Current)

**Pros:** Free, private, fast Whisper
**Cons:** WiFi-only, cert warnings
**Best for:** Personal use, testing

### Option 2: Tailscale

**Pros:** Works anywhere, real SSL
**Cons:** Requires app, learning curve
**Best for:** Personal + friends

### Option 3: Cloud (Fly.io)

**Pros:** Works for everyone, simple
**Cons:** $5-10/mo, slower Whisper
**Best for:** Public product

### Option 4: Hybrid

**Frontend:** GitHub Pages (free)
**Backend:** Local Flask (free)
**Database:** Supabase PostgreSQL (free tier)

**Best for:** Public viewing, private processing

---

## File Structure

```
soulfra-simple/
├── cringeproof_api.py          # Backend API
├── ecosystem.config.cjs         # PM2 config
├── soulfra.db                   # Database
├── cert.pem, key.pem           # SSL certs
├── whisper_transcriber.py      # Whisper wrapper
├── ollama_client.py            # Ollama wrapper
├── voice_idea_board_routes.py  # Idea extraction
├── logs/
│   ├── cringeproof-error.log
│   └── cringeproof-out.log
└── voice-archive/              # GitHub Pages repo
    ├── record.html
    ├── screenshot.html
    ├── index.html
    └── css/soulfra.css
```

---

## What Makes It "CringeProof"?

1. **No performance anxiety** - Just talk, AI extracts value
2. **Private by default** - Runs on your Mac, not cloud
3. **Low friction** - One tap to record, auto-processes
4. **No vanity metrics** - Focus on ideas, not likes
5. **Real connection** - Voice → insights → action

---

## Next Steps

1. ✅ Read this architecture doc
2. ✅ Follow `TEST_CHECKLIST.md` to verify setup
3. ✅ Create iOS Shortcut (see `SIRI_SHORTCUT_GUIDE.md`)
4. ⏳ Test recording from phone
5. ⏳ Decide on auth strategy
6. ⏳ Consider Tailscale for remote access

---

**Questions? Issues?**

Check logs: `pm2 logs cringeproof-api`
Check health: `https://192.168.1.87:5002/health`
Check database: `sqlite3 soulfra.db "SELECT * FROM voice_ideas"`
