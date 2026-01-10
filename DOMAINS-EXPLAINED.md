# 🌐 Domains Explained - How Everything Connects

**Created:** January 2, 2026
**Purpose:** Understand how soulfra.com, soulfra.github.io, and github.com/Soulfra/soulfra all connect

---

## 🤔 Your Question

> "how does it work with soulfra.com, soulfra.github.io, github.com/soulfra, github.com/soulfra/soulfra? or all these other domains and shit or we have domains listing and other things we need to get it rolling"

**Answer:** They're all connected! Let me show you how.

---

## 🗺️ The Complete Domain Map

### URLs You're Confused About:

```
1. soulfra.com                           ← Your custom domain (what people visit)
2. soulfra.github.io/soulfra/            ← GitHub Pages URL (the actual hosting)
3. github.com/Soulfra/soulfra            ← Git repository (the code)
4. github.com/Soulfra                     ← Your GitHub organization
```

**They're all the SAME website, just different ways to access it!**

---

## 📖 How They Connect - The Full Story

### Step 1: The Git Repository

```
github.com/Soulfra/soulfra
```

This is where your **code** lives (the HTML files).

**What's inside:**
```
soulfra/
├── index.html
├── style.css
├── feed.xml
├── posts/
│   ├── my-first-post.html
│   └── another-post.html
├── CNAME              ← Important! (tells GitHub your custom domain)
└── README.md
```

**How you update it:**
```bash
cd output/soulfra
git add .
git commit -m "New post"
git push
```

---

### Step 2: GitHub Pages Auto-Deploys

GitHub sees your push and automatically deploys to:

```
soulfra.github.io/soulfra/
```

This is the **default** GitHub Pages URL for your repo.

**Anyone can visit this URL!**

---

### Step 3: Custom Domain Points to GitHub Pages

You have a file called `CNAME` in your repo:

```bash
# output/soulfra/CNAME
soulfra.com
```

This tells GitHub: "When someone visits soulfra.com, serve them this repo!"

**Plus DNS configuration:**
```
At your domain registrar (Namecheap, GoDaddy, etc.):

Type: CNAME
Name: www
Value: soulfra.github.io

Type: A
Name: @
Value: 185.199.108.153  (GitHub Pages IP)
```

Now when someone types `soulfra.com`, they see your GitHub Pages site!

---

## 🔗 How All URLs Connect

```
┌──────────────────────────────────────────────────────────┐
│                    THE FULL FLOW                         │
└──────────────────────────────────────────────────────────┘

1. CODE REPOSITORY (Source of truth)
   github.com/Soulfra/soulfra
   └─> HTML files stored here

2. AUTOMATIC DEPLOYMENT
   GitHub Action runs on every push
   └─> Deploys to GitHub Pages

3. DEFAULT GITHUB PAGES URL (Works automatically)
   soulfra.github.io/soulfra/
   └─> Anyone can visit this!

4. CUSTOM DOMAIN (What you want people to use)
   soulfra.com
   └─> DNS points to GitHub Pages
   └─> CNAME file tells GitHub this is your domain
   └─> Serves the SAME content as #3

ALL FOUR URLS SHOW THE SAME WEBSITE!
```

---

## 🎯 Real Example - One Blog Post

When you publish a blog post, here's where it lives:

### In Git Repo:
```
github.com/Soulfra/soulfra/blob/main/posts/my-post.html
                            ↑         ↑
                           branch   file path
```

### On GitHub Pages (default URL):
```
soulfra.github.io/soulfra/posts/my-post.html
```

### On Your Custom Domain:
```
soulfra.com/posts/my-post.html
```

**They're ALL the same file!**

---

## 📚 Your Other Domains

You have 4 domains in `domains.txt`:

```
howtocookathome.com
soulfra.com
deathtodata.com
calriven.com
```

Each one can have its own GitHub repo:

| Domain | GitHub Repo | GitHub Pages URL | Custom Domain Status |
|--------|------------|------------------|---------------------|
| **soulfra.com** | github.com/Soulfra/soulfra | soulfra.github.io/soulfra/ | ✅ LIVE |
| calriven.com | github.com/Soulfra/calriven | soulfra.github.io/calriven/ | ⏳ DNS pending |
| deathtodata.com | github.com/Soulfra/deathtodata | soulfra.github.io/deathtodata/ | ⏳ DNS pending |
| howtocookathome.com | Not created yet | N/A | ❌ Not set up |

---

## 🔍 Understanding GitHub Organization

### Your GitHub Organization:

```
github.com/Soulfra          ← Organization (collection of repos)
   ├─ soulfra               ← Repo for soulfra.com
   ├─ calriven              ← Repo for calriven.com
   ├─ deathtodata           ← Repo for deathtodata.com
   ├─ dealordelete-site     ← Repo for dealordelete.com
   ├─ mascotrooms-site      ← Repo for mascotrooms.com
   └─ ... (6 more repos)
```

**Each repo = one website**

---

## 🌐 GitHub Pages URL Structure

### Pattern:
```
{username}.github.io/{repo-name}/
```

### Your Examples:
```
soulfra.github.io/soulfra/          ← soulfra repo
soulfra.github.io/calriven/          ← calriven repo
soulfra.github.io/deathtodata/       ← deathtodata repo
```

**Note:** `{username}` is your organization name (Soulfra).

---

## 📋 DNS Configuration for Custom Domains

### For soulfra.com (Already Working):

**At your domain registrar (Namecheap, GoDaddy, etc.):**

```
Type: A Record
Name: @
Value: 185.199.108.153

Type: A Record
Name: @
Value: 185.199.109.153

Type: A Record
Name: @
Value: 185.199.110.153

Type: A Record
Name: @
Value: 185.199.111.153

Type: CNAME
Name: www
Value: soulfra.github.io
```

**In your repo:**
```
File: output/soulfra/CNAME
Content: soulfra.com
```

---

### For calriven.com (Pending):

**Same DNS setup, but:**
```
File: output/calriven/CNAME
Content: calriven.com
```

**Then wait 24-48 hours for DNS to propagate.**

---

## 🧪 Testing Domain Configuration

### Test 1: GitHub Pages URL
```bash
curl -I https://soulfra.github.io/soulfra/
# Should return: HTTP/2 200
```

### Test 2: Custom Domain
```bash
curl -I http://soulfra.com
# Should return: HTTP/1.1 200 OK
```

### Test 3: DNS Lookup
```bash
dig soulfra.com
# Should show GitHub Pages IPs (185.199.108.153, etc.)
```

### Test 4: CNAME File
```bash
curl http://soulfra.github.io/soulfra/CNAME
# Should return: soulfra.com
```

---

## 🚀 Adding a New Domain

Want to add `howtocookathome.com`? Here's how:

### Step 1: Create GitHub Repo
```bash
# On github.com
Create new repo: github.com/Soulfra/howtocookathome
```

### Step 2: Generate Content
```bash
# Add to domains.txt
echo "howtocookathome.com | cooking | Simple recipes" >> domains.txt

# Generate site
python3 export_static.py --brand howtocookathome
```

### Step 3: Push to GitHub
```bash
cd output/howtocookathome
git init
git remote add origin https://github.com/Soulfra/howtocookathome.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Step 4: Enable GitHub Pages
```
1. Go to repo settings: github.com/Soulfra/howtocookathome/settings/pages
2. Source: Deploy from branch "main"
3. Folder: / (root)
4. Save
```

### Step 5: Add CNAME File
```bash
echo "howtocookathome.com" > output/howtocookathome/CNAME
git add CNAME
git commit -m "Add custom domain"
git push
```

### Step 6: Configure DNS
```
At your domain registrar:

Type: A
Name: @
Value: 185.199.108.153
       185.199.109.153
       185.199.110.153
       185.199.111.153

Type: CNAME
Name: www
Value: soulfra.github.io
```

### Step 7: Wait & Test
```bash
# Wait 1-24 hours for DNS
# Then test:
curl -I http://howtocookathome.com
```

**Done! Your new domain is live!**

---

## 📊 Domain Status Checker

Run this to check all your domains:

```bash
#!/bin/bash
# domain-checker.sh

domains=(
    "soulfra.com"
    "calriven.com"
    "deathtodata.com"
    "howtocookathome.com"
)

for domain in "${domains[@]}"; do
    echo "Testing: $domain"

    # Test HTTP
    if curl -s -I "http://$domain" | grep -q "200\|301\|302"; then
        echo "  ✅ $domain is LIVE"
    else
        echo "  ❌ $domain is DOWN"
    fi

    # Check DNS
    ip=$(dig +short $domain | head -1)
    if [ -z "$ip" ]; then
        echo "  ⚠️  No DNS record found"
    else
        echo "  🌐 DNS resolves to: $ip"
    fi

    echo ""
done
```

---

## 🔐 HTTPS / SSL Certificates

GitHub Pages provides FREE SSL certificates!

### Enable HTTPS:

```
1. Go to repo settings
2. GitHub Pages section
3. Check "Enforce HTTPS"
4. Wait a few minutes
5. Your site is now https://soulfra.com
```

**Important:** DNS must be configured first!

---

## 🎯 Common Issues & Solutions

### Issue 1: "Site not found" on custom domain

**Problem:** DNS not configured or not propagated yet

**Solution:**
```bash
# Check DNS
dig soulfra.com

# Should show GitHub Pages IPs
# If not, update DNS and wait 24-48 hours
```

---

### Issue 2: GitHub Pages URL works, custom domain doesn't

**Problem:** CNAME file missing or DNS misconfigured

**Solution:**
```bash
# Check CNAME file exists
curl https://soulfra.github.io/soulfra/CNAME

# Check DNS points to GitHub Pages
dig soulfra.com
```

---

### Issue 3: "ERR_TOO_MANY_REDIRECTS"

**Problem:** DNS configured as CNAME to CNAME (not allowed)

**Solution:**
```
Use A records for apex domain (@):
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153

Use CNAME only for www subdomain:
www → soulfra.github.io
```

---

### Issue 4: Changes not showing up

**Problem:** Browser cache or GitHub Pages delay

**Solution:**
```bash
# Force refresh (Cmd+Shift+R on Mac)
# Or check in incognito mode

# Wait 1-2 minutes after git push
# GitHub Pages needs time to rebuild
```

---

## 📱 URL Redirects

Make `www.soulfra.com` redirect to `soulfra.com`:

**DNS configuration:**
```
Type: CNAME
Name: www
Value: soulfra.github.io
```

GitHub Pages automatically redirects www → non-www (or vice versa).

---

## 🗂️ Managing Multiple Domains

### Current Setup:

```
Local (Laptop):
├── output/soulfra/           → soulfra.com
├── output/calriven/          → calriven.com
├── output/deathtodata/       → deathtodata.com
└── output/howtocookathome/   → howtocookathome.com (not created yet)

GitHub:
├── github.com/Soulfra/soulfra         → soulfra.github.io/soulfra/
├── github.com/Soulfra/calriven        → soulfra.github.io/calriven/
└── github.com/Soulfra/deathtodata     → soulfra.github.io/deathtodata/

Live Websites:
├── http://soulfra.com         ✅ LIVE
├── http://calriven.com        ⏳ Pending DNS
└── http://deathtodata.com     ⏳ Pending DNS
```

### Publish All Domains:
```bash
./publish_all.sh
# Pushes all domains to GitHub
```

---

## 💡 Domain Naming Best Practices

### Good Domain Names:
- ✅ Short (soulfra.com)
- ✅ Memorable (calriven.com)
- ✅ Descriptive (howtocookathome.com)

### Avoid:
- ❌ Numbers/hyphens (my-site-123.com)
- ❌ Misspellings
- ❌ Too long

---

## 🎓 Understanding the Connection

```
┌────────────────────────────────────────────────────────────┐
│                    SIMPLE MENTAL MODEL                      │
└────────────────────────────────────────────────────────────┘

soulfra.com (What people type)
    ↓
DNS lookup
    ↓
Points to GitHub Pages IPs (185.199.108.153)
    ↓
GitHub sees CNAME file says "soulfra.com"
    ↓
Serves content from github.com/Soulfra/soulfra repo
    ↓
User sees your website!

ALTERNATIVE PATH:
User types: soulfra.github.io/soulfra/
    ↓
GitHub immediately knows what repo to serve
    ↓
User sees same website!
```

**It's all the same content, just different URLs!**

---

## ✅ Quick Reference

### Your 4 Main URLs:

| What | URL | Purpose |
|------|-----|---------|
| **Custom Domain** | http://soulfra.com | What you tell people |
| **GitHub Pages** | https://soulfra.github.io/soulfra/ | Auto-generated URL |
| **Git Repo** | https://github.com/Soulfra/soulfra | Where code lives |
| **Organization** | https://github.com/Soulfra | All your repos |

### Key Files:

| File | Location | Purpose |
|------|----------|---------|
| CNAME | output/soulfra/CNAME | Tells GitHub your custom domain |
| index.html | output/soulfra/index.html | Homepage |
| feed.xml | output/soulfra/feed.xml | RSS feed |

---

## 🚀 Next Steps

1. **Test your current domains:** Use `domain-checker.sh` above
2. **Add missing domains:** Follow "Adding a New Domain" section
3. **Configure DNS:** Update A/CNAME records for pending domains
4. **Enable HTTPS:** Check "Enforce HTTPS" in GitHub Pages settings

---

**Bottom Line:** soulfra.com, soulfra.github.io/soulfra/, and github.com/Soulfra/soulfra are all connected. The git repo holds your code, GitHub Pages hosts it, and your custom domain points to it via DNS. They're the same website, just different ways to access it!

**See also:**
- `SIMPLE-TEST-NOW.md` - Test all your domains
- `DEPLOYMENT-SIMPLIFIED.md` - Deployment options
- `WHAT-YOURE-RUNNING.md` - Understand your services
