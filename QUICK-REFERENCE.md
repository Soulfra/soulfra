# Quick Reference - Your Actual System

**Everything you need to know on one page.**

---

## 🎯 What You Have

**ONE working publishing system:**
```
Studio → Multi-AI Debate → Export HTML → Git Push → LIVE
```

**FOUR live domains:**
- soulfra.com (main blog)
- deathtodata.com (privacy blog)
- calriven.com (ownership blog)
- howtocookathome.com (ready for content)

**ZERO blockchain or crypto projects.**

---

## 🚀 How to Use It

### Start the System
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

### Open Studio
```
http://localhost:5001/studio
```

### Generate Content
1. Click "🤖 Multi-AI Debate"
2. Enter topic: "Should we use TypeScript?"
3. Select brand: Soulfra
4. Click "🚀 Generate Multi-AI Debate"
5. Wait 60 seconds
6. **BOOM! Live at soulfra.com**

---

## 📁 What Each Folder Does

```
soulfra-simple/
├── app.py              ← Main Flask server (port 5001)
├── export_static.py    ← Convert Flask → static HTML
├── database.py         ← SQLite database
│
├── output/             ← GitHub Pages repos (your live sites)
│   ├── soulfra/        ← soulfra.com (LIVE)
│   ├── deathtodata/    ← deathtodata.com (LIVE)
│   ├── calriven/       ← calriven.com (LIVE)
│   └── howtocookathome/ ← howtocookathome.com (ready)
│
├── templates/          ← HTML templates
│   └── studio.html     ← Studio UI
│
├── static/             ← CSS, JS, images
│
└── Soulfra/            ← SEPARATE EXPERIMENT (can ignore)
```

---

## 🌐 Your Domains Explained

| Domain | What It Does | Status |
|--------|-------------|--------|
| **soulfra.com** | Main blog - identity & security | ✅ LIVE |
| **deathtodata.com** | Privacy manifesto | ✅ LIVE |
| **calriven.com** | Ownership philosophy | ✅ LIVE |
| **howtocookathome.com** | Future cooking content | 🔨 READY |
| ~~soulfraapi.com~~ | Experiment in Soulfra/ folder | 🧪 IGNORE |
| ~~soulfra.ai~~ | Experiment in Soulfra/ folder | 🧪 IGNORE |

---

## ❌ What You DON'T Have

- ❌ NO blockchain
- ❌ NO cryptocurrency
- ❌ NO crypto mining
- ❌ NO Web3
- ❌ NO smart contracts

**"Faucet" = API key distribution (like a water faucet drips free API keys)**

---

## 🧹 Clean Up (Optional)

### Create backup + archive bloat:
```bash
bash CLEANUP-BLOAT.sh
```

This will:
- Create backup
- Move Soulfra/ folder to archive/
- Move 448 bloat files to archive/
- Keep only core 15 files

**Safe - creates backup first!**

---

## 📚 Full Documentation

- **ARCHITECTURE-CLARIFIED.md** - Complete system explanation
- **SIMPLE-PUBLISHING-WORKFLOW.md** - How one-button publishing works
- **CORE-VS-CRUFT.md** - 15 core files vs 448 bloat files

---

## 🎯 Bottom Line

**You have ONE simple system:**
1. Studio UI to create content
2. Multi-AI debate generator
3. Auto-publish to GitHub Pages
4. Four live domains (FREE)

**Everything else is noise.**

**Focus on:** Creating debates and publishing to your domains.

**Ignore:** Soulfra/ folder, "blockchain" references, "faucet" terminology.

---

## 💡 Quick Commands

```bash
# Start server
python3 app.py

# Generate content
# Visit: http://localhost:5001/studio

# Clean up bloat (optional)
bash CLEANUP-BLOAT.sh

# Check what's running
lsof -i :5001
```

---

**That's it. Simple.**
