# Encryption Tiers - How Security Composes

**Understanding how each port/tier adds layers of encryption and security**

---

## The Key Insight

**Different ports don't just run different services - they compose different security tiers!**

Like Russian nesting dolls, each tier wraps the previous one with more security:

```
TIER 1: localhost         (no encryption - learning)
  ↓ wraps in
TIER 2: LAN               (network isolation)
  ↓ wraps in
TIER 3: nginx + HTTPS     (TLS encryption)
  ↓ wraps in
TIER 4: QR Auth + Session (identity + device)
  ↓ wraps in
TIER 5: End-to-End        (coming: encrypted content)
```

**Each tier is OSS** (open source), **each adds security**, **all compose together**.

---

## TIER 1: Localhost Only (Port 5001)

### What It Is

Running Soulfra on `localhost:5001` - accessible only from your computer.

### Configuration

```python
# app.py
app.run(host='127.0.0.1', port=5001)
        #    ^^^^^^^^^^^
        #    localhost only
```

### Encryption

**NONE** - All traffic is unencrypted HTTP.

### Security

- **Process isolation**: OS keeps Soulfra separate from other programs
- **No network exposure**: Not accessible from other devices
- **File system permissions**: SQLite database protected by OS

### When to Use

- ✓ **Learning & Development**: Safe to experiment
- ✓ **Writing private posts**: No one else can access
- ✓ **Testing new features**: Break things safely

### Threat Model

**Protected against**:
- ✓ Other users on network (can't access)
- ✓ Internet attackers (not exposed)

**NOT protected against**:
- ✗ Malware on your computer
- ✗ Physical access to your machine
- ✗ Root/admin user on same computer

### Example

```bash
# Start server
python3 app.py

# Access
curl http://localhost:5001/

# From other device - FAILS
curl http://192.168.1.100:5001/
# Connection refused
```

---

## TIER 2: LAN Access (Port 5001 on 0.0.0.0)

### What It Is

Binding to all network interfaces - accessible from devices on your home/office network.

### Configuration

```python
# app.py
app.run(host='0.0.0.0', port=5001)
        #    ^^^^^^^^^
        #    all interfaces
```

### Encryption

**STILL NONE** - HTTP traffic is unencrypted.

**But**: Traffic stays on local network (behind router's NAT).

### Security

- **Network isolation**: Router blocks external access by default
- **Same network required**: Devices must be on same WiFi/Ethernet
- **OS firewalls**: macOS/Linux firewall can block connections

### Additional Protection

```bash
# macOS firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock python3

# Linux (ufw)
sudo ufw allow from 192.168.1.0/24 to any port 5001
# Only allow from local network
```

### When to Use

- ✓ **Testing on phone/tablet**: Same WiFi network
- ✓ **Team development**: Share with local team
- ✓ **Home server**: Family/roommates access

### Threat Model

**Protected against**:
- ✓ Internet attackers (behind NAT)
- ✓ Unauthorized local devices (can add MAC filtering)

**NOT protected against**:
- ✗ Anyone on your WiFi (can sniff traffic)
- ✗ MITM attacks on local network
- ✗ Malicious apps on same network

### Example

```bash
# Start server
python3 app.py

# Access from phone (on same WiFi)
curl http://192.168.1.100:5001/

# Sniff traffic (unencrypted!)
tcpdump -i en0 -A 'port 5001'
# Can see all HTTP requests/responses in plain text
```

---

## TIER 3: Public with HTTPS (Port 443 via nginx)

### What It Is

Production deployment with nginx reverse proxy and SSL/TLS certificate.

### Configuration

```nginx
# /etc/nginx/sites-enabled/soulfra
server {
    listen 80;
    server_name soulfra.com;
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name soulfra.com;

    # SSL Certificate (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/soulfra.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soulfra.com/privkey.pem;

    # TLS Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;

    # Proxy to Flask
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Encryption

**TLS 1.3** - Military-grade encryption:
- **ECDHE key exchange**: Perfect forward secrecy
- **AES-128-GCM**: Authenticated encryption
- **SHA-256 hash**: Integrity verification

**What This Means**:
- Browser ↔ nginx: **Encrypted**
- nginx ↔ Flask (localhost): **Unencrypted** (same machine)

### Security Headers

```nginx
# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Content-Security-Policy "default-src 'self';" always;
```

### When to Use

- ✓ **Production websites**: Public-facing
- ✓ **Client projects**: Professional deployment
- ✓ **Sensitive data**: Login credentials, private posts

### Threat Model

**Protected against**:
- ✓ MITM attacks (TLS encryption)
- ✓ Packet sniffing (encrypted in transit)
- ✓ Session hijacking (secure cookies)
- ✓ XSS attacks (security headers)

**NOT protected against**:
- ✗ Compromised server (attacker has root)
- ✗ Stolen certificates
- ✗ DNS hijacking (need DNSSEC)

### How to Enable

```bash
# Get SSL certificate
sudo certbot --nginx -d soulfra.com -d www.soulfra.com

# Auto-renew (Let's Encrypt expires every 90 days)
sudo certbot renew --dry-run
```

### Verification

```bash
# Check SSL configuration
curl -I https://soulfra.com

# Should show:
# HTTP/2 200
# strict-transport-security: max-age=31536000

# Test with SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=soulfra.com
```

---

## TIER 4: QR Auth + Session Encryption

### What It Is

Passwordless authentication via QR codes with device fingerprinting and encrypted sessions.

### How It Works

```
1. User visits website
    ↓
2. Clicks "Login with QR"
    ↓
3. Server generates auth token:
   {
     "type": "auth",
     "token": "random_uuid_v4",
     "expires": timestamp + 5_minutes,
     "fingerprint": device_hash
   }
    ↓
4. Encode as QR code
    ↓
5. User scans with phone
    ↓
6. Phone opens: /qr/faucet/<base64_encoded_payload>
    ↓
7. Server verifies:
   - Token not expired
   - Token not already used
   - Device fingerprint matches (optional)
    ↓
8. Create session:
   - Generate session_id (32 bytes random)
   - Set httponly, secure, samesite cookie
   - Store in database with user_id
    ↓
9. Phone authenticated!
```

### Encryption

**Session Cookies**:
```python
# Session cookie settings
app.config['SESSION_COOKIE_HTTPONLY'] = True   # JS can't access
app.config['SESSION_COOKIE_SECURE'] = True     # HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
```

**Device Fingerprinting**:
```python
fingerprint = hashlib.sha256(
    user_agent +
    ip_address +
    accept_language +
    screen_resolution
).hexdigest()
```

### Security Features

1. **Short-lived tokens**: QR codes expire in 5 minutes
2. **One-time use**: Token consumed after first scan
3. **Device binding**: Optional fingerprint matching
4. **Secure cookies**: httponly, secure, samesite flags
5. **Session expiry**: Auto-logout after inactivity

### When to Use

- ✓ **Mobile-first apps**: Phone is primary device
- ✓ **Passwordless systems**: No password to forget
- ✓ **Public kiosks**: Scan QR, use, close browser = logout
- ✓ **Privacy-focused**: No username/password stored on device

### Threat Model

**Protected against**:
- ✓ Password theft (no passwords!)
- ✓ Phishing (QR codes unique per session)
- ✓ Session hijacking (device fingerprint)
- ✓ CSRF attacks (samesite cookies)

**NOT protected against**:
- ✗ QR code screenshot (could be shared)
- ✗ Stolen phone (if unlocked)
- ✗ Shoulder surfing (someone sees you scan)

### Implementation

See `qr_auth.py` for complete implementation.

---

## TIER 5: End-to-End Encryption (Future)

### What It Is

Content encrypted on client, decrypted on client - server never sees plaintext.

### How It Would Work

```
User writes post in browser
    ↓
JavaScript generates AES-256 key
    ↓
Encrypts post content
    ↓
Sends encrypted blob to server
    ↓
Server stores encrypted blob
    ↓
Other user requests post
    ↓
Server sends encrypted blob
    ↓
Browser decrypts with key
    ↓
User sees plaintext
```

**Key sharing**: Via QR codes, or asymmetric encryption (RSA/ECDH).

### When to Use

- Future feature for maximum privacy
- Server admin can't read content
- Like Signal/WhatsApp but for blog posts

---

## Comparison Table

| Tier | Encryption | Port(s) | Use Case | Threat Protection |
|------|-----------|---------|----------|-------------------|
| **1: Localhost** | None | 5001 | Development | OS isolation only |
| **2: LAN** | None | 5001 | Home network | NAT firewall |
| **3: HTTPS** | TLS 1.3 | 80, 443 | Production | MITM, sniffing |
| **4: QR Auth** | Session cookies | Any | Passwordless | Phishing, hijacking |
| **5: E2E** | AES-256 | Any | Max privacy | Server compromise |

---

## How They Compose (All OSS!)

**Development**:
```bash
# Just Flask
python3 app.py
# Tier 1: localhost only
```

**Home Server**:
```bash
# Flask + router firewall
python3 app.py  # host='0.0.0.0'
# Tier 2: LAN access
```

**Production (HTTP)**:
```bash
# Flask + nginx
gunicorn -b localhost:5001 app:app
nginx -c /etc/nginx/nginx.conf
# Tier 3: HTTPS encryption
```

**Mobile-first**:
```bash
# Flask + nginx + QR auth
# (above + qr_auth.py)
# Tier 4: Passwordless + device binding
```

**Maximum Privacy**:
```bash
# (all above + E2E encryption)
# Tier 5: Server can't read content
```

**Each tier adds to the previous!**

---

## Testing Each Tier

```bash
# Tier 1: Localhost
curl http://localhost:5001/
# Works

# Tier 2: LAN
curl http://192.168.1.100:5001/
# Works if host='0.0.0.0'

# Tier 3: HTTPS
curl https://soulfra.com/
# Shows TLS encryption

# Tier 4: QR Auth
python3 -c "from qr_auth import generate_login_qr; generate_login_qr()"
# Generates QR, scan, verify session created

# Automated testing
python3 test_hello_world.py  # Tests Tier 1, 2
python3 test_network_stack.py  # Tests Tier 1, 2, 3
```

---

## Real-World Example: Restaurant Menu

Imagine a restaurant with tiered security:

**Tier 1**: Kitchen (private, staff only) = localhost
**Tier 2**: Dining room (customers on-site) = LAN
**Tier 3**: Delivery (encrypted bag) = HTTPS
**Tier 4**: QR code menu (scan to order) = QR Auth
**Tier 5**: Secret recipes (encrypted even from chef) = E2E

**Each tier adds access!** Soulfra works the same way.

---

## Port Reference

| Port | Tier | Service | Encryption |
|------|------|---------|------------|
| 5001 | 1, 2 | Flask | None |
| 11434 | - | Ollama | localhost only |
| 80 | 3 | nginx | None (redirects to 443) |
| 443 | 3 | nginx | TLS 1.3 |

**All are OSS!** All ports run open-source software (Flask, nginx, Ollama).

---

## Summary

**Ports aren't just numbers - they're security tiers that compose!**

- **Port 5001 alone** = Tier 1 (localhost)
- **Port 5001 on 0.0.0.0** = Tier 2 (LAN)
- **Port 5001 + nginx 443** = Tier 3 (HTTPS)
- **Port 5001 + nginx + QR** = Tier 4 (Passwordless)

**Each tier wraps the previous with more security, all OSS, all composable.**

Like Unix pipes: `cat | grep | sort | uniq`
Like Docker layers: `FROM → RUN → COPY → CMD`
Like Soulfra tiers: `localhost → LAN → HTTPS → QR Auth`

**It all composes!** 🎉

---

## Next Steps

1. **Current tier**: Run `python3 test_network_stack.py` to see which tier you're at
2. **Upgrade**: Follow `deployment_ladder.py` to climb tiers
3. **Verify**: Check encryption with browser DevTools (🔒 icon)
4. **Document**: See `PORT_GUIDE.md` for port details

**Now you understand how ports = security tiers, all OSS, all composable!**
