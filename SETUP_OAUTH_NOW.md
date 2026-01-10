# OAuth Setup - Get CringeProof → Soulfra Login Working

**Status: 90% done - just need OAuth credentials**

## What Works Now:
- ✅ Database tables created (professionals, reviews, loyalty_points)
- ✅ OAuth routes registered in Flask (`oauth_bp`)
- ✅ `.env` file ready for credentials
- ✅ Ollama running on `http://192.168.1.87:11434`
- ✅ Cal reasoning endpoint at `/api/cal/reason`

## What's Missing:
- GitHub OAuth Client ID + Secret (2 minutes to get)
- Google OAuth Client ID + Secret (optional, 5 minutes)

---

## Step 1: Get GitHub OAuth Credentials (2 minutes)

### Go Here:
https://github.com/settings/developers

### Click:
1. "OAuth Apps" → "New OAuth App"

### Fill In:
```
Application name: Soulfra Platform
Homepage URL: http://192.168.1.87:5001
Authorization callback URL: http://192.168.1.87:5001/auth/github/callback
```

### Copy the credentials:
- **Client ID**: `Iv1.abc123def456` (shows immediately)
- **Client Secret**: Click "Generate a new client secret" → Copy it NOW (only shows once)

---

## Step 2: Add Credentials to `.env`

Open `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/.env` and replace:

```bash
# Change these lines:
GITHUB_CLIENT_ID=YOUR_GITHUB_CLIENT_ID_HERE
GITHUB_CLIENT_SECRET=YOUR_GITHUB_CLIENT_SECRET_HERE

# To your actual values:
GITHUB_CLIENT_ID=Iv1.abc123def456
GITHUB_CLIENT_SECRET=ghp_1234567890abcdef...
```

---

## Step 3: Restart Flask

```bash
# Kill existing Flask
pkill -9 -f "python3 app.py"

# Restart
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

---

## Step 4: Test Login

### Visit:
http://192.168.1.87:5001/auth/github

### What Should Happen:
1. Redirects to GitHub
2. "Authorize Soulfra Platform?"
3. Click "Authorize"
4. Redirects back to your Flask app
5. You're logged in - session has your GitHub username
6. User account created in database automatically

---

## Step 5: Connect CringeProof to Soulfra Login

### Update CringeProof Frontend

In `/Users/matthewmauer/Desktop/voice-archive/index.html` (or wherever CringeProof login is):

```html
<!-- Add "Login with GitHub" button -->
<a href="http://192.168.1.87:5001/auth/github">
    <button>Login with GitHub</button>
</a>
```

### Now When You:
1. Go to CringeProof.com
2. Click "Login with GitHub"
3. Authorize via GitHub
4. **You're logged into Soulfra platform**
5. Voice recordings → Transcription → Cal reasoning → All tied to YOUR account

---

## What This Unlocks:

### For You:
- Talk into CringeProof → Logged in as YOU
- Voice goes to database with your user_id
- Cal knows WHO is asking questions
- Track your usage/credits

### For Businesses Using Your Platform:
- They add "Login with Soulfra" button to their site
- Button points to `http://192.168.1.87:5001/auth/github`
- You handle authentication
- They get back a session token
- Now they can call `/api/cal/reason` with authenticated users

---

## Optional: Google OAuth (For Gmail Logins)

If you want "Sign in with Google" too:

### Go Here:
https://console.cloud.google.com/apis/credentials

### Create OAuth 2.0 Client ID:
```
Application type: Web application
Name: Soulfra Platform
Authorized redirect URIs: http://192.168.1.87:5001/auth/google/callback
```

### Add to `.env`:
```bash
GOOGLE_CLIENT_ID=123456-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def...
```

### Then Visit:
http://192.168.1.87:5001/auth/google

---

## Architecture:

```
CringeProof.com (Frontend)
    ↓
"Login with GitHub" button
    ↓
http://192.168.1.87:5001/auth/github (YOUR Flask server)
    ↓
GitHub OAuth (free)
    ↓
User authorizes
    ↓
Callback to YOUR server with code
    ↓
YOUR server creates user account in soulfra.db
    ↓
User session established
    ↓
Voice recording → Transcription → Cal reasoning
    ↓
Everything tied to authenticated user
```

---

## Next Steps After OAuth Works:

1. **Production Domain Setup**
   - Point `api.soulfra.com` to your server IP
   - Update callback URLs to `https://api.soulfra.com/auth/github/callback`
   - Get SSL cert (Let's Encrypt, free)

2. **Multi-Domain Auth**
   - CringeProof.com → Login via api.soulfra.com
   - StPetePros.com → Login via api.soulfra.com
   - Same user account works across ALL your domains

3. **API Keys for Businesses**
   - Generate API keys for businesses
   - They call `/api/cal/reason` with API key
   - No OAuth needed for simple API calls

---

## You're 2 Minutes Away

Just get GitHub OAuth credentials, paste into `.env`, restart Flask.

Then:
- CringeProof login works
- Soulfra admin works
- Cal knows WHO you are
- Voice → AI → Automated → From your laptop

**This is the middleware you wanted.**
