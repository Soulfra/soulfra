# OSS Deployment - Quick Start Guide

**Goal**: Deploy Soulfra Platform to GitHub Pages (free static hosting) in 5 minutes.

---

## 🚀 Quick Deploy (3 Commands)

```bash
# 1. Build static site
python3 build.py

# 2. Commit to git
git add docs/ build.py GITHUB_PAGES_SETUP.md OSS_DEPLOYMENT_QUICKSTART.md
git commit -m "Deploy static site to GitHub Pages"

# 3. Push to GitHub
git push origin main
```

**Then**:
1. Go to GitHub repo → **Settings** → **Pages**
2. Select **Source**: `main` branch, `/docs` folder
3. Click **Save**

**Live in 2 minutes** at: `https://YOUR_USERNAME.github.io/YOUR_REPO`

---

## 📁 What Was Built

```
docs/
├── index.html              # Homepage (25 blog posts)
├── about.html              # About page
├── feed.xml                # RSS feed
├── widget-embed.js         # Embeddable widget (iframe)
├── post/                   # 25 blog post pages
├── docs/                   # 18 documentation pages
│   ├── index.html          # Docs homepage
│   ├── READTHEDOCS_ARCHITECTURE.html
│   ├── QUICKSTART.html
│   └── ... (15 more)
└── static/                 # CSS, images
```

**Total**:
- ✅ 25 blog posts
- ✅ 18 documentation pages
- ✅ RSS feed
- ✅ Embeddable widget
- ✅ All markdown docs converted to HTML

---

## 🧪 Test Locally

```bash
# Option 1: Build + serve in one command
python3 build.py --serve
# Opens http://localhost:8000

# Option 2: Manual serve
cd docs && python3 -m http.server 8000
open http://localhost:8000
```

**Test these URLs**:
- http://localhost:8000 - Homepage
- http://localhost:8000/docs/index.html - Docs
- http://localhost:8000/docs/READTHEDOCS_ARCHITECTURE.html - Architecture doc
- http://localhost:8000/about.html - About page
- http://localhost:8000/feed.xml - RSS feed

---

## 🔄 Update Workflow

### Add New Blog Post

```python
# In Flask app or Python shell
from database import get_db
db = get_db()
db.execute('''
    INSERT INTO posts (slug, title, content, published_at)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
''', ('my-new-post', 'My New Post', '<p>Content here</p>'))
db.commit()
```

Then rebuild:
```bash
python3 build.py
git add docs/
git commit -m "Add new blog post"
git push
```

### Add New Documentation

```bash
# Create .md file
echo "# My New Doc\n\nContent..." > MY_NEW_DOC.md

# Rebuild
python3 build.py
git add docs/ MY_NEW_DOC.md
git commit -m "Add documentation"
git push
```

### Edit Existing Doc

```bash
# Edit .md file
nano READTHEDOCS_ARCHITECTURE.md

# Rebuild
python3 build.py
git add docs/ READTHEDOCS_ARCHITECTURE.md
git commit -m "Update architecture docs"
git push
```

---

## 🌐 Custom Domain (GoDaddy)

### 1. Add CNAME file

```bash
echo "deathtodata.com" > docs/CNAME
git add docs/CNAME
git commit -m "Add custom domain"
git push
```

### 2. Configure DNS at GoDaddy

**Login to GoDaddy** → **DNS Settings** → **Add A Records**:

```
Type: A
Name: @
Value: 185.199.108.153
TTL: 600
```

**Add 3 more A records**:
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

### 3. Add Subdomains (Optional)

```
Type: CNAME
Name: app
Value: YOUR_USERNAME.github.io
TTL: 600

Type: CNAME
Name: ref
Value: YOUR_USERNAME.github.io
TTL: 600
```

**Wait 10-15 minutes** for DNS propagation.

---

## 🔌 Embed Widget Anywhere

Add this to any HTML page (WordPress, static site, etc.):

```html
<!-- Load widget script -->
<script src="https://YOUR_USERNAME.github.io/YOUR_REPO/widget-embed.js"></script>

<!-- Widget container -->
<div id="soulfra-widget"
     data-brand="deathtodata"
     data-width="400px"
     data-height="600px">
</div>
```

**Brands**: `deathtodata`, `soulfra`, `calriven`

---

## 📧 Email Integration (SendGrid)

### 1. Create SendGrid Account
https://sendgrid.com (Free: 100 emails/day)

### 2. Create API Key
Settings → API Keys → Create

### 3. Add to GitHub Secrets
Repo → Settings → Secrets → New secret
- Name: `SENDGRID_API_KEY`
- Value: `SG.xxxxxxxx`

### 4. Send Email via GitHub Actions

Create `.github/workflows/send-email.yml`:

```yaml
name: Send Email

on:
  workflow_dispatch:
    inputs:
      to:
        description: 'Recipient email'
        required: true

jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - name: Send via SendGrid
        run: |
          curl -X POST https://api.sendgrid.com/v3/mail/send \
            -H "Authorization: Bearer ${{ secrets.SENDGRID_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "personalizations": [{"to": [{"email": "${{ github.event.inputs.to }}"}]}],
              "from": {"email": "noreply@soulfra.com"},
              "subject": "Test Email",
              "content": [{"type": "text/plain", "value": "Hello!"}]
            }'
```

**Trigger**: GitHub → Actions → Send Email → Run workflow

---

## 🤖 Auto-Build on Push (GitHub Actions)

Create `.github/workflows/build.yml`:

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install markdown2

      - name: Build site
        run: python3 build.py

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/
          git diff --quiet && git diff --staged --quiet || \
            (git commit -m "Auto-build site" && git push)
```

**Result**: Site rebuilds automatically on every push.

---

## 📊 What's Built

| Component | Count | Example |
|-----------|-------|---------|
| Blog posts | 25 | `/post/welcome-to-soulfra.html` |
| Documentation | 18 | `/docs/READTHEDOCS_ARCHITECTURE.html` |
| Static pages | 2 | `/about.html`, `/index.html` |
| Feeds | 1 | `/feed.xml` |
| Widgets | 1 | `/widget-embed.js` |

---

## 🛠️ Build System

### What `build.py` Does

1. **Reads posts from database** → Converts to HTML pages
2. **Reads all .md files** in root → Converts to `/docs/docs/*.html`
3. **Creates documentation index** → Categorized by topic
4. **Generates widget-embed.js** → For iframe embedding
5. **Copies static files** → CSS, images, etc.
6. **Generates RSS feed** → For subscribers

### Build Options

```bash
# Standard build
python3 build.py

# Build + serve locally (recommended for testing)
python3 build.py --serve
```

---

## 📖 Documentation Available

All markdown docs are now live at `/docs/*.html`:

**Architecture**:
- READTHEDOCS_ARCHITECTURE.html
- ARCHITECTURE_EXPLAINED.html
- connection_map.html

**Guides**:
- QUICKSTART.html
- LAUNCHER_GUIDE.html
- THEME_BUILDER_GUIDE.html

**Setup**:
- DEPLOYMENT.html
- EMAIL_SYSTEM_SETUP.html
- NETWORK_GUIDE.html
- PORT_GUIDE.html

**Other**:
- README.html
- PITCH_DECK.html
- ENCRYPTION_TIERS.html
- And 9 more...

---

## 🎯 Next Steps

### Required
- [ ] Create GitHub repo (if not done)
- [ ] Push code to GitHub
- [ ] Enable GitHub Pages in repo settings
- [ ] Update `SITE_CONFIG['url']` in build.py

### Optional
- [ ] Add custom domain (GoDaddy)
- [ ] Set up SendGrid for emails
- [ ] Add GitHub Actions for auto-build
- [ ] Configure email automation
- [ ] Add analytics (Google Analytics/Plausible)

---

## 🔍 Troubleshooting

### Site not updating on GitHub Pages

```bash
# Wait 1-2 minutes for GitHub Pages rebuild
# Then hard refresh: Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)

# Check Actions tab on GitHub to see build status
```

### Build errors

```bash
# Install markdown2 if missing
pip install markdown2

# Fix database
python3 -c "from database import init_db; init_db()"

# Check build output
python3 build.py
```

### Custom domain not working

```bash
# Verify CNAME file exists
cat docs/CNAME

# Check DNS (wait 10-15 min for propagation)
dig deathtodata.com

# Verify A records point to GitHub Pages IPs
```

---

## 📚 Full Documentation

See **GITHUB_PAGES_SETUP.md** for complete deployment guide including:
- Custom domain setup (detailed)
- Email integration (SendGrid/Mailgun)
- GitHub Actions automation
- Scheduled tasks (cron jobs)
- Widget customization
- Advanced troubleshooting

---

## ✅ Summary

You now have:
- ✅ Static site generator (`build.py`)
- ✅ 25 blog posts + 18 docs built to HTML
- ✅ GitHub Pages ready (just enable in settings)
- ✅ Embeddable widgets for WordPress/static sites
- ✅ RSS feed for subscribers
- ✅ Local testing with `--serve` option
- ✅ Custom domain support (GoDaddy)
- ✅ Email integration ready (SendGrid)

**Deploy now**:
```bash
python3 build.py
git add docs/
git commit -m "Deploy to GitHub Pages"
git push
```

**Then enable GitHub Pages** in repo settings → Pages → Source: `main` / `/docs`

**Live in 2 minutes!** 🚀
