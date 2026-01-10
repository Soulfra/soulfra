# QR Gallery - Phone Testing Guide

**Status:** ✅ All features working locally
**Date:** 2025-12-27

---

## ✅ What's Working

1. **Gallery routes** - `/gallery/<slug>` serves QR galleries with tracking
2. **Gallery index** - `/galleries` lists all available galleries
3. **QR code display** - Galleries show QR code for easy phone scanning
4. **Navigation** - Galleries link to: Home, Post, All Galleries, Docs
5. **Lineage tracking** - Scans tracked with `previous_scan_id` (parent/child)
6. **Device detection** - iOS/Android/Desktop tracked
7. **Share URLs** - Include `?ref=<scan_id>` for viral tracking

---

## 🧪 Option 1: Test on Same WiFi (Fastest)

If your phone is on the same WiFi network as your computer:

### Step 1: Get your local IP

Your server is running on: **`http://192.168.1.123:5001`**

### Step 2: Test from phone browser

On your phone, open browser and visit:

```
http://192.168.1.123:5001/gallery/i-love-that-youre-considering-sharing-a-recipe-for
```

Or visit the galleries index:

```
http://192.168.1.123:5001/galleries
```

### Step 3: Test QR scanning

1. Visit gallery on phone
2. Scroll to "Share This Gallery" section
3. Take screenshot of QR code
4. Use phone camera or QR scanner app to scan
5. Should open same gallery with `?ref=` parameter

### Step 4: Verify lineage tracking

```bash
sqlite3 soulfra.db "SELECT id, device_type, previous_scan_id FROM qr_scans ORDER BY id DESC LIMIT 5;"
```

Should show:
- Scan #1: `previous_scan_id = NULL` (original)
- Scan #2: `previous_scan_id = 1` (child of #1)
- Scan #3: `previous_scan_id = 2` (grandchild)

---

## 🚀 Option 2: Deploy to Railway (Production)

For permanent deployment with HTTPS (required for QR scanning from other networks):

### Prerequisites

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or use Homebrew
brew install railway
```

### Step 1: Login to Railway

```bash
railway login
```

This opens browser for authentication.

### Step 2: Initialize project

```bash
railway init
```

Choose "Create new project" and give it a name (e.g., "soulfra-qr-galleries")

### Step 3: Add gunicorn to requirements

```bash
echo "gunicorn" >> requirements.txt
```

### Step 4: Deploy

```bash
railway up
```

This will:
1. Upload your code
2. Detect Python project
3. Install dependencies
4. Run database migrations
5. Start gunicorn server

### Step 5: Get your URL

```bash
railway domain
```

This generates a public HTTPS URL like:
**`https://soulfra-qr-galleries-production.up.railway.app`**

### Step 6: Set environment variables

```bash
railway variables set BASE_URL=https://your-app.up.railway.app
railway variables set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### Step 7: Regenerate QR codes with production URL

```bash
# Locally, with production URL
python3 qr_gallery_system.py --post 29 --base-url https://your-app.up.railway.app

# Upload new QR codes
railway run python3 qr_gallery_system.py --all
```

### Step 8: Test from phone

Open on phone:
```
https://your-app.up.railway.app/galleries
```

---

## 📱 Option 3: Quick Tunnel (No Account Needed)

Use localtunnel for instant public HTTPS URL:

### Step 1: Install localtunnel

```bash
npx localtunnel --port 5001
```

### Step 2: Get URL

Output will show:
```
your url is: https://random-word-1234.loca.lt
```

### Step 3: Test from phone

Visit `https://random-word-1234.loca.lt/galleries`

**Note:** localtunnel URLs change each time and may show a warning page first.

---

## 🧪 Option 4: Tailscale Funnel (Best for Testing)

Tailscale Funnel provides stable HTTPS without deployment:

### Step 1: Install Tailscale

```bash
# macOS
brew install tailscale

# Start Tailscale
sudo tailscale up
```

### Step 2: Enable Funnel

```bash
tailscale funnel 5001
```

### Step 3: Get URL

Output shows:
```
https://your-device.your-domain.ts.net
```

### Step 4: Test from anywhere

Your app is now accessible from any device via HTTPS.

---

## 🔍 Testing Checklist

### Basic Functionality
- [  ] `/galleries` loads and shows 1 gallery
- [ ] Clicking gallery card opens `/gallery/<slug>`
- [  ] Gallery displays QR code image
- [  ] Footer navigation links work (Home, Post, Galleries, Docs)

### QR Code Scanning
- [  ] Can scan QR code from gallery page
- [  ] Scanning opens correct gallery URL
- [  ] URL includes `?ref=<scan_id>` parameter

### Lineage Tracking
- [  ] First scan creates record with `previous_scan_id = NULL`
- [  ] Sharing from scan #1 creates scan #2 with `previous_scan_id = 1`
- [  ] Can view lineage tree: `python3 qr_analytics.py --tree --qr-code 1`

### Device Detection
- [  ] iOS device shows `device_type = 'iOS'`
- [  ] Android shows `device_type = 'Android'`
- [  ] Desktop shows `device_type = 'Desktop'`

### Analytics Dashboard
- [  ] `python3 qr_analytics.py --dashboard` generates HTML
- [  ] Dashboard shows scan count, device breakdown, locations

---

## 📊 View Analytics

### Check scan data

```bash
sqlite3 soulfra.db "SELECT * FROM qr_scans ORDER BY scanned_at DESC LIMIT 10;"
```

### Generate lineage tree

```bash
python3 qr_analytics.py --tree --qr-code 1
```

Output:
```
🌳 LINEAGE TREE - QR Code #1
Root #1:
├─ Scan #1 (iOS, San Francisco)
│  ├─ Scan #2 (Android, New York)  [child of #1]
│  │  └─ Scan #3 (iOS, London)     [grandchild]
│  └─ Scan #4 (Desktop, Tokyo)     [child of #1]
```

### View dashboard

```bash
python3 qr_analytics.py --dashboard
open output/analytics/qr_dashboard.html
```

---

## 🐛 Troubleshooting

### Gallery not found

**Error:** `Gallery not generated yet`

**Fix:**
```bash
python3 qr_gallery_system.py --post 29
```

### QR code not displaying

**Issue:** Image shows broken

**Fix:** Check QR code exists:
```bash
ls -la static/qr_codes/galleries/
```

If missing:
```bash
python3 qr_gallery_system.py --post 29
```

### Lineage not tracking

**Issue:** All scans show `previous_scan_id = NULL`

**Fix:** Ensure URL includes `?ref=` parameter when sharing. Update gallery template if needed.

### Railway deployment fails

**Error:** `Module not found: gunicorn`

**Fix:**
```bash
echo "gunicorn" >> requirements.txt
railway up
```

---

## 🎯 Success Criteria

✅ Can access gallery from phone
✅ QR code displays and is scannable
✅ Scanning creates new scan record
✅ Lineage tracking works (parent/child)
✅ Device type detected correctly
✅ Navigation links work
✅ Analytics dashboard shows data

---

## 📝 Next Steps After Testing

1. **Generate more galleries**
   ```bash
   python3 qr_gallery_system.py --all
   ```

2. **Create quizzes from posts**
   ```bash
   python3 post_to_quiz.py --all
   ```

3. **Deploy to production**
   ```bash
   railway up
   ```

4. **Share QR codes**
   - Print QR codes
   - Share via social media
   - Embed in blog posts
   - Track viral spread!

---

## 🔗 Useful Commands

```bash
# Start local server
python3 app.py

# Regenerate gallery
python3 qr_gallery_system.py --post <ID>

# View scans
sqlite3 soulfra.db "SELECT COUNT(*) FROM qr_scans;"

# View lineage
python3 qr_analytics.py --tree --qr-code <ID>

# Deploy to Railway
railway up

# View Railway logs
railway logs
```

---

**Server running on:** `http://192.168.1.123:5001`
**Gallery URL:** `http://192.168.1.123:5001/gallery/i-love-that-youre-considering-sharing-a-recipe-for`
**All Galleries:** `http://192.168.1.123:5001/galleries`

**Ready to test!** 🚀
