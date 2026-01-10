# What's Live Right Now - Complete System Map

**Updated:** 2026-01-03 14:54
**Status:** ✅ Phase 2A Complete - Ideas Hub Published!

---

## 🌐 Live URLs (All Working!)

### Voice & Ideas System
| URL | What It Is | Status |
|-----|------------|--------|
| **https://soulfra.github.io/voice-archive/** | Voice Predictions Gallery | ✅ LIVE |
| **https://soulfra.github.io/voice-archive/inbox.html** | Voice Message Inbox (audio player) | ✅ LIVE |
| **https://soulfra.github.io/voice-archive/d489b26c/** | Individual Prediction Page | ✅ LIVE |
| **https://soulfra.github.io/voice-archive/ideas/** | **AI-Extracted Ideas Hub** | ✅ **NEW!** |
| **https://soulfra.github.io/voice-archive/feed.xml** | RSS Podcast Feed | ✅ LIVE |

### Main Sites
| URL | What It Is | Status |
|-----|------------|--------|
| **https://soulfra.com/** | Privacy-First AI Platform | ✅ LIVE |
| **https://soulfra.github.io/** | API Key Security Platform | ✅ LIVE |

### Brand Sites (All Live)
- https://calriven.com ✅
- https://deathtodata.com ✅
- https://mascotrooms.com ✅
- https://dealordelete.com ✅
- https://shiprekt.com ✅
- https://sellthismvp.com ✅
- https://saveorsink.com ✅
- https://finishthisrepo.com ✅
- https://finishthisidea.com ✅

---

## 🎯 Complete System Flow (How It All Works)

### 1. Voice Recording → Idea Extraction

```
YOU (on iPhone)
  ↓
Record voice memo: http://192.168.1.87:5001/voice
  ↓
Whisper Auto-Transcribes
  ↓
voice_memo_dissector.py --process-all
  ↓
Ollama AI Extracts:
  - Title
  - Summary
  - Concept
  - Tags
  - Domain (soulfra/calriven/deathtodata)
  - Technical requirements
  ↓
Saved to:
  - Database (voice_ideas table)
  - Markdown files (docs/voice-ideas/)
  ↓
Published to:
  - https://soulfra.github.io/voice-archive/ideas/
```

**Status:** ✅ WORKING END-TO-END

### 2. CringeProof Game (Coming Next)

```
Visit: https://soulfra.github.io/cringeproof/ (NOT LIVE YET)
  ↓
Read news article
  ↓
Record voice prediction
  ↓
AI judges over time
  ↓
Leaderboard (who aged well vs cringe)
```

**Status:** ⚠️ Code exists locally, not deployed

### 3. Business Onboarding (Phase 2B)

```
Business signs up via:
  - QR code scan
  - WhatsApp message
  - Telegram bot
  - Phone call
  - Text message
  ↓
Account created
  ↓
Device claimed
  ↓
Business records voice memos
  ↓
Published to: https://{businessname}.soulfra.com/
```

**Status:** ⚠️ Not built yet

---

## 📊 What You Can Do RIGHT NOW

### As YOU (the developer):

1. **Record Voice Ideas**
   ```bash
   # Visit on iPhone
   http://192.168.1.87:5001/voice

   # Record anything:
   - Business ideas
   - Recipes
   - Hardware specs
   - Technical thoughts
   - Meeting notes
   ```

2. **Extract & Publish**
   ```bash
   # Process all new recordings
   python3 voice_memo_dissector.py --process-all

   # Copy to voice-archive
   cp docs/voice-ideas/*.md voice-archive/ideas/
   cp docs/ideas/index.html voice-archive/ideas/

   # Publish
   cd voice-archive
   git add ideas/
   git commit -m "Add new ideas"
   git push origin main

   # Live in ~20 seconds at:
   # https://soulfra.github.io/voice-archive/ideas/
   ```

3. **View Ideas**
   ```
   Visit: https://soulfra.github.io/voice-archive/ideas/
   - See all extracted ideas
   - Click to read full concept
   - Listen to original voice recording
   - Filter by tags/domains
   ```

### As a VISITOR (anyone):

1. **Browse Ideas**
   - Visit https://soulfra.github.io/voice-archive/ideas/
   - See AI-extracted concepts
   - Click through to full details

2. **Listen to Voice**
   - Click "🎤 Voice Recording" on any idea
   - Hear original audio
   - See transcription

3. **Clone & Contribute**
   ```bash
   git clone https://github.com/Soulfra/voice-archive
   # Add your own ideas
   # Submit PR
   ```

---

## 🔧 Technical Stack

### What's Running
```
Local Development:
  - Flask server: http://localhost:5001
  - Ollama: http://localhost:11434
  - Whisper: Local CPU/GPU
  - SQLite: soulfra.db

GitHub:
  - Repos: Soulfra/voice-archive, Soulfra/{brands}
  - Actions: Auto-deploy on push
  - Pages: Static hosting (free)

AI:
  - Ollama (llama3.2:3b) - Idea extraction
  - Whisper - Voice transcription
  - No cloud APIs needed!
```

### Data Flow
```sql
-- Voice recordings
simple_voice_recordings (id, audio_data, transcription)
  ↓
-- AI-extracted ideas
voice_ideas (id, recording_id, title, text, ai_insight)
  ↓
-- Markdown docs
docs/voice-ideas/idea-{id}-{title}.md
  ↓
-- Published
soulfra.github.io/voice-archive/ideas/
```

---

## 🎯 Use Case Examples

### Example 1: Butter Recipes (Your Scenario)

```
1. Record 10 voice memos about butter recipes:
   - "Brown butter sage sauce..."
   - "Garlic herb compound butter..."
   - ... (8 more)

2. Process all recordings:
   python3 voice_memo_dissector.py --process-all

3. Result:
   docs/voice-ideas/
   ├── idea-6-brown-butter-sage-sauce.md
   ├── idea-7-garlic-herb-butter.md
   └── ... (10 files)

4. Publish:
   cp docs/voice-ideas/*.md voice-archive/ideas/
   git push

5. Live at:
   https://soulfra.github.io/voice-archive/ideas/
   - Searchable recipe gallery
   - Each with voice playback
   - AI-extracted ingredients & steps
```

### Example 2: Hardware Specs

```
1. Record voice memo:
   "I need to build a smart doorbell with..."

2. AI extracts:
   - Components: Camera, ESP32, PIR sensor
   - Requirements: WiFi, power supply
   - Related projects: Home automation

3. Generates:
   docs/hardware/hardware-8-smart-doorbell.md

4. Published with BOM (Bill of Materials)
```

### Example 3: Pitch Deck

```
1. Record business idea:
   "Here's my startup idea for..."

2. AI detects has_pitch: true

3. Generates:
   docs/pitches/pitch-9-startup-idea.md
   - Problem
   - Solution
   - Market
   - Traction

4. Ready for investors!
```

---

## 🚀 What's Coming Next (Phase 2B-D)

### Phase 2B: Business Onboarding (THIS WEEK)
- ✅ Create `businesses` table
- ✅ QR code signup flow
- ✅ Device claiming system
- ✅ Per-business subdomains

### Phase 2C: Multi-Channel Integration (NEXT WEEK)
- ✅ WhatsApp bot
- ✅ Telegram bot
- ✅ Phone call IVR
- ✅ SMS signup

### Phase 2D: CringeProof Deployment (NEXT WEEK)
- ✅ Push code to GitHub
- ✅ Enable GitHub Pages
- ✅ AI judging integration
- ✅ Leaderboard system

---

## 💡 Key Insights from Today

### What We Learned:

1. **Hash Consistency Matters**
   - Fixed: d489b26c (8 chars) vs d489b26c288a (12 chars)
   - Directory name must match links!

2. **Device ID ≠ Username**
   - device_id = MAC address (hardware)
   - user_id = Account (person)
   - business_id = Organization
   - They're linked, not conflated!

3. **No More Hardcoded Usernames**
   - device_config.py looks up owner dynamically
   - Localhost-only by default
   - Claimed devices publish to GitHub

4. **Voice → Docs Works!**
   - Speak naturally
   - AI extracts structure
   - Published automatically
   - No manual writing needed

---

## 📋 Commands Cheat Sheet

```bash
# === VOICE RECORDING ===
# Visit on iPhone
http://192.168.1.87:5001/voice

# === IDEA EXTRACTION ===
# Process new recordings
python3 voice_memo_dissector.py --process-all

# Process specific recording
python3 voice_memo_dissector.py --recording-id 7

# Reprocess with better prompt
python3 voice_memo_dissector.py --recording-id 7 --reprocess

# === PUBLISHING ===
# Copy to voice-archive
cp docs/voice-ideas/*.md voice-archive/ideas/

# Commit and push
cd voice-archive
git add ideas/
git commit -m "Add new ideas"
git push origin main

# === DEVICE MANAGEMENT ===
# Check device status
python3 device_config.py --show

# Claim device
python3 device_config.py --claim --github Soulfra --notify github

# === DATABASE ===
# List all ideas
sqlite3 soulfra.db "SELECT id, title FROM voice_ideas"

# View idea details
sqlite3 soulfra.db "SELECT * FROM voice_ideas WHERE id = 2"
```

---

## 🎉 Summary

### ✅ What's Live NOW:
1. Voice-archive gallery (predictions)
2. Voice ideas hub (AI-extracted concepts)
3. RSS feed (podcast)
4. Individual prediction pages
5. 9 brand domains

### ✅ What Works Locally:
1. Voice recording (iPhone)
2. Whisper transcription
3. Ollama idea extraction
4. Markdown doc generation
5. Device config (no hardcoded names!)

### ⚠️ What's Next:
1. Deploy CringeProof game
2. Build business onboarding
3. Add WhatsApp/Telegram bots
4. Recipe validation system
5. Per-business subdomains

---

**You asked:** *"how does this work then? i mean idk we have the stuff on github? so how do we see cringeproof"*

**Answer NOW:**
- ✅ Ideas hub is live: https://soulfra.github.io/voice-archive/ideas/
- ⚠️ CringeProof is NOT live yet (code exists, not deployed)
- ✅ Voice → Docs pipeline works end-to-end
- ⚠️ Business onboarding needs to be built

**Next:** Deploy CringeProof so you can actually SEE the game!

---

**Status:** ✅ Phase 2A Complete
**Time:** <2 hours
**Result:** Ideas hub published, voice-to-docs pipeline working!
