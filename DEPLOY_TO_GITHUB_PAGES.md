# Deploy Soulfra.com to GitHub Pages

> **QR Business Cards Online** - Deploy your professional directory with scannable QR codes

---

## Current Status

✅ **25 professionals** with QR business cards
✅ **Static site built** at `output/soulfra/`
✅ **QR codes embedded** in every profile
❌ **Not deployed yet** - GitHub Pages not configured

---

## Quick Deploy (5 minutes)

### Step 1: Create GitHub Repository

Go to https://github.com/new and create:
- **Repository name:** `soulfra` (or your preferred name)
- **Visibility:** Public (required for free GitHub Pages)
- **Initialize:** ❌ Do NOT check any boxes (empty repo)

Click **Create repository**.

### Step 2: Configure Git Remote

```bash
# Add GitHub remote
git remote add origin https://github.com/YOUR-USERNAME/soulfra.git

# Verify
git remote -v
```

Replace `YOUR-USERNAME` with your GitHub username.

### Step 3: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Add StPetePros with QR business cards"

# Push
git branch -M main
git push -u origin main
```

### Step 4: Enable GitHub Pages

1. Go to your repo: `https://github.com/YOUR-USERNAME/soulfra`
2. Click **Settings** tab
3. Click **Pages** in left sidebar
4. Under **Build and deployment**:
   - Source: **GitHub Actions**
   - (The workflow `.github/workflows/deploy-github-pages.yml` will auto-detect)

5. Wait ~2 minutes for deployment

### Step 5: Add Custom Domain (Optional)

If you own `soulfra.com`:

1. In GitHub Pages settings, add custom domain: `soulfra.com`
2. In your DNS provider (Cloudflare, Namecheap, etc.), add:
   ```
   Type: CNAME
   Name: @  (or www)
   Value: YOUR-USERNAME.github.io
   ```
3. Wait 24-48 hours for DNS propagation
4. Enable "Enforce HTTPS" in GitHub Pages settings

---

## What You Get

### Live URLs

- **soulfra.com** → Soulfra login page
- **soulfra.com/stpetepros/** → Professional directory (25 businesses)
- **soulfra.com/stpetepros/professional-21.html** → Individual profile with QR code

### QR Business Card System

Each professional gets:
- **Scannable QR code** embedded in profile
- **QR points to:** `https://soulfra.com/stpetepros/professional-{id}.html`
- **Works like RFID:** Scan → opens profile instantly
- **Downloadable:** Right-click QR → Save image

### Example URLs

```
St. Petersburg Plumbing Experts
→ https://soulfra.com/stpetepros/professional-21.html
→ QR code scans to same URL

Tampa Electrical Experts
→ https://soulfra.com/stpetepros/professional-22.html
→ QR code scans to same URL
```

---

## Verify Deployment

### Test Locally First

```bash
# Serve locally
python3 build_stpetepros_demo.py --serve

# Open browser
open http://localhost:8000/stpetepros/
```

Test QR codes:
1. Open `http://localhost:8000/stpetepros/professional-21.html`
2. You should see a QR code in the sidebar
3. Scan with phone → should open the profile page

### Test Live Deployment

Once GitHub Pages deploys:

```bash
# Check deployment status
gh workflow view "Deploy to GitHub Pages"  # If you have GitHub CLI

# Or visit
https://github.com/YOUR-USERNAME/soulfra/actions
```

Test URLs:
- `https://YOUR-USERNAME.github.io/` → should show Soulfra login
- `https://YOUR-USERNAME.github.io/stpetepros/` → should show directory
- Scan any QR code → should open profile

---

## Auto-Deploy on Every Push

The workflow `.github/workflows/deploy-github-pages.yml` auto-deploys when you push:

```bash
# Add new professionals
python3 generate_demo_professionals.py --count 10

# Generate QR codes
python3 generate_qr_codes.py

# Rebuild site
python3 build_stpetepros_demo.py

# Push to GitHub (auto-deploys)
git add output/soulfra/
git commit -m "Add 10 more professionals with QR codes"
git push
```

GitHub Actions will:
1. Detect changes to `output/soulfra/**`
2. Deploy to GitHub Pages (~2 minutes)
3. Site updates at `soulfra.com`

---

## Troubleshooting

### Error: "remote origin already exists"

```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR-USERNAME/soulfra.git
```

### Error: "Repository not found"

Make sure:
- Repository exists at `https://github.com/YOUR-USERNAME/soulfra`
- You're logged in: `gh auth login` or use HTTPS with username/password
- Repository name matches exactly

### 404 Error on GitHub Pages

- Wait 2-5 minutes after first push
- Check Actions tab for deployment status
- Verify GitHub Pages source is set to "GitHub Actions"
- Check `output/soulfra/CNAME` file exists and contains `soulfra.com`

### QR Codes Not Showing

```bash
# Check database
sqlite3 soulfra.db "SELECT id, business_name, length(qr_business_card) as qr_size FROM professionals WHERE id=21;"

# Should show: 21|St. Petersburg Plumbing Experts|698

# If qr_size is NULL, regenerate
python3 generate_qr_codes.py --regenerate
python3 build_stpetepros_demo.py
```

### DNS Not Resolving

- DNS changes take 24-48 hours
- Test with `https://YOUR-USERNAME.github.io` first
- Verify CNAME record: `dig soulfra.com` should show `YOUR-USERNAME.github.io`
- Enable "Enforce HTTPS" only AFTER DNS propagates

---

## File Structure

```
output/soulfra/                        # Deployed to GitHub Pages
├── index.html                         # Soulfra login page
├── CNAME                              # Custom domain: soulfra.com
├── stpetepros/                        # StPetePros directory
│   ├── index.html                     # Directory homepage (25 pros)
│   ├── professional-21.html           # St. Petersburg Plumbing
│   │   └── <img> QR code embedded    # Scan to open profile
│   ├── professional-22.html           # Tampa Electrical
│   │   └── <img> QR code embedded
│   ├── ... (23 more)
│   ├── auth-demo.js                   # Visual token system
│   └── signup-demo.html               # Professional signup form
└── ... (other soulfra pages)
```

---

## Next Steps

### Add More Professionals

```bash
# Generate 20 more using Ollama (includes QR codes)
python3 generate_demo_professionals.py --count 20

# Rebuild and deploy
python3 build_stpetepros_demo.py
git add output/soulfra/
git commit -m "Add 20 more Tampa Bay professionals"
git push
```

### Download QR Codes for Print

```bash
# Extract QR code from database to file
sqlite3 soulfra.db <<EOF
.output professional-21-qr.png
SELECT qr_business_card FROM professionals WHERE id=21;
.quit
EOF

# Or use the admin dashboard
open https://192.168.1.87:5001/admin/stpetepros
# Click "QR" button next to any professional
```

### Connect Production Backend

Once GitHub Pages is live, you can:
1. Point signup form to production API at `192.168.1.87:5001`
2. Enable real-time approvals via admin dashboard
3. Auto-rebuild static site when professionals are approved

---

## Support

- **Documentation:** `ONBOARDING_QUICK_START.md`
- **QR Code Generator:** `generate_qr_codes.py --help`
- **Static Site Builder:** `build_stpetepros_demo.py --help`
- **GitHub Pages Docs:** https://docs.github.com/pages

---

**Last updated:** 2026-01-10
**Version:** 1.0 - QR Business Cards Edition
