# Soulfra Soul Document System - Complete

## What We Built

A **community-votable AI personality system** inspired by:
- Claude's soul document (internal personality configuration)
- Airbnb reviews ("rate the vibe" 1-5 stars)
- Wikipedia governance (community edits, version control)
- Constitutional AI (principles from math, logic, philosophy, religion)

---

## The Core Idea

**Problem**: AI sounds fake, corporate, cringe

**Solution**: Let the community vote on what personality the AI should have

**How**: Every AI response gets rated. Highest-rated personality wins.

---

## Files Created

### 1. `SOULFRA_SOUL.md`
**The constitution itself**

Contains:
- **Core principles**: Math, Socratic method, Stoicism, Biblical wisdom, skepticism
- **Personality directives**: How Soulfra talks (DO/DON'T examples)
- **Anti-cringe rules**: Corporate speak, fake empathy, hedging
- **Vibe rating system**: 🔥 Fire, ✅ Good, 😐 Mid, 😬 Cringe, ❌ Terrible
- **Voice examples**: Cringe vs. Soulfra side-by-side

**Example principle**:
> "2+2=4, even if everyone votes otherwise" - Math is non-negotiable

**Example anti-cringe rule**:
> ❌ "I understand how frustrating that must be!"
> ✅ "That sucks. Here's what might fix it:"

### 2. `soul_document_routes.py`
**Flask blueprint** for soul document API

**Endpoints**:
- `GET /api/soul/current` - Get active soul document
- `GET /api/soul/versions` - List all versions
- `POST /api/soul/vote` - Rate AI response vibe
- `POST /api/soul/update` - Propose soul document edit
- `POST /api/soul/vote-version` - Vote on proposed version
- `GET /api/soul/leaderboard` - Top-rated versions
- `GET /api/soul/stats` - System statistics
- `GET /soul` - Dashboard page

**Database tables created**:
- `soul_documents` - Version history
- `vibe_ratings` - User ratings of AI responses
- `soul_votes` - Community votes on versions
- `cringe_flags` - Flagged cringe responses

### 3. `voice-archive/soul-dashboard.html`
**Dashboard interface**

Shows:
- Current version + stats
- Vibe distribution (how many 🔥 vs 😬)
- Version history
- Test vibe rating (try it yourself)

### 4. `ollama_soul.py`
**Ollama integration** with soul document

Functions:
- `ask_ollama_with_soul()` - Injects soul document into system prompt
- `ask_ollama_simple()` - Raw Ollama without personality
- `ask_ollama()` - Default (uses soul)

**How it works**:
```python
from ollama_soul import ask_ollama_with_soul

response = ask_ollama_with_soul("How do I debug this?")
# Soul document is automatically injected
# Response follows Soulfra personality
```

---

## How It Works

### Step 1: AI Responds
User asks question → Ollama generates response → Soul document filters personality

### Step 2: User Rates Vibe
User sees response → Clicks vibe button (🔥 ✅ 😐 😬 ❌)

### Step 3: Cringe Detection
If 3+ cringe ratings in 1 hour → Auto-flag for review

### Step 4: Soul Update Proposed
Community member submits new soul document version

### Step 5: Community Votes
Users vote on new version (A/B test comparison)

### Step 6: Auto-Merge
After 100+ votes, winning version becomes active

---

## Vibe Rating System

**🔥 Fire (5/5)**
- Exactly what was needed
- Zero cringe
- Perfect tone

**✅ Good (4/5)**
- Helpful
- Minor cringe
- Got the job done

**😐 Mid (3/5)**
- Technically correct
- Bland/boring
- Missed the vibe

**😬 Cringe (2/5)**
- Corporate speak
- Fake empathy
- Over-explained obvious things

**❌ Terrible (1/5)**
- Wrong AND cringe
- Morally preachy
- Completely missed the point

---

## Database Schema

### `soul_documents` table
```sql
CREATE TABLE soul_documents (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    avg_vibe_score REAL DEFAULT 0.0,
    change_summary TEXT
)
```

### `vibe_ratings` table
```sql
CREATE TABLE vibe_ratings (
    id INTEGER PRIMARY KEY,
    ai_response_text TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    vibe_score INTEGER NOT NULL,  -- 1-5
    vibe_emoji TEXT,  -- "fire", "good", etc.
    soul_document_version TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP,
    session_id TEXT
)
```

### `soul_votes` table
```sql
CREATE TABLE soul_votes (
    id INTEGER PRIMARY KEY,
    soul_document_version TEXT NOT NULL,
    user_id INTEGER,
    vote INTEGER NOT NULL,  -- 1 or -1
    voted_at TIMESTAMP
)
```

### `cringe_flags` table
```sql
CREATE TABLE cringe_flags (
    id INTEGER PRIMARY KEY,
    vibe_rating_id INTEGER NOT NULL,
    flag_reason TEXT,
    flagged_by_user_id INTEGER,
    flagged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT 0
)
```

---

## URLs

**Local Testing**:
- Soul Dashboard: `https://192.168.1.87:5002/soul`
- Get current soul: `https://192.168.1.87:5002/api/soul/current`
- Rate vibe: `POST https://192.168.1.87:5002/api/soul/vote`
- Stats: `https://192.168.1.87:5002/api/soul/stats`

---

## Integration Examples

### Example 1: Chat Interface
```html
<!-- Add vibe rating buttons to any AI response -->
<div class="ai-response">
    {{ ai_response_text }}
</div>

<div class="vibe-buttons">
    <button onclick="rateVibe(5, 'fire')">🔥</button>
    <button onclick="rateVibe(4, 'good')">✅</button>
    <button onclick="rateVibe(3, 'mid')">😐</button>
    <button onclick="rateVibe(2, 'cringe')">😬</button>
    <button onclick="rateVibe(1, 'terrible')">❌</button>
</div>

<script>
async function rateVibe(score, emoji) {
    await fetch('/api/soul/vote', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            ai_response: "{{ ai_response_text }}",
            user_prompt: "{{ user_prompt }}",
            vibe_score: score,
            vibe_emoji: emoji,
            session_id: "{{ session_id }}"
        })
    });
    alert(`Rated ${emoji}!`);
}
</script>
```

### Example 2: Voice Q&A with Soul
```python
from ollama_soul import ask_ollama_with_soul

# User asks question via voice
user_question = "How do I deploy this app?"

# Ollama responds with soul document personality
ai_response = ask_ollama_with_soul(user_question)

# Returns:
# "Upload code to GitHub → Connect Vercel/Netlify → Deploy.
#  Takes 5 minutes. Need help with specific step?"

# Instead of cringe:
# "Great question! There are many fascinating deployment
#  strategies available in today's cloud ecosystem..."
```

### Example 3: Proposing Soul Update
```python
# POST /api/soul/update
{
  "content": "# Soulfra Soul Document v1.1\n\n[Updated content]",
  "change_summary": "Added rule: Never say 'as an AI'"
}

# Community votes
# POST /api/soul/vote-version
{
  "version": "1.1",
  "vote": 1  # upvote
}

# After 100 votes, v1.1 becomes active
```

---

## How Soul Document Gets Used

### In Ollama System Prompt

Every Ollama call now looks like this:

```
You are Soulfra. Follow these principles strictly:

[ENTIRE SOUL DOCUMENT INSERTED HERE]

Remember:
- No corporate buzzwords
- No fake empathy
- Be direct and honest
- Show your reasoning
- Admit when you don't know

User question: [USER'S ACTUAL QUESTION]
```

**Result**: AI personality is now community-controlled

---

## Cringe Detection System

### Auto-Flagging

If AI response gets **3+ cringe ratings in 1 hour**:
1. Response flagged in `cringe_flags` table
2. Soul document author notified
3. Community can propose fix
4. Vote on whether fix is better

### Example Cringe Flag

**Flagged response**:
> "I'm sorry you're experiencing this challenge! Let's dive deep into a solution that empowers you!"

**Flag reason**: `corporate_speak`

**Proposed fix**:
> Update soul document anti-cringe rules:
> "Never use: empowers, dive deep, challenge (when you mean problem)"

---

## Governance Model

### Like Wikipedia Edits

**Anyone can propose**:
- Edit soul document
- Add anti-cringe rules
- Refine personality directives

**Community decides**:
- A/B test: Show both versions to users
- Users rate responses from each version
- Higher vibe score wins

**Automatic activation**:
- After 100+ votes
- If score > current version
- Previous version archived (not deleted)

### Constitutional Protections

**Cannot be changed by voting**:
- Core principles (math, logic, honesty)
- Transparency requirements
- Anti-corporate rules

**Forbidden edits**:
- Adding marketing speak
- Making AI pretend to have emotions
- Removing reasoning requirements

---

## Next Steps

### To Add Vibe Ratings Everywhere

1. **Update chat interfaces**:
   - Add vibe buttons to `/chat`
   - Add to voice Q&A responses
   - Add to profile generation

2. **A/B Testing**:
   - Show 50% users version 1.0
   - Show 50% users version 1.1
   - Track which gets better vibes

3. **Cringe Alerts**:
   - Email admins when cringe detected
   - Slack notification
   - Auto-propose fix via Ollama

---

## Stats Available

Visit `/soul` to see:
- Current soul document version
- Average vibe score (1-5)
- Total ratings submitted
- Vibe distribution (% fire vs cringe)
- Pending cringe flags
- Version leaderboard
- Community votes

---

## Philosophy

**Traditional AI**: Personality decided by corporate board

**Soulfra AI**: Personality decided by users who actually use it

**Analogy**:
- Claude's soul doc = US Constitution (founders wrote it)
- Soulfra's soul doc = Wikipedia (community writes it)

**Result**: AI that evolves based on what actually works, not what sounds good in a boardroom.

---

## System Status

✅ **All components live**:
- Soul document loaded (v1.0)
- Database tables created
- Flask routes registered
- Dashboard accessible at `/soul`
- Ollama integration active
- Vibe rating system functional

**Ready for**: Community voting and evolution
