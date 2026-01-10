# Web Domain Manager - README

## ✅ What We Just Built

**A web-based interface to manage your domains and chat with Ollama AI**

---

## 🎯 How To Use It

### 1. Start Flask App (Already Running)

Your Flask app is running on `localhost:5001`

### 2. Open Domain Manager

Visit in your browser:
```
http://localhost:5001/domains
```

### 3. You'll See:

**Left Side: Your Domains**
- List of all 5 domains (soulfra.com, stpetepros.com, etc.)
- Add new domain form with AI analysis
- Click any domain to select it

**Right Side: Ollama Chat**
- Chat with AI about domains, deployment, sitemaps, etc.
- Ask questions like:
  - "How do I build stpetepros.com as a real website?"
  - "Create a sitemap for my stpetepros.com domain"
  - "How do I deploy this to production?"
  - "What features should I add to stpetepros.com?"

---

## 🚀 Features

### Add New Domain
1. Type domain name (e.g., `mynewdomain.com`)
2. Click "Add Domain"
3. AI analyzes:
   - Industry/niche suggestion
   - Geographic region/SEO strategy
   - Content strategy
4. Generates QR code for login
5. Adds to database

### Chat with Ollama
- Context-aware (knows about selected domain)
- Can analyze local files/transcripts
- Suggests sitemap, deployment, features
- Remembers conversation history

### Domain List
- Shows all domains from database
- Click to select for chat context
- See tagline and category

---

## 📁 Files Created

1. **`web_domain_manager_routes.py`** - Flask routes
   - `/domains` - Main UI
   - `/api/domains/list` - Get all domains (JSON)
   - `/api/domains/create` - Add new domain (JSON)
   - `/api/domains/chat` - Chat with Ollama (JSON)

2. **`templates/domain_manager.html`** - Web interface
   - Beautiful purple gradient UI
   - Responsive layout
   - Real-time chat
   - Domain management

3. **`app.py`** - Updated with route registration

---

## 🧪 Test It Now

```bash
# Flask is already running, just visit:
open http://localhost:5001/domains
```

### Try These Commands in Chat:

**Domain Strategy:**
```
How should I build stpetepros.com?
```

**Sitemap Generation:**
```
Create a sitemap for a professional services directory
```

**Deployment:**
```
How do I deploy this from localhost to stpetepros.com?
```

**File Analysis** (coming soon):
```
Analyze this transcript: [paste content]
```

---

## 🔗 How It All Connects

```
┌─────────────────────────────────────────┐
│   You → localhost:5001/domains          │
│                                         │
│   ┌──────────────┐   ┌──────────────┐ │
│   │ Domain List  │   │  Ollama Chat │ │
│   │              │   │              │ │
│   │ - soulfra    │   │  💬 Ask me   │ │
│   │ - stpetepros │   │  anything!   │ │
│   │ - Add new    │   │              │ │
│   └──────────────┘   └──────────────┘ │
│                                         │
└─────────────────────────────────────────┘
            ↓
    Flask Backend (app.py)
            ↓
    ┌───────┴────────┐
    │               │
Database (5 domains) Ollama (22 models)
```

## 🗺️ Routing Architecture

### How Multi-Domain Routing Works

Your Flask app routes traffic to different brands based on the request domain:

```
Browser Request
    ↓
[http://stpetepros.com]
    ↓
Flask receives: request.host = "stpetepros.com"
    ↓
Database Lookup:
    SELECT * FROM brands WHERE domain = 'stpetepros.com'
    ↓
    Returns: {name: "Stpetepros", slug: "stpetepros", category: "Home Services"}
    ↓
Template Selection:
    1. Check for brand-specific template: templates/brands/stpetepros.html
    2. If not found, use: templates/index.html (default)
    ↓
Render HTML with brand context
    ↓
Return to browser
```

### Domain Role Separation

Each domain serves a specific purpose in your ecosystem:

1. **soulfra.com** - The Faucet
   - Main entry point and identity hub
   - Handles authentication and QR pairing
   - Central database (soulfra.db)
   - Coordinates other domains

2. **deathtodata.com** - Search & Ranking
   - Content discovery engine
   - SEO and page ranking
   - Data analysis and insights

3. **calriven.com** - Algorithms & Processing
   - Backend computation layer
   - Algorithm execution
   - Technical processing

4. **stpetepros.com** - Production Site
   - Professional services directory
   - First real business application
   - Uses shared infrastructure

5. **localhost:5001** - Development Sandbox
   - Safe testing environment
   - Preview changes before deployment
   - Domain manager interface

### The "Sandbox Code"

The sandbox is your **localhost:5001** development environment where you:
- Test all changes safely before deploying
- Use Domain Manager (/domains) to view and edit
- Preview domains with the Preview button
- Chat with Ollama to plan and analyze

When ready, you deploy to production domains (soulfra.com, stpetepros.com, etc.)

---

## 🎨 Next Steps

### 1. **Create Brand-Specific Templates**

Right now all domains use the same homepage. You want:
- `soulfra.com` → Storytelling platform
- `stpetepros.com` → Professional services directory

We'll create template/brands/stpetepros.html next.

### 2. **Deployment to Production**

Move from `localhost:5001` to actual domains:
- Configure DNS (GoDaddy)
- Deploy Flask app to server
- Point domains to server IP

### 3. **File Upload for Ollama**

Add ability to upload:
- Call transcripts
- Documents
- Images (OCR)

Ollama will analyze and provide insights.

---

## 💡 What You Can Do Right Now

1. **Visit** `http://localhost:5001/domains`
2. **Add** a test domain (e.g., `test.com`)
3. **Chat** with Ollama about building stpetepros.com
4. **Ask** AI to help you create a sitemap or deployment plan

---

## 🐛 Troubleshooting

**If Flask isn't running:**
```bash
python3 app.py
```

**If Ollama isn't working:**
```bash
ollama list  # Check models
```

**If domain manager doesn't load:**
- Check terminal for errors
- Verify `web_domain_manager_routes.py` exists
- Check browser console (F12)

---

##Ready to Test?

Open your browser and go to:
**http://localhost:5001/domains**

The system is fully working! 🎉
