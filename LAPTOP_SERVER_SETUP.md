# Use Your Laptop as the CringeProof Server

Stop paying for VPS. Your laptop is already a server.

## Why This Works

- **Whisper is already on your Mac** (fast, local)
- **Database is local** (soulfra.db - you own it)
- **Only you use it right now** (not serving millions of requests)
- **When you outgrow this** → migrate to VPS (not before)

## Step 1: Router Port Forwarding (5 minutes)

### Find Your Router Admin Page

Open a browser and visit one of these:
- http://192.168.1.1 (most common)
- http://192.168.0.1
- http://10.0.0.1

Login with your router password (check the sticker on your router).

### Set Up Port Forwarding

Look for:
- "Port Forwarding"
- "Virtual Servers"
- "NAT"
- "Applications & Gaming"

**Add this rule:**
```
External Port: 5001
Internal IP: 192.168.1.87 (your Mac's IP - check with: ifconfig | grep "inet ")
Internal Port: 5001
Protocol: TCP
```

Save and restart router.

### Test It

From your phone (disconnect from WiFi, use cellular):
```
Visit: http://YOUR_PUBLIC_IP:5001/status
```

To find your public IP: Google "what is my ip" or visit https://ifconfig.me

**If you see the status page → IT WORKS**

## Step 2: Get a Permanent URL with DuckDNS (Free)

Your home IP changes occasionally. DuckDNS fixes this.

### Sign Up

1. Visit https://www.duckdns.org
2. Sign in with GitHub
3. Create subdomain: `matthewmauer.duckdns.org` (or whatever you want)

### Install Auto-Updater on Your Mac

```bash
# Create script
mkdir ~/duckdns
cd ~/duckdns
echo "echo url=\"https://www.duckdns.org/update?domains=matthewmauer&token=YOUR_TOKEN&ip=\" | curl -k -o ~/duckdns/duck.log -K -" > duck.sh
chmod 700 duck.sh
```

Replace `YOUR_TOKEN` with the token from DuckDNS website.

### Run Every 5 Minutes

```bash
# Add to crontab
crontab -e

# Add this line:
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

**Test:**
```
Visit: http://matthewmauer.duckdns.org:5001/status
```

## Step 3: Update CringeProof to Use Your URL

### Update config.js

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive
```

Edit `config.js`:
```javascript
API_BACKEND_URL: 'https://matthewmauer.duckdns.org:5001',
```

### Add HTTPS (Optional but Recommended)

Right now it's `http://` (unencrypted). To add HTTPS:

**Option A: Use Let's Encrypt + Caddy (easiest)**
```bash
brew install caddy

# Create Caddyfile:
matthewmauer.duckdns.org:443 {
    reverse_proxy localhost:5001
    tls {
        dns duckdns YOUR_TOKEN
    }
}

# Run:
caddy run
```

**Option B: Keep HTTP for now**
- Chrome/Safari will warn "Not Secure"
- Works fine for testing
- Add HTTPS later when you have users

## Step 4: Kill Cloudflare Tunnel

```bash
# Find the tunnel process
ps aux | grep cloudflared

# Kill it
kill PROCESS_ID

# Remove from config
# Delete Cloudflare references from voice-archive/config.js
```

## Result: You Now Own Everything

✅ **Backend:** Flask on your laptop (port 5001)
✅ **Database:** soulfra.db on your SSD
✅ **Whisper:** Runs locally (fast)
✅ **URL:** matthewmauer.duckdns.org:5001
✅ **Cost:** $0/month
✅ **Control:** 100% yours

## When to Move to VPS

Move to DigitalOcean/Railway when:
- You get > 100 users
- You want 99.9% uptime
- Your laptop needs to sleep
- You travel and can't leave Mac on

**Until then: your laptop IS your server.**

## Troubleshooting

### Port forwarding not working?

1. Check Mac firewall: System Preferences → Security → Firewall → allow port 5001
2. Check router firewall: some ISPs block port 5001, try 8080 instead
3. Try DMZ mode (router setting - opens all ports to your Mac)

### DuckDNS not updating?

```bash
# Test manually:
~/duckdns/duck.sh
cat ~/duckdns/duck.log
# Should say "OK"
```

### Flask not accessible from internet?

```bash
# Make sure Flask binds to 0.0.0.0, not 127.0.0.1
# In app.py:
app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))
```

## Security Notes

- **Self-signed SSL certs are fine** for now (you're the only user)
- **Add Let's Encrypt** when you have real users
- **Firewall** - only port 5001 is exposed, rest of Mac is protected
- **DDoS protection** - if you get attacked, change DuckDNS subdomain

---

**Your laptop is powerful enough to serve 1000+ users.** Start there.
