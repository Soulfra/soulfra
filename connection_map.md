# Soulfra Connection Map

**Complete reference of WHERE each network connection point is located**

This document shows the exact files, lines, configs, and settings where each layer of the network stack connects to the next. Use this as a reference when debugging connectivity issues or understanding the flow.

---

## Table of Contents

1. [Python ↔ Operating System](#1-python--operating-system)
2. [Flask ↔ HTTP Server](#2-flask--http-server)
3. [Server ↔ Network Interfaces](#3-server--network-interfaces)
4. [LAN ↔ Router](#4-lan--router)
5. [Router ↔ Internet](#5-router--internet)
6. [DNS ↔ Domain](#6-dns--domain)
7. [Application ↔ Configuration](#7-application--configuration)

---

## 1. Python ↔ Operating System

**Where**: `app.py` (bottom of file)

**Connection Point**:
```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
```

**What Happens**:
- Python's `socket` library creates a socket
- Socket binds to OS network layer
- OS allocates port 5001 to Python process
- OS network stack handles TCP/IP

**File Path**: `app.py:~line 2000` (end of file)

**How to Verify**:
```bash
# Check if Python has bound to port
lsof -i :5001

# Should show:
# COMMAND   PID  USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
# Python  12345  user    3u  IPv4  xxxxxx      0t0  TCP *:5001 (LISTEN)
```

**How to Change**:
```python
# Change port
app.run(host='0.0.0.0', port=8080)  # Use port 8080 instead

# Bind to localhost only
app.run(host='127.0.0.1', port=5001)  # No LAN access

# Bind to all interfaces (recommended)
app.run(host='0.0.0.0', port=5001)  # LAN access enabled
```

---

## 2. Flask ↔ HTTP Server

**Where**: `app.py` (route definitions)

**Connection Points**:
```python
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/v1/<brand>/posts', methods=['POST'])
def create_post(brand):
    # API endpoint
    return jsonify({'status': 'success'})
```

**What Happens**:
- Flask maps URL paths → Python functions
- HTTP requests become function calls
- Function returns become HTTP responses
- Templates rendered to HTML

**File Path**: `app.py:~line 100-1900` (throughout file)

**How to Verify**:
```bash
# Test route directly
curl http://localhost:5001/
curl http://localhost:5001/admin
curl -X POST http://localhost:5001/api/v1/test/posts
```

**How to Add Routes**:
```python
@app.route('/new-page')
def new_page():
    return render_template('new.html')
```

---

## 3. Server ↔ Network Interfaces

**Where**: `app.py` + OS network configuration

**Critical Setting**:
```python
app.run(host='0.0.0.0', port=5001)
        ^^^^^^^^^^^^
        This is CRITICAL!
```

**What Each Host Value Means**:

| Host Value | Meaning | Access |
|------------|---------|--------|
| `127.0.0.1` | Localhost only | Only this computer |
| `0.0.0.0` | All interfaces | Localhost + LAN + Public IP |
| `192.168.1.100` | Specific interface | Only that network interface |

**Network Interfaces** (OS level):

```bash
# View network interfaces (Mac/Linux)
ifconfig

# Common interfaces:
# lo0       127.0.0.1    Loopback (localhost)
# en0       192.168.1.x  WiFi
# en1       192.168.1.y  Ethernet
```

**Connection Map**:
```
host='0.0.0.0' → Binds to:
  ├─ 127.0.0.1:5001      (localhost)
  ├─ 192.168.1.100:5001  (LAN IP)
  └─ [any other IPs]
```

**How to Verify**:
```bash
# Test localhost
curl http://localhost:5001

# Test LAN IP (find yours with: ifconfig)
curl http://192.168.1.100:5001

# From another computer on same network
curl http://192.168.1.100:5001
```

---

## 4. LAN ↔ Router

**Where**: Local network topology (physical/wireless)

**Connection Flow**:
```
Your Computer (192.168.1.100:5001)
    ↓
WiFi/Ethernet
    ↓
Router (192.168.1.1)
```

**How to Verify**:

```bash
# 1. Find your LAN IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. Find your router (gateway)
netstat -nr | grep default

# 3. Test connectivity
ping 192.168.1.1  # Router should respond

# 4. Access from another device on LAN
# On your phone (connected to same WiFi):
# Visit: http://192.168.1.100:5001
```

**Troubleshooting**:

If LAN access doesn't work:

1. **Check firewall**:
   ```bash
   # Mac
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

   # Linux
   sudo ufw status
   ```

2. **Check host binding**:
   ```python
   # In app.py - must be 0.0.0.0
   app.run(host='0.0.0.0', port=5001)
   ```

3. **Restart server** after changing host setting

---

## 5. Router ↔ Internet

**Where**: Router admin panel (usually http://192.168.1.1)

**Port Forwarding Configuration**:

| Setting | Value | Notes |
|---------|-------|-------|
| **External Port** | 5001 | Port visible to internet |
| **Internal IP** | 192.168.1.100 | Your computer's LAN IP |
| **Internal Port** | 5001 | Port on your computer |
| **Protocol** | TCP | (not UDP) |

**Common Router Admin URLs**:
- Generic: http://192.168.1.1 or http://192.168.0.1
- Netgear: http://routerlogin.net
- TP-Link: http://tplinkwifi.net
- Linksys: http://myrouter.local

**Connection Flow**:
```
Internet Request
  ↓
Your Public IP (e.g., 207.190.100.103:5001)
  ↓
Router receives request
  ↓
Router checks port forwarding rules
  ↓
Router forwards to: 192.168.1.100:5001
  ↓
Your computer receives request
```

**How to Verify**:

1. **Get your public IP**:
   ```bash
   curl https://api.ipify.org
   ```

2. **Test from external network**:
   - Use phone cellular data (NOT WiFi)
   - Visit: http://YOUR_PUBLIC_IP:5001

3. **Use online port checker**:
   - Visit: https://www.yougetsignal.com/tools/open-ports/
   - Enter your public IP and port 5001

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Port closed | Forwarding not configured | Add port forwarding rule |
| Wrong internal IP | Computer IP changed (DHCP) | Set static IP or update rule |
| ISP blocks port | Some ISPs block common ports | Try different port (e.g., 8080) |
| Router firewall | WAN firewall enabled | Allow inbound on port 5001 |

---

## 6. DNS ↔ Domain

**Where**: Domain registrar's control panel (GoDaddy, Namecheap, etc.)

**Required DNS Records**:

```
Type    Name    Value                  TTL
────────────────────────────────────────────
A       @       207.190.100.103        600
A       www     207.190.100.103        600
CNAME   www     yourdomain.com         3600
TXT     @       soulfra-verify-xxxxx   3600
```

**What Each Record Does**:

| Record Type | Purpose | Example |
|-------------|---------|---------|
| **A** | Maps domain → IP | `soulfra.com → 207.190.100.103` |
| **CNAME** | Maps subdomain → domain | `www → soulfra.com` |
| **TXT** | Verification token | `soulfra-verify-abc123` |

**Connection Flow**:
```
User types: http://soulfra.com
    ↓
Browser queries DNS
    ↓
DNS server looks up A record
    ↓
A record returns: 207.190.100.103
    ↓
Browser connects to: 207.190.100.103:80
    ↓
(Rest of chain: Router → LAN → Server)
```

**How to Configure**:

1. **Generate DNS records**:
   ```bash
   python3 dns_setup_guide.py
   ```

2. **Add to registrar**:
   - Log in to GoDaddy/Namecheap/etc.
   - Find "DNS Management" or "DNS Records"
   - Add each record as shown
   - Save changes

3. **Wait for propagation**: 5-60 minutes

4. **Verify DNS**:
   ```bash
   # Check if domain resolves
   host soulfra.com

   # Should show:
   # soulfra.com has address 207.190.100.103

   # Or use:
   dig soulfra.com +short
   ```

---

## 7. Application ↔ Configuration

**Where**: `.env` file

**Environment Variables**:

```bash
# .env file
DOMAIN=soulfra.com
BASE_URL=http://soulfra.com
PORT=5001
```

**How These Are Used**:

```python
# In app.py or config.py:
import os

DOMAIN = os.environ.get('DOMAIN', 'localhost')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5001')
PORT = int(os.environ.get('PORT', 5001))

# Used in templates for generating links:
<a href="{{ BASE_URL }}/admin">Admin Panel</a>

# Used in API responses:
{
  "url": "http://soulfra.com/posts/123",
  "share_link": "http://soulfra.com/share/abc"
}
```

**File Path**: `.env` (root directory)

**How to Change**:

```bash
# Edit .env file
nano .env

# Or create if doesn't exist
cat > .env << EOF
DOMAIN=mysite.com
BASE_URL=http://mysite.com
PORT=5001
EOF

# Restart server to apply changes
```

---

## Visual Connection Map

```
┌─────────────────────────────────────────────────────────────┐
│ USER'S BROWSER                                               │
│ http://soulfra.com/admin                                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [6] DNS LOOKUP                                               │
│ WHERE: Domain registrar (GoDaddy, Namecheap)                │
│ FILE:  DNS A record                                          │
│ VALUE: soulfra.com → 207.190.100.103                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [5] INTERNET → PUBLIC IP                                     │
│ WHERE: Internet routing                                      │
│ VALUE: 207.190.100.103:5001                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [4] ROUTER PORT FORWARDING                                   │
│ WHERE: Router admin panel (192.168.1.1)                      │
│ CONFIG: WAN:5001 → 192.168.1.100:5001                        │
│ FILE:  Router's forwarding table                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [3] LAN → YOUR COMPUTER                                      │
│ WHERE: Local network                                         │
│ VALUE: 192.168.1.100:5001                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [2] OS NETWORK STACK → PYTHON                                │
│ WHERE: app.py (line ~2000)                                   │
│ CODE:  app.run(host='0.0.0.0', port=5001)                    │
│ VALUE: Binds Python to all network interfaces                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ [1] FLASK ROUTE → FUNCTION                                   │
│ WHERE: app.py (throughout)                                   │
│ CODE:  @app.route('/admin')                                  │
│        def admin():                                          │
│            return render_template('admin.html')              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE GENERATED                                           │
│ HTML page sent back through same chain (reverse)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: Files & Settings

| What You Want To Change | Where To Find It | How To Change It |
|-------------------------|------------------|------------------|
| **Port number** | `app.py` line ~2000 | `app.run(port=5001)` |
| **LAN access** | `app.py` line ~2000 | `app.run(host='0.0.0.0')` |
| **Domain name** | `.env` | `DOMAIN=yoursite.com` |
| **Base URL** | `.env` | `BASE_URL=http://yoursite.com` |
| **Routes (pages)** | `app.py` throughout | `@app.route('/page')` |
| **Port forwarding** | Router admin panel | External → Internal mapping |
| **DNS records** | Domain registrar | A record, CNAME, TXT |
| **Server type** | `soulfra.service` | `gunicorn` vs `python3 app.py` |

---

## Testing Each Connection Point

Use these commands to test each layer:

```bash
# [1] Test Flask routes
curl http://localhost:5001/
curl http://localhost:5001/admin

# [2] Test OS binding
lsof -i :5001

# [3] Test LAN access (replace with your IP)
curl http://192.168.1.100:5001

# [4] Test router (from phone cellular data)
curl http://YOUR_PUBLIC_IP:5001

# [5] Test DNS resolution
host yourdomain.com
dig yourdomain.com

# [6] Test full domain access
curl http://yourdomain.com

# Or run automated tests:
python3 test_network_stack.py
```

---

## Common Connection Issues

| Symptom | Failed Connection | Check This |
|---------|-------------------|------------|
| "Connection refused" on localhost | Python ↔ OS | Server not running? `python3 app.py` |
| Works localhost, not LAN | Server ↔ Network | `host='0.0.0.0'` in app.py? |
| Works LAN, not public IP | Router ↔ Internet | Port forwarding configured? |
| Domain doesn't resolve | DNS ↔ Domain | A record added? Wait for propagation |
| Resolves but won't load | Full chain | Port forwarding + server running? |

---

## Production Deployment Checklist

When deploying to production, verify these connection points:

- [ ] **app.py**: `host='0.0.0.0', port=5001`
- [ ] **.env**: `DOMAIN=yourdomain.com` set correctly
- [ ] **.env**: `BASE_URL=https://yourdomain.com` (with HTTPS)
- [ ] **DNS**: A record pointing to public IP
- [ ] **Router**: Port forwarding configured (or cloud provider security group)
- [ ] **Server**: Running with `systemctl status soulfra` (or PM2, Docker, etc.)
- [ ] **Firewall**: Allows port 5001 (or 80/443 for HTTP/HTTPS)
- [ ] **SSL**: Certificate installed for HTTPS (Let's Encrypt, Cloudflare)

---

## Next Steps

1. **Test your setup**: `python3 test_network_stack.py`
2. **Visualize topology**: `python3 network_diagram.py`
3. **Interactive validation**: `./tier_validator.sh`
4. **Step-by-step deployment**: `python3 deployment_ladder.py` (coming next)

---

**Need help?** Run the automated diagnostic:
```bash
python3 test_network_stack.py --verbose
```

This will show you exactly which connection point is failing and how to fix it.
