# Soulfra Port Guide

**Complete reference to every port used by Soulfra**

---

## Quick Reference

| Port | Service | Required? | Purpose |
|------|---------|-----------|---------|
| **5001** | Soulfra Flask | Yes | Main web application |
| **11434** | Ollama AI | Optional | Local AI inference |
| **8888** | soulfra_zero.py | No | Zero-dependency demo |
| **80** | nginx | Production only | HTTP (redirects to HTTPS) |
| **443** | nginx | Production only | HTTPS (SSL/TLS) |

---

## Port 5001: Soulfra Flask Application

**What it is**: The main Soulfra web application

**Where it's configured**:
```python
# app.py (line ~11300)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
```

**How to access**:
```bash
# Localhost
http://localhost:5001

# LAN (from other devices on same network)
http://192.168.1.100:5001  # Replace with your IP

# Public internet (requires port forwarding)
http://YOUR_PUBLIC_IP:5001
```

**What runs on this port**:
- Homepage and blog
- User authentication
- Admin panel
- API endpoints
- Chat/messaging
- Post generation
- Neural network inference
- Database operations

**How to start**:
```bash
# Development
python3 app.py

# Production (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

**How to change the port**:
```python
# app.py
app.run(host='0.0.0.0', port=8080)  # Use port 8080 instead
```

```bash
# Or with environment variable
PORT=8080 python3 app.py

# Or with gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

---

## Port 11434: Ollama AI Service

**What it is**: Local AI inference engine (like ChatGPT, but runs on your machine)

**Where it's configured**:
```bash
# .env file
OLLAMA_HOST=http://localhost:11434

# Or in docker-compose.yml
OLLAMA_HOST=http://ollama:11434
```

**How to access**:
```bash
# Direct API access
curl http://localhost:11434/

# From Soulfra code
response = requests.post('http://localhost:11434/api/generate', ...)
```

**What runs on this port**:
- LLM inference (llama2, mistral, etc.)
- AI comment generation
- Post analysis
- Content classification

**How to start**:
```bash
# Native installation
ollama serve

# Or with Docker
docker run -d -p 11434:11434 ollama/ollama

# Or with docker-compose
docker-compose up -d ollama
```

**How to test it's working**:
```bash
# Check if Ollama is running
curl http://localhost:11434/

# Should return: "Ollama is running"

# List models
ollama list

# Test generation
ollama run llama2 "Hello world"
```

**Is it required?**
- **No** - Soulfra works without it
- Features that won't work: AI comment generation, post analysis
- Everything else still works (posts, auth, database, etc.)

**How to change the port**:
```bash
# Set environment variable before starting
OLLAMA_HOST=0.0.0.0 OLLAMA_PORT=12345 ollama serve

# Then update .env
OLLAMA_HOST=http://localhost:12345
```

---

## Port 8888: Zero-Dependency Demo (soulfra_zero.py)

**What it is**: Minimal HTTP server with zero external dependencies

**Where it's configured**:
```python
# soulfra_zero.py
server = HTTPServer(('localhost', 8888), MyHTTPRequestHandler)
```

**How to access**:
```bash
http://localhost:8888
```

**What runs on this port**:
- Neural network training dashboard
- Multi-format output (JSON/CSV/TXT/HTML/RTF)
- Pure stdlib HTTP server (no Flask)
- Read-only access to soulfra.db

**How to start**:
```bash
python3 soulfra_zero.py
# Visit: http://localhost:8888
```

**When to use**:
- Demonstrating Python stdlib capabilities
- Zero-dependency environments
- Learning/teaching purposes
- Quick dashboard without Flask

**Is it required?**
- **No** - This is an optional demo server
- Demonstrates what's possible with pure Python stdlib
- Not needed for normal Soulfra operation

---

## Port 80: HTTP (Production with nginx)

**What it is**: Standard HTTP port (unencrypted)

**Where it's configured**:
```nginx
# nginx.conf or /etc/nginx/sites-enabled/soulfra
server {
    listen 80;
    server_name soulfra.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}
```

**How to access**:
```bash
http://soulfra.com  # Automatically redirects to HTTPS
```

**What it does**:
- Receives HTTP requests
- Redirects to HTTPS (port 443)
- No content served directly (security)

**When to use**:
- Production deployments only
- With SSL certificate
- With nginx reverse proxy

**How to enable**:
```bash
# Uncomment nginx section in docker-compose.yml
docker-compose up -d nginx

# Or install nginx directly
sudo apt install nginx
sudo cp nginx.conf /etc/nginx/sites-available/soulfra
sudo ln -s /etc/nginx/sites-available/soulfra /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Port 443: HTTPS (Production with SSL)

**What it is**: Standard HTTPS port (encrypted with SSL/TLS)

**Where it's configured**:
```nginx
# nginx.conf
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

**How to access**:
```bash
https://soulfra.com
```

**What it does**:
- Receives encrypted HTTPS requests
- Terminates SSL (decrypts)
- Proxies to Soulfra on port 5001
- Adds security headers

**When to use**:
- Production deployments
- Public-facing websites
- When you have a domain name
- For secure connections

**How to enable**:
```bash
# Get SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d soulfra.com -d www.soulfra.com

# Certificate auto-renews
sudo certbot renew --dry-run
```

---

## How Ports Compose Together

### Development Setup (Localhost)

```
Your Code (app.py)
    ↓
Flask :5001 ← You access this
    ↓
SQLite (soulfra.db)

Optional:
Ollama :11434 ← For AI features
```

**Access**: `http://localhost:5001`

---

### Production Setup (Docker)

```
[Browser]
    ↓
nginx :80 → Redirect → nginx :443 (HTTPS)
    ↓
Soulfra Flask :5001
    ↓ ↓
    │ └→ Ollama :11434
    ↓
SQLite (soulfra.db)
```

**Access**: `https://soulfra.com`

**How it works**:
1. User visits `http://soulfra.com` (port 80)
2. nginx redirects to `https://soulfra.com` (port 443)
3. nginx terminates SSL and proxies to Flask (port 5001)
4. Flask handles request, may call Ollama (port 11434)
5. Response goes back through nginx to user

---

## Testing All Ports

```bash
# Test Soulfra (5001)
curl http://localhost:5001/
# Should return HTML

# Test Ollama (11434)
curl http://localhost:11434/
# Should return: "Ollama is running"

# Test zero-dep demo (8888)
curl http://localhost:8888/
# Should return HTML dashboard

# Test nginx (80/443) - production only
curl http://soulfra.com
curl https://soulfra.com
```

**Or use the automated test**:
```bash
python3 test_hello_world.py
# Tests ports 5001 and 11434 automatically
```

---

## Port Forwarding (Router Configuration)

To make Soulfra accessible from the internet, configure port forwarding:

### Basic Setup (HTTP only)

```
External Port: 5001
Internal IP:   192.168.1.100  (your computer's LAN IP)
Internal Port: 5001
Protocol:      TCP
```

**Access**: `http://YOUR_PUBLIC_IP:5001`

### Production Setup (with nginx)

```
Rule 1:
  External Port: 80
  Internal IP:   192.168.1.100
  Internal Port: 80
  Protocol:      TCP

Rule 2:
  External Port: 443
  Internal IP:   192.168.1.100
  Internal Port: 443
  Protocol:      TCP
```

**Access**: `https://soulfra.com`

**Do NOT forward port 11434** - Ollama should never be exposed to the internet!

---

## Firewall Configuration

### macOS

```bash
# Allow port 5001
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/python3
```

### Linux (ufw)

```bash
# Allow ports
sudo ufw allow 5001/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Do NOT allow 11434 (Ollama should be localhost-only)
```

### Docker

```yaml
# docker-compose.yml already handles ports
ports:
  - "5001:5001"  # Soulfra
  - "11434:11434"  # Ollama (WARNING: Only expose if needed)
```

**Security note**: Only expose ports you need. Never expose Ollama (11434) to the internet.

---

## Common Port Conflicts

### Port 5001 already in use

```bash
# Find what's using it
lsof -i :5001

# Kill the process
kill -9 PID

# Or use a different port
PORT=5002 python3 app.py
```

### Port 11434 already in use

```bash
# Check if Ollama is already running
ps aux | grep ollama

# Kill if needed
killall ollama

# Restart
ollama serve
```

### Port 80/443 already in use

```bash
# Check what's using it
sudo lsof -i :80
sudo lsof -i :443

# Usually Apache or another nginx
sudo systemctl stop apache2
# OR
sudo systemctl stop nginx
```

---

## Environment Variables

Control ports via environment variables:

```bash
# .env file
PORT=5001
OLLAMA_HOST=http://localhost:11434
BASE_URL=http://localhost:5001

# For production
PORT=5001
OLLAMA_HOST=http://ollama:11434  # Docker service name
BASE_URL=https://soulfra.com
```

**Load environment**:
```bash
# Python automatically loads .env if python-dotenv installed
pip install python-dotenv

# Or manually
export PORT=5001
export OLLAMA_HOST=http://localhost:11434
python3 app.py
```

---

## Quick Reference Commands

```bash
# Start everything (Docker)
docker-compose up -d
# Starts: Soulfra (5001) + Ollama (11434)

# Start Soulfra only
python3 app.py
# Runs on: http://localhost:5001

# Start Ollama only
ollama serve
# Runs on: http://localhost:11434

# Start zero-dep demo
python3 soulfra_zero.py
# Runs on: http://localhost:8888

# Test all services
python3 test_hello_world.py

# Check what's running on each port
lsof -i :5001   # Soulfra
lsof -i :11434  # Ollama
lsof -i :8888   # Zero-dep demo
```

---

## Summary

**Minimum to run Soulfra**:
- Port 5001 (Soulfra Flask app) ✓ REQUIRED
- soulfra.db (SQLite database) ✓ REQUIRED

**Optional enhancements**:
- Port 11434 (Ollama AI) - for AI features
- Port 8888 (soulfra_zero.py) - for demos
- Port 80/443 (nginx) - for production/SSL

**Most common setup**:
```bash
# Development
python3 app.py           # Port 5001
ollama serve             # Port 11434 (optional)

# Production
docker-compose up -d     # Ports 5001, 11434, 80, 443
```

**Access URLs**:
- Development: `http://localhost:5001`
- LAN: `http://192.168.1.100:5001`
- Production: `https://soulfra.com`

**That's it!** Now you understand every port Soulfra uses and why.

---

## Next Steps

- Test all ports: `python3 test_hello_world.py`
- Test network layers: `python3 test_network_stack.py`
- See network diagram: `python3 network_diagram.py`
- Deploy step-by-step: `python3 deployment_ladder.py`
