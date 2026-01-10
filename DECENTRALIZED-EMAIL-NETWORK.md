# Decentralized Ollama via Email - The DIY Network

**Use your own hardware - no cloud needed!**

Turn old iPhones, routers, Raspberry Pis, SSDs into a resilient AI network.

Like spam email chains but actually useful.

---

## The Vision

```
            GitHub Pages (Free)
                   ↓
            User sends email
                   ↓
       ┌───────────┴───────────┐
       │   Email Network       │
       │   (Your Hardware)     │
       └───────────┬───────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐    ┌────────┐    ┌────────┐
│ Mac    │    │iPhone  │    │  Pi    │
│Ollama  │    │Relay   │    │Backup  │
└────────┘    └────────┘    └────────┘

Whoever is online processes it!
```

**Cost**: $0 (use your existing email + hardware)

**Reliability**: As long as ONE device is on, it works

**Privacy**: Your infrastructure, your data

---

## What You Need

### Required

1. **Email account** (Gmail, any SMTP)
2. **At least 1 device** running the node script
3. **Ollama** on at least 1 device

### Optional (for redundancy)

- Multiple devices running nodes
- Old iPhones (via Termux)
- Raspberry Pi
- Old routers (with Python)
- External SSDs (for storage)

---

## Setup (15 Minutes)

### Step 1: Create Shared Email (5 min)

1. **Create dedicated Gmail**:
   - Go to: https://accounts.google.com/signup
   - Email: `ollama@yourdomain.com` (or any)
   - Password: Strong password

2. **Enable App Passwords**:
   - Go to Google Account → Security
   - Enable 2-Step Verification
   - App Passwords → Mail → Generate
   - Copy the 16-character password

3. **Save credentials**:
   ```bash
   export OLLAMA_EMAIL="ollama@yourdomain.com"
   export OLLAMA_PASSWORD="your-16-char-app-password"
   ```

---

### Step 2: Run Node on Your Mac (5 min)

1. **Install dependencies**:
   ```bash
   pip install requests
   ```

2. **Start the node**:
   ```bash
   python3 ollama_email_node.py \
     --email ollama@yourdomain.com \
     --password YOUR_APP_PASSWORD \
     --node-name "my-mac"
   ```

3. **You should see**:
   ```
   ╔═══════════════════════════════════╗
   ║   OLLAMA EMAIL NODE              ║
   ╚═══════════════════════════════════╝

   Node Name:     my-mac
   Ollama Status: ✅ Online

   Waiting for requests...
   ```

---

### Step 3: Deploy Frontend to GitHub Pages (5 min)

1. **Edit `email-ollama-chat.html`**:
   - Replace `ollama@yourdomain.com` with your actual email
   - Line 241: `const NODE_EMAIL = 'ollama@yourdomain.com';`

2. **Push to GitHub**:
   ```bash
   cp email-ollama-chat.html index.html
   git add index.html
   git commit -m "Add decentralized Ollama chat"
   git push
   ```

3. **Enable GitHub Pages**:
   - Repo Settings → Pages
   - Source: `main` branch
   - Save

4. **Visit your page**:
   - `https://YOUR_USERNAME.github.io/repo-name/`

---

## How to Use

1. **Visit your GitHub Pages URL**
2. **Enter**:
   - Your email (for response)
   - API key (from faucet)
   - Your question

3. **Click "Send Request"**
   - Opens your email client
   - Pre-filled message
   - Send it!

4. **Wait 30-60 seconds**
   - Check your inbox
   - AI response arrives via email!

---

## Add More Nodes (Optional)

The more devices, the better redundancy!

### Add Old iPhone Node

1. **Install Termux** (from F-Droid on Android, or iSH on iOS)

2. **Install Python**:
   ```bash
   pkg install python
   pip install requests
   ```

3. **Download node script**:
   ```bash
   curl -O https://raw.githubusercontent.com/YOUR/repo/ollama_email_node.py
   ```

4. **Run it**:
   ```bash
   python ollama_email_node.py \
     --email ollama@yourdomain.com \
     --password YOUR_PASSWORD \
     --node-name "iphone-backup" \
     --ollama-url "http://your-mac-ip:11434"
   ```

   *Note: iPhone can't run Ollama, but it can relay to your Mac's Ollama!*

---

### Add Raspberry Pi Node

1. **Install Ollama on Pi**:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ollama pull llama3
   ```

2. **Install dependencies**:
   ```bash
   sudo apt install python3-pip
   pip3 install requests
   ```

3. **Run node**:
   ```bash
   python3 ollama_email_node.py \
     --email ollama@yourdomain.com \
     --password YOUR_PASSWORD \
     --node-name "pi-node"
   ```

---

### Add Old Router Node

If your router supports Python (DD-WRT, OpenWrt):

1. **SSH into router**:
   ```bash
   ssh root@192.168.1.1
   ```

2. **Install Python** (via opkg):
   ```bash
   opkg update
   opkg install python3
   ```

3. **Run node** (as relay):
   ```bash
   python3 ollama_email_node.py \
     --email ollama@yourdomain.com \
     --password YOUR_PASSWORD \
     --node-name "router-relay" \
     --ollama-url "http://192.168.1.100:11434"  # Your Mac IP
   ```

---

## How the Email Network Works

### Request Flow

```
1. User fills form on GitHub Pages
   └─ Opens mailto: link

2. User's email client sends to ollama@yourdomain.com
   Subject: [OLLAMA_REQUEST] sk_github_user_abc123
   Body: What is consciousness?

3. ALL nodes check inbox (every 30 seconds)
   └─ First one to see it processes it

4. Processing node:
   ✓ Checks Ollama is available
   ✓ Sends prompt to local Ollama
   ✓ Gets AI response
   ✓ Sends email back to user
   ✓ Marks request as processed

5. User receives response (30-60 seconds)
```

---

### Redundancy Example

```
3 nodes running:
- Mac (has Ollama) ← Primary
- iPhone (relay to Mac) ← Backup
- Pi (has Ollama) ← Backup

Scenario 1: Mac is on
  → Mac processes request (fastest)

Scenario 2: Mac is off
  → iPhone sees request, relays to Mac... fails
  → Pi processes request instead ✅

Scenario 3: All offline
  → Email waits in inbox
  → First node to come online processes it
```

Like spam email - resilient by design!

---

## Advanced Features

### Load Balancing

Nodes can report their status:

```python
# In ollama_email_node.py, add:

def report_status():
    """Send status email every 5 minutes"""
    subject = "[NODE_STATUS] my-mac"
    body = json.dumps({
        'node': 'my-mac',
        'ollama': 'online',
        'load': psutil.cpu_percent(),
        'timestamp': time.time()
    })
    send_email(subject, body)
```

Frontend can read these and route to least-busy node.

---

### Storage Node

Use external SSD to cache requests/responses:

```python
# Storage node (no Ollama)
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_PASSWORD \
  --node-name "ssd-storage" \
  --storage-only  # Flag to only archive, not process
```

Archives all requests/responses to disk.

---

### Multi-Model Support

Add model selection to email subject:

```
Subject: [OLLAMA_REQUEST] sk_key_abc123 model:llama3
Subject: [OLLAMA_REQUEST] sk_key_abc123 model:mistral
```

Node parses and uses specified model.

---

## Advantages

| Feature | Email Network | ngrok/Cloud |
|---------|--------------|-------------|
| **Cost** | $0 | $8+/month |
| **Setup** | 15 min | 1 hour+ |
| **Reliability** | Multi-device | Single point |
| **Privacy** | Your hardware | Cloud servers |
| **Offline** | Works (queued) | Fails |
| **Scale** | Add devices | Pay more |
| **Old hardware** | Reuse it! | Useless |

---

## Limitations

1. **Latency**: 30-60 seconds (email delay)
2. **Email limits**: Gmail = 500 emails/day (500 requests/day)
3. **No streaming**: Responses come as complete emails
4. **Manual relay**: iPhone can't run Ollama (needs relay)

---

## Use Cases

### 1. Home AI Network

- Mac runs Ollama (main)
- Pi runs Ollama (backup)
- iPhone relays when away
- Router archives all requests

**Result**: AI always available, even if Mac sleeps!

---

### 2. Multi-Location Nodes

- Node at home
- Node at work
- Node at friend's house

**Result**: Distributed network across locations!

---

### 3. Old Hardware Revival

- 5 old iPhones = 5 relay nodes
- Old router = email forwarder
- External SSD = request archive

**Result**: Junk drawer → AI network!

---

## Troubleshooting

### "Node not processing requests"

**Check**:
```bash
# Is Ollama running?
curl http://localhost:11434/api/tags

# Is node script running?
ps aux | grep ollama_email_node

# Can it connect to email?
python3 -c "
import imaplib
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('ollama@yourdomain.com', 'password')
print('✅ Email connection works!')
"
```

---

### "Response not arriving"

**Check**:
1. Node logs (did it process?)
2. Spam folder
3. Email quota (Gmail = 500/day)

---

### "Multiple nodes processing same request"

**Expected behavior!** Email is eventually consistent.

**Mitigation**:
- First node marks as read
- Others skip read emails
- At most 1-2 duplicate responses

---

## Summary

**What you built**:
- Decentralized AI network
- Uses email as transport
- Works on ANY hardware
- $0 cost
- Resilient like spam

**Deployment**:
- 1 HTML file → GitHub Pages
- 1 Python script → Your devices
- 1 email account → Communication layer

**Result**: Truly decentralized AI that you control!

---

## Files Created

1. **`ollama_email_node.py`** - The node script (run on any device)
2. **`email-ollama-chat.html`** - Frontend (deploy to GitHub Pages)
3. **`DECENTRALIZED-EMAIL-NETWORK.md`** - This guide

---

## Quick Start

```bash
# Terminal 1: Start node on Mac
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD

# Terminal 2: Start node on Pi (optional)
ssh pi@raspberry.local
python3 ollama_email_node.py \
  --email ollama@yourdomain.com \
  --password YOUR_APP_PASSWORD

# Then:
# 1. Deploy email-ollama-chat.html to GitHub Pages
# 2. Visit your page
# 3. Send a request
# 4. Check your email for response!
```

---

**Welcome to the decentralized future! 🌐**

No cloud. No subscriptions. Just your hardware and email.

Like the early internet but for AI.
