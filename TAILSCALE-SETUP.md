# Tailscale Funnel Setup - Permanent URL for Flask Backend

Get a stable, self-hosted URL for your Flask backend without Cloudflare dependency.

## What is Tailscale Funnel?

- **Free mesh VPN** - Creates encrypted network between your devices
- **Permanent URL** - Get `https://your-laptop.tailscale-funnel.com` that never changes
- **No port forwarding** - Works behind NAT without router configuration
- **Self-hosted** - You control everything, no cloud dependency

## Setup Steps

### 1. Install Tailscale (One-time)

```bash
# macOS (using Homebrew)
brew install tailscale

# Or download from: https://tailscale.com/download
```

### 2. Create Free Account

```bash
# Start Tailscale
sudo tailscale up

# Follow the browser prompt to create free account
# Uses GitHub, Google, or Microsoft for auth
```

### 3. Enable Funnel for Flask

```bash
# Expose Flask backend (running on localhost:5001) to public internet
tailscale funnel --bg --https=443 https://localhost:5001
```

**Your permanent URL:**
```
https://your-macbook-name.tailscale-funnel.com
```

The URL is based on your machine's name. To customize:
```bash
sudo tailscale up --hostname=cringeproof-backend
# URL becomes: https://cringeproof-backend.tailscale-funnel.com
```

### 4. Update CringeProof Config

Edit `voice-archive/config.js`:

```javascript
const CONFIG = {
    API_BACKEND_URL: (() => {
        const hostname = window.location.hostname;

        // Local testing
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'https://localhost:5001';
        }

        // Production - Tailscale Funnel (PERMANENT URL)
        return 'https://cringeproof-backend.tailscale-funnel.com';
    })()
};
```

### 5. Test Connection

```bash
# From any device (doesn't need Tailscale installed)
curl https://cringeproof-backend.tailscale-funnel.com/api/health

# Should return:
{"status":"ok","timestamp":"2026-01-04T..."}
```

### 6. Deploy to GitHub Pages

```bash
cd voice-archive
git add config.js
git commit -m "Switch to Tailscale Funnel (permanent URL)"
git push origin main
```

Wait 2-3 minutes for GitHub Pages rebuild, then visit:
```
https://cringeproof.com/record-simple.html
```

## How It Works

```
User's Browser
     ↓
cringeproof.com (GitHub Pages)
     ↓
config.js detects production
     ↓
Calls: https://cringeproof-backend.tailscale-funnel.com/api/...
     ↓
Tailscale Funnel (edge server)
     ↓
Encrypted tunnel to your Mac
     ↓
Flask (localhost:5001)
     ↓
Whisper AI transcribes
     ↓
Response back through tunnel
     ↓
User sees transcription
```

## Laptop Online/Offline Behavior

### Laptop Open (Flask Running)
- ✅ All API calls work
- ✅ Recordings uploaded immediately
- ✅ Real-time transcription
- ✅ Connection badge shows "Backend Online"

### Laptop Closed (Flask Offline)
- ✅ Recordings save to IndexedDB (local browser storage)
- ✅ Service worker queues uploads
- ✅ Connection badge shows "Backend Offline (X queued)"
- ⏳ Queue auto-processes when laptop comes back online

### Laptop Reconnects
- 🔄 Connection monitor detects Flask is back
- 🚀 Queue manager processes all pending uploads
- ✅ Transcriptions appear retroactively
- 🎉 User sees "X recordings synced"

## Benefits Over Cloudflare Tunnel

| Feature | Cloudflare Tunnel | Tailscale Funnel |
|---------|------------------|------------------|
| **URL Stability** | Changes every restart | Permanent |
| **Account Required** | Optional (quick tunnels) | Yes (free) |
| **Self-Hosted** | Cloudflare edge servers | Your Tailscale mesh |
| **Uptime Guarantee** | None (quick tunnels) | Same as your laptop |
| **Setup Complexity** | Low | Low |
| **Zero-Trust Security** | Basic | Advanced |

## Advanced: Named Cloudflare Tunnel Alternative

If you prefer Cloudflare, use **named tunnels** instead of quick tunnels:

```bash
# One-time setup
cloudflared tunnel login
cloudflared tunnel create cringeproof
cloudflared tunnel route dns cringeproof cringeproof-api.yourdomain.com

# Run tunnel (URL never changes)
cloudflared tunnel run cringeproof
```

**Named tunnel URL:** `https://cringeproof-api.yourdomain.com` (permanent)

## Troubleshooting

### Funnel URL returns 502 Bad Gateway
```bash
# Check if Tailscale is running
tailscale status

# Restart funnel
tailscale funnel --bg --https=443 https://localhost:5001
```

### Flask not accepting connections
```bash
# Verify Flask is running
curl https://localhost:5001/api/health

# Check Flask is using HTTPS (not HTTP)
# Flask must serve HTTPS for Funnel to work
```

### Connection monitor shows "Offline" but Flask is running
- Check browser console for CORS errors
- Verify `/api/health` endpoint exists in Flask
- Test direct curl to Funnel URL

## Monitoring

View Tailscale Funnel logs:
```bash
tailscale funnel status
```

View active connections:
```bash
tailscale status
```

## Keeping It Running

### Auto-start Tailscale on boot (macOS)
```bash
# Tailscale app starts automatically
# Funnel needs manual restart after reboot

# Add to ~/.zshrc or launch agent:
tailscale funnel --bg --https=443 https://localhost:5001
```

### Keep Flask running 24/7
Use a process manager like `pm2` or `supervisord`:

```bash
# Install pm2
npm install -g pm2

# Start Flask with pm2
cd /path/to/soulfra-simple
pm2 start app.py --interpreter python3 --name flask-backend

# Auto-start on boot
pm2 startup
pm2 save
```

## Security Notes

- Tailscale Funnel exposes Flask to public internet
- Flask's `/api/health` endpoint is public (intentional - for connection monitoring)
- All other endpoints should require authentication
- Funnel uses Tailscale's TLS certificates (auto-renewed)
- Traffic is encrypted end-to-end

## Cost

**Free tier includes:**
- ✅ Up to 100 devices
- ✅ Unlimited Funnel bandwidth
- ✅ Permanent URLs
- ✅ Zero-trust security

**Paid plans ($6/user/month):**
- Multiple users
- Advanced ACLs
- SSO integration

For personal use (1 user, 1 backend), **free tier is sufficient**.

## Next Steps

After Tailscale Funnel is running:

1. **Test offline queueing:**
   - Stop Flask (`ctrl+C`)
   - Record voice memo at cringeproof.com/record-simple.html
   - See "Backend Offline (1 queued)" badge
   - Restart Flask
   - Watch queue auto-process

2. **Monitor connection:**
   - Click connection badge to manually refresh
   - Check browser console for queue manager logs
   - View IndexedDB in DevTools → Application → Storage

3. **Deploy updates:**
   - All changes to `voice-archive/` auto-deploy via GitHub Pages
   - Service worker updates on refresh
   - No backend restart needed for frontend changes

---

**You now have a self-hosted, offline-first voice archive with permanent URL.**
