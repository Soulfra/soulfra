# 🌐 CringeProof / Soulfra System URLs

Complete reference for all frontend pages, backend APIs, and admin panels.

---

## 📱 Frontend URLs (Static Sites)

### GitHub Pages (Production)
- **Base URL:** `https://soulfra.github.io/voice-archive/`
- **Custom Domain:** `https://cringeproof.com/`

### Local Development
- **Base URL:** File served from `voice-archive/` folder

### Pages

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` or `/index.html` | Main landing page |
| **Record Simple** | `/record-simple.html` | Basic voice recorder (iOS compatible) |
| **Record Game** | `/record-game.html` | Token game recorder with challenges |
| **Ideas Hub** | `/ideas/` | AI-extracted ideas from recordings |
| **Wordmap** | `/wordmap.html` | D3.js word cloud visualization |
| **Screenshot** | `/screenshot.html` | Screenshot text extraction |
| **Login** | `/login.html` | QR code authentication |

---

## 🔌 Backend URLs (Flask API)

### Local Development
- **Base URL:** `https://localhost:5001`
- **Local Network:** `https://192.168.1.87:5002` (for iPhone testing)

### Cloudflare Tunnel (Optional)
- **Tunnel URL:** `https://wooden-example-happy-fine.trycloudflare.com`

### Admin Panel

| Panel | URL | Description |
|-------|-----|-------------|
| **Database Admin** | `/admin/database` | SharePoint-like database viewer |
| **Canvas Editor** | `/admin/canvas` | WYSIWYG image editor |
| **Image Gallery** | `/admin/images` | QR code gallery |
| **Deploy Checks** | `/admin/deploy-ready` | Pre-deployment checklist |

**Full URL Examples:**
- `https://localhost:5001/admin/database`
- `https://192.168.1.87:5002/admin/database`

---

## 🎤 Voice Recording API

### Endpoints

#### Save Voice Recording
```
POST /api/simple-voice/save
Content-Type: multipart/form-data

Body:
- audio: File (audio/mp4 or audio/webm)

Response:
{
  "success": true,
  "recording_id": 42,
  "transcription": "Hello this is my voice...",
  "transcription_method": "whisper-local",
  "wordmap_updated": true
}
```

#### List Recordings
```
GET /api/simple-voice/list?user_id=1

Response:
{
  "success": true,
  "recordings": [
    {
      "id": 42,
      "filename": "recording_20260103_123456.m4a",
      "file_size": 245789,
      "transcription": "...",
      "created_at": "2026-01-03 12:34:56"
    }
  ]
}
```

#### Play Recording
```
GET /api/simple-voice/play/<recording_id>

Response: Audio file (audio/mp4 or audio/webm)
```

#### Delete Recording
```
DELETE /api/simple-voice/delete/<recording_id>

Response:
{
  "success": true,
  "message": "Recording 42 deleted"
}
```

---

## 🗺️ Wordmap API

### Endpoints

#### Get User Wordmap
```
GET /api/wordmap/<user_id>

Response:
{
  "success": true,
  "wordmap": {
    "blockchain": 48,
    "voice": 29,
    "python": 19,
    "recording": 1
  },
  "recording_count": 15,
  "last_updated": "2026-01-03 15:30:00",
  "pure_source_id": 1
}
```

#### Get Domain Wordmap
```
GET /api/wordmap/domain/<domain>

Response:
{
  "success": true,
  "wordmap": {
    "authentic": 50,
    "cringe": 40,
    "social": 30
  },
  "contributor_count": 3,
  "last_updated": "2026-01-03 15:30:00"
}
```

**Example Domains:**
- `cringeproof.com`
- `soulfra.com`
- `deathtodata.com`
- `calriven.com`

---

## 💡 Ideas API

### Endpoints

#### Save Idea
```
POST /api/ideas/save
Content-Type: application/json

Body:
{
  "user_id": 1,
  "title": "CringeProof Prediction",
  "summary": "Voice prediction about ideas...",
  "transcript": "Full transcription text...",
  "recording_id": 42
}

Response:
{
  "success": true,
  "idea_id": 7
}
```

#### List Ideas
```
GET /api/ideas/list?user_id=1

Response:
{
  "success": true,
  "ideas": [...]
}
```

#### Extract Ideas from Recording
```
POST /api/ideas/extract
Content-Type: application/json

Body:
{
  "recording_id": 42,
  "use_ollama": true
}

Response:
{
  "success": true,
  "ideas": ["idea 1", "idea 2"],
  "title": "Generated Title",
  "summary": "AI-generated summary"
}
```

---

## 🔐 Authentication API

### QR Code Authentication

#### Generate QR Code
```
POST /api/qr/generate
Content-Type: application/json

Body:
{
  "user_id": 1
}

Response:
{
  "success": true,
  "token": "abc123xyz",
  "qr_url": "/qr/auth/abc123xyz",
  "expires_at": "2026-01-03 16:30:00"
}
```

#### Scan QR to Login
```
GET /qr/auth/<token>

Redirects to: /voice (if valid token)
```

#### Verify Token
```
POST /api/qr/verify
Content-Type: application/json

Body:
{
  "token": "abc123xyz"
}

Response:
{
  "success": true,
  "user_id": 1,
  "username": "matt"
}
```

---

## 🎮 RPG Token Game

### Endpoints

#### Earn Reputation
```
POST /api/reputation/earn
Content-Type: application/json

Body:
{
  "user_id": 1,
  "points": 100,
  "reason": "Completed 5-deck challenge"
}

Response:
{
  "success": true,
  "new_reputation": 1250
}
```

#### Leaderboard
```
GET /api/leaderboard?limit=10

Response:
{
  "success": true,
  "rankings": [
    {
      "rank": 1,
      "username": "matt",
      "reputation": 1250,
      "level": 5
    }
  ]
}
```

---

## 📊 Database Admin API

### Export CSV
```
GET /api/admin/export/<table_name>/csv

Response: CSV file download
```

### Export Emails
```
GET /api/admin/export-emails

Response: CSV file with all user emails
```

### Custom SQL Query
```
POST /api/admin/sql-query
Content-Type: application/json

Body:
{
  "query": "SELECT * FROM users LIMIT 10"
}

Response:
{
  "success": true,
  "columns": ["id", "username", "email"],
  "data": [...]
}
```

**⚠️ Security Warning:** SQL endpoint blocks `DROP`, `DELETE`, `TRUNCATE`, `ALTER`

---

## 🔄 System Health

### Status Dashboard
```
GET /status

Response: HTML dashboard with system metrics
```

### Database Schemas
```
GET /status/schemas

Response:
{
  "success": true,
  "schemas": {
    "users": "CREATE TABLE users (...)",
    "simple_voice_recordings": "..."
  }
}
```

### Route Map
```
GET /status/routes

Response:
{
  "success": true,
  "routes": [
    {
      "endpoint": "/api/simple-voice/save",
      "methods": ["POST", "OPTIONS"]
    }
  ]
}
```

---

## 📡 Sitemap & SEO

### Sitemap
```
GET /sitemap.xml

Response: XML sitemap for search engines
```

### Robots.txt
```
GET /robots.txt

Response: SEO configuration
```

---

## 🚀 Quick Reference

### Testing Voice Recording on iPhone

1. **Connect to local network:**
   - Backend: `https://192.168.1.87:5002`
   - Frontend: Open `voice-archive/record-simple.html` in Safari

2. **Record audio:**
   - Tap 🎤 button
   - Grant microphone permission
   - Recording auto-uploads to backend
   - Whisper transcribes audio
   - Wordmap updates automatically

### Checking Admin Panel

```bash
# Local development
open https://localhost:5001/admin/database

# Local network (iPhone)
open https://192.168.1.87:5002/admin/database
```

### Testing Wordmap

```bash
# View wordmap visualization
open https://localhost:5001/wordmap.html

# Fetch wordmap data via API
curl -k https://localhost:5001/api/wordmap/1

# Fetch domain wordmap
curl -k https://localhost:5001/api/wordmap/domain/cringeproof.com
```

---

## 🔧 Configuration Files

### Backend Config
- **File:** `app.py`
- **Port:** 5001 (HTTPS)
- **SSL:** Self-signed certificate
- **CORS:** Enabled for GitHub Pages

### Frontend Config
- **File:** `voice-archive/config.js`
- **Backend URL:** Auto-detects localhost vs production
- **User ID:** Defaults to 1 (replace with auth)

---

## 📝 Notes

- **CORS:** Enabled for `https://soulfra.github.io`, `https://cringeproof.com`, `http://localhost:*`, `https://192.168.*.*:*`
- **iOS Safari:** Uses `audio/mp4` format, not `audio/webm`
- **Blob URLs:** Converted to data URLs for Safari playback
- **Transcription:** Whisper runs locally (faster) or via OpenAI API (fallback)
- **Wordmaps:** Update automatically after each recording
- **Admin Access:** No auth required in DEV_MODE

---

**Last Updated:** 2026-01-03
**Maintained By:** Soulfra Engineering
