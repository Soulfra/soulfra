# Deploy StPetePros Demo to GitHub Pages

> **TL;DR:** Build → Git → Push → Live at `https://soulfra.github.io/stpetepros-demo/`

---

## Prerequisites

- GitHub account with `Soulfra` organization (or your personal account)
- Git installed locally
- Python 3.x for build script

---

## Option 1: Quick Deploy (Automated)

```bash
# Build and get deployment commands
python3 build_stpetepros_demo.py --deploy
```

This will output the exact commands to run. Follow them.

---

## Option 2: Manual Deploy (Step-by-Step)

### Step 1: Build the Static Site

```bash
python3 build_stpetepros_demo.py
```

**Output:**
```
🏗️  Building StPetePros Static Demo...
📊 Fetching data from database...
✅ Found X professionals in Y categories
📄 Generating index.html...
📄 Generating X professional pages...
✅ Static site built successfully!
📂 Output: /path/to/static-sites/stpetepros
🌐 Open: file:///path/to/static-sites/stpetepros/index.html
```

### Step 2: Test Locally (Optional but Recommended)

```bash
python3 build_stpetepros_demo.py --serve
```

This starts a local server at `http://localhost:8000`. Open in browser to test:
- Click "Demo Login" → Select a persona → See token animations
- Click "Join as Pro" → Fill out form → Save to localStorage
- Search professionals (client-side filtering)
- View professional profiles

Press `Ctrl+C` to stop the server when done.

### Step 3: Create GitHub Repository

Go to https://github.com/Soulfra (or your account) and create a new repository:

- **Repository name:** `stpetepros-demo`
- **Description:** "Static demo of StPetePros professional directory with client-side auth simulation"
- **Visibility:** Public (required for free GitHub Pages)
- **Initialize:** ❌ Do NOT initialize with README, .gitignore, or license (empty repo)

Click **Create Repository**.

### Step 4: Deploy to GitHub

```bash
# Navigate to the output directory
cd static-sites/stpetepros

# Initialize git repo
git init

# Add remote (replace 'Soulfra' with your username if needed)
git remote add origin https://github.com/Soulfra/stpetepros-demo.git

# Add all files
git add .

# Commit
git commit -m "Build StPetePros static demo with visual token system"

# Push to GitHub
git push -u origin main
```

If the push fails with "branch not found", try:
```bash
git branch -M main
git push -u origin main
```

### Step 5: Enable GitHub Pages

1. Go to your repository: `https://github.com/Soulfra/stpetepros-demo`
2. Click **Settings** tab
3. Scroll down to **Pages** (in left sidebar)
4. Under **Source**, select:
   - Branch: `main`
   - Folder: `/ (root)`
5. Click **Save**

GitHub will show: **Your site is ready to be published at `https://soulfra.github.io/stpetepros-demo/`**

Wait 1-2 minutes for deployment to complete.

### Step 6: Verify Deployment

Open `https://soulfra.github.io/stpetepros-demo/` in your browser.

You should see:
- ✅ StPetePros homepage with professional listings
- ✅ "Demo Login" button (test persona selection + token animations)
- ✅ "Join as Pro" button (test signup form + localStorage)
- ✅ Search bar (test client-side filtering)
- ✅ Professional profile pages (click "View Profile" on any card)

---

## What You Get on GitHub Pages

### 🔐 Visual Token System
- **5 Persona Colors:**
  - CalRiven (blue) - Work/Technical
  - CringeProof (purple) - Ideas/Creative
  - Soulfra (cyan) - Spiritual/Balanced
  - DeathToData (dark grey) - Privacy
  - HowToCookAtHome (orange) - Cooking

- **Token Features:**
  - Diffusion animation (spreading across domains)
  - Decay countdown (7-day expiration timer)
  - Aging effect (color fades over time)
  - Caching (persists in localStorage)

### 📄 Static Pages
- `index.html` - Homepage with professional directory
- `professional-{id}.html` - Individual professional profiles
- `signup-demo.html` - Professional signup form (localStorage only)
- `auth-demo.js` - Client-side auth simulation

### ✅ Zero Backend Required
- No Flask server needed
- No database queries (all pre-rendered HTML)
- No API calls (localStorage for demo data)
- Works entirely from static CDN

---

## Updating the Demo

### When You Add New Professionals

```bash
# 1. Rebuild static site (pulls latest from database)
python3 build_stpetepros_demo.py

# 2. Navigate to output directory
cd static-sites/stpetepros

# 3. Commit and push changes
git add .
git commit -m "Update professional listings"
git push
```

GitHub Pages will auto-deploy the update in ~1 minute.

### When You Modify Auth System

If you edit `auth-demo.js` or `signup-demo.html` templates:

```bash
# 1. Edit templates
nano static-sites/stpetepros-templates/auth-demo.js
nano static-sites/stpetepros-templates/signup-demo.html

# 2. Rebuild (copies templates to output)
python3 build_stpetepros_demo.py

# 3. Deploy
cd static-sites/stpetepros
git add .
git commit -m "Update auth simulation"
git push
```

---

## Custom Domain (Optional)

### Using `stpetepros.com` instead of `soulfra.github.io/stpetepros-demo/`

1. **Add CNAME file to repository:**
   ```bash
   cd static-sites/stpetepros
   echo "stpetepros.com" > CNAME
   git add CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. **Configure DNS:**
   - Go to your DNS provider (Cloudflare, Namecheap, etc.)
   - Add CNAME record:
     - **Name:** `@` (or `www`)
     - **Value:** `soulfra.github.io`
     - **TTL:** Automatic

3. **Enable HTTPS:**
   - Go to repository Settings → Pages
   - Check "Enforce HTTPS"

Wait 24-48 hours for DNS propagation. Then `https://stpetepros.com` will show your demo.

---

## Troubleshooting

### Error: "Permission denied (publickey)"

Your SSH key isn't configured. Use HTTPS instead:
```bash
git remote set-url origin https://github.com/Soulfra/stpetepros-demo.git
git push -u origin main
```

### Error: "Repository not found"

Make sure the repository name matches:
```bash
git remote -v  # Should show: https://github.com/Soulfra/stpetepros-demo.git
```

If wrong, update it:
```bash
git remote set-url origin https://github.com/Soulfra/stpetepros-demo.git
```

### Error: "fatal: refusing to merge unrelated histories"

The remote repo has files (README, LICENSE, etc.). Either:

**Option A: Force push (overwrites remote)**
```bash
git push -u origin main --force
```

**Option B: Pull and merge**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Site Not Updating After Push

- Check GitHub Actions tab for build status
- Clear browser cache (Ctrl+Shift+R)
- Wait 2-3 minutes for CDN to update

---

## Production Checklist

Before sharing the demo publicly:

- [ ] Test all persona logins (CalRiven, CringeProof, Soulfra, etc.)
- [ ] Verify token diffusion animation plays
- [ ] Confirm token decay countdown works
- [ ] Test signup form → saves to localStorage
- [ ] Check professional search (client-side filtering)
- [ ] Verify QR codes display (if professionals have them)
- [ ] Test on mobile devices (responsive design)
- [ ] Check console for JavaScript errors (F12 → Console)
- [ ] Verify footer links (About, GitHub repo, etc.)
- [ ] Confirm "Demo Mode" warnings are visible

---

## Sharing the Demo

Send this link to anyone:

```
https://soulfra.github.io/stpetepros-demo/
```

**What they can do:**
- Browse professional directory (static HTML, no backend)
- Test demo login (persona selection, token animations)
- Fill out signup form (saves to their browser's localStorage only)
- See how the visual token system works
- View individual professional profiles
- Search/filter professionals (client-side JavaScript)

**What they CANNOT do:**
- Actually create a real account (no backend)
- Send real messages to professionals (demo mode alert)
- Access admin dashboard (static demo only shows public pages)

---

## Next Steps

Once the demo is live and proven:

1. **Integrate with Real Backend:**
   - Replace localStorage with API calls to `/api/master/signup`
   - Connect to production database
   - Enable real QR code generation

2. **Add Admin Dashboard:**
   - Create admin.html with approval workflow
   - Add stats dashboard (pending, approved, rejected)
   - Export CSV functionality

3. **Google Business Profile Integration:**
   - See `GOOGLE_BUSINESS_PROFILE_INTEGRATION.md`
   - Auto-create Google Business listings
   - Pull real Google reviews

4. **Multi-State Expansion:**
   - `tampa.stpetepros.com`
   - `orlando.stpetepros.com`
   - `miami.stpetepros.com`

5. **Payment Integration:**
   - Stripe checkout for premium listings
   - Featured placement
   - Verified badges

---

## Support

- **Documentation:** `ONBOARDING_QUICK_START.md`
- **Backend Guide:** `SIMPLE_README.md`
- **Google Integration:** `GOOGLE_BUSINESS_PROFILE_INTEGRATION.md`
- **GitHub Repo:** https://github.com/Soulfra/stpetepros-demo

---

**Last updated:** 2026-01-10
**Version:** 1.0 - Static Demo Edition
