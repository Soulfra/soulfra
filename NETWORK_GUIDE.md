# Soulfra Network Guide

**Complete guide to understanding and deploying Soulfra's network stack**

---

## What This Guide Covers

This guide explains:
1. **How it works**: The 9-layer network stack from OS to domain
2. **Where connections are**: Exact files, lines, and configs
3. **How to deploy**: Step-by-step from localhost to production
4. **How to debug**: Tools and techniques for troubleshooting
5. **How to prove it works**: Testing each tier

---

## The Big Picture

### How Python Becomes a Website

Soulfra is a **Python web application** that composes layers all the way from code to production:

```
┌────────────────────────────────────────────┐
│ Your Code (app.py)                         │  ← You write Python
├────────────────────────────────────────────┤
│ Flask Framework                             │  ← Converts Python → HTTP
├────────────────────────────────────────────┤
│ Server (Flask dev / gunicorn)              │  ← Serves HTTP requests
├────────────────────────────────────────────┤
│ Operating System (network stack)           │  ← TCP/IP, sockets, ports
├────────────────────────────────────────────┤
│ Network Interface (LAN)                    │  ← Your local network
├────────────────────────────────────────────┤
│ Router (NAT + port forwarding)             │  ← Gateway to internet
├────────────────────────────────────────────┤
│ Public Internet (ISP)                      │  ← Your public IP
├────────────────────────────────────────────┤
│ DNS (domain name system)                   │  ← yourdomain.com → IP
├────────────────────────────────────────────┤
│ User's Browser                             │  ← Sees your website
└────────────────────────────────────────────┘
```

**This is exactly how ReadTheDocs, Heroku, Django, and every web platform works!**

---

## The 9 Layers Explained

### Layer 1: Operating System (Network Stack)

**What it does**: Provides TCP/IP networking, port binding, sockets

**Connection point**: Python's `socket` library → OS kernel

**File/Code**:
```python
# app.py
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
    #        ^
    #        This creates a socket and binds to OS network layer
```

**How to verify**:
```bash
# Check if Python process has bound to port 5001
lsof -i :5001

# Should show Python listening on port 5001
```

**What can go wrong**:
- Port already in use
- No permission to bind port (ports < 1024 need root)
- OS firewall blocking port

---

### Layer 2: Python Environment

**What it does**: Runs the Python interpreter and loads modules

**Connection point**: `requirements.txt` → pip → Python modules

**Files**:
- `requirements.txt` - Lists dependencies
- `app.py` - Main application
- Virtual environment (optional): `venv/`

**How to verify**:
```bash
# Check Python version
python3 --version

# Check Flask is installed
python3 -c "import flask; print(flask.__version__)"

# Test app imports
python3 -c "import app; print('OK')"
```

**What can go wrong**:
- Python not installed
- Flask not installed (`pip3 install -r requirements.txt`)
- Import errors in app.py

---

### Layer 3: Flask Application

**What it does**: Maps URLs to Python functions, handles HTTP

**Connection point**: `@app.route()` decorators → HTTP paths

**File/Code**:
```python
# app.py
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')
```

**How to verify**:
```bash
# Test routes
curl http://localhost:5001/
curl http://localhost:5001/admin
```

**What can go wrong**:
- Syntax errors in route functions
- Templates not found
- Database connection issues

---

### Layer 4: HTTP Server

**What it does**: Serves HTTP requests on a port

**Connection point**: Flask/gunicorn → Network socket

**Development**:
```python
# Flask development server
app.run(host='0.0.0.0', port=5001)
```

**Production**:
```bash
# gunicorn (recommended for production)
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

**How to verify**:
```bash
# Check server is responding
curl -I http://localhost:5001

# Should return HTTP/1.1 200 OK or similar
```

**What can go wrong**:
- Server not started
- Crashed due to error
- Port already in use

---

### Layer 5: Network Interfaces

**What it does**: Binds server to network interfaces (localhost, LAN, etc.)

**Connection point**: `host='0.0.0.0'` → Network adapters

**Critical setting**:
```python
app.run(host='0.0.0.0', port=5001)
        #    ^^^^^^^^^
        #    CRITICAL for LAN access!
```

**What each value means**:

| `host` value | Accessible from |
|--------------|-----------------|
| `127.0.0.1` | Only localhost (this computer) |
| `0.0.0.0` | Localhost + LAN + Public IP (all interfaces) |
| `192.168.1.100` | Only that specific network interface |

**Network interfaces** (found via `ifconfig`):
- `lo0` / `lo` - Loopback (127.0.0.1) - localhost
- `en0` / `eth0` - WiFi/Ethernet - LAN
- `en1` / `eth1` - Other adapters

**How to verify**:
```bash
# Get your LAN IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Test from LAN (replace with your IP)
curl http://192.168.1.100:5001

# Test from another device on same WiFi
# Open http://192.168.1.100:5001 on your phone
```

**What can go wrong**:
- `host='127.0.0.1'` → No LAN access
- Firewall blocking local connections
- Server not restarted after config change

---

### Layer 6: Router (NAT & Port Forwarding)

**What it does**: Routes traffic between LAN and internet

**Connection point**: Router port forwarding rules

**Configuration** (in router admin panel):
```
External Port:  5001
Internal IP:    192.168.1.100
Internal Port:  5001
Protocol:       TCP
```

**How NAT works**:
```
Internet Request → Public IP:5001
    ↓
Router NAT Table
    ↓
Forwards to → LAN IP (192.168.1.100):5001
    ↓
Your Computer receives request
```

**How to verify**:
```bash
# Find router IP
netstat -nr | grep default

# Access router admin panel
# Usually: http://192.168.1.1
# Check port forwarding rules

# Test from external network:
# - Use phone cellular data (NOT WiFi)
# - Visit: http://YOUR_PUBLIC_IP:5001

# Or use online port checker:
# - https://www.yougetsignal.com/tools/open-ports/
```

**What can go wrong**:
- Port forwarding not configured
- Internal IP changed (use static IP)
- ISP blocks port (try different port)
- Router firewall blocking WAN access

---

### Layer 7: Public Internet

**What it does**: Routes traffic via public IP address

**Connection point**: ISP → Public IP

**How to find your public IP**:
```bash
curl https://api.ipify.org
```

**How it works**:
```
User anywhere in world
    ↓
Types: http://207.190.100.103:5001
    ↓
Internet routes to your ISP
    ↓
ISP routes to your router (public IP)
    ↓
Router forwards to your computer (port forwarding)
    ↓
Your server responds
```

**How to verify**:
```bash
# From external network (phone cellular):
curl http://YOUR_PUBLIC_IP:5001

# Or use online tools:
# https://www.yougetsignal.com/tools/open-ports/
```

**What can go wrong**:
- Port forwarding not working
- ISP uses CGNAT (no public IP) - use ngrok or VPN
- Firewall blocking
- Dynamic IP changed

---

### Layer 8: DNS (Domain Name System)

**What it does**: Translates domain names to IP addresses

**Connection point**: DNS A record → Public IP

**DNS Records needed**:
```
Type    Name    Value
────────────────────────────────────────
A       @       207.190.100.103        # yourdomain.com → IP
A       www     207.190.100.103        # www.yourdomain.com → IP
CNAME   www     yourdomain.com         # Alternative
TXT     @       soulfra-verify-xxxxx   # Verification (optional)
```

**How DNS works**:
```
User types: http://soulfra.com
    ↓
Browser queries DNS server
    ↓
DNS: "soulfra.com has A record → 207.190.100.103"
    ↓
Browser connects to 207.190.100.103
    ↓
(Rest of chain: router → server)
```

**Where to configure**: Domain registrar (GoDaddy, Namecheap, etc.)

**How to verify**:
```bash
# Check if domain resolves
host yourdomain.com

# Should show:
# yourdomain.com has address 207.190.100.103

# Or use dig
dig yourdomain.com +short
```

**How to generate records**:
```bash
python3 dns_setup_guide.py
```

**What can go wrong**:
- DNS records not added
- Typo in IP address
- DNS not propagated yet (wait 5-60 minutes)
- TTL too high (takes longer to update)

---

### Layer 9: Domain Access

**What it does**: Full chain from domain to server

**Connection point**: All previous layers composed together

**Configuration** (`.env` file):
```bash
DOMAIN=soulfra.com
BASE_URL=http://soulfra.com
PORT=5001
```

**Full request flow**:
```
1. User types: http://soulfra.com
2. DNS lookup: soulfra.com → 207.190.100.103
3. Internet routes to public IP
4. Router port forwarding: 207.190.100.103:5001 → 192.168.1.100:5001
5. LAN delivers to your computer
6. OS network stack: port 5001 → Python process
7. Flask receives request, routes to function
8. Function generates HTML response
9. Response travels back same path (reverse)
10. User sees webpage
```

**How to verify**:
```bash
# Test full domain access
curl http://yourdomain.com

# Should return HTML of your site
```

**What can go wrong**:
- Any layer in the chain broken
- DNS points to wrong IP
- Port forwarding misconfigured
- Server not running

---

## The 4 Tiers of Deployment

Soulfra can work at 4 different tiers:

### Tier 1: Localhost Only

**Accessible from**: This computer only

**Configuration**:
```python
app.run(host='127.0.0.1', port=5001)
```

**URL**: `http://localhost:5001`

**Use case**: Development, testing

**Pros**: Simple, no network config needed

**Cons**: Can't access from other devices

---

### Tier 2: LAN Access

**Accessible from**: Devices on same WiFi/network

**Configuration**:
```python
app.run(host='0.0.0.0', port=5001)
```

**URL**: `http://192.168.1.100:5001` (your LAN IP)

**Use case**: Testing on phone/tablet, local team

**Pros**: Easy testing on multiple devices

**Cons**: Only works on same network

---

### Tier 3: Public IP

**Accessible from**: Anywhere on internet

**Configuration**:
- Server: `host='0.0.0.0'`
- Router: Port forwarding enabled

**URL**: `http://207.190.100.103:5001` (your public IP)

**Use case**: Quick internet deployment

**Pros**: Accessible from anywhere

**Cons**: Ugly URL, IP can change

---

### Tier 4: Domain Name

**Accessible from**: Anywhere via domain

**Configuration**:
- Server: `host='0.0.0.0'`
- Router: Port forwarding
- DNS: A record configured
- `.env`: Domain set

**URL**: `http://soulfra.com`

**Use case**: Production deployment

**Pros**: Professional URL, persistent

**Cons**: Costs $10-15/year

---

## Tools for Testing & Deployment

We've created tools for every step of the process:

### 1. test_network_stack.py

**Tests all 9 layers and shows what's working**

```bash
python3 test_network_stack.py
```

Output:
```
[1/9] Operating System        ✓ PASS
[2/9] Python Environment       ✓ PASS
[3/9] Flask Application        ✓ PASS
[4/9] HTTP Server              ✓ PASS
[5/9] Nginx (Optional)         ⊘ SKIP
[6/9] LAN Access               ✓ PASS
[7/9] Public IP                ⊘ SKIP (requires port forwarding)
[8/9] DNS Configuration        ⊘ SKIP (no domain)
[9/9] Domain Access            ⊘ SKIP (no domain)

✓ Passed: 5/9
Current: TIER 2 - LAN Working
Next: Configure router port forwarding
```

**When to use**: Debug connectivity issues, verify setup

---

### 2. network_diagram.py

**Visualizes your network topology**

```bash
# Full diagram with real IPs
python3 network_diagram.py

# Simplified request flow
python3 network_diagram.py --simple

# Connection points only
python3 network_diagram.py --connections

# Live updating (refreshes every 5 sec)
python3 network_diagram.py --live
```

**When to use**: Understand your setup, visual reference

---

### 3. tier_validator.sh

**Interactive tier-by-tier validation**

```bash
./tier_validator.sh
```

Walks you through:
1. Testing localhost
2. Testing LAN access
3. Configuring port forwarding
4. Testing public IP
5. Configuring DNS
6. Testing domain

**When to use**: Step-by-step setup validation

---

### 4. deployment_ladder.py

**Interactive deployment from localhost → production**

```bash
# Start from beginning
python3 deployment_ladder.py

# Start at specific rung
python3 deployment_ladder.py --rung 3

# Skip automated tests (faster)
python3 deployment_ladder.py --skip-tests
```

Guides you through:
- Rung 1: Localhost setup
- Rung 2: LAN configuration
- Rung 3: Port forwarding
- Rung 4: Domain setup
- Rung 5: HTTPS/SSL info

**When to use**: Initial deployment, progressive setup

---

### 5. connection_map.md

**Reference of WHERE each connection is**

Read `connection_map.md` to find:
- Exact file and line for each layer
- How to change each setting
- How to verify each connection
- Common issues and fixes

**When to use**: Debugging specific layers, reference

---

## Common Deployment Scenarios

### Scenario 1: Personal Blog (Development)

**Goal**: Run locally for writing posts

**Configuration**:
```python
# app.py
app.run(host='127.0.0.1', port=5001)
```

**Access**: `http://localhost:5001`

**Launcher**:
```bash
python3 launcher.py  # GUI launcher
```

**Tier**: 1 (Localhost)

---

### Scenario 2: Personal Blog (Home Server)

**Goal**: Access from any device in home

**Configuration**:
```python
# app.py
app.run(host='0.0.0.0', port=5001)
```

**Access**: `http://192.168.1.100:5001`

**Launcher**:
```bash
./start_soulfra.sh  # Auto-start script
```

**Tier**: 2 (LAN)

---

### Scenario 3: Public Website (No Domain)

**Goal**: Quick internet deployment

**Requirements**:
- Server: `host='0.0.0.0'`
- Router: Port forwarding `5001 → 192.168.1.100:5001`

**Access**: `http://207.190.100.103:5001`

**Launcher**:
```bash
# Systemd service for auto-start
sudo systemctl enable soulfra
sudo systemctl start soulfra
```

**Tier**: 3 (Public IP)

---

### Scenario 4: Production Website (Domain)

**Goal**: Professional deployment

**Requirements**:
- Server: `host='0.0.0.0'`
- Router: Port forwarding
- DNS: A record `soulfra.com → 207.190.100.103`
- `.env`: `DOMAIN=soulfra.com`

**Access**: `http://soulfra.com`

**Launcher**:
```bash
# Systemd + gunicorn
sudo systemctl enable soulfra
sudo systemctl start soulfra
```

**Tier**: 4 (Domain)

---

### Scenario 5: Secure Production (HTTPS)

**Goal**: Encrypted connections

**Additional requirements**:
- SSL certificate (Let's Encrypt)
- Nginx reverse proxy
- Port 80 & 443 forwarding

**Access**: `https://soulfra.com`

**Configuration**:
```nginx
# /etc/nginx/sites-enabled/soulfra
server {
    listen 80;
    server_name soulfra.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name soulfra.com;

    ssl_certificate /etc/letsencrypt/live/soulfra.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soulfra.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Tier**: 4+ (Domain + HTTPS)

---

## Debugging Guide

### Problem: "Connection refused" on localhost

**Layer**: 1-4 (Server not running)

**Check**:
```bash
# Is server running?
ps aux | grep python
lsof -i :5001

# Try starting
python3 app.py
```

**Fix**: Start the server

---

### Problem: Works on localhost, not on LAN

**Layer**: 5 (Network interfaces)

**Check**:
```bash
# What is server bound to?
lsof -i :5001

# Should show *:5001 not 127.0.0.1:5001
```

**Fix**: Change `host='127.0.0.1'` to `host='0.0.0.0'` in app.py

---

### Problem: Works on LAN, not from internet

**Layer**: 6-7 (Port forwarding)

**Check**:
```bash
# Router port forwarding configured?
# Check router admin panel (usually 192.168.1.1)

# Test from external:
# - Use phone cellular data
# - Visit http://PUBLIC_IP:5001
```

**Fix**: Configure port forwarding in router

---

### Problem: Domain doesn't resolve

**Layer**: 8 (DNS)

**Check**:
```bash
# Does domain resolve?
host yourdomain.com

# If not, DNS not configured or not propagated
```

**Fix**:
1. Add A record at registrar
2. Wait 5-60 minutes for propagation
3. Verify with `host` command

---

### Problem: Domain resolves but site won't load

**Layer**: All layers (Full chain)

**Check**:
```bash
# Does DNS point to right IP?
host yourdomain.com
# Should match:
curl https://api.ipify.org

# Is port forwarding working?
# Test from phone cellular

# Is server running?
systemctl status soulfra
```

**Fix**: Check each layer systematically with `python3 test_network_stack.py`

---

## Composition Principle

The key insight: **Each layer wraps the one below it**

Like Russian nesting dolls:

```
Domain wraps
  ↓
DNS wraps
  ↓
Public IP wraps
  ↓
Router wraps
  ↓
LAN wraps
  ↓
Server wraps
  ↓
Flask wraps
  ↓
Python wraps
  ↓
OS
```

**Just like**:

- Linux: Syscalls wrap kernel wrap hardware
- Docker: Containers wrap images wrap registries
- Git: Commits wrap trees wrap blobs
- **Soulfra**: Domain wraps IP wraps server wraps Flask wraps Python

This is how **everything** in computing works!

---

## Quick Start Recipes

### Recipe 1: "Just make it work on my computer"

```bash
# Start server
python3 app.py

# Open browser
open http://localhost:5001
```

**Tier**: 1

---

### Recipe 2: "Let me test on my phone"

```bash
# 1. Update app.py
# Change: host='127.0.0.1'
# To:     host='0.0.0.0'

# 2. Restart server
python3 app.py

# 3. Get your IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 4. On phone (same WiFi):
# Visit: http://192.168.1.100:5001
```

**Tier**: 2

---

### Recipe 3: "Deploy to the internet"

```bash
# 1. Configure port forwarding on router:
#    External: 5001 → Internal: YOUR_LAN_IP:5001

# 2. Get public IP
curl https://api.ipify.org

# 3. Test from phone cellular data:
#    http://YOUR_PUBLIC_IP:5001
```

**Tier**: 3

---

### Recipe 4: "Deploy with domain name"

```bash
# 1. Complete Tier 3 (public IP working)

# 2. Buy domain (GoDaddy, Namecheap, etc.)

# 3. Add DNS A record:
#    yourdomain.com → YOUR_PUBLIC_IP

# 4. Update .env:
echo "DOMAIN=yourdomain.com" >> .env
echo "BASE_URL=http://yourdomain.com" >> .env

# 5. Restart server

# 6. Wait 5-60 min for DNS, then:
#    http://yourdomain.com
```

**Tier**: 4

---

## Next Steps

1. **Test your current setup**:
   ```bash
   python3 test_network_stack.py
   ```

2. **Visualize your network**:
   ```bash
   python3 network_diagram.py
   ```

3. **Deploy step-by-step**:
   ```bash
   python3 deployment_ladder.py
   ```

4. **Read connection reference**:
   ```bash
   cat connection_map.md
   ```

5. **Set up auto-start**:
   ```bash
   cat LAUNCHER_GUIDE.md
   ```

---

## Additional Resources

- **LAUNCHER_GUIDE.md** - All the ways to run Soulfra
- **QUICKSTART.md** - 5-minute deployment guide
- **connection_map.md** - Reference of all connection points
- **dns_setup_guide.py** - Generate DNS records
- **soulfra.service** - Systemd service file

---

## Philosophy

This guide is based on a simple principle:

> **Understanding WHERE connections are is more powerful than memorizing HOW they work**

If you know:
- WHERE the port is configured (`app.py` line ~2000)
- WHERE the host is set (`app.run(host='0.0.0.0')`)
- WHERE DNS is configured (domain registrar)
- WHERE port forwarding is (router admin panel)

...then you can:
- Debug any networking issue
- Deploy to any environment
- Understand any web application
- Help others with their deployments

**This knowledge transfers to every web framework:**
- Django (same `host` and `port`)
- Node.js/Express (same port forwarding)
- Ruby on Rails (same DNS)
- Go/Rust web servers (same principles)

**You're not just learning Soulfra - you're learning how the internet works!**

---

**Ready to deploy?**

```bash
python3 deployment_ladder.py
```

Let's climb! 🚀
