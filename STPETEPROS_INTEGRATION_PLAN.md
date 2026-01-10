# StPetePros.com Integration Plan

**How to use the Soulfra platform to run stpetepros.com (multi-domain "dogfooding" strategy)**

## Overview

You have two domains on the same GoDaddy account:
- **soulfra.com** → Creative storytelling platform (current)
- **stpetepros.com** → Professional services directory (new)

This guide shows how to **"dogfood"** (use your own platform) to run both domains from a single codebase, sharing:
- User accounts
- QR code systems
- AI infrastructure
- Content management
- Analytics/tracking

---

## Architecture: Multi-Tenant Single Codebase

```
┌─────────────────────────────────────────────────┐
│          Soulfra Platform (Single Codebase)     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ soulfra.com  │      │stpetepros.com│        │
│  │              │      │              │        │
│  │ Brand: 🟣    │      │ Brand: 🔵    │        │
│  │ Story focus  │      │ Services     │        │
│  └──────────────┘      └──────────────┘        │
│         │                      │                │
│         └──────────┬───────────┘                │
│                    │                            │
│         ┌──────────▼──────────┐                 │
│         │  Shared Database    │                 │
│         │  - users            │                 │
│         │  - posts            │                 │
│         │  - qr_codes         │                 │
│         │  - brands           │                 │
│         └─────────────────────┘                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Step 1: Add StPetePros to Brand Configuration

### File: `vanity_qr.py`

**Current Configuration:**
```python
BRAND_DOMAINS = {
    'cringeproof': {
        'domain': 'cringeproof.com',
        'colors': {'primary': '#2D3748', 'secondary': '#E53E3E'},
        'style': 'minimal'
    },
    'soulfra': {
        'domain': 'soulfra.com',
        'colors': {'primary': '#8B5CF6', 'secondary': '#3B82F6'},
        'style': 'rounded'
    },
    'howtocookathome': {
        'domain': 'howtocookathome.com',
        'colors': {'primary': '#F97316', 'secondary': '#EAB308'},
        'style': 'circles'
    }
}
```

**Add StPetePros:**
```python
BRAND_DOMAINS = {
    # ... existing brands ...

    'stpetepros': {
        'domain': 'stpetepros.com',
        'colors': {
            'primary': '#0F172A',    # Professional dark blue
            'secondary': '#0EA5E9',  # Sky blue
            'accent': '#10B981'      # Success green
        },
        'style': 'professional',     # Clean, business-oriented styling
        'category': 'services',      # Services directory (vs 'blog', 'story', etc.)
        'tagline': 'Your St. Petersburg Professional Network',
        'description': 'Find trusted professionals, leave reviews, earn loyalty rewards',
        'features': [
            'professional_directory',
            'customer_reviews',
            'qr_business_cards',
            'loyalty_rewards',
            'skill_certifications'
        ]
    }
}
```

---

## Step 2: Database Schema Updates

### Add Brand-Specific Content Types

**Migration: `migrate_stpetepros.py`**

```python
#!/usr/bin/env python3
"""
Add StPetePros tables to database
"""
from database import get_db

def migrate_stpetepros():
    """Add tables for professional services platform"""
    db = get_db()

    # Professionals/Service Providers
    db.execute('''
        CREATE TABLE IF NOT EXISTS professionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            business_name TEXT NOT NULL,
            category TEXT,  -- 'plumber', 'electrician', 'lawyer', etc.
            bio TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            qr_business_card BLOB,  -- QR code for digital business card
            verified BOOLEAN DEFAULT 0,
            rating_avg REAL DEFAULT 0.0,
            review_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Professional Reviews
    db.execute('''
        CREATE TABLE IF NOT EXISTS professional_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professional_id INTEGER NOT NULL,
            reviewer_user_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            qr_verification_code TEXT,  -- QR code scanned to verify service
            service_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id),
            FOREIGN KEY (reviewer_user_id) REFERENCES users(id)
        )
    ''')

    # Loyalty Rewards (shared across brands)
    db.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            brand_slug TEXT NOT NULL,  -- 'stpetepros', 'soulfra', etc.
            points INTEGER DEFAULT 0,
            points_lifetime INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'bronze',  -- bronze, silver, gold, platinum
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Skill Certifications (QR-based)
    db.execute('''
        CREATE TABLE IF NOT EXISTS skill_certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            skill_category TEXT,
            level TEXT,  -- 'beginner', 'intermediate', 'expert'
            qr_certificate BLOB,  -- QR code with verification
            issued_by TEXT,
            verified BOOLEAN DEFAULT 0,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    print("✅ StPetePros tables created successfully")

if __name__ == '__main__':
    migrate_stpetepros()
```

---

## Step 3: Domain Routing Configuration

### Detect Brand from Domain

**File: `subdomain_router.py` (update existing)**

```python
def detect_brand_from_domain():
    """
    Detect brand from full domain (not just subdomain)

    Handles:
    - soulfra.com → 'soulfra'
    - stpetepros.com → 'stpetepros'
    - cringeproof.com → 'cringeproof'
    - localhost:5001 → 'soulfra' (default for development)

    Returns:
        Brand dict or None
    """
    from flask import request
    from vanity_qr import BRAND_DOMAINS

    host = request.host.lower()

    # Remove port if present (localhost:5001 → localhost)
    if ':' in host:
        host = host.split(':')[0]

    # Check each brand's domain
    for brand_slug, brand_config in BRAND_DOMAINS.items():
        if brand_config['domain'] in host:
            return {
                'slug': brand_slug,
                **brand_config
            }

    # Default to soulfra for development
    if 'localhost' in host or '127.0.0.1' in host:
        return {
            'slug': 'soulfra',
            **BRAND_DOMAINS['soulfra']
        }

    return None
```

### Brand-Specific Templates

**File: `app.py` (update Flask routes)**

```python
from subdomain_router import detect_brand_from_domain

@app.before_request
def set_brand_context():
    """Inject brand context into every request"""
    g.brand = detect_brand_from_domain()

    # Set brand-specific features
    if g.brand:
        g.features = g.brand.get('features', [])
        g.category = g.brand.get('category', 'blog')
        g.theme = {
            'primary': g.brand['colors']['primary'],
            'secondary': g.brand['colors']['secondary'],
            'accent': g.brand['colors']['accent']
        }

@app.route('/')
def homepage():
    """Brand-specific homepage"""
    if g.brand['slug'] == 'stpetepros':
        # Show professional directory homepage
        return render_template('stpetepros/homepage.html', brand=g.brand)
    elif g.brand['slug'] == 'soulfra':
        # Show storytelling platform homepage
        return render_template('soulfra/homepage.html', brand=g.brand)
    else:
        # Default homepage
        return render_template('homepage.html', brand=g.brand)
```

---

## Step 4: GoDaddy DNS Configuration

### DNS Records for Both Domains

**In GoDaddy Control Panel:**

#### soulfra.com (existing)
```
Type    Name    Value                   TTL
A       @       YOUR_SERVER_IP          600
A       www     YOUR_SERVER_IP          600
CNAME   *       soulfra.com             600  (for subdomains)
```

#### stpetepros.com (new)
```
Type    Name    Value                   TTL
A       @       YOUR_SERVER_IP          600  (same server as soulfra.com!)
A       www     YOUR_SERVER_IP          600
CNAME   *       stpetepros.com          600  (for subdomains)
```

**Key Point:** Both domains point to the **same server IP**. The Flask app uses `request.host` to determine which brand to show.

---

## Step 5: Content Strategy by Brand

### Soulfra.com Content Focus
- **Primary**: Story chapters (Soulfra Dark)
- **Secondary**: Creative writing, worldbuilding
- **QR Codes**: Trading cards, collectibles
- **Audience**: Story readers, fans, creative community

### StPetePros.com Content Focus
- **Primary**: Professional services directory
- **Secondary**: Customer reviews, business networking
- **QR Codes**: Business cards, loyalty rewards, certifications
- **Audience**: St. Petersburg locals, business owners, service seekers

---

## Step 6: Shared Features vs Brand-Specific

### Shared Across All Brands
- User authentication (single login works everywhere)
- QR code infrastructure (multi_part_qr.py, vanity_qr.py)
- AI systems (llm_router.py, story_modes_system.py)
- Analytics/tracking
- Database

### StPetePros-Specific Features
- Professional directory
- Customer review system
- QR business cards
- Service booking
- Loyalty rewards program
- Skill certifications

### Soulfra-Specific Features
- Story chapter serialization
- Trading card printer
- Interactive narrative
- Character submissions
- Radio show integration

---

## Step 7: Implementation Checklist

### Phase 1: Configuration
- [ ] Add `stpetepros` to `BRAND_DOMAINS` in `vanity_qr.py`
- [ ] Run `python3 migrate_stpetepros.py` to add tables
- [ ] Update `subdomain_router.py` to detect domain (not just subdomain)
- [ ] Test locally: Edit `/etc/hosts` to point stpetepros.com to localhost

### Phase 2: Templates
- [ ] Create `templates/stpetepros/` directory
- [ ] Build `homepage.html` for professional directory
- [ ] Create professional profile templates
- [ ] Add review submission forms

### Phase 3: Features
- [ ] Build professional directory (browse/search)
- [ ] Add customer review system
- [ ] Generate QR business cards
- [ ] Implement loyalty rewards tracking
- [ ] Create skill certification system

### Phase 4: DNS & Deployment
- [ ] Configure GoDaddy DNS for stpetepros.com
- [ ] Test both domains point to same server
- [ ] Verify brand detection works (check `g.brand` in Flask)
- [ ] Deploy to production

### Phase 5: Content Migration
- [ ] Import St. Petersburg professionals
- [ ] Seed initial reviews (if available)
- [ ] Create sample business QR cards
- [ ] Set up loyalty tiers

---

## Example Use Cases

### Use Case 1: Professional QR Business Card

**Professional signs up on stpetepros.com:**

```python
from vanity_qr import create_and_save_vanity_qr

# Create QR business card for "Joe's Plumbing"
qr_bytes = create_and_save_vanity_qr(
    full_url='https://stpetepros.com/professionals/joe-plumbing',
    brand_slug='stpetepros',
    custom_code='joe-plumbing'
)

# Generate PDF business card with QR code
# Customer scans → sees profile, reviews, contact info
# Customer can leave review via QR → earn loyalty points
```

### Use Case 2: Cross-Brand User

**User has account on both sites:**

1. Signs up on **soulfra.com** (username: `reader123`)
2. Reads chapters, collects trading cards
3. Same login works on **stpetepros.com**
4. Finds plumber, leaves review, earns points
5. Points tracked separately per brand:
   - Soulfra: 500 story points
   - StPetePros: 250 loyalty points

### Use Case 3: Skill Certification via QR

**Electrician wants to verify license:**

```python
from qr_unified import generate_skill_certification_qr

# Generate QR certificate
cert_qr = generate_skill_certification_qr(
    user_id=42,
    skill_name='Licensed Electrician',
    issued_by='State of Florida',
    verified=True
)

# Professional adds to profile
# Customers scan to verify credentials
```

---

## Database Queries: Brand-Specific Content

### Get All Professionals for StPetePros

```python
from database import get_db

db = get_db()
professionals = db.execute('''
    SELECT * FROM professionals
    WHERE verified = 1
    ORDER BY rating_avg DESC
    LIMIT 20
''').fetchall()
```

### Get User's Loyalty Points (Brand-Specific)

```python
def get_user_loyalty_points(user_id, brand_slug='stpetepros'):
    db = get_db()
    result = db.execute('''
        SELECT points, tier
        FROM loyalty_points
        WHERE user_id = ? AND brand_slug = ?
    ''', (user_id, brand_slug)).fetchone()

    return result or {'points': 0, 'tier': 'bronze'}
```

---

## Benefits of Multi-Domain Dogfooding

### 1. Code Reuse
- Write once, use across both domains
- QR systems work for both stories AND business cards
- AI features (LLM router, story modes) can power professional descriptions

### 2. Shared User Base
- Users don't need separate accounts
- Cross-promotional opportunities
- Network effects (Soulfra readers → StPetePros customers)

### 3. Unified Analytics
- Track user behavior across brands
- Understand cross-brand engagement
- Single dashboard for both domains

### 4. Cost Efficiency
- One server, two domains
- Shared database, backups
- Single codebase to maintain

### 5. Innovation Transfer
- Features built for Soulfra can benefit StPetePros
- Professional network can fund creative projects
- Experimentation on one brand → rollout to others

---

## Testing Multi-Domain Setup Locally

### 1. Edit `/etc/hosts` (macOS/Linux)

```bash
sudo nano /etc/hosts
```

Add:
```
127.0.0.1  soulfra.com
127.0.0.1  www.soulfra.com
127.0.0.1  stpetepros.com
127.0.0.1  www.stpetepros.com
```

### 2. Run Flask App

```bash
python3 app.py
```

### 3. Test Both Domains

```bash
# Visit in browser
http://soulfra.com:5001      # Should show Soulfra homepage
http://stpetepros.com:5001   # Should show StPetePros homepage
```

### 4. Verify Brand Detection

```python
# In Flask route
@app.route('/debug/brand')
def debug_brand():
    return {
        'detected_brand': g.brand['slug'],
        'domain': g.brand['domain'],
        'colors': g.brand['colors'],
        'features': g.brand.get('features', [])
    }
```

Visit:
- `http://soulfra.com:5001/debug/brand` → Should show `'detected_brand': 'soulfra'`
- `http://stpetepros.com:5001/debug/brand` → Should show `'detected_brand': 'stpetepros'`

---

## Future: Add More Brands

Once StPetePros is working, you can easily add more brands:

```python
BRAND_DOMAINS = {
    # ... existing ...

    'newbrand': {
        'domain': 'newbrand.com',
        'colors': {...},
        'style': 'modern',
        'category': 'ecommerce'
    }
}
```

**Same platform, infinite brands.**

---

## Next Steps

1. **Add StPetePros config** → Edit `vanity_qr.py`
2. **Run migration** → `python3 migrate_stpetepros.py`
3. **Test locally** → Edit `/etc/hosts`, verify brand detection
4. **Build templates** → Create `templates/stpetepros/homepage.html`
5. **Configure GoDaddy DNS** → Point stpetepros.com to server IP
6. **Deploy and test** → Verify both domains work in production

---

## Summary

**StPetePros.com integration is straightforward:**

1. Add brand config to `BRAND_DOMAINS`
2. Run database migration for new tables
3. Update routing to detect domain (not subdomain)
4. Point GoDaddy DNS to same server IP
5. Build brand-specific templates and features

**Key Insight:** The Soulfra platform is **multi-tenant by design**. All the QR systems, AI features, and infrastructure work for **any brand** you add.

**Dogfooding = Using your own tools to build your own businesses.**

You're not just building a storytelling platform. You're building **the engine** that can power any content-driven business, from creative fiction to professional services.
