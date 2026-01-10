# 🌐 Domain Routing & Multi-Service Architecture Guide

**Your Question:** "How do we route soulfraapi.com and soulfra.ai into the mix to be useful too?"

**Answer:** You have 3 separate Flask applications for different services. Here's how to route them properly.

---

## 🎯 THE THREE SERVICES

You have discovered 3 separate Flask applications in `/Soulfra/`:

```
1. soulfra.com       → Main content/blog site (GitHub Pages)
2. soulfra.ai        → AI interface (Ollama API frontend)
3. soulfraapi.com    → API backend (external integrations)
```

Each serves a different purpose and can run independently or together.

---

## 📁 YOUR DISCOVERED ARCHITECTURE

### Service 1: soulfra.com (Content Site)

**Type:** Static site (GitHub Pages)
**Source:** `/github-repos/soulfra/`
**Technology:** HTML + CSS + JavaScript
**Hosting:** GitHub Pages (free, auto-deploy)
**Content:** Blog posts, articles, homepage

**Current Status:** ✅ LIVE at http://soulfra.com

**How It Works:**
```
Write in Studio → Magic Publish → Database → HTML files → GitHub → Live
```

**No server needed** - GitHub Pages serves static HTML files

---

### Service 2: soulfra.ai (AI Interface)

**Type:** Dynamic Flask application
**Source:** `/Users/matthewmauer/Desktop/roommate-chat/Soulfra/Soulfra.ai/app.py`
**Technology:** Python Flask + Ollama
**Hosting:** VPS or cloud server (DigitalOcean, AWS, etc.)
**Purpose:** AI chat interface, content generation API

**What It Does:**
- Provides web UI for Ollama chat
- API endpoints for content transformation
- Powers the Magic Publish transformation engine

**Not Currently Live** - Needs deployment

**Example Routes (from your app.py):**
```python
/                    # AI chat interface
/api/chat            # Chat with Ollama
/api/transform       # Transform content for brands
```

---

### Service 3: soulfraapi.com (API Backend)

**Type:** Dynamic Flask application
**Source:** `/Users/matthewmauer/Desktop/roommate-chat/Soulfra/Soulfraapi.com/app.py`
**Technology:** Python Flask + SQLite
**Hosting:** VPS or cloud server
**Purpose:** External API integrations, webhooks, third-party access

**What It Does:**
- Provides REST API for external services
- JWT authentication for API consumers
- Webhooks for automation (Zapier, Make, etc.)

**Not Currently Live** - Needs deployment

**Example Routes:**
```python
/api/posts           # Get posts (JSON)
/api/auth/token      # Generate API token
/api/webhooks        # Receive external events
```

---

## 🚀 DEPLOYMENT OPTIONS

### Option 1: All Services on One VPS (Simple)

**Best for:** Getting started quickly, low traffic

```
┌─────────────────────────────────────────┐
│  Your VPS (DigitalOcean Droplet)        │
│  Public IP: 123.45.67.89                │
├─────────────────────────────────────────┤
│  Nginx (Reverse Proxy)                  │
│  • soulfra.ai → localhost:5002          │
│  • soulfraapi.com → localhost:5003      │
├─────────────────────────────────────────┤
│  Flask App 1 (port 5002)                │
│  • Soulfra.ai AI interface              │
├─────────────────────────────────────────┤
│  Flask App 2 (port 5003)                │
│  • Soulfraapi.com API backend           │
└─────────────────────────────────────────┘
```

**Setup Steps:**

1. **Launch VPS** (DigitalOcean $6/month droplet)
2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   pip3 install flask ollama
   ```

3. **Upload your apps:**
   ```bash
   scp -r Soulfra.ai/ root@123.45.67.89:/var/www/soulfra-ai/
   scp -r Soulfraapi.com/ root@123.45.67.89:/var/www/soulfra-api/
   ```

4. **Run as systemd services** (auto-restart on crash):
   ```bash
   # /etc/systemd/system/soulfra-ai.service
   [Unit]
   Description=Soulfra AI Service

   [Service]
   WorkingDirectory=/var/www/soulfra-ai
   ExecStart=/usr/bin/python3 app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Configure Nginx reverse proxy:**
   ```nginx
   # /etc/nginx/sites-available/soulfra-ai
   server {
       listen 80;
       server_name soulfra.ai;

       location / {
           proxy_pass http://localhost:5002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

   # /etc/nginx/sites-available/soulfraapi
   server {
       listen 80;
       server_name soulfraapi.com;

       location / {
           proxy_pass http://localhost:5003;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Enable sites and restart Nginx:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/soulfra-ai /etc/nginx/sites-enabled/
   sudo ln -s /etc/nginx/sites-available/soulfraapi /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

7. **Configure DNS** (at your registrar):
   ```
   soulfra.ai        A    123.45.67.89
   soulfraapi.com    A    123.45.67.89
   ```

8. **Add SSL certificates** (free via Let's Encrypt):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d soulfra.ai
   sudo certbot --nginx -d soulfraapi.com
   ```

**Cost:** $6/month (DigitalOcean) or $5/month (Linode)

---

### Option 2: Separate Services (Scalable)

**Best for:** High traffic, independent scaling

```
┌──────────────────────────┐
│  GitHub Pages (Free)      │
│  soulfra.com             │
│  Static HTML             │
└──────────────────────────┘

┌──────────────────────────┐
│  VPS 1 ($6/mo)           │
│  soulfra.ai              │
│  AI + Ollama             │
└──────────────────────────┘

┌──────────────────────────┐
│  VPS 2 ($6/mo)           │
│  soulfraapi.com          │
│  API Backend             │
└──────────────────────────┘
```

**Why separate?**
- AI service needs GPU for Ollama (expensive)
- API service needs 99.9% uptime (use cheap VPS)
- Content site is free (GitHub Pages)

---

### Option 3: Docker + Docker Compose (Recommended)

**Best for:** Easy deployment, portability, scaling

```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - soulfra-ai
      - soulfra-api

  soulfra-ai:
    build: ./Soulfra.ai
    environment:
      - OLLAMA_HOST=ollama:11434
    depends_on:
      - ollama

  soulfra-api:
    build: ./Soulfraapi.com
    environment:
      - DATABASE_URL=/data/soulfra.db
    volumes:
      - ./data:/data

  ollama:
    image: ollama/ollama
    volumes:
      - ollama-data:/root/.ollama

volumes:
  ollama-data:
```

**Deploy with one command:**
```bash
docker-compose up -d
```

---

## 🔒 SSL/HTTPS SETUP

### For GitHub Pages (soulfra.com)

**Automatic** - GitHub provides free SSL

1. Enable in repo settings: https://github.com/Soulfra/soulfra/settings/pages
2. Check "Enforce HTTPS"
3. Wait 24-48 hours for cert provisioning

### For Flask Apps (soulfra.ai, soulfraapi.com)

**Option 1: Let's Encrypt (Free)**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d soulfra.ai
sudo certbot --nginx -d soulfraapi.com

# Auto-renewal (runs automatically)
sudo certbot renew --dry-run
```

**Option 2: Cloudflare (Free + CDN)**

1. Add domains to Cloudflare
2. Point DNS to your VPS IP
3. Enable "Full SSL" in Cloudflare settings
4. Cloudflare handles SSL automatically

**Recommended:** Use Cloudflare for DDoS protection + free CDN

---

## 🌍 DNS CONFIGURATION MATRIX

| Domain | Type | Value | TTL | Purpose |
|--------|------|-------|-----|---------|
| **soulfra.com** | A | 185.199.108.153 | 3600 | GitHub Pages |
| **soulfra.com** | A | 185.199.109.153 | 3600 | GitHub Pages |
| **soulfra.com** | A | 185.199.110.153 | 3600 | GitHub Pages |
| **soulfra.com** | A | 185.199.111.153 | 3600 | GitHub Pages |
| **www.soulfra.com** | CNAME | soulfra.github.io | 3600 | GitHub Pages www |
| **soulfra.ai** | A | YOUR_VPS_IP | 3600 | AI Service |
| **soulfraapi.com** | A | YOUR_VPS_IP | 3600 | API Service |

---

## 🎯 ICP SEPARATION & ROUTING

### Content Sites (GitHub Pages)

**Purpose:** Blog posts, marketing, SEO

| Domain | ICP | Content Focus |
|--------|-----|---------------|
| soulfra.com | Tech founders | Thought leadership, startups |
| calriven.com | Sysadmins | Linux, infrastructure |
| deathtodata.com | Privacy advocates | Anti-surveillance, encryption |
| dealordelete.com | Entrepreneurs | Business deals, MVPs |

**Routing:** Each domain = separate GitHub repo
**No cross-contamination:** Content stays in its brand

### AI Service (soulfra.ai)

**Purpose:** Internal tool for content transformation

**Routes:**
```
/                 → AI chat UI
/api/chat         → Ollama chat endpoint
/api/transform    → Content transformation
```

**Access:** Private (internal use only) or public API with auth

### API Service (soulfraapi.com)

**Purpose:** External integrations, webhooks

**Routes:**
```
/api/posts        → Get posts (JSON)
/api/auth/token   → Generate API key
/api/webhooks     → Receive events from Zapier, etc.
```

**Access:** Public API with JWT authentication

---

## 🧪 TESTING YOUR ROUTING

### Test 1: Content Site (GitHub Pages)

```bash
# Should return 200 OK
curl -I http://soulfra.com
curl -I https://soulfra.com  # (after SSL setup)

# Should show HTML content
curl http://soulfra.com | head -20
```

### Test 2: AI Service

```bash
# Local development
python3 /Users/matthewmauer/Desktop/roommate-chat/Soulfra/Soulfra.ai/app.py
curl http://localhost:5002

# Production (after deployment)
curl https://soulfra.ai/api/chat -X POST -d '{"prompt": "Hello"}'
```

### Test 3: API Service

```bash
# Local development
python3 /Users/matthewmauer/Desktop/roommate-chat/Soulfra/Soulfraapi.com/app.py
curl http://localhost:5003/api/posts

# Production (after deployment)
curl https://soulfraapi.com/api/posts
```

---

## 🚨 COMMON ROUTING ISSUES

### Issue 1: "Connection Refused"

**Cause:** Flask app not running or wrong port

**Fix:**
```bash
# Check if app is running
ps aux | grep python3

# Check which port is listening
lsof -i :5002
lsof -i :5003

# Restart app
sudo systemctl restart soulfra-ai
```

### Issue 2: "SSL Certificate Error"

**Cause:** Let's Encrypt cert not provisioned or expired

**Fix:**
```bash
# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

### Issue 3: "502 Bad Gateway"

**Cause:** Nginx can't reach Flask app

**Fix:**
```bash
# Check Nginx config
sudo nginx -t

# Check Flask app logs
journalctl -u soulfra-ai -f

# Verify proxy_pass port matches app
grep proxy_pass /etc/nginx/sites-available/soulfra-ai
```

### Issue 4: DNS Not Resolving

**Cause:** DNS records not propagated

**Fix:**
```bash
# Check DNS propagation
dig soulfra.ai
nslookup soulfra.ai

# Wait 24-48 hours for propagation
# Use Cloudflare for faster propagation (5 min)
```

---

## 🎯 RECOMMENDED SETUP (Fastest Path to Live)

### Week 1: Get soulfra.com Live (Already Done!)

✅ Content site on GitHub Pages
✅ HTTP working
⏳ HTTPS pending (24-48 hours)

### Week 2: Deploy soulfra.ai (AI Service)

1. Launch DigitalOcean droplet ($6/month)
2. Install Ollama + Flask
3. Deploy Soulfra.ai app
4. Configure Nginx reverse proxy
5. Point DNS soulfra.ai → VPS IP
6. Add SSL with Let's Encrypt

**Timeline:** 2-4 hours setup

### Week 3: Deploy soulfraapi.com (API Service)

1. Use same VPS (different port)
2. Deploy Soulfraapi.com app
3. Configure Nginx for soulfraapi.com
4. Point DNS → VPS IP
5. Add SSL

**Timeline:** 1-2 hours setup

### Week 4: Configure Other Content Domains

1. Configure DNS for 8 remaining domains
2. Wait for GitHub Pages SSL
3. Test all domains live

**Timeline:** 30 min setup, 24-48hr propagation

---

## 📊 SERVICE DEPENDENCY MAP

```
┌─────────────────────────────────────────────────────────────┐
│  LOCALHOST:5001 (Development)                                │
│  • Studio UI                                                 │
│  • Content creation                                          │
│  • Database management                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓ (calls for transformation)
┌─────────────────────────────────────────────────────────────┐
│  soulfra.ai (AI Service)                                     │
│  • Ollama content transformation                             │
│  • AI chat interface                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓ (returns transformed content)
┌─────────────────────────────────────────────────────────────┐
│  LOCALHOST:5001 (Development)                                │
│  • Saves to database                                         │
│  • Exports to HTML                                           │
│  • Pushes to GitHub                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓ (git push)
┌─────────────────────────────────────────────────────────────┐
│  GitHub Repos                                                │
│  • soulfra, calriven, deathtodata, etc.                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓ (auto-deploy)
┌─────────────────────────────────────────────────────────────┐
│  GitHub Pages (Content Sites)                                │
│  • soulfra.com, calriven.com, etc.                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  soulfraapi.com (API Service) - Independent                  │
│  • External integrations                                     │
│  • Webhooks                                                  │
│  • Third-party API access                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 ARCHITECTURE DECISIONS EXPLAINED

### Why Separate soulfra.ai from localhost:5001?

**Localhost (Development):**
- You edit code here
- Test features
- Manage content
- Not accessible to public

**soulfra.ai (Production AI):**
- Public-facing AI interface
- Users can chat with Ollama
- API for external services
- Always online, high uptime

### Why Separate soulfraapi.com?

**API Service Needs:**
- External access (Zapier, webhooks)
- High uptime (99.9%+)
- Rate limiting
- API key management
- Different scaling needs than AI service

**Content Site Needs:**
- Fast static serving (GitHub CDN)
- Free hosting
- No server maintenance

### Why Not One Big App?

**Microservices Benefits:**
- Scale independently (AI needs GPU, API needs CPU)
- Deploy independently (update API without touching AI)
- Fail independently (API down ≠ content site down)
- Different domains = different SSL certs

---

## 🚀 QUICK START DEPLOYMENT

### Deploy soulfra.ai in 10 Minutes

```bash
# 1. Launch DigitalOcean droplet (Ubuntu 22.04)
# 2. SSH in
ssh root@YOUR_VPS_IP

# 3. Install dependencies
apt update && apt install -y python3 python3-pip nginx
pip3 install flask ollama

# 4. Upload your app
scp -r Soulfra.ai root@YOUR_VPS_IP:/var/www/

# 5. Run Flask app
cd /var/www/Soulfra.ai
nohup python3 app.py &

# 6. Configure Nginx
cat > /etc/nginx/sites-available/soulfra-ai <<EOF
server {
    listen 80;
    server_name soulfra.ai;
    location / {
        proxy_pass http://localhost:5002;
    }
}
EOF

ln -s /etc/nginx/sites-available/soulfra-ai /etc/nginx/sites-enabled/
systemctl restart nginx

# 7. Point DNS
# Go to your registrar, add: soulfra.ai A YOUR_VPS_IP

# 8. Add SSL (after DNS propagates)
apt install certbot python3-certbot-nginx
certbot --nginx -d soulfra.ai

# Done! Test:
curl https://soulfra.ai
```

---

## 📞 NEXT STEPS

1. **Immediate:** Enable `push_to_github: true` in Studio UI
2. **This Week:** Deploy soulfra.ai to VPS
3. **Next Week:** Deploy soulfraapi.com
4. **Month 1:** Configure DNS for all 8 content domains

**Need Help?**
- DigitalOcean Docs: https://docs.digitalocean.com/
- Let's Encrypt: https://letsencrypt.org/getting-started/
- Nginx Config: https://nginx.org/en/docs/

---

**Your multi-domain empire is 95% built. Just needs DNS + deployment! 🚀**
