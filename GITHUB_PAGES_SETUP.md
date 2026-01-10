# GitHub Pages Deployment Guide - OSS Style

Complete guide for deploying Soulfra Platform to GitHub Pages (free static hosting).

---

## Quick Start

```bash
# 1. Build the static site
python3 build.py

# 2. Test locally
cd docs && python3 -m http.server 8000
# Visit: http://localhost:8000

# 3. Deploy to GitHub
git add docs/
git commit -m "Deploy static site to GitHub Pages"
git push origin main
```

---

## Part 1: GitHub Repository Setup

### 1. Create GitHub Repository

```bash
# If you haven't already initialized git
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Enable GitHub Pages

1. Go to your repo on GitHub.com
2. Click **Settings** tab
3. Scroll to **Pages** section (left sidebar)
4. Under **Source**, select:
   - **Branch**: `main`
   - **Folder**: `/docs`
5. Click **Save**

**Your site will be live at**: `https://YOUR_USERNAME.github.io/YOUR_REPO`

---

## Part 2: Configure Site URL

Update `build.py` with your GitHub Pages URL:

```python
# In build.py, line ~24
SITE_CONFIG = {
    'title': 'Soulfra Platform',
    'description': 'Multi-brand architecture with unified accounts',
    'url': 'https://YOUR_USERNAME.github.io/YOUR_REPO',  # ← Update this
    # ...
}
```

Then rebuild:
```bash
python3 build.py
git add docs/
git commit -m "Update site URL"
git push
```

---

## Part 3: What Gets Built

### Directory Structure

```
docs/
├── index.html                  # Homepage with blog posts
├── about.html                  # About page
├── feed.xml                    # RSS feed
├── widget-embed.js             # Embeddable widget script
├── post/                       # Blog posts
│   ├── welcome-to-soulfra.html
│   ├── calriven-ch1-canvas.html
│   └── ...
├── docs/                       # Documentation
│   ├── index.html              # Docs homepage
│   ├── READTHEDOCS_ARCHITECTURE.html
│   ├── QUICKSTART.html
│   └── ...
└── static/                     # CSS, images, etc.
    └── style.css
```

### What Each File Does

- **`index.html`**: Main landing page with recent blog posts
- **`docs/index.html`**: Documentation hub (categorized by topic)
- **`post/*.html`**: Individual blog post pages
- **`docs/*.html`**: Rendered markdown documentation
- **`widget-embed.js`**: JavaScript for embedding widgets in other sites
- **`feed.xml`**: RSS feed for blog subscribers
- **`about.html`**: About the platform

---

## Part 4: Build Process Explained

### What `build.py` Does

```bash
python3 build.py
```

**Steps**:
1. **Reads posts from database** → Converts to HTML
2. **Reads all .md files** in root → Converts to `/docs/docs/*.html`
3. **Creates doc index** → Categorized by topic (Architecture, Guides, Setup)
4. **Generates widget-embed.js** → For iframe embedding
5. **Copies static files** → CSS, images, etc.
6. **Generates RSS feed** → For subscribers

### Build Options

```bash
# Standard build
python3 build.py

# Build + serve locally
python3 build.py --serve
# Opens server at http://localhost:8000

# Watch mode (TODO - not yet implemented)
python3 build.py --watch
```

---

## Part 5: Updating Content

### Adding New Blog Posts

1. **Add post to database** (via Flask app):
   ```python
   from database import get_db
   db = get_db()
   db.execute('''
       INSERT INTO posts (slug, title, content, published_at)
       VALUES (?, ?, ?, CURRENT_TIMESTAMP)
   ''', ('my-new-post', 'My New Post', '<p>Content here</p>'))
   db.commit()
   ```

2. **Rebuild site**:
   ```bash
   python3 build.py
   git add docs/
   git commit -m "Add new blog post"
   git push
   ```

### Adding New Documentation

1. **Create .md file** in root directory:
   ```bash
   # Example: MY_NEW_DOC.md
   echo "# My New Doc\n\nContent here..." > MY_NEW_DOC.md
   ```

2. **Rebuild**:
   ```bash
   python3 build.py
   git add docs/ MY_NEW_DOC.md
   git commit -m "Add new documentation"
   git push
   ```

### Editing Existing Docs

1. **Edit .md file** in root
2. **Rebuild and deploy**:
   ```bash
   python3 build.py
   git add docs/
   git commit -m "Update documentation"
   git push
   ```

---

## Part 6: GoDaddy Custom Domain (Optional)

### Connect GoDaddy Domain to GitHub Pages

**Goal**: Make your GitHub Pages site available at `deathtodata.com` instead of `username.github.io/repo`

### 1. Add CNAME File

Create `docs/CNAME` (no file extension):

```bash
echo "deathtodata.com" > docs/CNAME
git add docs/CNAME
git commit -m "Add custom domain"
git push
```

### 2. Configure DNS at GoDaddy

**Login to GoDaddy** → **DNS Settings** → **Add Records**:

#### Option A: Root Domain (deathtodata.com)

```
Type: A
Name: @
Value: 185.199.108.153
TTL: 600
```

Add 3 more A records with these IPs:
- `185.199.109.153`
- `185.199.110.153`
- `185.199.111.153`

#### Option B: Subdomain (app.deathtodata.com)

```
Type: CNAME
Name: app
Value: YOUR_USERNAME.github.io
TTL: 600
```

### 3. Configure Subdomains

For multi-subdomain architecture (ReadTheDocs style):

```
Type: CNAME
Name: app
Value: YOUR_USERNAME.github.io
TTL: 600

Type: CNAME
Name: ref
Value: YOUR_USERNAME.github.io
TTL: 600

Type: CNAME
Name: org
Value: YOUR_USERNAME.github.io
TTL: 600
```

**Note**: All subdomains point to the same GitHub Pages site. The Flask app handles subdomain routing.

### 4. Enable HTTPS

GitHub Pages automatically provisions SSL certificates (Let's Encrypt) for custom domains.

1. Go to **GitHub repo** → **Settings** → **Pages**
2. Check **Enforce HTTPS** (wait 10-15 minutes for certificate provisioning)

---

## Part 7: Embedding Widgets

### Use the Widget on Any Site

Add this to any HTML page (WordPress, static site, etc.):

```html
<!-- Load widget script -->
<script src="https://YOUR_USERNAME.github.io/YOUR_REPO/widget-embed.js"></script>

<!-- Widget container -->
<div id="soulfra-widget" data-brand="deathtodata" data-width="400px" data-height="600px"></div>
```

**Options**:
- `data-brand`: `"deathtodata"` | `"soulfra"` | `"calriven"`
- `data-width`: Width in pixels (default: `"400px"`)
- `data-height`: Height in pixels (default: `"600px"`)

### Example: WordPress Site

```html
<!-- Add to WordPress post/page HTML editor -->
<h2>Try Our Interactive Quiz</h2>
<script src="https://YOUR_USERNAME.github.io/YOUR_REPO/widget-embed.js"></script>
<div id="soulfra-widget" data-brand="soulfra" data-width="500px" data-height="700px"></div>
```

---

## Part 8: Automation with GitHub Actions

### Auto-Build on Push (Future Enhancement)

Create `.github/workflows/build.yml`:

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  workflow_dispatch:

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
        run: |
          pip install markdown2

      - name: Build static site
        run: |
          python3 build.py

      - name: Commit and push if changed
        run: |
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"
          git add docs/
          git diff --quiet && git diff --staged --quiet || (git commit -m "Auto-build static site" && git push)
```

**Result**: Site rebuilds automatically whenever you push to `main` branch.

---

## Part 9: Email Integration (SendGrid/Mailgun)

### SendGrid Setup (Free Tier: 100 emails/day)

1. **Create account**: https://sendgrid.com
2. **Create API key**: Settings → API Keys → Create
3. **Add to GitHub Secrets**: Repo → Settings → Secrets → New secret
   - Name: `SENDGRID_API_KEY`
   - Value: `SG.xxxxxxxxxxxxxxx`

### Send Email via GitHub Actions

Create `.github/workflows/send-email.yml`:

```yaml
name: Send Email

on:
  workflow_dispatch:
    inputs:
      to:
        description: 'Recipient email'
        required: true
      subject:
        description: 'Email subject'
        required: true
      body:
        description: 'Email body'
        required: true

jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - name: Send email via SendGrid
        run: |
          curl --request POST \
            --url https://api.sendgrid.com/v3/mail/send \
            --header "Authorization: Bearer ${{ secrets.SENDGRID_API_KEY }}" \
            --header 'Content-Type: application/json' \
            --data '{
              "personalizations": [{
                "to": [{"email": "${{ github.event.inputs.to }}"}]
              }],
              "from": {"email": "noreply@soulfra.com"},
              "subject": "${{ github.event.inputs.subject }}",
              "content": [{
                "type": "text/plain",
                "value": "${{ github.event.inputs.body }}"
              }]
            }'
```

**Trigger manually**: GitHub repo → Actions → Send Email → Run workflow

---

## Part 10: Scheduled Tasks (Cron Jobs)

### Daily Newsletter (Example)

Create `.github/workflows/daily-newsletter.yml`:

```yaml
name: Daily Newsletter

on:
  schedule:
    - cron: '0 9 * * *'  # Every day at 9 AM UTC
  workflow_dispatch:

jobs:
  send-newsletter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Get latest posts
        run: |
          # Query database for posts from last 24 hours
          # Generate email HTML
          # Send via SendGrid

      - name: Send newsletter
        run: |
          echo "Sending daily newsletter..."
          # Implementation here
```

---

## Part 11: Testing Locally

### Test Static Site Before Deploying

```bash
# Build site
python3 build.py

# Serve locally
cd docs && python3 -m http.server 8000

# Visit in browser
open http://localhost:8000
```

**Or use the built-in serve option**:

```bash
python3 build.py --serve
# Builds + serves on http://localhost:8000
```

### Test Links

Check that all links work:
- ✅ Homepage links to posts
- ✅ Posts link back to homepage
- ✅ Docs index shows all documentation
- ✅ Static assets (CSS) load correctly
- ✅ RSS feed is valid XML

---

## Part 12: Troubleshooting

### Site Not Updating on GitHub Pages

1. **Wait 1-2 minutes** - GitHub Pages rebuild takes time
2. **Check Actions tab** - See if deployment succeeded
3. **Clear browser cache** - Hard refresh with Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)
4. **Verify commit** - Make sure `docs/` folder was committed

### Custom Domain Not Working

1. **Wait 10-15 minutes** - DNS propagation takes time
2. **Check CNAME file** - Should contain your domain (e.g., `deathtodata.com`)
3. **Check DNS settings** - Use `dig deathtodata.com` to verify A records
4. **HTTPS not working** - Wait 15 minutes for Let's Encrypt certificate

### Build Errors

```bash
# If markdown2 is missing
pip install markdown2

# If database is missing
python3 -c "from database import init_db; init_db()"

# If permissions error
chmod +x build.py
```

---

## Part 13: Next Steps

### Enhancements to Add

- [ ] **Search functionality** - Add search box to docs index
- [ ] **Dark mode toggle** - CSS variables + localStorage
- [ ] **Analytics** - Google Analytics or Plausible
- [ ] **Comments** - Utterances (GitHub Issues as comments)
- [ ] **Sitemap** - Generate `sitemap.xml` for SEO
- [ ] **Auto-rebuild** - GitHub Actions on push
- [ ] **Email capture** - Mailchimp/SendGrid integration

### Documentation to Add

- [ ] API reference docs
- [ ] Widget customization guide
- [ ] Theming guide
- [ ] Contributing guide

---

## Summary

**You now have**:
- ✅ Static site builder (`build.py`)
- ✅ GitHub Pages deployment (free hosting)
- ✅ Blog posts + documentation in one site
- ✅ Embeddable widgets (`widget-embed.js`)
- ✅ RSS feed for subscribers
- ✅ Custom domain support (GoDaddy)
- ✅ Local testing (`--serve` option)

**To deploy**:
```bash
python3 build.py
git add docs/
git commit -m "Update site"
git push
```

**Live in 2 minutes at**: `https://YOUR_USERNAME.github.io/YOUR_REPO`

---

**Next**: Set up GoDaddy DNS, configure email (SendGrid), add GitHub Actions automation.
