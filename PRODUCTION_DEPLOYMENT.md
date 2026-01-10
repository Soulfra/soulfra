# Production Deployment Guide
**Soulfra Multi-Domain Network - Real Domain Setup**

This guide covers deploying the Soulfra Network to production with your real domains.

---

## Overview

You have **9 verified domains** in the Soulfra Network:
1. `soulfra.com` - Master hub & auth provider
2. `stpetepros.com` - Tampa Bay professional directory
3. `cringeproof.com` - Voice ideas platform
4. `calriven.com` - AI & real estate platform
5. `deathtodata.com` - Privacy & crypto blog
6. `howtocookathome.com` - Recipe platform
7. `hollowtown.com` - Gaming community
8. `oofbox.com` - Gaming platform
9. `niceleak.com` - Game discovery

**One codebase serves all domains** using domain-based routing.

---

## Prerequisites

- All 9 domains registered and DNS accessible
- Server with Python 3.8+, SQLite, and Nginx
- SSL certificates (Let's Encrypt recommended)
- SMTP credentials for email notifications (optional)

---

## Phase 1: DNS Configuration

### Point All Domains to Your Server

Add **A records** for each domain:

```
# Example DNS records (replace with your server IP)
soulfra.com            A     123.45.67.89
stpetepros.com         A     123.45.67.89
cringeproof.com        A     123.45.67.89
calriven.com           A     123.45.67.89
deathtodata.com        A     123.45.67.89
howtocookathome.com    A     123.45.67.89
hollowtown.com         A     123.45.67.89
oofbox.com             A     123.45.67.89
niceleak.com           A     123.45.67.89

# Add www subdomain redirects (optional)
www.soulfra.com        CNAME  soulfra.com
www.stpetepros.com     CNAME  stpetepros.com
# ... etc for all domains
```

### Verify DNS Propagation

```bash
dig soulfra.com +short
dig stpetepros.com +short
# Should return your server IP for all domains
```

---

## Phase 2: Server Setup

### 1. Clone Repository

```bash
cd /var/www
git clone https://github.com/your-username/soulfra-simple.git
cd soulfra-simple
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Secrets

```bash
cp config/secrets.env.example config/secrets.env
nano config/secrets.env
```

**Fill in your secrets:**

```bash
# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your-256-bit-random-secret-here

# Database
DATABASE_URL=sqlite:///soulfra.db

# Email (optional but recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@soulfra.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soulfra.com

# Geolocation for StPetePros (optional)
IPAPI_KEY=your-ipapi-key  # Free at https://ipapi.co/

# Production mode
FLASK_ENV=production
FLASK_DEBUG=False
```

### 4. Initialize Database

```bash
# Run migrations
sqlite3 soulfra.db < migrations/add_categories_table.sql

# Initialize master auth tables
python3 -c "from soulfra_master_auth import init_master_auth_tables; from database import get_db; init_master_auth_tables()"
```

---

## Phase 3: SSL Certificates (Let's Encrypt)

### Install Certbot

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

### Generate Certificates for All Domains

```bash
sudo certbot certonly --nginx \
  -d soulfra.com \
  -d stpetepros.com \
  -d cringeproof.com \
  -d calriven.com \
  -d deathtodata.com \
  -d howtocookathome.com \
  -d hollowtown.com \
  -d oofbox.com \
  -d niceleak.com \
  --email your@email.com \
  --agree-tos \
  --no-eff-email
```

Certificates will be saved to:
```
/etc/letsencrypt/live/soulfra.com/
/etc/letsencrypt/live/stpetepros.com/
# ... etc
```

---

## Phase 4: Nginx Configuration

### Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/soulfra-network
```

**Add this configuration:**

```nginx
# Soulfra Network - Multi-Domain Configuration

# Upstream Flask application
upstream soulfra_app {
    server 127.0.0.1:5001;
}

# HTTP → HTTPS redirect for all domains
server {
    listen 80;
    server_name soulfra.com stpetepros.com cringeproof.com calriven.com deathtodata.com howtocookathome.com hollowtown.com oofbox.com niceleak.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server for all domains
server {
    listen 443 ssl http2;
    server_name soulfra.com stpetepros.com cringeproof.com calriven.com deathtodata.com howtocookathome.com hollowtown.com oofbox.com niceleak.com;

    # SSL certificates (adjust paths for each domain)
    ssl_certificate /etc/letsencrypt/live/$server_name/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$server_name/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/soulfra-network-access.log;
    error_log /var/log/nginx/soulfra-network-error.log;

    # Static files
    location /static {
        alias /var/www/soulfra-simple/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://soulfra_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for live features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Increase max upload size (for voice recordings)
    client_max_body_size 50M;
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/soulfra-network /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## Phase 5: Flask Application (Gunicorn)

### Install Gunicorn

```bash
pip install gunicorn
```

### Create Systemd Service

```bash
sudo nano /etc/systemd/system/soulfra-network.service
```

**Add:**

```ini
[Unit]
Description=Soulfra Network Flask Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/soulfra-simple
Environment="PATH=/var/www/soulfra-simple/venv/bin"
ExecStart=/var/www/soulfra-simple/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    --access-logfile /var/log/soulfra/access.log \
    --error-logfile /var/log/soulfra/error.log \
    app:app

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Create Log Directory

```bash
sudo mkdir -p /var/log/soulfra
sudo chown www-data:www-data /var/log/soulfra
```

### Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable soulfra-network
sudo systemctl start soulfra-network
sudo systemctl status soulfra-network
```

---

## Phase 6: Testing

### 1. Test Each Domain

Visit each domain in your browser:
- https://soulfra.com
- https://stpetepros.com
- https://cringeproof.com
- https://calriven.com
- https://deathtodata.com
- https://howtocookathome.com
- https://hollowtown.com
- https://oofbox.com
- https://niceleak.com

### 2. Test Soulfra Master Auth

1. **Create Account**: https://soulfra.com/signup-soulfra
2. **Login**: https://soulfra.com/login
3. **Test Cross-Domain Login**:
   - Login on soulfra.com
   - Visit stpetepros.com/professional/inbox
   - Should stay logged in (same JWT token)

### 3. Test StPetePros Professional Signup

1. Visit https://stpetepros.com/signup/professional
2. Should redirect to Soulfra login
3. Create account → redirected back to professional signup
4. Fill out business info → profile created
5. Visit https://stpetepros.com/professional/inbox

### 4. Test Messaging

1. Visit a professional profile (e.g., https://stpetepros.com/professional/11)
2. Fill out "Contact" form
3. Professional logs in → sees message in inbox

---

## Phase 7: Monitoring & Maintenance

### Application Logs

```bash
# Flask application logs
sudo journalctl -u soulfra-network -f

# Nginx access logs
sudo tail -f /var/log/nginx/soulfra-network-access.log

# Error logs
sudo tail -f /var/log/nginx/soulfra-network-error.log
```

### Database Backups

```bash
# Create backup script
cat > /var/www/soulfra-simple/backup.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 /var/www/soulfra-simple/soulfra.db ".backup /var/www/soulfra-simple/backups/soulfra_$DATE.db"
# Keep only last 30 days
find /var/www/soulfra-simple/backups -name "soulfra_*.db" -mtime +30 -delete
EOF

chmod +x /var/www/soulfra-simple/backup.sh

# Add to crontab (daily at 2am)
crontab -e
0 2 * * * /var/www/soulfra-simple/backup.sh
```

### SSL Certificate Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically renews via cron. Verify:
sudo systemctl status certbot.timer
```

---

## Phase 8: Next Steps (Optional)

### 1. Email Notifications

Configure SMTP in `config/secrets.env` to send:
- Welcome emails
- Password reset emails
- New message notifications
- Professional signup confirmations

### 2. Add More Categories

```python
from category_manager import CategoryManager
cm = CategoryManager()

# Add custom category
cm.add_category(
    slug='car-detailing',
    name='Car Detailing',
    domain_slug='stpetepros',
    silo_type='professionals',
    description='Auto detailing and car cleaning',
    requires_verification=False
)
```

### 3. Add OAuth Providers

Edit `config/secrets.env`:
```bash
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
```

### 4. Geo-Restriction for StPetePros

StPetePros has geo-restriction configured but not enforced (soft mode).

To enable:
```python
# In brand_router.py:183
# Change enforcement_mode from "soft" to "hard" in config/domains.yaml
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Port 443)                         │
│  All 9 domains → SSL termination → Proxy to Flask          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Flask + Gunicorn (Port 5001)                   │
│  • Brand Router (detects domain from Host header)           │
│  • Auth Bridge (enforces Soulfra Master Auth)               │
│  • Domain-specific routes                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                          │
│  • soulfra_master_users (cross-domain auth)                 │
│  • professionals (StPetePros listings)                      │
│  • categories (expandable categories)                       │
│  • messages (inbox system)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Flow: User Creates Professional Profile on StPetePros

1. User visits `stpetepros.com/signup/professional`
2. Nginx proxies to Flask (Host: stpetepros.com)
3. Brand Router detects domain → loads StPetePros config
4. Auth Bridge checks auth → not logged in
5. Redirects to `stpetepros.com/login`
6. User creates Soulfra account via `/api/master/signup`
7. JWT token generated → stored in cookie
8. Redirected back to professional signup form
9. User fills out business info → professional created
10. Professional can now access inbox at `/professional/inbox`

---

## Troubleshooting

### Issue: "Domain not found" errors

**Solution**: Check `config/domains.yaml` - ensure domain exists and `verified: true`

### Issue: Cross-domain login not working

**Solution**:
1. Verify JWT_SECRET is the same in production as in config
2. Check cookie domain settings
3. Ensure HTTPS is working (cookies won't work on HTTP/HTTPS mix)

### Issue: StPetePros requires login but shouldn't

**Solution**: Check `config/domains.yaml` → `stpetepros.requires_auth` should be `true` only for protected routes

### Issue: Messages not appearing in inbox

**Solution**:
1. Check professional's `user_id` is set
2. Verify messages table has entries: `sqlite3 soulfra.db "SELECT * FROM messages;"`
3. Check user_id matches between soulfra_master_users and users tables

---

## Support

- **Documentation**: `/docs` on your server
- **GitHub Issues**: https://github.com/your-username/soulfra-simple/issues
- **Email**: support@soulfra.com

---

**You're ready to launch! 🚀**

All 9 domains are now configured, authenticated via Soulfra Master Auth, with professional directories, expandable categories, and inbox messaging.
