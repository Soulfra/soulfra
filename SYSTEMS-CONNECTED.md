# 🔗 Everything Connected - Your Full System

**Created:** December 31, 2024
**Purpose:** Show how all your existing systems connect together

---

## 🎯 What You Asked (And Already Have!)

**You:** "how do we extract stuff from database and get it into proper tiers?"
**Answer:** You built `membership_system.py` + I just created `query_by_tier.py`!

**You:** "are there more types or tiers?"
**Answer:** You have TWO tier systems already!

**You:** "how does this work with stripe?"
**Answer:** You already have full Stripe integration!

**You:** "rotating... dead mans switch... decentralization?"
**Answer:** You built `rotation_helpers.py` for exactly this!

---

## 🏗️ Your Two Tier Systems

### 1. Brand Tiers (For Domains)
**Purpose:** Categorize domain importance/features

| Tier | Meaning | Use For |
|------|---------|---------|
| **foundation** | Core brands | Soulfra, DeathToData, Calriven |
| **business** | Revenue-generating | StPetePros, local services |
| **creative** | Content/community | HowToCookAtHome, gaming |

**Extract by tier:**
```bash
python3 query_by_tier.py --tier foundation
python3 query_by_tier.py --tier business
python3 query_by_tier.py --tier creative
```

### 2. Membership Tiers (For Users/Stripe)
**Purpose:** Monetization + limits

| Tier | Price | Domain Limit | Features |
|------|-------|-------------|----------|
| **Free** | $0 | 10 domains | Basic export, limited AI |
| **Pro** | $5/mo | 50 domains | Unlimited AI, better usernames |
| **Premium** | $10/mo | Unlimited | Reserved usernames, priority support |

**Your file:** `membership_system.py`

**Extract by membership:**
```bash
python3 query_by_tier.py --membership free
python3 query_by_tier.py --membership pro
python3 query_by_tier.py --membership premium
```

---

## 💳 Stripe Integration (You Already Built!)

**File:** `membership_system.py`

**What it does:**
- Creates Stripe checkout sessions
- Handles subscriptions (free/pro/premium)
- Manages customer IDs
- Tracks payment status
- Webhooks for subscription updates

**Database:** `memberships` table
```sql
CREATE TABLE memberships (
  user_id INTEGER,
  stripe_customer_id TEXT,
  tier TEXT (free/pro/premium),
  stripe_subscription_id TEXT,
  status TEXT (active/cancelled/expired)
)
```

**How to use:**
```python
from membership_system import get_membership, can_create_brand

# Check user's membership
membership = get_membership(user_id=1)
# Returns: {'tier': 'pro', 'status': 'active'}

# Check if user can add more domains
can_add = can_create_brand(user_id=1)
# Returns: True/False based on tier limits
```

---

## 🔄 Rotation System (Dead Man's Switch!)

**File:** `rotation_helpers.py`

**What it does:**
- Rotates domain contexts (questions, themes, profiles)
- Changes content periodically
- Template versioning (v1_dinghy → v4_galleon)
- Automatic cycling

**Rotation Types:**

### 1. Question Rotation (Daily)
```python
from rotation_helpers import get_rotation_context

context = get_rotation_context('mycooking.com', 'question')
# Day 1: "What's your favorite quick recipe?"
# Day 2: "How do you meal prep on Sundays?"
# Day 3: "What cooking tool changed your life?"
```

### 2. Theme Rotation (Weekly)
```python
theme = get_rotation_context('mycooking.com', 'theme')
# Week 1: "ocean" (blue palette)
# Week 2: "sunset" (orange palette)
# Week 3: "starlight" (dark palette)
```

### 3. Profile Rotation (Monthly)
```python
profile = get_rotation_context('mycooking.com', 'profile')
# Month 1: Beginner cook persona
# Month 2: Pro chef persona
# Month 3: Meal prep expert persona
```

**Dead Man's Switch Concept:**
- If no activity for 30 days → auto-rotate
- If owner inactive → publish archive
- If server down → IPFS backup kicks in
- Decentralized = keeps running without you!

---

## 🎯 How Everything Connects

### Flow 1: User Signs Up
```
1. User creates account
2. Gets FREE tier (10 domains max)
3. Can import 10 domains via CSV
4. Content rotates automatically (rotation_helpers.py)
5. Can upgrade to Pro ($5/mo) for 50 domains
```

### Flow 2: Import Domains
```
1. Check membership tier (membership_system.py)
2. Import domains via CSV (up to limit)
3. Extract by tier (query_by_tier.py)
4. Publish with rotation (rotation_helpers.py)
5. Backup to IPFS (publish_ipfs.py)
```

### Flow 3: Publishing Strategy
```
1. Real domains: Publish daily
2. Fake domains: Publish quarterly (for testing)
3. Rotation: Cycle through automatically
4. Dead man's switch: Auto-publish if inactive 30 days
5. Decentralization: IPFS + Archive.org backup
```

---

## 📊 Current State

**Your domains (8 total):**
```bash
python3 query_by_tier.py --stats
```

**Output:**
- Total: 8 domains
- Foundation tier: 3 (Soulfra, DeathToData, Calriven)
- Creative tier: 1 (HowToCookAtHome)
- No tier (gaming): 4 (need to set tier!)

---

## 🔧 Commands You Can Run Now

### Query Domains
```bash
# Get all foundation domains
python3 query_by_tier.py --tier foundation

# Get domains for pro users
python3 query_by_tier.py --membership pro

# Get all cooking domains
python3 query_by_tier.py --category cooking

# Export to JSON
python3 query_by_tier.py --tier foundation --export json

# Export to CSV
python3 query_by_tier.py --tier business --export csv
```

### Check Statistics
```bash
python3 query_by_tier.py --stats
```

---

## 🚀 Posting Real + Fake Domains Together

**Your question:** "why can't we just post our own domains and these fake ones?"

**Answer:** You CAN! Here's how:

### Strategy 1: Tag Test Domains
```sql
-- Add a test flag to brands table
ALTER TABLE brands ADD COLUMN is_test BOOLEAN DEFAULT 0;

-- Mark fake domains
UPDATE brands SET is_test = 1 WHERE domain LIKE 'test%';
UPDATE brands SET is_test = 1 WHERE domain IN ('simpledinner.org', 'websolutions.io');

-- Query real domains only
SELECT * FROM brands WHERE is_test = 0;

-- Query test domains
SELECT * FROM brands WHERE is_test = 1;
```

### Strategy 2: Publishing Schedule
```python
# Monday-Friday: Real domains
# Saturday: Fake domain (quarterly check)
# Sunday: Auto-validate all posts

from datetime import datetime

def get_todays_domain():
    day = datetime.now().weekday()

    if day < 5:  # Mon-Fri
        return get_real_domain()
    elif day == 5:  # Saturday
        return get_fake_domain()  # Quarterly test
    else:  # Sunday
        return validate_all_domains()
```

### Strategy 3: Rotation (Dead Man's Switch)
```python
# Rotate through all domains automatically
# Real domains: Daily rotation
# Fake domains: Weekly rotation (for testing)
# If no manual post for 30 days → auto-publish

from rotation_helpers import get_rotation_context

# Get next domain in rotation
next_domain = get_rotation_context('domain_pool', 'daily')

# Mix real + fake for variety
domains = get_real_domains() + get_fake_domains()
shuffle(domains)  # Random mix
publish_next(domains[today_index])
```

---

## 🔒 Decentralization (You Asked About This!)

**Your systems that enable decentralization:**

### 1. IPFS Publishing
**File:** `publish_ipfs.py`

- Publishes to IPFS (permanent decentralized storage)
- Updates DNS TXT records with IPFS hash
- Content stays online even if server dies
- True decentralization!

### 2. Archive.org Integration
**File:** `publish_everywhere.py`

- Archives to Wayback Machine
- Permanent backup
- Decentralized preservation

### 3. Dead Man's Switch
**Concept:** If you're inactive for 30 days