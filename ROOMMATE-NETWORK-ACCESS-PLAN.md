# 🏠 ROOMMATE NETWORK ACCESS PLAN
**How to share Ollama, Flask, and other services with your roommates on the local network**

---

## 🎯 GOAL

Let your roommates access:
1. **Ollama API** - Use your AI models from their laptops
2. **Flask Studio** - Write blog posts via your Magic Publish system
3. **QR Flow System** - Use the authentication flow
4. **Any other local services** - Without exposing them to the entire internet

---

## 🔐 CURRENT STATE (Localhost Only)

Right now, all your services are bound to `127.0.0.1` (localhost):

```python
# In app.py:
app.run(host='127.0.0.1', port=5001)  # Only accessible from YOUR laptop
```

```bash
# Ollama:
ollama serve  # Binds to 127.0.0.1:11434 by default
```

**Problem:** Roommates on same WiFi CANNOT access these because localhost = only your machine.

---

## ✅ SOLUTION: Bind to 0.0.0.0 (All Network Interfaces)

### Step 1: Find Your Local IP Address

```bash
# On macOS:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Or simpler:
ipconfig getifaddr en0  # WiFi
ipconfig getifaddr en1  # Ethernet
```

**Example output:** `192.168.1.42`

This is your **local IP** on your home network.

---

### Step 2: Configure Flask to Accept Network Connections

**Option A: Modify app.py directly**

```python
# In /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/app.py
# Change this line:
app.run(host='127.0.0.1', port=5001, debug=True)

# To this:
app.run(host='0.0.0.0', port=5001, debug=True)
```

**Option B: Use environment variable**

```bash
export FLASK_RUN_HOST=0.0.0.0
python3 app.py
```

**Now roommates can access:**
- `http://192.168.1.42:5001/studio` (from their laptops on same WiFi)

---

### Step 3: Configure Ollama to Accept Network Connections

**Method 1: Set environment variable**

```bash
# In ~/.zshrc or ~/.bash_profile:
export OLLAMA_HOST=0.0.0.0:11434

# Then restart Ollama:
pkill ollama
ollama serve
```

**Method 2: Use systemd/launchd (persistent)**

Create: `~/Library/LaunchAgents/com.ollama.server.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0:11434</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Now roommates can access:**
- `http://192.168.1.42:11434/api/tags` (list models)
- `http://192.168.1.42:11434/api/generate` (generate text)

---

### Step 4: Configure QR Flow System (Ports 8001, 5002, 5003)

**In Soulfra/START-ALL.sh, modify each app.py:**

```bash
# Before starting each service, add FLASK_RUN_HOST:
export FLASK_RUN_HOST=0.0.0.0

# Or modify each app.py file in:
# - Soulfra.com/app.py
# - Soulfraapi.com/app.py
# - Soulfra.ai/app.py

# Change:
app.run(port=8001)

# To:
app.run(host='0.0.0.0', port=8001)
```

---

## 🔥 FIREWALL CONFIGURATION (macOS)

By default, macOS might block incoming connections. Allow them:

### Check current firewall status:
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### Allow Python (for Flask apps):
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3
```

### Allow Ollama:
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/ollama
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/ollama
```

---

## 🧪 TESTING FROM ROOMMATE'S LAPTOP

### From your roommate's computer (on same WiFi):

**Test Ollama:**
```bash
curl http://192.168.1.42:11434/api/tags
```

**Test Flask Studio:**
```bash
curl http://192.168.1.42:5001/studio
# Or just open in browser
```

**Test QR Flow:**
```bash
curl http://192.168.1.42:8001
```

---

## 🔐 SECURITY CONSIDERATIONS

### ⚠️ WARNING: No Authentication!

Currently, your services have **NO password protection**. Anyone on your WiFi can:
- Use your Ollama models (consume GPU/CPU)
- Publish blog posts
- Access your databases

### Add Basic Authentication (Recommended)

**For Flask apps:**

```python
from flask import request, Response

def check_auth(username, password):
    return username == 'roommate' and password == 'your-shared-password'

def authenticate():
    return Response(
        'Login required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Protect routes:
@app.route('/studio')
@requires_auth
def studio():
    # ... existing code
```

**For Ollama:**

Use nginx or Apache as a reverse proxy with basic auth:

```nginx
server {
    listen 11435;
    location / {
        auth_basic "Ollama API";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:11434;
    }
}
```

---

## 🌐 ALTERNATIVE: SSH Tunneling (More Secure)

Instead of exposing ports directly, roommates can SSH tunnel:

**Roommate runs this on their laptop:**
```bash
# Forward their local port 5001 to your laptop's port 5001
ssh -L 5001:localhost:5001 you@192.168.1.42

# Then access via localhost:
curl http://localhost:5001/studio
```

**Pros:**
- Encrypted connection
- Uses SSH authentication (keys/passwords you already have)
- No firewall changes needed

**Cons:**
- Requires SSH access to your laptop
- Roommate needs to keep SSH connection open

---

## 📡 EXTERNAL API INTEGRATION (Google, Stack Overflow, etc.)

### For debugging with external APIs:

**Create API debugging script:**

```python
#!/usr/bin/env python3
"""
API DEBUGGER - Test external API calls to help debug issues
"""

import requests
import json

def test_google_search_api():
    """Test Google Custom Search API"""
    api_key = "YOUR_GOOGLE_API_KEY"
    search_engine_id = "YOUR_SEARCH_ENGINE_ID"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': 'ollama network access configuration'
    }

    response = requests.get(url, params=params)
    print(json.dumps(response.json(), indent=2))

def test_stackoverflow_api():
    """Test Stack Overflow API (no key needed for read-only)"""
    url = "https://api.stackexchange.com/2.3/search"
    params = {
        'order': 'desc',
        'sort': 'relevance',
        'intitle': 'ollama network access',
        'site': 'stackoverflow'
    }

    response = requests.get(url, params=params)

    for item in response.json().get('items', [])[:5]:
        print(f"Q: {item['title']}")
        print(f"   Link: {item['link']}")
        print(f"   Score: {item['score']}")
        print()

def test_github_api():
    """Search GitHub issues/discussions"""
    url = "https://api.github.com/search/issues"
    params = {
        'q': 'ollama network access repo:ollama/ollama',
        'per_page': 5
    }

    response = requests.get(url, params=params)

    for item in response.json().get('items', []):
        print(f"Issue: {item['title']}")
        print(f"       {item['html_url']}")
        print()

# Run all tests:
test_stackoverflow_api()
test_github_api()
```

---

## 🚀 QUICK START GUIDE FOR ROOMMATES

**Copy-paste instructions to send your roommates:**

```
Hey! Here's how to use my Ollama API and blog system:

1. Make sure you're on the same WiFi (our home network)

2. Use these URLs:
   - Ollama API: http://192.168.1.42:11434
   - Blog Studio: http://192.168.1.42:5001/studio

3. Example: Generate text with Ollama from Python

   import requests

   response = requests.post(
       'http://192.168.1.42:11434/api/generate',
       json={
           'model': 'llama3.2',
           'prompt': 'Why is the sky blue?',
           'stream': False
       }
   )

   print(response.json()['response'])

4. Example: Publish a blog post

   Open browser → http://192.168.1.42:5001/studio
   Write content → Click "Magic Publish"

   Your post will appear on soulfra.com in ~10 minutes!

5. Issues? Let me know!
```

---

## 📋 CHECKLIST: Enable Roommate Access

- [ ] Find your local IP: `ipconfig getifaddr en0`
- [ ] Modify Flask apps to bind `0.0.0.0`
- [ ] Set Ollama env var: `export OLLAMA_HOST=0.0.0.0:11434`
- [ ] Restart all services
- [ ] Configure firewall to allow Python/Ollama
- [ ] Test from another device on WiFi
- [ ] (Optional) Add basic authentication
- [ ] (Optional) Set up SSH tunneling
- [ ] Share instructions with roommates

---

## 🔧 TROUBLESHOOTING

### Roommate can't connect?

1. **Check firewall:**
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   ```

2. **Verify service is listening on 0.0.0.0:**
   ```bash
   lsof -i :5001
   # Should show "0.0.0.0:5001" or "*:5001", NOT "127.0.0.1:5001"
   ```

3. **Ping your laptop:**
   ```bash
   # From roommate's laptop:
   ping 192.168.1.42
   ```

4. **Check WiFi isolation:**
   - Some routers have "AP isolation" or "client isolation" enabled
   - This prevents devices from talking to each other
   - Check router settings or ask network admin

5. **Try different port:**
   - Some routers block certain ports
   - Try 8080, 3000, or other common ports

---

## 🌐 BONUS: Raspberry Pi Remote Access

Based on the Raspberry Pi docs you linked, here's how to do similar things:

### SSH Access (Basic)
```bash
# On your laptop:
sudo systemsetup -setremotelogin on  # Enable SSH

# From roommate's laptop:
ssh your-username@192.168.1.42
```

### SCP File Transfer
```bash
# Roommate sends file to you:
scp document.pdf you@192.168.1.42:~/Desktop/

# You send file to roommate:
scp ~/Desktop/data.db roommate@192.168.1.50:~/
```

### VNC (Screen Sharing)
```bash
# macOS built-in:
System Preferences → Sharing → Screen Sharing (enable)

# Roommate connects via Finder:
# Go → Connect to Server → vnc://192.168.1.42
```

---

**Bottom line:** You CAN share Ollama and Flask with roommates, just need to:
1. Bind services to `0.0.0.0` instead of `127.0.0.1`
2. Configure firewall
3. Add authentication for security
4. Give roommates your local IP + port numbers

This is all LOCAL NETWORK - not exposed to the internet!
