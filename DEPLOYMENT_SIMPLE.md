# Simple Deployment Guide

## The Problem

Your HTML files were hardcoded with `192.168.1.87:5002` which only works on your local network.

## The Solution

Now you have **2 config files** that control the backend URL:

- `voice-archive/config.js` (for cringeproof.com)
- `output/soulfra/config.js` (for soulfra.com)

## Switch Between Environments

**Use the script:**

```bash
./switch-backend.sh
```

Choose:
1. **Local testing** - Works on your network (192.168.1.87:5002)
2. **Production VPS** - Works anywhere (api.cringeproof.com)  
3. **Localhost dev** - Works on this computer only (localhost:5002)

## Deployment Paths

### Path 1: Local Testing (Current Setup)

**Frontend**: GitHub Pages (free)  
**Backend**: Your laptop (192.168.1.87:5002)

**Works**: Only on your local network  
**Cost**: $0/month

**Steps:**
```bash
# 1. Keep backend URL as-is (192.168.1.87:5002)
./switch-backend.sh
# Choose option 1

# 2. Deploy frontend to GitHub Pages
cd voice-archive/
git add .
git commit -m "Deploy with local backend"
git push

cd ../output/soulfra/
git add .
git commit -m "Deploy login hub"
git push
```

**Access:**
- Login: https://soulfra.com (works from anywhere)
- Backend: Doesn't work - needs VPS

**Problem**: GitHub Pages can't reach 192.168.1.87 (private IP)

---

### Path 2: Production (What You Need)

**Frontend**: GitHub Pages (free)  
**Backend**: VPS like DigitalOcean ($6/month)

**Works**: From anywhere in the world  
**Cost**: $6/month

**Steps:**

#### 1. Deploy Backend to VPS

```bash
# SSH into server
ssh root@YOUR_VPS_IP

# Install dependencies
apt-get update
apt-get install python3 python3-pip ffmpeg nginx certbot -y

# Clone backend code
git clone https://github.com/YOUR_USERNAME/soulfra-backend.git
cd soulfra-backend

# Install Python packages
pip3 install flask flask-cors openai-whisper bcrypt

# Initialize database
python3 -c "from database import init_db; init_db()"
python3 user_wordmap_engine.py init

# Run backend
python3 cringeproof_api.py &
```

#### 2. Set up nginx

```bash
sudo nano /etc/nginx/sites-available/api
```

Add:
```nginx
server {
    listen 80;
    server_name api.cringeproof.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### 3. Enable SSL

```bash
sudo certbot --nginx -d api.cringeproof.com
```

#### 4. Update DNS

Add A record:
```
Type: A
Name: api
Value: YOUR_VPS_IP
```

#### 5. Switch backend config

```bash
# On your laptop
./switch-backend.sh
# Choose option 2 (Production VPS)

# Deploy to GitHub Pages
cd voice-archive/
git add .
git commit -m "Switch to production backend"
git push
```

**Access:**
- Login: https://soulfra.com ✅
- Onboarding: https://cringeproof.com/onboarding.html ✅  
- Backend: https://api.cringeproof.com ✅

---

## Quick Reference

### Change Backend URL

**Manual:**
Edit these 2 files:
- `voice-archive/config.js` line 22
- `output/soulfra/config.js` line 12

**Script:**
```bash
./switch-backend.sh
```

### Test Locally

```bash
# Start backend
python3 cringeproof_api.py

# Serve HTML
cd voice-archive/
python3 -m http.server 8000

# Visit: http://localhost:8000
```

### Deploy to GitHub Pages

```bash
cd voice-archive/
git add .
git commit -m "Update config"
git push
```

---

## Files Changed

**Created:**
- `voice-archive/config.js` - API config for cringeproof
- `output/soulfra/config.js` - API config for soulfra
- `switch-backend.sh` - Script to switch backends

**Modified:**
- `output/soulfra/index.html` - Now uses config.js
- `voice-archive/onboarding.html` - Now uses config.js

**Next:** Update remaining 12 HTML files to use config.js (optional)

---

## FAQ

**Q: Why can't GitHub Pages access 192.168.1.87?**  
A: That's a private local IP. GitHub Pages servers can't reach your home network.

**Q: Do I need a VPS?**  
A: Only if you want it to work from anywhere. Local testing is free.

**Q: Can I use Raspberry Pi instead of VPS?**  
A: Yes! Port forward 5002, use DuckDNS for domain, follow same nginx setup.

**Q: What about the database?**  
A: SQLite file (`soulfra.db`) must be on same server as Flask backend.

---

## Summary

**Before:** 14 HTML files with hardcoded `192.168.1.87:5002`  
**After:** 2 config files, 1 script to switch backends

**To deploy properly:** Need VPS ($6/mo) or port-forwarded home server (free)
