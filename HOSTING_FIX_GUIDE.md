# Hosting Fix Guide - Stop Rebuilding, Start Exposing

**Date**: 2026-01-03
**Problem**: soulfra.com/cringeproof.com point to GitHub Pages (static), but you need Flask (dynamic)

---

## 🎯 The Real Issue

You've already built:
- ✅ Payment systems (mvp_payments.py, payment_routes.py)
- ✅ VIBE token economy (VIBE_TOKEN_ECONOMY.py)
- ✅ Ollama debugging (debug_lab.py)
- ✅ Voice transcription (WhisperTranscriber)

**You DON'T need to rebuild them. You need to EXPOSE them.**

---

## Current State

### DNS Configuration:
```
soulfra.com → 185.199.110.153 (GitHub Pages)
cringeproof.com → 185.199.108.153 (GitHub Pages)
```

### What's Running:
- **GitHub Pages**: Static HTML at soulfra.github.io
- **Local Flask**: Python app on http://localhost:5001 (NOT public)

### The Problem:
Your Mac is NOT accessible from the internet. DNS points to GitHub Pages, not your local Flask.

---

## Solution: Expose Flask with ngrok

### Step 1: Start ngrok

```bash
# Terminal 1: Make sure Flask is running
python3 app.py

# Terminal 2: Start ngrok
ngrok http 5001
```

### Step 2: Get Public URL

ngrok will show:
```
Forwarding  https://abc123-xyz.ngrok-free.app -> http://localhost:5001
```

**Copy that URL!** That's your public endpoint.

### Step 3: Test from Phone

Visit on iPhone:
```
https://abc123-xyz.ngrok-free.app/voice
https://abc123-xyz.ngrok-free.app/debug-quests
```

---

## What Works Now

### With ngrok Running:

**Voice Upload**:
```
https://[your-ngrok-url]/voice
- Record voice on iPhone
- Auto-transcribe with Whisper
- Extract ideas with Ollama
```

**Debug Quests**:
```
https://[your-ngrok-url]/debug-quests
- Browse learning quests
- Request fast fixes
- View leaderboard
```

**Payments** (Already Built!):
```python
# mvp_payments.py has:
- Stripe checkout
- Coinbase Commerce
- Lightning Network
- BTCPay Server
```

---

## Permanent Solutions

### Option 1: ngrok Paid ($10/month)
- Static subdomain (dev.soulfra.com)
- No reconnections needed
- Good for testing

### Option 2: Deploy to VPS ($5/month)
- DigitalOcean/Linode droplet
- Deploy Flask permanently
- Update DNS: soulfra.com → VPS IP

### Option 3: Hybrid (Recommended)
- **GitHub Pages** (Free): Documentation, voice-archive
- **VPS** ($5/mo): Flask app, API, dynamic features
- **Subdomains**:
  - soulfra.github.io → Static docs
  - api.soulfra.com → Flask API
  - cringeproof.com → Flask app

---

## Quick VPS Deploy Guide

### If You Want Permanent Hosting:

```bash
# 1. Rent VPS (DigitalOcean, Linode, AWS)
# $5/month for basic droplet

# 2. SSH into VPS
ssh root@your-vps-ip

# 3. Clone repo
git clone https://github.com/Soulfra/soulfra-simple
cd soulfra-simple

# 4. Install dependencies
pip3 install -r requirements.txt

# 5. Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# 6. Update DNS
# soulfra.com A record → your-vps-ip
# cringeproof.com A record → your-vps-ip
```

---

## What You've Already Built

### Payment Systems (STOP REBUILDING THESE):

1. **mvp_payments.py**
   - Stripe: $0.50-$5.00 checkouts
   - Coinbase: Crypto payments
   - Lightning: Instant BTC
   - BTCPay: Self-hosted

2. **payment_routes.py**
   - Revenue distribution
   - Domain ownership payouts
   - 1099 tax data

3. **VIBE_TOKEN_ECONOMY.py**
   - Soulbound tokens
   - Betting pools
   - Gig economy

### Ollama/AI Systems:

1. **debug_lab.py**
   - AI error explanation
   - Log analysis
   - Debug challenges

2. **ollama_client.py**
   - Fast local inference
   - No API costs
   - Context-aware

### Voice/Transcription:

1. **WhisperTranscriber**
   - Audio → text
   - Works locally

2. **voice_memo_dissector.py**
   - Extract ideas
   - Categorize content

---

## Stop Rebuilding. Start Exposing.

### You DON'T Need:
- ❌ Another payment wrapper
- ❌ Another token economy
- ❌ Another Venmo clone
- ❌ Another Ollama integration

### You DO Need:
- ✅ ngrok running (or VPS)
- ✅ Public URL for Flask
- ✅ DNS update (or subdomain)

---

## Current System Map

### What's LIVE Right Now:

**GitHub Pages (Static)**:
- https://soulfra.github.io → API docs
- https://soulfra.github.io/voice-archive → Voice recordings
- https://soulfra.com → Points here (needs to change)

**Local Flask (Hidden)**:
- http://localhost:5001 → Your Python app
- http://192.168.1.87:5001 → LAN access only
- **NOT PUBLIC** (that's the problem!)

### After ngrok:

**Public Flask**:
- https://[ngrok-url] → Your Flask app
- All routes accessible:
  - /voice
  - /debug-quests
  - /api/domains
  - etc.

---

## Next Steps

### Immediate (5 minutes):
1. Open Terminal
2. Run: `ngrok http 5001`
3. Copy ngrok URL
4. Test on iPhone

### Short-term (this week):
1. Register ngrok paid ($10/mo) for static URL
2. OR deploy to VPS ($5/mo)
3. Update DNS to point to VPS

### Long-term (architecture):
- **soulfra.com** → VPS Flask app
- **api.soulfra.com** → Flask API
- **docs.soulfra.com** → GitHub Pages (static)
- **cringeproof.com** → VPS Flask app

---

## The "OSS" Question

> "its suppose to be oss if people just point something to our domain"

**OSS (Open Source Software)** doesn't mean:
- ❌ Everyone gets free hosting from your Mac
- ❌ You serve traffic for free

**OSS means**:
- ✅ Code is public on GitHub
- ✅ People can fork and run their own instance
- ✅ Contributions welcome

**Your Setup**:
- GitHub repo: Public (OSS) ✅
- GitHub Pages: Free static hosting ✅
- Flask app: Needs VPS or ngrok (your cost)

**If someone forks your repo**:
- They can run Flask on THEIR server
- They update DNS to THEIR IP
- They pay for THEIR hosting

---

## Summary

**Problem**: Domains point to GitHub Pages (static), you need Flask (dynamic)

**Solution**: Expose Flask with ngrok or deploy to VPS

**What You Already Have**:
- All payment systems built (don't rebuild!)
- All AI/Ollama integrations done
- All voice transcription working

**What You Need**:
- Public URL for Flask (ngrok or VPS)
- Update DNS or use subdomain

**Don't rebuild Venmo. Just expose Flask.**

---

## Commands to Run NOW

```bash
# Terminal 1: Flask (if not running)
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py

# Terminal 2: ngrok
ngrok http 5001

# Copy the https://xxx.ngrok-free.app URL
# Test on your iPhone
```

**That's it. Problem solved.**
