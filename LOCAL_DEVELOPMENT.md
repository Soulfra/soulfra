# 🛠️ Local Development - Quick Start

## What You Just Got

✅ **Simple HTTP server** (no Flask dependencies)
✅ **Voice input** (speak instead of type)
✅ **Keyboard shortcuts** (accessibility)
✅ **Deploy script** (push to GitHub Pages)

---

## Start Local Server

```bash
./start_local_server.sh
```

**Opens:**
- 🏠 Main site: http://localhost:8000
- 🎤 Voice input: http://localhost:8000/voice-input.html

---

## Use Voice Input

1. Open: http://localhost:8000/voice-input.html
2. Click **"Start Speaking"** (or press `Ctrl+Space`)
3. Talk instead of typing
4. Text appears in real-time
5. Click **"Copy to Clipboard"** when done

### Voice Shortcuts
- `Ctrl+Space` - Toggle voice on/off
- `Ctrl+K` - Clear text
- `Ctrl+/` - Show all shortcuts

---

## Deploy to Production

When you're ready to push to soulfra.com:

```bash
./deploy.sh "your commit message"
```

**Example:**
```bash
./deploy.sh "Add voice input feature"
```

**What it does:**
1. Copies files to `output/soulfra/`
2. Git commit
3. Push to GitHub
4. Site updates in 2-5 minutes

**Live at:** https://soulfra.com

---

## Workflow

### 1. Local Development
```bash
# Start server
./start_local_server.sh

# Use voice input to work faster
# Visit: http://localhost:8000/voice-input.html
```

### 2. Make Changes
- Edit HTML files
- Refresh browser (Ctrl+R)
- Test locally

### 3. Deploy
```bash
./deploy.sh "Describe your changes"
```

### 4. Verify
- Wait 2-5 minutes
- Visit: https://soulfra.com
- Check changes are live

---

## Files Created

| File | Purpose |
|------|---------|
| `start_local_server.sh` | Run local HTTP server on port 8000 |
| `voice-input.html` | Voice-to-text interface (Web Speech API) |
| `keyboard-shortcuts.js` | Global keyboard shortcuts |
| `deploy.sh` | Push changes to GitHub Pages |

---

## Keyboard Shortcuts (Global)

Press `Ctrl+/` anywhere to see full list:

- `Ctrl+Space` - Toggle voice input
- `Ctrl+K` - Clear text
- `Ctrl+H` - Go to home
- `Ctrl+D` - Go to domains
- `Ctrl+Shift+C` - Copy all text
- `Ctrl+/` - Show help

---

## Why This Works

### No Flask Required
- Flask was broken (missing 50+ dependencies)
- Python's built-in `http.server` just works
- Perfect for static HTML sites

### Voice Input = Web Speech API
- Built into Chrome/Edge
- No server required
- Real-time transcription
- Continuous listening mode

### Separate Local vs Production
- Local: `soulfra-simple/` (development)
- Deploy: `output/soulfra/` (GitHub Pages)
- Git: Separate repos, no conflicts

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is busy
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Try again
./start_local_server.sh
```

### Voice not working
- Use Chrome or Edge (Safari doesn't support Web Speech API)
- Allow microphone permissions
- Check: chrome://settings/content/microphone

### Deploy failed
```bash
cd output/soulfra
git status
git pull origin main
cd ../..
./deploy.sh "retry deployment"
```

---

## Next Steps

1. **Start server:** `./start_local_server.sh`
2. **Open voice input:** http://localhost:8000/voice-input.html
3. **Make changes**
4. **Deploy:** `./deploy.sh "your message"`

**You can now speak instead of typing! 🎤**
