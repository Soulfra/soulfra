# Railway.app Deployment Guide

## Quick Deploy: CringeProof API

### 1. Create Railway Project

```bash
# Login to Railway (if not already)
railway login

# Initialize project in this directory
railway init

# Link to new project
railway link
```

### 2. Set Environment Variables

```bash
# Required
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set PYTHONUNBUFFERED=1
railway variables set WHISPER_MODEL=base

# Optional - for Ollama
railway variables set OLLAMA_HOST=http://localhost:11434
```

### 3. Deploy

```bash
# Deploy current code
railway up

# Watch logs
railway logs
```

### 4. Get Public URL

```bash
# Get your deployment URL
railway domain
```

Example: `cringeproof-api-production.up.railway.app`

---

## Post-Deployment Steps

### 1. Update Frontend (`voice-archive/record.html`)

Replace hardcoded local IP:
```javascript
// OLD
const serverUrl = 'https://192.168.1.87:5002';

// NEW
const serverUrl = 'https://cringeproof-api-production.up.railway.app';
```

### 2. Test the Pipeline

```bash
# Health check
curl https://cringeproof-api-production.up.railway.app/health

# Expected response:
# {
#   "status": "healthy",
#   "whisper": true,
#   "ollama": false,  # Will be false until Ollama configured
#   "classifier": true
# }
```

### 3. Upload Test Recording

Visit: `https://cringeproof.com/record.html`
- Click "Start Recording"
- Speak for 5 seconds
- Check Railway logs for processing

---

## Database Migration (SQLite → PostgreSQL)

### Option A: Keep SQLite (Persistent Volume)

Railway doesn't support SQLite well due to ephemeral filesystem.

**Workaround**: Mount Railway volume
```bash
railway volume create soulfra-db
railway volume mount soulfra-db /app/data
```

Update `database.py` to use `/app/data/soulfra.db`

### Option B: Migrate to PostgreSQL (Recommended)

```bash
# Add PostgreSQL service
railway add postgres

# Get connection string
railway variables

# Update database.py to use PostgreSQL
```

**Migration script**:
```python
# migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
import os

# Export SQLite data
sqlite_conn = sqlite3.connect('soulfra.db')
# Import to PostgreSQL (Railway provides DATABASE_URL)
pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
# ... migration logic
```

---

## Ollama Integration Options

### Option 1: Run Ollama on Railway (Complex)

```dockerfile
# Custom Dockerfile needed
FROM python:3.11
RUN curl -fsSL https://ollama.com/install.sh | sh
# ... start both Ollama server and Flask app
```

### Option 2: External Ollama Service

Use Modal.com or Replicate.com for serverless Ollama:

```python
# Replace ollama_client.py with API calls
import replicate

def extract_ideas_from_transcript(text, recording_id, user_id):
    output = replicate.run(
        "meta/llama-2-70b-chat",
        input={"prompt": f"Extract ideas from: {text}"}
    )
    return parse_ideas(output)
```

### Option 3: Swap for OpenAI API (Fastest)

```python
# In cringeproof_api.py
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_ideas_with_gpt(transcription):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Extract structured ideas from this voice memo: {transcription}"
        }]
    )
    return parse_gpt_response(response)
```

Cost: ~$0.001 per voice memo

---

## Monitoring & Debugging

### Check Logs
```bash
railway logs --tail 100
```

### SSH into Container
```bash
railway run bash
```

### Health Check Endpoint
```bash
curl https://your-app.up.railway.app/health
```

---

## Cost Estimate

| Resource | Usage | Cost |
|----------|-------|------|
| Railway Hobby Plan | 1 service | $5/month |
| CPU (Whisper transcription) | ~5s per recording | $0.01/recording |
| RAM (2GB) | Included | Free |
| Bandwidth | 100GB | Included |

**Total**: ~$5-10/month for <1000 recordings/month

---

## Troubleshooting

### "Module not found: whisper"
- Check buildCommand includes `pip install openai-whisper`
- Redeploy: `railway up`

### "Database locked"
- SQLite doesn't work well on Railway's ephemeral filesystem
- Use PostgreSQL instead (see migration above)

### "Timeout on /api/simple-voice/save"
- Whisper transcription can take 10-30s for long recordings
- Increase timeout in `railway.toml`: `--timeout 300`

### "CORS error from cringeproof.com"
- Check CORS origins in `cringeproof_api.py:29`
- Should include: `'https://cringeproof.com'`

---

## Next Steps

1. ✅ Deploy API to Railway
2. ⏳ Update `record.html` with production URL
3. ⏳ Set up GitHub Actions for auto-rebuild
4. ⏳ Add prohibited words filtering
5. ⏳ Configure Ollama (external service or OpenAI swap)
