# 🎤 Soulfra - Voice-First Development Platform

**Building the internet with voice memos. Zero cloud dependencies.**

[![StPetePros](https://img.shields.io/badge/Live-StPetePros-purple)](https://soulfra.com/stpetepros/)
[![CringeProof](https://img.shields.io/badge/Live-CringeProof-blue)](https://cringeproof.com/)
[![Architecture](https://img.shields.io/badge/Docs-Architecture-green)](https://github.com/soulfra/soulfra-simple/blob/main/ARCHITECTURE.md)

---

## 🚀 What This Is

A complete operating system for **idea → deployment** that runs on your laptop:

1. **Record voice memo** (on phone)
2. **AI transcribes** (Whisper, local)
3. **AI extracts ideas** (Ollama, local)
4. **Export to static HTML** (no backend needed)
5. **Deploy to GitHub Pages** (30 seconds)
6. **Live website updated** ✅

**Zero API keys. Zero cloud costs. Fully owned.**

---

## 📦 Apps (Repos)

Each repo is a self-contained "app" in the Soulfra ecosystem:

### 🏢 [StPetePros](https://github.com/soulfra/soulfra-simple) - Tampa Bay Directory
**Live:** [soulfra.com/stpetepros](https://soulfra.com/stpetepros/)

Professional directory for Tampa Bay. Features:
- ✅ Keyboard navigation (arrow keys, escape, numbers)
- ✅ Static HTML (no backend for customers)
- ✅ CSV import/export (manage like spreadsheet)
- ✅ Auto-deployment (git push → live in 30s)
- ✅ 17 professionals (including Soulfra itself!)

**Built with voice memos.** Every feature documented in voice archive.

---

### 🎬 [CringeProof](https://cringeproof.com/) - Voice Wall
**Live:** [cringeproof.com](https://cringeproof.com/)

Social platform for voice memos:
- 🎤 Record voice → Auto-transcribed → Posted to wall
- 🤖 AI personas comment (brand_ai_orchestrator)
- 📊 Feed shows latest posts
- 🔗 Links back to features they created

**Philosophy:** "Answer Today's Questions" - focus on shipping, not vaporware.

---

### 🎯 [AI Agents](https://github.com/soulfra/agent-router)
AI customer service agents for each business:

```python
# Each StPetePros professional gets an AI
professional = {
    'name': 'Joe\'s Plumbing',
    'category': 'plumbing'
}

# Auto-generates agent
agent = create_ai_agent(professional)
# Handles: emails, scheduling, quotes
# Escalates: complex questions to human
```

**Payment tiers:**
- Free: Basic responses
- $10/mo: Scheduling
- $30/mo: Follow-ups
- $100/mo: Relationship building

---

### 🗄️ [Database Layer](https://github.com/soulfra/soulfra-simple)
**Tech:** SQLite (74 tables)

```
soulfra.db
├── professionals (StPetePros listings)
├── users (cross-domain accounts)
├── posts (CringeProof wall)
├── brands (AI personas)
├── voice_suggestions (voice memos)
└── ... (69 more tables)
```

**Sync:** Laptop → Export scripts → GitHub Pages → Live sites

---

### 🎙️ [Voice Archive](https://github.com/soulfra/voice-archive) *(Coming Soon)*
All voice memos with transcripts:
- 📂 Practice sessions (8 .webm files)
- 📂 Voice news memos (4 .m4a files)
- 📝 Auto-transcribed with Whisper
- 🔗 Links to features they created
- 📊 Index by date/domain/feature

**Example:**
```
2026-01-11_keyboard_navigation.m4a
→ Transcript: "Add keyboard navigation to StPetePros..."
→ Feature: Arrow keys work on all professional pages
→ Commit: abc123f
→ Live: soulfra.com/stpetepros/professional-1.html
```

---

## 🏗️ The Stack (All Local)

| Layer | Tech | Why |
|---|---|---|
| **Input** | Voice memos | Faster than typing |
| **Transcription** | Whisper (local) | No API costs |
| **AI** | Ollama (local) | No rate limits |
| **Database** | SQLite | No server needed |
| **Backend** | Flask (localhost) | Dev only |
| **Frontend** | Static HTML | No backend for users |
| **Hosting** | GitHub Pages | Free, fast, reliable |
| **Deploy** | Git + Actions | 30 second deploys |

**Total cloud cost:** $0/month

---

## 🎨 The Workflow

### Example: Adding Keyboard Navigation

**1. Voice Input**
```
"Add keyboard navigation to StPetePros.
 Arrow keys between professionals.
 Escape to go back.
 Numbers to jump."
```

**2. Processing** (automatic)
```python
# Whisper transcribes
transcript = whisper.transcribe(audio)

# Ollama extracts ideas
ideas = ollama.extract({
    "feature": "keyboard navigation",
    "domain": "stpetepros",
    "keys": ["arrows", "escape", "numbers"]
})
```

**3. Implementation** (you or Claude)
```python
# Edit export-to-github-pages.py
# Add <script> with navigation JS
# Inject into all 17 professional pages
```

**4. Export** (automatic)
```bash
python3 export-to-github-pages.py
# Generates 17 HTML files
# Outputs to ~/Desktop/soulfra.github.io/stpetepros/
```

**5. Deploy** (automatic)
```bash
git push
# GitHub Actions triggers
# Live in 30 seconds
```

**Total time:** Idea → Live in under 1 minute

---

## 🔄 The Self-Referential Loop

**StPetePros lists Soulfra:**
- Category: Web Design & Development
- Bio: "Built with voice memos. Zero dependencies."
- Link: github.com/soulfra (this profile)

**You're using the thing that built itself.**

When you browse StPetePros with keyboard navigation → you're experiencing the feature that was voice-requested → which is documented in voice archive → which is hosted on GitHub (here) → which links back to StPetePros.

**Every feature is a portfolio piece.**

---

## 📊 Stats

- **17** Professionals in StPetePros
- **74** Database tables
- **12** Voice memos (and counting)
- **30s** Average deploy time
- **$0** Monthly costs
- **0** Third-party APIs (except GitHub)

---

## 🛠️ Quick Start

**1. Clone the "OS":**
```bash
git clone https://github.com/soulfra/soulfra-simple
cd soulfra-simple
```

**2. Check status:**
```bash
./status.sh
```

**3. Start automation:**
```bash
./stpetepros-simple.sh
```

**4. Add a professional:**
```bash
# Export to CSV
python3 csv-manager.py export

# Edit professionals.csv in Excel

# Import back
python3 csv-manager.py import professionals.csv

# Deploy
python3 export-to-github-pages.py
cd ~/Desktop/soulfra.github.io
git push
```

**5. Browse with keyboard:**
Visit [soulfra.com/stpetepros](https://soulfra.com/stpetepros/) and press arrow keys!

---

## 🎯 The Vision

**Craigslist** = Text-only, no verification, spam
**Meta** = Walled garden, ads, privacy invasion
**Soulfra** = Voice-first, AI-native, zero lock-in

**The apex:** Build features faster than anyone by using voice as the primary interface. No typing required. No cloud costs. Fully owned infrastructure.

**The OS:** This isn't just a website generator. It's a complete operating system where:
- Voice memos = shell commands
- GitHub Pages = package manager
- Ollama/Whisper = userland
- SQLite = filesystem
- Flask = kernel

**The future:** Decentralized. Run on laptop, VPS, or distributed across devices. Sync via Git. Each "app" (repo) is a package others can install.

---

## 🔗 Links

- **Live Sites:**
  - [StPetePros Directory](https://soulfra.com/stpetepros/) (try arrow keys!)
  - [CringeProof Voice Wall](https://cringeproof.com/)

- **Documentation:**
  - [Architecture Guide](https://github.com/soulfra/soulfra-simple/blob/main/ARCHITECTURE.md)
  - [Domains Explained](https://github.com/soulfra/soulfra-simple/blob/main/DOMAINS.md)

- **Code:**
  - [Main Repo](https://github.com/soulfra/soulfra-simple)
  - [GitHub Pages](https://github.com/soulfra/soulfra.github.io)

---

## 💬 Contact

**Found on StPetePros:** Listed as "Soulfra - Web Design & Development"
**Email:** hello@soulfra.com
**Phone:** (727) 555-SOUL
**Website:** [soulfra.com](https://soulfra.com)

**Built with:** Voice memos, Ollama, Whisper, SQLite, Flask, GitHub Pages, and vibes.

---

<div align="center">

**🎤 Voice-First | 🤖 AI-Native | 🔓 Zero Lock-In**

*Building the internet one voice memo at a time*

</div>
