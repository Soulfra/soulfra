# Soulfra Repository Map

**Quick reference: Which repo controls which URL?**

---

## GitHub Organizations & Accounts

- **@Soulfra** - Main GitHub organization
- **@CringeProof** - CringeProof brand GitHub organization

---

## Profile vs Website (The Confusion Explained)

### `github.com/Soulfra/soulfra` (Profile README Repo)
- **What it does:** Shows on your GitHub profile at `github.com/Soulfra`
- **What it shows:** "Building the non-typing internet" intro
- **How to edit:** Edit `~/Desktop/soulfra-profile/README.md` and push
- **NOT a website** - Just your profile page

### `github.com/Soulfra/soulfra.github.io` (GitHub Pages Site)
- **What it does:** Website at `soulfra.github.io`
- **What it shows:** Multi-brand showcase (CalRiven, DeathToData, etc.)
- **How to edit:** Edit HTML files in that repo
- **IS a website** - Live at https://soulfra.github.io

**They are completely separate!**

---

## Main Projects

### 1. voice-archive (OSS Component)

**Repo:** `github.com/Soulfra/voice-archive`

**What it is:**
- OSS voice recording system
- Anyone can fork and deploy
- Configuration via `.env.example`

**How to edit:**
```bash
cd ~/Desktop/roommate-chat/soulfra-simple/voice-archive
# Edit files
git add .
git commit -m "Update voice-archive"
git push
```

**Files:**
- `mobile.html` - Touch-optimized voice recording UI
- `mobile.js` - MediaRecorder + shadow accounts
- `router-config.js` - Backend auto-detection
- `shadow-account.js` - Browser fingerprinting
- `queue-manager.js` - Offline upload queue
- `DEPLOY.md` - Deployment guide
- `test-deployment.html` - Debug page

---

### 2. CringeProof (Production Site)

**Domain:** `cringeproof.com`

**DNS Setup:**
- Points to: GitHub Pages
- Repo: `github.com/CringeProof/cringeproof.github.io`

**Live URLs:**
- `cringeproof.com` - Main site
- `cringeproof.com/mobile.html` - Voice recording
- `cringeproof.com/test-deployment.html` - Debug tools

**How to deploy:**
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
./deploy-mobile-to-github.sh
```

**What this does:**
1. Clones `CringeProof/cringeproof.github.io` to `/tmp/cringeproof-deploy`
2. Copies mobile files from `voice-archive/`
3. Commits and pushes
4. GitHub Pages updates in 1-2 minutes

---

### 3. roommate-chat (Private Development Repo)

**Repo:** `github.com/Soulfra/roommate-chat` (private)

**Local path:** `~/Desktop/roommate-chat/soulfra-simple/`

**What it contains:**
- Flask backend (`app.py`)
- All development files
- voice-archive source code
- Test scripts
- Documentation (this file!)

**How Flask serves files:**
```python
# app.py line 19591-19594
@app.route('/mobile.html')
def serve_mobile():
    return send_from_directory('voice-archive', 'mobile.html')
```

**Local URLs (when Flask running):**
- `https://192.168.1.87:5001/mobile.html`
- `https://192.168.1.87:5001/voice-archive/mobile.html`
- `https://192.168.1.87:5001/test-deployment.html`

---

## URL Routing Explained

### Profile Page
```
github.com/Soulfra
  ↓
Shows: soulfra/soulfra/README.md
  ↓
"Building the non-typing internet"
```

### GitHub Pages Site
```
soulfra.github.io
  ↓
Repo: soulfra/soulfra.github.io
  ↓
HTML files in that repo
```

### CringeProof
```
cringeproof.com
  ↓
DNS → GitHub Pages
  ↓
Repo: CringeProof/cringeproof.github.io
  ↓
mobile.html deployed via ./deploy-mobile-to-github.sh
```

### Local Development
```
https://192.168.1.87:5001
  ↓
Flask server (app.py)
  ↓
Serves: voice-archive/mobile.html
```

---

## Editing Workflow

### To update your GitHub profile:
```bash
cd ~/Desktop/soulfra-profile
# Edit README.md
git add README.md
git commit -m "Update profile"
git push
# Visit github.com/Soulfra to see changes
```

### To update voice-archive (OSS repo):
```bash
cd ~/Desktop/roommate-chat/soulfra-simple/voice-archive
# Edit mobile.html, DEPLOY.md, etc.
git add .
git commit -m "Update voice-archive"
git push origin main
# Visit github.com/Soulfra/voice-archive to see changes
```

### To deploy to CringeProof.com:
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
./deploy-mobile-to-github.sh
# Wait 1-2 minutes
# Visit cringeproof.com/mobile.html
```

### To test locally:
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
python3 app.py
# Visit https://192.168.1.87:5001/mobile.html on iPhone
```

---

## Security: What NOT to Commit

**Sensitive files (already in .gitignore):**
- `.env` (contains API_BACKEND_URL)
- `*.pem` (SSL certificates)
- `*.key` (Private keys)
- `secrets/` (Credentials directory)
- `*.db` (SQLite databases with user data)

**Safe to commit:**
- `.env.example` (template with placeholders)
- `README.md` (documentation)
- `DEPLOY.md` (deployment guide)
- `mobile.html` (public frontend code)
- `router-config.js` (routing logic)

---

## SSH Authentication Setup

**Your SSH key:** `~/.ssh/id_ed25519`

**Add to agent (terminal):**
```bash
ssh-add ~/.ssh/id_ed25519
```

**Check it's loaded:**
```bash
ssh-add -l
```

**Now you can push without passwords:**
```bash
git push
# No password prompt!
```

---

## Common Questions

### "Which repo do I edit to change X?"

| What you want to change | Repo to edit | How to deploy |
|------------------------|--------------|---------------|
| GitHub profile intro | `soulfra/soulfra` | `git push` |
| soulfra.github.io site | `soulfra/soulfra.github.io` | `git push` |
| cringeproof.com mobile | `voice-archive/mobile.html` | `./deploy-mobile-to-github.sh` |
| OSS voice-archive docs | `voice-archive/DEPLOY.md` | `git push` |
| Local Flask routes | `app.py` | Restart Flask |

### "Why does editing soulfra/soulfra not change soulfra.github.io?"

They are **different repos**:
- `soulfra/soulfra` → Shows on `github.com/Soulfra` (profile page)
- `soulfra/soulfra.github.io` → Shows on `soulfra.github.io` (website)

### "How do I know if I'm going to leak secrets?"

**Before committing:**
```bash
# Check what files you're about to commit
git status

# Look for:
# ❌ .env (DON'T COMMIT)
# ❌ *.pem (DON'T COMMIT)
# ❌ *.key (DON'T COMMIT)
# ✅ .env.example (safe to commit)
# ✅ *.md (safe to commit)
# ✅ *.html (safe to commit)
```

**.gitignore protects you** - If a file is in `.gitignore`, git won't track it.

---

## Repository Cleanup Recommendations

You have **20 repos** under @Soulfra. Some are:
- `-site` repos (calriven-site, deathtodata-site, etc.) - Individual site repos
- Main repos (voice-archive, soulfra, calriven, etc.) - Core projects

**Options:**

1. **Keep as-is** - Each brand has its own repo (good for separation)
2. **Consolidate** - Merge `-site` repos into main repos (reduces clutter)
3. **Archive old ones** - Archive repos you're not using

**Recommendation:** Archive old repos you're not actively working on. Keep:
- `soulfra/soulfra` (profile README)
- `soulfra/voice-archive` (OSS component)
- `soulfra/soulfra.github.io` (showcase site)
- `Soulfra/roommate-chat` (private dev repo)

---

## Terminal Cheat Sheet

### Quick status check
```bash
# Where am I?
pwd

# Which repo is this?
git remote -v

# What changed?
git status
```

### Push workflow
```bash
# Stage files
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

### Deploy CringeProof
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
./deploy-mobile-to-github.sh
```

### Start Flask locally
```bash
cd ~/Desktop/roommate-chat/soulfra-simple
python3 app.py
# Visit https://192.168.1.87:5001/mobile.html
```

---

**Now you can edit from terminal and know exactly where things go!**
