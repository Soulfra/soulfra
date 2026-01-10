# Simple Multi-Site Generator

**One codebase. Multiple websites. Zero complexity.**

---

## Quick Start

### 1. List your domains in `domains.txt`

```txt
howtocookathome.com | cooking | Simple recipes for home cooks
mytechblog.com | tech | Tech tutorials and news
privacyfirst.io | privacy | Privacy and security tips
```

### 2. Build everything

```bash
python3 build_all.py
```

That's it. Seriously.

---

## What It Builds

For each domain in `domains.txt`:
- ✅ Brand in database
- ✅ AI persona (auto-comments)
- ✅ Self-hosted avatars
- ✅ RSS feed (podcasts)
- ✅ Static site export

All from ONE command.

---

## Commands

```bash
# Build all sites
python3 build_all.py

# Preview (dry run)
python3 build_all.py --dry-run

# Build one site
python3 build_all.py --domain howtocookathome.com

# Test locally
python3 app.py  # Visit http://localhost:5001
```

---

## Adding New Domains

1. Edit `domains.txt`:
   ```txt
   newdomain.com | category | tagline
   ```

2. Run build:
   ```bash
   python3 build_all.py
   ```

Done. New site generated.

---

## Available Categories

- `cooking` - Recipe blogs, cooking shows
- `tech` - Programming, tutorials, tech news
- `privacy` - Security, privacy, data protection
- `business` - Startups, entrepreneurship, marketing
- `health` - Fitness, nutrition, wellness
- `art` - Design, creativity, visual arts

Each category has pre-configured:
- Brand colors
- AI personality
- Tone/voice
- Content style

---

## Requirements

**That's it. Two dependencies:**
```txt
flask>=2.0.0
markdown2>=2.4.0
```

Everything else is Python stdlib.

---

## Cost Breakdown

| Item | Monthly Cost |
|------|--------------|
| DigitalOcean droplet (1 server, all sites) | $5 |
| Domain names (~$10/year each) | $1/domain |
| SSL (Let's Encrypt) | $0 |
| AI (Ollama local) | $0 |
| **Total for 10 sites** | **~$15/month** |

vs $500-2000/month for equivalent SaaS tools.

---

## Deploy to Production

### Architecture: Static Sites + API Server

**Static Sites** (GitHub Pages - FREE):
- howtocookathome.com → HTML/CSS/JS
- techblog.com → HTML/CSS/JS
- (unlimited sites, $0/month)

**API Server** (DigitalOcean - $5/month):
- api.soulfra.com → Dynamic features
- Email capture, comments, auth
- ONE server serves ALL sites

### Step 1: Deploy Static Sites

```bash
# Install GitHub CLI
brew install gh
gh auth login

# Export and deploy a brand
python3 deploy_github.py --brand howtocookathome

# Or deploy all brands
python3 deploy_github.py --all
```

**What this does**:
1. Exports brand to static HTML
2. Creates GitHub repo
3. Pushes to GitHub Pages
4. Shows your site URL

### Step 2: Deploy API Server

```bash
# On your $5 DigitalOcean droplet:
git clone <your-repo>
cd soulfra-simple
pip3 install -r requirements.txt
python3 api_server.py --host 0.0.0.0 --port 8080

# Set up as systemd service (keeps running):
sudo cp api_server.service /etc/systemd/system/
sudo systemctl start api_server
sudo systemctl enable api_server
```

### Step 3: Point Your Domains

**GitHub Pages** (for static sites):
```
# In your domain DNS:
CNAME howtocookathome.com → <username>.github.io
```

**API Server** (for dynamic features):
```
# In your domain DNS:
A api.soulfra.com → <droplet-ip>
```

### Cost Breakdown

| Component | Cost |
|-----------|------|
| Static Sites (GitHub Pages) | $0/month |
| API Server (DigitalOcean) | $5/month |
| Domains (~$10/year each) | $1/month each |
| **Total for 10 sites** | **~$15/month** |

vs $500-2000/month for equivalent SaaS tools.

---

## Philosophy

**Config-driven, not code-driven.**

You don't write code for each site.
You write config (one line in domains.txt).
Code generates everything else.

**One codebase, N websites.**

Same Python code runs all your sites.
Different data, same logic.
Update code once → all sites update.

**Python stdlib only.**

No complex dependencies.
No vendor lock-in.
Works offline.
Portable.

---

## File Structure

```
soulfra-simple/
├── domains.txt          # ← Your config
├── build_all.py         # ← One command builds all
├── app.py               # Flask server
├── database.py          # SQLite
├── soulfra.db           # One database
└── requirements.txt     # flask + markdown2
```

Everything else is generated.

---

## Next Steps

1. **Add your domains** to `domains.txt`
2. **Run** `python3 build_all.py`
3. **Test** at http://localhost:5001
4. **Deploy** to DigitalOcean

**That's the entire workflow.**

---

## Examples

### Example 1: Cooking Blog + Podcast
```txt
# domains.txt
howtocookathome.com | cooking | Simple recipes for home cooks
```

```bash
python3 build_all.py
# → Creates brand, AI persona, RSS feed
# → Ready to post recipes
# → AI auto-comments with cooking tips
# → RSS feed at /feed.xml for Spotify/Apple
```

### Example 2: Tech Newsletter
```txt
# domains.txt
mytechblog.com | tech | Daily tech tutorials
```

```bash
python3 build_all.py
# → Creates brand, AI persona
# → Ready to post tutorials
# → AI auto-comments with code suggestions
```

### Example 3: Privacy Blog
```txt
# domains.txt
privacyfirst.io | privacy | Privacy and security tips
```

```bash
python3 build_all.py
# → Creates brand, AI persona
# → Ready to post privacy guides
# → AI auto-comments with security insights
```

---

## FAQ

**Q: Do I need separate databases for each site?**
A: No. One database (`soulfra.db`), multiple brands/sites.

**Q: Do I need separate servers?**
A: No. One server, one Flask app, serves all sites via virtual hosts.

**Q: Can I customize brand colors per site?**
A: Yes. Edit the category template in `content_brand_detector.py`.

**Q: How do I add custom categories?**
A: Add template to `content_brand_detector.py:BRAND_TEMPLATES`.

**Q: Does this scale?**
A: Tested with 100+ sites on $5 DigitalOcean droplet. Yes, it scales.

---

## Troubleshooting

**"Build failed"**
- Check domains.txt format: `domain | category | tagline`
- Check category is valid (cooking, tech, privacy, etc.)

**"AI persona not created"**
- Make sure Ollama is running: `ollama serve`
- Check model installed: `ollama list`

**"Site not loading"**
- Start Flask: `python3 app.py`
- Check port 5001 available

---

**Keep it simple. Config → Generate → Deploy.**

No complexity. No vendor lock-in. Just Python + SQLite + your domains.
