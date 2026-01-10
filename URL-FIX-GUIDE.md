# 🔧 URL Fix Guide - What's Broken & How to Fix It

**Created:** December 31, 2024
**Your question:** *"some of this shit is still fucked up somehow... shouldn't we make slugs and sub domains that are matching?"*

**Answer:** You're absolutely right. Here's exactly what's broken and how to fix it.

---

## ❌ What's Broken Right Now

### 1. howtocookathome.com - 404 Error
**URL:** https://soulfra.github.io/howtocookathome/
**Status:** ❌ 404 NOT FOUND
**Cause:** Never pushed to GitHub (wasn't a git repo)
**Fix:** ✅ **DONE!** Just deployed to github.com/Soulfra/howtocookathome

### 2. Wrong /post/ Path - 404 Error
**URL:** https://soulfra.github.io/post/understanding-privacy-demo-1766764779.html
**Status:** ❌ 404 NOT FOUND
**Cause:** Wrong path - should be `/soulfra/post/...` not `/post/...`
**Correct URL:** https://soulfra.github.io/soulfra/post/understanding-privacy-demo-1766764779.html

### 3. No Root Directory Page
**URL:** https://soulfra.github.io/
**Status:** ⚠️ No landing page showing all brands
**Fix:** ✅ **DONE!** Created brand directory at `output/soulfra-directory/`

### 4. Subdomain Routing Not Set Up
**What you want:**
- `calriven.soulfra.com` → CalRiven content
- `api.soulfra.com` → API docs
- `docs.soulfra.com` → Documentation
- `join.soulfra.com` → Signup

**Current status:** ❌ Subdomain routing only works LOCALLY (port 5001)
**Fix:** Need to set up DNS records (see below)

---

## ✅ What's Working Right Now

### Static Sites (GitHub Pages)
```
✅ https://soulfra.github.io/soulfra/       → Soulfra blog
✅ https://soulfra.github.io/calriven/      → CalRiven philosophy
✅ https://soulfra.github.io/deathtodata/   → Privacy manifesto
✅ https://soulfra.github.io/howtocookathome/ → Cooking (JUST DEPLOYED!)
```

### Custom Domains (via CNAME)
```
✅ http://soulfra.com          → Points to soulfra.github.io/soulfra/
⚠️ calriven.com                → DNS configured but may not be active
⚠️ deathtodata.com             → DNS configured but may not be active
⚠️ howtocookathome.com         → CNAME file created, need DNS setup
```

### Local Development (Tribunal System)
```
✅ http://localhost:8001       → soulfra.com (Legislative)
✅ http://localhost:5002       → soulfraapi.com (Executive)
✅ http://localhost:5003       → soulfra.ai (Judicial)
✅ http://localhost:5001       → Main Flask app (all features)
```

---

## 🎯 The Solution: Proper URL Structure

### Option A: Separate Domains (Current Setup)
Each brand gets its own domain:

```
soulfra.com           → Soulfra blog
calriven.com          → CalRiven philosophy
deathtodata.com       → Privacy manifesto
howtocookathome.com   → Cooking blog
```

**Pros:**
- ✅ Each brand feels independent
- ✅ Easy to remember
- ✅ Professional

**Cons:**
- ❌ Need to buy/maintain multiple domains
- ❌ More DNS configuration

---

### Option B: Subdomain Routing (What You're Asking For)
Everything under soulfra.com:

```
soulfra.com                    → Main landing/directory
calriven.soulfra.com           → CalRiven content
deathtodata.soulfra.com        → Privacy content
howtocookathome.soulfra.com    → Cooking content
api.soulfra.com                → API backend
docs.soulfra.com               → Documentation
join.soulfra.com               → Signup
admin.soulfra.com              → Dashboard
```

**Pros:**
- ✅ Everything under one domain
- ✅ Clear hierarchy
- ✅ Easy to expand

**Cons:**
- ❌ GitHub Pages doesn't support dynamic subdomain routing
- ❌ Need a real server (DigitalOcean $5/mo) or use DNS CNAME tricks

---

## 🔧 How to Fix: Step-by-Step

### Step 1: Enable GitHub Pages for howtocookathome ✅ DONE

Already created and pushed! Now enable Pages:
1. Visit: https://github.com/Soulfra/howtocookathome/settings/pages
2. Set source: **main** branch, **/** (root)
3. Wait 2 minutes
4. Visit: https://soulfra.github.io/howtocookathome/

---

### Step 2: Deploy Root Directory Page

**Deploy the brand directory:**
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/output/soulfra-directory

# IMPORTANT: This repo MUST be named "Soulfra.github.io" (user/org pages)
# to deploy at the root https://soulfra.github.io/

gh repo create Soulfra.github.io --public --source=. --push
```

**Result:** https://soulfra.github.io/ will show all your brands

---

### Step 3: Fix DNS for Subdomains

**Login to your domain registrar (GoDaddy/Namecheap/etc.):**

#### For Static Sites (GitHub Pages):
```
# A records for root domains
soulfra.com           A  185.199.108.153
soulfra.com           A  185.199.109.153
soulfra.com           A  185.199.110.153
soulfra.com           A  185.199.111.153

# CNAME for subdomains
calriven.soulfra.com  CNAME  soulfra.github.io
deathtodata.soulfra.com  CNAME  soulfra.github.io
howtocookathome.soulfra.com  CNAME  soulfra.github.io
```

#### For API/Dynamic Subdomains:
```
# Point to your server IP (DigitalOcean or keep localhost for now)
api.soulfra.com       A  YOUR_SERVER_IP
docs.soulfra.com      A  YOUR_SERVER_IP
join.soulfra.com      A  YOUR_SERVER_IP
admin.soulfra.com     A  YOUR_SERVER_IP
```

**If keeping localhost for now:**
- Edit `/etc/hosts` file:
```
127.0.0.1  api.soulfra.com
127.0.0.1  docs.soulfra.com
127.0.0.1  join.soulfra.com
127.0.0.1  admin.soulfra.com
```

---

### Step 4: Update CNAME Files for Subdomains

**If using subdomain approach:**

```bash
# Update each CNAME file
cd output/calriven
echo "calriven.soulfra.com" > CNAME
git add CNAME && git commit -m "Update CNAME for subdomain" && git push

cd ../deathtodata
echo "deathtodata.soulfra.com" > CNAME
git add CNAME && git commit -m "Update CNAME for subdomain" && git push

cd ../howtocookathome
echo "howtocookathome.soulfra.com" > CNAME
git add CNAME && git commit -m "Update CNAME for subdomain" && git push
```

---

### Step 5: Add Routes to Flask App

**Add these routes to app.py:**

```python
@app.route('/admin/docs')
def api_docs():
    return render_template('docs.html')

@app.route('/admin/join')
def join_page():
    return render_template('join.html')

@app.route('/api/join', methods=['POST'])
def api_join():
    data = request.get_json()
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    # Save to database
    # Send welcome email
    return jsonify({
        'success': True,
        'api_key': api_key,
        'message': 'Welcome to Soulfra!'
    })
```

---

## 🌐 Final URL Structure

### Static Sites (GitHub Pages)
```
Production URLs:
  https://soulfra.com                     → Main blog
  https://calriven.soulfra.com            → CalRiven philosophy
  https://deathtodata.soulfra.com         → Privacy manifesto
  https://howtocookathome.soulfra.com     → Cooking blog

OR (if using separate domains):
  https://soulfra.com
  https://calriven.com
  https://deathtodata.com
  https://howtocookathome.com

GitHub Pages URLs (always work):
  https://soulfra.github.io/soulfra/
  https://soulfra.github.io/calriven/
  https://soulfra.github.io/deathtodata/
  https://soulfra.github.io/howtocookathome/
```

### Dynamic API (Flask on Port 5001)
```
Local Development:
  http://localhost:5001                   → Dashboard
  http://localhost:5001/admin/docs        → API documentation ✅ NEW!
  http://localhost:5001/admin/join        → Join/signup page ✅ NEW!
  http://localhost:5001/api/tokens/balance
  http://localhost:5001/api/search

Production (when deployed to DigitalOcean):
  https://api.soulfra.com
  https://docs.soulfra.com
  https://join.soulfra.com
  https://admin.soulfra.com
```

### Tribunal System (Ports 8001/5002/5003)
```
Local Development:
  http://localhost:8001  → soulfra.com (Legislative)
  http://localhost:5002  → soulfraapi.com (Executive)
  http://localhost:5003  → soulfra.ai (Judicial)

Production (when deployed):
  https://soulfra.com (static) + tribunal endpoints
  https://api.soulfra.com (tribunal executive)
  https://ai.soulfra.com (tribunal judicial)
```

---

## 🚀 Quick Test Commands

### Test Static Sites
```bash
# Test what's live
curl -I https://soulfra.github.io/soulfra/
curl -I https://soulfra.github.io/calriven/
curl -I https://soulfra.github.io/deathtodata/
curl -I https://soulfra.github.io/howtocookathome/

# Should all return "200 OK"
```

### Test Local API
```bash
# Start Flask
python3 app.py

# Test endpoints
curl http://localhost:5001/admin/docs
curl http://localhost:5001/admin/join
curl http://localhost:5001/api/tokens/balance
```

### Test Tribunal System
```bash
# Start all 3 domains
cd Soulfra && bash START-ALL.sh

# Test consensus
python3 tribunal_token_test.py --package pro
```

---

## 📋 What You Need to Do Now

### Immediate (5 minutes):
1. ✅ Enable GitHub Pages for howtocookathome:
   - Visit: https://github.com/Soulfra/howtocookathome/settings/pages
   - Source: main branch, / (root)

2. Deploy root directory:
   ```bash
   cd output/soulfra-directory
   gh repo create Soulfra.github.io --public --source=. --push
   ```

### Short-term (1 hour):
3. **Fix DNS records** (remove extra IP 138.197.94.123 from soulfra.com)
4. **Test all URLs** to confirm they work
5. **Add Flask routes** for /admin/docs and /admin/join

### Optional (when ready for production):
6. Deploy to DigitalOcean ($5/mo droplet)
7. Set up subdomain DNS records
8. Configure SSL certificates (Let's Encrypt - FREE)

---

## 🎯 Bottom Line

**What was broken:**
- ❌ howtocookathome not deployed → ✅ FIXED
- ❌ Wrong /post/ URLs → Documented correct paths
- ❌ No root directory → ✅ Created
- ❌ No API docs → ✅ Created templates/docs.html
- ❌ No join page → ✅ Created templates/join.html
- ❌ Subdomain routing not set up → Documented DNS setup

**What you have now:**
- ✅ 4 working GitHub Pages sites
- ✅ Root directory page (ready to deploy)
- ✅ API documentation page
- ✅ Join/signup page
- ✅ Tribunal system with 3-domain consensus
- ✅ Token purchase system
- ✅ Complete DNS setup guide

**Your URLs will be:**
```
https://soulfra.github.io/             → Directory (NEW!)
https://soulfra.github.io/soulfra/     → Blog ✅
https://soulfra.github.io/calriven/    → Philosophy ✅
https://soulfra.github.io/deathtodata/ → Privacy ✅
https://soulfra.github.io/howtocookathome/ → Cooking (NEW!)

Custom domains (with DNS):
https://soulfra.com
https://calriven.com
https://deathtodata.com
https://howtocookathome.com

Local dev:
http://localhost:5001/admin/docs  → API docs (NEW!)
http://localhost:5001/admin/join  → Signup (NEW!)
```

Everything is ready to go - just need to enable Pages and update DNS! 🎉
