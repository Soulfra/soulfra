# Make CringeProof.com ACTUALLY Work

**Problem:** cringeproof.com is live but features don't work (login, voice recording, payments)

**Why:** Backend API (Flask) only runs on your laptop (localhost:5001)

**Solution:** Choose ONE of these 3 options:

---

## Option 1: Ngrok (2 minutes, FREE, laptop must stay on)

### Steps:
```bash
# 1. Install ngrok (one-time)
brew install ngrok

# 2. Run this script
./START_BACKEND.sh

# 3. Copy the HTTPS URL (like https://abc-123.ngrok-free.app)

# 4. Update voice-archive/index.html line 286:
const BACKEND_URL = 'https://abc-123.ngrok-free.app';  # YOUR URL HERE

# 5. Commit and push
cd voice-archive
git add index.html
git commit -m "Connect to Ngrok backend"
git push origin main

# DONE - cringeproof.com now works!
```

**Pros:**
- ✅ 2 minutes to set up
- ✅ Free tier (no credit card)
- ✅ Full features working

**Cons:**
- ❌ Only works when laptop is on
- ❌ URL changes every time you restart ngrok

---

## Option 2: Railway (10 minutes, FREE tier, always on)

### Steps:
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Create new project
railway init

# 4. Deploy
railway up

# 5. Get your URL
railway domain

# 6. Update voice-archive/index.html line 286:
const BACKEND_URL = 'https://your-app.up.railway.app';

# 7. Commit and push
cd voice-archive
git add index.html
git commit -m "Connect to Railway backend"
git push origin main

# DONE - always online!
```

**Pros:**
- ✅ Always online (24/7)
- ✅ Free tier (500 hrs/month)
- ✅ Automatic deploys from GitHub

**Cons:**
- ⚠️ Requires credit card for free tier
- ⚠️ Sleeps after inactivity (free tier)

---

## Option 3: Client-Side Only (0 minutes, works now, limited features)

### What works WITHOUT backend:
- ✅ Page views / analytics
- ✅ Voice recording (saves to browser only)
- ✅ Share buttons (tracking)

### What DOESN'T work:
- ❌ Login / signup
- ❌ Saving voice memos to share
- ❌ Payments
- ❌ Leaderboards

### Setup:
```bash
# 1. Get Google Analytics tracking ID
# Visit: https://analytics.google.com
# Create property → Get ID (G-XXXXXXXXXX)

# 2. Update voice-archive/_includes/analytics.html line 6:
gtag('config', 'G-YOUR-TRACKING-ID');

# 3. Add analytics to all pages
# Add this to <head> in each HTML file:
{% include _includes/analytics.html %}

# 4. Commit and push
cd voice-archive
git add .
git commit -m "Add analytics"
git push origin main

# DONE - analytics working!
```

---

## Which One Should You Use?

**Just testing / showing friends:**
→ Use **Ngrok** (Option 1)

**Want it always online:**
→ Use **Railway** (Option 2)

**Don't care about backend features:**
→ Use **Client-Side Only** (Option 3)

---

## What's Currently Working

With backend connected (Option 1 or 2):
- ✅ Voice recording + saving
- ✅ Login / signup (email or OAuth)
- ✅ 10 free tokens on signup (faucet)
- ✅ Credits system
- ✅ Password recovery
- ✅ Multi-domain auth
- ✅ Payment checkout (needs Stripe keys)

Without backend (Option 3):
- ✅ Analytics tracking
- ✅ Page views
- ✅ Share button clicks
- ⚠️ Voice recording (browser only, can't share)

---

## DNS / GoDaddy Setup (Optional)

If you want `api.cringeproof.com` instead of Ngrok URL:

### Ngrok Custom Domain:
1. Upgrade to Ngrok paid ($8/month)
2. Add CNAME in GoDaddy:
   ```
   api.cringeproof.com → CNAME → YOUR-SUBDOMAIN.ngrok.io
   ```

### Railway Custom Domain:
1. In Railway dashboard → Settings → Domains
2. Add custom domain: `api.cringeproof.com`
3. Add CNAME in GoDaddy:
   ```
   api → CNAME → your-app.up.railway.app
   ```

---

## Testing It Works

### 1. Open cringeproof.com
### 2. Open browser console (F12)
### 3. Check for errors

**If backend connected:** Should see "Backend available" in console

**If backend NOT connected:** Should see "Backend not available, showing offline mode"

### 4. Try features:
- Click "🎙️ Record" → Should be able to record voice
- Click "🔐 Login" → Should show login form
- Click "🛒 Checkout" → Should show payment options

---

**Bottom line:** Run `./START_BACKEND.sh` and update the URL in index.html. That's it.
