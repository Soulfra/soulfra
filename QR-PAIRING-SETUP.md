# QR Pairing Setup - iPhone → GitHub Profile README

**Complete guide to enable QR code pairing for voice memo contributions**

---

## Overview

This enables a Discord-style QR login flow where:
1. User scans QR code on your GitHub profile
2. iPhone opens pairing page
3. User connects their GitHub account (OAuth)
4. User records voice memos
5. Voice memos automatically create gists and update your README

**Think of it like Instagram/Snapchat stories, but for GitHub profiles!**

---

## Step 1: Create GitHub OAuth App

### 1.1 Navigate to OAuth Settings

Go to: https://github.com/settings/developers

Click: **"New OAuth App"**

### 1.2 Configure OAuth App

Fill in the following:

```
Application name: Soulfra iPhone Pairing
Homepage URL: https://cringeproof.com
Authorization callback URL: https://cringeproof.com/oauth/callback
```

**Important:** The callback URL must match exactly what you configure in your Flask app.

### 1.3 Save Credentials

After creating the app, you'll see:
- **Client ID** (e.g., `Iv1.a1b2c3d4e5f6g7h8`)
- **Client Secret** (generate one if not shown)

**Copy these!** You'll need them for environment variables.

---

## Step 2: Configure Environment Variables

### 2.1 Create `.env` File

In your project root (`soulfra-profile/`):

```bash
cd ~/Desktop/soulfra-profile
touch .env
```

### 2.2 Add OAuth Credentials

Edit `.env`:

```bash
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
GITHUB_CLIENT_SECRET=your_secret_here_xxxxxxxxxx
GITHUB_REDIRECT_URI=https://cringeproof.com/oauth/callback

# GitHub API Token (for backend gist creation)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=Soulfra

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_for_sessions
```

### 2.3 Verify `.gitignore`

Make sure `.env` is in `.gitignore` (already added):

```bash
grep ".env" .gitignore
```

Should output: `.env`

---

## Step 3: Integrate OAuth Routes into Flask

### 3.1 Update Flask App

In your Flask app (e.g., `app.py` in CringeProof backend):

```python
from flask import Flask, session
from scripts.github_oauth import init_oauth_routes

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Required for sessions

# Initialize OAuth routes
init_oauth_routes(app)

# Your existing routes...
@app.route('/mobile.html')
def mobile():
    return render_template('mobile.html')

@app.route('/api/upload', methods=['POST'])
def upload_voice_memo():
    # Handle voice memo upload
    # Now can use OAuth token from session!
    from scripts.github_oauth import is_paired, create_gist_for_user

    if is_paired():
        # User is authenticated via OAuth
        gist = create_gist_for_user(
            filename='voice-memo.json',
            content=json.dumps(metadata),
            description='Voice memo from iPhone'
        )
        return jsonify({'gist_url': gist['html_url']})
    else:
        return jsonify({'error': 'Not paired'}), 401
```

### 3.2 Install Dependencies

```bash
pip3 install Flask requests qrcode[pil]
```

---

## Step 4: Deploy Backend with OAuth Routes

### Option 1: Local Testing (Localhost)

For local testing, use ngrok or cloudflared tunnel:

```bash
# Terminal 1: Run Flask
cd ~/Desktop/soulfra-profile
export FLASK_APP=app.py
flask run --port=5001

# Terminal 2: Create tunnel
cloudflared tunnel --url https://localhost:5001
```

Copy the public URL (e.g., `https://abc123.trycloudflare.com`) and update:
- GitHub OAuth callback: `https://abc123.trycloudflare.com/oauth/callback`
- `.env` GITHUB_REDIRECT_URI

### Option 2: Production (cringeproof.com)

Deploy Flask app to production server with OAuth routes enabled.

**HTTPS required!** OAuth won't work over HTTP.

---

## Step 5: Test the QR Pairing Flow

### 5.1 Generate QR Code

Already done! QR code is in README.md:

```bash
# View QR code
open assets/qr-pair.svg

# Or regenerate if needed
cd scripts
python3 generate-qr-widget.py --url "https://cringeproof.com/pair"
```

### 5.2 Test Pairing on iPhone

1. **Open GitHub profile on desktop:**
   Visit: https://github.com/Soulfra

2. **Scan QR code with iPhone:**
   - Open Camera app
   - Point at QR code
   - Tap notification

3. **Should open:** `https://cringeproof.com/pair`

4. **Click "Connect GitHub"**

5. **Authorize permissions**
   - GitHub will ask to authorize the app
   - Scopes requested: `gist, repo`

6. **Success!**
   - Redirects to `/pair/success`
   - Shows: "Paired Successfully!"
   - Auto-redirects to voice recorder

7. **Record voice memo**
   - Voice memo uploads
   - Backend creates gist using your OAuth token
   - Gist added to story wall in README

---

## Step 6: Voice Memo → Story Wall Workflow

### 6.1 Flask Upload Handler

Update your voice memo upload handler:

```python
from scripts.create_gist import create_story_from_voice_memo

@app.route('/api/upload', methods=['POST'])
def upload_voice_memo():
    audio_file = request.files['audio']
    metadata = request.form.get('metadata')

    # Save audio file
    audio_path = f"uploads/{audio_file.filename}"
    audio_file.save(audio_path)

    # Create voice memo data
    voice_memo_data = {
        'title': 'Voice Memo from iPhone',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'audio_file': audio_path,
        'metadata': json.loads(metadata) if metadata else {}
    }

    # Choose privacy level
    privacy_level = request.form.get('privacy', 'public')  # 'public' or 'private'

    # Create gist and add to story wall
    result = create_story_from_voice_memo(voice_memo_data, privacy_level=privacy_level)

    # Commit README changes
    os.system('cd ~/Desktop/soulfra-profile && git add README.md && git commit -m "Add voice memo to story wall" && git push')

    return jsonify(result)
```

### 6.2 Privacy Levels

Users can choose:

**Public Story:**
- Full gist embedded in README
- Content visible to everyone
- Appears in "Public Stories" section

**Private Story:**
- Hash-only proof in README
- Gist URL visible, content requires authentication
- Appears in "Private Stories" section

---

## Step 7: Auto-Update README via GitHub Actions (Optional)

Instead of manual commits, auto-push README changes:

### 7.1 Create GitHub Action

Create `.github/workflows/update-story-wall.yml`:

```yaml
name: Update Story Wall

on:
  repository_dispatch:
    types: [voice_memo_uploaded]

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Commit README changes
        run: |
          git config user.name "Soulfra Bot"
          git config user.email "noreply@soulfra.com"
          git add README.md
          git commit -m "Update story wall with new voice memo"
          git push
```

### 7.2 Trigger from Flask

```python
import requests

def trigger_readme_update():
    requests.post(
        'https://api.github.com/repos/Soulfra/soulfra/dispatches',
        headers={'Authorization': f'token {GITHUB_TOKEN}'},
        json={'event_type': 'voice_memo_uploaded'}
    )
```

---

## Troubleshooting

### Issue: "Invalid state parameter"

**Cause:** CSRF protection failed

**Fix:**
- Ensure Flask sessions are enabled (`app.secret_key` set)
- Don't block cookies in browser
- Use HTTPS (OAuth requires secure connections)

### Issue: "Failed to create gist: 401"

**Cause:** Invalid or expired GitHub token

**Fix:**
- Check `.env` has correct `GITHUB_CLIENT_SECRET`
- Re-authorize the OAuth app
- Generate new GitHub Personal Access Token if using `GITHUB_TOKEN`

### Issue: QR code doesn't scan

**Cause:** QR code not embedded correctly in README

**Fix:**
- Ensure `assets/qr-pair.svg` exists
- Check markdown syntax in README.md
- Regenerate QR code: `python3 scripts/generate-qr-widget.py`

### Issue: Callback URL mismatch

**Cause:** GitHub OAuth app callback doesn't match Flask route

**Fix:**
- GitHub OAuth app callback: `https://cringeproof.com/oauth/callback`
- `.env` GITHUB_REDIRECT_URI must match exactly
- No trailing slashes!

---

## Complete Workflow Diagram

```
┌────────────────────────────────────────────────────┐
│  GitHub Profile README (github.com/Soulfra)        │
│                                                    │
│  [QR Code: Scan to Pair iPhone]                   │
└────────────────────────────────────────────────────┘
                    ↓ Scan with iPhone Camera
┌────────────────────────────────────────────────────┐
│  Pairing Page (cringeproof.com/pair)               │
│                                                    │
│  [Connect GitHub Account] button                  │
└────────────────────────────────────────────────────┘
                    ↓ Click button
┌────────────────────────────────────────────────────┐
│  GitHub OAuth (github.com/login/oauth/authorize)   │
│                                                    │
│  Authorize Soulfra iPhone Pairing?                │
│  Permissions: Create gists, Update repos           │
│  [Authorize] button                                │
└────────────────────────────────────────────────────┘
                    ↓ User approves
┌────────────────────────────────────────────────────┐
│  Callback Handler (cringeproof.com/oauth/callback) │
│                                                    │
│  - Exchange code for access token                 │
│  - Store token in session                         │
│  - Redirect to success page                       │
└────────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────┐
│  Success Page (cringeproof.com/pair/success)       │
│                                                    │
│  ✅ Paired Successfully!                           │
│  [Start Recording] button                          │
└────────────────────────────────────────────────────┘
                    ↓ Auto-redirect after 3s
┌────────────────────────────────────────────────────┐
│  Voice Recorder (cringeproof.com/mobile.html)      │
│                                                    │
│  🎤 [Record Voice Memo]                           │
└────────────────────────────────────────────────────┘
                    ↓ Record & Upload
┌────────────────────────────────────────────────────┐
│  Flask Backend (cringeproof.com/api/upload)        │
│                                                    │
│  - Receive audio file                             │
│  - Create gist using OAuth token                  │
│  - Add to story wall in README                    │
│  - Commit & push to GitHub                        │
└────────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────┐
│  GitHub Profile README - Updated!                  │
│                                                    │
│  ## 📱 Story Wall                                  │
│                                                    │
│  ### Public Stories                                │
│  🎤 Voice Memo from iPhone - 2026-01-04           │
│  [Gist embedded here]                              │
│                                                    │
│  ### Private Stories                               │
│  🔒 Private thought - 2026-01-04                   │
│  Hash: abc123... [Verify proof]                    │
└────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Set up GitHub OAuth App** (Step 1)
2. **Configure `.env` file** (Step 2)
3. **Integrate OAuth routes into Flask** (Step 3)
4. **Deploy backend** (Step 4)
5. **Test QR pairing on iPhone** (Step 5)
6. **Record first voice memo!** 🎤

---

## Security Notes

- **Never commit `.env` file** - Contains secrets
- **Use HTTPS in production** - OAuth requires secure connections
- **Validate OAuth state** - Prevents CSRF attacks (already implemented)
- **Limit token scopes** - Only request `gist` and `repo` permissions
- **Rotate secrets regularly** - Regenerate client secret periodically

---

**Questions?** Open an issue at: https://github.com/Soulfra/soulfra/issues
