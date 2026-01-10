# Testing Guide - How to Actually Test This Shit

**The confusion is real. Here's how to test each layer without going insane.**

---

## The Confusion Map

### You Have 3 voice-archive Folders:
1. `/Users/matthewmauer/Desktop/voice-archive` - **Standalone repo**
2. `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive` - **Flask serves from here**
3. Possibly more on GitHub - `Soulfra/voice-archive`

### You Have 5 Domains:
1. **soulfra.com** - Main platform
2. **cringeproof.com** - Voice capture
3. **calriven.com** - Real estate
4. **deathtodata.com** - Privacy
5. **stpetepros.com** - Tampa Bay pros

### You Have 3 Servers Running:
1. **Port 5001** - Main Soulfra Flask app
2. **Port 5002** - CringeProof API (isolated microservice)
3. **Port 8888** - Mesh router (if running)

---

## Quick Test Commands

### 1. Check What's Running

```bash
# See all running servers
lsof -i :5001
lsof -i :5002
lsof -i :8888

# Check Flask is serving
curl -k https://192.168.1.87:5002/health

# Check soul leaderboard API
curl -k https://192.168.1.87:5002/api/soul/agents | python3 -m json.tool
```

### 2. Test Voice Upload

```bash
# Test voice endpoint exists
curl -k -X POST https://192.168.1.87:5002/api/simple-voice/save \
  -H "Content-Type: application/json" \
  -d '{"text": "Test voice memo", "source": "test"}'
```

### 3. Test Screenshot OCR

```bash
# Test screenshot text endpoint
curl -k -X POST https://192.168.1.87:5002/api/screenshot-text/save \
  -H "Content-Type: application/json" \
  -d '{"text": "Debug notes from screenshot", "source": "ocr_test"}'
```

### 4. Test Soul Leaderboard

```bash
# Get all agents
curl -k https://192.168.1.87:5002/api/soul/agents | jq '.agents[] | {name: .agent_name, votes: .net_votes}'

# Vote on an agent
curl -k -X POST https://192.168.1.87:5002/api/soul/vote-agent \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "soulfra", "vote": 1, "session_id": "test123"}'

# Check leaderboard
curl -k https://192.168.1.87:5002/api/soul/leaderboard-rotating | jq '.leaderboard[] | {rank, agent_name, hot_score}'
```

---

## Testing Workflows

### Workflow 1: Voice Memo → README

**What you want:**
- Record voice memo on phone
- AirDrop to Mac
- Auto-transcribe with Whisper
- Ollama generates README section
- Preview before commit

**Current status:** Partially built
**Missing:** Auto-README generation from voice

**How to test:**
```bash
# 1. Record voice on iPhone (Voice Memos app)
# 2. AirDrop to Mac Downloads folder
# 3. Run this:

cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Import voice memo
python3 << 'EOF'
import requests

# Simulate voice upload
response = requests.post('https://192.168.1.87:5002/api/simple-voice/save',
    json={
        'text': 'This is a test voice memo about building Soulfra',
        'source': 'iphone',
        'session_id': 'test-voice-readme'
    },
    verify=False
)

print(response.json())
EOF

# 4. Check database
sqlite3 soulfra.db "SELECT id, transcription, created_at FROM simple_voice_recordings ORDER BY id DESC LIMIT 5;"
```

### Workflow 2: Screenshot → OCR → Debug

**What you want:**
- Take screenshot of code/notes on phone
- Upload to cringeproof.com/screenshot
- OCR extracts text
- Ollama analyzes for bugs/issues

**Current status:** API exists, no UI
**Missing:** Screenshot upload page

**How to test:**
```bash
# Visit https://192.168.1.87:5002/screenshot (will create this)
# Or test API directly:

curl -k -X POST https://192.168.1.87:5002/api/screenshot-text/save \
  -H "Content-Type: application/json" \
  -d '{
    "text": "def calculate_hot_score(votes_up, votes_down, timestamp):\n    net_votes = votes_up - votes_down\n    return net_votes",
    "source": "debug_screenshot"
  }'
```

### Workflow 3: Test GitHub Profile Changes

**What you want:**
- Push changes to github.com/Soulfra/.github
- See dynamic README update
- Verify snake animation works
- Check leaderboard auto-updates

**How to test:**
```bash
cd soulfra-dotgithub

# Check what will be pushed
git status
git diff profile/README.md

# Push to GitHub
git add .
git commit -m "test: Update GitHub profile README"
git push origin main

# Wait 1-2 minutes, then check:
# https://github.com/Soulfra

# Manually trigger GitHub Actions:
# 1. Go to https://github.com/Soulfra/.github/actions
# 2. Click "Generate Snake Animation" → Run workflow
# 3. Click "Update Leaderboard Stats" → Run workflow
```

### Workflow 4: Test Domain Routing

**What you want:**
- soulfra.com → GitHub Pages or Flask?
- cringeproof.com → Flask API?
- Local testing before DNS changes

**How to test:**
```bash
# Check DNS records
dig soulfra.com
dig cringeproof.com

# Test local routing
curl -k https://192.168.1.87:5002 | head -20

# Test if domains point to GitHub Pages
curl -I https://soulfra.github.io
curl -I https://cringeproof.com

# Add to /etc/hosts for local testing:
# 127.0.0.1 soulfra.local
# Then test: http://soulfra.local:5002
```

### Workflow 5: Test StPetePros Voice Chat

**What you want:**
- Tampa Bay tech community
- Voice Q&A format
- Business owners ask, tech experts answer

**Current status:** Database schema exists (voice Q&A)
**Missing:** StPetePros-specific interface

**How to test:**
```bash
# Check voice Q&A system
curl -k https://192.168.1.87:5002/build-profile-voice.html

# Check if stpetepros agent exists
curl -k https://192.168.1.87:5002/api/soul/agents | jq '.agents[] | select(.agent_name=="stpetepros")'

# Visit: https://192.168.1.87:5002/soul/leaderboard
# Should see StPetePros in list
```

---

## Debug Dashboard (Will Create)

### Quick Links
- **Soul Leaderboard:** https://192.168.1.87:5002/soul/leaderboard
- **Live Feed:** https://192.168.1.87:5002/soul/feed-page
- **Soul Dashboard:** https://192.168.1.87:5002/soul
- **Voice Q&A:** https://192.168.1.87:5002/build-profile-voice.html
- **Health Check:** https://192.168.1.87:5002/health

### Port Map
```
5001 → Main Soulfra Flask (if running)
5002 → CringeProof API (isolated microservice) ✅
8888 → Mesh Router (if running)
11434 → Ollama (local LLM)
```

### Database Locations
```
soulfra.db → /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra.db
cringeproof.db → If separate database exists
```

### Git Repos
```
Working Folder:
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

Voice Archive (which one?):
/Users/matthewmauer/Desktop/voice-archive (standalone)
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice-archive (Flask serves from)

GitHub Profile:
/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra-dotgithub
→ Pushes to github.com/Soulfra/.github
```

---

## Common Test Scenarios

### Test 1: "I recorded a voice memo, where did it go?"

```bash
# Check database
sqlite3 soulfra.db "SELECT id, transcription, created_at FROM simple_voice_recordings ORDER BY created_at DESC LIMIT 10;"

# Check file system
ls -lth voice-archive/ | head -20
ls -lth /Users/matthewmauer/Desktop/voice-archive/ | head -20
```

### Test 2: "I pushed to GitHub, how do I see changes?"

```bash
# Check git status
cd soulfra-dotgithub
git log --oneline -5
git remote -v

# Verify push succeeded
git status

# Check GitHub directly
open https://github.com/Soulfra/.github
```

### Test 3: "Soul leaderboard shows wrong data"

```bash
# Delete database and restart
rm soulfra.db
python3 cringeproof_api.py

# Check new data
curl -k https://192.168.1.87:5002/api/soul/agents | jq '.agents[] | {name: .agent_name, version: .soul_document_version}'

# Should show 5 agents:
# - soulfra (v1.0)
# - cringeproof (v1.0)
# - calriven (v1.0)
# - deathtodata (v1.0)
# - stpetepros (v1.0)
```

### Test 4: "Screenshot OCR not working"

```bash
# Test endpoint exists
curl -k https://192.168.1.87:5002/api/screenshot-text/save

# Should return: {"error": "No text provided", "success": false}
# This means endpoint works, just needs text parameter
```

### Test 5: "Can't test on phone"

```bash
# Get your Mac's local IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# On iPhone, visit:
# https://192.168.1.87:5002/soul/leaderboard

# If SSL error, accept certificate warning
```

---

## Quick Fixes

### Fix 1: Port already in use
```bash
lsof -ti:5002 | xargs kill -9
python3 cringeproof_api.py
```

### Fix 2: Database locked
```bash
rm soulfra.db-journal 2>/dev/null
sqlite3 soulfra.db "PRAGMA integrity_check;"
```

### Fix 3: Ollama not responding
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:latest",
  "prompt": "test",
  "stream": false
}'
```

### Fix 4: Can't find voice-archive
```bash
# Find all instances
find /Users/matthewmauer/Desktop -name "voice-archive" -type d

# Check which Flask serves
ps aux | grep python | grep 5002
# See working directory
```

### Fix 5: GitHub Actions not running
```bash
# Check .github/workflows/ exists
ls -la soulfra-dotgithub/.github/workflows/

# Verify YAML syntax
cat soulfra-dotgithub/.github/workflows/snake-animation.yml

# Push again
cd soulfra-dotgithub
git add .github/
git commit -m "fix: Add GitHub Actions workflows"
git push origin main
```

---

## Testing Checklist

Before saying "it works":

- [ ] Flask running on port 5002
- [ ] Soul leaderboard shows 5 agents (not 4)
- [ ] Can vote on agents (upvote/downvote)
- [ ] Voice upload works (test with curl)
- [ ] Screenshot OCR endpoint responds
- [ ] GitHub profile README has typing animation
- [ ] Snake animation workflow exists
- [ ] Leaderboard update workflow exists
- [ ] All 5 domains in BRANDS.md are represented
- [ ] Database has correct agent data
- [ ] Can test on iPhone (via local IP)

---

## Next Steps to Build

1. **Create /screenshot page** - Upload screenshots for OCR debugging
2. **Create /debug dashboard** - See all repos, ports, status
3. **Voice → README pipeline** - Auto-generate README from voice
4. **StPetePros voice chat** - Tampa Bay tech Q&A
5. **Consolidate voice-archive** - Figure out which folder is real

Check `TESTING_GUIDE.md` (this file) before pushing anything to production.
