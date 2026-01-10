# Deploy to VPS - No Tunnels, No Bullshit

**Goal**: Get your backend running on a real server with a real domain.

**Time**: 15 minutes  
**Cost**: $6/month  
**Result**: `https://api.cringeproof.com` works forever

---

## Step 1: Create VPS (5 min)

**Option A: DigitalOcean** ($6/mo, easiest)

1. Go to https://digitalocean.com
2. Create account
3. Click "Create" → "Droplets"
4. Choose:
   - **OS**: Ubuntu 24.04 LTS
   - **Size**: Basic $6/mo (1GB RAM)
   - **Datacenter**: Closest to you
5. **SSH Key**: Add your public key (~/.ssh/id_rsa.pub)
6. Click "Create Droplet"
7. Copy IP address (e.g., `147.182.123.45`)

**Option B: Vultr** ($6/mo, same thing)
**Option C: Linode** ($5/mo, also works)

---

## Step 2: Deploy Backend (5 min)

SSH into server:

```bash
ssh root@YOUR_VPS_IP
```

Run this ONE command:

```bash
# Install everything + clone your repo
apt update && apt install -y python3 python3-pip ffmpeg nginx certbot python3-certbot-nginx git && \
git clone https://github.com/YOUR_USERNAME/soulfra-backend.git /root/backend && \
cd /root/backend && \
pip3 install flask flask-cors openai-whisper bcrypt && \
python3 -c "from database import init_db; init_db()" && \
python3 user_wordmap_engine.py init && \
echo "✅ Backend installed"
```

**Create systemd service:**

```bash
cat > /etc/systemd/system/cringeproof.service << 'SERVICE'
[Unit]
Description=CringeProof API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/backend
ExecStart=/usr/bin/python3 /root/backend/cringeproof_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl start cringeproof
systemctl enable cringeproof
systemctl status cringeproof
```

**Test it works:**

```bash
curl http://localhost:5002/health
# Should return: {"status": "ok"}
```

---

## Step 3: Set Up nginx (3 min)

```bash
cat > /etc/nginx/sites-available/api << 'NGINX'
server {
    listen 80;
    server_name api.cringeproof.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Step 4: Add DNS Record (2 min)

Go to your domain registrar (Namecheap, GoDaddy, Cloudflare DNS, etc.):

**Add A Record:**
```
Type: A
Name: api
Value: YOUR_VPS_IP
TTL: 300 (5 minutes)
```

Wait 2-5 minutes for DNS propagation.

**Test:**
```bash
curl http://api.cringeproof.com/health
```

---

## Step 5: Enable SSL (1 min)

```bash
certbot --nginx -d api.cringeproof.com
# Follow prompts (auto-renews every 90 days)
```

**Test HTTPS:**
```bash
curl https://api.cringeproof.com/health
```

**✅ DONE**

---

## Step 6: Update Your Config (1 min)

**On your laptop:**

```bash
cd soulfra-simple/
./switch-backend.sh
# Choose option 2 (Production VPS)
```

Or manually edit:
- `voice-archive/config.js` → `API_BACKEND_URL: 'https://api.cringeproof.com'`
- `output/soulfra/config.js` → `API_BACKEND_URL: 'https://api.cringeproof.com'`

**Deploy to GitHub Pages:**

```bash
cd voice-archive/
git add config.js
git commit -m "Switch to VPS backend"
git push

cd ../output/soulfra/
git add config.js
git commit -m "Switch to VPS backend"  
git push
```

**Visit https://soulfra.com** → Should work from anywhere ✅

---

## Troubleshooting

### nginx shows 502 Bad Gateway

```bash
systemctl status cringeproof
journalctl -u cringeproof -n 50
```

Restart:
```bash
systemctl restart cringeproof
```

### certbot fails

Make sure DNS is working first:
```bash
dig api.cringeproof.com
# Should show your VPS IP
```

### Can't SSH

Check firewall allows SSH:
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

---

## Maintenance

### View Logs

```bash
journalctl -u cringeproof -f
```

### Restart Backend

```bash
systemctl restart cringeproof
```

### Update Code

```bash
cd /root/backend
git pull
systemctl restart cringeproof
```

### Backup Database

```bash
cp /root/backend/soulfra.db /root/backup-$(date +%Y%m%d).db
```

Automate daily:
```bash
crontab -e
# Add:
0 2 * * * cp /root/backend/soulfra.db /root/backup-$(date +\%Y\%m\%d).db
```

---

## Cost Breakdown

- VPS: $6/month (DigitalOcean Basic)
- Domain: $12/year (already have)
- SSL: FREE (Let's Encrypt)

**Total: $6/month**

**vs Cloudflare Tunnel:** FREE but breaks randomly, URLs change, can't debug

**Worth it?** Fuck yes.

---

## One-Line Deploy (Advanced)

Create this on VPS as `/root/deploy.sh`:

```bash
#!/bin/bash
cd /root/backend && \
git pull && \
pip3 install -r requirements.txt && \
systemctl restart cringeproof && \
echo "✅ Deployed"
```

Then from laptop:
```bash
ssh root@YOUR_VPS_IP "bash /root/deploy.sh"
```

**Ship code in ONE command.** 🚀

---

## What You Get

- **Stable URL**: Never changes
- **Your domain**: api.cringeproof.com (looks professional)
- **Full control**: SSH access, logs, restart anytime
- **Auto-restart**: systemd keeps it running
- **Free SSL**: Auto-renews
- **Fast debugging**: Direct server access

**No tunnels. No proxies. No bullshit.**

This is how real apps run.
