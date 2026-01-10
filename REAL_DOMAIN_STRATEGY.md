# Real Domain Strategy - Deploy Professional System on Your Actual Domains

**Last Updated:** 2026-01-09
**Status:** Ready to Deploy
**Your Domains:** 9 (soulfra.com, cringeproof.com, stpetepros.com, etc.)

---

## What Changed

**Before:** Fake subdomains like joesplumbing.cringeproof.com

**Now:** Your REAL domains:
- **stpetepros.com** → Tampa Bay trade professionals
- **cringeproof.com** → Creators/content professionals
- **howtocookathome.com** → Food professionals
- **hollowtown/oofbox/niceleak.com** → Gaming creators
- **soulfra/deathtodata/calriven.com** → Tech/privacy/AI professionals

---

## Domain Mapping

### stpetepros.com (Trade Professionals)
**Purpose:** Tampa Bay area licensed professionals

**Supports:**
- Plumbers
- Electricians
- HVAC technicians
- Contractors
- Handymen
- Landscapers
- Roofers
- Painters

**URL Structure:**
- Homepage: `stpetepros.com`
- Professional: `stpetepros.com/pro/joesplumbing`
- Tutorial: `stpetepros.com/pro/joesplumbing/tutorial/fix-leaky-faucet`
- pSEO: `stpetepros.com/pro/joesplumbing/l/fix-faucet-tampa`

**Geographic Scope:** Tampa Bay only (35-mile radius)

---

### cringeproof.com (Content Creators)
**Purpose:** Platform hub for podcasters, YouTubers, bloggers

**Supports:**
- Podcasters
- YouTubers
- Bloggers
- Content creators
- Influencers

**URL Structure:**
- Homepage: `cringeproof.com`
- Professional: `cringeproof.com/pro/tampatechtalk`
- Tutorial: `cringeproof.com/pro/tampatechtalk/episode/startup-funding`

**Geographic Scope:** National

---

### howtocookathome.com (Food Professionals)
**Purpose:** Chefs, restaurants, cooking instructors

**Supports:**
- Chefs
- Restaurants
- Cooking instructors
- Food bloggers
- Nutritionists
- Meal prep
- Catering

**URL Structure:**
- Homepage: `howtocookathome.com`
- Professional: `howtocookathome.com/pro/chef-mike`
- Tutorial: `howtocookathome.com/pro/chef-mike/recipe/perfect-pasta`

**Geographic Scope:** National

---

### hollowtown/oofbox/niceleak.com (Gaming)
**Purpose:** Gaming content creators, streamers, esports

**Supports:**
- Gaming streamers
- Esports players
- Gaming YouTubers
- Gaming podcasters
- Game reviewers
- Gaming journalists

**URL Structure:**
- Homepage: `hollowtown.com`
- Professional: `hollowtown.com/pro/gamer-tag`
- Content: `hollowtown.com/pro/gamer-tag/stream/pro-tips`

**Geographic Scope:** National

---

### soulfra/deathtodata/calriven.com (Tech/Privacy/AI)
**Purpose:** Tech professionals, consultants, developers

**Supports:**
- Developers
- Tech bloggers
- Security consultants
- Privacy advocates
- AI consultants
- ML engineers

**URL Structure:**
- Homepage: `soulfra.com`
- Professional: `soulfra.com/pro/dev-name`
- Content: `soulfra.com/pro/dev-name/tutorial/api-security`

**Geographic Scope:** National

---

## Setup Instructions

### Step 1: Domain Configuration

Already done! Your domains are configured in:
- `domains_config.py` - Single source of truth
- `domain_mapper.py` - Routing logic

Test it:
```bash
python3 domains_config.py --list
python3 domain_mapper.py --route plumber Tampa
```

---

### Step 2: DNS Configuration

For each domain, set DNS records:

```
# Example for stpetepros.com
A     stpetepros.com           →  YOUR_SERVER_IP
CNAME www.stpetepros.com       →  stpetepros.com
```

**Where to set:** Your domain registrar (Namecheap, GoDaddy, Cloudflare, etc.)

---

### Step 3: Nginx Configuration

Create nginx config for each domain:

```nginx
# /etc/nginx/sites-available/stpetepros.com

server {
    listen 80;
    server_name stpetepros.com www.stpetepros.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name stpetepros.com www.stpetepros.com;

    ssl_certificate /etc/letsencrypt/live/stpetepros.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stpetepros.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/stpetepros.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### Step 4: SSL Certificates

Get free SSL with Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d stpetepros.com -d www.stpetepros.com
```

Repeat for each domain.

---

### Step 5: Flask App Configuration

Update `app.py` to handle multiple domains:

```python
from domain_mapper import get_domain_config, route_professional_to_domain
from domains_config import DOMAINS

@app.before_request
def detect_domain():
    """Detect which domain is being accessed"""
    domain = request.host.split(':')[0]  # Remove port if present

    # Get domain config
    config = get_domain_config(domain)

    if config:
        g.domain = domain
        g.domain_config = config
    else:
        # Unknown domain, redirect to main
        return redirect('https://soulfra.com')

@app.route('/')
def homepage():
    """Homepage varies by domain"""
    domain = g.get('domain', 'soulfra.com')
    config = g.get('domain_config', {})

    if config.get('type') == 'professional_directory':
        # Show professional directory
        return render_template('professional_directory.html', config=config)
    else:
        # Show blog/platform homepage
        return render_template('homepage.html', config=config)
```

---

### Step 6: Test Locally

Edit `/etc/hosts`:
```
127.0.0.1  stpetepros.com
127.0.0.1  cringeproof.com
127.0.0.1  howtocookathome.com
```

Start Flask:
```bash
python3 app.py
```

Visit:
- http://stpetepros.com:5001
- http://cringeproof.com:5001
- http://howtocookathome.com:5001

---

## Professional Routing

Professionals are automatically routed to the correct domain:

```python
from domain_mapper import route_professional_to_domain

# Tampa plumber → stpetepros.com
domain = route_professional_to_domain('plumber', 'Tampa', 'FL')
# Returns: 'stpetepros.com'

# Podcast creator → cringeproof.com
domain = route_professional_to_domain('podcast')
# Returns: 'cringeproof.com'

# Chef → howtocookathome.com
domain = route_professional_to_domain('chef')
# Returns: 'howtocookathome.com'
```

---

## Offline/Online Workflow

Use `offline_sync_manager.py` for laptop work:

```bash
# Enable offline mode
python3 offline_sync_manager.py --work-offline

# Preload assets
python3 offline_sync_manager.py --preload

# Compile sites
python3 offline_sync_manager.py --compile

# Work offline (SQLite local, changes queued)

# When back online
python3 offline_sync_manager.py --sync
```

---

## Automated Onboarding

After manual signup, automate everything:

```bash
# You meet person, create account manually
# Then run:
python3 automated_onboarding_flow.py --onboard 123

# Automated steps:
# 1. Domain assigned (auto)
# 2. Welcome email (auto)
# 3. Tutorial prompt (auto, 24hrs)
# 4. They record tutorial (manual)
# 5. Quality check (auto)
# 6. pSEO generated (auto)
# 7. Site published (auto)
# 8. Complete! (auto)
```

---

## Domain Sync

Keep all domain files in sync:

```bash
# Update domains_config.py (single source of truth)
# Then sync to all formats:
python3 domains_config.py --sync-all

# This updates:
# - domains.json
# - domains.csv
# - domains.txt
# - my-real-domains.csv
# - domains-master.csv
# - domains-simple.txt
```

---

## Launch Checklist

### Pre-Launch
- [ ] All 9 domains configured in domains_config.py
- [ ] DNS records set for all domains
- [ ] Nginx configs created for all domains
- [ ] SSL certificates obtained (Let's Encrypt)
- [ ] Flask app handles multiple domains
- [ ] Test locally with /etc/hosts

### Deploy
- [ ] Push code to production server
- [ ] Restart Flask app
- [ ] Reload nginx
- [ ] Test each domain in browser
- [ ] Test professional routing
- [ ] Test offline sync

### Post-Launch
- [ ] Monitor logs for errors
- [ ] Test automated onboarding
- [ ] Verify email delivery
- [ ] Check pSEO generation
- [ ] Confirm lead capture working

---

## Next Steps

1. **Test the domain mapping**:
   ```bash
   python3 domain_mapper.py --validate
   ```

2. **Sync domain configs**:
   ```bash
   python3 domains_config.py --sync-all
   ```

3. **Set up offline mode**:
   ```bash
   python3 offline_sync_manager.py --work-offline
   python3 offline_sync_manager.py --preload
   ```

4. **Create first professional** (manually):
   - Go to stpetepros.com/signup
   - Enter details
   - Note professional_id

5. **Start automated onboarding**:
   ```bash
   python3 automated_onboarding_flow.py --onboard <professional_id>
   ```

6. **Deploy to production**:
   - Configure DNS
   - Set up nginx
   - Get SSL certificates
   - Deploy Flask app

---

## Questions?

**"Do I need separate servers for each domain?"**
No! One Flask app, one server, multiple domains. Nginx routes by Host header.

**"What if I want to add another domain?"**
Add to `domains_config.py`, run `--sync-all`, configure DNS/nginx.

**"Can I use subdomains instead?"**
Yes, but you specifically said you want to use your actual domains. Stick with that.

**"Does offline mode really work?"**
Yes. SQLite local, changes queued, sync when online. Like Git.

**"How do I automate onboarding?"**
Meet person → create account → run `--onboard <id>` → automated.

---

**Your domains are ready. Let's deploy! 🚀**
