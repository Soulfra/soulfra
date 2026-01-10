# 🎮 AI BATTLE ARENA - Game Design Document
**Soulfra Public Interactive Service**

---

## 🎯 Vision

Transform Soulfra into a fun, interactive public service where:
- **Users submit prompts** → AI models compete to write best response
- **Roommates vote** on which AI wrote the best content
- **Leaderboard tracks** which AI models win most often
- **Privacy-first** - all data encrypted/hashed, QR authentication required
- **Local/network only** - localhost + roommate network access

---

## 🏗️ System Architecture

### Already Built (Security Foundation):
✅ **PII Protection** - IPs hashed, GPS encrypted, logs redacted
✅ **QR Authentication** - Scan QR to login, session-based access
✅ **Geofencing Ready** - GPS radius matching (20-50km based on reputation)
✅ **Reputation System** - XP tracking, trust scores, level progression
✅ **Multi-Domain Publishing** - 9 AI models, 8 brand domains

### Newly Added (Battle Arena):
✅ **Battle Routes** (`battle_routes.py`)
✅ **Database Tables** (battle_sessions, battle_responses, battle_votes, battle_stats)
✅ **AI vs AI Competition** - Multiple models generate responses simultaneously
✅ **Voting System** - Upvote/downvote AI responses
✅ **Leaderboard** - Track AI win/loss records

---

## 🎮 How to Play

### Step 1: Access the Arena
```
From your laptop: http://192.168.1.87:5001/battle
From roommate's device: http://192.168.1.87:5001/login_qr
```

1. Scan QR code to authenticate
2. Session expires after timeout (configurable)
3. Geofencing: Only people within radius can access

### Step 2: Create a Battle
```
1. Click "New Battle"
2. Enter prompt: "Write a haiku about encryption"
3. Select category: creative, code, explanation, debate, horoscope
4. Choose AI models (2-4):
   - soulfra-model (security expert 🔐)
   - deathtodata-model (privacy advocate 🕵️)
   - drseuss-model (creative storyteller 🎭)
   - calos-model (architecture expert 🏗️)
   - publishing-model (content specialist 📝)
   - visual-expert (vision specialist 👁️)
   - codellama:7b (code expert 💻)
   - mistral:7b (general reasoning 🧠)
5. Click "Start Battle!"
```

### Step 3: AI Models Compete
- AI models generate responses in background (async)
- Each model gets same prompt
- Responses stored in battle_responses table
- Battle status changes: generating → active

### Step 4: Vote for Winner
```
1. Read all AI responses
2. Click ⬆️ (upvote) or ⬇️ (downvote) on each
3. Can change vote anytime
4. Votes stored: battle_votes table
5. Stats updated: battle_stats table
```

### Step 5: Check Leaderboard
```
Visit: /battle/leaderboard

See rankings:
- Total battles
- Wins / Losses
- Win rate %
- Average votes per battle
- Last battle timestamp
```

---

## 📊 Database Schema

### `battle_sessions`
Stores individual battle instances:
```sql
id              INTEGER PRIMARY KEY
prompt          TEXT (user's prompt)
category        TEXT (general, code, creative, etc.)
creator_user_id INTEGER (who created battle)
models          TEXT (JSON array of model names)
status          TEXT (generating, active, completed)
created_at      TIMESTAMP
expires_at      TIMESTAMP
```

### `battle_responses`
AI-generated responses:
```sql
id              INTEGER PRIMARY KEY
battle_id       INTEGER (foreign key)
model_name      TEXT (which AI model)
response_text   TEXT (AI's response)
generated_at    TIMESTAMP
```

### `battle_votes`
User votes:
```sql
id              INTEGER PRIMARY KEY
battle_id       INTEGER
response_id     INTEGER (which AI response)
voter_user_id   INTEGER (who voted)
vote_type       TEXT (upvote or downvote)
created_at      TIMESTAMP
UNIQUE(battle_id, voter_user_id, response_id)
```

### `battle_stats`
AI leaderboard:
```sql
id                      INTEGER PRIMARY KEY
model_name              TEXT UNIQUE
total_battles           INTEGER
wins                    INTEGER
losses                  INTEGER
total_votes             INTEGER
avg_votes_per_battle    REAL
last_battle_at          TIMESTAMP
```

---

## 🎯 Battle Categories

### 1. **General** (Default)
- Open-ended questions
- Explanations
- Opinions

### 2. **Code**
- Programming challenges
- Algorithm explanations
- Debugging help
- Code review

### 3. **Creative**
- Stories
- Poetry (haikus, limericks)
- Song lyrics
- Fictional scenarios

### 4. **Explanation**
- How things work
- Simplified explanations (ELI5)
- Technical documentation

### 5. **Debate**
- Pros/cons
- Different perspectives
- Argument for/against

### 6. **Horoscope** (NEW!)
- Daily horoscope generation
- Personalized based on user input
- 13-month calendar support

---

## 🏆 Leaderboard & Rankings

### Win Calculation:
1. Battle ends when voting slows down
2. Winner = AI with most net votes (upvotes - downvotes)
3. Stats updated:
   - Winner: `wins += 1`
   - Others: `losses += 1`
   - All: `total_battles += 1`, `total_votes += vote_count`

### Rankings Displayed:
```
Rank | AI Model             | Battles | Wins | Losses | Win Rate | Avg Votes
-----|----------------------|---------|------|--------|----------|----------
1    | soulfra-model       | 42      | 28   | 14     | 66.7%    | 12.3
2    | drseuss-model       | 38      | 24   | 14     | 63.2%    | 15.1
3    | deathtodata-model   | 35      | 20   | 15     | 57.1%    | 9.8
4    | calos-model         | 29      | 15   | 14     | 51.7%    | 8.2
5    | publishing-model    | 31      | 14   | 17     | 45.2%    | 10.5
```

---

## 🚀 Next Features to Build

### Week 2: Article Competition System
**Goal:** Multiple AI models write articles on same topic → users vote → winner publishes to civicresume.com

**New Files:**
- `article_competition.py` - Article battle generator
- `article_routes.py` - Voting/publishing routes
- `ARTICLE-TEMPLATES.md` - Article format guide

**Features:**
- Topic rotation (daily/weekly themes)
- Research integration (AI fetches sources)
- Citation tracking
- Publishing workflow
- Analytics dashboard

### Week 3: Horoscope Generator
**Goal:** Users input birthday/interests → AI generates personalized horoscopes

**New Files:**
- `horoscope_generator.py` - AI-powered horoscope system
- `calendar_helpers.py` - 13-month calendar support
- `horoscope_routes.py` - User interface

**Features:**
- Birthday/zodiac input
- Interest/personality quiz
- Daily rotation
- 13-month calendar (lunar, custom systems)
- Personalization engine

### Week 4: Public Service Launch
**Goal:** Open to public with documentation + analytics

**Tasks:**
- Create `/public` route - Public-facing interface
- Write user guide - How to play, vote, earn XP
- Analytics dashboard - Track usage, popular features
- QR code generation - Easy network access
- Testing suite - localhost + network verification

---

## 🎮 Example Battle Flow

### Battle #1: "Write a haiku about encryption"

**Prompt:** Write a haiku about encryption

**Category:** Creative

**Models:** soulfra-model, drseuss-model, deathtodata-model

**Responses:**

1. **soulfra-model (🔐):**
   ```
   Keys hide in the dark,
   Cipher text flows like a stream,
   Secrets safe from sight.
   ```
   **Votes:** ⬆️ 5 | ⬇️ 1 | Net: +4

2. **drseuss-model (🎭):**
   ```
   Oh, the keys you'll lock!
   Oh, the data you'll block!
   With ciphers so grand,
   No one will understand!
   ```
   **Votes:** ⬆️ 8 | ⬇️ 0 | Net: +8

3. **deathtodata-model (🕵️):**
   ```
   Encrypt all the things,
   Big Tech cannot track your trails,
   Privacy first, win.
   ```
   **Votes:** ⬆️ 6 | ⬇️ 2 | Net: +4

**Winner:** drseuss-model (🎭) with +8 net votes!

**Stats Updated:**
- drseuss-model: wins +1
- soulfra-model: losses +1
- deathtodata-model: losses +1

---

## 📱 Network Access

### Localhost (Your Laptop):
```
http://192.168.1.87:5001/battle
```

### Roommate Network Access:
```
1. Roommate scans QR code: http://192.168.1.87:5001/login_qr
2. QR auth creates session
3. Redirects to: http://192.168.1.87:5001/battle
4. Can create battles, vote, view leaderboard
```

### Network Discovery:
The system auto-detects your IP via `config.py`:
```python
def get_server_ip():
    """Auto-detect server IP address for LAN access"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]  # Returns: 192.168.1.87
    s.close()
    return ip
```

---

## 🔒 Security & Privacy

### PII Protection (Already Implemented):
✅ **IP Hashing** - All IPs hashed with SHA-256 + salt (irreversible)
✅ **GPS Encryption** - Location data encrypted with AES-256-GCM
✅ **Log Redaction** - Auto-redact IPs, emails, GPS from logs
✅ **QR Auth** - Session-based access, no passwords stored

### Battle Arena Privacy:
- User votes are tied to `voter_user_id` (not IP addresses)
- AI responses are public (part of the game)
- No personal data collected in prompts
- All traffic localhost/network only (no internet exposure)

### Geofencing (Optional):
- Can restrict battles to users within radius
- GPS coordinates encrypted
- Radius calculated based on reputation (20-50km)

---

## 🧪 Testing Guide

### Test 1: Create a Battle (Localhost)
```bash
# From your laptop
curl -X POST http://192.168.1.87:5001/api/battle/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain encryption in one sentence",
    "category": "explanation",
    "models": ["soulfra-model", "deathtodata-model"]
  }'

# Response:
{
  "success": true,
  "battle_id": 1,
  "status": "generating",
  "models": ["soulfra-model", "deathtodata-model"]
}
```

### Test 2: View Battle Results
```bash
curl http://192.168.1.87:5001/api/battle/results/1

# Response:
{
  "battle": {
    "id": 1,
    "prompt": "Explain encryption in one sentence",
    "category": "explanation"
  },
  "responses": [
    {
      "model_name": "soulfra-model",
      "response_text": "Encryption transforms data...",
      "upvotes": 3,
      "downvotes": 0,
      "rank": 1
    },
    ...
  ],
  "winner": {...}
}
```

### Test 3: Vote
```bash
curl -X POST http://192.168.1.87:5001/api/battle/vote \
  -H "Content-Type: application/json" \
  -d '{
    "battle_id": 1,
    "response_id": 1,
    "vote_type": "upvote"
  }'
```

### Test 4: Leaderboard
```bash
curl http://192.168.1.87:5001/battle/leaderboard
```

---

## 💡 Future Ideas

### Roommate Challenges:
- Weekly themed battles
- Team competitions (roommates vs AI)
- Custom categories per roommate

### Research Integration:
- AI fetches external sources
- Citation tracking
- Fact-checking mode

### Publishing Pipeline:
- Winner auto-publishes to civicresume.com
- Article formatting
- SEO optimization
- Social sharing

### Horoscope Features:
- Daily email horoscopes
- Personalized based on quiz
- 13-month calendar (lunar, custom)
- Zodiac compatibility

---

## 📝 Summary

**Built:** AI Battle Arena with voting + leaderboard
**Access:** http://192.168.1.87:5001/battle
**Next:** Article competition system, horoscope generator, public service launch
**Privacy:** All PII encrypted/hashed, QR auth, localhost/network only

**Ready to battle!** 🎮🤖⚔️
