# Serverless OAuth for GitHub Pages (No Cloudflare Tunnel Needed!)

## Problem
- GitHub Pages = static hosting only (no Python/Flask)
- OAuth needs backend server
- Cloudflare Tunnel = overcomplicated, breaks with reconnects
- You want: **cringeproof.com CNAME** → GitHub Pages → OAuth just works

## Solution: Supabase Auth (100% Serverless)

Supabase provides **free serverless OAuth** that works perfectly with GitHub Pages + CNAME domains.

### Why Supabase?
- ✅ Free tier (50,000 users)
- ✅ Google/GitHub/Apple OAuth built-in
- ✅ Works with custom domains (CNAME)
- ✅ Pure JavaScript (no backend needed)
- ✅ Session management included
- ✅ Email magic links (passwordless)

## Setup (5 minutes)

### Step 1: Create Supabase Project
```bash
# Go to: https://supabase.com
# Click "New Project"
# Name: cringeproof-auth
# Region: US West (closest to you)
# Database Password: (generate strong one)
```

### Step 2: Enable OAuth Providers
```
Dashboard → Authentication → Providers

Google OAuth:
- Client ID: (from Google Cloud Console)
- Client Secret: (from Google Cloud Console)
- Authorized redirect URIs: https://cringeproof.com

GitHub OAuth:
- Client ID: (from GitHub Developer Settings)
- Client Secret: (from GitHub)
- Authorization callback URL: https://cringeproof.com

Apple Sign In:
- Services ID: (from Apple Developer)
- Key ID: (from Apple)
- Team ID: (from Apple)
```

### Step 3: Add Supabase to cringeproof.com

Create `/voice-archive/auth.js`:

```javascript
// Supabase Auth - Works with GitHub Pages + CNAME
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  'https://YOUR_PROJECT.supabase.co',
  'YOUR_ANON_KEY'
)

// Google OAuth
export async function loginWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'https://cringeproof.com/record-simple.html'
    }
  })

  if (error) console.error('Login failed:', error)
  return data
}

// GitHub OAuth
export async function loginWithGitHub() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: {
      redirectTo: 'https://cringeproof.com/record-simple.html'
    }
  })

  if (error) console.error('Login failed:', error)
  return data
}

// Apple Sign In
export async function loginWithApple() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'apple',
    options: {
      redirectTo: 'https://cringeproof.com/record-simple.html'
    }
  })

  if (error) console.error('Login failed:', error)
  return data
}

// Check if user is logged in
export async function getUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

// Logout
export async function logout() {
  const { error } = await supabase.auth.signOut()
  if (error) console.error('Logout failed:', error)
}

// Listen for auth changes
supabase.auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event, session)

  if (event === 'SIGNED_IN') {
    // Save to localStorage
    localStorage.setItem('auth_token', session.access_token)
    localStorage.setItem('user_id', session.user.id)
    localStorage.setItem('email', session.user.email)
  }

  if (event === 'SIGNED_OUT') {
    localStorage.clear()
  }
})
```

### Step 4: Add Login Buttons to HTML

Update `/voice-archive/index.html`:

```html
<script type="module">
  import { loginWithGoogle, loginWithGitHub, loginWithApple, getUser } from './auth.js'

  // Check if already logged in
  const user = await getUser()
  if (user) {
    console.log('Logged in as:', user.email)
    document.getElementById('userEmail').textContent = user.email
  }

  // Login button handlers
  document.getElementById('googleLogin').onclick = loginWithGoogle
  document.getElementById('githubLogin').onclick = loginWithGitHub
  document.getElementById('appleLogin').onclick = loginWithApple
</script>

<!-- Login Buttons -->
<button id="googleLogin">🔐 Login with Google</button>
<button id="githubLogin">🔐 Login with GitHub</button>
<button id="appleLogin">🔐 Login with Apple</button>

<div id="userEmail"></div>
```

## Deployment (CNAME Only - No Tunnels!)

### GoDaddy DNS Setup
```
Type: CNAME
Name: www
Value: USERNAME.github.io
TTL: 600
```

### GitHub Pages Settings
```
Repo: voice-archive
Settings → Pages
Source: Deploy from branch (main)
Custom domain: cringeproof.com
Enforce HTTPS: ✅
```

### That's It!
No Cloudflare Tunnel needed. Just:
1. Git push to voice-archive repo
2. CNAME points to GitHub Pages
3. Supabase handles all OAuth
4. Works perfectly with custom domain

## Testing

### Localhost (Development)
```javascript
// Use localhost URL for testing
const supabase = createClient(
  'https://YOUR_PROJECT.supabase.co',
  'YOUR_ANON_KEY',
  {
    auth: {
      redirectTo: 'http://localhost:8000/record-simple.html'
    }
  }
)
```

### Production (cringeproof.com)
```javascript
// Use production URL
const supabase = createClient(
  'https://YOUR_PROJECT.supabase.co',
  'YOUR_ANON_KEY',
  {
    auth: {
      redirectTo: 'https://cringeproof.com/record-simple.html'
    }
  }
)
```

## What Happens When User Logs In

1. User clicks "Login with Google"
2. Redirected to Google OAuth consent screen
3. User approves
4. Google redirects to: `https://cringeproof.com/record-simple.html?access_token=...`
5. Supabase JavaScript detects token in URL
6. Auto-saves session to localStorage
7. User is logged in!

## Database Integration

Supabase also gives you a PostgreSQL database (free tier: 500MB):

```javascript
// Save voice recording metadata
const { data, error } = await supabase
  .from('voice_recordings')
  .insert([
    {
      user_id: user.id,
      transcription: 'Hello world',
      public_hash: 'abc123',
      created_at: new Date()
    }
  ])
```

## Why This Beats Cloudflare Tunnel

| Feature | Cloudflare Tunnel | Supabase |
|---------|------------------|----------|
| Setup Complexity | High (command line, restart on disconnect) | Low (web dashboard) |
| Reliability | Breaks on reconnect | Always online |
| Custom Domain | Requires manual config | Built-in support |
| Cost | Free but flaky | Free and stable |
| OAuth Providers | DIY in Flask | Built-in (Google/GitHub/Apple) |
| Session Management | Roll your own | Built-in |
| Database | Separate SQLite | Built-in Postgres |

## Summary

**Stop fighting with Cloudflare Tunnel.** Use Supabase instead:
- GitHub Pages hosts your static files
- CNAME points to GitHub Pages
- Supabase handles all OAuth
- Pure JavaScript, no Python backend needed
- Works perfectly with cringeproof.com

Your Flask app on localhost:5001 can still exist for development/testing, but production OAuth goes through Supabase.
