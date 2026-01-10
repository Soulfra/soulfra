# Multi-Domain Authentication Architecture

Complete guide to your decentralized Soulfra + CringeProof login system.

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Static Sites)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  soulfra.com (GitHub Pages)          cringeproof.com           │
│  ├── login.html                       ├── cringeproof-login.html│
│  ├── signup.html                      ├── cringeproof-signup.html│
│  └── dashboard.html                   └── cringeproof-dashboard.html│
│                                                                 │
│  github.com/soulfra                                            │
│  └── README.md (Profile + Gacha Widget)                       │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓ API Calls
┌────────────────────────────────────────────────────────────────┐
│                   BACKEND (Flask on Railway)                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  app.py (Flask server)                                         │
│  ├── auth_routes.py (Email/Password login)                    │
│  ├── oauth_routes.py (Google/GitHub/Apple OAuth)              │
│  ├── customer_export.py (Customer data aggregation)           │
│  ├── batch_workflows.py (GitHub Pages sync)                   │
│  └── product_tracking.py (QR/UPC tracking)                    │
│                                                                 │
│  Per-Domain Isolation:                                         │
│  - Session domain: soulfra.com vs cringeproof.com             │
│  - Database field: users.display_name = domain                │
│  - Same email = different accounts per domain                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓ Database
┌────────────────────────────────────────────────────────────────┐
│                        DATABASES                                │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  soulfra.db                    cringeproof.db                  │
│  ├── 23 users (dev/test)       ├── 0 users (production)       │
│  ├── 200+ tables (bloat)       ├── 7 tables (clean schema)    │
│  └── Port 5002                 └── Port 5001                   │
│                                                                 │
│  Environment variable switching: SOULFRA_DB=soulfra.db|cringeproof.db│
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## 🔑 Per-Domain User Isolation

Your `auth_routes.py` already supports **per-domain isolation**:

```python
# Signup with domain
POST /api/auth/signup
{
  "email": "user@example.com",
  "password": "password123",
  "domain": "soulfra.com"  // or "cringeproof.com"
}

# Login with domain
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123",
  "domain": "soulfra.com"  // or "cringeproof.com"
}
```

**How it works:**
- `display_name` field stores domain: `soulfra.com` or `cringeproof.com`
- Same email can have **different accounts** on different domains
- Session includes domain context: `session['domain'] = 'soulfra.com'`

**Example:**
```
user@gmail.com on soulfra.com → User ID 1
user@gmail.com on cringeproof.com → User ID 2

Different passwords, different accounts, isolated data!
```

## 🌐 GitHub Pages Setup

### Soulfra.com (Already Configured)

**DNS:**
```
soulfra.com CNAME → soulfra.github.io
```

**Files:**
- `soulfra.github.io/CNAME` → Contains `soulfra.com`
- `soulfra.github.io/login.html` → Soulfra login page
- `soulfra.github.io/index.html` → Homepage

**Login Flow:**
1. User visits `https://soulfra.com/login.html`
2. Fills email/password → Sends to backend API with `domain: 'soulfra.com'`
3. Backend creates/validates user in `soulfra.db` with `display_name='soulfra.com'`
4. Redirects to `https://soulfra.com/dashboard.html`

### CringeProof.com

**Option 1: Same GitHub Pages Repo**
```
cringeproof.com CNAME → soulfra.github.io
```

Then access:
- `https://cringeproof.com/cringeproof-login.html`
- `https://cringeproof.com/cringeproof-dashboard.html`

**Option 2: Separate GitHub Pages Repo**
1. Create new repo: `cringeproof/cringeproof.github.io`
2. Add `CNAME` file: `cringeproof.com`
3. Copy `cringeproof-login.html` → `login.html`
4. Configure DNS: `cringeproof.com CNAME → cringeproof.github.io`

### GitHub Profile (github.com/soulfra)

**Special repository for profile README:**

1. Create repo: `soulfra/soulfra` (name must match username)
2. Upload `README.md` from `github-profile-readme/README.md`
3. Appears on your profile: `https://github.com/soulfra`

**Optional: Add Gacha Widget**
- Upload `GACHA_WIDGET.html` to the repo
- Enable GitHub Pages for the repo
- Access at: `https://soulfra.github.io/soulfra/GACHA_WIDGET.html`
- Link from README: `[🎲 Try Gacha](https://soulfra.github.io/soulfra/GACHA_WIDGET.html)`

## 🚀 Deployment Flow

### 1. Deploy Backend to Railway

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Create Procfile
echo "web: gunicorn app:app --bind 0.0.0.0:\$PORT" > Procfile

# Create requirements.txt
pip3 freeze > requirements.txt

# Login to Railway
railway login

# Initialize project
railway init

# Set environment variables
railway variables set SOULFRA_DB=cringeproof.db
railway variables set FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
railway variables set GOOGLE_CLIENT_ID=your_google_client_id
railway variables set GOOGLE_CLIENT_SECRET=your_google_client_secret
railway variables set GITHUB_CLIENT_ID=your_github_client_id
railway variables set GITHUB_CLIENT_SECRET=your_github_client_secret

# Deploy
railway up

# Get public URL
railway domain
# Example: soulfra-backend-production.up.railway.app
```

### 2. Update Static Sites

**Update `soulfra.github.io/login.html`:**
```javascript
const API_URL = 'https://soulfra-backend-production.up.railway.app';
```

**Update `soulfra.github.io/cringeproof-login.html`:**
```javascript
const API_URL = 'https://soulfra-backend-production.up.railway.app';
```

**Commit and push to GitHub:**
```bash
cd soulfra.github.io
git add .
git commit -m "Update API URL for production"
git push
```

### 3. Configure OAuth Redirect URLs

**Google:**
- Add redirect: `https://soulfra-backend-production.up.railway.app/auth/google/callback`

**GitHub:**
- Add callback: `https://soulfra-backend-production.up.railway.app/auth/github/callback`

### 4. Test Full Flow

**Soulfra Login:**
1. Visit: `https://soulfra.com/login.html`
2. Click "Continue with Google" or "Continue with GitHub"
3. Authorize
4. Should redirect back to soulfra.com

**CringeProof Login:**
1. Visit: `https://cringeproof.com/cringeproof-login.html`
2. Click "Continue with Google"
3. Should create **separate account** with `domain='cringeproof.com'`

## 📊 Database Switching

**Environment Variable:**
```bash
# Use cringeproof.db
export SOULFRA_DB=cringeproof.db
./START_CRINGEPROOF.sh

# Use soulfra.db
export SOULFRA_DB=soulfra.db
./START_SOULFRA.sh
```

**Railway Configuration:**
```bash
# Production uses cringeproof.db (clean, 0 users)
railway variables set SOULFRA_DB=cringeproof.db
```

**Run Both Simultaneously:**
```bash
# Terminal 1: CringeProof (Port 5001, cringeproof.db)
./START_CRINGEPROOF.sh

# Terminal 2: Soulfra (Port 5002, soulfra.db)
./START_SOULFRA.sh
```

## 🎮 Use Cases

### Use Case 1: Same Person, Two Domains

**Scenario:** You use both soulfra.com and cringeproof.com

**Result:**
- `you@gmail.com` on soulfra.com → Profile 1
- `you@gmail.com` on cringeproof.com → Profile 2
- Separate accounts, separate data, isolated

### Use Case 2: Business vs Personal

**Scenario:**
- `soulfra.com` = Professional AI platform
- `cringeproof.com` = Gaming/community site

**Result:**
- Professional identity on soulfra.com
- Gaming identity on cringeproof.com
- Same email, different contexts

### Use Case 3: Multi-Tenant SaaS

**Scenario:**
- You offer white-label service
- Each client gets their own domain
- Same backend, isolated data

**Result:**
- `client1.soulfra.com` → Domain: `client1.soulfra.com`
- `client2.soulfra.com` → Domain: `client2.soulfra.com`
- Per-domain user accounts, zero data leakage

## 🔒 Security Considerations

1. **Session Isolation:**
   - Sessions include `domain` field
   - Backend validates domain on every request
   - No cross-domain data access

2. **OAuth Domain Binding:**
   - OAuth callback includes domain in state
   - After OAuth, user assigned to correct domain
   - No confusion between domains

3. **Database Isolation:**
   - `display_name` field stores domain
   - SQL queries filter by domain
   - Same email = different user IDs

4. **HTTPS Everywhere:**
   - GitHub Pages → Auto HTTPS
   - Railway → Auto HTTPS
   - No HTTP traffic

## 🎯 Next Steps

1. ✅ **Create GitHub profile README:**
   - Create repo: `soulfra/soulfra`
   - Upload `README.md`
   - Optional: Add gacha widget

2. ✅ **Deploy backend to Railway:**
   - Follow `DEPLOY_RAILWAY.md`
   - Set OAuth credentials
   - Get public URL

3. ✅ **Update static sites:**
   - Change `API_URL` to Railway URL
   - Push to GitHub Pages
   - Test login from iPhone

4. ✅ **Configure OAuth:**
   - Follow `OAUTH_SETUP_GUIDE.md`
   - Add redirect URLs
   - Test Google/GitHub login

5. ✅ **Proof-of-concept test:**
   - Be first user on cringeproof.com
   - Export to CSV
   - Verify per-domain isolation

## 📚 Files Created

```
github-profile-readme/
├── README.md - GitHub profile README
├── SETUP_INSTRUCTIONS.md - How to create special repo
└── GACHA_WIDGET.html - Interactive gacha simulator

soulfra.github.io/
├── login.html - Soulfra login page (purple gradient)
└── cringeproof-login.html - CringeProof login (neubrutalist)

/
├── DEPLOY_RAILWAY.md - Railway deployment guide
├── OAUTH_SETUP_GUIDE.md - Get OAuth credentials
├── START_PRODUCTION.sh - Production startup with OAuth
├── START_CRINGEPROOF.sh - CringeProof backend (port 5001)
├── START_SOULFRA.sh - Soulfra backend (port 5002)
├── FRESH_START.md - Fresh database proof-of-concept
└── MULTI_DOMAIN_ARCHITECTURE.md - This file
```

## 🤝 Support

**Questions?** Check the docs:
- GitHub Profile README: `github-profile-readme/SETUP_INSTRUCTIONS.md`
- OAuth Setup: `OAUTH_SETUP_GUIDE.md`
- Railway Deployment: `DEPLOY_RAILWAY.md`
- Fresh Database: `FRESH_START.md`
- Customer Export: `CUSTOMER_EXPORT_README.md`
