# 📱 LAN Access Setup - Use Soulfra from Your Phone

This guide shows you how to access Soulfra (including chat with Ollama) from your phone on the same WiFi network.

## 🎯 Quick Start

### 1. Start Ollama for LAN Access

**Terminal 1:**
```bash
./start_ollama_lan.sh
```

This makes Ollama accessible from your phone at `http://192.168.1.74:11434` (or whatever your computer's IP is).

### 2. Start Flask for LAN Access

**Terminal 2:**
```bash
./start_flask_lan.sh
```

This makes the web app accessible from your phone at `http://192.168.1.74:5001`.

### 3. Access from Phone

1. **Connect your phone to the SAME WiFi network** as your computer
2. **Open browser on your phone**
3. **Go to** the URL shown in Terminal 2 (e.g., `http://192.168.1.74:5001`)
4. **Click "💬 Chat"** in the navigation
5. **Start chatting** with any of the 22 Ollama models!

---

## 📋 What Each Script Does

### `start_ollama_lan.sh`
- Starts Ollama bound to `0.0.0.0:11434` (all network interfaces)
- Makes Ollama accessible from phone
- Shows your local IP address
- **Run this FIRST in a separate terminal**

### `start_flask_lan.sh`
- Sets `OLLAMA_HOST=http://192.168.1.74:11434` (your IP)
- Starts Flask app
- Chat from phone will connect to Ollama on your computer
- **Run this SECOND in a separate terminal**

---

## 🔍 Troubleshooting

### Issue: Phone can't access `http://192.168.1.74:5001`

**Solutions:**
1. **Check WiFi**: Ensure phone and computer are on SAME network
2. **Check IP**: Run `./start_ollama_lan.sh` to see your actual IP (might not be 192.168.1.74)
3. **Check Firewall**:
   - **macOS**: System Preferences → Security & Privacy → Firewall → Allow incoming connections for Python
   - **Linux**: `sudo ufw allow 5001` and `sudo ufw allow 11434`
   - **Windows**: Windows Firewall → Allow apps → Python

### Issue: Chat doesn't work from phone

**Solutions:**
1. **Check Ollama is running**: Run `./start_ollama_lan.sh` FIRST
2. **Check Flask knows Ollama's IP**: Run `./start_flask_lan.sh` (it sets `OLLAMA_HOST` automatically)
3. **Test Ollama directly from phone**: Open `http://192.168.1.74:11434/api/tags` in phone browser - should show list of models
4. **Check firewall allows port 11434**: See firewall instructions above

### Issue: QR code doesn't work

**Explanation**: The QR code on the homepage is for Netflix-style pairing, which logs you in. After scanning and pairing:
1. Your computer will redirect to the workspace
2. Your phone will show "Paired successfully"
3. You can then navigate to `/chat` from the main navigation

**Alternative**: Just type the IP address directly in your phone browser instead of scanning QR.

---

## 🌐 Deployment Options

### Option 1: Same WiFi Network (Current Setup)
**Pros:**
- Simple setup
- No external services needed
- Works offline

**Cons:**
- Only works on same WiFi
- Computer must be running
- IP changes when you move networks

**Best for:** Development, testing, home use

---

### Option 2: ngrok (Internet Access)
**Pros:**
- Works from anywhere
- Can share with others
- Get a public URL

**Cons:**
- Requires ngrok account
- Free tier limited to 1 tunnel (need 2 for Flask + Ollama)
- Paid plan required for multiple tunnels ($10/month)

**Setup:**
```bash
# 1. Sign up at https://ngrok.com
# 2. Install authtoken
ngrok authtoken YOUR_AUTH_TOKEN

# 3. Start ngrok for Flask (Terminal 1)
ngrok http 5001

# 4. Start ngrok for Ollama (Terminal 2)
ngrok http 11434

# 5. Set environment variables (Terminal 3)
export BASE_URL=https://abc123.ngrok.io
export OLLAMA_HOST=https://xyz789.ngrok.io
python3 app.py
```

**Best for:** Testing from anywhere, sharing with friends

---

### Option 3: VPS/Cloud with Domain
**Pros:**
- Professional setup
- Always accessible
- Custom domain
- Scalable

**Cons:**
- Costs money ($5-20/month)
- Requires DevOps knowledge
- More complex setup

**Setup:**
```bash
# 1. Get a VPS (DigitalOcean, Linode, etc.)
# 2. Point domain to VPS (e.g., soulfra.yourdomain.com)
# 3. SSH into VPS
# 4. Install Ollama and models
# 5. Install Python dependencies
# 6. Set environment variables
export BASE_URL=https://soulfra.yourdomain.com
export OLLAMA_HOST=http://localhost:11434
# 7. Use systemd or supervisor to keep services running
# 8. Set up nginx reverse proxy with SSL
```

**Best for:** Production, serious projects, business use

---

## 📝 How It Works

### Current Configuration

When you run the scripts:

1. **config.py auto-detects your IP**: `192.168.1.74`
2. **BASE_URL**: `http://192.168.1.74:5001` (Flask auto-uses IP)
3. **OLLAMA_HOST**: Set by `start_flask_lan.sh` to `http://192.168.1.74:11434`

### What Happens When You Chat from Phone:

1. **Phone browser** → `http://192.168.1.74:5001/chat`
2. **You type message** → POST to `/api/chat/send`
3. **Flask receives message** → Calls `context_manager.py`
4. **Context manager** → Sends to Ollama at `http://192.168.1.74:11434/api/generate`
5. **Ollama responds** → Back through Flask → Back to your phone

### Why localhost Doesn't Work from Phone:

- `localhost` means "this device"
- From your phone's perspective, `localhost` = your phone, not your computer
- That's why we use the IP address (`192.168.1.74`)

---

## 🔒 Security Notes

### Development Mode (Current Setup):
- ⚠️ **DEFAULT SECRET_KEY** - Not secure for production
- ⚠️ **DEFAULT ADMIN_PASSWORD** - Change in production
- ⚠️ **No HTTPS** - Traffic not encrypted
- ⚠️ **Firewall open** - Make sure only trusted devices on WiFi

### For Production:
```bash
# Set secure environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export ADMIN_PASSWORD=your_secure_password
export BASE_URL=https://yourdomain.com

# Use HTTPS with SSL certificate
# Use environment variables for sensitive config
# Close firewall except for specific ports
# Use authentication for all sensitive routes
```

---

## 🧪 Testing the Setup

### Test 1: Can Phone Reach Flask?
```bash
# From phone browser:
http://192.168.1.74:5001/status
```
✅ **Expected**: Status page loads

### Test 2: Can Phone Reach Ollama?
```bash
# From phone browser:
http://192.168.1.74:11434/api/tags
```
✅ **Expected**: JSON list of Ollama models

### Test 3: Can Chat Work?
```bash
# From phone browser:
http://192.168.1.74:5001/chat
```
1. Register/login (or use as guest if tier 2+)
2. Type a message
3. Select a model
4. Click Send

✅ **Expected**: Ollama responds with AI-generated text

---

## 💡 Tips

### Faster Access on Phone:
1. **Bookmark the IP URL** on your phone for quick access
2. **Add to Home Screen** (iOS/Android) to make it feel like an app
3. **Use QR code** from homepage for quick pairing/login

### Better Performance:
1. **Use smaller models** (e.g., `mistral:7b` instead of `llama2:70b`) for faster responses
2. **Close other apps** running on your computer
3. **Use 5GHz WiFi** instead of 2.4GHz for faster speeds

### Multi-Device:
- You can access from **multiple devices** at once (phone, tablet, other computers)
- Each device gets its own session
- All chat to the same Ollama instance on your computer

---

## 📚 Next Steps

1. ✅ **Tested on phone?** Great! Now try different Ollama models
2. 🎨 **Want to customize?** Edit `chat.html` and `context_manager.py`
3. 🚀 **Ready for production?** Consider Option 3 (VPS/Cloud) above
4. 🤝 **Want to share?** Use ngrok (Option 2) to get a public URL

---

## 🆘 Still Having Issues?

1. **Check the terminal output** of both scripts for errors
2. **Run `python3 config.py`** to verify configuration
3. **Check firewall settings** (most common issue)
4. **Verify Ollama has models**: `ollama list`
5. **Check both services are running**:
   - Ollama: `curl http://localhost:11434/api/tags`
   - Flask: `curl http://localhost:5001/status`

---

Generated on 2025-12-28 by Claude Code
