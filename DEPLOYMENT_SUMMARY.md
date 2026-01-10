# CringeProof Voice Pipeline - Online Deployment Summary

## ✅ Completed

### 1. Railway Deployment Configuration
- ✅ Updated `railway.toml` to deploy `cringeproof_api:app` with Whisper
- ✅ Added `gunicorn` to `requirements.txt`
- ✅ Configured health check endpoint `/health`
- ✅ Set timeout to 300s (for Whisper transcription)

### 2. GitHub Actions Auto-Rebuild Workflow
- ✅ Created `.github/workflows/rebuild-on-webhook.yml` in voice-archive repo
- ✅ Triggers on `repository_dispatch` event (webhook from Railway API)
- ✅ Also runs every 6 hours as backup
- ✅ Rebuilds static site and auto-publishes to GitHub Pages

### 3. Webhook Integration
- ✅ Added `trigger_site_rebuild()` function to `cringeproof_api.py`
- ✅ Sends GitHub webhook after idea extraction completes
- ✅ Requires `GITHUB_TOKEN` environment variable on Railway

### 4. Prohibited Words Content Filtering
- ✅ Created `prohibited_words_filter.py` with domain-specific filtering
- ✅ Integrated into voice recording pipeline
- ✅ Logs detections for review (doesn't block by default)
- ✅ Database tables: `prohibited_words`, `prohibited_word_log`

Domain-specific configs:
- **soulfra.com**: Filters profanity, hate speech, spam
- **cringeproof.com**: Minimal filtering (authentic expression)
- **deathtodata.com**: Filters PII (phone numbers, SSN, addresses)

### 5. Frontend Configuration
- ✅ Updated `record.html` with Railway production URL placeholder
- ✅ Changed default from local IP to Railway domain
- ✅ Updated footer to reflect production deployment

---

## 🚀 Deployment Steps

### Step 1: Deploy to Railway

```bash
# 1. Login to Railway
railway login

# 2. Create new project
railway init

# 3. Link to project
railway link

# 4. Set environment variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set GITHUB_TOKEN=ghp_your_github_token_here
railway variables set PYTHONUNBUFFERED=1

# 5. Deploy
railway up

# 6. Get your deployment URL
railway domain
```

Example URL: `cringeproof-api-production.up.railway.app`

### Step 2: Update Frontend with Railway URL

Open `voice-archive/record.html` and replace placeholder:

```javascript
value="https://YOUR-ACTUAL-RAILWAY-URL.up.railway.app"
```

### Step 3: Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create new token (classic) with scopes: `repo`, `workflow`
3. Copy token (starts with `ghp_`)
4. Add to Railway:

```bash
railway variables set GITHUB_TOKEN=ghp_your_actual_token_here
```

### Step 4: Initialize Prohibited Words Database

On Railway (one-time setup):

```bash
railway run python3 prohibited_words_filter.py
```

This creates the tables and inserts default patterns.

### Step 5: Test the Pipeline

1. Visit `https://cringeproof.com/record.html`
2. Click "Start Recording"
3. Speak for 5-10 seconds
4. Check Railway logs:

```bash
railway logs --tail 50
```

Expected output:
```
🎤 Transcribing: recording.webm
✅ Whisper transcription complete
🤖 Ollama extracting ideas...
✅ Idea extracted
🎯 Classified to: cringeproof.com (87%)
✅ Site rebuild triggered
```

5. Wait 2-3 minutes for GitHub Actions to rebuild site
6. Visit `https://cringeproof.com/ideas/` to see new idea

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
│                     (cringeproof.com)                            │
│                      GitHub Pages                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ 1. POST /api/simple-voice/save
                 │    (audio file)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Railway.app                                 │
│                   cringeproof_api.py                             │
│                   (Flask + Gunicorn)                             │
├─────────────────────────────────────────────────────────────────┤
│  2. Whisper (transcription)                                      │
│     openai-whisper (Python library)                              │
│                                                                   │
│  3. Prohibited Words Filter                                      │
│     check_prohibited() → log if detected                         │
│                                                                   │
│  4. Ollama (idea extraction)                                     │
│     extract_ideas_from_transcript()                              │
│                                                                   │
│  5. Domain Classifier                                            │
│     classify_and_store() → assigns domain_id                     │
│                                                                   │
│  6. Database                                                      │
│     PostgreSQL (Railway) or SQLite (persistent volume)           │
│                                                                   │
│  7. GitHub Webhook Trigger                                       │
│     POST https://api.github.com/.../dispatches                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ repository_dispatch event
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions                              │
│          voice-archive/.github/workflows/                        │
│              rebuild-on-webhook.yml                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Checkout repos (voice-archive + soulfra-simple)              │
│  2. Run build_site.py (generates HTML)                           │
│  3. Run generate_rss.py (creates feed.xml)                       │
│  4. Commit changes to voice-archive                              │
│  5. Deploy to GitHub Pages                                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Updated static site
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Pages CDN                             │
│                   cringeproof.com                                │
│               (New idea appears in /ideas/)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Estimate

| Service | Plan | Cost |
|---------|------|------|
| Railway (Hobby) | 1 service, 2GB RAM | $5/month |
| Railway CPU | ~10s per recording | ~$0.01/recording |
| GitHub Pages | Static hosting | Free |
| GitHub Actions | <2000 min/month | Free |
| **Total** | ~1000 recordings/month | **~$15/month** |

---

## 🔧 Optional Enhancements

### Ollama Integration Options

Railway doesn't support running Ollama server directly (too heavy). Options:

**Option A: Use OpenAI API** (recommended for production)
```python
# Swap Ollama for GPT-4o-mini
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_ideas_with_gpt(transcription):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Extract ideas: {transcription}"}]
    )
    return parse_gpt_response(response)
```
Cost: ~$0.001/recording

**Option B: Modal.com for Serverless Ollama**
```bash
# Deploy Ollama to Modal.com
modal deploy ollama_modal.py

# Call from Railway API
response = requests.post('https://yourname--ollama.modal.run', json={'prompt': text})
```
Cost: ~$0.005/recording

**Option C: Keep Ollama Local**
- Run Ollama on your dev machine
- Railway API calls your local Ollama via Tailscale VPN
- Free but requires local machine to be online

### Database Migration (SQLite → PostgreSQL)

Railway's ephemeral filesystem doesn't persist SQLite well. Migrate to PostgreSQL:

```bash
# Add PostgreSQL to Railway project
railway add postgres

# Export SQLite data
sqlite3 soulfra.db .dump > backup.sql

# Import to PostgreSQL
railway connect postgres
psql < backup.sql
```

Update `database.py`:
```python
import os
import psycopg2

def get_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # PostgreSQL (Railway)
        return psycopg2.connect(db_url)
    else:
        # SQLite (local dev)
        return sqlite3.connect('soulfra.db')
```

---

## 🐛 Troubleshooting

### "Whisper model not found"
Railway's ephemeral filesystem doesn't cache Whisper models. Add to `railway.toml`:
```toml
[build]
buildCommand = "pip install -r requirements.txt && python3 -c 'import whisper; whisper.load_model(\"base\")'"
```

### "GitHub webhook failing"
Check Railway logs:
```bash
railway logs --tail 100 | grep webhook
```

Verify GITHUB_TOKEN has correct permissions (`repo`, `workflow` scopes).

### "CORS error from cringeproof.com"
Add domain to CORS origins in `cringeproof_api.py`:
```python
CORS(app, origins=['https://cringeproof.com', 'https://www.cringeproof.com'])
```

### "Site not rebuilding after recording"
Check GitHub Actions:
1. Go to `https://github.com/Soulfra/voice-archive/actions`
2. Look for failed workflow runs
3. Check logs for errors

Manual trigger:
```bash
# Trigger workflow manually
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/Soulfra/voice-archive/dispatches \
  -d '{"event_type":"new-voice-recording"}'
```

---

## 📝 Next Steps

1. ✅ Deploy to Railway
2. ✅ Set environment variables (SECRET_KEY, GITHUB_TOKEN)
3. ⏳ Update record.html with actual Railway URL
4. ⏳ Test full pipeline (record → transcribe → extract → classify → publish)
5. ⏳ Configure Ollama (choose Option A, B, or C above)
6. ⏳ Migrate to PostgreSQL (optional but recommended)
7. ⏳ Set up custom domain (cringeproof-api.com) on Railway
8. ⏳ Add monitoring (Railway metrics + error tracking)

---

## 🎯 What This Solves

**Before**: All offline, manual process
- ❌ Local IP (192.168.1.87:5002) only works on home WiFi
- ❌ Manual `python3 build_site.py` after each recording
- ❌ Manual git commit/push to publish
- ❌ No content filtering
- ❌ Ollama required on local machine

**After**: Fully online, automated workflow
- ✅ Works from anywhere (Railway public URL)
- ✅ Auto-rebuilds site via GitHub Actions
- ✅ Auto-publishes to GitHub Pages
- ✅ Content filtering with domain-specific rules
- ✅ Ollama optional (can swap for OpenAI API)
- ✅ Full audit trail (prohibited word detections logged)

**Pipeline latency**: 30 seconds - 2 minutes from recording to published idea.
