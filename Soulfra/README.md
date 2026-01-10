# Soulfra Triple Domain System

**Created:** December 31, 2024
**Purpose:** QR-based account creation with AI chat across 3 domains

## What You Built

A complete triple-domain authentication and AI chat system:

```
┌─────────────────────┐
│   soulfra.com       │  ← Static site (GitHub Pages - FREE)
│   Landing page      │     Shows QR code
│                     │
└──────────┬──────────┘
           │ QR scan →
           ↓
┌─────────────────────┐
│  soulfraapi.com     │  ← Flask API (Laptop $0 / DigitalOcean $5/mo)
│  Account Creation   │     Creates user + session token
│  SQLite database    │     Redirects to soulfra.ai
│                     │
└──────────┬──────────┘
           │ Redirect with token →
           ↓
┌─────────────────────┐
│   soulfra.ai        │  ← Flask app (Laptop $0 / DigitalOcean $5/mo)
│   AI Chat           │     Chat interface
│   Ollama integration│     Validates session
└─────────────────────┘
```

## Folder Structure

```
soulfra/
├── README.md                   ← This file
├── generate-qr.py              ← QR code generator
├── START-ALL.sh                ← Start all 3 services
├── STOP-ALL.sh                 ← Stop all services
├── TEST-FLOW.sh                ← Test the triple QR flow
├── EXPOSE-TO-IPHONE.sh         ← Get URLs for iPhone testing
│
├── Soulfra.com/                ← Domain 1: Static landing page
│   ├── index.html              ← Landing page
│   ├── style.css               ← Styling
│   ├── qr-code.png             ← QR code (generated)
│   └── README.md               ← Deployment guide
│
├── Soulfraapi.com/             ← Domain 2: Account creation API
│   ├── app.py                  ← Flask API server
│   ├── requirements.txt        ← Python dependencies
│   ├── soulfraapi.db           ← SQLite database (auto-created)
│   └── README.md               ← API documentation
│
└── Soulfra.ai/                 ← Domain 3: AI chat interface
    ├── app.py                  ← Flask chat server
    ├── templates/
    │   └── chat.html           ← Chat UI
    ├── requirements.txt        ← Python dependencies
    └── README.md               ← Setup guide
```

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd Soulfraapi.com && pip3 install -r requirements.txt && cd ..
cd Soulfra.ai && pip3 install -r requirements.txt && cd ..
pip3 install qrcode[pil]
```

### 2. Generate QR Code

```bash
python3 generate-qr.py
```

### 3. Start Ollama

```bash
ollama serve
ollama pull llama3.2
```

### 4. Start All Services

```bash
bash START-ALL.sh
```

This starts:
- soulfra.com on port 8001
- soulfraapi.com on port 5002
- soulfra.ai on port 5003

### 5. Test the Flow

```bash
bash TEST-FLOW.sh
```

Or test manually:

1. Visit: http://localhost:8001 (landing page)
2. Simulate QR scan: `curl -L http://localhost:5002/qr-signup?ref=test`
3. Copy redirect URL and paste in browser
4. Chat interface should load!

## The Triple QR Flow

### Step 1: User Visits soulfra.com

**URL:** http://localhost:8001

User sees:
- Landing page
- QR code
- "Scan to create account"

QR code encodes: `http://localhost:5002/qr-signup?ref=landing`

### Step 2: User Scans QR with iPhone

iPhone camera opens: `http://localhost:5002/qr-signup?ref=landing`

**soulfraapi.com** receives request:
1. Creates new user account in SQLite
2. Generates random username (e.g., "CoolSoul456")
3. Creates session token (32 random bytes, urlsafe)
4. Stores in sessions table with 24-hour expiry
5. Redirects to: `http://localhost:5003/?session=TOKEN123`

### Step 3: User Lands on soulfra.ai

**soulfra.ai** receives session token:
1. Validates token with soulfraapi.com API
2. If valid → show chat interface
3. User can now chat with Ollama AI
4. All messages sent with session token

## API Endpoints

### soulfraapi.com (Port 5002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/qr-signup` | GET | Create account from QR scan, redirect to soulfra.ai |
| `/validate-session` | POST | Validate session token |
| `/account/<user_id>` | GET | Get account info |
| `/stats` | GET | API statistics |

**Example QR signup:**
```bash
curl -L http://localhost:5002/qr-signup?ref=test
# Redirects to: http://localhost:5003/?session=abc123...
```

**Example session validation:**
```bash
curl -X POST http://localhost:5002/validate-session \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN"}'
```

### soulfra.ai (Port 5003)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | Chat interface (requires ?session=TOKEN) |
| `/api/chat` | POST | Send message to Ollama |

**Example chat:**
```bash
curl -X POST http://localhost:5003/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!", "session":"YOUR_TOKEN"}'
```

## Database Schema

**soulfraapi.com SQLite database:**

### `users` table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ref_source TEXT,  -- 'landing', 'qr', 'test'
    is_active BOOLEAN DEFAULT 1
);
```

### `sessions` table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,  -- 24 hours from creation
    device_fingerprint TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Testing on iPhone

### Option 1: Same WiFi Network (Simplest)

```bash
bash EXPOSE-TO-IPHONE.sh
```

This will show your local IP (e.g., 192.168.1.100).

Update QR code:
1. Edit `generate-qr.py`
2. Change `LOCALHOST_URL` to `http://192.168.1.100:5002/qr-signup?ref=landing`
3. Run `python3 generate-qr.py`

Now iPhone can scan the QR code!

### Option 2: ngrok (Works Anywhere)

```bash
# Install ngrok
brew install ngrok

# Terminal 1: Expose soulfraapi.com
ngrok http 5002
# Copy the URL: https://abc123.ngrok.io

# Terminal 2: Expose soulfra.ai
ngrok http 5003
# Copy the URL: https://xyz789.ngrok.io
```

Update services:
1. Update QR code: `generate-qr.py` → `https://abc123.ngrok.io/qr-signup?ref=landing`
2. Update API redirect: `export SOULFRA_AI_URL=https://xyz789.ngrok.io`
3. Restart services: `bash STOP-ALL.sh && bash START-ALL.sh`

## Deployment to Production

### soulfra.com → GitHub Pages (FREE)

```bash
cd Soulfra.com
git init
git add .
git commit -m "Deploy Soulfra landing page"
gh repo create soulfra-com --public --source=. --push

# Enable Pages in repo settings
gh browse
# Settings → Pages → Source: main branch
```

Live at: `https://<username>.github.io/soulfra-com`

### soulfraapi.com → DigitalOcean ($5/month)

```bash
# Create droplet
# SSH into droplet
git clone <your-repo>
cd soulfra/Soulfraapi.com
pip3 install -r requirements.txt

# Run with production settings
export SOULFRA_AI_URL=https://soulfra.ai
python3 app.py

# Point DNS: soulfraapi.com → droplet IP
```

### soulfra.ai → DigitalOcean ($5/month)

```bash
# Same droplet as API (different port) OR separate droplet
cd ../Soulfra.ai
pip3 install -r requirements.txt

# Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2

# Run
export SOULFRA_API_URL=https://soulfraapi.com
python3 app.py

# Point DNS: soulfra.ai → droplet IP
```

## Cost Breakdown

| Service | Hosting | Cost |
|---------|---------|------|
| **soulfra.com** | GitHub Pages | $0/month |
| **soulfraapi.com** | Laptop | $0/month |
| **soulfra.ai** | Laptop | $0/month |
| **Custom domains** | Optional | $10-15/year each |
| **TOTAL (laptop)** | - | **$0-45/year** |

Or production:

| Service | Hosting | Cost |
|---------|---------|------|
| **soulfra.com** | GitHub Pages | $0/month |
| **soulfraapi.com** | DigitalOcean | $5/month |
| **soulfra.ai** | DigitalOcean (same droplet) | $0/month |
| **Custom domains** | Optional | $10-15/year each |
| **TOTAL (production)** | - | **$60-105/year** |

## Helper Scripts

### `generate-qr.py`
Generates QR code pointing to soulfraapi.com/qr-signup

```bash
python3 generate-qr.py           # Localhost
python3 generate-qr.py --prod    # Production
```

### `START-ALL.sh`
Starts all three services in background

```bash
bash START-ALL.sh
```

Creates logs in `logs/` directory. Saves PIDs to `.pids` file.

### `STOP-ALL.sh`
Stops all services

```bash
bash STOP-ALL.sh
```

### `TEST-FLOW.sh`
Tests the complete triple QR flow

```bash
bash TEST-FLOW.sh
```

Checks:
- ✅ soulfra.com running
- ✅ soulfraapi.com running
- ✅ soulfra.ai running
- ✅ Ollama running (optional)
- ✅ Account creation works
- ✅ Session validation works

### `EXPOSE-TO-IPHONE.sh`
Get URLs for iPhone testing

```bash
bash EXPOSE-TO-IPHONE.sh
```

Shows local IP and ngrok instructions.

## Environment Variables

### soulfraapi.com

```bash
# Port (default: 5002)
export PORT=5002

# Where to redirect after signup
export SOULFRA_AI_URL=http://localhost:5003

# Session expiry in hours (default: 24)
export SESSION_EXPIRY_HOURS=24
```

### soulfra.ai

```bash
# Port (default: 5003)
export PORT=5003

# Ollama URL (default: http://127.0.0.1:11434)
export OLLAMA_URL=http://127.0.0.1:11434

# API URL for session validation
export SOULFRA_API_URL=http://localhost:5002

# Ollama model (default: llama3.2)
export OLLAMA_MODEL=llama3.2
```

## Troubleshooting

### "Services not running"
```bash
bash START-ALL.sh
```

### "Ollama not responding"
```bash
ollama serve
ollama pull llama3.2
```

### "Can't reach from iPhone"
```bash
# Check firewall allows ports 5002, 5003
# Make sure laptop and iPhone on same WiFi
bash EXPOSE-TO-IPHONE.sh
```

### "Session invalid"
- Sessions expire after 24 hours
- Scan QR code again to create new account

### "Database locked"
```bash
# Stop all services
bash STOP-ALL.sh

# Restart
bash START-ALL.sh
```

## What's Next?

### Ready for iPhone Testing

All code is complete. To test on iPhone:

1. Run `bash EXPOSE-TO-IPHONE.sh` to get your local IP
2. Update QR code with your local IP
3. Scan QR code with iPhone camera
4. Should create account and open chat!

### Deploy to Production

1. Deploy soulfra.com to GitHub Pages (free)
2. Deploy soulfraapi.com + soulfra.ai to DigitalOcean ($5/month)
3. Point custom domains (optional)
4. Update QR code with production URLs

### Add Features (Optional)

- Email collection on signup
- Password-based login
- User profiles
- Chat history
- Multiple AI models
- Voice input/output

## Philosophy

**Own your stack. No external dependencies.**

- ✅ Static site (GitHub Pages)
- ✅ Self-hosted API (SQLite)
- ✅ Self-hosted AI (Ollama)
- ✅ No tracking, no analytics
- ✅ User owns their data
- ✅ Works offline after signup

## Credits

Built using existing templates from soulfra-simple:
- `qr_auth.py` - QR authentication
- `session_manager.py` - Session management
- `ollama_client.py` - Ollama integration

**Total build time:** ~45 minutes
**Lines of code:** ~1,200
**External dependencies:** Flask, Ollama
**Cost:** $0/month (laptop) or $5/month (production)

---

**Bottom line:** 3 domains, 3 purposes, 1 seamless flow. QR scan → account → AI chat.
