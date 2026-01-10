# 🚀 CringeProof GitHub Pages + Flask Hybrid Deployment

**Goal**: Deploy CringeProof with GitHub Pages (static files) + Flask API (dynamic backend)

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     USER BROWSER                            │
│              https://cringeproof.com                        │
└─────────────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────┴────────────┐
        │                          │
        ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│  GITHUB PAGES   │      │   FLASK API     │
│  (Static CDN)   │      │  (localhost)    │
│                 │      │                 │
│  - wall.html    │      │  - /api/wall/*  │
│  - record.html  │      │  - /github/*    │
│  - CSS/JS       │      │  - /api/ipfs/*  │
│  - Images       │      │  - SQLite DB    │
└─────────────────┘      └─────────────────┘
   FREE + FAST           YOUR LAPTOP/VPS
```

---

## Why This Hybrid Approach?

### GitHub Pages (Static):
- ✅ **FREE** hosting
- ✅ **FAST** (Cloudflare CDN)
- ✅ **SSL** included (HTTPS automatic)
- ✅ **No server management**
- ❌ Can't run Python/databases

### Flask API (Dynamic):
- ✅ **Database** (SQLite)
- ✅ **Voice recording** storage
- ✅ **IPFS integration**
- ✅ **GitHub OAuth**
- ❌ Requires server (laptop/VPS/Railway)

### Combined:
- ✅ Static pages served FREE from GitHub
- ✅ API calls go to your Flask server
- ✅ Best of both worlds

---

## Step-by-Step Deployment

### Phase 1: Prepare GitHub Repository

1. **Create GitHub Repo**:
   ```bash
   # Already exists: soulfra/voice-archive
   # Or create new: gh repo create cringeproof-app --public
   ```

2. **Add CNAME File**:
   ```bash
   cd voice-archive/
   echo "cringeproof.com" > CNAME
   git add CNAME
   git commit -m "Add custom domain"
   git push origin main
   ```

3. **Enable GitHub Pages**:
   - Go to: `https://github.com/soulfra/voice-archive/settings/pages`
   - Source: **Deploy from main branch**
   - Custom domain: `cringeproof.com`
   - ✅ Enforce HTTPS

---

### Phase 2: Configure DNS (GoDaddy)

**For cringeproof.com → GitHub Pages**:

Add these DNS records in GoDaddy:

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

**Verify**:
```bash
dig cringeproof.com +noall +answer
# Should show GitHub Pages IPs
```

Wait 10-60 minutes for DNS propagation.

---

### Phase 3: Update HTML to Use Hybrid URLs

Currently `wall.html` calls:
```javascript
fetch('/api/wall/feed?domain=cringeproof.com')
```

Update to:
```javascript
// Use Flask API on localhost (or your VPS)
const API_BASE = 'https://192.168.1.87:5001';  // Dev
// const API_BASE = 'https://api.cringeproof.com';  // Production

fetch(`${API_BASE}/api/wall/feed?domain=cringeproof.com')
```

This way:
- **HTML/CSS/JS** → Served from GitHub Pages (fast)
- **API calls** → Go to your Flask server

---

### Phase 4: Flask API Configuration

**Option A: Run on Laptop** (Development)
```bash
# Start Flask
python3 app.py

# Available at: https://192.168.1.87:5001
```

**Option B: Deploy to VPS** (Production)
```bash
# SSH to VPS
ssh user@your-vps.com

# Clone repo
git clone https://github.com/soulfra/voice-archive
cd voice-archive

# Install dependencies
pip3 install -r requirements.txt

# Run Flask with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

**Option C: Deploy to Railway** (Easiest)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

Railway gives you: `https://cringeproof-api.railway.app`

---

### Phase 5: API Subdomain (Optional)

Instead of `https://192.168.1.87:5001`, use `https://api.cringeproof.com`

**DNS Record**:
```
Type: CNAME
Name: api
Value: cringeproof-api.railway.app  (or your VPS IP)
```

**Update wall.html**:
```javascript
const API_BASE = 'https://api.cringeproof.com';
```

---

### Phase 6: Add GitHub Auth

1. **Register GitHub OAuth App**:
   - Go to: https://github.com/settings/developers
   - New OAuth App
   - Name: `CringeProof`
   - Homepage: `https://cringeproof.com`
   - Callback: `https://api.cringeproof.com/github/callback`
   - Get `CLIENT_ID` and `CLIENT_SECRET`

2. **Set Environment Variables**:
   ```bash
   export GITHUB_CLIENT_ID=your_client_id
   export GITHUB_CLIENT_SECRET=your_client_secret
   export GITHUB_REDIRECT_URI=https://api.cringeproof.com/github/callback
   ```

3. **Add to app.py**:
   ```python
   from github_auth_routes import github_auth_bp
   app.register_blueprint(github_auth_bp)
   ```

4. **Update wall.html**:
   ```html
   <!-- Add login button -->
   <a href="https://api.cringeproof.com/github/login">
       Login with GitHub
   </a>
   ```

---

## Testing

### Test GitHub Pages (Static):
```bash
# Should load from GitHub
curl https://cringeproof.com
curl https://cringeproof.com/wall.html
```

### Test Flask API (Dynamic):
```bash
# Should return JSON
curl https://api.cringeproof.com/api/wall/feed?domain=cringeproof.com
curl https://api.cringeproof.com/github/status
```

### Test Hybrid (Browser):
1. Visit `https://cringeproof.com/wall.html`
2. HTML loads from GitHub Pages ✅
3. JavaScript makes API call to `https://api.cringeproof.com` ✅
4. Data populates from Flask database ✅

---

## Deployment Checklist

### GitHub Pages:
- [ ] CNAME file added to repo
- [ ] GitHub Pages enabled in repo settings
- [ ] Custom domain configured: `cringeproof.com`
- [ ] DNS A records pointing to GitHub
- [ ] HTTPS enforced
- [ ] Static files (HTML/CSS/JS) pushed to main branch

### Flask API:
- [ ] app.py running (laptop/VPS/Railway)
- [ ] Environment variables set (GITHUB_CLIENT_ID, etc.)
- [ ] GitHub auth routes registered
- [ ] Database migrations run
- [ ] CORS enabled for cringeproof.com origin
- [ ] SSL certificate (if self-hosting)

### DNS:
- [ ] cringeproof.com → GitHub Pages IPs
- [ ] www.cringeproof.com → CNAME to soulfra.github.io
- [ ] api.cringeproof.com → CNAME to Railway/VPS (optional)

### Testing:
- [ ] Static pages load from GitHub
- [ ] API calls work from browser
- [ ] GitHub OAuth flow works
- [ ] Voice recording saves to database
- [ ] Wall displays recordings

---

## Production URLs

Once deployed:

| Component | URL | Hosted On |
|-----------|-----|-----------|
| Homepage | https://cringeproof.com | GitHub Pages (free) |
| Voice Wall | https://cringeproof.com/wall.html | GitHub Pages (free) |
| Recorder | https://cringeproof.com/record-simple.html | GitHub Pages (free) |
| Wall API | https://api.cringeproof.com/api/wall/feed | Flask (Railway/VPS) |
| GitHub Login | https://api.cringeproof.com/github/login | Flask (Railway/VPS) |
| IPFS Publish | https://api.cringeproof.com/api/ipfs/publish | Flask (Railway/VPS) |

---

## Cost Breakdown

| Service | Cost | What For |
|---------|------|----------|
| GitHub Pages | **FREE** | Static HTML/CSS/JS hosting |
| GitHub OAuth | **FREE** | User authentication |
| IPFS (self-hosted) | **FREE** | Decentralized storage |
| Railway (Starter) | **FREE** ($5 credit/month) | Flask API hosting |
| GoDaddy Domain | **$12/year** | cringeproof.com |
| **TOTAL** | **~$12/year** | For global deployment |

---

## Next Steps

1. **Test Locally First**:
   - Push `voice-archive/` to GitHub
   - Update API_BASE in wall.html to `https://192.168.1.87:5001`
   - Verify hybrid works locally

2. **Deploy Flask API**:
   - Choose: Railway (easiest) or VPS (more control)
   - Set environment variables
   - Deploy and get API URL

3. **Update DNS**:
   - Point cringeproof.com to GitHub Pages
   - Point api.cringeproof.com to Flask API

4. **Final Test**:
   - Visit https://cringeproof.com
   - Test GitHub login
   - Record voice memo
   - See it appear on wall

---

## Troubleshooting

### "DNS_PROBE_FINISHED_NXDOMAIN"
- DNS not propagated yet (wait 1 hour)
- A records not configured correctly

### "Mixed Content" Warning
- API calls must use HTTPS, not HTTP
- Get SSL cert for Flask API (Railway includes SSL free)

### "CORS Error"
- Add CORS headers in Flask:
  ```python
  from flask_cors import CORS
  CORS(app, origins=['https://cringeproof.com'])
  ```

### GitHub OAuth Redirect Mismatch
- Callback URL in GitHub app settings must match exactly
- Check: `https://api.cringeproof.com/github/callback`

---

**Built on Bitcoin's Birthday 2026 - Free hosting, decentralized storage, user ownership.**
