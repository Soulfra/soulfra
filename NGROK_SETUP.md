# 🌐 Ngrok Setup - Share Your Practice Rooms Over the Internet

## What is Ngrok?

Ngrok creates a secure tunnel from the internet to your local development server. This lets you share your practice rooms with friends/family anywhere in the world, not just on your local WiFi.

**Without ngrok**: Only works on same WiFi (e.g., http://192.168.1.74:5001)
**With ngrok**: Works from anywhere (e.g., https://abc123.ngrok.io)

---

## Quick Setup (5 minutes)

### 1. Install Ngrok

**macOS**:
```bash
brew install ngrok
```

**Linux**:
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

**Windows**:
Download from https://ngrok.com/download

### 2. Create Free Ngrok Account

1. Go to https://dashboard.ngrok.com/signup
2. Sign up with email or GitHub
3. Verify your email

### 3. Get Your Auth Token

1. After signing in, go to https://dashboard.ngrok.com/get-started/your-authtoken
2. Copy your auth token (looks like: `2abc123def456ghi789jkl`)

### 4. Configure Ngrok

Run this command with YOUR auth token:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

Example:
```bash
ngrok config add-authtoken 2abc123def456ghi789jkl
```

You should see:
```
Authtoken saved to configuration file: /Users/yourname/.ngrok2/ngrok.yml
```

### 5. Start Ngrok Tunnel

Make sure your Flask app is running on port 5001, then run:
```bash
ngrok http 5001
```

You'll see:
```
Session Status                online
Account                       your@email.com
Version                       3.x.x
Region                        United States (us)
Forwarding                    https://abc123.ngrok.io -> http://localhost:5001
```

**Copy the `https://abc123.ngrok.io` URL** - this is your public URL!

---

## Using Ngrok with Practice Rooms

### Method 1: Manual URL Replacement

When you create a practice room, you'll get a URL like:
```
http://192.168.1.74:5001/practice/room/abc123
```

Replace the host with your ngrok URL:
```
https://abc123.ngrok.io/practice/room/abc123
```

Share this URL or create a QR code from it.

### Method 2: Environment Variable (Recommended)

Set the public URL in your environment:

```bash
export PUBLIC_URL=https://abc123.ngrok.io
```

Then restart your Flask app. The app will use this URL for QR codes and sharing.

### Method 3: Run Both Together

Create a script to run both at once:

**run_with_ngrok.sh**:
```bash
#!/bin/bash

# Start Flask in background
python3 app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Start ngrok
ngrok http 5001

# When ngrok stops, kill Flask
kill $FLASK_PID
```

Make it executable:
```bash
chmod +x run_with_ngrok.sh
./run_with_ngrok.sh
```

---

## Testing Your Setup

### 1. Create a Practice Room

Visit in your browser:
```
https://YOUR_NGROK_URL/practice/create
```

Example:
```
https://abc123.ngrok.io/practice/create
```

### 2. Fill Out the Form

- Room Topic: "Test from Phone"
- Max Participants: 10
- Duration: 1 hour

### 3. Get the Room URL

After creating, you'll get a URL like:
```
https://abc123.ngrok.io/practice/room/xyz789
```

### 4. Test from Your Phone

**Important**: You can now test from anywhere:
- Your phone on cellular data (not WiFi)
- A friend's phone
- A different city/state

Open the URL in your phone's browser or scan the QR code.

---

## Important Notes

### Free Plan Limitations

- ✅ HTTPS tunnels
- ✅ Unlimited requests
- ✅ Works anywhere
- ⚠️ URL changes each time you restart ngrok
- ⚠️ Session expires after 2 hours (need to restart)

### Paid Plan Benefits ($8/month)

- 🎯 Custom subdomain (e.g., `myapp.ngrok.io` - stays the same)
- 🎯 No session expiration
- 🎯 More simultaneous tunnels

### Security

- ✅ Ngrok uses HTTPS (encrypted)
- ✅ Your Flask app runs locally (you control it)
- ⚠️ Anyone with the URL can access your room
- ⚠️ Don't share admin URLs publicly

---

## Troubleshooting

### "ERR_NGROK_108: Authentication failed"

You haven't set up your auth token. Run:
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### "tunnel session failed: your account is limited to 1 tunnel"

You're already running ngrok somewhere else. Find and stop it:
```bash
pkill ngrok
```

Then start again.

### "Failed to complete tunnel connection"

Your Flask app isn't running on port 5001. Check:
```bash
lsof -i:5001
```

If nothing shows, start Flask:
```bash
python3 app.py
```

### URL Changes Every Time

This is normal for free plan. Upgrade to paid for custom subdomain, or:
- Save the URL each time you start
- Share the URL via text/email each session

### "This site can't be reached"

Ngrok tunnel is down. Check your terminal where ngrok is running. You might need to restart it.

---

## Alternative: Use Localtunnel (Free Alternative)

If you don't want to sign up for ngrok:

```bash
npm install -g localtunnel
lt --port 5001
```

You'll get a URL like: https://unusual-cat-12.loca.lt

---

## Next Steps

✅ Ngrok is set up
✅ You can share rooms over internet

**What's next?**

1. **For development/testing**: Keep using ngrok
2. **For production**: Deploy to Render/Railway (see DEPLOYMENT.md)
3. **For custom domain**: Upgrade ngrok or deploy to production

---

## Quick Reference

```bash
# Start ngrok
ngrok http 5001

# Start ngrok with custom subdomain (paid)
ngrok http 5001 --domain=myapp.ngrok.io

# View ngrok web interface
http://localhost:4040

# Stop ngrok
Ctrl+C in ngrok terminal
```

---

**You're ready to share practice rooms with anyone, anywhere!** 🚀
