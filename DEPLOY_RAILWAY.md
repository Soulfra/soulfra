# Railway Deployment Guide - Soulfra Backend

Deploy your Flask backend to Railway (free tier) to make it accessible from your iPhone and static sites.

## What is Railway?

Railway is a modern hosting platform with:
- ✅ Free tier (500 hours/month, $5 credit)
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Environment variables
- ✅ No credit card required for free tier

## Step 1: Install Railway CLI

**macOS:**
```bash
brew install railway
```

**Linux/macOS (alternative):**
```bash
curl -fsSL https://railway.app/install.sh | sh
```

**Windows:**
```powershell
iwr https://railway.app/install.ps1 | iex
```

## Step 2: Login to Railway

```bash
railway login
```

This opens your browser to authenticate with GitHub.

## Step 3: Initialize Railway Project

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Initialize Railway project
railway init
```

Follow prompts:
- Project name: `soulfra-backend`
- Environment: `production`

## Step 4: Create Procfile

Railway needs a `Procfile` to know how to run your app:

```bash
cat > Procfile << 'EOF'
web: gunicorn app:app --bind 0.0.0.0:$PORT
EOF
```

## Step 5: Create requirements.txt

Railway needs to know your Python dependencies:

```bash
pip3 freeze > requirements.txt
```

Or manually create:

```txt
Flask==3.0.0
Flask-CORS==4.0.0
gunicorn==21.2.0
requests==2.31.0
werkzeug==3.0.1
cryptography==41.0.7
```

## Step 6: Create runtime.txt

Tell Railway which Python version to use:

```bash
echo "python-3.11.0" > runtime.txt
```

## Step 7: Set Environment Variables

**Via Railway CLI:**

```bash
# Set database file
railway variables set SOULFRA_DB=soulfra.db

# Set Flask secret key
railway variables set FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Set OAuth credentials (get these from Google/GitHub)
railway variables set GOOGLE_CLIENT_ID=your_google_client_id
railway variables set GOOGLE_CLIENT_SECRET=your_google_client_secret
railway variables set GITHUB_CLIENT_ID=your_github_client_id
railway variables set GITHUB_CLIENT_SECRET=your_github_client_secret

# Set base URL (Railway will provide this)
railway variables set BASE_URL=https://soulfra-backend-production.up.railway.app
```

**Via Railway Dashboard:**
1. Go to: https://railway.app/dashboard
2. Click your project
3. Go to "Variables" tab
4. Add environment variables

## Step 8: Deploy to Railway

```bash
# Deploy your app
railway up
```

Railway will:
1. Upload your code
2. Install dependencies from `requirements.txt`
3. Run `gunicorn` from `Procfile`
4. Assign a public URL

## Step 9: Get Your Public URL

```bash
# Get your Railway URL
railway domain
```

Example output:
```
soulfra-backend-production.up.railway.app
```

Your backend is now live at:
```
https://soulfra-backend-production.up.railway.app
```

## Step 10: Test Your Deployment

**Test health endpoint:**
```bash
curl https://soulfra-backend-production.up.railway.app/
```

**Test login API:**
```bash
curl -X POST https://soulfra-backend-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "domain": "soulfra.com"}'
```

## Step 11: Update Static Sites

Update `API_URL` in your login pages:

**soulfra.github.io/login.html:**
```javascript
const API_URL = 'https://soulfra-backend-production.up.railway.app';
```

**soulfra.github.io/cringeproof-login.html:**
```javascript
const API_URL = 'https://soulfra-backend-production.up.railway.app';
```

## Step 12: Configure OAuth Redirect URLs

Update your OAuth app settings:

**Google OAuth Console:**
- Go to: https://console.cloud.google.com/apis/credentials
- Edit OAuth client
- Add redirect URI: `https://soulfra-backend-production.up.railway.app/auth/google/callback`

**GitHub OAuth Settings:**
- Go to: https://github.com/settings/developers
- Edit your OAuth app
- Authorization callback URL: `https://soulfra-backend-production.up.railway.app/auth/github/callback`

## Troubleshooting

**Check logs:**
```bash
railway logs
```

**Restart app:**
```bash
railway restart
```

**Connect to Railway shell:**
```bash
railway shell
```

**View environment variables:**
```bash
railway variables
```

## Using Custom Domain (Optional)

Railway supports custom domains for free!

**Add custom domain:**
```bash
railway domain add api.soulfra.com
```

Railway will give you DNS records to add:

```
CNAME api.soulfra.com -> soulfra-backend-production.up.railway.app
```

Then update your DNS at your domain registrar.

## Alternative: Fly.io

If Railway doesn't work, try Fly.io:

**Install flyctl:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Deploy to Fly.io:**
```bash
fly launch
fly deploy
```

## Cost Breakdown

**Railway Free Tier:**
- 500 hours/month (enough for one app running 24/7)
- $5 credit/month
- 1GB RAM
- 1GB disk space

**Paid tier (if needed):**
- $5/month for additional resources

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Update static site `API_URL` variables
3. ✅ Configure OAuth redirect URLs
4. ✅ Test login from iPhone at `soulfra.com/login.html`
5. ✅ Test registration from iPhone
6. ✅ Export customer list to CSV

## Support

**Railway Docs:** https://docs.railway.app/
**Railway Discord:** https://discord.gg/railway
**Fly.io Docs:** https://fly.io/docs/
