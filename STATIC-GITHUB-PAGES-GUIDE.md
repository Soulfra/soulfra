# Static GitHub Pages + Ollama - Complete Guide

**The Simplest Possible Deployment**

No Railway, no Vercel, no Docker. Just GitHub Pages (free) + your Ollama (localhost).

---

## What You're Building

```
┌────────────────────────────────────────┐
│  GITHUB PAGES (Free, Always Online)   │
│  https://username.github.io/chat       │
│                                        │
│  • Static HTML file (static-chat.html)│
│  • Pure JavaScript                     │
│  • Works in any browser                │
└──────────────┬─────────────────────────┘
               │
               │ User enters API key
               │
               ▼
┌────────────────────────────────────────┐
│  OLLAMA PROXY (Your Mac)               │
│  https://abc123.ngrok.io               │
│                                        │
│  • Validates API keys                  │
│  • Proxies to localhost:11434          │
│  • 50 lines of Python                  │
└──────────────┬─────────────────────────┘
               │
               ▼
┌────────────────────────────────────────┐
│  OLLAMA (localhost:11434)              │
│  • Your local AI models                │
│  • No cloud costs                      │
└────────────────────────────────────────┘
```

---

## Setup (10 Minutes Total)

### Step 1: Deploy Static Chat to GitHub Pages (3 minutes)

1. **Create a GitHub repo** (or use existing):
   ```bash
   # Option A: Create new repo
   mkdir soulfra-chat
   cd soulfra-chat
   git init

   # Option B: Use existing repo
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   ```

2. **Copy the static HTML file**:
   ```bash
   cp static-chat.html index.html
   # OR rename it for clarity:
   # static-chat.html is ready to go!
   ```

3. **Push to GitHub**:
   ```bash
   git add static-chat.html  # or index.html
   git commit -m "Add static Ollama chat"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/soulfra-chat.git
   git push -u origin main
   ```

4. **Enable GitHub Pages**:
   - Go to repo Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/` (root)
   - Save

5. **Visit your site**:
   - URL: `https://YOUR_USERNAME.github.io/soulfra-chat/static-chat.html`
   - OR: `https://YOUR_USERNAME.github.io/soulfra-chat/` (if you named it index.html)

**Done!** Your chat interface is now live and free forever.

---

### Step 2: Start Ollama Proxy (2 minutes)

1. **Install dependencies**:
   ```bash
   pip install flask flask-cors requests
   ```

2. **Start the proxy**:
   ```bash
   python3 ollama_proxy.py
   ```

   You should see:
   ```
   ╔═══════════════════════════════════════╗
   ║     OLLAMA PROXY                     ║
   ╚═══════════════════════════════════════╝

   Proxy running on: http://localhost:8000
   Ollama target:    http://localhost:11434
   ```

3. **Test it**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"proxy": "online", "ollama": "online"}
   ```

---

### Step 3: Expose via ngrok (2 minutes)

1. **Install ngrok** (if not installed):
   ```bash
   brew install ngrok
   # OR download from: https://ngrok.com/download
   ```

2. **Sign up for free** (one-time):
   - Visit: https://ngrok.com/signup
   - Get your auth token
   - Run: `ngrok config add-authtoken YOUR_TOKEN`

3. **Start ngrok tunnel**:
   ```bash
   ngrok http 8000
   ```

   You'll see:
   ```
   Forwarding https://abc123.ngrok.io -> http://localhost:8000
   ```

4. **Copy the ngrok URL**:
   - Example: `https://abc123.ngrok.io`
   - This is your public Ollama proxy URL!

5. **Test it**:
   ```bash
   curl https://abc123.ngrok.io/health
   # Should work from anywhere!
   ```

---

### Step 4: Update Static HTML (1 minute)

1. **Edit `static-chat.html`**:
   - Find this line:
     ```javascript
     value="http://localhost:11434"
     ```
   - Change to your ngrok URL:
     ```javascript
     value="https://abc123.ngrok.io"
     ```

2. **Push update**:
   ```bash
   git add static-chat.html
   git commit -m "Update Ollama URL to ngrok"
   git push
   ```

3. **Wait 1 minute for GitHub Pages to rebuild**

---

### Step 5: Get an API Key (2 minutes)

You need an API key to use the chat. Two options:

#### Option A: Use Existing GitHub Faucet

If you already have the GitHub Faucet running:

1. Visit: `http://localhost:5001/github/connect`
2. Connect your GitHub account
3. Get your API key (format: `sk_github_yourname_abc123`)

#### Option B: Manually Create API Key

If you don't have the faucet running, manually create one:

```bash
python3 -c "
from database import get_db
import hashlib
import secrets

db = get_db()

# Create API key
username = 'yourname'
api_key = f'sk_github_{username}_{secrets.token_hex(8)}'

db.execute('''
    INSERT INTO api_keys (user_id, api_key, is_active, created_at)
    VALUES (1, ?, 1, datetime('now'))
''', (api_key,))

db.commit()
db.close()

print(f'API Key: {api_key}')
"
```

---

## How to Use

1. **Visit your GitHub Pages URL**:
   - `https://YOUR_USERNAME.github.io/soulfra-chat/static-chat.html`

2. **Enter your API key**:
   - Paste the API key from Step 5
   - Enter your ngrok URL (or keep default if you updated HTML)
   - Click "Save & Connect"

3. **Start chatting**:
   - Type a message
   - Press Enter or click Send
   - AI responds from your local Ollama!

---

## How It Works

### The Flow

```
1. User visits GitHub Pages
   └─ Static HTML loads in browser

2. User enters API key
   └─ Stored in localStorage (browser only)

3. User sends message
   └─ JavaScript makes fetch() request to ngrok URL
   └─ ngrok tunnels to localhost:8000 (proxy)
   └─ Proxy validates API key against database
   └─ Proxy forwards request to localhost:11434 (Ollama)
   └─ Ollama generates response
   └─ Response travels back through tunnel to browser
   └─ JavaScript displays message
```

### Security

- **API keys** validated against your local database
- **CORS** enabled so GitHub Pages can call your proxy
- **HTTPS** via ngrok (encrypted)
- **Local Ollama** never exposed directly

---

## Advantages

### ✅ What's Great

1. **Free hosting**: GitHub Pages = $0
2. **No deployment**: Just push HTML file
3. **Always online**: GitHub Pages has 99.9% uptime
4. **Fast**: Static HTML loads instantly
5. **Simple**: One HTML file, that's it
6. **Flexible**: Easy to add features (just edit HTML)

### ⚠️ Limitations

1. **ngrok free tier**: URL changes when you restart (paid tier = permanent URL)
2. **Your Mac must be on**: Ollama runs on your machine
3. **API key management**: Manual (unless you run GitHub Faucet)

---

## Making It Better

### Use a Permanent URL (Optional)

Instead of ngrok, use:

- **Tailscale**: Permanent URL, free
  - Install: `brew install tailscale`
  - Setup: `tailscale up`
  - Get URL: `tailscale serve 8000`
  - Update HTML with Tailscale URL

- **Cloudflare Tunnel**: Permanent URL, free
  - Install: `brew install cloudflare/cloudflare/cloudflared`
  - Setup: `cloudflared tunnel create soulfra`
  - Get URL: `cloudflared tunnel route dns soulfra soulfra.yourdomain.com`

- **ngrok Pro**: Permanent URL, $8/month
  - Reserve domain: `ngrok http 8000 --domain=soulfra.ngrok.io`

### Add GitHub Faucet (Optional)

To automatically generate API keys:

1. Run GitHub Faucet on localhost:5001
2. Deploy it to Railway/Vercel (or keep local + ngrok)
3. Update link in static-chat.html footer:
   ```html
   <a href="https://your-faucet.railway.app">Connect GitHub</a>
   ```

---

## Troubleshooting

### "Connection error"

**Problem**: Can't reach Ollama proxy

**Fix**:
```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/tags

# 2. Check proxy is running
curl http://localhost:8000/health

# 3. Check ngrok is running
# Visit ngrok dashboard: http://localhost:4040
```

### "Invalid API key"

**Problem**: API key not recognized

**Fix**:
```bash
# Check if API key exists in database
python3 -c "
from database import get_db
db = get_db()
keys = db.execute('SELECT * FROM api_keys').fetchall()
for key in keys:
    print(f'{key[\"api_key\"]} - Active: {key[\"is_active\"]}')
db.close()
"
```

### "CORS error"

**Problem**: Browser blocks request

**Fix**:
- Make sure `ollama_proxy.py` has `CORS(app)` at the top
- Restart the proxy: `python3 ollama_proxy.py`

---

## Next Steps

### Add More Features to Static Page

Since it's just HTML, you can easily add:

1. **Red/Blue A/B Testing**:
   - Generate 2 responses
   - Show side-by-side
   - User picks winner

2. **Drag/Drop Images**:
   - Upload image to base64
   - Send to Ollama vision model
   - Display AI description

3. **Magic Eraser**:
   - Click parts of image to remove
   - Send masked image to AI
   - Get edited version

4. **Multiple Models**:
   - Dropdown to select model
   - Different personalities

All of this is just JavaScript - no backend changes needed!

---

## Summary

**What you deployed**:
- 1 static HTML file → GitHub Pages (free, always online)
- 1 Python proxy script → Your Mac (validates API keys)
- 1 ngrok tunnel → Expose locally (free tier works)

**Cost**: $0 (or $8/month for ngrok Pro if you want permanent URL)

**Deployment time**: 10 minutes

**Maintenance**: Restart ngrok when your Mac restarts (or use Tailscale for permanent)

**Scalability**: GitHub Pages can handle millions of users (only your Ollama is the bottleneck)

---

## Files Created

1. **`static-chat.html`** - The chat interface (deploy to GitHub Pages)
2. **`ollama_proxy.py`** - The API gateway (run on your Mac)
3. **`STATIC-GITHUB-PAGES-GUIDE.md`** - This guide

---

## Quick Start Commands

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start proxy
python3 ollama_proxy.py

# Terminal 3: Start ngrok
ngrok http 8000

# Then:
# 1. Push static-chat.html to GitHub
# 2. Enable GitHub Pages
# 3. Visit your page
# 4. Enter API key
# 5. Chat!
```

---

**That's it!** You now have a free, always-online chat interface that talks to your local Ollama. 🎉
