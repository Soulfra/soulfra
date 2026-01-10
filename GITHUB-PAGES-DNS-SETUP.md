# GitHub Pages + Custom Domains Setup

Complete guide for connecting your 8 domains to GitHub Pages and the Soulfra network.

---

## Overview

**What We're Building:**
- `soulfra.com` → Main hub at `soulfra.github.io`
- `calriven.com`, `deathtodata.com`, etc. → Brand-specific pages
- `voice-archive` → Centralized content-addressed storage

**Architecture:**
```
All Domains → GitHub Pages (Static Sites)
     ↓
soulfra.github.io (Hub)
     ├── /voice-archive (Predictions)
     ├── Links to brand sites
     └── Community info
```

---

## Domain Mapping

### 1. Main Hub: soulfra.com

**GitHub Repo:** `Soulfra/soulfra.github.io`
**Custom Domain:** `soulfra.com`
**CNAME File:** `/CNAME` (already created)

**DNS Records (at your domain registrar):**
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

**Verify:**
```bash
dig soulfra.com +noall +answer
# Should show GitHub Pages IPs

dig www.soulfra.com +noall +answer
# Should show CNAME to soulfra.github.io
```

---

### 2. Voice Archive: voice-archive subdomain

**Option A: Subdirectory (Recommended)**
- URL: `https://soulfra.com/voice-archive`
- Already works via repo: `Soulfra/voice-archive`
- No DNS changes needed
- Linked from main hub

**Option B: Subdomain (Optional)**
- URL: `https://voice.soulfra.com`
- Requires DNS CNAME:
  ```
  Type: CNAME
  Name: voice
  Value: soulfra.github.io
  ```
- Update `voice-archive/CNAME` to `voice.soulfra.com`

**We're using Option A** (simpler, already working)

---

### 3. Brand Domains

Each brand can have its own repo and custom domain:

#### CalRiven: calriven.com

**GitHub Repo:** `Soulfra/calriven` or `Soulfra/calriven-site`
**CNAME File:** `/CNAME` with `calriven.com`

**DNS Records:**
```
Type: A
Name: @
Value: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153

Type: CNAME
Name: www
Value: soulfra.github.io
```

**Repo Structure:**
```
calriven/
  index.html  ← Brand landing page
  CNAME       ← calriven.com
  .nojekyll   ← Disable Jekyll processing
```

#### DeathToData: deathtodata.com

**Same as CalRiven**, using repo `Soulfra/deathtodata-site`

#### HowToCookAtHome: howtocookathome.com

**Same pattern**, repo `Soulfra/howtocookathome`

#### Remaining Domains

- **stpetepros.com** → `Soulfra/stpetepros`
- **hollowtown.com** → `Soulfra/hollowtown`
- **niceleak.com** → `Soulfra/niceleak`
- **oofbox.com** → `Soulfra/oofbox`

---

## GitHub Pages Settings

For **each** repository:

1. Go to repo Settings → Pages
2. **Source:** Deploy from branch `main` / `root`
3. **Custom domain:** Enter domain (e.g., `calriven.com`)
4. **Enforce HTTPS:** ✓ (enabled)
5. **Build and deployment:** GitHub Actions (if using workflow) or Branch

**Screenshot Example:**
```
┌─────────────────────────────────────┐
│ GitHub Pages                         │
├─────────────────────────────────────┤
│ Your site is live at                 │
│ https://soulfra.github.io            │
│                                      │
│ Custom domain: soulfra.com           │
│ ☑ Enforce HTTPS                      │
│                                      │
│ Source: Deploy from branch           │
│ Branch: main  /root                  │
└─────────────────────────────────────┘
```

---

## DNS Provider Instructions

### Namecheap

1. Dashboard → Domain List → Manage
2. Advanced DNS tab
3. Add records as shown above
4. TTL: Automatic (or 300 seconds)
5. Save all changes

**Propagation:** 5-30 minutes

### Cloudflare

1. Dashboard → DNS → Records
2. Add A records (GitHub Pages IPs)
3. Add CNAME for www
4. **Proxy status:** DNS only (gray cloud)
5. **SSL/TLS:** Full (not Flexible)

**Important:** Don't use "Proxied" mode initially - use "DNS only"

### GoDaddy

1. Domain Settings → Manage DNS
2. Add A records
3. Add CNAME
4. TTL: 1 hour
5. Save

---

## Verification Steps

### 1. Check DNS Propagation

```bash
# Check A records
dig soulfra.com +short
# Should show: 185.199.108.153, 185.199.109.153, etc.

# Check CNAME
dig www.soulfra.com +short
# Should show: soulfra.github.io
```

**Online Tool:** https://dnschecker.org

### 2. Test HTTPS

```bash
# Should return 200 OK
curl -I https://soulfra.com

# Should NOT show SSL errors
curl https://calriven.com
```

### 3. Verify GitHub Pages Status

```bash
# Check if site is live
gh api repos/Soulfra/soulfra.github.io/pages

# Expected:
{
  "status": "built",
  "cname": "soulfra.com",
  "https_enforced": true
}
```

---

## Troubleshooting

### "Domain is improperly configured"

**Cause:** DNS not propagated yet
**Fix:** Wait 1 hour, then check again

### "CNAME already taken"

**Cause:** Another GitHub repo using same domain
**Fix:** Remove CNAME from other repo first

### "Certificate error" (SSL/TLS)

**Cause:** GitHub hasn't issued cert yet
**Fix:**
1. Uncheck "Enforce HTTPS"
2. Wait 5 minutes
3. Re-check "Enforce HTTPS"
4. Wait 10-15 minutes for cert issuance

### DNS Changes Not Showing

```bash
# Clear local DNS cache
# macOS:
sudo dscacheutil -flushcache

# Linux:
sudo systemd-resolve --flush-caches

# Windows:
ipconfig /flushdns
```

---

## Deployment Workflow

### Automated (GitHub Actions)

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

**Trigger:** Every `git push` to `main`

### Manual (Branch Deployment)

```bash
cd soulfra.github.io
git add .
git commit -m "Update hub page"
git push origin main

# GitHub Pages auto-deploys from main branch
```

---

## Complete Setup Checklist

### ✅ soulfra.github.io (Main Hub)

- [x] Repo created
- [x] index.html with brand links
- [x] CNAME file: `soulfra.com`
- [ ] DNS A records configured
- [ ] DNS CNAME configured (www)
- [ ] GitHub Pages enabled
- [ ] Custom domain connected
- [ ] HTTPS enforced

### ✅ voice-archive

- [x] Repo created at `Soulfra/voice-archive`
- [x] index.html with brand filtering
- [x] GitHub Actions workflow
- [x] Linked from hub at `/voice-archive`
- [ ] Test: https://soulfra.github.io/voice-archive

### ⏸️ Brand Repos (To Create)

- [ ] calriven.com - `Soulfra/calriven` + DNS
- [ ] deathtodata.com - `Soulfra/deathtodata` + DNS
- [ ] howtocookathome.com - `Soulfra/howtocookathome` + DNS
- [ ] stpetepros.com - `Soulfra/stpetepros` + DNS
- [ ] hollowtown.com - `Soulfra/hollowtown` + DNS
- [ ] niceleak.com - `Soulfra/niceleak` + DNS
- [ ] oofbox.com - `Soulfra/oofbox` + DNS

---

## Next Steps (Priority Order)

### 1. Deploy Main Hub (NOW)

```bash
cd ~/Desktop/roommate-chat/soulfra-simple/soulfra.github.io
git add .
git commit -m "Add hub landing page with brand network"
git push origin main
```

**Result:** https://soulfra.github.io/ goes live

### 2. Configure DNS for soulfra.com (AFTER PUSH)

- Add A records (GitHub IPs)
- Add CNAME (www → soulfra.github.io)
- Wait 30 minutes
- Enable "Enforce HTTPS" in repo settings

**Result:** https://soulfra.com/ redirects to hub

### 3. Deploy Voice Archive Updates

```bash
cd ~/Desktop/roommate-chat/soulfra-simple/voice-archive
git add index.html
git commit -m "Add brand filtering and hub link"
git push origin main
```

**Result:** https://soulfra.github.io/voice-archive/ has brand filters

### 4. Test Complete Flow

```
Voice Memo → AirDrop → import_voice_memo.py → Database
                                ↓
                    python3 publish_voice_archive.py local_import
                                ↓
                         voice-archive/ updated
                                ↓
                            git push
                                ↓
                    https://soulfra.com/voice-archive/
```

### 5. Create Brand Pages (Later)

- Clone existing brand-site repos
- Update index.html with brand theme
- Add CNAME file
- Configure DNS
- Push to GitHub

---

## Reference: GitHub Pages IPs

**IPv4 (A Records):**
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

**IPv6 (AAAA Records - Optional):**
```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

**CNAME (www subdomain):**
```
<your-org>.github.io
```

For Soulfra: `soulfra.github.io`

---

## Support Links

- **GitHub Pages Docs:** https://docs.github.com/en/pages
- **Custom Domain Setup:** https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site
- **DNS Checker:** https://dnschecker.org
- **SSL/TLS Status:** https://www.ssllabs.com/ssltest/

---

**Last Updated:** 2026-01-03
**Status:** Hub + Voice Archive ready, DNS pending, Brand pages to be created

---

## Quick Commands

```bash
# Test local voice workflow
python3 import_voice_memo.py ~/Downloads/recording.m4a

# Publish to GitHub Pages
python3 publish_voice_archive.py local_import

# Deploy hub
cd soulfra.github.io && git push

# Deploy voice-archive
cd voice-archive && git push

# Check DNS
dig soulfra.com +short

# Check Pages status
gh api repos/Soulfra/soulfra.github.io/pages
```
