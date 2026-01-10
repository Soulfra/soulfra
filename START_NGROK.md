# How to Get Your Phone Connected (ngrok Setup)

## Quick Start (5 minutes)

### 1. Install ngrok
```bash
brew install ngrok
```

### 2. Start ngrok tunnel
```bash
# This exposes port 5002 (your API) to the internet
ngrok http 5002
```

You'll see output like:
```
Forwarding  https://abc-123-def.ngrok-free.app -> http://localhost:5002
```

### 3. Copy that HTTPS URL

Example: `https://abc-123-def.ngrok-free.app`

### 4. Update record.html

In `voice-archive/record.html`, line 152-153, change:
```html
<input
    type="text"
    id="server-url"
    placeholder="https://abc-123-def.ngrok-free.app"
    value="https://abc-123-def.ngrok-free.app"
>
```

### 5. Commit and push
```bash
cd voice-archive
git add record.html
git commit -m "Use ngrok tunnel for phone access"
git push
```

### 6. Test from your phone

1. Open Safari/Chrome on your phone
2. Go to https://cringeproof.com/signup.html
3. Create account (first user = admin!)
4. Go to https://cringeproof.com/record.html
5. Click "Start Recording"
6. Speak your idea
7. Wait 30 seconds
8. Check https://cringeproof.com/ideas/ - your idea appears!

---

## Troubleshooting

### "Can't reach API"
- Make sure ngrok is running: `ngrok http 5002`
- Make sure your laptop API is running: `python3 cringeproof_api.py`
- Check the ngrok URL matches what's in record.html

### "ngrok URL changes every time"
- Free tier gets new URL each restart
- Paid tier ($8/month): Get fixed subdomain like `https://cringeproof.ngrok.io`
- OR use Tailscale (free, VPN to your laptop)

### "Whisper/Ollama too slow"
- ngrok adds ~100ms latency (not bad)
- Whisper transcription takes 5-30 seconds (normal)
- Ollama extraction takes 10-60 seconds (normal)
- Total: 30 seconds - 2 minutes from record → published

---

## Keep ngrok Running

### Option A: Keep terminal open
```bash
# Just leave this terminal window running
ngrok http 5002
```

### Option B: Run in background
```bash
# Install screen
brew install screen

# Start screen session
screen -S ngrok

# Run ngrok
ngrok http 5002

# Detach: Press Ctrl+A, then D
# Reattach later: screen -r ngrok
```

### Option C: Auto-start on login
```bash
# Create ~/Library/LaunchAgents/com.cringeproof.ngrok.plist
# (ngrok will auto-start when you log in)
```

---

## Alternative: Tailscale (VPN)

**If you don't want ngrok:**

1. Install Tailscale on laptop: `brew install tailscale`
2. Install Tailscale on phone (App Store)
3. Sign into same account on both
4. Phone can now reach `http://100.x.x.x:5002` (Tailscale IP)
5. No changes needed to record.html - just update server URL in the UI

**Pros**: Free, permanent URL, no ngrok subscription
**Cons**: Requires VPN app on phone

---

## Next Steps

Once ngrok is working:
1. Test signup/login from phone
2. Record voice memo from phone
3. Check it appears on cringeproof.com/ideas/
4. Set up admin panel (pricing, settings)
5. Add monetization hooks

You're 90% there!
