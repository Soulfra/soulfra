# Soulfra OSS - Deployment Guide

Complete guide to deploying and customizing your own Soulfra instance.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Theme Customization](#theme-customization)
3. [Deployment Options](#deployment-options)
4. [Reskin Examples](#reskin-examples)
5. [Domain Configuration](#domain-configuration)

---

## Quick Start

### One-Command Install

```bash
# Clone repository
git clone https://github.com/calriven/soulfra
cd soulfra

# Run installer
bash deploy/install.sh

# Start server
python3 app.py
```

Visit `http://localhost:5001`

---

## Theme Customization

### Edit Theme Config

```bash
# Edit theme settings
nano deploy/theme_config.yaml
```

### Theme Options

**Brand:**
```yaml
brand:
  name: "Your Brand"
  tagline: "Your Tagline"
  domain: "yourdomain.com"
```

**Colors:**
```yaml
colors:
  primary: "#4a90e2"    # Main brand color
  secondary: "#2c3e50"  # Secondary color
  accent: "#27ae60"     # Accent color
```

### Apply Theme

```bash
python3 deploy/apply_theme.py
```

This updates:
- Brand name in templates
- Color scheme in CSS
- Domain in routes

---

## Deployment Options

### Option 1: Railway.app (Recommended)

**Pros:** Free tier, auto-deploy from Git, managed database
**Cons:** None

**Steps:**

1. **Create Railway account**: https://railway.app

2. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

3. **Deploy**:
   ```bash
   railway init
   railway up
   ```

4. **Add domain**:
   ```bash
   railway domain
   ```

**Done!** Your site is live at `https://your-app.up.railway.app`

---

### Option 2: Fly.io

**Pros:** Global edge network, generous free tier
**Cons:** Requires Dockerfile

**Steps:**

1. **Install flyctl**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**:
   ```bash
   flyctl auth login
   ```

3. **Deploy**:
   ```bash
   flyctl launch
   flyctl deploy
   ```

**Done!** Live at `https://your-app.fly.dev`

---

### Option 3: VPS (DigitalOcean, Linode, etc.)

**Pros:** Full control, lowest cost at scale
**Cons:** Manual setup

**Steps:**

1. **Create Ubuntu droplet** ($5/mo)

2. **SSH into server**:
   ```bash
   ssh root@your-server-ip
   ```

3. **Install dependencies**:
   ```bash
   apt update
   apt install -y python3 python3-pip nginx certbot python3-certbot-nginx git
   ```

4. **Clone repository**:
   ```bash
   cd /var/www
   git clone https://github.com/your-username/soulfra
   cd soulfra
   bash deploy/install.sh
   ```

5. **Install gunicorn**:
   ```bash
   pip3 install gunicorn
   ```

6. **Create systemd service** (`/etc/systemd/system/soulfra.service`):
   ```ini
   [Unit]
   Description=Soulfra App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/soulfra
   ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Enable service**:
   ```bash
   systemctl enable soulfra
   systemctl start soulfra
   ```

8. **Configure nginx** (`/etc/nginx/sites-available/soulfra`):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static {
           alias /var/www/soulfra/static;
       }
   }
   ```

9. **Enable site**:
   ```bash
   ln -s /etc/nginx/sites-available/soulfra /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

10. **SSL with Let's Encrypt**:
    ```bash
    certbot --nginx -d yourdomain.com
    ```

**Done!** Live at `https://yourdomain.com`

---

### Option 4: Docker

**Pros:** Consistent environment, easy updates
**Cons:** Requires Docker knowledge

**Use the included `docker-compose.yml`:**

```bash
docker-compose up -d
```

---

## Reskin Examples

### Example 1: Math Tutoring Platform

**Goal:** Create "MathMentor" - a math tutoring platform

**Edit `deploy/theme_config.yaml`:**

```yaml
brand:
  name: "MathMentor"
  tagline: "Master Math, One Problem at a Time"
  domain: "mathmentor.com"

colors:
  primary: "#3498db"
  secondary: "#2c3e50"
  accent: "#e74c3c"

features:
  post_to_quiz: true  # Convert math posts to quizzes
  neural_soul_scoring: true
```

**Deploy:**
```bash
python3 deploy/apply_theme.py
railway up  # or your deployment method
```

**Result:** Math-focused platform with auto-generated quizzes

---

### Example 2: Cooking Blog

**Goal:** Fork "How to Cook at Home" brand

**Edit `deploy/theme_config.yaml`:**

```yaml
brand:
  name: "How to Cook at Home"
  tagline: "Simple Recipes for Everyday Cooking"
  domain: "howtocookathome.com"

colors:
  primary: "#27ae60"
  secondary: "#16a085"
  accent: "#f39c12"

features:
  qr_galleries: true  # QR codes for recipe galleries
  dm_via_qr: true     # In-person DM with chef
```

**Deploy:**
```bash
python3 deploy/apply_theme.py
railway up
```

**Result:** Cooking blog with QR recipe cards

---

### Example 3: Programming Challenges

**Goal:** Create "CodeQuest" - programming challenges platform

**Edit `deploy/theme_config.yaml`:**

```yaml
brand:
  name: "CodeQuest"
  tagline: "Level Up Your Coding Skills"
  domain: "codequest.dev"

colors:
  primary: "#9b59b6"
  secondary: "#8e44ad"
  accent: "#3498db"

features:
  post_to_quiz: true  # Convert coding lessons to challenges
  neural_soul_scoring: true  # AI-rate solutions
```

**Deploy:**
```bash
python3 deploy/apply_theme.py
fly launch
```

**Result:** Coding challenges platform with AI ratings

---

## Domain Configuration

### Point Your Domain

**If using Railway/Fly.io:**
1. Get your app URL (e.g., `your-app.up.railway.app`)
2. Add CNAME record:
   ```
   Name: @ (or www)
   Type: CNAME
   Value: your-app.up.railway.app
   ```

**If using VPS:**
1. Get your server IP
2. Add A record:
   ```
   Name: @
   Type: A
   Value: your.server.ip.address
   ```

### SSL Certificate

**Railway/Fly.io:** Automatic HTTPS ✅

**VPS:** Use Let's Encrypt
```bash
certbot --nginx -d yourdomain.com
```

---

## GitHub Pages (Static Only)

If you want 100% free hosting (static files only):

```bash
# Export static site
python3 export_static.py --all

# Deploy to GitHub Pages
cd output/<brand-slug>
git init
git add .
git commit -m "Deploy"
gh repo create <brand-slug> --public --source=. --push

# Enable GitHub Pages in repo settings
```

**Limitations:** No dynamic features (comments, analytics, DM)

---

## Environment Variables

Create `.env` file:

```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///soulfra.db

# Optional
OPENAI_API_KEY=sk-...        # Enhanced quiz generation
SMTP_HOST=smtp.gmail.com      # Email notifications
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
GOOGLE_ANALYTICS=G-XXXXXXXXXX
```

---

## Customization Scripts

### Apply Theme

```bash
python3 deploy/apply_theme.py
```

Applies theme from `deploy/theme_config.yaml`

### Generate QR Galleries

```bash
python3 qr_gallery_system.py --all
```

Generates QR code galleries for all posts

### Neural Soul Scoring

```bash
python3 neural_soul_scorer.py --all
```

Scores all posts with AI neural networks

### Post to Quiz

```bash
python3 post_to_quiz.py --all
```

Generates quizzes from all posts

### QR Analytics

```bash
python3 qr_analytics.py --dashboard
```

Generates QR analytics dashboard

---

## Troubleshooting

### Issue: Database errors

**Solution:**
```bash
rm soulfra.db
python3 -c "from database import init_db; init_db()"
sqlite3 soulfra.db < database_tier_migrations.sql
```

### Issue: Gallery routes not working

**Solution:** Register routes in `app.py`:
```python
from gallery_routes import register_gallery_routes
register_gallery_routes(app)
```

### Issue: Theme not applying

**Solution:**
```bash
python3 deploy/apply_theme.py
# Restart server
```

---

## Support & Community

- **GitHub Issues**: https://github.com/calriven/soulfra/issues
- **Documentation**: See `/docs` folder
- **Examples**: See `deploy/theme_config.yaml` for reskin examples

---

## License

MIT License - Feel free to fork and customize!

---

## Credits

Built with ❤️ by the Soulfra community

**Tech Stack:**
- Python + Flask
- SQLite
- No Node.js, No Webpack, No npm
- Pure Python stdlib for ML

**Fork it, theme it, make it yours! 🚀**
