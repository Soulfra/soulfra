# Network Access - Simple Guide

**Created:** 2025-12-27
**Question:** "How do we do ollama and all this stuff through ips not just localhost? and there are different tiers we already have?"
**Answer:** Clear explanation of localhost vs IPs, ports, and which tier is which

---

## The Confusion

**User asked:**
- "localhost:8888" ← Port 8888 is NOT used
- "into ips and shit too" ← Want to access from other devices
- "ollama... through ips" ← Ollama has its own port (11434)
- "different tiers" ← Referencing ENCRYPTION_TIERS.md

**Let's clarify:**

---

## Port Guide (What Actually Exists)

| Port | Service | Access | URL | Purpose |
|------|---------|--------|-----|---------|
| **5001** | Flask | localhost | http://localhost:5001 | Main platform |
| **5001** | Flask | LAN | http://192.168.x.x:5001 | Mobile/roommate access |
| **11434** | Ollama | localhost | http://localhost:11434 | AI chat (optional) |
| ~~8888~~ | ❌ NOTHING | N/A | N/A | **NOT USED** |

**Key Points:**
- **Port 5001** - Your learning platform (Flask app)
- **Port 11434** - Ollama AI (if installed)
- **Port 8888** - Ignore this, it's not part of Soulfra

---

## localhost vs IP Addresses

### What's localhost?

**localhost** = Your computer talking to itself

```
http://localhost:5001
        ↑
    Alias for 127.0.0.1 (loopback address)
```

**Who can access:** Only you, on THIS computer

**Example:**
```bash
# On your MacBook:
curl http://localhost:5001

# ✅ Works!
```

```bash
# On your phone:
curl http://localhost:5001

# ❌ Fails! (Phone's localhost ≠ Computer's localhost)
```

---

### What's an IP Address?

**IP address** = Your computer's address on the network

```bash
# Find your IP:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Example output:
inet 192.168.1.123 netmask 0xffffff00
     ↑
   This is your IP
```

**Who can access:** Anyone on the same WiFi network

**Example:**
```bash
# On your MacBook:
curl http://192.168.1.123:5001

# ✅ Works!
```

```bash
# On your phone (same WiFi):
curl http://192.168.1.123:5001

# ✅ Works! (Phone can reach your computer's IP)
```

---

## Complete Access Matrix

| Device | URL | Works? | Why? |
|--------|-----|--------|------|
| **Your computer → localhost** | `http://localhost:5001` | ✅ Yes | Loopback works |
| **Your computer → own IP** | `http://192.168.1.123:5001` | ✅ Yes | Can reach self |
| **Phone → localhost** | `http://localhost:5001` | ❌ No | Phone's localhost ≠ Your localhost |
| **Phone → your IP** | `http://192.168.1.123:5001` | ✅ Yes (same WiFi) | Network route exists |
| **Roommate → localhost** | `http://localhost:5001` | ❌ No | Roommate's computer ≠ Your computer |
| **Roommate → your IP** | `http://192.168.1.123:5001` | ✅ Yes (same WiFi) | Network route exists |
| **Internet → your IP** | `http://192.168.1.123:5001` | ❌ No | Private IP, not routable |

**TL;DR:**
- `localhost` = You only
- `192.168.x.x` = Same WiFi only
- Public domain = Internet (requires deployment)

---

## Tier System Explained

Based on [ENCRYPTION_TIERS.md](ENCRYPTION_TIERS.md), here are the security tiers:

### Tier 1: localhost Only

**Configuration:**
```python
# app.py
app.run(host='127.0.0.1', port=5001)
```

**Access:**
```bash
http://localhost:5001  # Only your computer
```

**Security:**
- ✅ Process isolation (OS protects)
- ✅ File permissions (SQLite protected)
- ❌ No encryption (HTTP, not HTTPS)
- ❌ No network exposure

**When to use:**
- Development
- Learning/practicing
- Private work

---

### Tier 2: LAN (Local Area Network)

**Configuration:**
```python
# app.py
app.run(host='0.0.0.0', port=5001)
        #    ^^^^^^^^ Accept from all IPs
```

**Access:**
```bash
# From any device on same WiFi:
http://192.168.1.123:5001
```

**Security:**
- ✅ Network isolation (WiFi only, not internet)
- ✅ Router firewall (blocks external access)
- ❌ No encryption (HTTP, not HTTPS)
- ⚠️  Anyone on WiFi can access

**When to use:**
- Mobile testing
- Roommate collaboration (same WiFi)
- QR code scanning (phone → computer)

---

### Tier 3: HTTPS (Production)

**Configuration:**
```bash
# Use nginx + certbot
nginx
SSL certificate from Let's Encrypt
```

**Access:**
```bash
https://yourdomain.com
```

**Security:**
- ✅ TLS encryption (all traffic encrypted)
- ✅ Internet-routable (accessible anywhere)
- ✅ Certificate validation (prevents MITM)
- ✅ Session cookies encrypted

**When to use:**
- Public deployment
- Production use
- Sensitive data

**Setup:** See [DEPLOYMENT.md](DEPLOYMENT.md)

---

### Tier 4: QR Auth + Sessions

**Configuration:**
```python
# QR codes generate signed tokens
# Sessions track authenticated users
```

**Access:**
```bash
# Scan QR → Auto-login → Session cookie
```

**Security:**
- ✅ All Tier 3 features
- ✅ User authentication
- ✅ Device tracking (QR scan = authorized device)
- ✅ HMAC-signed QR payloads (tamper-proof)

**When to use:**
- Multi-user deployments
- Shared hosting
- Access control needed

---

### Tier 5: End-to-End Encryption (Future)

**Not implemented yet**

---

## How to Access from Different Devices

### Scenario 1: Just You, One Computer

**Use:** localhost

```bash
python3 app.py
# Opens: http://localhost:5001
```

**Why:** Fastest, simplest, most secure

---

### Scenario 2: You + Your Phone (Testing)

**Use:** Local IP address

```bash
# Step 1: Find your IP
ifconfig | grep "inet " | grep -v 127.0.0.1
# → inet 192.168.1.123

# Step 2: Start server on all interfaces
# Edit app.py temporarily:
app.run(host='0.0.0.0', port=5001)  # Accept all IPs

# Step 3: On phone (same WiFi):
# Browser → http://192.168.1.123:5001
```

**Why:** Mobile testing, QR code scanning

**Revert after:** Change back to `host='127.0.0.1'` when done

---

### Scenario 3: You + Roommates (Same WiFi)

**Use:** Local IP address (same as Scenario 2)

```bash
# You start server:
python3 app.py  # With host='0.0.0.0'

# Tell roommates:
"Visit http://192.168.1.123:5001"

# Or share QR code that encodes URL
```

**Why:** Collaborative learning sessions, practice rooms

---

### Scenario 4: Deploy to Internet

**Use:** ngrok (temporary) or VPS (permanent)

**Option A: ngrok (Quick & Temporary)**
```bash
# Terminal 1
python3 app.py

# Terminal 2
ngrok http 5001

# Gives you:
https://abc123.ngrok.io → Forwards to localhost:5001
```

**Why:** Quick demos, sharing with friends

**Docs:** [NETWORK_GUIDE.md](NETWORK_GUIDE.md)

---

**Option B: VPS (Permanent)**
```bash
# Deploy to DigitalOcean/AWS/etc.
# Use nginx + SSL certificate
# Point domain to VPS IP
```

**Why:** Production deployment

**Docs:** [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Ollama Through IPs

**Ollama runs on a different port!**

### localhost Access (Default)

```bash
# Ollama runs on:
http://localhost:11434

# Test it:
curl http://localhost:11434/api/tags
```

**Who can access:** Only your computer

---

### LAN Access (Optional)

**By default, Ollama only listens on localhost**

To allow LAN access:

```bash
# Option 1: Environment variable
OLLAMA_HOST=0.0.0.0 ollama serve

# Option 2: Config file
# ~/.ollama/config.json
{
  "host": "0.0.0.0:11434"
}
```

**Now accessible from:**
```bash
# From phone/roommate:
http://192.168.1.123:11434
```

**Warning:** Only do this on trusted WiFi!

---

## Port Summary Table

| Port | Default Host | Service | Access From |
|------|-------------|---------|-------------|
| 5001 | 127.0.0.1 | Flask | Localhost only |
| 5001 | 0.0.0.0 | Flask | Same WiFi |
| 11434 | 127.0.0.1 | Ollama | Localhost only |
| 11434 | 0.0.0.0 | Ollama | Same WiFi (if configured) |
| ~~8888~~ | ❌ N/A | Nothing | N/A |

---

## Why NOT Port 8888?

**Port 8888 is commonly used for:**
- Jupyter Notebook
- Some API servers
- Custom applications

**But NOT for Soulfra!**

**If you see references to 8888:**
- Ignore them
- Or delete them
- They're not part of this platform

**Actual ports:**
- Flask → 5001
- Ollama → 11434

---

## Quick Reference Commands

### Find Your IP

```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
```

---

### Start Flask (localhost only)

```python
# app.py
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
```

```bash
python3 app.py
# Accessible: http://localhost:5001
```

---

### Start Flask (LAN access)

```python
# app.py
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

```bash
python3 app.py
# Accessible: http://192.168.x.x:5001
```

---

### Start Ollama (localhost only)

```bash
ollama serve
# Accessible: http://localhost:11434
```

---

### Start Ollama (LAN access)

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
# Accessible: http://192.168.x.x:11434
```

---

### Test Connectivity

```bash
# From localhost
curl http://localhost:5001/

# From LAN
curl http://192.168.1.123:5001/

# Check Ollama
curl http://localhost:11434/api/tags
```

---

## Troubleshooting

### Problem: Can't access from phone

**Symptom:**
```
Phone browser → http://192.168.1.123:5001
Error: "Site can't be reached"
```

**Fixes:**

**1. Check both devices on same WiFi**
```bash
# On Mac:
networksetup -getairportnetwork en0

# On phone:
Settings → WiFi → Check network name

# Must match!
```

**2. Check Flask is listening on all IPs**
```python
# app.py - should be:
app.run(host='0.0.0.0', port=5001)

# NOT:
app.run(host='127.0.0.1', port=5001)  # ← Only localhost!
```

**3. Check firewall**
```bash
# macOS - temporarily disable
sudo pfctl -d

# Re-enable after testing
sudo pfctl -e
```

---

### Problem: Ollama not accessible

**Symptom:**
```bash
curl http://localhost:11434/api/tags
# Error: Connection refused
```

**Fix:**

**1. Is Ollama running?**
```bash
# Check process
ps aux | grep ollama

# If not running:
ollama serve
```

**2. Is it on the right port?**
```bash
# Should be 11434, not 8888
curl http://localhost:11434/api/tags  # ✅
curl http://localhost:8888/api/tags   # ❌
```

---

### Problem: Port already in use

**Symptom:**
```
Address already in use
Port 5001 is in use by another program
```

**Fix:**

```bash
# Find process using port
lsof -ti:5001

# Kill it
kill -9 $(lsof -ti:5001)

# Restart
python3 app.py
```

---

## Summary

**Ports:**
- **5001** = Flask (learning platform)
- **11434** = Ollama (AI chat)
- **8888** = Not used, ignore it

**Access:**
- **localhost** = You only (`http://localhost:5001`)
- **LAN** = Same WiFi (`http://192.168.x.x:5001`)
- **Internet** = Requires deployment (`https://yourdomain.com`)

**Tiers:**
1. localhost (dev)
2. LAN (mobile/roommates)
3. HTTPS (production)
4. QR Auth (multi-user)
5. E2E (future)

**To test on phone:**
1. Find IP: `ifconfig | grep "inet "`
2. Start Flask with `host='0.0.0.0'`
3. On phone: `http://YOUR_IP:5001`

**Ollama access:**
- Default: `http://localhost:11434`
- LAN: `OLLAMA_HOST=0.0.0.0 ollama serve`

---

**Created:** 2025-12-27
**Next:** Test mobile access using [MOBILE_QR_TEST.md](MOBILE_QR_TEST.md)
