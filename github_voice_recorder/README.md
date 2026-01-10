# 🎤 Soulfra Voice Recorder (GitHub Pages)

HTTPS-enabled voice recorder that runs on GitHub Pages and sends recordings to your local Flask server.

## 🔐 Why GitHub Pages?

**Problem:** Modern browsers require HTTPS to access microphone
- ❌ `http://192.168.1.87:5001/voice` → Mic blocked by browser
- ✅ `https://yourusername.github.io/voice-recorder/` → Mic allowed!

**Solution:** Host static HTML on GitHub Pages (free SSL), record audio, send to local server

## 🚀 Quick Setup

### Option 1: Deploy to GitHub Pages

```bash
# 1. Create GitHub repo
gh repo create soulfra-voice-recorder --public

# 2. Push files
cd github_voice_recorder
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/soulfra-voice-recorder.git
git push -u origin main

# 3. Enable GitHub Pages
# Go to repo Settings → Pages → Source: main branch → Save

# 4. Visit your site
# https://YOUR_USERNAME.github.io/soulfra-voice-recorder/
```

### Option 2: Test Locally (Self-Signed SSL)

```bash
# Generate SSL certificate
python3 ../ssl_local_server.py --generate

# Start Flask with HTTPS
python3 ../ssl_local_server.py --serve

# Open in browser
open https://192.168.1.87:5001/voice

# Accept security warning (self-signed cert)
```

## 📱 iPhone/Mobile Setup

### Method 1: GitHub Pages (Recommended)

1. Deploy to GitHub Pages (see above)
2. On iPhone, visit: `https://YOUR_USERNAME.github.io/soulfra-voice-recorder/`
3. Enter local server URL: `https://192.168.1.87:5001`
4. Tap "TAP TO RECORD"
5. Recording uploads to your local server automatically!

### Method 2: Self-Signed SSL (Local Only)

1. Generate SSL cert: `python3 ssl_local_server.py --generate`
2. Start HTTPS server: `python3 ssl_local_server.py --serve`
3. On iPhone, visit: `https://192.168.1.87:5001/voice`
4. Tap "Show Details" → "Visit this website"
5. Mic access now works!

## 🌉 Architecture

```
GitHub Pages (HTTPS)
    ↓ Records audio
    ↓ (WebM blob)
    ↓
Local Network
    ↓ HTTPS POST
    ↓
Flask Server (192.168.1.87:5001)
    ↓ Saves to database
    ↓ Transcribes with Whisper
    ↓
SQLite Database
```

## 🔧 Configuration

### Update Server URL

In `index.html`, change default server:

```javascript
<input
    type="text"
    id="serverUrl"
    value="https://YOUR_LOCAL_IP:5001"
>
```

### CORS Setup (Flask)

Your Flask server needs CORS headers to accept requests from GitHub Pages:

```python
# In app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    'https://yourusername.github.io',
    'https://192.168.1.87:5001'
])
```

Or manually:

```python
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
```

## 🎯 Features

- ✅ HTTPS (browser mic access works)
- ✅ Mobile-friendly design
- ✅ Recording timer
- ✅ Automatic upload to local server
- ✅ Shows transcription after upload
- ✅ Saves server URL in localStorage
- ✅ Works offline (once loaded)

## 🔗 Pair with Ollama

Combine with `ollama_websocket_bridge.py` to:

1. Record voice on GitHub Pages (HTTPS)
2. Upload to local Flask server
3. Transcribe with Whisper
4. Send transcription to Ollama via WebSocket
5. Get AI response
6. Synthesize in your voice with TTS

Full offline-first AI voice assistant!

## 📝 Files

- `index.html` - Voice recorder UI
- `README.md` - This file
- `_config.yml` - GitHub Pages config (optional)

## 🐛 Troubleshooting

### "Mic access denied"

- Must use HTTPS (not HTTP)
- Or use localhost (exception to HTTPS rule)
- Or use self-signed SSL certificate

### "Upload failed"

- Check server URL is correct
- Make sure Flask is running
- Enable CORS on Flask server
- Check firewall allows port 5001

### "Certificate invalid"

- Self-signed certs show browser warnings (expected)
- Click "Advanced" → "Proceed anyway"
- Or use GitHub Pages for trusted SSL

## 🚀 Next Steps

1. Deploy to GitHub Pages
2. Test on iPhone
3. Connect to Ollama WebSocket bridge
4. Add voice cloning with Piper TTS
5. Build full voice AI assistant!

---

**Status:** ✅ Ready to deploy

**Like:** Voice memos meets GitHub Pages meets local AI
