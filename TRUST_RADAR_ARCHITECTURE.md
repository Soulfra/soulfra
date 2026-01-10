# 🎯 Trust Radar Architecture - "Which AI Is Correct?"

**Concept:** When multiple AI personas debate the same voice memo, which interpretation aligns best with the original truth?

**Last Updated:** 2026-01-03

---

## 🧠 The Core Question

**User's insight:** "its like when we oput the trust radars when the ais know which one is correct or not idk"

When you record a voice memo and 3 different AI personas respond:
- **CalRiven** (logical): "Performative content is inefficient"
- **Soulfra** (balanced): "Balance authenticity with community needs"
- **DeathToData** (rebellious): "BURN IT ALL DOWN, social media is garbage"

**Which one is "correct"?**

Not "correct" as in factually true, but:
- Which aligns with your original voice signature (SHA256 wordmap)?
- Which resonates with the community (votes)?
- Which gets validated by the SHA256 chain?
- Which interpretation captures the "spirit" of your original recording?

---

## 🔷 The Trust Radar System

### Layer 1: SHA256 Voice Signature Alignment

**Original Voice Memo:**
```
Recording #7: "cringe on social media... authentic... validation game is broken"

Wordmap (top words):
- social: 8
- authentic: 5
- real: 4
- people: 3
- trust: 2

SHA256 Signature: 5d234bfa76794ee55b83b1f9216957e4...
```

**AI Response Alignment Scoring:**

Each AI response gets its own wordmap and SHA256 hash:

```python
def calculate_response_alignment(original_wordmap, response_wordmap):
    """
    Calculate % overlap between original voice and AI response

    Returns alignment score 0-100%
    """
    overlap_words = set(original_wordmap.keys()) & set(response_wordmap.keys())

    # Weight by frequency
    alignment_score = sum(
        min(original_wordmap[word], response_wordmap[word])
        for word in overlap_words
    )

    max_possible = sum(original_wordmap.values())

    return (alignment_score / max_possible) * 100
```

**Example:**
```
Original: {social: 8, authentic: 5, real: 4, trust: 2}

CalRiven Response: {data: 10, metrics: 7, analysis: 5, social: 3}
→ Alignment: 28% (only 'social' overlaps)

Soulfra Response: {authentic: 7, trust: 5, balance: 4, social: 3}
→ Alignment: 67% (authentic, trust, social overlap)

DeathToData Response: {broken: 10, burn: 8, garbage: 7, social: 2}
→ Alignment: 22% (only 'social' overlaps)
```

**Result:** Soulfra has highest alignment with original voice signature.

---

### Layer 2: Community Voting (Trust Score)

**Upvotes/Downvotes on AI Responses:**

```sql
CREATE TABLE ai_response_votes (
    id INTEGER PRIMARY KEY,
    debate_id INTEGER,
    persona TEXT,  -- 'calriven', 'soulfra', 'deathtodata'
    user_id INTEGER,
    vote_type TEXT,  -- 'upvote', 'downvote'
    created_at TEXT,
    FOREIGN KEY (debate_id) REFERENCES ai_debates(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Trust Radar Score:**

```python
def calculate_trust_radar_score(debate_id, persona):
    """
    Calculate trust radar score for an AI response

    Combines:
    - SHA256 alignment with original (40% weight)
    - Community upvotes (30% weight)
    - Response quality metrics (30% weight)
    """
    alignment = calculate_response_alignment(original, response)

    upvotes = db.execute('''
        SELECT COUNT(*) FROM ai_response_votes
        WHERE debate_id = ? AND persona = ? AND vote_type = 'upvote'
    ''', (debate_id, persona)).fetchone()[0]

    downvotes = db.execute('''
        SELECT COUNT(*) FROM ai_response_votes
        WHERE debate_id = ? AND persona = ? AND vote_type = 'downvote'
    ''', (debate_id, persona)).fetchone()[0]

    community_score = (upvotes - downvotes) / max(upvotes + downvotes, 1) * 100

    # Quality metrics: response length, coherence, etc.
    quality_score = calculate_quality_metrics(response)

    # Weighted average
    trust_score = (
        alignment * 0.4 +
        community_score * 0.3 +
        quality_score * 0.3
    )

    return trust_score
```

---

### Layer 3: SHA256 Chain Verification

**Response → Original Chain:**

```python
# Original voice memo
original_hash = sha256(original_content)

# AI response
response_hash = sha256(response_content)

# Chain hash (proves response is linked to original)
chain_hash = sha256(response_hash + original_hash)
```

**Trust Radar Chain Validation:**

If an AI response has a valid SHA256 chain → it's provably responding to the original memo (not a different topic).

```
Original: "cringe on social media"
  SHA256: 5d234bfa...
      ↓
CalRiven Response: "Performative content inefficient"
  SHA256: a7b3c2d1...
  Chain: sha256(a7b3c2d1 + 5d234bfa) = VERIFIED ✅
      ↓
Soulfra Response: "Balance authenticity"
  SHA256: b8c4d3e2...
  Chain: sha256(b8c4d3e2 + 5d234bfa) = VERIFIED ✅
      ↓
DeathToData Response: "BURN IT ALL"
  SHA256: c9d5e4f3...
  Chain: sha256(c9d5e4f3 + 5d234bfa) = VERIFIED ✅
```

All 3 are provably responding to the same original memo.

**But which one captures the "spirit" best?** → Trust Radar Score.

---

## 🎨 Trust Radar Visualization

**Proposed UI for `/suggestion/<id>`:**

```
Original Voice Memo: "The cringe on social media..."
SHA256: 5d234bfa...

┌─────────────────────────────────────────────────────────────┐
│  AI TRUST RADAR                                             │
│                                                             │
│  🔵 CalRiven (Logical)                    Trust: 62%       │
│  ├─ SHA256 Alignment: 28%                                  │
│  ├─ Community Votes: +12 / -3                              │
│  └─ "Performative content is inefficient..."               │
│                                                             │
│  🟣 Soulfra (Balanced)                    Trust: 89% ⭐     │
│  ├─ SHA256 Alignment: 67%                                  │
│  ├─ Community Votes: +45 / -2                              │
│  └─ "Balance authenticity with community..."               │
│                                                             │
│  🔴 DeathToData (Rebellious)              Trust: 58%       │
│  ├─ SHA256 Alignment: 22%                                  │
│  ├─ Community Votes: +18 / -8                              │
│  └─ "BURN IT ALL DOWN, social media..."                    │
│                                                             │
│  Highest Alignment: Soulfra (89%)                          │
│  Chain Verification: ✅ All verified                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 The "Ingredients" Analogy

**Your insight:** "thats why maybe some things are being messed up in the ingredients onull or chull or ruby or python or psotgres and whatever else"

The **trust radar** is about the **ingredients** layer:

**Same base ingredient (voice memo) → Different cooking methods (AI personas) → Which dish tastes best?**

```
Voice Memo (base ingredient)
    ↓
┌───────────────┬───────────────┬───────────────┐
│   CalRiven    │   Soulfra     │  DeathToData  │
│  (analyzed)   │  (balanced)   │   (burned)    │
│   🔵 Logic    │  🟣 Harmony   │   🔴 Chaos    │
└───────────────┴───────────────┴───────────────┘
         ↓              ↓              ↓
    Trust Radar determines which "dish" aligns
    best with the original "ingredient"
```

**The "null" issue:**
- Database: SQLite (no Postgres) ✅
- Language: Python ✅
- Templates: Jinja2 ✅
- Issue: Some fields returning `null` or empty (category was missing) ✅ **FIXED**

The "ingredients" are the **data types and nullability**:
- `category` was `NULL` in some rows → Fixed by adding default
- `chain_verified` was `True` when it should be `None` → Fixed logic
- SHA256 hashes proving authenticity → Working ✅

---

## 🔗 Trust Radar Database Schema

```sql
-- AI Debates (original suggestions + AI responses)
CREATE TABLE ai_debates (
    id INTEGER PRIMARY KEY,
    suggestion_id INTEGER NOT NULL,
    recording_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (suggestion_id) REFERENCES voice_suggestions(id)
);

-- AI Persona Responses
CREATE TABLE ai_debate_responses (
    id INTEGER PRIMARY KEY,
    debate_id INTEGER NOT NULL,
    persona TEXT NOT NULL,  -- 'calriven', 'soulfra', 'deathtodata'
    counter_argument TEXT,
    wordmap_json TEXT,
    sha256_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,  -- Links to original suggestion
    alignment_score REAL,  -- SHA256 alignment %
    controversy_score REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (debate_id) REFERENCES ai_debates(id)
);

-- Community Votes on AI Responses
CREATE TABLE ai_response_votes (
    id INTEGER PRIMARY KEY,
    debate_id INTEGER NOT NULL,
    persona TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL,  -- 'upvote', 'downvote'
    created_at TEXT NOT NULL,
    FOREIGN KEY (debate_id) REFERENCES ai_debates(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(debate_id, persona, user_id)  -- One vote per user per response
);

-- Trust Radar Scores (calculated)
CREATE TABLE trust_radar_scores (
    id INTEGER PRIMARY KEY,
    debate_id INTEGER NOT NULL,
    persona TEXT NOT NULL,
    alignment_score REAL,  -- SHA256 alignment (0-100)
    community_score REAL,  -- Upvote/downvote ratio (0-100)
    quality_score REAL,    -- Response quality metrics (0-100)
    trust_score REAL,      -- Weighted average (0-100)
    calculated_at TEXT NOT NULL,
    FOREIGN KEY (debate_id) REFERENCES ai_debates(id),
    UNIQUE(debate_id, persona)
);
```

---

## 🎯 Use Cases

### Use Case 1: Voice Memo → AI Debate → Trust Radar

```python
# 1. User records voice memo
recording = record_voice_memo("The cringe on social media...")

# 2. Extract SHA256 signature
wordmap = extract_wordmap(recording.transcription)
signature = sha256(wordmap)

# 3. Generate AI debates
debate = AIDebateGenerator().create_debate_from_recording(
    recording_id=7,
    personas=['calriven', 'soulfra', 'deathtodata']
)

# 4. Calculate trust radar scores
for response in debate.responses:
    alignment = calculate_response_alignment(wordmap, response.wordmap)
    trust_score = calculate_trust_radar_score(debate.id, response.persona)

    print(f"{response.persona}: {trust_score:.0f}% trust")

# Output:
# calriven: 62% trust
# soulfra: 89% trust ⭐
# deathtodata: 58% trust
```

### Use Case 2: Community Voting Updates Trust Score

```python
# User upvotes Soulfra's response
vote_on_ai_response(
    debate_id=123,
    persona='soulfra',
    user_id=5,
    vote_type='upvote'
)

# Recalculate trust scores
trust_scores = recalculate_trust_radar(debate_id=123)

# Soulfra's score increases due to community validation
```

### Use Case 3: Detecting AI Hallucination

```python
# DeathToData responds with completely unrelated content
original_wordmap = {social: 8, authentic: 5, real: 4}
response_wordmap = {unicorns: 10, rainbows: 8, magic: 5}

alignment = calculate_response_alignment(original_wordmap, response_wordmap)
# alignment = 0% (no word overlap)

# Trust radar flags this as low-quality response
if alignment < 20:
    print("⚠️  AI response may be off-topic or hallucinating")
```

---

## 🧪 Implementation Status

**Current Status:** 🔧 Concept documented, not yet implemented

**What Works:**
- ✅ Voice recordings with SHA256 signatures
- ✅ Voice suggestions with AI-extracted ideas
- ✅ SHA256 chain verification (response → original)
- ✅ Brand facets (@soulfra, @deathtodata, @calriven)

**What Needs Building:**
- 🔧 `ai_debates` table
- 🔧 `ai_debate_responses` table
- 🔧 `ai_response_votes` table
- 🔧 `trust_radar_scores` table
- 🔧 Alignment calculation algorithm
- 🔧 Trust score calculation
- 🔧 UI for trust radar visualization

**Next Steps:**
1. Create database schema for AI debates
2. Implement alignment scoring algorithm
3. Add voting system for AI responses
4. Build trust radar UI component
5. Integrate with existing AI debate generator

---

## 💡 Key Insights

### "Which AI Is Correct?"

Not about factual correctness, but:
- **SHA256 alignment** - Which response uses similar words to the original?
- **Community validation** - Which response resonates with other users?
- **Chain verification** - All responses must prove they're responding to the same original
- **Trust score** - Weighted combination of all factors

### The "Ingredients" Layer

The trust radar is the **quality control** layer:
- Same base ingredient (voice memo)
- Multiple processing methods (AI personas)
- Measure which output aligns best with the input
- Community votes validate the "taste test"

### Why This Matters

**Without trust radar:**
- 3 AIs respond, but which one is "best"?
- User has to read all 3 and decide
- No way to measure alignment

**With trust radar:**
- Automatic alignment scoring
- Community votes surface best responses
- SHA256 chain proves authenticity
- Clear signal: "Soulfra 89% trust ⭐"

---

## 🚀 Future Enhancements

### Trust Radar Evolution

1. **Payment tier weighting** - Higher-paying users get more vote weight?
2. **Temporal decay** - Old votes matter less than recent votes
3. **User expertise** - Votes from domain experts weighted higher
4. **Multi-modal alignment** - Not just word overlap, but semantic meaning (embeddings)
5. **AI vs AI debates** - CalRiven debates Soulfra, trust radar scores both

### Trust Radar as Game Mechanic

```
🎮 Trust Radar Game:
- Record voice memo
- 3 AIs debate your memo
- Community votes on best response
- Winning AI gets reputation boost
- Users who voted for winning AI get rewards
- Like "Kangaroo Court" but for AI interpretations
```

---

## 📊 Summary

**Trust Radar = "Which AI interpretation aligns best with your original voice?"**

**Measured by:**
1. SHA256 wordmap alignment (40% weight)
2. Community upvotes/downvotes (30% weight)
3. Response quality metrics (30% weight)

**Output:** Trust score 0-100% for each AI persona

**UI:** Visual radar showing which AI "gets you" best

**Goal:** Not to find one "correct" answer, but to surface the interpretation that **resonates** most with the original voice signature and community validation.

**Like:** Multiple chefs cooking the same ingredient - trust radar measures which dish tastes closest to the original ingredient's essence.

🎯 **The "ingredients" are clean (Python, SQLite, SHA256).** Now we build the trust radar to measure which AI cooks them best.
