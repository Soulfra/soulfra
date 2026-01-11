# 🚀 Zero Dependencies Deployment - Just Python + SQLite

## You Asked: "How the fuck did this go from origin servers to DNS to file server to mail server to web server to proxy server?"

**This guide shows you EXACTLY how - with NO dependencies.**

## The Complete Stack (Built into macOS):

```
Your Computer (Origin)
    ↓
  127.0.0.1:5001 (Flask)
    ↓
  /etc/hosts (Local DNS)
    ↓
  soulfra.db (SQLite file server)
    ↓
  sendmail (Mail server)
    ↓
  Caddy (Reverse proxy)
    ↓
  Internet (Production)
```

## What You Already Have (NO installation needed):

```bash
# Check what's already installed:
which python3    # ✅ Web framework
which sqlite3    # ✅ Database
which sendmail   # ✅ Email
which curl       # ✅ HTTP client
which caddy      # ✅ Reverse proxy (you have this!)
```

## The Journey: localhost → Production

### Step 1: Origin Server (Your Computer)

```bash
# Start Flask on localhost
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py

# Now running on: http://127.0.0.1:5001
```

**What's happening:**
- Python starts web server
- Listens on port 5001
- Only accessible from YOUR computer

### Step 2: Local DNS (/etc/hosts)

```bash
# Check your local DNS
cat /etc/hosts | grep soulfra
```

Output:
```
127.0.0.1 soulfra.local
127.0.0.1 calriven.local
127.0.0.1 deathtodata.local
```

**What this does:**
- Overrides public DNS
- `calriven.local` → `127.0.0.1` (your computer)
- Now you can visit: http://calriven.local:5001

### Step 3: File Server (SQLite)

```bash
# Check database
ls -lh soulfra.db

# Query data
sqlite3 soulfra.db "SELECT id, name, domain FROM brands"
```

**What's happening:**
- All data in ONE file: `soulfra.db`
- No MySQL, no PostgreSQL needed
- 600KB file holds everything

### Step 4: Mail Server (sendmail)

```bash
# Check mail server
which sendmail
# Output: /usr/sbin/sendmail

# Check postfix (also built-in)
which postfix
# Output: /usr/sbin/postfix
```

**What's happening:**
- macOS has built-in SMTP
- Port 25 for local mail
- Can send emails without external service

### Step 5: Web Server (Flask → Gunicorn)

**Development:**
```bash
python3 app.py
# Single-threaded, debug mode, port 5001
```

**Production:**
```bash
pip3 install gunicorn
gunicorn app:app -w 4 -b 0.0.0.0:5001
# 4 workers, multi-process, production-ready
```

### Step 6: Reverse Proxy (Caddy)

**You already have Caddy installed!**

```bash
which caddy
# Output: /opt/homebrew/bin/caddy
```

Create `Caddyfile`:
```
soulfra.com {
    reverse_proxy localhost:5001
}

calriven.com {
    reverse_proxy localhost:5001
}
```

Run:
```bash
caddy run
```

**What Caddy does:**
- Automatic HTTPS (Let's Encrypt)
- Routes multiple domains
- Handles SSL certificates
- Port 80/443 → backend :5001

### Step 7: Public DNS (Domain Registrar)

**Check current DNS:**
```bash
dig +short soulfra.com
# Output: 185.199.109.153 (GitHub Pages)
```

**To point to your VPS:**
```
1. Login to domain registrar (Namecheap, GoDaddy, etc.)
2. Go to DNS settings
3. Add A record:
   Type: A
   Name: @
   Value: YOUR_VPS_IP
   TTL: 300
4. Wait 5-60 minutes for propagation
```

## Current State: soulfra.com

**Problem:** Homepage is broken

**Why:** soulfra.com points to GitHub Pages (static HTML) but Flask app is dynamic

**Fix:** Choose one:

### Option 1: Keep GitHub Pages (Static)
```bash
# Build static site
python3 build.py

# Push to GitHub
git add .
git commit -m "Update site"
git push origin main

# GitHub Pages serves: soulfra.com
```

### Option 2: Switch to VPS (Dynamic)
```bash
# 1. Get VPS ($5/mo)
# 2. Install Python + Caddy
# 3. Clone repo
# 4. Start Gunicorn
# 5. Start Caddy
# 6. Update DNS A record → VPS IP
```

## The Full Command List (Zero Dependencies):

```bash
# 1. Start Flask (localhost only)
python3 app.py

# 2. Check database
sqlite3 soulfra.db "SELECT * FROM brands"

# 3. Send test email
python3 email_sender.py test@example.com

# 4. Start production web server
pip3 install gunicorn
gunicorn app:app -w 4

# 5. Start reverse proxy
caddy run

# 6. Check DNS
dig +short soulfra.com

# 7. Test HTTPS
curl -I https://soulfra.com
```

## What You DON'T Need:

❌ Docker
❌ npm/Node.js
❌ MySQL/PostgreSQL
❌ Redis
❌ Kubernetes
❌ Complex CI/CD
❌ Build tools

## What You DO Need:

✅ Python3 (built-in)
✅ SQLite (built-in)
✅ sendmail (built-in)
✅ Caddy (you have it!)
✅ Domain name ($12/year)
✅ VPS ($5/month - optional)

## Files You Created:

| File | Purpose |
|------|---------|
| `web_stack_from_scratch.ipynb` | Full tutorial (7 cells) |
| `add_domain.py` | One-command domain builder |
| `test_domains.py` | Verify everything works |
| `build_network_from_scratch.py` | Populate database |

## Next Steps:

1. **Learn the stack:**
   ```bash
   jupyter notebook web_stack_from_scratch.ipynb
   ```

2. **Fix homepage:**
   - Decide: GitHub Pages (static) OR VPS (dynamic)
   - See `deployment_decision_guide.md`

3. **Test locally:**
   ```bash
   python3 app.py
   open http://localhost:5001
   ```

4. **Deploy:**
   - Static: Push to GitHub
   - Dynamic: Get VPS, run Caddy

## Summary:

**You wanted to understand:**
> "how the fuck else did this go from origin servers (offline/localhost) to like dns to file server to mail server to web server to proxy server?"

**Now you know:**
1. **Origin** - Your computer (127.0.0.1)
2. **DNS** - /etc/hosts (local) → Registrar (public)
3. **File Server** - SQLite (soulfra.db)
4. **Mail Server** - sendmail (port 25)
5. **Web Server** - Flask (dev) / Gunicorn (prod)
6. **Proxy Server** - Caddy (routes domains)

**All with ZERO dependencies - just built-in macOS tools!** 🎉
