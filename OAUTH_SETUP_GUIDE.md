# OAuth Setup Guide - Google, GitHub, Apple

Step-by-step guide to get OAuth credentials for your Soulfra login system.

## 🔐 Why OAuth?

OAuth allows users to login with existing accounts (Google, GitHub, Apple) instead of creating new passwords. Benefits:
- ✅ No password management
- ✅ Faster signup/login
- ✅ More secure (uses existing OAuth providers)
- ✅ Automatic email verification

## 📧 Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Project name: `Soulfra`
4. Click "Create"

### Step 2: Enable Google+ API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click "Enable"

### Step 3: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `Soulfra`
   - User support email: your_email@gmail.com
   - Developer contact: your_email@gmail.com
   - Scopes: `email`, `profile`, `openid`
   - Test users: Add your email
   - Click "Save and Continue"

4. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: `Soulfra Web`
   - Authorized redirect URIs:
     - `http://localhost:5001/auth/google/callback` (for testing)
     - `https://soulfra-api.railway.app/auth/google/callback` (for production)
   - Click "Create"

5. **Save your credentials:**
   - Client ID: `123456789-abc123def456.apps.googleusercontent.com`
   - Client Secret: `GOCSPX-abc123def456...`

### Step 4: Add to .env

```bash
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456...
```

## 🐙 GitHub OAuth Setup

### Step 1: Create GitHub OAuth App

1. Go to: https://github.com/settings/developers
2. Click "OAuth Apps" → "New OAuth App"

### Step 2: Configure App

- Application name: `Soulfra`
- Homepage URL: `https://soulfra.com`
- Application description: `Soulfra decentralized AI platform`
- Authorization callback URL:
  - `http://localhost:5001/auth/github/callback` (for testing)
  - Or `https://soulfra-api.railway.app/auth/github/callback` (for production)

### Step 3: Get Credentials

After creating the app:
1. **Client ID** is shown immediately
2. Click "Generate a new client secret"
3. **Client Secret** is shown once (copy it now!)

### Step 4: Add to .env

```bash
GITHUB_CLIENT_ID=Iv1.abc123def456
GITHUB_CLIENT_SECRET=abc123def456789...
```

## 🍎 Apple Sign In Setup (Optional)

Apple Sign In is more complex and requires:
- Apple Developer Account ($99/year)
- App ID configuration
- Service ID configuration
- Private key generation

**For now, you can skip Apple Sign In** and just use Google/GitHub.

If you want to set it up later:
1. Go to: https://developer.apple.com/account/resources/identifiers/list
2. Follow: https://developer.apple.com/sign-in-with-apple/get-started/

## 🔧 Local Testing

### Step 1: Create .env file

```bash
cat > .env << 'EOF'
# Flask Configuration
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=development
FLASK_DEBUG=1

# Database
SOULFRA_DB=soulfra.db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Base URL
BASE_URL=http://localhost:5001
EOF
```

### Step 2: Add Your Credentials

Edit `.env` and replace:
- `your_google_client_id_here`
- `your_google_client_secret_here`
- `your_github_client_id_here`
- `your_github_client_secret_here`

### Step 3: Start Server

```bash
./START_PRODUCTION.sh
```

### Step 4: Test OAuth

**Test Google OAuth:**
1. Go to: http://localhost:5001/login.html
2. Click "Continue with Google"
3. You should be redirected to Google login
4. After login, redirected back to your app

**Test GitHub OAuth:**
1. Go to: http://localhost:5001/login.html
2. Click "Continue with GitHub"
3. You should be redirected to GitHub authorization
4. After authorization, redirected back to your app

## 🚀 Production Deployment

When deploying to Railway:

### Step 1: Update OAuth Redirect URLs

**Google:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth client
3. Add redirect URI: `https://your-railway-app.up.railway.app/auth/google/callback`

**GitHub:**
1. Go to: https://github.com/settings/developers
2. Edit your OAuth app
3. Update callback URL: `https://your-railway-app.up.railway.app/auth/github/callback`

### Step 2: Set Railway Environment Variables

```bash
railway variables set GOOGLE_CLIENT_ID=your_google_client_id
railway variables set GOOGLE_CLIENT_SECRET=your_google_client_secret
railway variables set GITHUB_CLIENT_ID=your_github_client_id
railway variables set GITHUB_CLIENT_SECRET=your_github_client_secret
railway variables set BASE_URL=https://your-railway-app.up.railway.app
```

## 🔒 Security Best Practices

1. **Never commit .env to git:**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use different OAuth apps for dev/prod:**
   - Development: `http://localhost:5001` callbacks
   - Production: `https://your-domain.com` callbacks

3. **Rotate secrets regularly:**
   - Regenerate client secrets every 6 months
   - Update in .env and Railway

4. **Limit OAuth scopes:**
   - Only request `email` and `profile`
   - Don't ask for unnecessary permissions

## 🐛 Troubleshooting

**Error: "redirect_uri_mismatch"**
- Make sure redirect URI in OAuth app settings exactly matches the one in your code
- Check for trailing slashes, http vs https, etc.

**Error: "invalid_client"**
- Client ID or Secret is wrong
- Copy-paste carefully, check for extra spaces

**Error: "access_denied"**
- User clicked "Cancel" during OAuth
- This is expected behavior, show friendly error message

**OAuth works locally but not in production:**
- Update OAuth app redirect URIs to include production URL
- Update `BASE_URL` environment variable in Railway

## 📚 Resources

- **Google OAuth Docs:** https://developers.google.com/identity/protocols/oauth2
- **GitHub OAuth Docs:** https://docs.github.com/en/developers/apps/building-oauth-apps
- **Apple Sign In Docs:** https://developer.apple.com/sign-in-with-apple/
- **OAuth 2.0 Explained:** https://www.oauth.com/

## ✅ Checklist

- [ ] Created Google Cloud project
- [ ] Enabled Google+ API
- [ ] Created Google OAuth credentials
- [ ] Created GitHub OAuth app
- [ ] Created .env file with credentials
- [ ] Tested Google login locally
- [ ] Tested GitHub login locally
- [ ] Updated OAuth redirect URLs for production
- [ ] Set Railway environment variables
- [ ] Tested OAuth in production
