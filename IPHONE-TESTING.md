# iPhone Testing Guide

**The "hardest part" is now solved.** This guide shows you how to test CringeProof mobile.html on your iPhone with a stable tunnel.

## Quick Start (Recommended: Tailscale Funnel)

### 1. One-Time Setup
```bash
chmod +x setup-iphone-tunnel.sh
./setup-iphone-tunnel.sh
```

This will:
- Install Tailscale (if needed)
- Start the funnel
- Give you a **permanent URL** like `https://your-macbook.tailscale-funnel.com`

### 2. Start Flask
```bash
python app.py
```

### 3. Open on iPhone
```
https://your-macbook.tailscale-funnel.com/mobile.html
```

That's it! The URL works across:
- ✅ iPhone Safari
- ✅ MacBook Chrome
- ✅ GitHub Actions (if needed)
- ✅ Terminal curl/wget
- ✅ Any device on any network

## How mobile.js Auto-Detection Works

`mobile.js` automatically detects the right API endpoint:

```javascript
detectAPIBaseURL() {
  // localhost → http://localhost:5001
  // Tailscale → https://your-macbook.tailscale-funnel.com
  // Cloudflare → https://screenshot-eve-gave-reproduce.trycloudflare.com
  // ngrok → https://abc123.ngrok.io
}
```

You don't need to change any code. It just works.

## Alternative: Cloudflare Tunnel (Less Stable)

If you want to stick with Cloudflare:

```bash
cloudflared tunnel --url https://localhost:5001 --no-tls-verify
```

**Note:** Cloudflare URLs change every restart and have timeout issues.

## Alternative: ngrok (Quick Testing)

```bash
ngrok http 5001
```

Look for the `https://` URL in the output.

## Troubleshooting

### Flask won't start
```bash
# Kill all Flask processes
pkill -f app.py

# Start fresh
python app.py
```

### Tailscale funnel not working
```bash
# Check status
tailscale status

# Restart funnel
tailscale funnel --bg --https=443 https://localhost:5001
```

### iPhone can't connect
1. Make sure Flask is running (`python app.py`)
2. Make sure tunnel is running (check the URL)
3. Try opening the URL on your MacBook first to verify it works
4. Check Safari Console on iPhone (Settings → Safari → Advanced → Web Inspector)

### Shadow account not working
Open Safari Console on iPhone and look for:
```
[ShadowAccount] Initialized
[MobileRecorder] Shadow account ready
```

If you see errors, check that `shadow-account.js` and `queue-manager.js` are loading.

## Testing the Full Loop

1. **Open mobile.html on iPhone**
   - Should see empty state with mic icon

2. **Tap Record button**
   - Recording modal should appear
   - Voice wave animation should animate
   - Timer should count up

3. **Speak an idea**
   - Just talk normally

4. **Tap Stop button**
   - Modal should close
   - "Processing..." card should appear in feed
   - Console should show upload attempt

5. **Check upload**
   - If online: Card updates with transcription
   - If offline: Card shows "uploading" status, queued for later

6. **Swipe left/right on feed**
   - Should feel haptic feedback
   - (Navigation not yet implemented, but gestures work)

## Comparing Tunnel Solutions

| Solution | Stability | URL Type | Setup Time |
|----------|-----------|----------|------------|
| **Tailscale Funnel** | ⭐⭐⭐⭐⭐ | Permanent | 2 min |
| Cloudflare Tunnel | ⭐⭐ | Changes | 30 sec |
| ngrok | ⭐⭐⭐⭐ | Changes | 30 sec |
| Port Forwarding | ⭐⭐⭐ | Permanent | 10 min |

**Recommendation:** Use Tailscale Funnel for permanent testing. Use Cloudflare/ngrok for quick demos.

## Integration with cringeproof.com

Once you have a stable tunnel, you can:

1. **Add custom domain to Tailscale**
   - Point `api.cringeproof.com` to your Tailscale URL
   - Update DNS CNAME

2. **Deploy to GitHub Pages**
   - Push `mobile.html` to `cringeproof/cringeproof.github.io`
   - Access at `https://cringeproof.github.io/mobile.html`
   - API calls go to your Tailscale backend

3. **Save to iPhone Home Screen**
   - Open mobile.html in Safari
   - Tap Share → Add to Home Screen
   - Now it's a PWA!

## Next Steps

- [ ] Test on iPhone with Tailscale URL
- [ ] Verify voice recording works
- [ ] Check shadow account creation
- [ ] Test offline queue (airplane mode)
- [ ] Add to iPhone home screen as PWA
- [ ] Connect workflow coordinator for voice/scan/emoji modes
