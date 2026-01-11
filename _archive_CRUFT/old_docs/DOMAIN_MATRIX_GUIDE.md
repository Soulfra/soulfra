# 🧠 Domain Matrix Guide - Build The Matrix

## The Big Picture

You've built an email system, BIP-39 recovery codes, and now you're seeing **The Matrix** - how everything connects.

**Currently Live:**
- ✅ cringeproof.com (GitHub Pages)
- ✅ soulfra.github.io (GitHub Pages)
- ⚠️ soulfra.com (points elsewhere)

**The Vision:**
- Multiple domains (calriven.com, deathtodata.com, howtocookathome.com, etc.)
- Each domain = Different theme/personality
- Users unlock domains via tier progression (GitHub stars)
- All powered by ONE database (The Matrix underneath)

## The Architecture

### Like The Matrix Movie

```
┌─────────────────────────────────────────────┐
│         THE MATRIX (soulfra.db)             │
│                                             │
│  One database, infinite realities           │
│  Users navigate different domains            │
│  Same code (app.py) powers everything       │
└─────────────────────────────────────────────┘
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
soulfra.com                   calriven.com
(purple theme)                (orange theme)
(hub network)                 (technical docs)
    ↓                               ↓
Same posts table            Same posts table
WHERE brand_id=1           WHERE brand_id=2
```

### Like Linux From Scratch

```
/etc/systemd/system/          →  brands table
    soulfra.service           →  Brand row 1
    calriven.service          →  Brand row 2
    deathtodata.service       →  Brand row 3

systemctl enable soulfra      →  DNS pointing
systemctl start soulfra       →  Flask app running
journalctl -u soulfra         →  Email outbox logs
```

### Like SQL JOINs

```sql
-- The Matrix: How everything connects

SELECT *
FROM brands b                    -- Domains/realities
LEFT JOIN posts p
    ON p.brand_id = b.id        -- Content per domain
LEFT JOIN comments c
    ON c.post_id = p.id         -- Discussions per post
LEFT JOIN users u
    ON u.id = c.user_id         -- People in the Matrix
LEFT JOIN email_outbox e
    ON e.professional_id = ...  -- Recovery emails
```

### Like OOP Classes

```python
class Brand:
    """Each domain is an instance"""
    def __init__(self, name, colors, personality):
        self.name = name
        self.colors = colors  # Visual DNA
        self.personality = personality  # AI persona

    def compile_theme(self):
        """Generate CSS (like binary compilation)"""
        return f":root {{ --color: {self.colors[0]} }}"

# Each domain = instance
soulfra = Brand("Soulfra", ["#667eea"], "professional")
calriven = Brand("CalRiven", ["#FF5722"], "technical")
```

## Current System State

### Database Tables (95 total)

**Key Tables:**
```
brands (1 row)        - Domain/brand definitions
users (?)             - GitHub authenticated users
posts (?)             - Content (JOINs to brands)
comments (?)          - Discussions (JOINs to posts)
email_outbox (2 rows) - Recovery emails (internal mailbox)
professionals (17)    - StPetePros businesses
```

**Tier System Tables:**
```
user_achievements     - GitHub stars, repos, etc.
domain_launches       - When domains were unlocked
custom_domains        - User-owned domains
```

**The Matrix Connections:**
```
brands ← posts        (brand_id)
posts ← comments      (post_id)
comments ← users      (user_id)
brands ← images       (brand_id)
```

### Brands in Database

Currently **1 brand**:
```
ID: 1
Name: StPetePros
Slug: stpetepros
Domain: soulfra.com
Tier: foundation
```

**Missing brands** (exist in code, not database):
- CalRiven (calriven.com)
- DeathToData (deathtodata.com)
- HowToCookAtHome (howtocookathome.com)
- CringeProof (cringeproof.com)

### Tier Progression System

**Hardcoded in** `core/tier_progression_engine.py`:

```python
Tier 0: Entry (FREE)
- soulfra.com only
- Browse, read content
- 0% ownership

Tier 1: Commenter (1 GitHub star)
- soulfra.com + deathtodata.com + calriven.com
- Comment, review, submit ideas
- 5% ownership base

Tier 2: Contributor (2+ stars, 5+ comments)
- All Tier 1 + howtocookathome.com + stpetepros.com
- Post content, voice memos
- 7% ownership base

Tier 3: Creator (10+ stars OR 50+ repos)
- All Tier 2 + random daily domain
- Moderate, admin features
- 10% ownership base

Tier 4: VIP (100+ repos, 50+ followers)
- ALL domains + choose premium
- Full admin, revenue share
- 25% ownership base
```

## Tools Built

### 1. Domain Builder Jupyter Notebook

**File:** `domain_matrix_builder.ipynb`

**What it does:**
- Cell 1: SELECT (query brands)
- Cell 2: INSERT (create new brand)
- Cell 3: JOIN (map to GitHub repo)
- Cell 4: WHERE (filter by tier)
- Cell 5: GROUP BY (aggregate stats)
- Cell 6: ORDER BY (rank domains)
- Cell 7: UNION (see complete matrix)

**Like SQL in Jupyter:**
```python
# Cell 1 = SELECT * FROM brands
brands = db.execute("SELECT * FROM brands").fetchall()

# Cell 2 = INSERT INTO brands (...)
new_brand = {'name': 'CalRiven', 'colors': [...]}
db.execute("INSERT INTO brands ...", new_brand)

# Cell 3 = JOIN with GitHub
github_map['calriven.com'] = {'owner': 'soulfra', 'repo': 'calriven'}
```

**Usage:**
```bash
jupyter notebook domain_matrix_builder.ipynb
```

### 2. Brand Matrix Visualizer

**File:** `brand_matrix_visualizer.py`

**What it does:**
- Shows all brands (like `htop`)
- Shows JOIN relationships (how tables connect)
- Shows tier progression (unlock path)
- Shows individual brand details (like `systemctl status`)

**Like Linux tools:**
```bash
# Full matrix (like htop)
python3 brand_matrix_visualizer.py

# Single brand (like systemctl status calriven)
python3 brand_matrix_visualizer.py calriven

# JOIN view (how tables connect)
python3 brand_matrix_visualizer.py --joins

# Tier view (unlock progression)
python3 brand_matrix_visualizer.py --tiers
```

**Output:**
```
🧠 ====================================================================
                         THE MATRIX
======================================================================

ID   NAME                 SLUG            TIER         DOMAIN
--------------------------------------------------------------------------------
🔷 1  StPetePros           stpetepros      foundation   soulfra.com

   Total brands: 1
```

## How to Build More Domains

### Option 1: Jupyter Notebook (Interactive)

```bash
jupyter notebook domain_matrix_builder.ipynb
```

**Run cells:**
1. Cell 1: See existing brands
2. Cell 2: Modify brand config, run to INSERT
3. Cell 3: See GitHub mapping instructions
4. Cell 7: Verify brand in matrix

### Option 2: Direct SQL (Fast)

```bash
sqlite3 soulfra.db
```

```sql
INSERT INTO brands (
    name, slug, domain, tier, category,
    color_primary, color_secondary, color_accent,
    personality, config_json
) VALUES (
    'CalRiven',
    'calriven',
    'calriven.com',
    'foundation',
    'technical',
    '#FF5722',
    '#FF9800',
    '#FFC107',
    'Technical, precise, systematic',
    '{"colors": ["#FF5722", "#FF9800", "#FFC107"]}'
);
```

### Option 3: Python Script (Automated)

```python
from database import get_db

db = get_db()
db.execute('''
    INSERT INTO brands (name, slug, domain, tier, ...)
    VALUES (?, ?, ?, ?, ...)
''', ('CalRiven', 'calriven', 'calriven.com', 'foundation', ...))
db.commit()
```

## How Users Pick Domains

### Tier 1: Auto-Unlock (Foundation)

Users DON'T pick - they unlock by starring:

```python
# User stars soulfra/calriven on GitHub
github_star_event → check_tier() → unlock_domains()

# Automatically unlocked:
- soulfra.com (always accessible)
- calriven.com (Tier 1 foundation)
- deathtodata.com (Tier 1 foundation)
```

### Tier 2+: User Choice (Creative)

Users CAN pick from available:

```python
# Tier 2: Choose 1 creative domain
choices = ['howtocookathome.com', 'stpetepros.com']
user.select_domain('howtocookathome.com')

# Tier 3: Random daily rotation
daily_domain = get_random_domain_for_today()
# Changes every day!

# Tier 4: Choose any premium domain
all_domains = get_all_domains()
user.pick_favorites(all_domains)
```

## CalRiven vs User-Picked Domains

**CalRiven:**
- Foundation tier (Tier 1)
- Auto-unlocked by starring GitHub repo
- Users don't "pick" it, they unlock it
- Always available once unlocked

**User-Picked:**
- Creative tier (Tier 2+)
- User explicitly chooses
- Limited selections (1 at Tier 2)
- More choices as tier increases

**Example Flow:**

```
User signs up
    ↓
Tier 0: Can only see soulfra.com
    ↓
User stars github.com/soulfra/calriven
    ↓
Tier 1 achieved!
    ↓
Auto-unlock: calriven.com + deathtodata.com
    ↓
User posts 5+ comments
    ↓
Tier 2 achieved!
    ↓
Prompt: "Choose a creative domain!"
    ↓
Options: howtocookathome.com OR stpetepros.com
    ↓
User picks: howtocookathome.com
    ↓
Now has access to:
- soulfra.com (always)
- calriven.com (Tier 1 auto)
- deathtodata.com (Tier 1 auto)
- howtocookathome.com (Tier 2 choice)
```

## Connecting to GitHub Pages

### Current State

**Live on GitHub Pages:**
```
✅ cringeproof.com (working)
✅ soulfra.github.io (working)
⚠️ soulfra.com (points elsewhere - old?)
```

### Multi-Domain Setup

**Each domain needs:**
1. GitHub repo (github.com/soulfra/calriven)
2. CNAME file (points calriven.com → GitHub Pages)
3. DNS configuration (at registrar)
4. Build/deploy system

**Example for CalRiven:**

```bash
# 1. Create GitHub repo
gh repo create soulfra/calriven --public

# 2. Add CNAME file
cd ~/Desktop/calriven.github.io
echo "calriven.com" > CNAME
git add CNAME
git commit -m "Add custom domain"
git push

# 3. Configure DNS (at domain registrar)
# A record: @ → 185.199.108.153 (GitHub Pages IP)
# CNAME: www → soulfra.github.io

# 4. Enable in GitHub repo settings
# Settings → Pages → Custom domain → calriven.com
```

### Unified Deploy System

**Build all domains from ONE database:**

```bash
# Export StPetePros to soulfra.github.io
python3 export_stpetepros.py

# Export CalRiven content to calriven.github.io
python3 export_calriven.py

# Export DeathToData to deathtodata.github.io
python3 export_deathtodata.py
```

**OR build once, deploy everywhere:**

```python
# build_all_domains.py
for brand in get_brands():
    export_to_github_pages(brand)
    deploy(f"{brand.slug}.github.io")
```

## The Matrix Underneath

### Same Code, Different Realities

**app.py runs on all domains:**

```python
# Before every request
@app.before_request
def detect_brand():
    # Check which domain user is on
    brand = detect_brand_from_subdomain()

    if request.host == 'calriven.com':
        # Load CalRiven theme (orange)
        g.brand = get_brand('calriven')
        g.brand_css = compile_theme(g.brand)
    elif request.host == 'soulfra.com':
        # Load Soulfra theme (purple)
        g.brand = get_brand('soulfra')
        g.brand_css = compile_theme(g.brand)
```

**Same route, different content:**

```python
@app.route('/')
def index():
    # Get posts for THIS brand
    posts = db.execute('''
        SELECT * FROM posts
        WHERE brand_id = ?
    ''', (g.brand.id,))

    return render_template('index.html',
                         posts=posts,
                         brand_css=g.brand_css)
```

**Result:**
- soulfra.com/ → Purple theme, Soulfra posts
- calriven.com/ → Orange theme, CalRiven posts
- Same database, same code, different realities!

## Testing The Matrix

### Test 1: Local Subdomains

```bash
# Start Flask
python3 app.py

# Visit different "realities"
open http://localhost:5001/              # Default (no brand)
open http://stpetepros.localhost:5001/   # StPetePros theme
open http://calriven.localhost:5001/     # CalRiven theme (if created)
```

### Test 2: Visualize Matrix

```bash
# See all brands
python3 brand_matrix_visualizer.py

# See JOINs
python3 brand_matrix_visualizer.py --joins

# See tiers
python3 brand_matrix_visualizer.py --tiers

# See single brand
python3 brand_matrix_visualizer.py calriven
```

### Test 3: Jupyter Notebook

```bash
# Build new domain interactively
jupyter notebook domain_matrix_builder.ipynb

# Run Cell 1: See current brands
# Run Cell 2: Create CalRiven
# Run Cell 7: Verify in matrix
```

## Next Steps

### Immediate (Proof of Concept)

1. **Create CalRiven brand:**
   ```bash
   jupyter notebook domain_matrix_builder.ipynb
   # Run Cell 2 (modify config for CalRiven)
   ```

2. **Verify it exists:**
   ```bash
   python3 brand_matrix_visualizer.py
   # Should show: StPetePros + CalRiven
   ```

3. **Test subdomain:**
   ```bash
   python3 app.py
   open http://calriven.localhost:5001/
   # Should show orange theme
   ```

### Production (Real Deployment)

1. **Point domains to GitHub Pages:**
   - Configure DNS for calriven.com
   - Add CNAME files
   - Enable custom domains in GitHub

2. **Build tier progression UI:**
   - Dashboard showing unlock progress
   - "Star to unlock" buttons
   - Domain selection interface

3. **Deploy Flask backend:**
   - Heroku/Railway for dynamic routing
   - OR keep GitHub Pages static
   - OR hybrid (static sites + API)

4. **Email existing professionals:**
   - Send BIP-39 recovery codes
   - Explain tier system
   - Invite to unlock domains

## Summary

**What You Built:**
- ✅ Email outbox system (internal mailbox)
- ✅ BIP-39 recovery codes (crypto-style)
- ✅ Domain Matrix Builder (Jupyter notebook)
- ✅ Brand Matrix Visualizer (htop for domains)
- ✅ Tier progression system (unlock path)

**What Exists in Code:**
- ✅ Subdomain routing (core/subdomain_router.py)
- ✅ Tier progression (core/tier_progression_engine.py)
- ✅ Brand theming (CSS compilation)
- ✅ GitHub star validation

**What's Missing:**
- ⚠️ Brands in database (only 1 exists)
- ⚠️ Domain DNS configuration
- ⚠️ Tier progression UI
- ⚠️ Multi-domain GitHub Pages setup

**The Matrix is Real:**
- Same database (soulfra.db)
- Same code (app.py)
- Different domains (infinite realities)
- Users unlock via GitHub stars

**Like:**
- Linux daemons (each brand = service)
- SQL JOINs (everything connects)
- OOP classes (each domain = instance)
- The Matrix (one code, many realities)

**Start building:** `jupyter notebook domain_matrix_builder.ipynb`

**The Matrix has you.**
