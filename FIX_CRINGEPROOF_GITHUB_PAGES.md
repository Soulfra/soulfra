# Fix CringeProof.com → GitHub Pages Routing

## Current State

- **Domain**: cringeproof.com (where is it pointed?)
- **GitHub Repo**: soulfra.github.io (has CNAME pointing to soulfra.com)
- **CringeProof Code**: `/cringeproof-vertical/` (React app, running on npm start)
- **Problem**: cringeproof.com points to GitHub but no content displays

## Solution Options

### Option A: Quick Fix - Use Existing soulfra.github.io with Subdirectory

**Steps**:
1. Create `/soulfra.github.io/cringeproof/` subdirectory
2. Add simple `index.html` that redirects to React app
3. Point cringeproof.com CNAME to `soulfra.github.io/cringeproof`

**Pros**: Fast, uses existing infrastructure
**Cons**: cringeproof.com shows URL redirect

### Option B: Deploy CringeProof React App to GitHub Pages

**Steps**:
1. Build React app to static files
2. Push to `soulfra.github.io/cringeproof/` with all assets
3. Configure routing

**Pros**: Clean, proper deployment
**Cons**: Requires build process, static site only (no backend)

### Option C: Use Flask App + Cloudflared Tunnel (SIMPLEST)

**Steps**:
1. Keep Flask app running on localhost:5001
2. Start cloudflared tunnel: `cloudflared tunnel --url http://localhost:5001`
3. Point cringeproof.com DNS A/CNAME to tunnel URL
4. Flask app already handles cringeproof.com domain routing (you have this built)

**Pros**: Everything already works, supports backend/voice/QR
**Cons**: Requires keeping server running

## What You ACTUALLY Need

Based on "we need to loop it so the readme and raw content and whatever is displayed properly":

**You want GitHub to display README with:**
- Audio files (voice memos)
- GIFs/videos
- Raw content

**GitHub README CAN display:**
- ✅ Images (GIFs, PNGs, JPEGs)
- ✅ Embedded videos (via  HTML <video> tag or GitHub video upload)
- ❌ Audio (no native support - use SoundCloud/external embed)
- ✅ Raw markdown, code blocks
- ✅ Shields.io badges (dynamic stats)

**GitHub Pages CAN display:**
- ✅ Full HTML/CSS/JS
- ✅ Audio via <audio> tag
- ✅ Video via <video> tag
- ✅ GIFs, images
- ✅ Fetch data from external APIs

## Recommended Approach

**Use GitHub Pages + HTML (not just README)**

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.github.io

# Create cringeproof subdirectory
mkdir -p cringeproof

# Create index.html with audio/video/GIFs
cat > cringeproof/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
  <title>CringeProof - Time-Locked Predictions</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
    audio, video { width: 100%; max-width: 600px; }
    .prediction { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
  </style>
</head>
<body>
  <h1>CringeProof</h1>
  <p>Time-locked prediction market</p>

  <!-- Embedded audio (voice predictions) -->
  <div class="prediction">
    <h3>Latest Voice Prediction</h3>
    <audio controls>
      <source src="voice-predictions/latest.mp3" type="audio/mpeg">
    </audio>
  </div>

  <!-- Embedded video -->
  <div class="prediction">
    <h3>Prediction Demo</h3>
    <video controls>
      <source src="videos/demo.mp4" type="video/mp4">
    </video>
  </div>

  <!-- Dynamic content from API -->
  <div id="live-feed"></div>

  <script>
    // Fetch live predictions from Flask API
    fetch('https://observation-mobility-realized-casa.trycloudflare.com/api/predictions')
      .then(r => r.json())
      .then(data => {
        document.getElementById('live-feed').innerHTML =
          data.map(p => `<div class="prediction">${p.text}</div>`).join('');
      });
  </script>
</body>
</html>
EOF

# Add CNAME for cringeproof.com
echo "cringeproof.com" > cringeproof/CNAME

# Commit and push
git add cringeproof/
git commit -m "Add CringeProof GitHub Pages site with audio/video support"
git push
```

Then in your domain registrar:
```
Type: CNAME
Name: cringeproof.com
Value: soulfra.github.io
```

## Test It

1. Visit https://soulfra.github.io/cringeproof/
2. Should see HTML page with audio/video
3. Wait for DNS propagation (~1 hour)
4. Visit https://cringeproof.com
5. Should show same content

## If You Want README with Media

GitHub README limitations:
- Can't embed <audio> tags
- Can embed GIFs (upload to repo or use URL)
- Can embed videos (GitHub supports .mp4 upload in markdown)

Example README with media:
```markdown
# CringeProof

## Latest Prediction

![Demo GIF](https://media.giphy.com/media/prediction-demo.gif)

## How It Works

https://github.com/user-attachments/assets/demo-video.mp4

(Upload video via GitHub web UI, paste URL)

## Live Stats

![Predictions](https://img.shields.io/badge/dynamic/json?url=https://soulfra.com/api/stats&label=predictions&query=$.count)
```

## Next Steps

**Pick one**:
1. [ ] Deploy HTML to soulfra.github.io/cringeproof/ (full audio/video support)
2. [ ] Update README.md with GIFs and uploaded videos (limited media)
3. [ ] Use cloudflared tunnel + Flask app (dynamic backend)

Let me know which you want and I'll implement it.
