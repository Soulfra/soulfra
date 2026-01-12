# 🌐 DNS Setup Guide - GitHub Pages Deployment

How to point your 9 domains to GitHub Pages for static deployment.

---

## Quick Start (5 Minutes)

### Step 1: Configure DNS for stpetepros.com

**At your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):**

Add these DNS records:

```
Type: A
Name: @
Value: 185.199.108.153

Type: A
Name: @
Value: 185.199.109.153

Type: A
Name: @
Value: 185.199.110.153

Type: A
Name: @
Value: 185.199.111.153

Type: CNAME
Name: www
Value: soulfra.github.io
```

### Step 2: Configure GitHub Pages

1. Go to: https://github.com/Soulfra/soulfra/settings/pages
2. Under "Custom domain" enter: `stpetepros.com`
3. Click "Save"
4. Wait for DNS check (green checkmark)
5. Check "Enforce HTTPS"

### Step 3: Test

Visit https://stpetepros.com/pay-bodega.html - should load your payment system!

---

## Architecture

### Old Way (Flask Server)
```
Domain → VPS Server IP → Nginx → Flask App → Database
```
- Costs: $5-50/month for VPS
- Maintenance: Server updates, security patches
- Complexity: Nginx config, SSL certs, database

### New Way (GitHub Pages)
```
Domain → GitHub Pages → Static HTML/JS
```
- Costs: $0/month
- Maintenance: Zero
- Complexity: Just git push

**Result:** Same features, $0 cost, zero maintenance!

---

## GitHub Pages IPs (Memorize These)

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

These are GitHub's CDN servers. Point your A records to all 4 for redundancy.

---

## Multi-Domain Strategy

### Challenge
GitHub Pages allows ONE custom domain per repository.

### Solutions

#### Option 1: Separate Repos (Recommended Now)

Create separate GitHub repos for each domain:

```
Soulfra/stpetepros → stpetepros.com (payment system)
Soulfra/deathtodata → deathtodata.com (privacy search)
Soulfra/calriven → calriven.com (AI platform)
Soulfra/howtocookathome → howtocookathome.com (recipes)
Soulfra/cringeproof → cringeproof.com (social)
Soulfra/hollowtown → hollowtown.com (gaming)
Soulfra/oofbox → oofbox.com (gaming)
Soulfra/niceleak → niceleak.com (gaming)
Soulfra/soulfra → soulfra.com (gateway)
```

**Pros:**
- Each domain has own GitHub Pages
- Clean separation
- Independent deployments
- Easy DNS setup

**Cons:**
- More repos to manage (solved with automation)

#### Option 2: Subdomain Strategy

Use subdomains under soulfra.com:

```
pay.soulfra.com (instead of stpetepros.com)
search.soulfra.com (instead of deathtodata.com)
ai.soulfra.com (instead of calriven.com)
```

**Pros:**
- Single repo
- One deployment

**Cons:**
- Not using your real domains
- SEO impact

#### Option 3: Cloudflare Pages (Best Long-Term)

Deploy to Cloudflare Pages instead:
- Supports multiple custom domains
- FREE (500 builds/month)
- Faster (global CDN)
- Better analytics

**Migration:**
1. Sign up: https://pages.cloudflare.com
2. Connect GitHub repo
3. Build command: `echo "No build needed"`
4. Output directory: `dist`
5. Add all 9 custom domains
6. DNS auto-configured

---

## DNS Configuration by Domain

### 1. stpetepros.com (Payment System)

**Purpose:** Bodega payment system with QR codes

**DNS Records:**
```
A @ 185.199.108.153
A @ 185.199.109.153
A @ 185.199.110.153
A @ 185.199.111.153
CNAME www soulfra.github.io
```

**GitHub Pages:**
- Repository: `Soulfra/stpetepros` (or deploy from `Soulfra/soulfra` dist/ folder)
- Custom domain: `stpetepros.com`
- Deploy from: `dist/`
- Live at: https://stpetepros.com/pay-bodega.html

**Files:**
- dist/pay-bodega.html
- dist/stpetepros-qr.html
- dist/bodega-demo.html
- dist/CNAME (contains: `stpetepros.com`)

---

### 2. soulfra.com (Gateway Control Panel)

**Purpose:** Master control panel for all domains

**DNS Records:**
```
A @ 185.199.108.153
A @ 185.199.109.153
A @ 185.199.110.153
A @ 185.199.111.153
CNAME www soulfra.github.io
```

**GitHub Pages:**
- Repository: `Soulfra/soulfra`
- Custom domain: `soulfra.com`
- Deploy from: `root` or `dist/`
- Live at: https://soulfra.com

**Files to create:**
- gateway.html (control panel)
- index.html (landing page)
- CNAME (contains: `soulfra.com`)

---

### 3. deathtodata.com (Privacy Search)

**DNS Records:**
```
A @ 185.199.108.153
A @ 185.199.109.153
A @ 185.199.110.153
A @ 185.199.111.153
CNAME www soulfra.github.io
```

**Deploy from:** `output/deathtodata/` or separate repo

---

### 4-9. Other Domains

Same DNS configuration for:
- calriven.com
- howtocookathome.com
- cringeproof.com
- hollowtown.com
- oofbox.com
- niceleak.com

---

## Step-by-Step: First Domain (stpetepros.com)

### Before You Start

**What you need:**
- Domain registrar login
- GitHub repo access
- 10 minutes

### Step 1: Add DNS Records at Registrar

**GoDaddy:**
1. Log in to GoDaddy
2. My Products → Domains → Manage DNS
3. Delete old A records
4. Add 4 new A records (all point to GitHub IPs)
5. Add CNAME for www → soulfra.github.io
6. Save

**Namecheap:**
1. Log in to Namecheap
2. Domain List → Manage → Advanced DNS
3. Delete old records
4. Add 4 A records
5. Add CNAME for www
6. Save

**Cloudflare:**
1. Log in to Cloudflare dashboard
2. Select domain
3. DNS → Add records
4. Add 4 A records (set proxy to "DNS only" - gray cloud)
5. Add CNAME (set proxy to "DNS only")
6. Save

**Other registrars:** Similar process - find DNS settings, add A and CNAME records

### Step 2: Create CNAME File

In your repo:
```bash
# Create CNAME file
echo "stpetepros.com" > dist/CNAME

# Commit
git add dist/CNAME
git commit -m "Add custom domain for stpetepros.com"
git push
```

### Step 3: Configure GitHub Pages

1. Go to: https://github.com/Soulfra/soulfra/settings/pages
2. Under "Build and deployment":
   - Source: Deploy from a branch
   - Branch: main
   - Folder: `/dist` (or `/root`)
3. Under "Custom domain":
   - Enter: `stpetepros.com`
   - Click "Save"
4. Wait for DNS check (5-10 minutes)
   - You'll see: "DNS check in progress"
   - Then: "DNS check successful" ✓
5. Check "Enforce HTTPS"
   - May take 10-20 minutes to provision SSL
6. Done!

### Step 4: Test

```bash
# Check DNS propagation
dig stpetepros.com

# Should show GitHub IPs:
# 185.199.108.153
# 185.199.109.153
# 185.199.110.153
# 185.199.111.153

# Test HTTPS
curl -I https://stpetepros.com

# Should return: HTTP/2 200

# Test in browser
open https://stpetepros.com/pay-bodega.html
```

---

## Troubleshooting

### "404 - There isn't a GitHub Pages site here"

**Cause:** CNAME file missing or wrong location

**Fix:**
```bash
# Check CNAME exists in dist/
cat dist/CNAME
# Should output: stpetepros.com

# If missing, create it:
echo "stpetepros.com" > dist/CNAME
git add dist/CNAME
git commit -m "Add CNAME"
git push

# Wait 2-3 minutes for deployment
```

### "Your site is ready to be published at..."

**Cause:** GitHub Pages not deployed yet

**Fix:**
1. Go to Actions tab: https://github.com/Soulfra/soulfra/actions
2. Check latest workflow run
3. If failed, check error logs
4. If succeeded, wait 2-3 minutes

### "DNS check in progress" (stuck)

**Cause:** DNS not propagated yet

**Fix:**
1. Wait 10-30 minutes
2. Check DNS: `dig stpetepros.com`
3. If still shows old IP, check registrar DNS settings
4. Try clearing GitHub custom domain and re-adding

### "Not secure" warning in browser

**Cause:** SSL certificate not provisioned yet

**Fix:**
1. Wait 10-20 minutes after DNS check succeeds
2. In GitHub Pages settings, uncheck then recheck "Enforce HTTPS"
3. Wait another 5-10 minutes
4. Clear browser cache and retry

### Domain shows wrong content

**Cause:** Wrong deploy folder

**Fix:**
```bash
# Check deploy folder in GitHub Pages settings
# Should be: /dist

# Verify files exist:
ls -la dist/
# Should show: pay-bodega.html, CNAME, etc.

# If files in wrong folder, move them:
mv *.html dist/
git add dist/
git commit -m "Move files to dist/"
git push
```

### Cloudflare proxy issues

**Cause:** Cloudflare orange cloud enabled

**Fix:**
1. Cloudflare dashboard → DNS
2. Find A records and CNAME
3. Click orange cloud to make it gray ("DNS only")
4. Save
5. GitHub Pages needs direct DNS access

---

## DNS Propagation Check

After configuring DNS, check worldwide propagation:

**Online tools:**
- https://dnschecker.org
- https://www.whatsmydns.net

**Command line:**
```bash
# Check from Google DNS
dig @8.8.8.8 stpetepros.com

# Check from Cloudflare DNS
dig @1.1.1.1 stpetepros.com

# Check A records
dig stpetepros.com A

# Check CNAME for www
dig www.stpetepros.com CNAME
```

**Expected output:**
```
stpetepros.com.  3600  IN  A  185.199.108.153
stpetepros.com.  3600  IN  A  185.199.109.153
stpetepros.com.  3600  IN  A  185.199.110.153
stpetepros.com.  3600  IN  A  185.199.111.153
www.stpetepros.com.  3600  IN  CNAME  soulfra.github.io.
```

---

## Advanced: Multiple Domains from One Repo

Want to deploy all 9 domains from a single repo? Use GitHub Actions:

**`.github/workflows/deploy-multi-domain.yml`:**
```yaml
name: Deploy All Domains

on:
  push:
    branches: [main]

jobs:
  deploy-stpetepros:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to stpetepros.com
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          cname: stpetepros.com

  deploy-soulfra:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to soulfra.com
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./gateway
          cname: soulfra.com
```

**Note:** This deploys to the `gh-pages` branch. Configure GitHub Pages to deploy from `gh-pages` branch instead of `main`.

---

## Cloudflare Pages Alternative

For easier multi-domain setup, use Cloudflare Pages:

### Setup

1. **Sign up:** https://pages.cloudflare.com
2. **Connect GitHub:** Authorize Cloudflare to access repo
3. **Create project:**
   - Project name: `soulfra-payment-system`
   - Production branch: `main`
   - Build command: (leave empty)
   - Build output directory: `dist`
4. **Add custom domains:**
   - Project Settings → Custom domains
   - Add: stpetepros.com, soulfra.com, etc.
   - DNS automatically configured if domains are on Cloudflare
5. **Deploy:** Push to GitHub → Auto-deploys

### Benefits

- ✅ Multiple custom domains (no limit)
- ✅ Automatic SSL (instant)
- ✅ Global CDN (faster than GitHub Pages)
- ✅ Web Analytics (built-in)
- ✅ Free tier: 500 builds/month, unlimited requests

---

## Security: HTTPS & HSTS

### Force HTTPS

GitHub Pages automatically redirects HTTP → HTTPS if "Enforce HTTPS" is checked.

### HSTS (HTTP Strict Transport Security)

Add to your HTML files:

```html
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
```

Or use Cloudflare's "Always Use HTTPS" feature.

---

## Monitoring

### Check Domain Status

Create `scripts/check-domains.sh`:

```bash
#!/bin/bash

DOMAINS=(
  "stpetepros.com"
  "soulfra.com"
  "deathtodata.com"
  "calriven.com"
  "howtocookathome.com"
  "cringeproof.com"
  "hollowtown.com"
  "oofbox.com"
  "niceleak.com"
)

for domain in "${DOMAINS[@]}"; do
  echo "Checking $domain..."
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain")

  if [ "$STATUS" -eq 200 ]; then
    echo "✅ $domain is UP (HTTP $STATUS)"
  else
    echo "❌ $domain is DOWN (HTTP $STATUS)"
  fi
done
```

Run daily:
```bash
chmod +x scripts/check-domains.sh
./scripts/check-domains.sh
```

### Uptime Monitoring

Use free services:
- **UptimeRobot:** https://uptimerobot.com (50 monitors free)
- **StatusCake:** https://www.statuscake.com
- **Pingdom:** https://www.pingdom.com

Add all 9 domains, check every 5 minutes.

---

## Next Steps

After DNS is configured:

1. ✅ Test payment flow on live domain
2. ✅ Add real Stripe keys to GitHub Secrets
3. ✅ Build Soulfra Gateway control panel (Phase 2)
4. ⏭ Deploy other 8 domains
5. ⏭ Setup analytics tracking
6. ⏭ Add custom email (mail@stpetepros.com)

---

## Quick Reference

### GitHub Pages IPs
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

### CNAME Target
```
soulfra.github.io
```

### DNS Checker
```
https://dnschecker.org
```

### GitHub Pages Settings
```
https://github.com/Soulfra/soulfra/settings/pages
```

---

**Your domain is ready to go live on GitHub Pages!** 🚀

**Cost:** $0/month
**Maintenance:** Zero
**Speed:** Fast (GitHub's global CDN)
**SSL:** Automatic
**Uptime:** 99.9%+
