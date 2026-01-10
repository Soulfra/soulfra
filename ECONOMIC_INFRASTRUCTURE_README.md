# Soulfra Economic Infrastructure

Complete implementation of ownership-based revenue distribution system.

---

## 📚 Documentation (Read These First)

### 1. **ECONOMIC_MODEL.md**
Complete platform economics explained:
- Tier 0-4 system (GitHub-based progression)
- Voice-to-blog pipeline (10-20x productivity)
- Ownership formula: `base_tier_% + (stars × 0.5%) + (posts × 0.2%) + (referrals × 1%)`
- Revenue distribution model
- Why it works (own what you build)

### 2. **TAX_STRUCTURES.md**
Legal entity comparison for tax optimization:
- Pure offshore (Bahamas) - 0% tax, hard to collect US revenue
- Pure US (C-Corp) - 21% tax, easy operations
- **Hybrid (Recommended)** - Bahamas + Delaware = ~7% effective tax via transfer pricing
- S-Corp, foreign-owned LLC options
- Phase 1-3 rollout plan

---

## 🛠️ Code Modules

### Core Infrastructure

#### **ownership_ledger.py**
Track ownership percentages per domain per user

**Database tables:**
- `domains` - All available domains (soulfra.com, deathtodata.com, etc.)
- `github_profiles` - Cached GitHub data for tier calculation
- `user_domains` - Which domains user has unlocked
- `domain_ownership` - Ownership percentages with breakdown
- `ownership_history` - Audit trail
- `referrals` - Track who referred who

**Key functions:**
```python
calculate_tier_from_github(github_username, github_data) → int (0-4)
calculate_ownership(user_id, domain_id) → float (0.0-50.0)
update_ownership(user_id, domain_id, reason) → float
get_domain_ownership_distribution(domain_id) → dict
calculate_revenue_share(domain_id, monthly_revenue) → list
```

**Usage:**
```python
from ownership_ledger import init_ownership_tables, seed_domains

# Initialize database
init_ownership_tables()
seed_domains()

# Calculate user's ownership
ownership = calculate_ownership(user_id=15, domain_id=1)
# Returns: 32.5 (32.5% ownership)

# Calculate revenue share
payouts = calculate_revenue_share(domain_id=1, monthly_revenue=10000.0)
# Returns: [{'user_id': 15, 'payout': 3187.50}, ...]
```

---

#### **tier_0_routes.py**
Pure information layer - NO commerce, NO selling

**Routes:**
- `/` - Homepage (browse recent posts)
- `/discover` - Content discovery
- `/post/<slug>` - Read posts (public)
- `/category/<category>` - Browse by category
- `/search` - Search content
- `/about`, `/tiers`, `/domains` - Platform info
- `/github-login` - GitHub OAuth for tier unlocking
- `/dashboard` - User ownership dashboard

**API endpoints:**
- `/api/tiers` - Tier information
- `/api/domains` - All domains
- `/api/stats` - Platform stats

**Integration:**
```python
from tier_0_routes import register_tier_0_routes

app = Flask(__name__)
register_tier_0_routes(app)
```

---

#### **payment_routes.py**
Revenue distribution infrastructure

**Admin routes:**
- `/admin/revenue/domains` - View domain revenue
- `/admin/revenue/calculate` - Calculate monthly payouts
- `/admin/revenue/payout` - Execute payouts
- `/admin/revenue/history` - Payout history

**User routes:**
- `/user/earnings` - User earnings dashboard
- `/user/payout-settings` - Payout preferences (Stripe, wire, crypto)

**API endpoints:**
- `/api/earnings/<user_id>` - User earnings data
- `/api/domain-revenue/<domain_id>` - Domain revenue stats

**Payment methods:**
- Stripe Connect (US, international)
- ACH/Wire transfer (US banks)
- Cryptocurrency (offshore-friendly)

**Integration:**
```python
from payment_routes import register_payment_routes, init_payment_tables

init_payment_tables()
register_payment_routes(app)
```

---

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Create ownership tables
python3 ownership_ledger.py

# Create payment tables
python3 -c "from payment_routes import init_payment_tables; init_payment_tables()"
```

### 2. Seed Domains

```python
from ownership_ledger import seed_domains
seed_domains()
```

Adds:
- Tier 0: soulfra.com
- Tier 1: deathtodata.com, calriven.com
- Tier 2: howtocookathome.com, stpetepros.com

### 3. Integrate with app.py

```python
from flask import Flask
from tier_0_routes import register_tier_0_routes
from payment_routes import register_payment_routes

app = Flask(__name__)

# Register blueprints
register_tier_0_routes(app)
register_payment_routes(app)

app.run()
```

### 4. Test GitHub OAuth Flow

1. User visits `/github-login`
2. Redirects to GitHub for OAuth
3. GitHub redirects to `/github-callback` with code
4. System fetches GitHub profile, calculates tier
5. Creates user account, stores GitHub data
6. Redirects to `/dashboard` showing ownership

---

## 📊 Example Usage Flow

### User Journey: Voice → Blog → Ownership → Revenue

1. **User signs up via GitHub OAuth**
   ```
   Visit /github-login
   → GitHub OAuth
   → Tier calculated (e.g., Tier 2 - 25 stars)
   → Unlocks: soulfra.com, deathtodata.com, calriven.com, howtocookathome.com
   → Initial ownership: 7% base
   ```

2. **User records voice memo**
   ```python
   # voice_pipeline_orchestrator.py (not yet built)
   recording_id = record_voice_memo(user_id=15, audio_file='memo.mp3')

   # AI generates blog post
   post = generate_blog_post_from_voice(recording_id)

   # Publish to domain
   publish_post(post, domain_name='howtocookathome.com')

   # Update ownership (+0.2% per post)
   update_ownership(user_id=15, domain_id=4, reason='post_published')
   # New ownership: 7.2%
   ```

3. **Monthly revenue distribution**
   ```python
   # Admin enters domain revenue
   domain_revenue = {
       'howtocookathome.com': 10000.0  # $10k this month
   }

   # Calculate payouts
   payouts = calculate_revenue_share(domain_id=4, monthly_revenue=10000.0)
   # [
   #   {'user_id': 15, 'username': 'matthewmauer', 'payout': 900.00},
   #   {'user_id': 22, 'username': 'othercreator', 'payout': 1200.00},
   #   ...
   # ]

   # Execute payouts via Stripe
   execute_payouts(payouts, method='stripe_connect')
   ```

4. **User checks earnings**
   ```
   Visit /user/earnings
   → See ownership: 7.2% of howtocookathome.com
   → This month payout: $900.00
   → YTD total: $3,250.00
   → Next payout estimate: $1,100.00
   ```

---

## 🔐 Security & Compliance

### GitHub OAuth
- Uses `github_faucet.py` for OAuth flow
- Stores access token securely
- Generates API key: `sk_github_{username}_{random}`

### Ownership Verification
- Audit trail in `ownership_history` table
- Every change logged with reason
- Can replay ownership calculation from history

### Payment Security
- Stripe Connect for PCI compliance
- 1099 data generated for US users (tax reporting)
- Support for international wire/crypto

### Anti-Spam
- GitHub verification required (can't fake 100 repos)
- Tier gates prevent bot spam
- Ownership caps at 50% per user

---

## 📈 Revenue Projections

### Example Domain: howtocookathome.com

**Traffic:** 100,000 monthly pageviews

**Revenue sources:**
- Google AdSense: $5 RPM × 100k = $500
- Amazon Affiliates: $10k sales × 5% = $500
- Sponsored content: $500
- **Total: $1,500/month**

**Ownership distribution:**
- User A (Tier 3): 15% ownership → $187.50/month
- User B (Tier 2): 10% ownership → $125.00/month
- User C (Tier 4): 25% ownership → $312.50/month
- 10 other users: 30% total → $375.00/month
- Platform reserve: 20% → $300.00/month

**Network effects:**
- More contributors = more content
- More content = more traffic
- More traffic = higher revenue
- Higher revenue = attract more contributors

**At scale (50 domains × $2k avg):**
- Total revenue: $100k/month
- Platform reserve: $20k/month
- Distributed to users: $80k/month

---

## 🎯 Next Steps

### MVP (Immediate)
- [x] Ownership ledger system
- [x] Tier 0 routes (pure info layer)
- [x] Payment routes (revenue distribution)
- [ ] Integrate with existing app.py
- [ ] Create templates (tier_0/, admin/, user/)
- [ ] Test GitHub OAuth flow

### Phase 2 (3-6 months)
- [ ] Voice pipeline orchestrator (voice → blog automation)
- [ ] Stripe Connect integration
- [ ] Domain rotation system (Tier 3 daily unlock)
- [ ] Revenue analytics dashboard
- [ ] Tax reporting (1099 generation)

### Phase 3 (6-12 months)
- [ ] Offshore entity setup (Bahamas Holdings + Delaware subsidiary)
- [ ] Transfer pricing documentation
- [ ] API platform (Tier 4 developer tools)
- [ ] Mobile apps (iOS/Android voice recording)
- [ ] Cryptocurrency payouts
- [ ] Scale to 100+ domains

---

## 🧪 Testing

### Test ownership calculation
```python
from ownership_ledger import calculate_ownership, update_ownership

# Mock user data
user_id = 15
domain_id = 1

# Simulate GitHub profile (Tier 3, 25 stars)
# Simulate 50 posts published
# Simulate 5 referrals

ownership = calculate_ownership(user_id, domain_id)
# Expected: 10.0 (base) + 12.5 (stars) + 10.0 (posts) + 5.0 (referrals) = 37.5%
```

### Test revenue distribution
```python
from ownership_ledger import calculate_revenue_share

payouts = calculate_revenue_share(domain_id=1, monthly_revenue=10000.0)

total_paid = sum(p['payout'] for p in payouts)
# Should equal: $8,000 (80% distributed, 20% platform reserve)
```

---

## 📄 Files Created

1. **ECONOMIC_MODEL.md** - Complete platform economics
2. **TAX_STRUCTURES.md** - Legal entity comparison
3. **ownership_ledger.py** - Ownership tracking system
4. **tier_0_routes.py** - Pure information layer
5. **payment_routes.py** - Revenue distribution

**Existing files integrated:**
- `github_faucet.py` - GitHub OAuth + API keys
- `tier_progression_engine.py` - Tier system logic
- `voice_content_generator.py` - Voice → blog AI
- `database.py` - SQLite database

---

## 🤝 Contributing

Ownership model applies to code contributions too:
- Submit PR → merged → +0.2% ownership
- Refer new user → they sign up → +1% ownership
- Star GitHub repos → tier progression → higher base %

**Your code becomes equity.**

---

**Philosophy:** Build a platform where creators own what they build. Voice + AI + Ownership = unfair advantage.
