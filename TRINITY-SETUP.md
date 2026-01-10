# Trinity Setup - Decentralized Soulfra

Your trinity: **Laptop + Phone 1 + Phone 2** → Self-sovereign publishing system

No GitHub/iCloud dependency. Peer-to-peer database sync. Phone as HTTP server.

---

## Part 1: Syncthing Setup (Database Sync)

### What is Syncthing?

- Open-source peer-to-peer file sync
- No central server (unlike iCloud/Dropbox)
- Works over local WiFi or internet
- End-to-end encrypted
- Syncs `soulfra.db` between all your devices

### Installation

#### Laptop (macOS)
```bash
brew install syncthing

# Start Syncthing
syncthing
```

Access dashboard: http://localhost:8384

#### Phone 1 & Phone 2 (iOS)
- Install **Möbius Sync** from App Store (Syncthing for iOS)
- Or use **Syncthing-Fork** on Android

#### Phone (Android)
```bash
# Install from F-Droid or Play Store
# Search: "Syncthing"
```

### Configuration

#### 1. Add Devices to Each Other

**On Laptop:**
1. Open http://localhost:8384
2. Go to "Actions" → "Show ID"
3. Copy your Device ID (looks like `ABCD-EFGH-1234-5678...`)

**On Phone:**
1. Open Möbius Sync
2. Tap "Devices" → "+"
3. Scan QR code from laptop OR paste Device ID
4. Name it "Laptop"

**Repeat in reverse** (add phone to laptop)

#### 2. Share soulfra.db Folder

**On Laptop:**
1. In Syncthing dashboard → "Add Folder"
2. **Folder Path**: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple`
3. **Folder Label**: `Soulfra`
4. **Folder ID**: `soulfra-db`
5. Go to "Sharing" tab
6. Check both phones
7. Click "Save"

**On Phones:**
1. Accept the folder share notification
2. Choose where to save (e.g., `/sdcard/Soulfra` on Android)
3. Enable "Watch for Changes"

#### 3. Test Sync

**On Laptop:**
```bash
# Add a test post
sqlite3 soulfra.db "INSERT INTO posts (title, slug, content, brand_id, user_id, published_at) VALUES ('Sync Test', 'sync-test-123', 'Testing database sync', 1, 1, datetime('now'))"
```

**On Phone:**
Wait ~30 seconds, then check:
```bash
# On Android (Termux)
sqlite3 /sdcard/Soulfra/soulfra.db "SELECT title FROM posts ORDER BY id DESC LIMIT 1"

# Should show: Sync Test
```

✅ **Now all devices have the same database in real-time**

---

## Part 2: Phone as HTTP Server

### Why?

- Serve your static sites from your phone
- No GitHub Pages needed
- Phone has an IP address on your network
- Can access from anywhere with Tailscale

### Option A: Android (Termux)

#### Install Termux
```bash
# Install from F-Droid (NOT Play Store - outdated)
# https://f-droid.org/en/packages/com.termux/
```

#### Setup Python HTTP Server
```bash
# In Termux
pkg update && pkg upgrade
pkg install python

# Navigate to synced folder
cd /sdcard/Soulfra/output/soulfra

# Serve on port 8000
python -m http.server 8000
```

**Access from any device on same WiFi:**
```
http://YOUR_PHONE_IP:8000
```

Find your phone's IP:
```bash
ip addr show wlan0 | grep "inet "
# Example: 192.168.1.100
```

### Option B: iOS (Pythonista)

#### Install Pythonista
- Install from App Store (paid app, ~$10)
- Built-in Python IDE with HTTP server

#### Setup
1. Open Pythonista
2. Create new script: `serve.py`
3. Paste this code:

```python
import SimpleHTTPServer
import SocketServer
import os

PORT = 8000
os.chdir('/var/mobile/Containers/Shared/AppGroup/YOUR_SYNCTHING_FOLDER/output/soulfra')

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)

print(f"Serving on port {PORT}")
httpd.serve_forever()
```

4. Run the script
5. Access from http://YOUR_IPHONE_IP:8000

### Option C: Dedicated Apps

#### Android
- **Tiny Web Server** (Play Store)
- **Simple HTTP Server** (F-Droid)

#### iOS
- **iSH Shell** (Alpine Linux on iOS)
- **WebServer** (Mocha HTTP server)

---

## Part 3: Tailscale (Access from Anywhere)

### Problem

Phone's IP changes when you leave WiFi (192.168.1.100 → gone)

### Solution: Tailscale

- Free VPN that creates permanent IPs for your devices
- Works anywhere (cellular, WiFi, anywhere)
- Your devices always have same IP on Tailscale network

### Setup

#### Install on All Devices

**Laptop:**
```bash
brew install tailscale
sudo tailscale up
```

**Phones:**
- Install Tailscale app from App Store / Play Store
- Sign in with same account

### Usage

**Your devices get permanent IPs:**
- Laptop: `100.100.100.1` (example)
- Phone 1: `100.100.100.2`
- Phone 2: `100.100.100.3`

**Access phone's website from anywhere:**
```
http://100.100.100.2:8000
```

Works even if:
- Phone is on cellular data
- You're in another country
- Phone's WiFi IP changed

---

## Part 4: DNS + Custom Domains

### Use Your Own Domains

You own: soulfra.com, soulfra.ai, soulfraapi.com

#### Point to Your Phone

**On your domain registrar (Namecheap, etc.):**

1. Go to DNS settings
2. Add A record:
   - **Host**: `@`
   - **Value**: `YOUR_TAILSCALE_IP` (e.g., `100.100.100.2`)
   - **TTL**: `1 minute`

3. Add CNAME for www:
   - **Host**: `www`
   - **Value**: `soulfra.com`

**Now:**
- `http://soulfra.com` → your phone
- Database synced between laptop + phones via Syncthing
- No GitHub Pages, no central authority

### Port Forwarding (If Not Using Tailscale)

**If on home WiFi without Tailscale:**

1. Log into your router (usually http://192.168.1.1)
2. Find "Port Forwarding" settings
3. Forward port `80` → your phone's local IP (192.168.1.100:8000)

**Now:**
- `http://YOUR_HOME_IP` → your phone
- But this only works from your home network

---

## Part 5: Publishing Workflow

### Old Way (Central)
```
Write post → Save to DB → Export → Git commit → Git push → GitHub Pages
```

### New Way (Decentralized)
```
Write post on laptop → Auto-syncs to phones via Syncthing → Phone serves it via HTTP
```

### Complete Example

**On Laptop:**
```bash
# Write a post
curl -X POST http://localhost:5001/api/voice-to-debate \
  -F "topic=Should we decentralize the web?" \
  -F "text=Centralized platforms control our data" \
  -F "brand=Soulfra"

# Export to static HTML
python3 export_static.py --brand Soulfra

# Cross-post everywhere
python3 publish_everywhere.py --latest --brand Soulfra
```

**Syncthing automatically syncs:**
- `soulfra.db` → Phone 1 + Phone 2 (database)
- `output/soulfra/` → Phone 1 + Phone 2 (static files)

**Phone serves the site:**
- Phone 1: `http://100.100.100.2:8000` (primary)
- Phone 2: `http://100.100.100.3:8000` (backup)
- Laptop: `http://localhost:5001/local-site/soulfra/` (dev)

---

## Part 6: PGP/GPG Signing (Prove Ownership)

### Why?

- Prove posts are from YOU
- Sign with private key (laptop)
- Anyone can verify with public key
- Works without laptop (backup keys on phones)

### Setup

#### 1. Generate GPG Key (Laptop)
```bash
# Install GPG
brew install gnupg

# Generate key
gpg --full-generate-key

# Choose:
# - RSA and RSA
# - 4096 bits
# - Key does not expire
# - Real name: Your Name
# - Email: you@soulfra.com
```

#### 2. Export Keys
```bash
# Export public key (shareable)
gpg --armor --export you@soulfra.com > soulfra-public.asc

# Export private key (SECRET - encrypted backup)
gpg --armor --export-secret-keys you@soulfra.com > soulfra-private.asc
```

#### 3. Backup to Phones

**Encrypted backup:**
```bash
# Encrypt private key with password
gpg --symmetric --armor soulfra-private.asc

# Creates: soulfra-private.asc.asc
# Copy this to phones via Syncthing
```

**On phones:**
- Store in password manager (1Password, Bitwarden)
- Or encrypted notes app

#### 4. Sign Posts

**Sign a post:**
```bash
# Get post content
sqlite3 soulfra.db "SELECT content FROM posts WHERE id=33" > post33.txt

# Sign it
gpg --clearsign post33.txt

# Creates: post33.txt.asc (signed version)
```

**Verify from anywhere (even without your laptop):**
```bash
# Someone else can verify
gpg --verify post33.txt.asc

# Output:
# gpg: Good signature from "Your Name <you@soulfra.com>"
```

#### 5. Git Commit Signing

**Configure Git:**
```bash
# Tell git to sign commits
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Find your key ID
gpg --list-secret-keys --keyid-format=long
# Look for: sec   rsa4096/ABCD1234EFGH5678
# Key ID: ABCD1234EFGH5678
```

**Now all commits are signed:**
```bash
git commit -m "Update post"
# Automatically signed with your GPG key
```

**GitHub shows verified badge:**
1. Upload public key to GitHub: Settings → SSH and GPG keys
2. All commits show ✅ Verified

---

## Part 7: Complete Trinity Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      YOUR TRINITY                        │
└─────────────────────────────────────────────────────────┘

         LAPTOP                 PHONE 1              PHONE 2
    (Primary Dev)         (Mobile Master)        (Verifier)
         │                      │                    │
         │◄─────Syncthing──────►│◄────Syncthing────►│
         │     (soulfra.db)     │    (soulfra.db)   │
         │                      │                    │
    ┌────▼────┐           ┌─────▼─────┐       ┌─────▼─────┐
    │ Flask   │           │  HTTP     │       │  HTTP     │
    │ Dev     │           │  Server   │       │  Server   │
    │ :5001   │           │  :8000    │       │  :8000    │
    └─────────┘           └───────────┘       └───────────┘
         │                      │                    │
         │                      │                    │
    Tailscale            Tailscale            Tailscale
    100.x.x.1            100.x.x.2            100.x.x.3
         │                      │                    │
         └──────────────────────┴────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   soulfra.com      │
                    │   (DNS → Phone 1)  │
                    └────────────────────┘
```

### Data Flow

1. **Write** post on laptop → `soulfra.db`
2. **Syncthing** syncs to phones (5-30 seconds)
3. **Export** to static HTML → `output/soulfra/`
4. **Syncthing** syncs HTML to phones
5. **Phone HTTP server** serves the site
6. **DNS** points soulfra.com → Phone 1's Tailscale IP
7. **Anyone** visits soulfra.com → loads from your phone

### Backup Strategy

- **Primary**: Laptop (development)
- **Live**: Phone 1 (public website)
- **Backup**: Phone 2 (redundancy)
- **Git**: GitHub (optional, for history)

### Failure Modes

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Laptop offline | ✅ Site still served from phones | Phones are independent |
| Phone 1 dies | ⚠️ Site down until DNS updated | Point DNS to Phone 2 |
| WiFi down | ✅ Works via Tailscale + cellular | Phones use mobile data |
| All offline | ❌ Site down | Can rebuild from Git history |
| Database corruption | ⚠️ Lose recent changes | Syncthing keeps file versions |

---

## Part 8: Quick Start

### First Time Setup (30 minutes)

```bash
# 1. Install Syncthing
brew install syncthing
syncthing &

# 2. Install on phones (App Store / F-Droid)
# 3. Pair devices (scan QR codes)
# 4. Share soulfra folder
# 5. Wait for initial sync (~10MB)

# 6. Test database sync
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts"
# On phone: same number

# 7. Start HTTP server on phone
# Termux: python -m http.server 8000
# Or use dedicated app

# 8. Visit from laptop
curl http://PHONE_IP:8000
# Should see: index.html

# 9. Install Tailscale (optional but recommended)
brew install tailscale
sudo tailscale up
# Install on phones

# 10. Update DNS (if you want soulfra.com → phone)
# A record: @ → YOUR_TAILSCALE_IP
```

### Daily Workflow

```bash
# Write a post (laptop)
python3 app.py  # Start Flask
# Use voice memo or manual post creation

# Export to static
python3 export_static.py --brand Soulfra

# Cross-post to all platforms
python3 publish_everywhere.py --latest

# That's it! Syncthing handles the rest
# Phones auto-serve updated site
```

---

## Part 9: Advanced

### Mesh CDN (All Devices Serve)

**Use DNS round-robin:**
```
soulfra.com:
  A → 100.100.100.1  (laptop)
  A → 100.100.100.2  (phone 1)
  A → 100.100.100.3  (phone 2)
```

Visitors get random device → load balancing

### IPFS Integration (Coming Soon)

Add to Trinity:
- **IPFS** on laptop publishes to decentralized network
- **ENS** domain: soulfra.eth → IPFS hash
- **Gateway**: soulfra.com → IPFS gateway

### Subscriber Sync

```bash
# Export subscribers
python3 manage_subscribers.py export
# → subscribers.csv

# Syncthing syncs to phones
# Import on phone (if needed)
python3 manage_subscribers.py import /sdcard/Soulfra/subscribers.csv
```

---

## Troubleshooting

### Syncthing Not Syncing

```bash
# Check status
curl http://localhost:8384/rest/system/status

# Rescan folder
curl -X POST http://localhost:8384/rest/db/scan?folder=soulfra-db

# Check for conflicts
ls -la | grep sync-conflict
```

### Phone Can't Be Reached

```bash
# Check Tailscale status
tailscale status

# Ping phone
ping 100.100.100.2

# Check HTTP server
curl -I http://100.100.100.2:8000
```

### Database Locked

```bash
# Close all connections
pkill -f "python.*app.py"
pkill -f "sqlite3"

# Check for lock
ls -la soulfra.db-shm soulfra.db-wal

# Force unlock (last resort)
sqlite3 soulfra.db "PRAGMA journal_mode=DELETE;"
```

---

## Summary

✅ **One database** → Synced between laptop + 2 phones via Syncthing
✅ **Phone HTTP server** → Serves static sites directly
✅ **Tailscale** → Permanent IPs, access from anywhere
✅ **DNS** → soulfra.com points to your phone
✅ **Cross-posting** → `publish_everywhere.py` → Substack, Medium, Email, WhatsApp, Signal
✅ **Subscribers** → `manage_subscribers.py` → One database, all platforms
✅ **PGP signing** → Prove authenticity without central authority

**No GitHub Pages needed. No central server. Self-sovereign.**
