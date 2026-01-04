# Soulfra

**Building the non-typing internet**

> Voice memos, QR scans, emoji navigation, gesture controls. Just login, scan, and go.

🔴 **LIVE UPDATE TEST** - Last edited: 2026-01-04 12:52 EST from MacBook Terminal
_Next edit will be from iPhone to prove mobile workflow works_

---

## 🎤 What I'm Building

### [CringeProof](https://cringeproof.com) / voice-archive

Instant voice recording → AI extraction → Published ideas

**The flow:**
1. Record voice memo on iPhone (one tap, no typing)
2. Shadow account system (no login required - browser fingerprinting)
3. Offline queue (record anywhere, uploads when online)
4. AI extracts ideas from transcription (Ollama + Whisper)
5. Published to GitHub Pages with cryptographic signatures

**Try it:**
- 📱 [Mobile Interface](https://cringeproof.com/mobile.html)
- 🧪 [Debug Page](https://cringeproof.com/test-deployment.html)

**Features:**
- Shadow accounts (Canvas + WebGL + Audio fingerprinting)
- Offline-first PWA (IndexedDB + ServiceWorker)
- Zero typing required
- Privacy-first (PII scrubbing, local-first)
- Works on: Local WiFi, GitHub Pages, Custom Domains

---

## 🎮 Core Philosophy: Gameplay Loops Over Polish

**Roblox, Minecraft, RuneScape don't look great but have addictive gameplay.**

Focus areas:
1. **Non-typing interaction**
   - Voice control (speak commands)
   - QR scanning (login, actions, pre-fill forms)
   - Emoji navigation (react, filter, choose)
   - Gesture controls (swipe, tap patterns)
   - Menu-only mode (click-based accessibility)

2. **Instant contribution**
   - No signup friction
   - Shadow accounts (fingerprint-based)
   - Offline queue (record first, sync later)
   - One-tap recording

3. **Community-driven content**
   - Users contribute voice memos
   - Select accounts when contributing ideas
   - Multi-brand system (CalRiven, DeathToData, HowToCookAtHome)

---

## 🛠️ Active Projects

### [voice-archive](https://github.com/Soulfra/voice-archive)
**OSS voice recording component**

Deploy to your own domain with your own backend:
- GitHub Pages hosting (free)
- Router config auto-detects environment
- Works local (same WiFi) or production (Cloudflare Workers, VPS)
- Full deployment docs and debug tools

### [soulfra.github.io](https://soulfra.github.io)
**Multi-brand showcase**

Voice predictions archive with community brands:
- CalRiven (data analysis)
- DeathToData (calling out cringe)
- HowToCookAtHome (recipes)
- StPetePros, Hollowtown, Niceleak, Oofbox

### Network Architecture Evolution

Building routing infrastructure from **Phase 1** (local WiFi) → **Phase 4** (fully serverless):

```
Phase 1: Local Network
  iPhone + MacBook (same WiFi)
  https://192.168.1.87:5001

Phase 2: Cloudflare Workers Router
  YOUR router code (not Tailscale, not ngrok)
  api.cringeproof.com → Cloudflare Worker → Tunnel → MacBook

Phase 3: VPS + nginx
  Permanent backend, full control
  $5/month VPS with reverse proxy

Phase 4: Fully Serverless
  Cloudflare Workers + R2 + Supabase
  No MacBook dependency, scales automatically
```

---

## 🧩 Technologies

**Frontend:**
- Vanilla JS (no frameworks - keep it fast)
- Shadow DOM for accessibility menu
- MediaRecorder API for voice
- IndexedDB for offline queue
- Service Workers for PWA

**Backend:**
- Flask (Python)
- SQLite (local development)
- Ollama (local AI - no API keys)
- Whisper (transcription)

**Deployment:**
- GitHub Pages (static hosting)
- Cloudflare Workers (serverless routing)
- Local network (MacBook Flask server)

**Infrastructure You Control:**
- router-config.js (auto-detect environment)
- No third-party tunnels in production
- Own your routing logic
- Own your domains

---

## 📦 Deployment Strategy

All projects designed to be **forkable and deployable** by anyone:

1. **Clone repo**
2. **Configure backend** (`.env.example` → `.env`)
3. **Test locally** (`test-deployment.html`)
4. **Deploy to GitHub Pages** (`git push`)

No vendor lock-in. No proprietary services. Just static HTML/CSS/JS + your own backend.

---

## 🌐 Live URLs

- **CringeProof:** https://cringeproof.com
- **Mobile App:** https://cringeproof.com/mobile.html
- **Debug Tools:** https://cringeproof.com/test-deployment.html
- **Main Site:** https://soulfra.github.io
- **RSS Feed:** https://soulfra.github.io/feed.xml

---

## 🔐 Privacy & Security

**Privacy-first architecture:**
- No tracking, no analytics
- PII scrubbing (names, emails, phones removed)
- Local AI processing (Ollama - your machine, your data)
- Shadow accounts (browser fingerprinting, not personal info)
- Cryptographic signatures (SHA-256 proof of authenticity)

**Security practices:**
- `.gitignore` for secrets (.env, *.pem, *.key)
- SSH keyring authentication (no passwords in terminal)
- CORS configuration for API access
- HTTPS required for microphone API

---

## 💡 Current Focus

**Making the non-typing internet real:**

1. **Accessibility menu** - Universal input mode switcher (voice, scan, emoji, gesture, menu)
2. **Workflow coordinator** - State machine routing input modes based on page context
3. **Shadow account system** - No login required, just start using
4. **Offline queue** - Record anywhere, sync when online
5. **Router infrastructure** - Own your routing between domains and backends

**Not building:**
- Complex UI frameworks
- Beautiful graphics
- Typing-required interfaces

**Building:**
- Addictive gameplay loops
- Zero-friction contribution
- Non-typing interactions
- Community-driven content

---

## 📖 Documentation

- **Deployment:** [voice-archive/DEPLOY.md](https://github.com/Soulfra/voice-archive/blob/main/DEPLOY.md)
- **Network Setup:** [NETWORK-SETUP.md](https://github.com/Soulfra/voice-archive/blob/main/NETWORK-SETUP.md)
- **Debug Tools:** [test-deployment.html](https://cringeproof.com/test-deployment.html)

---

## 🤝 Philosophy

**"Reverse engineer all the nodes"**

- Learn how routing works (HTTP proxying, CORS, SSL)
- Learn tunnel mechanics (SSH, WebSocket, nginx upstream)
- Learn serverless architecture (edge functions, state management)
- Build your own router infrastructure
- No dependency on third-party tunnels

**From local network → production serverless:**
- Phase by phase evolution guide
- Understand each layer
- Own your stack

---

## 📱 Pair Your iPhone

Two ways to record voice memos from your iPhone:

### Option 1: Local WiFi (Simpler - No OAuth!)

**If your iPhone + MacBook are on the same WiFi:**

<div align="center">
    <a href="http://192.168.1.87:5001/record">
        <img src="assets/qr-local.svg" alt="Scan to record (local WiFi)" width="200">
    </a>
    <br>
    <sub>📡 <strong>Same WiFi Required</strong> | No OAuth, No Login</sub>
</div>

**How it works:**
1. Scan QR code on iPhone (same WiFi as MacBook)
2. Opens recording page directly
3. Record voice memo
4. Automatically creates gist & updates this README!

**Setup:** See [LOCAL-WIFI-SETUP.md](LOCAL-WIFI-SETUP.md) - Just need a GitHub Personal Access Token (2 min setup)

---

### Option 2: OAuth (From Anywhere)

**If you want to record from anywhere (not same WiFi):**

<div align="center">
    <a href="https://cringeproof.com/pair">
        <img src="assets/qr-pair.svg" alt="Scan to pair (OAuth)" width="200">
    </a>
    <br>
    <sub>🌐 <strong>Works Anywhere</strong> | Requires GitHub OAuth Setup</sub>
</div>

**How it works:**
1. Scan QR code → Opens pairing page
2. Connect GitHub account (OAuth)
3. Paired! Can record from anywhere
4. Voice memos auto-update this README

**Setup:** See [QR-PAIRING-SETUP.md](QR-PAIRING-SETUP.md) - Requires GitHub OAuth app (30 min setup)

---

## 📬 Get In Touch

- **GitHub:** [@Soulfra](https://github.com/Soulfra)
- **Issues:** Open an issue on any repo
- **Fork:** All projects MIT licensed - fork and build your own

---

**Built for privacy-conscious creators who want to own their infrastructure**

No Tailscale. No ngrok. No vendor lock-in. Just you, your code, your domains.
