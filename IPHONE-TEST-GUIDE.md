# iPhone Testing Guide - Soulfra Unified System

**Your Local IP:** `192.168.1.87`

## Quick Start (5 Seconds)

1. Make sure laptop and iPhone are on **same WiFi**
2. Open Safari on iPhone
3. Go to: **`http://192.168.1.87:5001/dashboard`**
4. Bookmark it!

## What You'll See

### Unified Dashboard
- All systems in one place
- Search across all content
- QR faucet generator
- AI chat interface
- Canvas drawing tool
- Live stats (users, posts, QR scans)

### Links to Deployed Sites
- Soulfra (soulfra.github.io/soulfra)
- CalRiven (soulfra.github.io/calriven)
- DeathToData (soulfra.github.io/deathtodata)
- HowToCookAtHome (soulfra.github.io/howtocookathome)

## Testing Checklist

### ✅ Dashboard Access
```
http://192.168.1.87:5001/dashboard
```
Should load unified dashboard with all features.

### ✅ Search
```
http://192.168.1.87:5001/search
```
AI-powered search across all content.

### ✅ QR Faucet
```
http://192.168.1.87:5001/qr-search-gate
```
Generate QR codes for content/access.

### ✅ AI Chat
```
http://192.168.1.87:5001/chat
```
Chat with Ollama models.

### ✅ Canvas/Drawing
```
http://192.168.1.87:5001/draw
```
Mobile-friendly drawing tool with OCR.

### ✅ Status Page
```
http://192.168.1.87:5001/status
```
System status and all available routes.

## QR Code Testing

### Generate Dashboard QR Code

On laptop:
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
curl http://localhost:5001/api/qr/dashboard -o dashboard-qr.png
open dashboard-qr.png
```

Scan with iPhone camera → Opens dashboard directly!

### Print QR Code for Easy Access

Generate printable QR code:
1. Visit: http://192.168.1.87:5001/dashboard
2. Scroll to "Scan to Access from iPhone" section
3. QR code is already there!
4. Take screenshot or print

## All Available URLs (iPhone-Friendly)

| Feature | URL | What It Does |
|---------|-----|--------------|
| **Dashboard** | http://192.168.1.87:5001/dashboard | Main hub |
| **Search** | http://192.168.1.87:5001/search | AI search |
| **Gated Search** | http://192.168.1.87:5001/gated-search | QR-protected search |
| **QR Faucet** | http://192.168.1.87:5001/qr-search-gate | Generate QR codes |
| **Chat** | http://192.168.1.87:5001/chat | AI chat |
| **Domain Chat** | http://192.168.1.87:5001/domain-chat | Multi-domain chat |
| **Canvas** | http://192.168.1.87:5001/admin/canvas | Netflix-style entry |
| **Drawing** | http://192.168.1.87:5001/draw | Drawing tool |
| **Status** | http://192.168.1.87:5001/status | System status |
| **Routes** | http://192.168.1.87:5001/status/routes | All routes |
| **Generator** | http://192.168.1.87:5001/generate | Content generation |
| **QR Gallery** | http://192.168.1.87:5001/admin/qr-gallery | QR analytics |

## What's Running

**Flask Server:**
- Port: 5001
- IP: 192.168.1.87
- Database: soulfra.db (150+ tables)

**Ollama:**
- Port: 11434
- Models: llama3.2, etc.
- Status: ✅ Running

**Node.js Servers:**
- Port: 3000 (logo generator)
- Port: another (Picture of Day)

## Troubleshooting

### Can't Connect from iPhone

**1. Check same WiFi:**
```bash
# On laptop
ifconfig | grep "inet " | grep -v 127.0.0.1

# Should show: 192.168.1.87
```

**2. Check Flask is running:**
```bash
curl http://localhost:5001/dashboard
# Should return HTML
```

**3. Check firewall:**
```bash
# macOS - allow port 5001
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
```

**4. Restart Flask:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
pkill -f "python3 app.py"
python3 app.py
```

### Slow Performance on iPhone

**Normal!** Running Ollama on laptop, iPhone makes HTTP requests.

**Faster options:**
- Use lighter models (llama3.2:1b instead of llama3.2)
- Run on same device (not possible for iPhone)
- Deploy to cloud server

### SSL/HTTPS Warnings

Using `http://` (not `https://`) is normal for local development.

Safari may warn "Not Secure" - this is safe on your local network.

## Advanced: Using ngrok (Access from Anywhere)

If you want to test from anywhere (not just same WiFi):

```bash
# Install ngrok
brew install ngrok

# Expose Flask server
ngrok http 5001

# Get public URL
# Example: https://abc123.ngrok.io

# Access from iPhone anywhere
https://abc123.ngrok.io/dashboard
```

## Database Inspection (from iPhone)

**View database stats:**
```
http://192.168.1.87:5001/status
```

Shows:
- Total users
- Total posts
- QR scans
- All tables

**Export data:**
```
http://192.168.1.87:5001/api/export
```

## Creating an Account (from iPhone)

1. Visit: `http://192.168.1.87:5001/qr-search-gate`
2. Scan QR code with iPhone camera
3. Creates session automatically
4. Can now search, chat, etc.

## Testing the Triple-Domain System

The NEW triple-domain system we built is separate:

**Start it:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/Soulfra
bash START-ALL.sh
```

**Test on iPhone:**
```
http://192.168.1.87:8001  # soulfra.com landing page
http://192.168.1.87:5002  # soulfraapi.com API
http://192.168.1.87:5003  # soulfra.ai chat
```

**BUT** - We recommend using the unified dashboard instead (port 5001) which has everything!

## Mobile-Optimized Features

These work great on iPhone:

- ✅ Dashboard (responsive design)
- ✅ Search (mobile-friendly input)
- ✅ Drawing tool (touch-enabled)
- ✅ QR scanning (camera integration)
- ✅ Chat (mobile UI)

## Bookmarking on iPhone

1. Open: `http://192.168.1.87:5001/dashboard`
2. Tap Share button
3. "Add to Home Screen"
4. Name it "Soulfra"
5. Now acts like an app!

## Next Steps

1. ✅ Test dashboard on iPhone
2. ✅ Scan QR code to access
3. ✅ Try search, chat, canvas
4. Deploy CalRiven search page
5. Connect to existing deployed sites
6. Build out the ecosystem

## Summary

**Local IP:** 192.168.1.87
**Main URL:** http://192.168.1.87:5001/dashboard
**All systems working!**

Open Safari on iPhone, go to that URL, and explore!
