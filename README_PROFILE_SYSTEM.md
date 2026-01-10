# README-as-Profile System

## No Image Uploads. Avatars Earned from Feedback.

---

## The Concept

**Traditional Profiles:**
- Upload headshot
- List skills (self-reported)
- Describe yourself
- **Problem**: Easy to lie, hard to verify

**README Profiles:**
- Submit README as your "about me"
- NO image upload allowed
- Avatar auto-generates from what OTHERS say about you
- **Solution**: Reputation is earned, not claimed

---

## How It Works

### 1. Create Profile

```bash
POST /api/profile/create
{
  "slug": "alice",
  "readme_content": "# Alice\n\nBackend engineer building decentralized tools...",
  "github_username": "alice-codes"
}
```

**What Gets Created:**
- Profile URL: `/alice`
- README displayed as profile
- Default avatar (just initials)
- Projects list parsed from README

**No image upload!**

---

### 2. Others Leave Feedback

```
Sarah records voice memo:
"I worked with Alice on the payment system rewrite.
She refactored our entire codebase and mentored me."

→ Extracts: {person: "Alice", skills: ["refactoring", "mentoring"]}
→ Updates Alice's feedback count
```

---

### 3. Avatar Auto-Generates

```
GET /api/profile/alice/avatar
→ Returns SVG avatar generated from feedback

Components:
- Colors: From skill keywords ("refactoring" = blue, "mentoring" = green)
- Shapes: Complexity from mention count (5 mentions = 5 shapes)
- Patterns: Different for each skill category
```

**Avatar evolves as feedback grows!**

---

## The Profile Page

Visit `/alice`:

### What Alice CLAIMS (README)
```markdown
# Alice

I'm a backend engineer interested in distributed systems.

## Skills
- Python
- Go
- Databases

## Want to Build
- Decentralized chat app
- P2P file sharing
```

### What Others CONFIRM (Feedback)
```
✨ 5 people mentioned Alice

Skills confirmed by others:
- Refactoring (3 mentions)
- Mentoring (2 mentions)
- Debugging (1 mention)
- Architecture (1 mention)

Skills claimed but not confirmed:
- Go (0 mentions)
- Databases (0 mentions)

Unexpected skills (not claimed):
- Leadership (2 mentions)
- Design (1 mention)
```

### Authenticity Gap

```json
{
  "verified": ["Python", "Refactoring"],
  "unverified": ["Go", "Databases"],
  "unexpected": ["Leadership", "Design"],
  "authenticity_score": 40  // Only 40% of claims verified
}
```

**The gap reveals truth:**
- High score = Claims match reality
- Low score = Overclaiming skills
- Unexpected skills = Hidden talents others noticed

---

## Avatar Generation Details

### No Feedback Yet
```svg
<svg>
  <circle fill="hsl(180, 50%, 70%)" />  <!-- Color from slug hash -->
  <text>A</text>  <!-- First letter -->
  <text>No feedback yet</text>
</svg>
```

**Simple, gray, boring. Motivates getting feedback.**

### After 1 Mention
```svg
<svg>
  <circle fill="url(#gradient)" />  <!-- Gradient from skill -->
  <circle />  <!-- 1 shape for 1 mention -->
  <rect />  <!-- 1 skill indicator -->
</svg>
```

**Single color, simple shape.**

### After 5 Mentions
```svg
<svg>
  <linearGradient>  <!-- Multi-color from skills -->
    <stop hsl(200, 70%, 60%) />  <!-- refactoring -->
    <stop hsl(120, 70%, 60%) />  <!-- mentoring -->
    <stop hsl(350, 70%, 60%) />  <!-- debugging -->
  </linearGradient>
  <circle ... />  <!-- 5 shapes -->
  <circle ... />
  <circle ... />
  <circle ... />
  <circle ... />
  <rect ... />  <!-- 5 skill indicators -->
  <rect ... />
  <rect ... />
  <rect ... />
  <rect ... />
</svg>
```

**Complex, colorful, earned.**

---

## README Parsing

### Example README
```markdown
# Alice Smith

Backend engineer passionate about distributed systems
and teaching others.

## Skills
- Python
- Go
- PostgreSQL
- Docker

## Want to Build
- Decentralized chat application
- P2P file sharing tool
- Mentorship platform

## Experience
Previously worked at BigCorp on payment systems.
```

### Parsed Sections
```json
{
  "bio": "Backend engineer passionate about distributed systems and teaching others.",
  "skills_claimed": ["Python", "Go", "PostgreSQL", "Docker"],
  "projects": [
    "Decentralized chat application",
    "P2P file sharing tool",
    "Mentorship platform"
  ]
}
```

---

## API Endpoints

### Create Profile
```
POST /api/profile/create
```
Body:
```json
{
  "slug": "alice",
  "readme_content": "# Alice\n\n...",
  "github_username": "alice-codes"
}
```
Response:
```json
{
  "success": true,
  "slug": "alice",
  "url": "/alice",
  "avatar_url": "/api/profile/alice/avatar",
  "sections": {...}
}
```

### Get Profile
```
GET /api/profile/alice
```
Response:
```json
{
  "slug": "alice",
  "readme_content": "# Alice...",
  "skills_claimed": ["Python", "Go"],
  "skills_confirmed": ["Refactoring", "Mentoring"],
  "projects": ["Decentralized chat..."],
  "avatar_url": "/api/profile/alice/avatar",
  "feedback_stats": {
    "mention_count": 5,
    "positive_mentions": 5
  },
  "authenticity_gap": {
    "verified": ["Python"],
    "unverified": ["Go"],
    "unexpected": ["Leadership"],
    "authenticity_score": 50
  }
}
```

### Get Avatar (SVG)
```
GET /api/profile/alice/avatar
```
Returns: `image/svg+xml`

### Update README
```
PUT /api/profile/alice/update-readme
```
Body:
```json
{
  "readme_content": "# Alice\n\nUpdated bio..."
}
```

---

## The LinkedIn Killer Strategy

### LinkedIn's Problem
- **Self-reported everything**
- Skills: You click them yourself
- Endorsements: Reciprocal ("I'll endorse you if you endorse me")
- Headshots: Professionally staged
- **Result**: Everyone looks perfect, hard to verify truth

### README Profile Solution
- **Skills split**: Claimed vs. Confirmed
- Feedback: From actual work stories (STAR format)
- Avatar: Can't fake (auto-generates from feedback)
- **Result**: Truth emerges, authenticity visible

### The Feedback Loop

```
1. Alice creates profile with README
   ↓
2. Lists "Python, Go, Databases" as skills
   ↓
3. Lists "Want to build: Decentralized chat"
   ↓
4. Sarah records: "Alice refactored our codebase"
   ↓
5. Alice's avatar updates (gets more colorful)
   ↓
6. "Refactoring" shows as CONFIRMED skill
   ↓
7. "Go" shows as UNCONFIRMED (claimed but no feedback)
   ↓
8. Bob sees profile, thinks:
   "Oh, she's really good at refactoring (confirmed by Sarah)
    but claims Go experience with no confirmation"
   ↓
9. Bob works with Alice on Go project
   ↓
10. Bob leaves feedback: "Alice taught me Go"
    ↓
11. "Go" moves to CONFIRMED
    ↓
12. Avatar gets more complex
    ↓
13. Authenticity score increases
```

---

## Integration with Existing Systems

### With Collaboration Minesweeper
```
Record STAR interview story
→ Mention teammate
→ Extract skills
→ Update feedback table
→ Avatar auto-regenerates
```

### With GitHub OAuth
```
User has GitHub account
→ README can live in GitHub repo
→ Pull requests to update profile
→ Contribution graph shows activity
→ Stars/followers visible
```

### With Slug System
```
Claim slug: "alice"
→ Submit README
→ Get URL: cringeproof.com/alice
→ OR: alice.cringeproof.com (subdomain)
```

### With Voice Memos
```
Record voice about teammate
→ Transcribe with Whisper
→ Extract with Ollama
→ Update feedback automatically
→ Avatar regenerates
```

---

## Why This Prevents Gaming

### Can't Fake Feedback
- Feedback comes from voice memos (with transcripts)
- Stored permanently in database
- Traceable to storyteller
- Public record

### Can't Buy Endorsements
- No "endorse me and I'll endorse you"
- Only counts if mentioned in actual work story
- Story must pass STAR format validation
- Real project/situation required

### Can't Upload Fake Avatar
- No uploads allowed
- Avatar IS the feedback
- Gray/boring until earned
- Complexity = proof of work

### Can't Claim Unverified Skills
- Claims visible separately from confirmations
- Gap calculated and displayed
- Low authenticity score = red flag
- Others see what's NOT confirmed

---

## Example Profiles

### New User (No Feedback)
```
/bob

# Bob

DevOps engineer learning Rust.

## Skills (Claimed)
- Docker ⚠️ (0 confirmations)
- Kubernetes ⚠️ (0 confirmations)
- Rust ⚠️ (0 confirmations)

## Avatar
[Gray circle with "B"]
No feedback yet

Authenticity Score: N/A
```

### Established User (Feedback)
```
/alice

# Alice

Backend engineer building decentralized tools.

## Skills
✅ Refactoring (3 confirmations)
✅ Mentoring (2 confirmations)
✅ Python (2 confirmations)
⚠️ Go (0 confirmations)
⚠️ Databases (0 confirmations)

## Unexpected Skills (Others Noticed)
✨ Leadership (2 mentions)
✨ Design (1 mention)

## Avatar
[Colorful, complex SVG with 5 shapes]

Authenticity Score: 60%
(3 of 5 claimed skills confirmed)
```

---

## The Vision

**Profile images should be EARNED, not uploaded.**

Your avatar is a visual representation of your reputation.
It evolves as you work with others and they vouch for you.

Can't fake it. Can't buy it. Can't Photoshop it.

Just do good work, and your avatar reflects it. 🎨
