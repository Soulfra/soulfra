# 📱 Deploy from Phone (Like Dropbox)

**How it works:** Drop a file in `/deploy/` folder → Auto-deploys to soulfra.com in 30 seconds

---

## Setup (One Time):

### 1. Create deploy folder:
```bash
mkdir deploy
echo "Drop HTML files here to auto-deploy" > deploy/README.txt
```

### 2. Commit and push:
```bash
git add .github/workflows/auto-deploy-phone.yml deploy/
git commit -m "Add phone deployment system"
git push
```

### 3. Enable GitHub Pages:
- Go to: https://github.com/Soulfra/soulfra/settings/pages
- Source: `gh-pages` branch
- Save

---

## Using from iPhone/iPad:

### Method 1: Working Copy App (Best!)

1. **Install Working Copy** (App Store - Free)
2. **Clone repo:** `https://github.com/Soulfra/soulfra.git`
3. **Add files:**
   - Tap `+` → New File
   - Save to `deploy/` folder
   - Commit → Push
4. **Done!** Live in 30 seconds at soulfra.com

### Method 2: GitHub Mobile App

1. **Open GitHub app**
2. **Navigate to:** `Soulfra/soulfra` repo
3. **Add file:**
   - Tap `...` → Create new file
   - Path: `deploy/my-page.html`
   - Commit directly to `main`
4. **Done!** Auto-deploys

### Method 3: Shortcuts App (Advanced)

Create iPhone Shortcut:
1. Get text input (HTML content)
2. Save to iCloud Drive → `/deploy/`
3. Trigger git commit via Working Copy URL scheme

---

## What You Can Deploy:

### ✅ HTML Pages:
```bash
# Drop in deploy/ folder:
deploy/
  └── my-page.html

# Goes live at:
soulfra.com/my-page.html
```

### ✅ QR Payment Pages:
```bash
# Generate locally:
python3 qr-pay.py --code ABC123 --amount 10 --label "Tampa Plumber"

# File created:
output/soulfra/pay/pay-ABC123.html

# Push to deploy
git add output/soulfra/pay/
git commit -m "Add payment page"
git push
```

### ✅ Images, CSS, JS:
```bash
deploy/
  ├── style.css
  ├── logo.png
  └── script.js
```

---

## File Lifecycle:

```
1. Drop file in deploy/
   ↓
2. Push to GitHub (Working Copy app)
   ↓
3. GitHub Actions triggers
   ↓
4. Copies deploy/* to output/soulfra/
   ↓
5. Deploys to GitHub Pages
   ↓
6. Live at soulfra.com (30 seconds)
   ↓
7. Cleans deploy/ folder
```

---

## Examples:

### Example 1: Quick Landing Page
```bash
# On iPhone (Working Copy app):
# Create: deploy/landing.html

<!DOCTYPE html>
<html>
<head>
    <title>My Landing Page</title>
</head>
<body>
    <h1>Hello from iPhone!</h1>
</body>
</html>

# Commit → Push → Live at soulfra.com/landing.html
```

### Example 2: Payment Page
```bash
# On laptop:
python3 qr-pay.py --code TAMPA01 --amount 50 --label "AC Repair"

# On iPhone (Working Copy):
# Pull latest → See new file in output/soulfra/pay/
# Push → Live at soulfra.com/pay/pay-TAMPA01.html
```

### Example 3: Price Gun Workflow
```bash
# Generate 10 QR codes for different services:
python3 qr-pay.py --code PLUMB01 --amount 99 --label "Emergency Plumbing"
python3 qr-pay.py --code ELECT01 --amount 150 --label "Electrical Repair"
python3 qr-pay.py --code HVAC01 --amount 120 --label "AC Service"

# Print QR codes:
ls output/soulfra/pay/qr-*.svg

# Scan with phone → Payment page opens
```

---

## Rotating Password System:

### Daily Password:
```bash
# Get today's password:
python3 qr-pay.py --rotating-password

# Output:
# 🔑 Today's Password: January11
#    Tomorrow: 12
#    Use in URLs: soulfra.com/admin.html?password=January11
```

### How it works:
- Password changes daily (month + day)
- January 11 = "January11"
- January 12 = "January12"
- Share QR code with embedded password
- No server needed!

---

## Troubleshooting:

### "File not showing up on soulfra.com"
- Wait 30-60 seconds for GitHub Pages to rebuild
- Check: https://github.com/Soulfra/soulfra/actions
- Look for green checkmark ✅

### "Can't push from Working Copy"
- Make sure you're logged into GitHub
- Pull latest changes first
- Then commit → push

### "GitHub Actions failing"
- Check: https://github.com/Soulfra/soulfra/actions
- Click failed workflow for error details
- Usually: Invalid HTML or file permissions

---

## Tips:

1. **Keep deploy/ folder clean** - GitHub Actions auto-cleans it
2. **Test locally first** - Open HTML in browser before deploying
3. **Use templates** - Save common HTML structures
4. **QR codes** - Generate in bulk, deploy once
5. **Mobile editing** - Use Working Copy's text editor

---

## Advanced: Dropbox Integration

### Auto-sync Dropbox → GitHub:

1. **Install Dropbox on Mac/PC**
2. **Create folder:** `/Dropbox/soulfra-deploy/`
3. **Watch folder:**
```bash
# Watch script (auto-commit changes)
#!/bin/bash
fswatch -o ~/Dropbox/soulfra-deploy | while read; do
    cp -r ~/Dropbox/soulfra-deploy/* deploy/
    git add deploy/
    git commit -m "Auto-deploy from Dropbox"
    git push
done
```
4. **Now:** Drop file in Dropbox → Auto-deploys!

---

**Built for 2026 - Deploy from anywhere, anytime** 🚀
