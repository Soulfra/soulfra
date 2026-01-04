# Assets Directory

**Public artifacts for Soulfra projects**

This folder contains media and documentation that can be embedded in README files and deployed to websites.

---

## Structure

```
assets/
├── screenshots/     # UI screenshots (PNG/JPG)
├── demos/          # GIFs, videos, HTML demos
├── audio/          # Voice memo samples (watermarked)
└── docs/           # Additional documentation, diagrams
```

---

## Usage in README

### Screenshots

```markdown
![Mobile Voice Recording](assets/screenshots/mobile-recorder.png)
```

### Demos/GIFs

```markdown
![Accessibility Menu Demo](assets/demos/accessibility-menu.gif)
```

### Audio Samples

```markdown
<audio controls>
  <source src="assets/audio/sample-voice-memo.webm" type="audio/webm">
  Your browser does not support the audio element.
</audio>
```

---

## Privacy & Watermarking

### Public Assets
- Screenshots: Public UI demonstrations
- Demos: Functional walkthroughs
- Docs: Architecture diagrams

### Watermarked Assets
- Audio files: Include cryptographic signature in metadata
- Private demos: Blurred or obfuscated versions for public viewing

### Merkle Tree Proof
Each asset has a corresponding `.hash` file containing:
```json
{
  "file": "mobile-recorder.png",
  "sha256": "abc123...",
  "timestamp": "2026-01-04T19:00:00Z",
  "merkle_root": "def456...",
  "git_commit": "7b11fc3"
}
```

---

## Adding New Assets

1. **Add file to appropriate folder**
   ```bash
   cp screenshot.png assets/screenshots/
   ```

2. **Generate hash proof**
   ```bash
   python3 ../scripts/hash-asset.py assets/screenshots/screenshot.png
   ```

3. **Commit with proof**
   ```bash
   git add assets/
   git commit -m "Add screenshot with merkle proof"
   ```

4. **Reference in README**
   ```markdown
   ![Description](assets/screenshots/screenshot.png)
   ```

---

## File Size Limits

- Screenshots: Max 500KB (optimize with ImageOptim or similar)
- GIFs: Max 2MB (use MP4 or WebM for longer demos)
- Audio: Max 1MB per sample (use WebM Opus compression)

**Why?** Keep git repo size reasonable. Use external CDN for larger files.

---

## External CDN Option

For large files (videos > 10MB), use:
- GitHub Releases (versioned assets)
- Cloudflare R2 (your own CDN)
- Vimeo/YouTube (embedded videos)

Then link from README:
```markdown
[![Video Demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
```

---

## Cryptographic Proofs

All assets can be verified using:

```bash
# Verify hash
sha256sum assets/screenshots/mobile-recorder.png

# Check merkle root (proves this file is part of authenticated set)
python3 ../scripts/verify-merkle.py assets/screenshots/mobile-recorder.png
```

This proves:
1. File hasn't been tampered with
2. File existed at specific git commit timestamp
3. File is part of authenticated Soulfra content

---

## Privacy Levels

### Level 1: Public
- Full-resolution screenshots
- Complete demo videos
- Public documentation

### Level 2: Watermarked
- Blurred screenshots with visible watermark
- Audio with embedded signature
- Previews only (full version requires auth)

### Level 3: Private
- Not stored in this repo
- Hash-only reference (proves existence without revealing content)
- Requires private key to decrypt

**Example whitelist** (`../scripts/whitelist.json`):
```json
{
  "public": [
    "assets/screenshots/mobile-recorder.png",
    "assets/demos/accessibility-menu.gif"
  ],
  "watermarked": [
    "assets/audio/sample-voice-memo.webm"
  ],
  "private_hash_only": [
    "assets/audio/personal-memo-001.webm"
  ]
}
```

---

## Deployment

When deploying to soulfra.com:
1. Build script processes `assets/` folder
2. Checks whitelist for privacy level
3. Applies watermarks/obfuscation as needed
4. Generates merkle proofs
5. Deploys to CDN or GitHub Pages

See `../scripts/build-site.py` for implementation.
