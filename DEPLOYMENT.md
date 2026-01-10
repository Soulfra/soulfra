# Soulfra Deployment Guide

This guide shows you how to deploy Soulfra in different configurations.

**Key Principle**: Python + SQL + Standard web server. That's it.

---

## Table of Contents

1. [Quick Start (Single Domain)](#quick-start-single-domain)
2. [Multiple Subdomains](#multiple-subdomains)
3. [Separate Instances](#separate-instances)
4. [Extension Pattern](#extension-pattern)
5. [Production Checklist](#production-checklist)

---

## Quick Start (Single Domain)

**Scenario**: Deploy soulfra.com

### Step 1: Install Soulfra

```bash
# Clone or install
pip install soulfra

# Or from source
git clone https://github.com/calriven/soulfra
cd soulfra
pip install -e .
```

### Step 2: Initialize Database

```bash
# Create database and tables
python3 -c "from database import init_db; init_db()"

# Initialize soul git (optional)
python3 -c "from soul_git import init_soul_git; init_soul_git()"

# Initialize URL shortener (optional)
python3 -c "from url_shortener import init_url_shortener_table; init_url_shortener_table()"
```

### Step 3: Run Flask App

```bash
# Development
python3 app.py

# Production (with gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Step 4: Configure Nginx

```nginx
# /etc/nginx/sites-available/soulfra.com
server {
    listen 80;
    server_name soulfra.com www.soulfra.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (optional - serve directly)
    location /static {
        alias /path/to/soulfra/static;
        expires 30d;
    }
}
```

### Step 5: Enable and Restart

```bash
sudo ln -s /etc/nginx/sites-available/soulfra.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d soulfra.com -d www.soulfra.com
```

**Done!** Visit https://soulfra.com

---

## Multiple Subdomains

**Scenario**: Different subdomains for different souls/projects

- `calriven.soulfra.com` → CalRiven's soul
- `alice.soulfra.com` → Alice's soul
- `blog.soulfra.com` → Blog/newsletter

### Option A: Same Codebase, Different Views

**One database, multiple entry points**

```nginx
# /etc/nginx/sites-available/soulfra-multi
server {
    listen 80;
    server_name *.soulfra.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then in `app.py`:

```python
from flask import request

@app.before_request
def route_by_subdomain():
    """Route based on subdomain"""
    host = request.host
    
    if host.startswith('calriven.'):
        # Show CalRiven's soul
        return redirect(url_for('soul_detail', username='calriven'))
    
    elif host.startswith('alice.'):
        # Show Alice's soul
        return redirect(url_for('soul_detail', username='alice'))
    
    elif host.startswith('blog.'):
        # Show blog posts
        return redirect(url_for('index'))
    
    # Default: main site
    return None
```

### Option B: Separate Instances

**Different databases, separate processes**

```bash
# Create different directories
/var/www/calriven.soulfra.com/
/var/www/alice.soulfra.com/
/var/www/blog.soulfra.com/

# Each has its own:
# - app.py
# - soulfra.db
# - config.py
```

Nginx config:

```nginx
# CalRiven
server {
    listen 80;
    server_name calriven.soulfra.com;
    
    location / {
        proxy_pass http://127.0.0.1:5001;  # Port 5001
    }
}

# Alice
server {
    listen 80;
    server_name alice.soulfra.com;
    
    location / {
        proxy_pass http://127.0.0.1:5002;  # Port 5002
    }
}

# Blog
server {
    listen 80;
    server_name blog.soulfra.com;
    
    location / {
        proxy_pass http://127.0.0.1:5003;  # Port 5003
    }
}
```

Run each on different port:

```bash
# CalRiven instance
cd /var/www/calriven.soulfra.com
gunicorn -w 2 -b 127.0.0.1:5001 app:app

# Alice instance
cd /var/www/alice.soulfra.com
gunicorn -w 2 -b 127.0.0.1:5002 app:app

# Blog instance
cd /var/www/blog.soulfra.com
gunicorn -w 2 -b 127.0.0.1:5003 app:app
```

**Use systemd to manage each service:**

```ini
# /etc/systemd/system/soulfra-calriven.service
[Unit]
Description=Soulfra - CalRiven Instance
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/calriven.soulfra.com
ExecStart=/usr/bin/gunicorn -w 2 -b 127.0.0.1:5001 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Separate Instances

**Scenario**: Completely separate deployments on different servers

### Server 1: soulfra.com (Main platform)

```bash
# Full installation
git clone https://github.com/calriven/soulfra
cd soulfra
pip install -e .
python3 -c "from database import init_db; init_db()"
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Server 2: myproject.com (Custom instance)

```bash
# Install soulfra as dependency
pip install soulfra

# Create your custom app.py
cat > app.py << 'PYTHON'
from flask import Flask
from soulfra_core import get_unified_timeline, diff_souls

app = Flask(__name__)

@app.route('/')
def index():
    # Use soulfra's unified view
    timeline = get_unified_timeline(limit=20)
    return render_template('custom_index.html', timeline=timeline)

if __name__ == '__main__':
    app.run()
PYTHON

# Run your custom instance
python3 app.py
```

**This is the OSS pattern**: Install soulfra, extend it, run your own version.

---

## Extension Pattern

**How to fork/extend Soulfra for your own use**

### Method 1: Python Import

```python
# your_custom_app.py
from soulfra_core import get_unified_timeline, diff_souls, search_everything
from soul_model import Soul
from soul_git import soul_commit, soul_log

# Use any soulfra function
timeline = get_unified_timeline(limit=50)
soul = Soul(user_id=1).compile_pack()
commits = soul_log('username')

# Add your own features
@app.route('/my-custom-route')
def my_feature():
    # Your code here
    pass
```

### Method 2: Subclass Soul Model

```python
# custom_soul.py
from soul_model import Soul

class CustomSoul(Soul):
    """Extended soul with custom features"""
    
    def compile_pack(self):
        # Call parent method
        pack = super().compile_pack()
        
        # Add your custom data
        pack['custom_field'] = self.calculate_custom_metric()
        
        return pack
    
    def calculate_custom_metric(self):
        # Your custom logic
        return "custom value"
```

### Method 3: Custom Database Schema

```python
# custom_init.py
from database import get_db

def init_custom_tables():
    """Add your own tables"""
    db = get_db()
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS my_custom_table (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            custom_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    db.commit()
    db.close()
```

**This is standard Python**: Import, extend, customize.

---

## Production Checklist

### Security

- [ ] Change `SECRET_KEY` in config
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (Let's Encrypt)
- [ ] Set up firewall (ufw, iptables)
- [ ] Disable debug mode (`DEBUG=False`)
- [ ] Use strong database passwords

### Performance

- [ ] Use gunicorn/uwsgi (not Flask dev server)
- [ ] Set up nginx for static files
- [ ] Enable gzip compression
- [ ] Add caching headers
- [ ] Consider CDN for static assets
- [ ] Database indexing (already done in init scripts)

### Monitoring

- [ ] Set up logging
- [ ] Monitor error rates
- [ ] Track database size
- [ ] Set up backups
- [ ] Use systemd for auto-restart

### Backup

```bash
# Database backup
sqlite3 soulfra.db ".backup backup-$(date +%Y%m%d).db"

# Or with cron (daily)
0 2 * * * cd /var/www/soulfra && sqlite3 soulfra.db ".backup backup-$(date +\%Y\%m\%d).db"
```

### Environment Variables

```bash
# .env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///soulfra.db
DOMAIN=soulfra.com
```

Load in app:

```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
```

---

## Troubleshooting

### nginx shows 502 Bad Gateway

**Problem**: Flask app not running or wrong port

**Solution**:
```bash
# Check if gunicorn is running
ps aux | grep gunicorn

# Check logs
sudo journalctl -u soulfra.service -n 50

# Restart service
sudo systemctl restart soulfra
```

### Static files not loading

**Problem**: nginx not serving static files

**Solution**:
```nginx
location /static {
    alias /path/to/soulfra/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Database locked

**Problem**: SQLite locked by multiple processes

**Solution**: Use WAL mode
```python
db.execute('PRAGMA journal_mode=WAL')
```

Or migrate to PostgreSQL for multi-process:
```bash
pip install soulfra[postgres]
# Update DATABASE_URL to PostgreSQL
```

---

## Summary

**Soulfra deployment is simple**:

1. **Install**: `pip install soulfra` or clone repo
2. **Initialize**: Run init scripts for database
3. **Run**: `gunicorn -w 4 app:app`
4. **Proxy**: nginx → Flask
5. **SSL**: certbot
6. **Extend**: Standard Python imports

**No special infrastructure needed. Just Python + SQL + web server.**

**That's what you wanted**: Simple, reproducible, extensible. ✅
