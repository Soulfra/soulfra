# Content Pipeline - How Everything Connects

**Your complete guide to how README → soulfra.com works**

---

## The Big Picture

```
README.md (source of truth)
    ↓
scripts/build-site.py (convert to HTML)
    ↓
dist/index.html (deployable website)
    ↓
soulfra.com (live site)
    ↑
Merkle proofs + Privacy filters applied
```

---

## What You Asked About

### "How do I put artifacts in here so we can see how this works?"

**Answer:** Add images/demos to `/assets/` folder, reference in README.md

**Example:**
```bash
# 1. Add screenshot
cp mobile-screenshot.png assets/screenshots/

# 2. Reference in README
echo '![Mobile Interface](assets/screenshots/mobile-screenshot.png)' >> README.md

# 3. Build site
cd scripts && python3 build-site.py

# 4. Deploy
cp -r ../dist/* /path/to/soulfra.com-repo/
```

---

### "Printing like at the bottom of a printer or PDF... bleed lines or margins... watermarking"

**Answer:** Cryptographic watermarking using merkle tree proofs

**How it works:**

1. **Generate hash of file** (SHA-256)
   ```bash
   python3 scripts/hash-asset.py assets/audio/sample.webm
   ```

2. **Creates proof file** (`sample.webm.hash`)
   ```json
   {
     "file": "assets/audio/sample.webm",
     "sha256": "abc123...",
     "timestamp": "2026-01-04T19:30:00Z",
     "merkle_root": "def456...",
     "git_commit": "7b11fc3"
   }
   ```

3. **Merkle root published in README footer**
   - Anyone can verify file authenticity
   - Can't fake timestamps (git commit proves it)
   - Like a "watermark" but cryptographic

**Real-world example:**
- You record voice memo on iPhone
- Upload → generates SHA-256 hash
- Hash added to merkle tree
- Root hash committed to git
- **Result:** Provable that you recorded this on X date, can't be backdated

---

### "Is the README the face of soulfra.com?"

**Currently:** No - they're separate

**After this setup:** Yes!

**How:**

```
github.com/Soulfra/soulfra
    ├── README.md (master content)
    ├── assets/ (media files)
    ├── scripts/build-site.py (converter)
    └── dist/index.html (generated output)
          ↓
    Copy to soulfra-site repo
          ↓
    Deploy to soulfra.com
```

**Workflow:**
1. Edit README.md (single source of truth)
2. Run `python3 scripts/build-site.py`
3. Push `dist/` to soulfra.com hosting
4. README content is now live at soulfra.com

---

### "Merkle tree or whitelist things but keep them obfuscated or private"

**Answer:** `scripts/whitelist.json` controls privacy levels

**4 Privacy Levels:**

1. **Public** - Full visibility
   ```json
   "public": {
     "files": ["assets/screenshots/mobile.png"]
   }
   ```

2. **Watermarked** - Visible but cryptographically signed
   ```json
   "watermarked": {
     "files": ["assets/audio/sample.webm"],
     "watermark_config": {
       "type": "metadata",
       "signature_key": "soulfra-2026"
     }
   }
   ```

3. **Obfuscated** - Blurred preview only
   ```json
   "obfuscated": {
     "files": ["assets/screenshots/private-ui.png"],
     "blur_radius": 10,
     "preview_quality": 30
   }
   ```

4. **Hash-only** - Content stays private, only hash published
   ```json
   "hash_only": {
     "files": ["assets/audio/personal-memo-001.webm"]
   }
   ```

**Example use case:**

You have 100 voice memos. You want to prove you recorded them (timestamps), but keep content private.

Solution:
- Add all 100 to `hash_only` in whitelist
- Build site generates merkle tree of all 100 hashes
- Publish merkle root to README
- **Public can see:** "Soulfra has 100 voice memos recorded between Jan-Mar 2026"
- **Public can't see:** Actual audio content
- **You can prove later:** "Here's memo #42 - hash matches merkle tree from Jan 15"

---

### "Lottie/dot files?"

**Answer:**

**Lottie** = JSON-based animations (like privacy obfuscation effects)
- Use for UI demos, animated watermarks
- Add to `assets/demos/privacy-blur.json`
- Embed in README with `<lottie-player>` tag

**Dotfiles** = Hidden configuration files (`.gitignore`, `.env`)
- Already using: `.gitignore` hides secrets
- Privacy dotfiles: `.soulfra-private/` folder (gitignored)
- Only you see private content, public sees hash proofs

---

## How to Deploy to Your "Online Laptop"

**Question:** "how does it go on my online laptop?"

**Answer:** Your "online laptop" = remote server or GitHub Pages

### Option 1: GitHub Pages (Free, Easy)

```bash
# 1. Build site
cd scripts && python3 build-site.py

# 2. Create soulfra-site repo (if not exists)
gh repo create soulfra/soulfra-site --public

# 3. Copy dist/ contents to repo
cp -r ../dist/* ~/Desktop/soulfra-site/

# 4. Push to GitHub
cd ~/Desktop/soulfra-site
git add .
git commit -m "Deploy README-based site"
git push

# 5. Enable GitHub Pages
# Go to: Settings → Pages → Source: main branch

# 6. Point soulfra.com DNS
# In GoDaddy: CNAME → soulfra.com → soulfra.github.io
```

**Result:** soulfra.com now shows your README.md content!

### Option 2: VPS (Your Own Server)

```bash
# 1. Build site
python3 scripts/build-site.py

# 2. SCP to VPS
scp -r dist/* user@your-vps.com:/var/www/soulfra/

# 3. Configure nginx
# Point soulfra.com → /var/www/soulfra/
```

---

## Community & Organizations

**Question:** "how all the community and organizations and forums and shit work"

### GitHub Organizations

**@Soulfra** = Your organization (you already have this)

**Benefits:**
- Repos under organization name (not personal)
- Teams & permissions
- Unified branding

**Set up:**
1. Move repos to organization:
   ```bash
   # Transfer repo from personal to org
   gh repo edit Soulfra/voice-archive --org Soulfra
   ```

2. Create teams:
   - Core team (full access)
   - Contributors (write access)
   - Community (read access)

3. Enable Discussions:
   - Go to: Settings → Features → Discussions
   - Acts as built-in forum

### GitHub Discussions (Built-in Forum)

```
Soulfra/voice-archive → Discussions tab
    ├── Q&A
    ├── Ideas
    ├── Show and Tell
    └── General
```

**Enable:**
```bash
gh repo edit Soulfra/voice-archive --enable-discussions
```

---

## Complete Workflow Example

### Scenario: You record a voice memo on iPhone, want to publish with proof

**Step 1: Record on iPhone**
```
https://cringeproof.com/mobile.html
[Record voice memo]
→ Uploads to Flask backend
→ Saved as: recordings/memo-2026-01-04.webm
```

**Step 2: Add to soulfra/soulfra repo**
```bash
# Copy recording to assets
cp recordings/memo-2026-01-04.webm ~/Desktop/soulfra-profile/assets/audio/

# Generate cryptographic proof
cd ~/Desktop/soulfra-profile/scripts
python3 hash-asset.py ../assets/audio/memo-2026-01-04.webm

# Creates: assets/audio/memo-2026-01-04.webm.hash
```

**Step 3: Update whitelist**
```json
// scripts/whitelist.json
{
  "levels": {
    "watermarked": {
      "files": [
        "assets/audio/memo-2026-01-04.webm"
      ]
    }
  }
}
```

**Step 4: Reference in README**
```markdown
## Latest Voice Memo

<audio controls>
  <source src="assets/audio/memo-2026-01-04.webm" type="audio/webm">
</audio>

**Proof:** SHA-256: `abc123...` | Recorded: 2026-01-04 | [Verify](assets/audio/memo-2026-01-04.webm.hash)
```

**Step 5: Build & Deploy**
```bash
# Build site from README
python3 scripts/build-site.py

# Commit proof to git (immutable timestamp)
git add assets/ README.md
git commit -m "Add voice memo with cryptographic proof"
git push

# Deploy to soulfra.com
cp -r dist/* ~/Desktop/soulfra-site/
cd ~/Desktop/soulfra-site && git push
```

**Result:**
- Voice memo visible at soulfra.com
- Cryptographic proof in git history
- Anyone can verify: "This was recorded on 2026-01-04"
- Can't be backdated (git commit timestamp + merkle root)

---

## The Full Stack

```
┌─────────────────────────────────────────────────┐
│         Content Creation Layer                  │
├─────────────────────────────────────────────────┤
│  iPhone → mobile.html → Record voice memo       │
│  MacBook → Edit README.md                       │
│  GitHub → Commit changes                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          Privacy & Proof Layer                  │
├─────────────────────────────────────────────────┤
│  scripts/hash-asset.py → SHA-256 hashes         │
│  scripts/whitelist.json → Privacy levels        │
│  Merkle tree → Cryptographic proof              │
│  Git commits → Immutable timestamps             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           Build & Transform Layer               │
├─────────────────────────────────────────────────┤
│  scripts/build-site.py                          │
│    ├── README.md → HTML conversion              │
│    ├── Embed assets                             │
│    ├── Apply privacy filters                    │
│    └── Generate merkle proofs                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│            Deployment Layer                     │
├─────────────────────────────────────────────────┤
│  dist/index.html → Deployable HTML              │
│  GitHub Pages / VPS                             │
│  soulfra.com (live site)                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│             Verification Layer                  │
├─────────────────────────────────────────────────┤
│  Anyone can:                                    │
│    - Download .hash files                       │
│    - Verify SHA-256 matches                     │
│    - Check git commit timestamp                 │
│    - Validate merkle root                       │
│  = Provable authenticity                        │
└─────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Test the build system**
   ```bash
   cd ~/Desktop/soulfra-profile/scripts
   pip3 install markdown
   python3 build-site.py
   open ../dist/index.html
   ```

2. **Add your first artifact**
   - Take screenshot of mobile.html
   - Add to `assets/screenshots/`
   - Reference in README.md

3. **Deploy to GitHub Pages**
   - Create `soulfra-site` repo
   - Copy `dist/*` contents
   - Enable Pages in settings

4. **Point soulfra.com**
   - GoDaddy DNS: CNAME → soulfra.github.io
   - Wait 15 minutes for propagation

5. **Enable GitHub Discussions**
   ```bash
   gh repo edit Soulfra/soulfra --enable-discussions
   ```

---

**Questions? See REPO-MAP.md for troubleshooting.**
