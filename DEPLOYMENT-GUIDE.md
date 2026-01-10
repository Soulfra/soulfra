# Deployment Guide - soulfra.com vs soulfra.github.io

This guide explains the deployment options for your blog network and clears up confusion about different hosting approaches.

## The Key Difference

### soulfra.github.io (GitHub Pages)
- **Type**: Static site hosting
- **Technology**: HTML, CSS, JavaScript only
- **No Backend**: Cannot run Python/Flask, no database
- **Free**: Yes, completely free
- **Custom Domain**: Can point soulfra.com → soulfra.github.io
- **Use Case**: Static blog builds (frozen HTML)

### soulfra.com (Custom Domain + Real Hosting)
- **Type**: Full application hosting
- **Technology**: Python, Flask, SQLite, Ollama, everything
- **Backend**: Full Flask app with database
- **Cost**: ~$5-20/month depending on platform
- **Custom Domain**: Use your actual soulfra.com domain
- **Use Case**: Dynamic app with admin, chat, workflows

## Current Setup Clarification

You have **two deployment strategies**:

1. **Development (localhost:5001)** - Flask app running on your Mac
2. **Production Option A (GitHub Pages)** - Static HTML only
3. **Production Option B (Vercel/Railway)** - Full Flask app with custom domain

The confusion: You've been trying to run a Flask app on GitHub Pages, which doesn't work. GitHub Pages is for static files only.

## Recommended Deployment Strategy

### For Dynamic Features (Admin, Ollama, Workflows)
**Use Railway or Vercel** → Deploy to soulfra.com

### For Static Blog Content Only
**Use GitHub Pages** → Deploy to soulfra.github.io (or point soulfra.com to it)

---

## Option 1: Deploy to Railway (Recommended)

Railway supports full Python apps with databases and custom domains.

### Step 1: Create requirements.txt

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
pip3 freeze > requirements.txt
```

Or create manually:

```txt
Flask==3.0.0
gunicorn==21.2.0
anthropic==0.18.0
requests==2.31.0
markdown2==2.4.12
```

### Step 2: Deploy to Railway

```bash
# Install Railway CLI
brew install railway

# Login
railway login

# Initialize project
railway init

# Link to your project
railway link

# Add environment variables
railway variables set SECRET_KEY="your-secret-key-here"
railway variables set ANTHROPIC_API_KEY="sk-ant-your-key"
railway variables set FLASK_ENV="production"

# Deploy
railway up
```

### Step 3: Add Custom Domain

1. Go to Railway dashboard → Your project → Settings
2. Click "Domains"
3. Add custom domain: `soulfra.com`
4. Update DNS records at your domain registrar:
   ```
   Type: CNAME
   Name: @
   Value: [Railway provides this]
   ```

### Step 4: Setup Database Persistence

Railway doesn't persist SQLite files by default. Use Railway volumes:

```bash
railway volume create soulfra-db
railway volume attach soulfra-db /app/data
```

Update app.py to use `/app/data/soulfra.db`

---

## Option 2: Deploy to Vercel

Vercel is great for Flask but has some limitations.

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Deploy

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
vercel
```

Follow prompts:
- Project name: `soulfra-blog-network`
- Framework: `Other`
- Build command: (leave blank)

### Step 3: Add Custom Domain

```bash
vercel domains add soulfra.com
```

Follow DNS instructions provided.

### Step 4: Set Environment Variables

```bash
vercel env add SECRET_KEY
vercel env add ANTHROPIC_API_KEY
```

### Limitations of Vercel
- ⚠️ Serverless functions have 10-second timeout (may affect Ollama)
- ⚠️ SQLite needs special handling (use Vercel Postgres instead)
- ⚠️ File uploads limited

**Verdict**: Railway is better for this project.

---

## Option 3: Traditional VPS (DigitalOcean, Linode)

For full control, especially for Ollama hosting.

### Step 1: Create Droplet

1. Go to DigitalOcean
2. Create Droplet (Ubuntu 22.04)
3. Choose size: $12/month (2GB RAM minimum for Ollama)

### Step 2: Setup Server

```bash
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt update
apt install -y python3 python3-pip nginx git

# Clone your repo
cd /var/www
git clone https://github.com/yourusername/soulfra-simple.git
cd soulfra-simple

# Install Python packages
pip3 install -r requirements.txt gunicorn

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2

# Start Ollama service
systemctl enable ollama
systemctl start ollama
```

### Step 3: Setup Gunicorn Service

Create `/etc/systemd/system/soulfra.service`:

```ini
[Unit]
Description=Soulfra Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/soulfra-simple
Environment="PATH=/usr/bin"
Environment="SECRET_KEY=your-secret-key"
Environment="ANTHROPIC_API_KEY=your-key"
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5001 app:app

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
systemctl enable soulfra
systemctl start soulfra
```

### Step 4: Setup Nginx

Create `/etc/nginx/sites-available/soulfra.com`:

```nginx
server {
    listen 80;
    server_name soulfra.com www.soulfra.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and restart:
```bash
ln -s /etc/nginx/sites-available/soulfra.com /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 5: Setup SSL

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d soulfra.com -d www.soulfra.com
```

---

## GitHub Pages (Static Export Only)

If you want to use GitHub Pages, you need to export static HTML.

### Step 1: Build Static Site

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 export_static.py
```

This creates static HTML from your Flask templates.

### Step 2: Deploy to GitHub Pages

```bash
cd build/
git init
git add .
git commit -m "Deploy to GitHub Pages"
git branch -M main
git remote add origin https://github.com/yourusername/yourusername.github.io.git
git push -u origin main
```

### Step 3: Custom Domain

Create `build/CNAME`:
```
soulfra.com
```

Update DNS:
```
Type: A
Name: @
Value: 185.199.108.153
       185.199.109.153
       185.199.110.153
       185.199.111.153

Type: CNAME
Name: www
Value: yourusername.github.io
```

**Limitations**:
- No admin panel
- No Ollama chat
- No workflows
- No user accounts
- Just static blog pages

---

## Recommended Setup for You

Based on your needs (admin, Ollama, workflows, multiple domains):

### Architecture

```
Production:
  Railway (Primary App)
    - soulfra.com
    - Flask app
    - Admin dashboard
    - Workflows
    - User management
    - Database (SQLite or Postgres)

  Ollama Hosting:
    - Ollama Cloud (paid) OR
    - Separate DigitalOcean droplet ($12/mo) OR
    - Keep local on laptop (free but laptop must stay on)

Static Backups:
  GitHub Pages (Optional)
    - soulfra.github.io
    - Static blog exports
    - Emergency backup
```

### Deployment Steps

1. **Deploy main app to Railway**
   ```bash
   railway up
   railway domains add soulfra.com
   ```

2. **Setup Ollama** (choose one):
   - **Option A**: Use Ollama Cloud (sign up at ollama.com/cloud)
   - **Option B**: Deploy to separate VPS
   - **Option C**: Keep on laptop (requires laptop always on)

3. **Setup other domains as Railway services**
   ```bash
   # Each domain can be a separate Railway deployment
   railway domains add calriven.com
   railway domains add deathtodata.com
   # etc.
   ```

4. **Optional**: Export static versions to GitHub Pages for SEO/backup

---

## Environment Variables Needed

For production deployment, set these:

```bash
SECRET_KEY=your-random-secret-key-change-this
ANTHROPIC_API_KEY=sk-ant-your-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///soulfra.db  # or postgres://...
OLLAMA_API_URL=http://localhost:11434  # or cloud URL
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## DNS Configuration

Once you choose hosting, update DNS at your registrar (Namecheap, GoDaddy, etc.):

### For Railway
```
Type: CNAME
Name: @
Value: your-app.up.railway.app

Type: CNAME
Name: www
Value: your-app.up.railway.app
```

### For VPS
```
Type: A
Name: @
Value: your.server.ip.address

Type: A
Name: www
Value: your.server.ip.address
```

---

## Testing Deployment

Before going live:

1. **Test locally**: `python3 app.py` → visit localhost:5001
2. **Test database migrations**: Ensure all tables exist
3. **Test Ollama connection**: Try chat feature
4. **Test admin panel**: Create test users and permissions
5. **Test workflows**: Run automation scripts

---

## Next Steps

1. Choose deployment platform (Railway recommended)
2. Deploy to production
3. Setup custom domains
4. Configure Ollama hosting
5. Setup Mac Shortcuts to work with production URL
6. Schedule automated workflows
7. Monitor with Railway dashboard

Need help? Check specific guides:
- `MAC-SHORTCUTS-SETUP.md` - Mac automation
- `domains/BLOG-NETWORK-README.md` - Network features
- Railway docs: https://docs.railway.app
