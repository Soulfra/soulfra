# Unified Login System - Self-Hosting Guide

**Flow**: soulfra.com (login) → cringeproof.com (onboarding + squad matching)

Complete guide to deploy the unified authentication system with squad formation.

---

## Architecture

```
┌─────────────────┐
│  soulfra.com    │  Login Hub (GitHub Pages)
│  (static HTML)  │
└────────┬────────┘
         │ auth redirect
         ↓
┌─────────────────┐
│ cringeproof.com │  Onboarding + Features (GitHub Pages)
│ /onboarding.html│
└────────┬────────┘
         │ API calls
         ↓
┌─────────────────┐
│ Flask Backend   │  Voice Upload + Squad Matching
│ port 5002       │  (VPS or Local Server)
└─────────────────┘
         │
         ↓
┌─────────────────┐
│  soulfra.db     │  SQLite Database
│  user_wordmaps  │
└─────────────────┘
```

---

## 1. Backend Setup

### Install Dependencies

```bash
cd soulfra-simple/

# Python packages
pip3 install flask flask-cors openai-whisper bcrypt

# Audio processing
brew install ffmpeg  # macOS
# or: apt-get install ffmpeg  # Linux
```

### Initialize Database

```bash
# Create tables
python3 -c "from database import init_db; init_db()"

# Initialize wordmap tables
python3 user_wordmap_engine.py init

# Create test user
python3 -c "
from user_auth import create_user
create_user('test@soulfra.com', 'password123', 'soulfra.com')
print('✅ Test user created')
"
```

### SSL Certificates (Local HTTPS)

```bash
# Install mkcert
brew install mkcert
mkcert -install

# Generate certs
mkcert localhost 192.168.1.87 127.0.0.1 ::1

# Output:
# localhost+4.pem
# localhost+4-key.pem
```

### Run Backend

```bash
python3 cringeproof_api.py

# Expected output:
# ✅ Users table created
# 🚀 CringeProof API - Isolated Microservice
# 📍 Endpoint: https://192.168.1.87:5002
# 🎤 Voice Upload: POST /api/simple-voice/save
# 🔍 Squad Matching: GET /api/squad/match?user_id=X
# 🔒 HTTPS enabled
```

**Available Endpoints:**

- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login (used by soulfra.com)
- `POST /api/simple-voice/save` - Upload voice recording
- `GET /api/squad/match?user_id=X` - Find similar users
- `GET /api/encyclopedia/word-of-year` - Top word stats
- `GET /api/encyclopedia/progression?user_id=X` - User level

---

## 2. Frontend Deployment

### A. Deploy soulfra.com (Login Hub)

```bash
cd output/soulfra/

# Initialize git (if needed)
git init
git remote add origin https://github.com/YOUR_USERNAME/soulfra.github.io.git

# Deploy to GitHub Pages
git add .
git commit -m "Deploy unified login hub"
git push -u origin main
```

**Enable GitHub Pages:**

1. Go to: https://github.com/YOUR_USERNAME/soulfra.github.io/settings/pages
2. Source: Deploy from branch `main` / root folder
3. Save

**Update API URL** (for production):

Edit `output/soulfra/index.html` line 189:

```javascript
const API_URL = 'https://YOUR_SERVER_IP:5002';  // Change this
```

### B. Deploy cringeproof.com (Onboarding)

```bash
cd voice-archive/

# Initialize git (if needed)
git init
git remote add origin https://github.com/YOUR_USERNAME/cringeproof.github.io.git

# Deploy to GitHub Pages
git add .
git commit -m "Deploy onboarding + squad matching"
git push -u origin main
```

**Enable GitHub Pages:**

1. Go to: https://github.com/YOUR_USERNAME/cringeproof.github.io/settings/pages
2. Source: Deploy from branch `main` / root folder
3. Save

**Update API URLs** in these files:

- `onboarding.html` (line 358)
- `encyclopedia.html` (line 372)
- `record-simple.html`
- `wordmap.html`

```javascript
const API_URL = 'https://YOUR_SERVER_IP:5002';  // Change this
```

---

## 3. Self-Hosting Backend (Production)

### Option A: VPS (DigitalOcean, Linode, Vultr)

**Cost**: ~$6/month

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Install dependencies
apt-get update
apt-get install python3 python3-pip ffmpeg git nginx certbot python3-certbot-nginx -y

# Clone project
cd /var/www
git clone https://github.com/YOUR_USERNAME/soulfra-backend.git
cd soulfra-backend

# Install Python packages
pip3 install flask flask-cors openai-whisper bcrypt

# Initialize database
python3 -c "from database import init_db; init_db()"
python3 user_wordmap_engine.py init
```

**Create systemd service:**

```bash
sudo nano /etc/systemd/system/cringeproof.service
```

```ini
[Unit]
Description=CringeProof Flask API
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/soulfra-backend
ExecStart=/usr/bin/python3 cringeproof_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl start cringeproof
sudo systemctl enable cringeproof
sudo systemctl status cringeproof
```

**Configure nginx:**

```bash
sudo nano /etc/nginx/sites-available/api
```

```nginx
server {
    listen 80;
    server_name api.cringeproof.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Enable SSL:**

```bash
sudo certbot --nginx -d api.cringeproof.com
```

### Option B: Local Server (Raspberry Pi, Old Laptop)

**Cost**: $0/month (electricity only)

Same setup as VPS, but:

1. **Port forwarding**: Router settings → Forward port 5002 to local server IP
2. **Dynamic DNS**: Use DuckDNS (free) for stable domain
3. **SSL**: Use Let's Encrypt with DNS challenge

```bash
# Install DuckDNS client
echo "echo url=\"https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=\" | curl -k -o /var/log/duckdns.log -K -" > /usr/local/bin/duckdns.sh
chmod +x /usr/local/bin/duckdns.sh

# Add to cron (every 5 minutes)
*/5 * * * * /usr/local/bin/duckdns.sh
```

---

## 4. Test the Complete Flow

### Local Testing

1. **Start backend:**

```bash
cd soulfra-simple/
python3 cringeproof_api.py
```

2. **Open soulfra.com locally:**

```bash
cd output/soulfra/
python3 -m http.server 8000
```

Visit: http://localhost:8000

3. **Test login:**
   - Email: `test@soulfra.com`
   - Password: `password123`
   - Should redirect to: `cringeproof.com/onboarding.html`

4. **Test voice recording:**
   - Click microphone button on onboarding page
   - Record 5-10 seconds
   - Stop recording
   - Should see: "✅ Recording saved! Transcription: ..."

5. **Test squad matching:**
   - After recording, page auto-advances to "Finding Your Squad"
   - If no other users: "You're the First!"
   - If other users exist: Shows similarity scores + shared words

### Production Testing

1. Visit: https://soulfra.com
2. Login with account
3. Redirects to: https://cringeproof.com/onboarding.html
4. Record voice memo
5. View squad members

---

## 5. Create Test Data

To test squad matching, create multiple users:

```python
from user_auth import create_user

# Create 3 test users
create_user('alice@test.com', 'pass123', 'soulfra.com')
create_user('bob@test.com', 'pass123', 'soulfra.com')
create_user('carol@test.com', 'pass123', 'soulfra.com')
```

Then:

1. Login as Alice → Record voice memo about "technology startup ideas"
2. Login as Bob → Record voice memo about "tech entrepreneurship dreams"
3. Login as Carol → Record voice memo about "cooking recipes"

**Expected result**: Alice and Bob match high similarity, Carol matches low

---

## 6. DNS Configuration

### Custom Domains

**soulfra.com → GitHub Pages**

```
Type: CNAME
Name: @
Value: YOUR_USERNAME.github.io
```

**cringeproof.com → GitHub Pages**

```
Type: CNAME
Name: @
Value: YOUR_USERNAME.github.io
```

**api.cringeproof.com → Backend Server**

```
Type: A
Name: api
Value: YOUR_SERVER_IP
```

### Update HTML Files

Replace all instances of:

```javascript
const API_URL = 'https://192.168.1.87:5002';
```

With:

```javascript
const API_URL = 'https://api.cringeproof.com';
```

---

## 7. Monitoring & Maintenance

### Database Backups

```bash
# Manual backup
cp soulfra.db backups/soulfra-$(date +%Y%m%d).db

# Automated daily backups (cron)
crontab -e
# Add:
0 2 * * * cp /var/www/soulfra-backend/soulfra.db /var/www/backups/soulfra-$(date +\%Y\%m\%d).db
```

### View Logs

```bash
# systemd service logs
sudo journalctl -u cringeproof -f

# nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Update Code

```bash
# Frontend (GitHub Pages) - just push
git add .
git commit -m "Update UI"
git push

# Backend (VPS)
ssh root@YOUR_SERVER_IP
cd /var/www/soulfra-backend
git pull
sudo systemctl restart cringeproof
```

---

## 8. Troubleshooting

### CORS Errors

**Problem**: "Access blocked by CORS policy"

**Fix**: Update `cringeproof_api.py` CORS config:

```python
CORS(app, origins=[
    'https://soulfra.com',
    'https://cringeproof.com',
    'http://localhost:8000',  # For local testing
], supports_credentials=True)
```

### Login Redirect Not Working

**Problem**: After login, stays on soulfra.com

**Fix**: Check browser console for errors. Ensure `localStorage` works (HTTPS required)

### Squad Matching Returns Empty

**Problem**: No squad members found

**Cause**: Only one user, or no wordmap overlap

**Solution**: Create 2-3 test users with voice recordings

### Microphone Permission Denied

**Problem**: Can't record audio

**Fix**: Pages must be served over HTTPS (not `file://`)

```bash
# Serve locally with HTTPS
python3 -m http.server 8000
# Visit: https://localhost:8000 (accept self-signed cert warning)
```

---

## 9. Cost Breakdown

**Fully Self-Hosted (No Cloud)**

- Domain (soulfra.com + cringeproof.com): $24/year
- GitHub Pages: FREE
- Raspberry Pi 4 (4GB): $55 one-time
- Electricity: ~$2/month
- **Total: ~$3/month**

**Hybrid (VPS Backend)**

- Domain: $24/year
- GitHub Pages: FREE
- DigitalOcean Droplet (1GB): $6/month
- **Total: $8/month**

**No Stripe. No Ngrok. No Cloud Dependencies.** ✅

---

## 10. Next Steps

- [ ] Deploy backend to VPS or local server
- [ ] Deploy frontend to GitHub Pages
- [ ] Update API URLs in all HTML files
- [ ] Create 3+ test users with recordings
- [ ] Test complete login → onboarding → squad flow
- [ ] Enable SSL with Let's Encrypt (production)
- [ ] Set up automated database backups
- [ ] Add OSS payment system (Lightning, BTCPay)

---

## Files Modified

**Created:**

- `output/soulfra/index.html` - Universal login hub
- `voice-archive/onboarding.html` - Squad matching onboarding

**Modified:**

- `cringeproof_api.py` - Added `/api/squad/match` endpoint

**Existing (no changes):**

- `user_wordmap_engine.py` - Wordmap comparison engine
- `user_auth.py` - Authentication system
- `encyclopedia_engine.py` - Analytics engine

---

## Philosophy

"Your keys. Your identity. Period." 🔑

One login. Multiple domains. Squad formation based on what you actually say, not what you pretend to be.

**Welcome to the unified Soulfra ecosystem.**
