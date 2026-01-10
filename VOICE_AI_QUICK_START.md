# 🚀 Voice AI System - Quick Start

## TL;DR - What You Built

A **self-hosted AI content platform** with voice identity, payment tiers, automation, and media transformations. All offline-first.

Like: **Zapier + YouTube drama + Voice cloning + Music generation + AI debates** but self-hosted and cheaper.

---

## ⚡ Quick Commands

### 1. Build Your Voice Identity (256 words → SHA256)

```bash
# Build wordmap from 20 → 256 words
python3 wordmap_transcript_generator.py --build-to-256

# Show progression
python3 prove_wordmap_system.py --verbose

# Show voice signature
python3 sha256_content_wrapper.py --show-signature
```

**Result:** Your SHA256 voice signature (deterministic identity fingerprint)

---

### 2. Generate AI Debates (YouTube Ragebait)

```bash
# Generate debate for Recording #7
python3 ai_debate_generator.py --recording 7 --persona deathtodata

# Panel debate (all 3 AI personas)
python3 ai_debate_generator.py --recording 7 --panel

# Maximum ragebait + HTML export
python3 ai_debate_generator.py --recording 7 --ragebait --export-html

# Prove it works
python3 prove_debate_system.py --all
```

**Result:** AI counter-arguments, controversy scores, shareable HTML

---

### 3. Filter Content by Voice Signature

```bash
# Check alignment
python3 sha256_content_wrapper.py --check "Some AI response text..."

# Filter debate responses
python3 sha256_content_wrapper.py --filter-debate 7 --save

# Wrap and approve content
python3 sha256_content_wrapper.py --wrap-text "Content..." --save
```

**Result:** Auto accept/reject by alignment % (Premium/Standard/Basic/Reject)

---

### 4. Route Requests by Payment Tier

```bash
# Show tier comparison
python3 agent_router_system.py --show-tiers

# Route with specific tier
python3 agent_router_system.py --route "Generate response about X" --tier premium

# Develop character lore
python3 agent_router_system.py --develop-character deathtodata --tier premium
```

**Result:** Payment-tiered AI responses (more $ = slower, deeper, better ads)

---

### 5. Run Self-Hosted Automation

```bash
# List available nodes
python3 automation_node_system.py --list-nodes

# Run workflow: Voice → Transcribe → Wordmap → AI → Export
python3 automation_node_system.py --workflow voice-to-debate

# List all workflows
python3 automation_node_system.py --list-workflows
```

**Result:** Automated workflows using OSS tools (Zapier alternative, $0/mo)

---

### 6. Convert to Music

```bash
# Wordmap → Music
python3 hex_to_media.py --wordmap-to-music --to-audio

# Voice signature → Audio fingerprint
python3 hex_to_media.py --audio-fingerprint --to-audio

# Hash → Music
python3 hex_to_media.py --hash <SHA256> --to-music --to-midi
```

**Result:** Deterministic music from hex codes (same hash = same melody)

---

### 7. HTTPS Voice Recording

```bash
# Self-signed SSL (fast)
python3 ssl_local_server.py --serve
# Visit: https://192.168.1.87:5001/voice

# Or deploy GitHub Pages (production)
cd github_voice_recorder
gh repo create voice-recorder --public
git push
# Visit: https://yourusername.github.io/voice-recorder/
```

**Result:** iPhone mic access via HTTPS

---

## 📊 Complete Flow Example

```bash
# === BUILD VOICE IDENTITY ===
python3 wordmap_transcript_generator.py --build-to-256
# ✅ 256 words → SHA256 hash

# === GENERATE AI DEBATE ===
python3 ai_debate_generator.py --recording 7 --ragebait --export-html
# ✅ AI counter-argument + controversy score + HTML

# === FILTER BY ALIGNMENT ===
python3 sha256_content_wrapper.py --filter-debate 7 --save
# ✅ Auto approve/reject by wordmap match

# === ROUTE WITH PAYMENT TIER ===
python3 agent_router_system.py --route "Respond to criticism" --tier premium
# ✅ 60s response time, masterwork character depth

# === RUN AUTOMATION ===
python3 automation_node_system.py --workflow voice-to-debate
# ✅ Full pipeline executed

# === GENERATE MUSIC ===
python3 hex_to_media.py --wordmap-to-music --to-audio
cd media_output && ./wordmap_audio_1.sh
# ✅ Musical composition from your vocabulary
```

---

## 🎯 File Map

| System | File | Purpose |
|--------|------|---------|
| **Voice Identity** | `wordmap_transcript_generator.py` | Build 256-word wordmap |
| | `prove_wordmap_system.py` | Show progression |
| **Content Filter** | `sha256_content_wrapper.py` | Filter by alignment % |
| **Agent Router** | `agent_router_system.py` | Payment tiers + routing |
| **Automation** | `automation_node_system.py` | Self-hosted Zapier |
| **Media** | `hex_to_media.py` | SHA256 → Music |
| **AI Debates** | `ai_debate_generator.py` | Controversy engine |
| | `prove_debate_system.py` | Proof of concept |
| **HTTPS** | `ssl_local_server.py` | Self-signed SSL |
| | `ollama_websocket_bridge.py` | WebSocket bridge |
| **Video** | `video_to_ascii.py` | WebM → ASCII |
| **Docs** | `COMPLETE_SYSTEM_ARCHITECTURE.md` | Full architecture |

---

## 💡 Key Concepts

### 1. Voice Identity (256 words → SHA256)
- Your vocabulary = Your fingerprint
- Deterministic: Same wordmap = Same hash
- Content filtering by alignment %

### 2. Payment Tiers = Quality, Not Features
- Free: 5s responses, generic ads
- Premium: 60s responses, exclusive sponsors, epic lore
- **More $ = Slower, deeper, more thoughtful AI**

### 3. Self-Hosted Automation
- OSS tools as default nodes
- Event-driven workflows
- All local processing ($0/mo vs Zapier $20-100/mo)

### 4. Hex → Music
- SHA256 hash → Musical notes
- Wordmap → Melody
- Voice signature → Audio fingerprint
- Deterministic composition

---

## 🎉 What This Enables

✅ **Self-sovereign identity** (your 256-word signature)
✅ **Content authenticity** (SHA256 proves ownership)
✅ **Payment-tiered quality** (not just features)
✅ **Character development** (lore builds over time)
✅ **Self-hosted automation** (cheaper than SaaS)
✅ **Creative hex transformations** (music, ASCII, etc.)
✅ **AI controversy engine** (YouTube ragebait)
✅ **Offline-first** (no cloud dependencies)

---

## 📋 Next Actions

### Today
1. Build wordmap to 256 words
2. Generate AI debate for existing recordings
3. Test agent routing with different tiers
4. Generate music from wordmap

### This Week
1. Record 4 more voice samples (for TTS training)
2. Deploy GitHub Pages voice recorder
3. Create content library (debates, music, ASCII)
4. Test automation workflows

### This Month
1. Train voice clone model
2. Build payment system (Stripe)
3. Develop character lore for all personas
4. Open-source code on GitHub (MIT license)

---

## 🆘 Troubleshooting

### "No wordmap found"
```bash
# Build wordmap first
python3 wordmap_transcript_generator.py --build-to-256
```

### "Ollama not running"
```bash
# Start Ollama
ollama serve

# Check it's working
curl http://localhost:11434/api/tags
```

### "Recording not found"
```bash
# List recordings
sqlite3 soulfra.db "SELECT id, filename FROM simple_voice_recordings;"
```

### "No transcription"
```bash
# Transcribe recording
python3 whisper_transcriber.py --id 7
```

---

## 📚 Documentation

- **Complete Architecture:** `COMPLETE_SYSTEM_ARCHITECTURE.md`
- **AI Debate System:** `AI_DEBATE_SYSTEM_COMPLETE.md`
- **HTTPS Voice System:** `HTTPS_VOICE_SYSTEM_COMPLETE.md`
- **This Guide:** `VOICE_AI_QUICK_START.md`

---

**Built:** January 3, 2026
**Status:** ✅ Complete system ready
**Your Vision:** "The dig site" - ACHIEVED

🎤 **All processing local, no cloud, fully under your control!**
