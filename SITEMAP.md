# 🗺️ Bodega Payment SDK - Sitemap

Complete map of all files and what they do.

---

## 📦 Core System (dist/)

**Deployable files** - GitHub Pages serves everything from this folder

### Payment System
- **`pay-bodega.html`** (19KB, 638 lines)
  Bodega-styled payment page with Stripe embedded
  URL params: `?stripe=xxx&amount=25&item=Service&venmo=xxx`

- **`stpetepros-qr.html`** (17KB, 499 lines)
  QR code generator for payment links
  Generates payment QR + receipt QR

- **`bodega-demo.html`** (12KB)
  Interactive demo and documentation
  Test all payment flows

### Tools
- **`llm-router.js`** (351 lines)
  AI router with auto-fallback
  Tries: Ollama → Anthropic → OpenAI → Mock

- **`notebook-manager.html`** (513 lines)
  Jupyter notebook manager with Anki-style learning
  Track working/broken notebooks

### Static Assets
- **`index.html`** - Homepage
- **`feed.xml`** - RSS feed
- **`sitemap.xml`** - SEO sitemap
- **`assets/`** - Images, icons, etc.
  - `merkle-root.json` - Content verification

---

## 🔧 Backend (cloudflare-worker/)

**Serverless backend** for payment tracking

- **`payment-tracker.js`** (313 lines)
  Cloudflare Worker API
  Routes: `/health`, `/api/payments`, `/webhooks/stripe`, `/webhooks/coinbase`

- **`wrangler.toml`** (1KB)
  Deployment configuration
  KV namespaces: PAYMENTS, RECEIPTS

---

## 📚 Documentation (/)

### Core Docs
- **`README.md`** - Project overview and quick start
- **`BODEGA_PAYMENT_SYSTEM.md`** (450 lines) - Complete bodega system docs
- **`STATIC_DEPLOYMENT_COMPLETE.md`** (450 lines) - Deployment guide
- **`SITEMAP.md`** (this file) - File navigation map
- **`WORDMAP.md`** - Key terms and concepts
- **`ARCHITECTURE.md`** - System architecture

### Old Docs (Archive)
- `DEPLOYMENT_SIMPLE.md`
- `SYSTEM_MAP.md`
- Many other `*.md` files (to be organized)

---

## ⚙️ Configuration

- **`.github/workflows/`** - GitHub Actions
  - `deploy-github-pages.yml` - Main deployment (deploys dist/)
  - `deploy.yml` - SSH deployment to production
  - `build-waitlist.yml` - Waitlist builder
  - `update-readme.yml` - Auto-update README
  - `voice-email-processor.yml` - Voice email processing
  - `auto-deploy-phone.yml` - Deploy from phone

- **`.env.example`** - Environment variables template
- **`.gitignore`** - Git ignore rules
- **`CNAME`** - Custom domain config

---

## 🗃️ Database & Backend (Python)

### Flask App
- **`app.py`** - Main Flask application
- **`soulfra.db`** - SQLite database
- **`requirements.txt`** - Python dependencies

### Payment Routes
- **`stpetepros_routes.py`** - StPetePros payment endpoints
- **`payment.py`** - Payment logic
- **`receipt_generator.py`** - Receipt generation
- **`receipt_routes.py`** - Receipt endpoints

### Voice System
- **`voice_backend.py`** - Voice memo backend
- **`voice-integrated.html`** - Voice integration UI

### Database Helpers
- **`db_helpers.py`** - Database utilities
- **`rotation_helpers.py`** - Rotation logic
- **`start_demo.py`** - Demo starter

---

## 📁 Folders

### Active Folders
- **`dist/`** - **PRODUCTION** - Deployed to GitHub Pages
- **`cloudflare-worker/`** - Serverless backend
- **`.github/`** - GitHub configuration
- **`static/`** - Flask app assets (CSS, JS, images)
- **`templates/`** - Flask/Jinja templates
- **`docs/`** - Documentation (if exists)

### Archive/Legacy Folders
*(Not deployed, potentially deletable)*

- **`output/`** - Old build outputs (broken submodules)
  - `output/soulfra/` - Old GitHub Pages output
  - `output/calriven/` - Calriven brand
  - `output/deathtodata/` - DeathToData brand
  - `output/howtocookathome/` - Cooking brand
  - Many others...

- **`_archive_CRUFT/`** - Archived cruft
  - `old_api/` - Old API (broken submodule)

---

## 🎯 Key Files by Purpose

### Want to Deploy?
1. Check `dist/` folder
2. Read `BODEGA_PAYMENT_SYSTEM.md`
3. Run `.github/workflows/deploy-github-pages.yml`

### Want to Customize Payment Page?
1. Edit `dist/pay-bodega.html`
2. Modify CSS (lines 10-380)
3. Update JavaScript (lines 490-680)

### Want to Add Payment Method?
1. Edit `dist/stpetepros-qr.html`
2. Add option to `<select>` (line 250)
3. Add case to `generatePaymentURL()` (line 427)

### Want to Change Stripe Link?
1. Get Stripe Payment Link ID from dashboard
2. Use in QR generator: `stripe=test_xxxxx`
3. Or update directly in URL params

### Want to Track Payments?
1. Deploy Cloudflare Worker (`cloudflare-worker/`)
2. Setup KV namespaces
3. Configure webhooks in Stripe

### Want to Understand Architecture?
1. Read `ARCHITECTURE.md` (system overview)
2. Read `WORDMAP.md` (key terms)
3. Read this file (file locations)

---

## 📊 File Statistics

```
Total Files: ~500+
Core System: 5 files (2,000 lines)
Documentation: 50+ markdown files
Backend: 100+ Python files
Workflows: 6 GitHub Actions
```

**Deployable System (dist/):**
```
pay-bodega.html          638 lines
stpetepros-qr.html       499 lines
llm-router.js            351 lines
notebook-manager.html    513 lines
bodega-demo.html         ~300 lines
-----------------------------------
Total:                  ~2,300 lines
```

**Backend (cloudflare-worker/):**
```
payment-tracker.js       313 lines
wrangler.toml            43 lines
-----------------------------------
Total:                   356 lines
```

**Grand Total Core System:** ~2,700 lines of production code

---

## 🔍 Finding Things

### Search by Feature
- **Payment QR:** `dist/stpetepros-qr.html`
- **Bodega Receipt:** `dist/pay-bodega.html`
- **Stripe Integration:** `cloudflare-worker/payment-tracker.js`
- **LLM Fallback:** `dist/llm-router.js`
- **Notebook Manager:** `dist/notebook-manager.html`

### Search by Tech
- **HTML:** `dist/*.html`
- **JavaScript:** `dist/*.js`
- **Python:** `*.py`
- **Cloudflare:** `cloudflare-worker/`
- **GitHub Actions:** `.github/workflows/`

### Search by Purpose
- **Deployment:** `.github/workflows/deploy*.yml`
- **Documentation:** `*.md`
- **Configuration:** `*.json`, `*.toml`, `.env*`
- **Database:** `*.db`, `*_routes.py`, `db_*.py`

---

## 🗂️ Folder Structure (Simplified)

```
soulfra-simple/
├── dist/                          # ← DEPLOY THIS
│   ├── pay-bodega.html            # Payment page
│   ├── stpetepros-qr.html         # QR generator
│   ├── bodega-demo.html           # Demo
│   ├── llm-router.js              # AI router
│   └── notebook-manager.html      # Jupyter manager
│
├── cloudflare-worker/             # Serverless backend
│   ├── payment-tracker.js
│   └── wrangler.toml
│
├── .github/workflows/             # CI/CD
│   ├── deploy-github-pages.yml   # Main deployment
│   └── *.yml                      # Other workflows
│
├── static/                        # Flask assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                     # Flask templates
│   └── *.html
│
├── *.md                           # Documentation
│
└── *.py                           # Python backend
```

---

## Next: Navigate to...

- **Quick Start:** `README.md`
- **Full Docs:** `BODEGA_PAYMENT_SYSTEM.md`
- **Architecture:** `ARCHITECTURE.md`
- **Key Terms:** `WORDMAP.md`
- **Examples:** `bodega-demo.html`

**Live Demo:** `https://soulfra.github.io/bodega-demo.html`
