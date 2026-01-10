# 🚀 Soulfra Simple - Deploy Folder

**One-command deployment like cursor.directory**

---

## Files in This Folder

```
deploy/
├── DEPLOY_NOW.sh              # One-command deployment script
├── nginx-soulfra.conf         # Nginx config template (optimized for voice/WebM)
├── DEPLOYMENT_GUIDE.md        # Complete deployment documentation
└── README.md                  # This file
```

---

## ⚡ Quick Start

### Local Development

```bash
./deploy/DEPLOY_NOW.sh
```

Choose option `1` for local development on http://localhost:5001

### Production Deployment

```bash
./deploy/DEPLOY_NOW.sh
```

Choose option `2` for production deployment with:
- Nginx reverse proxy
- SSL certificate (Let's Encrypt)
- Gunicorn WSGI server
- Rate limiting
- Voice/WebM upload optimization

---

## 📋 What Gets Deployed

### Core Systems

1. **Voice Recording System** (`/voice`)
   - MediaRecorder API for 30-sec voice memos
   - WebM upload with SHA256 verification
   - Local storage in `voice_recordings/`

2. **Suggestion Box** (`/suggestion-box`)
   - Voice-based community suggestions
   - AI idea extraction (Ollama)
   - SHA256 chain verification

3. **CringeProof Voting** (`/suggestion/<id>`)
   - Community voting: upvote/downvote/cringe/authentic
   - CringeProof score calculation (0-100)
   - Brand-specific theming (@soulfra, @deathtodata, @calriven)

4. **Status Map** (`/status-map`)
   - Game-like visual debugging
   - Real-time system health checks
   - ✅/🔧/❌ status indicators

### Infrastructure

- **Database:** SQLite (`soulfra.db`)
- **Web Server:** Flask (dev) or Gunicorn (prod)
- **Reverse Proxy:** Nginx (prod only)
- **SSL:** Let's Encrypt (prod only)
- **AI:** Ollama + Whisper (optional)

---

## 🎯 Deployment Modes

### Mode 1: Local Development

**What it does:**
- Starts Flask on http://localhost:5001
- Debug mode enabled
- No SSL, no Nginx
- Perfect for testing

**Use case:** Building features, testing locally

### Mode 2: Production

**What it does:**
- Configures Nginx as reverse proxy
- Gets SSL certificate from Let's Encrypt
- Starts Gunicorn with multiple workers
- Sets up rate limiting
- Optimizes for voice/WebM uploads

**Use case:** Deploying to public domain

---

## 📊 Status Map Dashboard

After deployment, visit `/status-map` to see:

### System Checks

- ✅ **Database** - SQLite connection + record counts
- ✅ **Voice System** - Folder existence + WebM file count
- ✅ **CringeProof Voting** - Vote table + count
- ✅ **Ollama** - AI model availability
- ✅ **Whisper** - Transcription service
- ✅ **Flask Server** - Running status
- 🔧 **Nginx** - Installation + running status
- 🔧 **SSL** - Certificate status
- ⚠️ **File Count** - Warning if too many files

### Working Routes

- `/voice` - Voice recorder
- `/suggestion-box` - Community suggestions
- `/suggestion/<id>` - Suggestion detail + voting
- `/@<brand>/suggestions` - Brand-specific views
- `/chat` - Ollama chat interface
- `/status-map` - Status dashboard

---

## 🔧 Customization

### Change Domain

Edit `DEPLOY_NOW.sh` or run it interactively:

```bash
./deploy/DEPLOY_NOW.sh
# Choose option 2
# Enter domain: yourdomain.com
```

### Adjust Upload Limits

Edit `nginx-soulfra.conf`:

```nginx
# Change from 50M to 100M
client_max_body_size 100M;
```

### Change Rate Limits

Edit `nginx-soulfra.conf`:

```nginx
# Voice uploads: change from 10/min to 20/min
limit_req_zone $binary_remote_addr zone=voice_upload:10m rate=20r/m;

# API calls: change from 60/min to 120/min
limit_req_zone $binary_remote_addr zone=api:10m rate=120r/m;
```

---

## 🐛 Troubleshooting

### Script Won't Run

```bash
# Make executable
chmod +x deploy/DEPLOY_NOW.sh

# Run from project root
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
./deploy/DEPLOY_NOW.sh
```

### Server Won't Start

Check status map: http://localhost:5001/status-map

Common issues:
- Port 5001 already in use → `lsof -i :5001 && kill <PID>`
- Database missing → Auto-created on first run
- Voice folder missing → Auto-created on first run

### Nginx Config Error

```bash
# Test config
sudo nginx -t

# Check for syntax errors in:
/etc/nginx/sites-available/soulfra
```

### SSL Certificate Fails

```bash
# DNS not propagated yet
dig yourdomain.com +short

# Try manual cert
sudo certbot --nginx -d yourdomain.com
```

---

## 📦 What's NOT in This Folder

This deploy folder contains **only deployment essentials**.

**Archived to `/archive/prototypes/`:**
- 378 .py prototype files
- 253 .md documentation files
- Experimental features

**Core files (in project root):**
- `app.py` - Flask application
- `database.py` - Database connection
- `voice_suggestion_box.py` - Voice system
- `suggestion_box_routes.py` - API routes
- `requirements.txt` - Python dependencies

---

## 🎮 Like cursor.directory

**Philosophy:** Simple. Fast. Works.

**cursor.directory does:**
- Single command deployment ✅
- Clear status indicators ✅
- Minimal complexity ✅
- Fast iteration ✅

**We do the same:**
- `./deploy/DEPLOY_NOW.sh` - One command
- `/status-map` - Visual debugging
- 5 core files vs 378 prototypes
- Debug like gameplay (instant feedback)

---

## 🚀 Next Steps

1. **Test locally:**
   ```bash
   ./deploy/DEPLOY_NOW.sh
   # Choose 1
   # Visit http://localhost:5001/status-map
   ```

2. **Record a voice memo:**
   - Visit http://localhost:5001/voice
   - Record 30 seconds
   - Check http://localhost:5001/suggestion-box

3. **Test CringeProof voting:**
   - Visit http://localhost:5001/suggestion/1
   - Vote: upvote/downvote/cringe/authentic
   - Watch score update

4. **Deploy to production:**
   ```bash
   ./deploy/DEPLOY_NOW.sh
   # Choose 2
   # Enter domain
   # Follow prompts
   ```

---

## 📞 Support

**Documentation:**
- Full guide: `deploy/DEPLOYMENT_GUIDE.md`
- Trust radar: `TRUST_RADAR_ARCHITECTURE.md`
- Database: `DATABASE_ARCHITECTURE.md`

**Status:**
- Local: http://localhost:5001/status-map
- Production: https://yourdomain.com/status-map

---

**Last Updated:** 2026-01-03

**Like cursor.directory:** Simplified deployment, fast debugging, works on first try.
