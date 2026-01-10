# GitHub Profile README Integration

**Transform your voice recordings into a live, auto-updating GitHub profile**

---

## ✨ What We Built

### 1. **Dynamic README Generator** (`readme_generator.py`)

Generates GitHub-compatible markdown from your voice recordings:

**Endpoints:**
- `GET /api/readme/<slug>` - Raw markdown for README.md
- `GET /api/readme/<slug>/preview` - HTML preview with GitHub styling
- `GET /api/readme/<slug>/json` - Structured JSON data

**Features:**
- 🎙️ Latest 5 voice memos with timestamps
- 🥇 Top 10 words from wordmap with emoji rank indicators
- 📊 Live stats badges (recordings count, ideas count)
- 🔗 QR code badge for profile
- ⏰ Auto-timestamp of last update

**Example Output:**
```markdown
# matt

Voice-powered thinking. No cringe, just authenticity.

## 📊 My Wordmap

- 🥇 **about** (8 times)
- 🥈 **news** (8 times)
- 🥉 **hello** (2 times)
- ▰▰▱ **ideas** (5 times)
- ▱▱▱ **talk** (1 times)
```

---

### 2. **SVG Badge Generator** (`badge_routes.py`)

Dynamic SVG images that work in GitHub markdown:

**Badges:**
- `/badge/<slug>/qr.svg` - Scannable QR code with gradient background
- `/badge/<slug>/qr.png` - Downloadable PNG QR code
- `/badge/<slug>/wordmap.svg` - Word cloud visualization
- `/badge/<slug>/activity.svg` - Activity status indicator (animated)
- `/badge/<slug>/stats.svg` - Recording/ideas count display

**Features:**
- ✅ Real QR codes (using `qrcode` library, not placeholders)
- 🎨 Color gradients (teal → purple spectrum)
- 📏 Font sizes scale with word frequency
- ⚡ Animated activity status dots

**Usage in README:**
```markdown
![QR Code](https://api.cringeproof.com/badge/matt/qr.svg)
![Wordmap](https://api.cringeproof.com/badge/matt/wordmap.svg)
```

---

### 3. **Terminal CLI Tool** (`readme_cli.py`)

Command-line interface for README management:

**Commands:**
```bash
./readme_cli.py generate matt       # Generate README markdown
./readme_cli.py preview matt        # Preview with colors in terminal
./readme_cli.py push matt           # Push to GitHub repo
./readme_cli.py stats matt          # Show profile statistics
./readme_cli.py qr matt             # Display QR code in terminal
./readme_cli.py watch               # Auto-regenerate on changes
```

**Features:**
- 🎨 Rich terminal formatting (using `rich` library)
- 📊 Colored tables for stats
- 📱 Terminal-rendered QR codes
- 🔄 Watch mode for auto-updates
- 💾 Auto-save to README.md

**Installation:**
```bash
chmod +x readme_cli.py
pip install rich qrcode colorama
./readme_cli.py preview matt
```

---

### 4. **Embeddable Widgets** (`embed_routes.py`)

Iframe-embeddable components for any website:

**Widgets:**
- `/embed/<slug>/wordmap` - Interactive word cloud widget
- `/embed/<slug>/activity` - Live activity feed
- `/embed/<slug>/profile` - Glassmorphic profile card
- `/embed/<slug>/preview` - Full README preview

**Usage:**
```html
<!-- Wordmap Widget -->
<iframe src="https://api.cringeproof.com/embed/matt/wordmap"
        width="600" height="300" frameborder="0"></iframe>

<!-- Activity Feed -->
<iframe src="https://api.cringeproof.com/embed/matt/activity"
        width="400" height="500" frameborder="0"></iframe>

<!-- Profile Card -->
<iframe src="https://api.cringeproof.com/embed/matt/profile"
        width="350" height="200" frameborder="0"></iframe>
```

**Features:**
- 🎨 Glassmorphism design (backdrop blur effects)
- 🌈 Gradient backgrounds
- ⚡ Smooth hover animations
- 📱 Responsive layouts
- 🔗 Auto-linking to full profile

---

### 5. **GitHub Actions Workflow** (`.github/workflows/update-readme.yml`)

Automatic hourly README updates via GitHub Actions:

**Triggers:**
- ⏰ Every hour (cron: `0 * * * *`)
- 🔄 Manual trigger (workflow_dispatch)
- 📝 On code push (paths: `soulfra.db`, `**.py`)

**Workflow:**
```yaml
1. Checkout repository
2. Set up Python 3.11
3. Fetch README from API: /api/readme/${SLUG}
4. Auto-commit if changed
```

**Setup:**
```bash
# Add GitHub secrets:
# - USER_SLUG: 'matt'
# - API_URL: 'https://api.cringeproof.com'
```

---

## 🚀 How to Use

### For Your GitHub Profile (github.com/yourusername/yourusername)

1. **Create a profile repository:**
   ```bash
   mkdir yourusername
   cd yourusername
   git init
   ```

2. **Generate initial README:**
   ```bash
   ./readme_cli.py generate yourusername > README.md
   git add README.md
   git commit -m "🎙️ Initial voice-powered README"
   git push
   ```

3. **Add GitHub Actions workflow:**
   ```bash
   mkdir -p .github/workflows
   cp .github/workflows/update-readme.yml .github/workflows/
   git add .github/workflows/update-readme.yml
   git commit -m "⚡ Add auto-update workflow"
   git push
   ```

4. **Set GitHub secrets:**
   - Go to repository Settings → Secrets → Actions
   - Add `USER_SLUG` = your slug (e.g., "matt")
   - Add `API_URL` = https://api.cringeproof.com

5. **Done!** Your README will auto-update every hour from your voice recordings.

---

## 🎨 Customization

### Change Wordmap Colors

Edit `badge_routes.py`:
```python
colors = ['#00C49A', '#00D4AA', '#00E4BA', '#667eea', '#764ba2']
```

### Change Emoji Indicators

Edit `readme_generator.py`:
```python
if i == 0:
    emoji = "🥇"  # Change gold medal
elif i == 1:
    emoji = "🥈"  # Change silver medal
# ...
```

### Change QR Code Style

Edit `badge_routes.py`:
```python
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
img = qr.make_image(fill_color="#667eea", back_color="white")  # Custom colors
```

---

## 📦 Dependencies

```bash
pip install flask qrcode pillow rich colorama
```

**Libraries Used:**
- `qrcode` - Real QR code generation (not placeholders!)
- `rich` - Beautiful terminal formatting
- `flask` - Web framework for routes
- `pillow` - Image processing for QR codes

---

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Voice Recording (soulfra.com/voice)                        │
│  ↓                                                           │
│  Database (simple_voice_recordings, user_wordmaps)          │
│  ↓                                                           │
│  README Generator (readme_generator.py)                     │
│  ↓                                                           │
│  GitHub Actions (fetches /api/readme/<slug>)                │
│  ↓                                                           │
│  Auto-commit to GitHub                                      │
│  ↓                                                           │
│  Live Profile (github.com/<user>/<user>)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Next Steps

### Still TODO:
- [ ] OpenAPI spec generation for API documentation
- [ ] API key generation system (`/api/keys/generate`)
- [ ] Static component library (`.js` widgets for direct embedding)
- [ ] NPM package for easy installation
- [ ] Sentiment analysis for emoji indicators (😊 positive, 😐 neutral, 😞 negative)
- [ ] Real-time webhook triggers (update README instantly on new recording)

### Already Done:
- [x] Dynamic README generator with voice recordings
- [x] Real QR code generation (SVG + PNG)
- [x] Enhanced wordmap with emoji rank indicators
- [x] Terminal CLI tool with rich formatting
- [x] Embeddable iframe widgets (wordmap, activity, profile)
- [x] SVG badge generators with gradients
- [x] GitHub Actions workflow for auto-updates

---

## 💡 Cool Use Cases

1. **Developer Portfolio**: Show your latest thoughts/ideas on your GitHub profile
2. **Podcast Host**: Display recent episode topics as wordmap
3. **Content Creator**: Auto-update profile with latest content themes
4. **Startup Founder**: Share company vision through voice memos
5. **Teacher/Educator**: Showcase lesson topics and student feedback

---

## 🤝 Contributing

The system is modular and extensible:

- **Add new badges**: Create routes in `badge_routes.py`
- **Add new widgets**: Create routes in `embed_routes.py`
- **Customize README**: Modify `readme_generator.py`
- **Add CLI commands**: Extend `readme_cli.py`

---

## 📄 License

MIT License - Use freely for your GitHub profiles!

---

**Built with ❤️ using voice-powered thinking. No cringe, just authenticity.**

🔗 [cringeproof.com](https://cringeproof.com) | 🎙️ [Record Voice Memo](https://cringeproof.com/voice)
