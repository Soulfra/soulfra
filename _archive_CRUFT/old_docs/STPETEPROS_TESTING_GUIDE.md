# StPetePros Testing Guide

## ✅ What Just Got Deployed

You now have **universal keyboard navigation** + **static/dynamic hybrid system** working on StPetePros!

### Live Now
- https://soulfra.github.io/stpetepros/

### New Features

**1. Site-Wide Keyboard Shortcuts**
- `H` - Home/Directory
- `S` - Signup page
- `L` - Login (opens Flask backend if running)
- `?` - Show keyboard shortcuts help
- `Escape` - Go back
- `←/→` - Navigate between professionals (on profile pages)
- `1-9` - Jump to professional # (on profile pages)
- `0` - Back to directory (on profile pages)

**2. Auth Bridge (Static ↔ Flask)**
- Static pages check if you're logged in to Flask
- Shows user badge in top-right if logged in
- Dynamic features appear based on login status

**3. Local Testing Setup**
- Flask serves StPetePros at http://localhost:5001/stpetepros/
- Full auth integration works locally
- Optional: Use custom domains (stpetepros.local)

---

## 🧪 Testing Locally

### Quick Test (No Setup Required)

1. **Start Flask:**
   ```bash
   cd ~/Desktop/roommate-chat/soulfra-simple
   python3 app.py
   ```

2. **Open StPetePros:**
   - http://localhost:5001/stpetepros/

3. **Test Keyboard Nav:**
   - Press `?` to see all shortcuts
   - Press `H` to go home
   - Press `S` to go to signup
   - Navigate with arrows on professional pages

4. **Test Auth Bridge:**
   - Press `L` - should show "Login not available" modal (static mode)
   - Login to Flask first: http://localhost:5001/login
   - Then refresh StPetePros page
   - You should see user badge in top-right corner

---

## 🌐 Advanced: Custom Domains (Optional)

### Setup

1. **Run setup script:**
   ```bash
   cd ~/Desktop/roommate-chat/soulfra-simple
   ./setup-local-domains.sh
   ```
   This adds entries to `/etc/hosts`:
   - `127.0.0.1 stpetepros.local`
   - `127.0.0.1 soulfra.local`
   - `127.0.0.1 cringeproof.local`

2. **Start Flask:**
   ```bash
   python3 app.py
   ```

3. **Access via custom domains:**
   - http://stpetepros.local:5001/stpetepros/
   - http://soulfra.local:5001/
   - http://cringeproof.local:5001/

### Why Use Custom Domains?

- **Realistic testing:** Mimics production domain structure
- **CORS testing:** Test cross-domain auth
- **Session testing:** Cookies work properly across domains
- **Debug styling:** See how pages look with real domains

---

## 🔑 Testing Auth Flow (Full Stack)

### Scenario: User Signs Up → Gets Listed

**1. Static Page (GitHub Pages or Local)**
- User visits https://soulfra.github.io/stpetepros/
- Presses `S` to go to signup
- Sees $10 payment form

**2. Flask Backend (Your Laptop)**
- You receive email/Venmo payment
- Add professional to database:
  ```bash
  cd ~/Desktop/roommate-chat/soulfra-simple
  python3 csv-manager.py export  # Get CSV
  # Edit professionals.csv in Excel
  python3 csv-manager.py import professionals.csv
  ```

**3. Export to GitHub Pages**
- ```bash
  python3 export-to-github-pages.py
  cd ~/Desktop/soulfra.github.io
  git add stpetepros/
  git commit -m "Add new professional"
  git push
  ```

**4. Live in 30 Seconds**
- Professional appears at https://soulfra.github.io/stpetepros/
- Keyboard navigation automatically works
- If they log in (future), they see dashboard link

---

## 📊 Current Architecture

```
┌──────────────────────────────────────────┐
│  GitHub Pages (Static)                   │
│  - soulfra.github.io/stpetepros/         │
│  - Pure HTML/CSS/JS                      │
│  - Keyboard nav works                    │
│  - Auth-bridge checks Flask              │
└──────────────┬───────────────────────────┘
               │
               │ AJAX: /api/auth/check
               ↓
┌──────────────────────────────────────────┐
│  Flask Backend (Your Laptop)             │
│  - localhost:5001                        │
│  - Serves /stpetepros/ (local testing)   │
│  - /api/auth/check (login detection)     │
│  - Database (soulfra.db)                 │
│  - QR login, user accounts               │
└──────────────────────────────────────────┘
```

**Key Points:**
- **Static pages work standalone** (no Flask needed for users)
- **Auth bridge adds dynamic features** (when Flask is running)
- **Local testing gets full integration** (Flask serves static files)
- **GitHub Pages gets keyboard nav only** (until you deploy Flask publicly)

---

## 🎯 What to Test

### Keyboard Navigation
- [ ] Press `?` anywhere - help modal appears
- [ ] Press `H` from any page - goes to index
- [ ] Press `S` from any page - goes to signup
- [ ] Press `L` from any page - shows login prompt
- [ ] Press `Escape` - modal closes OR goes back
- [ ] On professional page: `←/→` navigates between pros
- [ ] On professional page: `1-9` jumps to specific pro
- [ ] On professional page: `0` returns to directory

### Auth Bridge (Local Only)
- [ ] Start Flask, visit http://localhost:5001/stpetepros/
- [ ] Login at http://localhost:5001/login
- [ ] Refresh StPetePros page
- [ ] User badge appears in top-right
- [ ] Badge shows username + tier
- [ ] Dashboard link works

### Static Mode (GitHub Pages)
- [ ] Visit https://soulfra.github.io/stpetepros/
- [ ] Keyboard shortcuts work
- [ ] Press `L` - shows "static demo" message
- [ ] No errors in browser console
- [ ] Navigation hint appears on first visit

---

## 🐛 Debugging

### Keyboard Shortcuts Don't Work
- **Check:** Browser console for errors
- **Check:** Scripts loaded (view page source, look for `global-nav.js`)
- **Fix:** Hard refresh (Cmd+Shift+R)

### Auth Bridge Not Working
- **Check:** Flask running at http://localhost:5001
- **Check:** CORS enabled in Flask (already configured)
- **Check:** Browser console for AJAX errors
- **Fix:** Login to Flask first, then refresh StPetePros

### Local Domains Not Working
- **Check:** Ran `./setup-local-domains.sh`
- **Check:** `/etc/hosts` has entries (run `cat /etc/hosts | grep stpetepros`)
- **Fix:** Re-run setup script with sudo password

---

## 🚀 Next Steps

### Now (Local Testing Working)
- ✅ Keyboard nav works everywhere
- ✅ Auth bridge detects Flask login
- ✅ Local testing at localhost:5001/stpetepros/

### Soon (Deploy Flask Publicly)
1. Deploy Flask to Railway/Render/VPS
2. Update `auth-bridge.js` FLASK_API URL
3. Point soulfra.com to Flask backend
4. Users can login + see personalized features

### Future (Full Platform)
1. User dashboard (saved favorites, AI agent)
2. Professional dashboard (edit listing, stats)
3. Payment integration (Stripe for $10 signup)
4. Voice memos → auto-generate content

---

## 💡 Tips

- **Use keyboard shortcuts everywhere** - Way faster than clicking
- **Press `?` anytime** - You'll forget shortcuts, modal reminds you
- **Test in incognito** - Sees what users see (no login)
- **Test with Flask running** - Sees full auth experience
- **Check browser console** - Errors will show there first

---

Built with voice memos, Ollama, Whisper, and Claude Code.

**Questions?** Press `?` on any page to see keyboard shortcuts!
