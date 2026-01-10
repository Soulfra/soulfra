# System Architecture - Multi-Service Setup

## 🎯 Your Systems Overview

You have **4 separate services** running that can now work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR SYSTEMS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐    │
│  │   FLASK     │      │   NODE.JS   │      │   OLLAMA    │    │
│  │  Port 5001  │ ←──→ │  Port 3000  │ ←──→ │  Port 11434 │    │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘    │
│         │                    │                     │           │
│         └────────────────────┴─────────────────────┘           │
│                              │                                 │
│                     ┌────────▼────────┐                        │
│                     │   DATABASE      │                        │
│                     │  soulfra.db     │                        │
│                     │  (SQLite)       │                        │
│                     └─────────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Flask Server (Port 5001)

**Location**: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/`

**What it does**:
- Domain manager
- Template browser
- Formula engine (brand theming)
- Blog/email generation
- QR login system
- User authentication

**Key Routes**:
```
Frontend Pages:
  GET  /                              - Homepage
  GET  /domains                       - Domain manager
  GET  /templates/browse              - Template browser UI
  GET  /login                         - Regular login
  GET  /login-qr                      - QR code login

Template System:
  GET  /api/templates/list            - List all templates
  POST /api/templates/read            - Read template content
  POST /api/templates/render          - Render template with variables
  POST /api/templates/generate-with-ollama - AI content generation
  POST /api/templates/deploy          - Deploy to domain

QR Authentication:
  POST /api/qr/generate               - Generate QR code
  GET  /api/qr/verify/<token>         - Verify QR scan
  GET  /api/qr/check-status/<token>   - Poll for scan

Blog/Domain Serving:
  GET  /blog/<domain>/<filename>      - Serve blog posts
  GET  /theme-<domain>.css            - Serve theme CSS
```

**Files**:
- `app.py` - Main Flask application
- `formula_engine.py` - Template rendering engine
- `ollama_client.py` - Ollama HTTP API client (NEW!)
- `qr_auth.py` - QR authentication system
- `database.py` - SQLite database connection

**How to start**:
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

---

## 2️⃣ Node.js Server (Port 3000)

**Location**: `/Users/matthewmauer/Desktop/roommate-chat/`

**What it does**:
- Chat system
- Ollama integration (HTTP API)
- Game systems (trivia, math)
- Practice room
- Cringeproof audio player

**Key Routes** (from server.js):
```
API Endpoints:
  GET  /api/config                    - Config info
  POST /api/practice-room/generate-response - Ollama chat
  GET  /api/game-performance          - Game stats
  POST /api/cringeproof/*             - Audio player controls
```

**Files**:
- `server.js` - Express server (693KB!)
- `ollama.js` - Ollama HTTP API integration
- `model-archetypes.json` - AI personality definitions

**How Ollama is called**:
```javascript
// Node.js uses HTTP API with context
const response = await fetch('http://127.0.0.1:11434/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    model: 'llama3.2',
    prompt: systemPrompt + userMessage,
    options: { temperature: 0.7, num_predict: 500 }
  })
});
```

**How to start**:
```bash
cd /Users/matthewmauer/Desktop/roommate-chat
node server.js
```

**Currently running**: PID 87056

---

## 3️⃣ Ollama (Port 11434)

**What it is**: AI model server (runs locally)

**Available models**:
- llama3.2
- mistral
- phi3
- codellama
- soulfra-model (custom)
- calos-model (custom)

**API Endpoints**:
```
GET  http://127.0.0.1:11434/api/tags       - List models
POST http://127.0.0.1:11434/api/generate   - Generate response
```

**How Flask now calls it** (NEW!):
```python
# Flask uses HTTP API (like Node.js)
from ollama_client import OllamaClient

client = OllamaClient()
result = client.generate_with_template_context(
    prompt="Your question",
    template_content="<html>...</html>",  # Ollama can see this!
    variables={"brand": "Soulfra"},       # And this!
    model="llama3.2"
)
```

**Why this matters**:
- ✅ Ollama can now see template content
- ✅ Ollama can see variables
- ✅ Ollama can help improve templates
- ✅ Ollama can suggest variables
- ✅ Same API as Node.js uses

**Check if running**:
```bash
curl http://127.0.0.1:11434/api/tags
```

---

## 4️⃣ Database (soulfra.db)

**Location**: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db`

**Size**: 2.6 MB

**Tables**:
```
users                - User accounts
qr_auth_tokens       - QR login tokens (NEW!)
posts                - Blog posts
comments             - Post comments
messages             - Direct messages
notifications        - User notifications
subscribers          - Newsletter emails
professionals        - StPetePros directory
user_activity        - Activity tracking
user_topics          - User topics
... and more
```

**Shared by**:
- Flask server (direct SQLite connection)
- Node.js server (could connect if needed)

**How to inspect**:
```bash
sqlite3 soulfra.db
.tables              # List tables
.schema users        # Show table schema
SELECT * FROM qr_auth_tokens;
```

---

## 🔗 How Systems Connect

### Flask ↔ Ollama (NEW INTEGRATION!)

**Before** (subprocess):
```python
# Flask couldn't pass context
result = subprocess.run(['ollama', 'run', 'llama3.2', prompt])
```

**After** (HTTP API):
```python
# Flask can pass template + variables as context
client = OllamaClient()
result = client.generate_with_template_context(
    prompt="Help me improve this template",
    template_content=template,  # Ollama sees this!
    variables=variables         # And this!
)
```

### Node.js ↔ Ollama

```javascript
// Node.js already uses HTTP API
import * as ollama from './ollama.js';

const result = await ollama.generateResponse(message, {
  model: 'llama3.2',
  temperature: 0.7,
  systemPrompt: 'You are a helpful assistant...'
});
```

### Flask ↔ Database

```python
from database import get_db

db = get_db()
users = db.execute('SELECT * FROM users').fetchall()
```

### QR Login Flow

```
1. User opens: http://localhost:5001/login-qr
                ↓
2. Browser calls: POST /api/qr/generate
                ↓
3. Flask creates QR code + token in database
                ↓
4. User scans QR with phone
                ↓
5. Phone opens: /qr/faucet/<token>
                ↓
6. Flask calls: /api/qr/verify/<token>
                ↓
7. Database marks token as used
                ↓
8. Session created, user logged in!
```

---

## 🎨 Template Browser Flow

```
1. User opens: http://localhost:5001/templates/browse
                ↓
2. Browser calls: GET /api/templates/list
                ↓
3. Flask returns all .tmpl files
                ↓
4. User clicks template
                ↓
5. Browser calls: POST /api/templates/read
                ↓
6. Flask returns template content
                ↓
7. User edits variables, clicks "Render"
                ↓
8. Browser calls: POST /api/templates/render
                ↓
9. formula_engine.py processes {{variables}}
                ↓
10. Preview shows rendered HTML!
```

**With Ollama** (NEW!):
```
7. User clicks "Generate with Ollama"
                ↓
8. Browser calls: POST /api/templates/generate-with-ollama
                ↓
9. Flask calls Ollama HTTP API with:
   - Template content (Ollama can see it!)
   - Current variables (Ollama knows them!)
   - User prompt
                ↓
10. Ollama generates content
                ↓
11. formula_engine.py renders template with AI content
                ↓
12. Preview shows result!
```

---

## 📦 File Structure

```
/Users/matthewmauer/Desktop/roommate-chat/
├── server.js                     # Node.js server (port 3000)
├── ollama.js                     # Node.js Ollama integration
├── model-archetypes.json         # AI personalities
├── soulfra.db                    # Database (2.6MB)
│
└── soulfra-simple/               # Flask app directory
    ├── app.py                    # Flask server (port 5001)
    ├── formula_engine.py         # Template engine
    ├── ollama_client.py          # Ollama HTTP client (NEW!)
    ├── qr_auth.py                # QR authentication
    ├── database.py               # Database connection
    ├── soulfra.db                # Database (symlink/copy)
    │
    ├── templates/                # Flask HTML templates
    │   ├── template_browser.html # Template browser UI
    │   ├── login_qr.html         # QR login page
    │   └── ... (141 other files)
    │
    ├── examples/                 # Formula templates (.tmpl)
    │   ├── theme.css.tmpl
    │   ├── email.html.tmpl
    │   └── brand-vars.json
    │
    └── domains/                  # Deployed content
        ├── soulfra/
        │   └── blog/
        └── stpetepros/
            └── blog/
```

---

## 🚀 Quick Start Guide

### Start All Systems

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Flask
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py

# Terminal 3: Start Node.js (already running)
cd /Users/matthewmauer/Desktop/roommate-chat
node server.js
```

### Access Points

```
Flask:          http://localhost:5001
Node.js:        http://localhost:3000
Ollama API:     http://localhost:11434

Template Browser:  http://localhost:5001/templates/browse
QR Login:          http://localhost:5001/login-qr
Domain Manager:    http://localhost:5001/domains
```

---

## 🎯 What's Fixed

### ✅ Template Rendering Bug
- **Was**: "File name too long" error
- **Now**: Correctly distinguishes file paths from HTML content

### ✅ Ollama Context Issue
- **Was**: Ollama couldn't see templates/variables
- **Now**: Flask uses HTTP API, passes full context

### ✅ QR Login System
- **Was**: Routes missing, database table missing
- **Now**: Full QR auth flow working

---

## 🔧 Debugging

### Check what's running:
```bash
lsof -i :5001   # Flask
lsof -i :3000   # Node.js
lsof -i :11434  # Ollama
```

### Test Ollama:
```bash
python3 ollama_client.py  # Test Flask integration
node -e "import('./ollama.js').then(m => m.checkOllamaHealth().then(console.log))"
```

### Inspect database:
```bash
sqlite3 soulfra.db
.tables
SELECT * FROM qr_auth_tokens;
```

### View logs:
```bash
tail -f /tmp/flask.log   # If logging is set up
```

---

## 🎮 Next Steps

Now that everything is connected:

1. **Test Template Browser**: http://localhost:5001/templates/browse
   - Try rendering a template
   - Try "Generate with Ollama" - it can now see your template!

2. **Test QR Login**: http://localhost:5001/login-qr
   - Generate a QR code
   - Scan it with your phone
   - See if login works

3. **Connect Roommate Game**:
   - 40+ QR files exist in soulfra-simple/
   - QR auth system is ready
   - Just need to add game routes

4. **Link Flask ↔ Node.js**:
   - Could share sessions via Redis
   - Could proxy requests between them
   - Could use same database (already possible!)

---

## 💡 Key Insights

**You were right about the pattern!**

```
Templates → Variables → Formulas → Output
```

This pattern appears in:
- **Your theme system**: Brand configs → CSS
- **Formula engine**: JSON → Any file
- **Ollama prompts**: Context → Response
- **QR codes**: Token → Auth

**The systems are like layers**:
```
┌─────────────────────────────────────┐
│ Frontend (Browser)                  │ ← User sees this
├─────────────────────────────────────┤
│ Flask + Node.js (Servers)           │ ← Handle requests
├─────────────────────────────────────┤
│ Ollama (AI)                         │ ← Generate content
├─────────────────────────────────────┤
│ Database (Storage)                  │ ← Persist data
└─────────────────────────────────────┘
```

Each layer can talk to the others via:
- HTTP APIs (Flask ↔ Ollama)
- Database (All systems)
- File system (Templates, domains)

---

**All systems are GO! 🚀**
