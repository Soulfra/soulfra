# Complete Deployment Guide for Soulfra Voice System

**From localhost to live production at api.cringeproof.com**

---

## Overview

This system allows you to run your Flask voice recording API on your own computer and expose it to the internet as `api.cringeproof.com` **WITHOUT** Cloudflare Tunnel or ngrok.

**Architecture:**
```
Internet → Router (Port Forwarding) → Your Computer → Flask (localhost:5001)
```

**Key Features Deployed:**
- ✅ Voice recording with Whisper transcription
- ✅ Device fingerprinting (tracks iPhone vs Mac vs Windows)
- ✅ Auto-scraping Google News based on voice keywords
- ✅ Smart caching system (24-hour TTL)
- ✅ GitHub README generator with QR codes
- ✅ Embeddable widgets (wordmap, activity feed)

---

## Quick Start

1. Run network setup:
   ```bash
   ./setup_port_forward.sh
   ```

2. Configure router port forwarding (5001 → your local IP)

3. Initialize database:
   ```bash
   python3 device_hash.py init
   python3 voice_scraper.py init
   ```

4. Start server:
   ```bash
   python3 app.py
   ```

5. Test from internet:
   ```bash
   curl http://api.cringeproof.com:5001/
   ```

---

## Network Setup

### Port Forwarding Configuration

Add this rule to your router:

```
Service Name:    Flask API
External Port:   5001
Internal IP:     <your-local-ip>  (from setup_port_forward.sh)
Internal Port:   5001
Protocol:        TCP
```

Router locations:
- **Netgear**: Advanced → Advanced Setup → Port Forwarding
- **Linksys**: Security → Apps and Gaming
- **TP-Link**: Advanced → NAT Forwarding → Virtual Servers
- **ASUS**: WAN → Virtual Server
- **Comcast/Xfinity**: Advanced → Port Forwarding

---

## DNS Configuration

### Option 1: Manual DNS

Add A record at your domain registrar:

```
Type:    A
Name:    api
Value:   <your-public-ip>
TTL:     3600
```

**Problem**: IP may change → DNS breaks

### Option 2: Dynamic DNS (Recommended)

Create `ddns_config.json`:

```json
{
    "provider": "namecheap",
    "domain": "cringeproof.com",
    "subdomain": "api",
    "api_password": "your-ddns-password",
    "check_interval": 3600
}
```

Run DDNS daemon:

```bash
python3 ddns_updater.py daemon
```

Supported providers: namecheap, godaddy, cloudflare, noip, duckdns

---

## Testing

### Local Testing

```bash
# Health check
curl http://localhost:5001/

# Upload voice
curl -X POST -F "audio=@test.webm" http://localhost:5001/api/simple-voice/submit

# Check devices
curl http://localhost:5001/api/devices/matt

# Check news
curl http://localhost:5001/api/news/recent
```

### Internet Testing

```bash
# Test with public IP
curl http://<your-public-ip>:5001/

# Test with domain
curl http://api.cringeproof.com:5001/
```

---

## Production Setup

### Run as Service (Linux)

Create `/etc/systemd/system/flask-api.service`:

```ini
[Unit]
Description=Flask Voice API
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/soulfra-simple
ExecStart=/usr/bin/python3 /path/to/soulfra-simple/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable flask-api
sudo systemctl start flask-api
sudo systemctl status flask-api
```

### HTTPS Setup (Recommended)

Install certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

Get certificate:

```bash
sudo certbot certonly --standalone -d api.cringeproof.com
```

Update port forwarding:
- Port 80 → localhost:80
- Port 443 → localhost:443

### Database Backups

Create `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p /backups/soulfra
cp soulfra.db "/backups/soulfra/soulfra_$DATE.db"
find /backups/soulfra -name "soulfra_*.db" -mtime +7 -delete
echo "✅ Backup completed: $DATE"
```

Add to crontab (daily at 3 AM):

```bash
crontab -e
0 3 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Can't access from internet

1. Check port forwarding:
   ```bash
   ./setup_port_forward.sh
   ```

2. Check firewall:
   ```bash
   sudo ufw allow 5001/tcp
   ```

3. Test port:
   ```bash
   netstat -tuln | grep 5001
   ```

### DNS not resolving

1. Check DNS propagation:
   ```bash
   dig api.cringeproof.com +short
   ```

2. Update DNS:
   ```bash
   python3 ddns_updater.py update
   ```

### Device tracking not working

```bash
# Reinitialize tables
python3 device_hash.py init

# Check tables
sqlite3 soulfra.db "SELECT * FROM device_fingerprints;"
```

### Scraping not working

```bash
# Test manually
python3 voice_scraper.py test "artificial intelligence"

# Clean cache
python3 voice_scraper.py cleanup

# Check stats
curl http://localhost:5001/api/news/stats
```

---

## Monitoring

### Check Logs

```bash
# Flask
tail -f /tmp/flask.log

# DDNS
journalctl -u ddns -f

# System
sudo systemctl status flask-api
```

### Cleanup Tasks

```bash
# Clean expired articles
python3 voice_scraper.py cleanup

# Device stats
python3 device_hash.py stats

# Current IP
python3 ddns_updater.py check
```

---

## Quick Reference

```
┌────────────────────────────────────────────┐
│         DEPLOYMENT CHECKLIST               │
├────────────────────────────────────────────┤
│ ☐ Run setup_port_forward.sh               │
│ ☐ Configure router port forwarding        │
│ ☐ Update DNS A record                     │
│ ☐ Set up DDNS updater                     │
│ ☐ Initialize database tables              │
│ ☐ Start Flask server                      │
│ ☐ Start DDNS daemon                       │
│ ☐ Test from internet                      │
│ ☐ Set up HTTPS (optional)                 │
│ ☐ Enable automated backups                │
└────────────────────────────────────────────┘
```

**Key URLs:**
- http://api.cringeproof.com:5001/
- http://api.cringeproof.com:5001/voice
- http://api.cringeproof.com:5001/api/devices/matt
- http://api.cringeproof.com:5001/api/news/recent
- http://api.cringeproof.com:5001/api/readme/matt
- http://api.cringeproof.com:5001/badge/matt/qr.svg

---

✅ **You now have a complete voice recording system running from your own computer!**
