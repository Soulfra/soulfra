# Voice Submission System - Complete Setup

**Status:** ✅ LIVE
**URL:** http://localhost:5001/submit

---

## What's Working Now

### 1. Public Voice Submission
- **URL:** http://localhost:5001/submit
- No login required
- Record voice in browser
- AI processing (Whisper + Ollama)
- Rate limited (spam protection)

### 2. Integration Points

**Flask API** (localhost:5001)
- `/submit` - Public submission page
- `/api/submit-voice` - Voice upload endpoint
- `/voice/public/<id>` - View submitted voice

**Static Sites** (need updating)
- `voice-archive/record.html` - CringeProof recorder
- Currently points to `192.168.1.87:5002` (Ollama)
- Should point to `localhost:5001` (Flask API)

**Ollama** (192.168.1.87:5002)
- AI processing backend
- Flask proxies requests to it

---

## How to Use

### Test Public Submission

```bash
# Visit submission page
open http://localhost:5001/submit

# Or via curl
curl http://localhost:5001/submit
```

### Submit Voice Memo

1. Visit http://localhost:5001/submit
2. Select category (Complaint, Feedback, Idea, Other)
3. Optional: Enable encryption
4. Click "Start Recording"
5. Speak your message
6. Click "Stop Recording"
7. Get shareable link

---

## Connecting cringeproof.com/record

Your static `voice-archive/record.html` file needs to connect to Flask API.

### Current Setup (Not Working)
```
cringeproof.com/record.html (static HTML)
   ↓ tries to call
192.168.1.87:5002 (Ollama directly)
   ↓ PROBLEM: CORS, no Flask routes
```

### Fixed Setup (What You Need)
```
cringeproof.com/record.html (static HTML)
   ↓ calls
localhost:5001/api/* (Flask API with CORS)
   ↓ proxies to
192.168.1.87:5002 (Ollama)
```

---

## Next Steps

### Option 1: Serve Static HTML from Flask

Add route to serve `record.html`:

```python
@app.route('/record')
def record_page():
    return send_file('voice-archive/record.html')
```

Then visit: `http://localhost:5001/record`

### Option 2: Update Static HTML to Use Flask API

Change `voice-archive/record.html` to point to Flask:

```javascript
// OLD (direct to Ollama)
const OLLAMA_URL = 'https://192.168.1.87:5002';

// NEW (via Flask proxy)
const API_URL = 'http://localhost:5001/api';
```

### Option 3: Multi-Domain with CORS

Keep static files on cringeproof.com, enable CORS in Flask:

```python
from flask_cors import CORS
CORS(app, origins=['https://cringeproof.com'])
```

---

## Testing

### Test `/submit` Route

```bash
curl -s http://localhost:5001/submit | grep "Submit Voice"
# Should return HTML with "Submit Voice Memo" title
```

### Test Voice Upload

```bash
# Record test audio
ffmpeg -f lavfi -i "sine=frequency=1000:duration=2" -c:a libopus test.webm

# Upload to API
curl -X POST http://localhost:5001/api/submit-voice \
  -F "audio=@test.webm" \
  -F "category=complaint" \
  -F "encrypt=false" \
  -F "anonymous=true"

# Expected response:
{
  "success": true,
  "recording_id": 1,
  "share_url": "http://localhost:5001/voice/public/1",
  "message": "Voice memo submitted! AI will process it shortly."
}
```

### Test Public View

```bash
curl http://localhost:5001/voice/public/1
# Should show voice player + AI transcription
```

---

## Troubleshooting

### Problem: `/submit` returns 404

**Cause:** Flask didn't restart with new routes

**Fix:**
```bash
pkill -f "python.*app.py"
python3 app.py
```

### Problem: Static HTML can't connect to API

**Cause:** CORS not enabled or wrong URL

**Fix:**
1. Check `voice-archive/record.html` API URL
2. Enable CORS in Flask if cross-domain
3. Or serve HTML from Flask directly

### Problem: Ollama not responding

**Cause:** Ollama not running or wrong port

**Fix:**
```bash
# Check if Ollama is running
curl http://192.168.1.87:5002/api/tags

# Should return list of models
```

---

## Architecture

### Current (What You Have)

```
Browser
   ↓
localhost:5001 (Flask)
   ├─ /submit (public voice submission)
   ├─ /api/submit-voice (upload endpoint)
   ├─ /voice/public/<id> (view submission)
   └─ /api/* (other routes)

192.168.1.87:5002 (Ollama)
   └─ AI processing

voice-archive/*.html (static files)
   └─ Separate from Flask
```

### Goal (Unified)

```
localhost:5001 (Flask - ONE SERVER)
   ├─ /submit (public voice submission)
   ├─ /record (CringeProof recorder)
   ├─ /voice/* (playback routes)
   ├─ /api/submit-voice (upload)
   ├─ /api/ollama/* (proxy to Ollama)
   └─ /voice-archive/* (serve static files)

192.168.1.87:5002 (Ollama)
   └─ AI processing (proxied by Flask)
```

---

## Files

### Created Files
- `public_voice_submission.py` - Public voice submission system
- `NO_PHONE_NUMBERS_NEEDED.md` - Why we don't need phone numbers
- `OSS_ROADMAP.md` - Path to full decentralization
- `VOICE_SETUP_COMPLETE.md` - This file

### Modified Files
- `app.py` - Added public voice routes

### Existing Files (Separate)
- `voice-archive/record.html` - CringeProof recorder (needs integration)
- `simple_voice_routes.py` - QR auth voice recording
- `voice_federation_routes.py` - Federated encrypted voice

---

## Summary

✅ **Public voice submission is LIVE** at http://localhost:5001/submit
✅ **No login required** - anyone can submit
✅ **AI processing** - Whisper + Ollama
✅ **Rate limiting** - spam protection
✅ **Encryption option** - for privacy

🔜 **Next:** Integrate CringeProof recorder with Flask API
🔜 **Next:** Multi-domain setup (Soulfra, CalRiven, DeathToData, HowToCook)
🔜 **Next:** ActivityPub federation

---

**Your vision is correct: No phone numbers needed for AI interactions. Browser-only works perfectly.**
