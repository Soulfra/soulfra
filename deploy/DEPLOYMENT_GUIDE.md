# 🚀 Soulfra Simple - Deployment Guide

**One-command deployment for voice + CringeProof voting system**

Like cursor.directory: Simple. Fast. Works.

---

## ⚡ Quick Start (Local)

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
./deploy/DEPLOY_NOW.sh
```

Choose option `1` for local development.

**Access:**
- Main: http://localhost:5001/
- Voice Box: http://localhost:5001/suggestion-box
- Status Map: http://localhost:5001/status-map

---

## 🌐 Production Deployment

### Prerequisites

1. **Server Requirements:**
   - Ubuntu 20.04+ or macOS
   - Python 3.8+
   - 2GB RAM minimum
   - 10GB disk space

2. **Domain Setup:**
   - Domain name (e.g., soulfra.com)
   - DNS access to create A records

---

## 📝 Step-by-Step Production Deployment

### Step 1: Server Setup

```bash
# SSH into your server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx git
```

### Step 2: Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/yourusername/soulfra-simple.git
cd soulfra-simple
sudo chown -R $USER:$USER .
```

### Step 3: Configure DNS

**Add A Record to your domain:**

```
Type: A
Name: @ (or subdomain like "voice")
Value: YOUR_SERVER_IP
TTL: 3600
```

**Verify DNS propagation:**

```bash
dig yourdomain.com +short
# Should show your server IP
```

### Step 4: Run Deployment Script

```bash
./deploy/DEPLOY_NOW.sh
```

Choose option `2` for production deployment.

**The script will:**
- Install Python dependencies
- Check database setup
- Configure Nginx
- Setup SSL with Let's Encrypt
- Start Gunicorn
- Auto-reload on code changes

---

## 🔧 Manual Deployment (Advanced)

### 1. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Initialize Database

```bash
# Database is auto-created by Flask
# To manually initialize:
python3 -c "from database import init_db; init_db()"
```

### 3. Configure Nginx

```bash
# Copy config template
sudo cp deploy/nginx-soulfra.conf /etc/nginx/sites-available/soulfra

# Replace placeholders
sudo sed -i 's/DOMAIN_NAME/yourdomain.com/g' /etc/nginx/sites-available/soulfra
sudo sed -i "s|PROJECT_PATH|$(pwd)|g" /etc/nginx/sites-available/soulfra

# Enable site
sudo ln -s /etc/nginx/sites-available/soulfra /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### 4. Get SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 5. Start Flask with Gunicorn

```bash
# Install gunicorn if not already
pip3 install gunicorn

# Start server
gunicorn -w 4 -b 127.0.0.1:5001 app:app

# Or with daemon mode:
gunicorn -w 4 -b 127.0.0.1:5001 --daemon app:app
```

### 6. Setup Systemd Service (Optional)

```bash
sudo nano /etc/systemd/system/soulfra.service
```

**Paste:**

```ini
[Unit]
Description=Soulfra Voice + CringeProof
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/soulfra-simple
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5001 app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable soulfra
sudo systemctl start soulfra
sudo systemctl status soulfra
```

---

## 🎤 Voice Recording Setup

### WebM Upload Path

Voice recordings are uploaded as WebM files to:

```
/voice_recordings/recording_TIMESTAMP.webm
```

**Nginx serves these with:**
- CORS headers for cross-origin audio playback
- `audio/webm` MIME type
- 1-year cache (content-addressed by SHA256)

### Testing Voice Upload

```bash
# Record a test voice memo
curl -X POST http://yourdomain.com/api/upload-voice \
  -F "audio=@test.webm" \
  -H "Content-Type: multipart/form-data"

# Check if file exists
ls -lh voice_recordings/
```

---

## 📊 Monitoring

### Check Server Status

```bash
# Flask (Gunicorn)
ps aux | grep gunicorn

# Nginx
sudo systemctl status nginx

# Logs
sudo tail -f /var/log/nginx/soulfra-access.log
sudo tail -f /var/log/nginx/soulfra-error.log
```

### Status Map

Visit: `https://yourdomain.com/status-map`

**Shows:**
- ✅ Database connection
- ✅ Voice recordings folder
- ✅ CringeProof voting
- ✅ Ollama (AI)
- ✅ Whisper (transcription)
- ✅ SSL certificate
- ⚠️ File count warning

---

## 🔒 Security

### Firewall Setup

```bash
# Allow HTTP, HTTPS, SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Rate Limiting

Nginx config includes:
- **Voice uploads:** 10 requests/minute per IP
- **API calls:** 60 requests/minute per IP

### SSL Auto-Renewal

Let's Encrypt certs auto-renew via cron:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check cron job
sudo systemctl list-timers | grep certbot
```

---

## 📦 Database Backups

### Backup Database

```bash
# Backup soulfra.db
cp soulfra.db backups/soulfra_$(date +%Y%m%d_%H%M%S).db

# Or with SQLite dump
sqlite3 soulfra.db .dump > backups/soulfra_$(date +%Y%m%d_%H%M%S).sql
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/soulfra"
mkdir -p $BACKUP_DIR

# Backup database
cp /var/www/soulfra-simple/soulfra.db \
   $BACKUP_DIR/soulfra_$(date +%Y%m%d_%H%M%S).db

# Backup voice recordings (optional - large)
# tar -czf $BACKUP_DIR/voice_$(date +%Y%m%d).tar.gz \
#    /var/www/soulfra-simple/voice_recordings/

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

**Add to crontab:**

```bash
crontab -e

# Daily backup at 3 AM
0 3 * * * /var/www/soulfra-simple/backup.sh
```

---

## 🐛 Troubleshooting

### Flask Server Won't Start

```bash
# Check if port 5001 is in use
lsof -i :5001

# Kill existing process
pkill -f "gunicorn"

# Check Python errors
python3 app.py
```

### Nginx 502 Bad Gateway

```bash
# Check if Flask is running
curl http://127.0.0.1:5001/

# Check Nginx logs
sudo tail -f /var/log/nginx/soulfra-error.log

# Restart services
sudo systemctl restart soulfra
sudo systemctl restart nginx
```

### Voice Upload Fails

```bash
# Check permissions
ls -la voice_recordings/
# Should be writable by Flask user

# Fix permissions
chmod 755 voice_recordings/
chown -R www-data:www-data voice_recordings/

# Check max upload size
grep client_max_body_size /etc/nginx/sites-enabled/soulfra
# Should be 50M
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check Nginx SSL config
sudo nginx -t
```

---

## 🔄 Updates and Maintenance

### Update Code

```bash
cd /var/www/soulfra-simple

# Pull latest changes
git pull origin main

# Install new dependencies
pip3 install -r requirements.txt

# Restart server
sudo systemctl restart soulfra
```

### Database Migrations

```bash
# No migrations needed (SQLite auto-creates tables)

# To add new tables, run:
python3 -c "from database import init_db; init_db()"
```

---

## 📱 Mobile Testing

### Test Voice Recording from Phone

1. Visit: `https://yourdomain.com/voice`
2. Grant microphone permissions
3. Record 30-sec voice memo
4. Check upload: `https://yourdomain.com/suggestion-box`

### WebM Compatibility

- **iOS Safari:** ✅ Supported (iOS 14.3+)
- **Android Chrome:** ✅ Supported
- **Desktop Chrome:** ✅ Supported
- **Firefox:** ✅ Supported

---

## ☁️ GitHub Pages Export (Optional)

### Export to Static Site

```bash
# Generate static HTML
python3 build.py

# Deploy to GitHub Pages
git add .
git commit -m "Static build"
git push origin gh-pages
```

**Access:** `https://yourusername.github.io/soulfra-simple/`

---

## 📊 SOC2/GDPR Compliance

### Data Deletion Endpoint

```bash
# Delete user data
curl -X POST https://yourdomain.com/api/delete-my-data \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123}'
```

### Data Export Endpoint

```bash
# Export user data
curl https://yourdomain.com/api/export-my-data?user_id=123 \
  -o my_data.json
```

---

## 🎮 Status Map (Game-Like Debugging)

Visit: `https://yourdomain.com/status-map`

**Visual debugging interface:**
- ✅ Green = Working
- 🔧 Orange = Needs setup
- ❌ Red = Broken
- ⚠️ Yellow = Warning

**Shows:**
- Database health
- Voice system status
- AI models (Ollama, Whisper)
- Deployment status (Nginx, SSL)
- File count warning

---

## 🚀 Performance Optimization

### Gunicorn Workers

```bash
# Formula: (2 x CPU cores) + 1
# For 2 cores: 5 workers
gunicorn -w 5 -b 127.0.0.1:5001 app:app
```

### Nginx Caching

```nginx
# In /etc/nginx/sites-available/soulfra

# Cache static files
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Cache voice recordings
location /voice_recordings/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 📞 Support

**Issues:**
- GitHub: https://github.com/yourusername/soulfra-simple/issues

**Docs:**
- Trust Radar: `TRUST_RADAR_ARCHITECTURE.md`
- Database: `DATABASE_ARCHITECTURE.md`
- Working Routes: `WORKING_ROUTES.md`

---

## ✅ Deployment Checklist

- [ ] Server has Python 3.8+
- [ ] DNS A record configured
- [ ] SSL certificate installed
- [ ] Nginx configured and running
- [ ] Flask/Gunicorn running on port 5001
- [ ] Voice recordings folder writable
- [ ] Database initialized
- [ ] Status map shows all ✅
- [ ] Test voice upload from phone
- [ ] Test CringeProof voting
- [ ] Backups configured

---

**Last Updated:** 2026-01-03

**Version:** 1.0.0 - Simple deployment like cursor.directory
