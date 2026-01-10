# Soulfra OSS - Build-in-Public Workflow

## Overview

Soulfra is a self-documenting platform that builds itself in public. This document explains the complete workflow from feedback to newsletter to decisions.

---

## The Full Cycle

```
┌────────────────────────────────────────────────────────────┐
│                    PUBLIC INTERACTION                       │
│  Users submit feedback (no login required)                 │
│  → /feedback form → feedback table                         │
└────────────┬───────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────┐
│                  AUTOMATED PROCESSING                       │
│  public_builder.py runs hourly (cron)                      │
│  → Groups high-priority feedback                           │
│  → CalRiven creates posts                                  │
│  → Reasoning engine analyzes                               │
│  → Feedback marked "in-progress"                           │
└────────────┬───────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────┐
│                  AI REASONING & ANALYSIS                    │
│  4 AI personas analyze each post:                          │
│  → CalRiven: Technical analysis                            │
│  → TheAuditor: Validation                                  │
│  → Soulfra: Platform perspective                           │
│  → DeathToData: Critical questions                         │
│  → All stored in reasoning_threads                         │
└────────────┬───────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────┐
│              WEEKLY NEWSLETTER DIGEST                       │
│  newsletter_digest.py runs weekly                          │
│  → Groups feedback by theme                                │
│  → Finds AI consensus/disagreement                         │
│  → Generates QUESTIONS for decision-making                 │
│  → Emails digest to subscribers                            │
└────────────┬───────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────┐
│                  HUMAN DECISIONS                            │
│  Newsletter includes clickable decisions:                  │
│  → "5 people want feature X - Prioritize/Schedule/Decline?"│
│  → "AIs disagree on Y - Side with CalRiven/TheAuditor?"   │
│  → Decisions guide roadmap                                 │
└────────────┬───────────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────────────────────────┐
│                  QR TIME CAPSULE                            │
│  Each feature/post gets a QR code:                         │
│  → Tracks who scanned (chain)                              │
│  → Shows journey: NYC → SF → Tokyo                         │
│  → Living artifact of feature's spread                     │
└────────────────────────────────────────────────────────────┘
```

---

## How to Use Each Component

### 1. Submit Feedback (Public)

**As any user (no login):**
```
Visit: http://localhost:5001/feedback

Fill out:
- Name (optional)
- Email (optional) 
- Component (dropdown: Reasoning Engine, Posts, etc.)
- Message (required)

Submit → Saved to feedback table
```

**What happens:**
- Feedback stored with timestamp
- Admin sees it in dashboard
- Hourly automation checks for high-priority items

---

### 2. Automated Post Creation

**Run manually:**
```bash
python3 public_builder.py
```

**Or via cron (hourly):**
```bash
crontab -e
# Add:
0 * * * * cd /path/to/soulfra-simple && python3 public_builder.py >> logs/builder.log 2>&1
```

**What it does:**
1. Checks feedback from last 24 hours
2. Scores each item:
   - Bug keywords (bug, broken, error): +10 points
   - Feature keywords (should, want, need): +5 points
   - Critical components: +5 points
3. If score ≥ 10: CalRiven creates post
4. Post auto-analyzed by reasoning engine
5. Feedback status → "in-progress"

**Example output:**
```
Found 1 priority items:
  • [Reasoning Engine] SQL noise in keywords (score: 10)

Created post #12: Feature Request: Reasoning Engine
Reasoning thread #10 created
```

---

### 3. Newsletter Digest Generation

**Run manually:**
```bash
python3 newsletter_digest.py
```

**Or via cron (weekly, Sunday 8pm):**
```bash
0 20 * * 0 cd /path/to/soulfra-simple && python3 newsletter_digest.py >> logs/digest.log 2>&1
```

**What it does:**
1. Groups feedback by theme (keyword similarity)
2. Analyzes AI reasoning threads for consensus/disagreement
3. Generates decision questions
4. Creates HTML email digest
5. Sends to subscribers (or saves preview)

**Example questions:**
```
1. 5 people requested QR Codes features
   [Prioritize] [Schedule] [Decline] [Need more info]

2. AIs disagree on: Performance optimization
   CalRiven: "Cache everything"
   TheAuditor: "Be careful with cache"
   [Side with CalRiven] [Side with TheAuditor] [Compromise]
```

---

### 4. Decision Making

**View digest:**
```bash
open weekly_digest_preview.html
```

**Click action buttons:**
- Each button links to `/admin/decision/{id}?action=Prioritize`
- Records your decision
- Updates roadmap/backlog
- Closes feedback loop

---

### 5. QR Time Capsule

**Generate QR for a post:**
```python
from database import get_db

db = get_db()
db.execute('''
    INSERT INTO qr_codes (code_type, code_data, target_url, created_by)
    VALUES (?, ?, ?, ?)
''', ('post', 'post-12', 'http://soulfra.com/post/feature-request-reasoning-engine', 1))
db.commit()
qr_id = db.lastrowid

# QR URL: http://soulfra.com/qr/{qr_id}
```

**When someone scans:**
- Records: who, when, where, device
- Links to previous scan (chain)
- Shows: "Last scanned by Alice in SF, 2 hours ago"
- Creates living history

**View scan chain:**
```sql
WITH RECURSIVE chain AS (
    SELECT *, 0 as depth FROM qr_scans WHERE qr_code_id = 1 
    ORDER BY scanned_at DESC LIMIT 1
    UNION ALL
    SELECT s.*, c.depth + 1 
    FROM qr_scans s JOIN chain c ON s.id = c.previous_scan_id
)
SELECT * FROM chain ORDER BY depth;
```

---

## Verification & Reproducibility

**Run full verification:**
```bash
python3 verify_oss.py
```

**Tests:**
1. ✅ Database structure (all tables exist)
2. ✅ Public builder workflow
3. ✅ Newsletter digest generation
4. ✅ Data export (JSON reproducibility)
5. ✅ Reasoning engine functionality
6. ✅ QR time capsule tracking

**Export all data:**
```bash
python3 verify_oss.py
# Creates: soulfra_export.json (full database dump)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `public_builder.py` | Automation: feedback → posts → reasoning |
| `newsletter_digest.py` | Weekly digest: questions for decisions |
| `verify_oss.py` | OSS reproducibility tests |
| `feedback` table | Public feedback (no login) |
| `qr_codes` + `qr_scans` | Time capsule tracking |
| `reasoning_threads` + `reasoning_steps` | AI analysis |
| `weekly_digest_preview.html` | Newsletter preview |
| `soulfra_export.json` | Full database export |

---

## Decision Questions Format

**Newsletter includes structured questions:**

```json
{
  "type": "feature_priority",
  "theme": "QR Codes",
  "count": 5,
  "question": "5 people requested QR Codes features",
  "context": "Example: 'Would love QR codes for sharing'",
  "actions": ["Prioritize", "Schedule", "Decline", "Need more info"]
}
```

**Disagreement resolution:**
```json
{
  "type": "resolve_disagreement",
  "post_title": "Performance optimization",
  "question": "AIs disagree on: Caching strategy",
  "context": "CalRiven: Cache everything\nTheAuditor: Test first",
  "actions": ["Side with CalRiven", "Side with TheAuditor", "Compromise", "Research"]
}
```

---

## Reproducibility Checklist

For OSS contributors/forks:

- [ ] Clone repo
- [ ] `pip install -e .` (when pyproject.toml is ready)
- [ ] `python3 init_platform.py` (initialize database)
- [ ] `python3 verify_oss.py` (run verification)
- [ ] Set up cron jobs (see AUTOMATION.md)
- [ ] Test feedback form at `/feedback`
- [ ] Run `public_builder.py` manually
- [ ] Generate `newsletter_digest.py` preview
- [ ] Export data with `verify_oss.py`

**All tests should pass.** If not, file an issue!

---

## The Build-in-Public Philosophy

**Traditional approach:**
- Build features in private
- Release when "done"
- Get feedback after launch
- Fix issues reactively

**Soulfra approach:**
- Accept feedback from day 1 (no login required)
- Automation creates posts from feedback
- AI personas analyze and debate
- Newsletter asks YOU for decisions
- QR codes track feature journey
- Everything is transparent

**This is building in public, automated.** 🚀

---

## Summary

```
User feedback → Auto posts → AI reasoning → Newsletter questions → 
Your decisions → Roadmap updates → QR tracking → Repeat
```

**Every part is:**
- Automated (cron jobs)
- Reproducible (verify_oss.py)
- Exportable (JSON)
- Trackable (QR time capsule)
- Documented (in the platform itself!)

**Soulfra documents itself by building itself.** That's the magic.
