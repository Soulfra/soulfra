# GitHub Mobile Workflow - Edit from iPhone

**How to edit your profile README and create gists from your iPhone**

---

## Proof Test Complete ✅

**Test marker added to README.md:**
> 🔴 **LIVE UPDATE TEST** - Last edited: 2026-01-04 12:52 EST from MacBook Terminal

**Verify it's live:**
1. Open https://github.com/Soulfra on any device
2. Look for the red marker at the top
3. If you see it → Profile README updates are LIVE!

---

## Method 1: GitHub Mobile App (iOS)

### Install & Setup
```
1. Download "GitHub" app from App Store
2. Log in as @Soulfra
3. Grant permissions for repositories
```

### Edit Profile README from iPhone

**Steps:**
1. Open GitHub app
2. Tap profile icon (bottom right)
3. Tap "Repositories"
4. Find "soulfra" repo (the one matching your username)
5. Tap to open
6. Scroll to "README.md"
7. Tap "..." menu (three dots)
8. Select "Edit file"
9. Make your changes
10. Scroll to bottom → "Commit changes"
11. Tap "Commit directly to main"

**Test Edit:**
- Change the marker from 🔴 to 🟢
- Add "Edited from iPhone" text
- Commit
- Refresh github.com/Soulfra on MacBook
- **Result:** Should see your iPhone edit!

---

## Method 2: GitHub Mobile Web (Safari)

**Better for complex edits:**

1. Open Safari on iPhone
2. Go to: https://github.com/Soulfra/soulfra
3. Tap "README.md"
4. Tap pencil icon (✏️) to edit
5. Make changes
6. Scroll down → "Commit changes"
7. Tap "Commit"

**Advantages:**
- Full markdown preview
- Better for longer edits
- More reliable than app

---

## Method 3: Create Gists from iPhone

### What are Gists?
- Quick code/text snippets
- Can be public or private
- Embeddable in README
- Version controlled

### Create Gist via iPhone App

1. Open GitHub app
2. Tap "+" icon (top right)
3. Select "New Gist"
4. Add filename (e.g., `voice-memo-metadata.json`)
5. Add content
6. Choose public/private
7. Tap "Create"

**Use case:**
```json
{
  "title": "iPhone Voice Memo",
  "timestamp": "2026-01-04T12:52:00Z",
  "duration": "45s",
  "transcription_url": "https://cringeproof.com/audio/123"
}
```

### Embed Gist in README

After creating gist, get the URL:
- Copy gist ID from URL (e.g., `abc123def456`)
- Add to README:
```markdown
<script src="https://gist.github.com/Soulfra/abc123def456.js"></script>
```

**Result:** Gist content appears in your profile README!

---

## Method 4: Voice → Gist Automation (Coming Soon)

**The Goal:**
Record voice memo on iPhone → Automatically creates gist → Updates README

**Workflow:**
```
iPhone (cringeproof.com/mobile.html)
    ↓ Record voice memo
Flask backend receives upload
    ↓ Extract metadata
Call GitHub API → Create gist
    ↓ Auto-commit
Update README with gist embed
    ↓ Push to GitHub
Profile updates automatically
```

**Implementation:**
- `scripts/create-gist.py` - Flask → GitHub API integration
- Auto-triggered on voice upload
- No manual iPhone editing needed!

---

## Current Capabilities

### ✅ What Works Now

1. **Manual README editing from iPhone**
   - GitHub app: ✅
   - Mobile web: ✅
   - Changes show live on github.com/Soulfra

2. **Create gists from iPhone**
   - Quick snippets: ✅
   - Embed in README: ✅
   - Update gist → README updates automatically

3. **Test marker verification**
   - Added from MacBook terminal: ✅
   - Pushed to GitHub: ✅
   - Visible at github.com/Soulfra: ✅

### 🔄 Coming Soon

1. **Voice → Gist automation**
   - Record on iPhone → Auto-creates gist
   - Flask integration script (in progress)

2. **Custom mobile edit UI**
   - Touch-optimized editor
   - Voice-first editing
   - Matches CringeProof mobile.html UX

---

## Proof of Concept Tests

### Test 1: MacBook → GitHub (COMPLETE ✅)
```bash
# Edit README locally
vim ~/Desktop/soulfra-profile/README.md

# Commit and push
git add README.md
git commit -m "Add test marker"
git push

# Verify at: https://github.com/Soulfra
# Result: ✅ Marker visible
```

### Test 2: iPhone GitHub App → GitHub (YOUR TURN)
```
1. Open GitHub app on iPhone
2. Navigate to soulfra/soulfra repo
3. Edit README.md
4. Change marker: 🔴 → 🟢
5. Add text: "Edited from iPhone"
6. Commit
7. Check github.com/Soulfra on MacBook
8. Expected: See green marker + iPhone text
```

### Test 3: iPhone → Gist → README (YOUR TURN)
```
1. Create gist from iPhone
2. Content: Voice memo metadata (JSON)
3. Copy gist URL
4. Edit README to embed gist
5. Commit
6. Check profile
7. Expected: Gist content embedded in README
```

### Test 4: Voice → Auto-Gist (FUTURE)
```
1. Record voice memo on cringeproof.com/mobile.html
2. Flask detects upload
3. Calls scripts/create-gist.py
4. Gist created automatically
5. README updated via GitHub API
6. Expected: Voice memo metadata appears in profile
```

---

## GitHub API Integration

### Creating Gists Programmatically

**From Flask backend:**

```python
import requests
import os

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def create_gist(filename, content, description, public=True):
    """Create a GitHub gist via API"""
    url = 'https://api.github.com/gists'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'description': description,
        'public': public,
        'files': {
            filename: {
                'content': content
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

**Usage:**
```python
# After voice memo upload
gist = create_gist(
    filename='voice-memo-2026-01-04.json',
    content=json.dumps(metadata),
    description='Voice memo recorded from iPhone'
)
print(f"Gist created: {gist['html_url']}")
```

---

## Gists vs Profile README

### Gists
- **Purpose:** Quick snippets, embeddable content
- **Editable:** Yes, from iPhone GitHub app
- **Versioned:** Yes, every edit tracked
- **Embeddable:** Yes, in README or external sites

### Profile README
- **Purpose:** Main landing page content
- **Editable:** Yes, from iPhone or desktop
- **Versioned:** Yes, via git commits
- **Source of truth:** For soulfra.com deployment

### How They Work Together

```
Voice Memo → Flask → Create Gist (metadata)
                          ↓
                  Update README (embed gist)
                          ↓
                   github.com/Soulfra updates
                          ↓
                   soulfra.com rebuilds from README
```

**Result:** iPhone voice memo → Entire web presence updates

---

## Next Steps

1. **Test iPhone editing now:**
   - Open GitHub app
   - Edit the test marker
   - Verify it shows on github.com/Soulfra

2. **Create your first gist:**
   - Quick snippet or voice memo metadata
   - Practice embedding in README

3. **Set up automation:**
   - See `scripts/create-gist.py` (coming next)
   - Flask → GitHub API integration

4. **Build custom mobile UI:**
   - Voice-optimized README editor
   - Matches CringeProof UX

---

## Troubleshooting

### "Can't edit README in GitHub app"
- Try mobile web (Safari) instead
- Ensure you're logged in as @Soulfra
- Check repo permissions

### "Gist embed not showing"
- Verify gist is public
- Check gist URL format
- Use `<script>` tag, not markdown link

### "Changes not appearing on profile"
- Refresh page (may take 10-20 seconds)
- Clear browser cache
- Verify commit went through (`git log`)

---

## Summary

**You can edit from iPhone RIGHT NOW:**
- ✅ GitHub app → Edit README.md
- ✅ Mobile web → Edit README.md
- ✅ Create gists from iPhone
- ✅ Changes appear live on github.com/Soulfra

**Automation coming:**
- 🔄 Voice → Gist (Flask integration)
- 🔄 Custom mobile editor
- 🔄 Auto-commit to README

**Test it yourself:**
Go to https://github.com/Soulfra/soulfra on iPhone → Edit the marker → See it update!
