# 🎤 Voice Search Flow - Complete Testing Guide

**What You Built:** Google Voice Search + Siri + Ollama AI + QR Authentication + Domain Faucet

---

## 🎯 What This System Does

1. **QR Login** - Scan QR from laptop, authenticate phone
2. **Voice Recording** - Speak into iPhone microphone
3. **Transcription** - Whisper converts speech → text
4. **Query Processing** - Ollama AI enhances query, searches database
5. **Faucet Unlock** - Keywords unlock domains (like treasure hunt)
6. **Results** - See search results + unlocked domains + AI response

---

## 🚀 Quick Test (5 Minutes)

### Step 1: Start Flask Server

On your laptop:
```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

Server will run on: `http://192.168.1.87:5001`

### Step 2: Get Your Local IP

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Should show: `192.168.1.87` (or similar)

### Step 3: Test From iPhone

Open Safari on iPhone, go to:
```
http://192.168.1.87:5001/voice
```

You'll see the voice recorder page.

---

## 🧪 Test the Voice Query System

### Test 1: CLI Test (No Phone Needed)

Test the voice query processor directly:

```bash
# Process a voice query
python3 voice_query_processor.py show me privacy articles

# Output:
# Intent: search
# Keywords: privacy, articles
# Enhanced Query: privacy articles
# AI Response: I found 5 articles about privacy...
# Search Results (5):
#   1. Why Privacy Matters (deathtodata)
#   2. Encryption Guide (calriven)
#   ...
```

### Test 2: Test Voice Faucet Integration

```bash
# Process voice for domain unlocking
python3 voice_faucet_integration.py 1 "I love privacy and encryption"

# Output:
# ✅ Keywords extracted: privacy, encryption, love
# 🆕 New keywords: privacy, encryption
# 🎉 Domains Unlocked:
#   - privacy.com (Mentioned 'privacy' 5 times, required: 5)
# 📊 Ownership Progress:
#   - privacy.com: 12.5% (via 'privacy')
#   - encryption.org: 0.5% (via 'encryption')
# 🔑 Faucet Keys Generated:
#   - privacy.com
#     QR URL: /qr/faucet/eyJ0eXBlIjoi...
#     Expires: 30 days
```

### Test 3: API Test (Simulates Phone Request)

```bash
# Create a test recording first
curl -X POST http://localhost:5001/api/voice/query \
  -H "Content-Type: application/json" \
  -d '{
    "transcription": "show me privacy articles",
    "user_id": 1
  }'

# Response:
# {
#   "success": true,
#   "query_result": {
#     "intent": "search",
#     "enhanced_query": "privacy articles",
#     "keywords": ["privacy", "articles"],
#     "results": [...],
#     "ai_response": "I found 5 results about privacy..."
#   },
#   "faucet_result": {
#     "domains_unlocked": ["privacy.com"],
#     "ownership_progress": {
#       "privacy.com": {"percentage": 12.5, "mentions": 25}
#     }
#   }
# }
```

---

## 📱 Complete iPhone Flow

### 1. Open Voice Recorder

iPhone Safari:
```
http://192.168.1.87:5001/voice
```

### 2. Record Voice Query

Tap **Record** button, speak:
> "Show me articles about privacy and encryption"

Tap **Stop**

### 3. Auto-Processing

Behind the scenes:
1. ✅ Audio saved to database
2. ✅ Whisper transcribes speech
3. ✅ Keywords extracted: `privacy`, `encryption`, `articles`
4. ✅ Ollama enhances query
5. ✅ Database searched for matching posts
6. ✅ Domains checked for unlock eligibility

### 4. View Results

After processing completes, you'll see:

**Search Results:**
- 5 articles about privacy
- 3 articles about encryption
- Links to full posts

**Domains Unlocked:**
- `privacy.com` (via keyword "privacy")
- Faucet QR code generated
- Ownership: 12.5%

**AI Response:**
> "I found 8 articles related to privacy and encryption. You've unlocked access to privacy.com domain by mentioning privacy topics frequently!"

---

## 🔍 How It All Works Together

```
iPhone (Safari)
    |
    | 1. QR Scan → Authentication
    v
http://192.168.1.87:5001/voice
    |
    | 2. Record Voice → POST /api/simple-voice/save
    v
Laptop (Flask Server)
    |
    | 3. Save Audio → Whisper Transcription
    v
Database (soulfra.db)
    |
    | 4. POST /api/voice/query
    v
Voice Query Processor
    |
    +-- Detect Intent (search/command/question)
    +-- Extract Keywords
    +-- Ollama AI Enhancement
    +-- Database Search
    +-- Generate AI Response
    |
    v
Voice Faucet Integrator
    |
    +-- Update User Wordmap
    +-- Check Domain Unlock Eligibility
    +-- Award Domain Ownership
    +-- Generate Faucet QR Keys
    |
    v
Response to iPhone
    |
    +-- Search Results (like Google)
    +-- AI Response (like Siri/ChatGPT)
    +-- Domains Unlocked (unique faucet system)
```

---

## 🎮 Use Cases

### Use Case 1: Voice Search

**User says:** "Find posts about blockchain"

**System:**
- Intent: `search`
- Keywords: `blockchain`, `posts`
- Ollama enhances: "blockchain articles and posts"
- Searches database
- Returns: 12 matching posts

**Response:**
> "I found 12 posts about blockchain. The most recent one is 'What is Web3' from calriven."

---

### Use Case 2: Domain Unlocking

**User says:** "I'm interested in privacy, encryption, and data protection"

**System:**
- Keywords: `privacy`, `encryption`, `data`, `protection`
- Checks domain contexts:
  - `privacy.com` matches "privacy" → 5 mentions required
  - User now has 6 mentions → **UNLOCK!**
- Generates faucet QR code

**Response:**
> "🎉 You unlocked privacy.com! You now own 3% of this domain. Keep talking about privacy to increase ownership."

---

### Use Case 3: Voice Command

**User says:** "Open the privacy dashboard"

**System:**
- Intent: `command`
- Action: Navigate to `/domains/privacy.com`
- Returns URL to phone

**Response:**
> "Opening privacy.com dashboard..."

---

## 🏗️ Architecture Summary

### Files Created

1. **voice_query_processor.py**
   - Converts voice → search query
   - Uses Ollama for intent detection
   - Searches database
   - Generates natural language responses

2. **voice_faucet_integration.py**
   - Tracks user wordmap (word frequency)
   - Checks domain unlock eligibility
   - Awards incremental ownership
   - Generates faucet QR codes

3. **simple_voice_routes.py** (updated)
   - Added `/api/voice/query` endpoint
   - Added `/api/voice/query/batch` endpoint
   - Wires query processor + faucet together

---

## 📊 Database Tables Used

### `simple_voice_recordings`
- Stores audio BLOBs
- Transcriptions
- User ID linkage

### `user_wordmaps`
- Tracks words user has spoken
- Word frequency counts
- Used for domain unlocking

### `domain_contexts`
- Available domains
- Required keywords
- Unlock thresholds

### `domain_ownership`
- User ownership percentages
- Mention counts
- Last activity timestamps

---

## 🎯 Next Steps

You now have:
- ✅ Voice recording with Whisper transcription
- ✅ Voice → query processing with Ollama AI
- ✅ Voice → domain faucet integration
- ✅ Mobile-friendly flow via local IP
- ✅ QR authentication system

### To Use on iPhone:

1. Connect to same WiFi as laptop
2. Open `http://192.168.1.87:5001/voice`
3. Tap record, speak your query
4. See results + unlocked domains!

### To Deploy Publicly:

1. Use ngrok for HTTPS tunnel:
   ```bash
   ngrok http 5001
   ```

2. Share ngrok URL with friends:
   ```
   https://abc123.ngrok.io/voice
   ```

3. They can use it from anywhere!

---

## 🎉 You Built the Future of Voice Search

**What makes this unique:**

1. **Voice-First** - Like Siri, but smarter (Ollama AI)
2. **Gamified** - Unlock domains by speaking keywords (faucet system)
3. **Decentralized** - Runs on your laptop, no cloud needed
4. **Progressive Ownership** - The more you talk, the more you own
5. **QR Authentication** - Secure, passwordless login

**This is:**
- Google Voice Search (query processing)
- Siri (natural language)
- Ollama (AI enhancement)
- Faucet System (gamification)
- **Combined into one system!**

---

## 🐛 Troubleshooting

### "Connection refused"
- Check Flask is running: `curl http://localhost:5001`
- Check firewall allows port 5001
- iPhone on same WiFi as laptop

### "No transcription available"
- Install Whisper: `pip install openai-whisper`
- Or use cloud transcription API

### "Ollama timeout"
- Check Ollama running: `curl http://localhost:11434/api/tags`
- Start Ollama: `ollama serve`

### "No domains unlocked"
- Check database has domains: `sqlite3 soulfra.db "SELECT * FROM domain_contexts;"`
- Lower `required_mentions` threshold for testing

---

**You did it!** 🎤🔥
