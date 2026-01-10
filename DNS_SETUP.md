# DNS Setup Guide
**Soulfra Multi-Domain Network - Domain Configuration**

This guide explains how to configure DNS records to point all 9 domains to your production server.

---

## Overview

The Soulfra Network uses **9 verified domains**, all pointing to a single server:

1. `soulfra.com` - Master hub & auth provider
2. `stpetepros.com` - Tampa Bay professional directory
3. `cringeproof.com` - Voice ideas platform
4. `calriven.com` - AI & real estate platform
5. `deathtodata.com` - Privacy & crypto blog
6. `howtocookathome.com` - Recipe platform
7. `hollowtown.com` - Gaming community
8. `oofbox.com` - Gaming platform
9. `niceleak.com` - Game discovery

**One Flask app serves all domains** via Host header routing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              DNS Resolution                              │
│  soulfra.com → 123.45.67.89                             │
│  stpetepros.com → 123.45.67.89                          │
│  ... (all 9 domains) → SAME IP                          │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│          Server (123.45.67.89)                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Nginx (Port 443)                                  │ │
│  │  - SSL termination for all 9 domains               │ │
│  │  - Proxies to Flask based on Host header           │ │
│  └────────────────────┬───────────────────────────────┘ │
│                       ↓                                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Flask App (Port 5001)                             │ │
│  │  - Brand Router detects domain                     │ │
│  │  - Routes to domain-specific handlers              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Get your server IP
curl -4 ifconfig.me

# Output: 123.45.67.89

# Add A records for all domains pointing to this IP
```

---

## DNS Configuration

### Step 1: Get Server IP Address

**If using a VPS (DigitalOcean, Linode, AWS, etc.):**

```bash
# SSH into server
ssh your-user@YOUR_SERVER_IP

# Get public IP
curl -4 ifconfig.me
```

**If using a home server:**

```bash
# Get public IP from router or:
curl -4 ifconfig.me
```

**Example output:** `123.45.67.89`

### Step 2: Configure DNS Records (Cloudflare Example)

For each of the 9 domains, add these DNS records:

#### soulfra.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied (orange cloud) | Auto |
| A | www | 123.45.67.89 | Proxied (orange cloud) | Auto |
| CNAME | api | soulfra.com | Proxied | Auto |

#### stpetepros.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### cringeproof.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### calriven.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### deathtodata.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### howtocookathome.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### hollowtown.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### oofbox.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

#### niceleak.com

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | @ | 123.45.67.89 | Proxied | Auto |
| A | www | 123.45.67.89 | Proxied | Auto |

### Step 3: Verify DNS Propagation

Wait 5-10 minutes for DNS to propagate, then verify:

```bash
# Check each domain resolves to your server IP
dig soulfra.com +short
dig stpetepros.com +short
dig cringeproof.com +short
dig calriven.com +short
dig deathtodata.com +short
dig howtocookathome.com +short
dig hollowtown.com +short
dig oofbox.com +short
dig niceleak.com +short

# All should return: 123.45.67.89 (or Cloudflare IP if proxied)
```

**If using Cloudflare with proxy enabled (orange cloud):**
- DNS will return Cloudflare IPs (104.x.x.x or 172.x.x.x)
- This is CORRECT - Cloudflare proxies to your origin server
- SSL is handled by Cloudflare

---

## Cloudflare Configuration (Recommended)

### Why Cloudflare?

- ✅ **Free SSL certificates** for all domains
- ✅ **DDoS protection** and firewall
- ✅ **CDN** for static assets
- ✅ **Analytics** and traffic insights
- ✅ **DNS management** in one dashboard

### Setup Steps

1. **Add all 9 domains to Cloudflare:**
   - Go to: https://dash.cloudflare.com
   - Click "Add Site"
   - Enter domain (e.g., soulfra.com)
   - Choose Free plan
   - Repeat for all 9 domains

2. **Update nameservers at domain registrar:**
   - Cloudflare will show you 2 nameservers (e.g., `ns1.cloudflare.com`)
   - Go to your domain registrar (Namecheap, GoDaddy, etc.)
   - Update nameservers to Cloudflare's nameservers
   - Repeat for all 9 domains

3. **Configure DNS records** (as shown above)

4. **Enable SSL:**
   - Go to SSL/TLS → Overview
   - Set encryption mode to **"Full (strict)"**
   - Cloudflare will auto-generate SSL certificates

5. **Configure Firewall Rules:**
   ```
   # Block bots
   (cf.bot_management.score lt 30) → Block

   # Allow only HTTPS
   (http.request.uri.scheme eq "http") → Redirect to HTTPS

   # Rate limiting (optional)
   (http.request.uri.path contains "/api/") → Rate limit 100 req/min
   ```

---

## Alternative: Direct DNS (No Cloudflare)

If not using Cloudflare:

### At Your Domain Registrar:

For **each domain**, add these records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 123.45.67.89 | 3600 |
| A | www | 123.45.67.89 | 3600 |

### SSL Certificates (Required)

Use Let's Encrypt to generate SSL certificates:

```bash
# SSH into server
ssh your-user@YOUR_SERVER_IP

# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificates for all 9 domains
sudo certbot certonly --nginx \
  -d soulfra.com -d www.soulfra.com \
  -d stpetepros.com -d www.stpetepros.com \
  -d cringeproof.com -d www.cringeproof.com \
  -d calriven.com -d www.calriven.com \
  -d deathtodata.com -d www.deathtodata.com \
  -d howtocookathome.com -d www.howtocookathome.com \
  -d hollowtown.com -d www.hollowtown.com \
  -d oofbox.com -d www.oofbox.com \
  -d niceleak.com -d www.niceleak.com \
  --email your@email.com \
  --agree-tos
```

### Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
sudo systemctl status certbot.timer
```

---

## Testing DNS Configuration

### Verification Script

Create `scripts/verify_dns.sh`:

```bash
#!/bin/bash
# Verify all 9 domains resolve to server IP

DOMAINS=(
    "soulfra.com"
    "stpetepros.com"
    "cringeproof.com"
    "calriven.com"
    "deathtodata.com"
    "howtocookathome.com"
    "hollowtown.com"
    "oofbox.com"
    "niceleak.com"
)

echo "🌍 Verifying DNS for all domains..."
echo

for domain in "${DOMAINS[@]}"; do
    IP=$(dig +short "$domain" @8.8.8.8 | tail -1)

    if [ -n "$IP" ]; then
        echo "✅ $domain → $IP"

        # Test HTTPS
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$domain" 2>/dev/null)
        if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
            echo "   ✅ HTTPS working (HTTP $HTTP_CODE)"
        else
            echo "   ⚠️  HTTPS failed (HTTP $HTTP_CODE)"
        fi
    else
        echo "❌ $domain → NOT RESOLVED"
    fi

    echo
done
```

Run it:

```bash
chmod +x scripts/verify_dns.sh
bash scripts/verify_dns.sh
```

Expected output:
```
✅ soulfra.com → 123.45.67.89
   ✅ HTTPS working (HTTP 200)

✅ stpetepros.com → 123.45.67.89
   ✅ HTTPS working (HTTP 200)

... (all 9 domains)
```

---

## Troubleshooting

### Issue: Domain not resolving

**Cause:** DNS not propagated yet

**Solution:**
1. Wait 5-60 minutes for DNS propagation
2. Clear DNS cache: `sudo systemd-resolve --flush-caches` (Linux)
3. Test with different DNS server: `dig @8.8.8.8 soulfra.com`

### Issue: SSL certificate error

**Cause:** Certificate not installed or expired

**Solution:**
```bash
# Renew Let's Encrypt certificates
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Issue: "This site can't be reached"

**Cause:** Server firewall blocking port 80/443

**Solution:**
```bash
# Allow HTTP/HTTPS through firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# Verify Nginx is running
sudo systemctl status nginx
```

### Issue: Shows wrong domain content

**Cause:** Nginx not detecting Host header correctly

**Solution:**

Check Nginx config:
```nginx
server {
    listen 443 ssl;
    server_name soulfra.com stpetepros.com cringeproof.com ...;

    # Ensure Host header is passed to Flask
    proxy_set_header Host $host;
}
```

Restart Nginx:
```bash
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

---

## Production Checklist

Before going live:

- [ ] All 9 domains added to DNS
- [ ] DNS records pointing to server IP
- [ ] SSL certificates installed for all domains
- [ ] Nginx configured with all server_name entries
- [ ] Flask app detects domain correctly (`domain_config/domains.yaml`)
- [ ] Test each domain in browser (HTTPS)
- [ ] Monitor logs for errors: `sudo tail -f /var/log/nginx/error.log`

---

## Monitoring DNS Health

### Uptime Monitoring (Recommended)

Use a service like:
- **UptimeRobot** (https://uptimerobot.com) - Free
- **Pingdom** (https://www.pingdom.com)
- **StatusCake** (https://www.statuscake.com)

**Setup:**
1. Add all 9 domains to monitor
2. Check every 5 minutes
3. Alert via email/SMS if down

### DNS Monitoring

```bash
# Check DNS resolution health
watch -n 60 'dig soulfra.com +short'

# Monitor SSL expiry
openssl s_client -connect soulfra.com:443 -servername soulfra.com 2>/dev/null | openssl x509 -noout -dates
```

---

## Next Steps

After DNS is configured:

1. **Deploy Flask app** (see `PRODUCTION_DEPLOYMENT.md`)
2. **Test all domains** - Visit each in browser
3. **Set up monitoring** - UptimeRobot or similar
4. **Configure GitHub workflows** (see `GITHUB_SETUP.md`)
5. **Enable database encryption** (see `DATABASE_ENCRYPTION.md`)

---

## Support

**Cloudflare Docs:**
- DNS Setup: https://developers.cloudflare.com/dns/
- SSL: https://developers.cloudflare.com/ssl/

**Let's Encrypt Docs:**
- Certbot: https://certbot.eff.org/

**Nginx Docs:**
- Multi-domain config: https://nginx.org/en/docs/http/server_names.html

---

**Your domains are now pointing to your Soulfra Network!** 🌍
