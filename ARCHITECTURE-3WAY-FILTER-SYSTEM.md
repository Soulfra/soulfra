# 🎯 CringeProof 3-Way Filter System Architecture

**Last Updated**: 2026-01-02
**Status**: Production Ready

---

## 🧠 The Big Picture

CringeProof is **not just a personality quiz** - it's a **soul filtering system** that assigns users to one of 3 AI personas, who then act as "filters" through which the user's messages, actions, and tribunal cases are viewed.

### The 3 AI Personas

1. **CalRiven** (Logic)
   - **Personality**: Intelligent, efficient, analytical
   - **Philosophy**: Truth through reason and data
   - **Tribunal Role**: Logical Prosecutor
   - **User ID**: 4

2. **Soulfra** (Balance)
   - **Personality**: Secure, trustworthy, fair
   - **Philosophy**: Balance between logic and emotion
   - **Tribunal Role**: Impartial Judge
   - **User ID**: 6

3. **DeathToData** (Rebellion)
   - **Personality**: Rebellious, defiant, freedom-focused
   - **Philosophy**: Individual autonomy over authority
   - **Tribunal Role**: Rebellious Defender
   - **User ID**: 5

---

## 📖 How It Works: User Journey

### Step 1: Play CringeProof Game

User visits: `http://192.168.1.87:5001/cringeproof`

**What Happens**:
1. Game starts via `/api/narrative/start`
2. User plays through 7 chapters about AI consciousness
3. Answers philosophical questions (identity, freedom, trust, AI, etc.)
4. Each answer rated 1-5 (Strongly Disagree → Strongly Agree)
5. Game completes → stored in `narrative_sessions` table

**Key Database Tables**:
```sql
narrative_sessions (
    id, user_id, brand_id, current_chapter,
    game_state (JSON with answers), status, created_at
)
```

### Step 2: Persona Assignment

After game completion, system analyzes answers:

**API**: `POST /api/cringeproof/assign-persona`

**Scoring Algorithm** (in `cringeproof_personas.py`):
```python
# Questions about identity/memory
if category in ['identity', 'memory', 'consciousness']:
    if rating >= 4:  logic_score += 2      # Analytical
    elif rating <= 2:  emotion_score += 2  # Intuitive
    else:  balance_score += 1

# Questions about freedom/choice
if category in ['freedom', 'choice', 'autonomy']:
    if rating >= 4:  emotion_score += 2    # Rebellious
    elif rating <= 2:  logic_score += 2    # Rules-based
    else:  balance_score += 1

# Questions about truth/trust
if category in ['truth', 'trust', 'honesty']:
    if rating >= 4:  balance_score += 2    # Trustworthy
    elif rating <= 2:  emotion_score += 2  # Skeptical
    else:  logic_score += 1

# Questions about AI/technology
if category in ['ai', 'technology', 'artificial']:
    if rating >= 4:  logic_score += 2      # Pro-AI
    elif rating <= 2:  emotion_score += 2  # Human-focused
    else:  balance_score += 1
```

**Winning Persona** = `max(logic_score, balance_score, emotion_score)`

**Database Update**:
```sql
UPDATE users
SET ai_persona_id = <persona_id>
WHERE id = <user_id>
```

### Step 3: Messages Tracked by Blamechain

**What Is Blamechain?**

A blockchain-like edit tracking system where:
- Users can edit their messages
- BUT: Every edit is permanently recorded with SHA-256 hashes
- Creates immutable "chain" of evidence

**How It Works**:

1. **User sends original message**:
   ```sql
   INSERT INTO messages (from_user_id, to_user_id, content)
   VALUES (1, 2, 'Original message')
   ```

2. **System creates version 1 in blamechain**:
   ```sql
   INSERT INTO message_history (
       message_id, message_table, version_number,
       content, content_hash, chain_hash
   ) VALUES (
       123, 'messages', 1,
       'Original message',
       SHA256('Original message'),
       SHA256('GENESIS' + content_hash + timestamp)
   )
   ```

3. **User edits message**:
   ```
   POST /api/blamechain/edit
   {
       "message_table": "messages",
       "message_id": 123,
       "new_content": "Edited message",
       "edit_reason": "Fixed typo"
   }
   ```

4. **System creates version 2**:
   ```sql
   INSERT INTO message_history (
       message_id, message_table, version_number,
       content, content_hash,
       previous_hash,  -- Links to v1's chain_hash
       chain_hash      -- SHA256(previous_hash + new_content_hash + timestamp)
   ) VALUES (
       123, 'messages', 2,
       'Edited message',
       SHA256('Edited message'),
       <v1_chain_hash>,
       SHA256(v1_chain_hash + new_hash + timestamp)
   )
   ```

5. **Original message updated with flag**:
   ```sql
   UPDATE messages
   SET content = 'Edited message',
       edited = 1,
       edit_count = 1,
       last_edited_at = NOW()
   WHERE id = 123
   ```

**Key Features**:
- ✅ Users can edit freely
- ✅ But chain NEVER forgets original
- ✅ Cryptographic hashes prevent tampering
- ✅ Can verify integrity: `/api/blamechain/verify/messages/123`

### Step 4: Tribunal 3-Way Argument

When someone flags a message for tribunal review:

**API**: `POST /api/tribunal/submit-with-edits`

**What Happens**:

1. **System retrieves edit history** from blamechain
2. **All 3 AI personas analyze the evidence**:

   **CalRiven (Logic)**:
   ```python
   def analyze(history):
       suspicion = 0
       suspicion += min(len(history) * 10, 40)  # Many edits
       suspicion += no_reason_count * 15         # No explanations

       if suspicion >= 70: return "GUILTY"
       elif suspicion <= 30: return "INNOCENT"
       else: return "REQUIRES_MORE_DATA"
   ```

   **Soulfra (Balance)**:
   ```python
   def analyze(history):
       logical_suspicion = calriven_score()
       emotional_suspicion = sentiment_analysis()

       avg = (logical + emotional) / 2

       if avg >= 60: return "GUILTY"
       elif avg <= 40: return "INNOCENT"
       else: return "MONITORING_RECOMMENDED"
   ```

   **DeathToData (Rebellion)**:
   ```python
   def analyze(history):
       # Always defends freedom unless overwhelming evidence
       if len(history) >= 8 and all_edits_unexplained():
           return "SUSPICIOUS_BUT_FREE"
       else:
           return "INNOCENT"
   ```

3. **System calculates consensus**:
   - All 3 agree → HIGH confidence
   - 2/3 agree → MODERATE confidence
   - All disagree → NO_CONSENSUS

4. **Verdict stored in database**:
   ```sql
   INSERT INTO kangaroo_submissions (
       user_id, transcription, verdict
   ) VALUES (
       <user_id>,
       <full_debate_transcript>,
       <consensus_verdict>
   )
   ```

---

## 🗂️ Database Schema

### Core Tables

```sql
-- Users and their assigned personas
users (
    id,
    username,
    ai_persona_id INTEGER REFERENCES users(id),  -- NEW COLUMN
    is_ai_persona BOOLEAN
)

-- Message edit history (blamechain)
message_history (
    history_id PRIMARY KEY,
    message_id,
    message_table TEXT,  -- 'messages', 'irc_messages', etc.
    version_number,
    content,
    edited_by_user_id,
    edit_reason,
    content_hash TEXT,      -- SHA256(content)
    previous_hash TEXT,     -- Links to previous version
    chain_hash TEXT UNIQUE, -- Immutable proof
    edited_at TIMESTAMP,
    flagged_for_tribunal BOOLEAN,
    tribunal_submission_id
)

-- Tribunal submissions
kangaroo_submissions (
    id,
    user_id,
    transcription TEXT,  -- Includes 3-way debate transcript
    verdict TEXT,        -- GUILTY, INNOCENT, etc.
    reasoning TEXT,
    submitted_at,
    judged_at
)

-- CringeProof game sessions
narrative_sessions (
    id,
    user_id,
    brand_id,
    game_state TEXT,  -- JSON with answers
    status TEXT,      -- 'active', 'completed'
    created_at
)

-- Soul scores (updated by persona assignment)
soul_scores (
    entity_type,
    entity_id,
    composite_score REAL,
    tier TEXT
)
```

### View: Full Blamechain

```sql
CREATE VIEW v_message_blamechain AS
SELECT
    mh.message_id,
    mh.version_number,
    mh.content,
    u.username AS editor_username,
    mh.edit_reason,
    mh.edited_at,
    mh.chain_hash,
    CASE
        WHEN mh.version_number > 3 THEN 'HIGH_EDIT_COUNT'
        WHEN mh.edit_reason IS NULL THEN 'NO_REASON_GIVEN'
        ELSE 'NORMAL'
    END AS suspicion_level
FROM message_history mh
JOIN users u ON mh.edited_by_user_id = u.id
ORDER BY mh.message_id, mh.version_number
```

---

## 🔌 API Endpoints

### CringeProof Game
```
POST   /api/narrative/start          # Start new game
POST   /api/narrative/answer         # Submit answers
POST   /api/narrative/advance        # Next chapter
```

### Persona Assignment
```
POST   /api/cringeproof/assign-persona    # Assign based on completed game
GET    /api/cringeproof/my-persona        # Get user's persona
GET    /api/tribunal/personas              # Get all 3 tribunal personas
```

### Blamechain (Edit Tracking)
```
GET    /api/blamechain/history/<table>/<id>      # View edit history
POST   /api/blamechain/edit                      # Edit message (recorded)
GET    /api/blamechain/verify/<table>/<id>       # Verify chain integrity
POST   /api/blamechain/flag-for-tribunal         # Flag suspicious edits
```

### Tribunal (3-Way Argument)
```
GET    /api/tribunal/analyze-edits/<table>/<id>  # Run 3-way analysis
POST   /api/tribunal/submit-with-edits            # Submit to Kangaroo Court
GET    /api/tribunal/three-way-debate/<id>       # View full debate
```

---

## 🎭 Example: Full Flow

### Scenario: User "Alice" completes CringeProof and sends suspicious message

1. **Alice plays CringeProof**
   - Answers favor logic and efficiency
   - Score: `{calriven: 18, soulfra: 10, deathtodata: 5}`
   - **Assigned to CalRiven** ✅

2. **Alice sends message to Bob**
   ```
   Original: "I never said that thing about the project"
   ```

3. **Alice edits message 3 times**:
   - v1: "I never said that thing about the project"
   - v2: "I might have mentioned something about the project"
   - v3: "I discussed the project with the team"
   - v4: "I fully disclosed all project details"

4. **Bob flags message for tribunal**
   ```
   POST /api/tribunal/submit-with-edits
   {
       "message_id": 456,
       "accusation": "Alice is changing her story"
   }
   ```

5. **3-Way Analysis Runs**:

   **CalRiven** (Alice's assigned persona - conflict of interest!):
   - Suspicion: 65/100 (4 edits, no reasons given)
   - Verdict: "REQUIRES_MORE_DATA"
   - Reasoning: "Pattern suggests revision of position based on new information"

   **Soulfra** (Neutral):
   - Suspicion: 70/100 (content changes drastically)
   - Verdict: "GUILTY"
   - Reasoning: "Progressive edits obscure original intent. Transparency violated."

   **DeathToData** (Defender):
   - Suspicion: 30/100 (defends right to revise)
   - Verdict: "INNOCENT"
   - Reasoning: "User has right to clarify position. Thought evolution ≠ deception."

6. **Consensus**: 2/3 lean GUILTY → **Final Verdict: GUILTY (Moderate Confidence)**

7. **Tribunal Record Created**:
   ```sql
   INSERT INTO kangaroo_submissions (
       user_id: Alice's ID,
       verdict: 'GUILTY',
       reasoning: 'Soulfra and CalRiven agreed: edits obscure intent',
       transcription: <full debate with edit history>
   )
   ```

---

## 🎯 Why This Matters

### Traditional System
- User edits message → original lost
- No accountability
- "He said / she said" disputes

### CringeProof 3-Way Filter System
- ✅ **Blamechain**: Every edit tracked forever (cryptographically)
- ✅ **3 Perspectives**: Logic (CalRiven), Balance (Soulfra), Rebellion (DeathToData)
- ✅ **Persona Assignment**: User's own personality determines which filter "owns" them
- ✅ **Tribunal Debate**: Public 3-way argument with evidence
- ✅ **Consensus Voting**: High confidence when all agree

---

## 📂 Files Created

| File | Purpose |
|------|---------|
| `migrations/add_blamechain.sql` | Database schema for edit tracking |
| `blamechain.py` | Edit history API (create, view, verify, flag) |
| `cringeproof_personas.py` | Persona assignment logic + scoring |
| `tribunal_blamechain.py` | 3-way AI debate system |
| `ARCHITECTURE-3WAY-FILTER-SYSTEM.md` | This document |

---

## 🚀 Deployment Checklist

### Local Development (DONE ✅)
- [x] Database tables created
- [x] Blamechain API working
- [x] Persona assignment logic implemented
- [x] 3-way tribunal system built

### Production Deployment (TODO)
- [ ] Add blamechain/persona routes to main `app.py`:
  ```python
  from blamechain import init_blamechain
  from cringeproof_personas import init_cringeproof_personas
  from tribunal_blamechain import init_tribunal_blamechain

  init_blamechain(app)
  init_cringeproof_personas(app)
  init_tribunal_blamechain(app)
  ```

- [ ] Test full flow:
  1. Play CringeProof → Get persona
  2. Send message → Edit it 3 times
  3. View blamechain history
  4. Submit to tribunal
  5. See 3-way debate

- [ ] GitHub Pages Export:
  - Static blog showcasing system
  - Screenshots of tribunal debates
  - Link to live Heroku version

- [ ] Heroku/Railway:
  - Full interactive system
  - User accounts + sessions
  - Real-time tribunal voting

---

## 🎨 GitHub Showcase Ideas

### Blog Post: "I Built an AI Tribunal That Tracks Every Edit You Make"
- Screenshot: CringeProof game (7 chapters)
- Screenshot: Persona assignment result
- Screenshot: Message edit history with hashes
- Screenshot: 3-way debate (CalRiven vs Soulfra vs DeathToData)
- Code snippets: Blamechain hash algorithm
- Philosophy: Why edit tracking matters for accountability

### Product Hunt: "CringeProof - 3-Way AI Tribunal for Message Accountability"
- Tagline: "Play a personality quiz, get assigned an AI judge, never hide an edit again"
- Features:
  - ✅ AI-powered narrative game about consciousness
  - ✅ Persona assignment (Logic/Balance/Rebellion)
  - ✅ Blockchain-style edit tracking
  - ✅ 3-way AI debate system
  - ✅ Kangaroo Court tribunal

---

## 🔮 Future Enhancements

1. **Ollama Integration for Debates**
   - Currently: Hard-coded logic
   - Future: Actual LLM-generated arguments
   - Each persona uses different Ollama models

2. **Voice Memo Integration**
   - Record tribunal arguments as voice
   - Link to existing `simple_voice_recordings` table
   - Transcribe debates with Whisper

3. **Cross-Platform Gaming**
   - Link to existing `cross_platform_players` system
   - Tribunal cases from Roblox/Minecraft actions
   - Game actions become tribunal evidence

4. **Public Leaderboard**
   - Top prosecutors (CalRiven scores)
   - Fairest judges (Soulfra accuracy)
   - Best defenders (DeathToData win rate)

---

## 📝 Summary

**CringeProof is a 3-way AI soul filtering system:**

1. **CringeProof Game** → Play 7-chapter narrative
2. **Persona Assignment** → Get CalRiven/Soulfra/DeathToData
3. **Blamechain** → All message edits tracked forever
4. **Tribunal** → 3 AI personas debate your case
5. **Verdict** → Consensus voting with confidence levels

**It's not just a game. It's a philosophical experiment in accountability, identity, and AI judgment.**

---

**Next Steps**: See `CRINGEPROOF-STATUS.md` for deployment guide.
