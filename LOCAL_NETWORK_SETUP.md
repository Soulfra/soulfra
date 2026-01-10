# Self-Host Soulfra on Your Laptop (Friends Can Join!)

**You asked:** "how can we self-host on my laptop my website and my friends can join it and their codes work/get used somehow with the logins or soulfra?"

**Answer:** Here are 3 ways to do exactly that.

---

## Option 1: Local WiFi Network (Easiest)

**Best for:** Roommates, friends at your house, same WiFi

### How It Works
- Flask runs on YOUR laptop
- Friends connect to your laptop's IP address
- Only works if everyone is on same WiFi
- **100% free, 100% private**

### Setup Steps

1. **Get your laptop's local IP address:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
   ```
   Example output: `192.168.1.87`

2. **Start Flask:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 app.py
   ```

   You should see:
   ```
   * Running on http://0.0.0.0:5001
   * Running on http://127.0.0.1:5001
   * Running on http://192.168.1.87:5001
   ```

3. **Share URL with friends:**
   - **Your URL**: `http://192.168.1.87:5001`
   - Friends type this into their browser
   - Works on phones, tablets, laptops

### Friends Access It Like This

**On their phone/laptop:**
```
http://192.168.1.87:5001
```

**They can use:**
- `/` - Homepage
- `/signup/professional` - Create account
- `/professional/inbox` - Check messages
- All routes work exactly like your local version

### Pros
- ✅ Instant, no setup
- ✅ Free forever
- ✅ No internet needed
- ✅ Full privacy
- ✅ Fast (local network)

### Cons
- ❌ Friends must be on same WiFi
- ❌ Stops working when you close laptop
- ❌ Can't access from outside your house

---

## Option 2: Ngrok Tunnel (Internet Access)

**Best for:** Friends anywhere in the world, temporary sharing

### How It Works
- Ngrok creates a tunnel from internet → your laptop
- Friends get a URL like `https://abc123.ngrok.io`
- Works from anywhere
- **Free tier = 8 hours/day, URL changes each restart**

### Setup Steps

1. **Install ngrok:**
   ```bash
   brew install ngrok

   # OR download from https://ngrok.com/download
   ```

2. **Sign up for ngrok** (free):
   - Go to: https://dashboard.ngrok.com/signup
   - Get your auth token

3. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

4. **Start Flask:**
   ```bash
   python3 app.py
   ```

5. **In another terminal, start ngrok:**
   ```bash
   ngrok http 5001
   ```

6. **You'll see:**
   ```
   Forwarding  https://abc123-def456.ngrok-free.app -> http://localhost:5001
   ```

7. **Share that URL with friends:**
   - `https://abc123-def456.ngrok-free.app`
   - Anyone can access it

### Friends Access It Like This

**On their browser anywhere:**
```
https://abc123-def456.ngrok-free.app
```

**They can:**
- Create accounts
- Login
- Use all features
- Same database as you

### Pros
- ✅ Works from anywhere (internet)
- ✅ Free tier available
- ✅ HTTPS (secure)
- ✅ Easy setup

### Cons
- ❌ URL changes every time you restart
- ❌ Free tier = 8 hours/day max
- ❌ Ngrok banner on pages (free tier)
- ❌ Stops when you close laptop

### Upgrading Ngrok

**Free tier limits:**
- 1 tunnel at a time
- 40 connections/minute
- Random subdomain

**Paid ($10/month):**
- Custom subdomain: `soulfra.ngrok.app`
- No banner
- Unlimited hours

---

## Option 3: Cloudflare Tunnel (Permanent URL)

**Best for:** Permanent deployment, custom domain, 24/7 access

### How It Works
- Cloudflare Tunnel connects your laptop to their network
- You get a permanent URL: `soulfra.yourdomain.com`
- Works from anywhere
- **100% free (Cloudflare Tunnel is free!)**
- Can use your own domain

### Setup Steps

1. **Install cloudflared:**
   ```bash
   brew install cloudflare/cloudflare/cloudflared
   ```

2. **Login to Cloudflare:**
   ```bash
   cloudflared tunnel login
   ```
   (Opens browser, authenticate with your Cloudflare account)

3. **Create a tunnel:**
   ```bash
   cloudflared tunnel create soulfra-laptop
   ```

   You'll get a UUID: `abc123-def456-ghi789`

4. **Create config file:**
   ```bash
   nano ~/.cloudflared/config.yml
   ```

   Add:
   ```yaml
   tunnel: abc123-def456-ghi789
   credentials-file: /Users/matthewmauer/.cloudflared/abc123-def456-ghi789.json

   ingress:
     - hostname: soulfra.yourdomain.com
       service: http://localhost:5001
     - service: http_status:404
   ```

5. **Point DNS to tunnel:**
   ```bash
   cloudflared tunnel route dns soulfra-laptop soulfra.yourdomain.com
   ```

6. **Start Flask:**
   ```bash
   python3 app.py
   ```

7. **Start tunnel:**
   ```bash
   cloudflared tunnel run soulfra-laptop
   ```

8. **Access at:**
   - `https://soulfra.yourdomain.com`

### Friends Access It Like This

**On their browser:**
```
https://soulfra.yourdomain.com
```

**Permanent access** - URL never changes!

### Pros
- ✅ Free forever
- ✅ Permanent URL
- ✅ Custom domain
- ✅ HTTPS (secure)
- ✅ No bandwidth limits
- ✅ DDoS protection

### Cons
- ❌ Requires domain name ($12/year)
- ❌ More complex setup
- ❌ Stops when you close laptop
- ❌ Need to keep tunnel running

### Keep Tunnel Running 24/7

**Run as background service:**

```bash
# Install as systemd service (Mac)
sudo cloudflared service install

# Start service
sudo launchctl load /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

Now tunnel runs even when you're not logged in!

---

## Comparison Table

| Feature | WiFi Only | Ngrok | Cloudflare |
|---------|-----------|-------|------------|
| **Free?** | ✅ Yes | ✅ (8hr/day) | ✅ Yes |
| **Internet access?** | ❌ No | ✅ Yes | ✅ Yes |
| **Custom domain?** | ❌ No | 💰 Paid | ✅ Yes |
| **Permanent URL?** | ✅ Yes (local IP) | ❌ No | ✅ Yes |
| **Setup time** | 30 seconds | 2 minutes | 10 minutes |
| **Best for** | Roommates | Quick demos | Permanent |

---

## How Logins Work (Multi-User)

**All 3 options use the SAME database:**
- SQLite file: `soulfra.db`
- Location: Your laptop
- **Shared across all users**

### When a friend creates an account:

1. Friend visits your URL (WiFi / Ngrok / Cloudflare)
2. Clicks "Sign Up"
3. Enters email/password
4. Account saved to YOUR laptop's database
5. They can login from any device
6. Same account works across all domains

### Important: Database is on YOUR Laptop

- All users share YOUR database
- If you close laptop, everyone loses access
- Database file: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db`

**To make it permanent:**
- Keep laptop running 24/7, OR
- Move database to a VPS (see `PRODUCTION_DEPLOYMENT.md`)

---

## How Friends Can Add Their Code

**Option A: Git Workflow (Recommended)**

1. **You push code to GitHub:**
   ```bash
   git add .
   git commit -m "Added feature"
   git push origin main
   ```

2. **Friend clones repo:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/soulfra-simple.git
   cd soulfra-simple
   ```

3. **Friend creates branch:**
   ```bash
   git checkout -b friend-feature
   ```

4. **Friend adds their route:**
   ```python
   # In app.py or new file
   @app.route('/friend-feature')
   def friend_feature():
       return "My code!"
   ```

5. **Friend pushes:**
   ```bash
   git add .
   git commit -m "Added my feature"
   git push origin friend-feature
   ```

6. **You merge on GitHub:**
   - Review pull request
   - Merge to main
   - Restart Flask

**Option B: Direct Access (Advanced)**

Give friend SSH access to your laptop:
```bash
ssh friend@YOUR_LAPTOP_IP
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
# Edit app.py
# Restart Flask
```

**Option C: Plugin System (Future)**

Create a `plugins/` folder:
```python
# plugins/friend_routes.py
from flask import Blueprint

friend_bp = Blueprint('friend', __name__)

@friend_bp.route('/friend-feature')
def friend_feature():
    return "My feature!"

# In app.py:
from plugins.friend_routes import friend_bp
app.register_blueprint(friend_bp)
```

---

## Quick Start Commands

### Method 1: WiFi Only
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py

# Get your IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Share: http://YOUR_IP:5001
```

### Method 2: Ngrok
```bash
# Terminal 1
python3 app.py

# Terminal 2
ngrok http 5001

# Share the https://xxx.ngrok.io URL
```

### Method 3: Cloudflare
```bash
# Terminal 1
python3 app.py

# Terminal 2
cloudflared tunnel run soulfra-laptop

# Share: https://soulfra.yourdomain.com
```

---

## Troubleshooting

### "Connection refused" error

**Cause:** Flask not running or wrong port

**Fix:**
```bash
ps aux | grep "python3 app.py"  # Check if running
lsof -i :5001  # Check what's on port 5001
python3 app.py  # Restart Flask
```

### Friends can't access (WiFi method)

**Cause:** Firewall blocking connections

**Fix (Mac):**
1. System Preferences → Security & Privacy → Firewall
2. Click lock, disable firewall temporarily
3. Or add Python to allowed apps

### Ngrok URL changes every restart

**Cause:** Free tier uses random URLs

**Fix:**
- Upgrade to paid plan ($10/month) for custom subdomain
- OR use Cloudflare Tunnel (free + custom domain)

### Database permissions error

**Cause:** Multiple users writing to SQLite simultaneously

**Fix:**
```python
# In database.py, add connection timeout
conn = sqlite3.connect('soulfra.db', timeout=30)
```

---

## Next Steps

1. **Choose your method** (WiFi / Ngrok / Cloudflare)
2. **Start Flask** with commands above
3. **Share URL** with friends
4. **Test login** - create account, verify it works
5. **Add features** - friends can contribute code

**Need help?** See:
- `SIMPLE_README.md` - What this project is
- `COLLABORATION_GUIDE.md` - How friends can contribute
- `PRODUCTION_DEPLOYMENT.md` - 24/7 deployment to VPS

---

**You're self-hosting now!** Your laptop = your server. 🚀
