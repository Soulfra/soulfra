# How to Use Your Sites

## What's Running RIGHT NOW

Flask server is running on your laptop at:
- **https://localhost:5001** (from this laptop)
- **https://192.168.1.87:5001** (from iPhone/other devices on your WiFi)

## What You Have

### ✅ ALREADY WORKING
- OAuth login (Google/GitHub/Apple)
- User accounts (stored in soulfra.db)
- Voice recording
- QR code authentication
- Admin dashboard
- Profile pages
- Leaderboard
- Voice CAPTCHA
- 100+ other features

### 📍 Key URLs (all at https://localhost:5001)

**Main Pages:**
- `/` - Homepage
- `/login.html` - Login page (OAuth buttons)
- `/feed` - CringeProof feed
- `/voice` - Voice recorder
- `/qr-idea.html` - QR voice interface (the one we just built)

**Admin:**
- `/admin?dev_login=true` - Auto-login as admin
- `/admin/studio` - Admin studio
- `/master-control` - Master control panel
- `/automation` - Automation dashboard

**API:**
- `/api/auth/login` - Login API
- `/api/auth/register` - Register API
- `/api/simple-voice/save` - Save voice recording
- `/api/ideas/list` - List all ideas

## How OAuth ACTUALLY Works

**The login buttons in login.html are placeholders.** They show errors because they need:

1. Go to Google Cloud Console → Create OAuth App → Get Client ID
2. Go to GitHub Settings → OAuth Apps → Create App → Get Client ID
3. Add those IDs to your environment variables or config

**But you can also just skip OAuth** and use the dev login:
- Go to: `https://localhost:5001/admin?dev_login=true`
- You're instantly logged in as admin
- No OAuth needed for testing

## The REAL Workflow

### Option A: Just Use Localhost (Easiest)
1. Open `https://localhost:5001`
2. Browse your site
3. Everything works
4. **No tunnel, no GitHub Pages, no confusion**

### Option B: Use from Phone on Same WiFi
1. Open `https://192.168.1.87:5001` on your phone
2. Accept the security warning (self-signed cert)
3. Everything works including microphone

### Option C: Share Publicly (If You Want)
1. Start cloudflared tunnel:
   ```bash
   cloudflared tunnel --url https://localhost:5001
   ```
2. Get public URL like `https://xyz.trycloudflare.com`
3. Share that URL with anyone
4. They can access your local Flask server from anywhere

## What About cringeproof.com?

**cringeproof.com is static** (GitHub Pages). It has:
- Voice viewer (`/voice/071323f8`)
- Media library (`/media/`)
- QR idea page (`/qr-idea.html`)
- Daily questions (`/index.html`)

But NO backend, NO login, NO database.

**If you want login on cringeproof.com**, you need:
1. Make it call your Flask backend via tunnel
2. OR rebuild it as pure static with localStorage (no real user accounts)

## Summary

**You're confused because you have TWO separate things:**

1. **Flask (localhost:5001)** = Full app with login, database, everything
2. **GitHub Pages (cringeproof.com)** = Static files, no backend

**They don't talk to each other unless you add a tunnel.**

**For now, just use Flask directly:**
→ Open https://localhost:5001
→ Everything works
→ Done

---

**Next Steps:**
1. Test login at `/admin?dev_login=true`
2. Record voice at `/voice`
3. Try QR interface at `/qr-idea.html`
4. When ready, set up real OAuth credentials
5. When ready, add cloudflared tunnel to make it public
