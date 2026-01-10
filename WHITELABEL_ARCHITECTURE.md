# White-Label Architecture - Multi-Tenant Professional Sites

**Date:** 2026-01-09
**Purpose:** How professionals get custom-branded sites (subdomain/domain) on CringeProof platform
**Status:** Architecture specification + existing implementation review

---

## What is "White-Label"?

**Definition:** White-label means each professional gets their own branded website without having to build/host it themselves.

**Example:**
- Joe runs Joe's Plumbing in Tampa
- He signs up for CringeProof Pro ($49/mo)
- He gets: `joesplumbing.cringeproof.com` with his logo, colors, license badge
- Customers see Joe's brand, not CringeProof's
- Joe can optionally upgrade to `joesplumbing.com` (Enterprise tier)

**Why this matters:**
1. **Professional credibility** - Having your own domain > profile on someone else's site
2. **SEO ownership** - Joe ranks for "Tampa plumber" on HIS domain
3. **Lead exclusivity** - Leads go directly to Joe, not a marketplace
4. **Brand consistency** - Matches Joe's truck decals, business cards, etc.

---

## Architecture Overview

### Multi-Tenant Design

**One codebase → Many professional websites**

```
CringeProof Platform (Flask app)
├── Shared infrastructure (one database, one server)
├── Shared templates (one design system)
└── Dynamic routing → different professionals

Professional A (joesplumbing.cringeproof.com)
├── Logo: Joe's Plumbing logo
├── Colors: Blue & white
├── Content: Joe's tutorials
└── License: FL License #CFC1234567

Professional B (acecooling.cringeproof.com)
├── Logo: Ace Cooling logo
├── Colors: Red & gray
├── Content: Ace's tutorials
└── License: FL License #CAC5678901
```

**How it works:**
1. Customer visits `joesplumbing.cringeproof.com`
2. Flask app detects subdomain: `joesplumbing`
3. Looks up professional profile in database
4. Renders shared template with Joe's branding/content
5. Customer sees Joe's site (doesn't know it's CringeProof underneath)

---

## Existing Implementation

### Subdomain Router (`subdomain_router.py`)

**Already implemented in the codebase!**

```python
def subdomain_router(app):
    """
    Route requests based on subdomain
    Example: joesplumbing.cringeproof.com → professional profile page
    """

    @app.before_request
    def detect_subdomain():
        # Get subdomain from request
        subdomain = request.host.split('.')[0]

        if subdomain not in ['www', 'cringeproof', 'localhost']:
            # This is a professional subdomain
            g.subdomain = subdomain
            g.professional = get_professional_by_subdomain(subdomain)
```

**What this enables:**
- Automatic routing based on subdomain
- No additional server configuration needed
- Each professional gets isolated namespace
- Shared infrastructure = low cost per professional

---

## Tier-Based Domain Options

### Free Tier ($0/mo)
**Profile on main site**

```
URL structure:
├── cringeproof.com/p/joesplumbing
└── cringeproof.com/directory/tampa/plumbers

Branding:
├── Name & photo in directory
├── Basic verification badge
├── Standard CringeProof template
└── No custom colors/logo
```

**Why it's limited:**
- Encourages upgrades to Pro
- Still provides value (verified profile)
- Low infrastructure cost

---

### Professional Tier ($49/mo)
**Custom subdomain**

```
URL structure:
├── joesplumbing.cringeproof.com (main)
├── joesplumbing.cringeproof.com/tutorials
├── joesplumbing.cringeproof.com/license-verify
└── joesplumbing.cringeproof.com/contact

Branding:
├── Custom logo (uploaded by professional)
├── Custom color scheme (primary + accent)
├── Custom tagline ("Tampa's Most Trusted Plumber")
├── Enhanced verification badge
└── Professional's business phone/email

pSEO landing pages:
├── joesplumbing.cringeproof.com/tampa-plumber
├── joesplumbing.cringeproof.com/st-petersburg-plumber
├── joesplumbing.cringeproof.com/emergency-plumbing-tampa
└── (50+ auto-generated variations per tutorial)
```

**Database schema:**

```python
class ProfessionalProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)

    # Business info
    business_name = db.Column(db.String(200))
    tagline = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    # Branding
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7))  # Hex color: #0066CC
    accent_color = db.Column(db.String(7))   # Hex color: #FF6600

    # License verification
    license_number = db.Column(db.String(50))
    license_state = db.Column(db.String(2))
    license_type = db.Column(db.String(100))
    license_verified = db.Column(db.Boolean, default=False)
    license_verified_at = db.Column(db.DateTime)

    # Subscription
    tier = db.Column(db.String(20))  # 'free', 'professional', 'enterprise'
    subscription_status = db.Column(db.String(20))  # 'active', 'canceled', 'past_due'
    stripe_customer_id = db.Column(db.String(100))
```

**Template rendering:**

```html
<!-- templates/professional_site.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{ professional.business_name }}</title>
    <style>
        :root {
            --primary-color: {{ professional.primary_color }};
            --accent-color: {{ professional.accent_color }};
        }
    </style>
</head>
<body>
    <header>
        <img src="{{ professional.logo_url }}" alt="{{ professional.business_name }}">
        <h1>{{ professional.business_name }}</h1>
        <p>{{ professional.tagline }}</p>
    </header>

    <!-- License badge -->
    <div class="verification-badge">
        <img src="/static/verified-badge.svg">
        <span>{{ professional.license_state }} Licensed {{ professional.license_type }}</span>
        <a href="/license-verify">Verify License #{{ professional.license_number }}</a>
    </div>

    <!-- Tutorials feed -->
    <section class="tutorials">
        {% for tutorial in professional.tutorials %}
            <article>
                <h2>{{ tutorial.title }}</h2>
                <div>{{ tutorial.html_content | safe }}</div>
                <audio controls src="{{ tutorial.audio_url }}"></audio>
            </article>
        {% endfor %}
    </section>
</body>
</html>
```

---

### Enterprise Tier ($199/mo)
**Custom domain + white-label mobile app**

```
URL structure (OPTION A: Custom subdomain):
├── joesplumbing.cringeproof.com (same as Pro)
└── All Pro features

URL structure (OPTION B: Custom domain):
├── joesplumbing.com (professional's domain)
├── joesplumbing.com/tutorials
├── joesplumbing.com/license-verify
└── joesplumbing.com/contact

Branding:
├── Everything from Pro tier
├── Custom domain (CNAME or full DNS)
├── White-label mobile app (iOS + Android)
├── Custom app icon & branding
├── Remove "Powered by CringeProof" footer
└── API access for CRM integration

White-label mobile app:
├── App name: "Joe's Plumbing"
├── App icon: Joe's logo
├── Push notifications: "New lead from tutorial!"
├── Offline recording: Record tutorials without internet
└── App Store presence: "Joe's Plumbing by Joe's Plumbing LLC"
```

**Custom domain setup:**

```
Professional owns: joesplumbing.com
They add DNS records:

CNAME record:
├── Host: www
├── Value: cringeproof.com
└── TTL: 3600

OR

A record:
├── Host: @
├── Value: 192.0.2.1 (CringeProof server IP)
└── TTL: 3600

SSL certificate:
├── Auto-provisioned via Let's Encrypt
└── Wildcard cert for *.cringeproof.com
```

**Implementation:**

```python
class CustomDomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional_profile.id'))
    domain = db.Column(db.String(255), unique=True)

    # DNS verification
    verification_token = db.Column(db.String(64))
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)

    # SSL
    ssl_certificate_issued = db.Column(db.Boolean, default=False)
    ssl_certificate_expires = db.Column(db.DateTime)

    # Status
    status = db.Column(db.String(20))  # 'pending', 'active', 'failed'


def verify_custom_domain(domain: str, verification_token: str) -> bool:
    """
    Verify professional owns domain by checking TXT record

    Expected TXT record:
    cringeproof-verification=abc123def456
    """
    import dns.resolver

    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            for txt in rdata.strings:
                if txt.decode() == f'cringeproof-verification={verification_token}':
                    return True
    except Exception as e:
        print(f"DNS verification failed: {e}")
        return False

    return False
```

---

## Database Schema (Complete)

### Core Tables

```sql
-- Professionals (one row per professional)
CREATE TABLE professional_profile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),

    -- Identity
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    business_name VARCHAR(200),
    tagline VARCHAR(500),
    bio TEXT,

    -- Contact
    phone VARCHAR(20),
    email VARCHAR(120),
    address_street VARCHAR(200),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zip VARCHAR(10),

    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#0066CC',
    accent_color VARCHAR(7) DEFAULT '#FF6600',
    font_family VARCHAR(100) DEFAULT 'Inter',

    -- License verification
    license_number VARCHAR(50),
    license_state VARCHAR(2),
    license_type VARCHAR(100),
    license_verified BOOLEAN DEFAULT FALSE,
    license_verified_at TIMESTAMP,
    license_api_data JSON,  -- Full response from state API

    -- Subscription
    tier VARCHAR(20) DEFAULT 'free',  -- 'free', 'professional', 'enterprise'
    subscription_status VARCHAR(20),  -- 'active', 'canceled', 'past_due', 'trialing'
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    trial_ends_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tutorials (one row per voice recording)
CREATE TABLE tutorial (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER REFERENCES professional_profile(id),

    -- Content
    title VARCHAR(500),
    audio_url VARCHAR(500),
    transcript TEXT,
    html_content TEXT,  -- AI-generated from transcript

    -- SEO metadata
    meta_description VARCHAR(500),
    keywords TEXT,
    canonical_url VARCHAR(500),

    -- Performance
    view_count INTEGER DEFAULT 0,
    lead_count INTEGER DEFAULT 0,  -- Tracked via UTM params

    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'published', 'archived'
    published_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- pSEO Landing Pages (50+ per tutorial)
CREATE TABLE pseo_landing_page (
    id INTEGER PRIMARY KEY,
    tutorial_id INTEGER REFERENCES tutorial(id),
    professional_id INTEGER REFERENCES professional_profile(id),

    -- URL
    slug VARCHAR(200),  -- 'tampa-emergency-plumber'
    full_url VARCHAR(500),  -- 'joesplumbing.cringeproof.com/tampa-emergency-plumber'

    -- SEO targeting
    target_city VARCHAR(100),  -- 'Tampa'
    target_keyword VARCHAR(200),  -- 'emergency plumber'
    long_tail_keyword VARCHAR(500),  -- 'emergency plumber in Tampa FL'

    -- Content (auto-generated variations)
    h1_headline VARCHAR(500),
    meta_title VARCHAR(200),
    meta_description VARCHAR(500),
    content_html TEXT,  -- Tutorial + city-specific content

    -- Performance
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    leads INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom Domains (Enterprise tier only)
CREATE TABLE custom_domain (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER REFERENCES professional_profile(id),

    domain VARCHAR(255) UNIQUE,

    -- Verification
    verification_token VARCHAR(64),
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,

    -- SSL
    ssl_certificate_issued BOOLEAN DEFAULT FALSE,
    ssl_certificate_expires TIMESTAMP,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'active', 'failed'
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead tracking (form submissions, phone calls, etc.)
CREATE TABLE lead (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER REFERENCES professional_profile(id),
    tutorial_id INTEGER REFERENCES tutorial(id),
    landing_page_id INTEGER REFERENCES pseo_landing_page(id),

    -- Lead info
    name VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(120),
    message TEXT,

    -- Attribution
    source VARCHAR(100),  -- 'organic', 'direct', 'referral'
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referrer_url VARCHAR(500),

    -- Geolocation
    ip_address VARCHAR(45),
    city VARCHAR(100),
    state VARCHAR(2),
    country VARCHAR(2),

    -- Status
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'contacted', 'qualified', 'converted', 'lost'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- White-label mobile app (Enterprise tier)
CREATE TABLE mobile_app (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER REFERENCES professional_profile(id),

    -- App identity
    app_name VARCHAR(100),
    app_icon_url VARCHAR(500),
    package_name VARCHAR(200),  -- com.joesplumbing.app

    -- App Store
    ios_app_id VARCHAR(50),
    android_app_id VARCHAR(200),

    -- Push notifications
    firebase_config JSON,
    apns_certificate TEXT,

    -- Status
    build_status VARCHAR(20),  -- 'pending', 'building', 'published', 'failed'
    ios_published BOOLEAN DEFAULT FALSE,
    android_published BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Routing Implementation

### Flask Subdomain Router

```python
# subdomain_router.py (enhanced version)

from flask import request, g, render_template, abort
from models import ProfessionalProfile, CustomDomain

def register_subdomain_routes(app):
    """
    Route subdomain/custom domain requests to professional sites
    """

    @app.before_request
    def detect_professional_site():
        """
        Detect if this is a professional's subdomain or custom domain
        Run before every request
        """
        host = request.host.lower()

        # Check if custom domain
        custom_domain = CustomDomain.query.filter_by(
            domain=host,
            verified=True,
            status='active'
        ).first()

        if custom_domain:
            g.professional = custom_domain.professional
            g.is_custom_domain = True
            return

        # Check if subdomain
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.cringeproof.com
            subdomain = parts[0]

            # Skip system subdomains
            if subdomain in ['www', 'api', 'admin', 'app', 'cdn']:
                return

            professional = ProfessionalProfile.query.filter_by(
                subdomain=subdomain,
                subscription_status='active'
            ).first()

            if professional:
                g.professional = professional
                g.is_custom_domain = False
                return

    @app.route('/')
    def professional_home():
        """
        Homepage for professional site
        If g.professional exists, render professional site
        Otherwise, render main CringeProof site
        """
        if not hasattr(g, 'professional'):
            return render_template('home.html')

        # This is a professional's site
        professional = g.professional
        tutorials = professional.tutorials.filter_by(status='published').all()

        return render_template('professional_site.html',
                             professional=professional,
                             tutorials=tutorials)

    @app.route('/tutorials')
    def professional_tutorials():
        """Tutorials page for professional site"""
        if not hasattr(g, 'professional'):
            abort(404)

        professional = g.professional
        tutorials = professional.tutorials.filter_by(status='published').all()

        return render_template('professional_tutorials.html',
                             professional=professional,
                             tutorials=tutorials)

    @app.route('/license-verify')
    def professional_license_verify():
        """License verification page"""
        if not hasattr(g, 'professional'):
            abort(404)

        professional = g.professional

        # Real-time verification via state API
        verification = verify_license_realtime(
            professional.license_number,
            professional.license_state
        )

        return render_template('professional_license.html',
                             professional=professional,
                             verification=verification)

    @app.route('/contact', methods=['GET', 'POST'])
    def professional_contact():
        """Contact form (lead capture)"""
        if not hasattr(g, 'professional'):
            abort(404)

        professional = g.professional

        if request.method == 'POST':
            # Capture lead
            lead = Lead(
                professional_id=professional.id,
                name=request.form.get('name'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                message=request.form.get('message'),
                source='contact_form',
                utm_source=request.args.get('utm_source'),
                utm_medium=request.args.get('utm_medium'),
                utm_campaign=request.args.get('utm_campaign'),
                referrer_url=request.referrer,
                ip_address=request.remote_addr
            )
            db.session.add(lead)
            db.session.commit()

            # Send notification to professional
            send_lead_notification(professional, lead)

            return render_template('contact_success.html',
                                 professional=professional)

        return render_template('professional_contact.html',
                             professional=professional)

    @app.route('/<slug>')
    def professional_landing_page(slug):
        """
        pSEO landing pages
        Example: joesplumbing.cringeproof.com/tampa-emergency-plumber
        """
        if not hasattr(g, 'professional'):
            abort(404)

        professional = g.professional

        # Look up landing page by slug
        landing_page = PSEOLandingPage.query.filter_by(
            professional_id=professional.id,
            slug=slug
        ).first()

        if not landing_page:
            abort(404)

        # Track impression
        landing_page.impressions += 1
        db.session.commit()

        return render_template('professional_landing_page.html',
                             professional=professional,
                             landing_page=landing_page,
                             tutorial=landing_page.tutorial)
```

---

## Branding Customization

### Logo Upload

```python
# routes/professional_settings.py

@app.route('/settings/branding', methods=['GET', 'POST'])
@login_required
def settings_branding():
    """Professional branding settings"""

    professional = g.current_user.professional_profile

    if request.method == 'POST':
        # Logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']

            # Validate
            if not logo_file.filename.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                flash('Logo must be PNG, JPG, or SVG')
                return redirect(url_for('settings_branding'))

            # Upload to S3 or local storage
            logo_url = upload_logo(logo_file, professional.id)
            professional.logo_url = logo_url

        # Color scheme
        professional.primary_color = request.form.get('primary_color')
        professional.accent_color = request.form.get('accent_color')

        # Tagline
        professional.tagline = request.form.get('tagline')

        db.session.commit()
        flash('Branding updated!')

        return redirect(url_for('settings_branding'))

    return render_template('settings_branding.html',
                         professional=professional)
```

### Color Picker UI

```html
<!-- templates/settings_branding.html -->
<form method="POST" enctype="multipart/form-data">
    <!-- Logo upload -->
    <div>
        <label>Logo</label>
        <input type="file" name="logo" accept=".png,.jpg,.jpeg,.svg">

        {% if professional.logo_url %}
            <img src="{{ professional.logo_url }}" alt="Current logo" style="max-width: 200px">
        {% endif %}
    </div>

    <!-- Primary color -->
    <div>
        <label>Primary Color</label>
        <input type="color"
               name="primary_color"
               value="{{ professional.primary_color or '#0066CC' }}">
        <p class="text-sm text-gray-600">Used for headers, buttons, links</p>
    </div>

    <!-- Accent color -->
    <div>
        <label>Accent Color</label>
        <input type="color"
               name="accent_color"
               value="{{ professional.accent_color or '#FF6600' }}">
        <p class="text-sm text-gray-600">Used for CTAs, highlights</p>
    </div>

    <!-- Tagline -->
    <div>
        <label>Tagline</label>
        <input type="text"
               name="tagline"
               value="{{ professional.tagline }}"
               placeholder="Tampa's Most Trusted Plumber"
               maxlength="500">
    </div>

    <button type="submit">Save Changes</button>
</form>

<!-- Live preview -->
<div class="preview" style="
    --primary-color: {{ professional.primary_color or '#0066CC' }};
    --accent-color: {{ professional.accent_color or '#FF6600' }};
">
    <h2 style="color: var(--primary-color)">{{ professional.business_name }}</h2>
    <p>{{ professional.tagline }}</p>
    <button style="background: var(--accent-color)">Get a Quote</button>
</div>
```

---

## Custom Domain Setup (Enterprise)

### Step 1: Professional Initiates

```python
@app.route('/settings/custom-domain', methods=['GET', 'POST'])
@login_required
@enterprise_tier_required
def settings_custom_domain():
    """Enterprise: Set up custom domain"""

    professional = g.current_user.professional_profile

    if request.method == 'POST':
        domain = request.form.get('domain').lower().strip()

        # Validate domain format
        if not is_valid_domain(domain):
            flash('Invalid domain format')
            return redirect(url_for('settings_custom_domain'))

        # Check if already taken
        existing = CustomDomain.query.filter_by(domain=domain).first()
        if existing:
            flash('Domain already in use')
            return redirect(url_for('settings_custom_domain'))

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Create custom domain record
        custom_domain = CustomDomain(
            professional_id=professional.id,
            domain=domain,
            verification_token=verification_token,
            status='pending'
        )
        db.session.add(custom_domain)
        db.session.commit()

        flash(f'Domain {domain} added. Please verify DNS.')
        return redirect(url_for('settings_custom_domain'))

    custom_domains = professional.custom_domains.all()

    return render_template('settings_custom_domain.html',
                         professional=professional,
                         custom_domains=custom_domains)
```

### Step 2: DNS Instructions

```html
<!-- templates/settings_custom_domain.html -->
<div class="dns-instructions">
    <h3>DNS Setup Instructions</h3>

    <p>To connect {{ custom_domain.domain }}, add these DNS records:</p>

    <div class="dns-record">
        <h4>1. CNAME Record (Required)</h4>
        <table>
            <tr>
                <td>Type:</td>
                <td><code>CNAME</code></td>
            </tr>
            <tr>
                <td>Name:</td>
                <td><code>www</code></td>
            </tr>
            <tr>
                <td>Value:</td>
                <td><code>proxy.cringeproof.com</code></td>
            </tr>
            <tr>
                <td>TTL:</td>
                <td><code>3600</code></td>
            </tr>
        </table>
    </div>

    <div class="dns-record">
        <h4>2. TXT Record (Verification)</h4>
        <table>
            <tr>
                <td>Type:</td>
                <td><code>TXT</code></td>
            </tr>
            <tr>
                <td>Name:</td>
                <td><code>@</code></td>
            </tr>
            <tr>
                <td>Value:</td>
                <td><code>cringeproof-verification={{ custom_domain.verification_token }}</code></td>
            </tr>
            <tr>
                <td>TTL:</td>
                <td><code>3600</code></td>
            </tr>
        </table>
    </div>

    <button onclick="verifyDomain('{{ custom_domain.id }}')">
        Verify DNS
    </button>

    <div id="verification-status"></div>
</div>
```

### Step 3: DNS Verification

```python
# tasks/verify_custom_domain.py

import dns.resolver
from models import CustomDomain

def verify_custom_domain_task(custom_domain_id: int):
    """
    Background task to verify custom domain DNS
    """
    custom_domain = CustomDomain.query.get(custom_domain_id)

    if not custom_domain:
        return

    domain = custom_domain.domain
    verification_token = custom_domain.verification_token

    # Check TXT record
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        verified = False

        for rdata in answers:
            for txt in rdata.strings:
                txt_value = txt.decode()
                if txt_value == f'cringeproof-verification={verification_token}':
                    verified = True
                    break

        if verified:
            custom_domain.verified = True
            custom_domain.verified_at = datetime.utcnow()
            custom_domain.status = 'active'

            # Provision SSL certificate
            provision_ssl_certificate(custom_domain)

            db.session.commit()

            # Notify professional
            send_domain_verified_email(custom_domain.professional)

            return True
        else:
            custom_domain.status = 'failed'
            custom_domain.error_message = 'TXT record not found'
            db.session.commit()
            return False

    except Exception as e:
        custom_domain.status = 'failed'
        custom_domain.error_message = str(e)
        db.session.commit()
        return False
```

### Step 4: SSL Certificate

```python
# ssl/provision_certificate.py

from acme import client, messages
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def provision_ssl_certificate(custom_domain: CustomDomain):
    """
    Provision SSL certificate via Let's Encrypt ACME protocol
    """
    domain = custom_domain.domain

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Create CSR (Certificate Signing Request)
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([
            x509.NameAttribute(x509.NameOID.COMMON_NAME, domain)
        ])
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(domain),
            x509.DNSName(f'www.{domain}')
        ]),
        critical=False
    ).sign(private_key, hashes.SHA256())

    # Request certificate from Let's Encrypt
    # (Full ACME implementation omitted for brevity)

    # Save certificate
    custom_domain.ssl_certificate_issued = True
    custom_domain.ssl_certificate_expires = datetime.utcnow() + timedelta(days=90)
    db.session.commit()

    # Configure nginx/caddy to use certificate
    update_web_server_config(domain, private_key, certificate)
```

---

## White-Label Mobile App (Enterprise)

### App Generation

```python
# mobile/generate_app.py

def generate_white_label_app(professional_id: int):
    """
    Generate white-label mobile app for professional
    Uses React Native / Expo for cross-platform build
    """
    professional = ProfessionalProfile.query.get(professional_id)

    # Create app config
    app_config = {
        'name': professional.business_name,
        'slug': professional.subdomain,
        'icon': professional.logo_url,
        'primaryColor': professional.primary_color,
        'accentColor': professional.accent_color,
        'ios': {
            'bundleIdentifier': f'com.cringeproof.{professional.subdomain}'
        },
        'android': {
            'package': f'com.cringeproof.{professional.subdomain}'
        }
    }

    # Generate app.json
    with open(f'mobile-apps/{professional.subdomain}/app.json', 'w') as f:
        json.dump(app_config, f)

    # Build app (Expo)
    subprocess.run([
        'expo', 'build:ios',
        '--config', f'mobile-apps/{professional.subdomain}/app.json'
    ])

    subprocess.run([
        'expo', 'build:android',
        '--config', f'mobile-apps/{professional.subdomain}/app.json'
    ])

    # Submit to App Store / Play Store
    # (Requires professional's developer account credentials)
```

### App Features

```javascript
// mobile-app/App.js

import React from 'react';
import { View, Text, Button } from 'react-native';
import { Audio } from 'expo-av';
import * as Notifications from 'expo-notifications';

export default function App() {
  const professional = useProfessionalData();

  return (
    <View style={{ backgroundColor: professional.primaryColor }}>
      <Text>{professional.businessName}</Text>

      {/* Record tutorial */}
      <Button
        title="Record Tutorial"
        onPress={recordTutorial}
        color={professional.accentColor}
      />

      {/* View leads */}
      <Button
        title="View Leads"
        onPress={viewLeads}
        color={professional.accentColor}
      />

      {/* Push notifications */}
      <NotificationBadge count={professional.unreadLeads} />
    </View>
  );
}

async function recordTutorial() {
  // Record audio
  const { recording } = await Audio.Recording.createAsync(
    Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
  );

  // Upload to server
  const formData = new FormData();
  formData.append('audio', {
    uri: recording.getURI(),
    type: 'audio/m4a',
    name: 'tutorial.m4a'
  });

  await fetch('https://api.cringeproof.com/tutorials', {
    method: 'POST',
    body: formData
  });
}
```

---

## Cost Analysis

### Infrastructure Costs

**Per professional:**
- Subdomain routing: $0 (same server)
- Database storage: ~$0.001/mo (10MB per professional)
- SSL certificate: $0 (Let's Encrypt)
- CDN bandwidth: ~$0.10/mo (assuming 1GB/mo)

**Custom domain (Enterprise):**
- DNS management: $0 (professional's registrar)
- SSL certificate: $0 (Let's Encrypt)
- Additional server config: $0 (automated)

**White-label mobile app (Enterprise):**
- App build: $0 (Expo free tier for first 10 apps/mo)
- App Store / Play Store: $99/year (iOS) + $25 one-time (Android)
- Push notifications: ~$0.01/mo (Firebase free tier)

**Total cost per professional:**
- Free tier: $0/mo
- Pro tier: ~$0.11/mo (99.8% profit margin on $49)
- Enterprise tier: ~$8/mo + $124/year app store fees (96% profit margin on $199)

---

## Security Considerations

### Subdomain Isolation

```python
# Prevent cross-professional data leaks

@app.before_request
def enforce_professional_isolation():
    """
    Ensure requests are scoped to correct professional
    """
    if hasattr(g, 'professional'):
        g.allowed_professional_id = g.professional.id
    else:
        g.allowed_professional_id = None


def get_tutorials_for_professional():
    """
    Always filter by g.allowed_professional_id
    """
    if not g.allowed_professional_id:
        return []

    return Tutorial.query.filter_by(
        professional_id=g.allowed_professional_id,
        status='published'
    ).all()
```

### Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: g.professional.id if hasattr(g, 'professional') else request.remote_addr)

@app.route('/contact', methods=['POST'])
@limiter.limit("5 per hour")  # Prevent lead spam
def professional_contact():
    pass
```

### CORS (API Access)

```python
# For Enterprise tier API access

from flask_cors import CORS

@app.route('/api/tutorials')
@api_key_required
def api_tutorials():
    """
    Enterprise API: Get professional's tutorials
    Requires API key in Authorization header
    """
    api_key = request.headers.get('Authorization')
    professional = ProfessionalProfile.query.filter_by(
        api_key=api_key
    ).first()

    if not professional or professional.tier != 'enterprise':
        abort(403)

    tutorials = professional.tutorials.all()
    return jsonify([t.to_dict() for t in tutorials])
```

---

## Migration Strategy

### Phase 1: Enable Pro Subdomain
**Month 1-3**

```python
# Feature flag: Enable subdomain for all Pro tier users
def enable_pro_subdomain():
    pros = ProfessionalProfile.query.filter_by(tier='professional').all()

    for pro in pros:
        if not pro.subdomain:
            # Auto-generate subdomain from business name
            pro.subdomain = slugify(pro.business_name)

            # Handle conflicts
            if ProfessionalProfile.query.filter_by(subdomain=pro.subdomain).first():
                pro.subdomain = f"{pro.subdomain}-{pro.id}"

    db.session.commit()
```

### Phase 2: Enable Enterprise Custom Domains
**Month 4-6**

```python
# Feature flag: Enable custom domain for Enterprise users
def enable_enterprise_custom_domains():
    enterprises = ProfessionalProfile.query.filter_by(tier='enterprise').all()

    for ent in enterprises:
        # Notify them custom domains are available
        send_custom_domain_available_email(ent)
```

### Phase 3: White-Label Mobile Apps
**Month 7-12**

```python
# On-demand: Generate mobile app when Enterprise user requests
def request_mobile_app(professional_id: int):
    professional = ProfessionalProfile.query.get(professional_id)

    if professional.tier != 'enterprise':
        raise ValueError('Mobile apps only available for Enterprise tier')

    # Check if already exists
    if professional.mobile_app:
        return professional.mobile_app

    # Create mobile app record
    app = MobileApp(
        professional_id=professional.id,
        app_name=professional.business_name,
        app_icon_url=professional.logo_url,
        package_name=f'com.cringeproof.{professional.subdomain}',
        build_status='pending'
    )
    db.session.add(app)
    db.session.commit()

    # Queue build job
    queue_mobile_app_build.delay(app.id)

    return app
```

---

## User Onboarding Flow

### Pro Tier Onboarding

```
Step 1: Sign up for Pro ($49/mo)
├── Stripe payment collection
└── Create professional profile

Step 2: Choose subdomain
├── Input: "joesplumbing"
├── Check availability
└── Reserve: joesplumbing.cringeproof.com

Step 3: Upload logo & branding
├── Logo upload
├── Color picker (primary/accent)
└── Tagline input

Step 4: Verify license
├── Input license number
├── State API verification
└── Badge appears on profile

Step 5: Record first tutorial
├── Voice recording (mobile or web)
├── AI generates content
└── Auto-publish to subdomain

Step 6: View site
├── Visit joesplumbing.cringeproof.com
└── Share link with customers
```

### Enterprise Tier Onboarding

```
Step 1-5: Same as Pro tier

Step 6: Optional: Set up custom domain
├── Input domain: joesplumbing.com
├── Follow DNS instructions
├── Verify TXT record
└── SSL auto-provisioned

Step 7: Optional: Request mobile app
├── Submit request
├── App built (24-48 hours)
├── Submit to App Store / Play Store
└── Download from stores in 7-14 days
```

---

## Analytics & Reporting

### Professional Dashboard

```python
@app.route('/dashboard')
@login_required
def professional_dashboard():
    """Analytics dashboard for professional"""

    professional = g.current_user.professional_profile

    # Last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)

    # Metrics
    metrics = {
        'total_views': sum(t.view_count for t in professional.tutorials),
        'total_leads': Lead.query.filter_by(professional_id=professional.id).count(),
        'leads_this_month': Lead.query.filter(
            Lead.professional_id == professional.id,
            Lead.created_at >= start_date
        ).count(),
        'top_tutorial': professional.tutorials.order_by(Tutorial.lead_count.desc()).first(),
        'conversion_rate': calculate_conversion_rate(professional.id)
    }

    # Top landing pages
    top_pages = PSEOLandingPage.query.filter_by(
        professional_id=professional.id
    ).order_by(PSEOLandingPage.leads.desc()).limit(10).all()

    # Lead sources
    lead_sources = db.session.query(
        Lead.source,
        func.count(Lead.id)
    ).filter(
        Lead.professional_id == professional.id,
        Lead.created_at >= start_date
    ).group_by(Lead.source).all()

    return render_template('dashboard.html',
                         metrics=metrics,
                         top_pages=top_pages,
                         lead_sources=lead_sources)
```

### Subdomain Analytics

```python
# Track subdomain performance across all professionals

def subdomain_analytics_report():
    """
    Monthly report: Which subdomains are performing best?
    """
    professionals = ProfessionalProfile.query.filter_by(
        tier='professional'
    ).all()

    report = []

    for pro in professionals:
        leads_this_month = Lead.query.filter(
            Lead.professional_id == pro.id,
            Lead.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()

        report.append({
            'subdomain': pro.subdomain,
            'business_name': pro.business_name,
            'leads': leads_this_month,
            'tutorials': pro.tutorials.count(),
            'conversion_rate': calculate_conversion_rate(pro.id)
        })

    # Sort by leads (best performers first)
    report.sort(key=lambda x: x['leads'], reverse=True)

    return report
```

---

## API Documentation (Enterprise)

### Authentication

```bash
# Enterprise API uses API key authentication

curl -H "Authorization: Bearer ent_abc123def456" \
     https://api.cringeproof.com/tutorials
```

### Endpoints

```python
# GET /api/tutorials
# List all tutorials for professional

@app.route('/api/tutorials')
@api_key_required
def api_list_tutorials():
    professional = g.api_professional
    tutorials = professional.tutorials.all()

    return jsonify({
        'tutorials': [
            {
                'id': t.id,
                'title': t.title,
                'audio_url': t.audio_url,
                'published_at': t.published_at.isoformat(),
                'view_count': t.view_count,
                'lead_count': t.lead_count
            }
            for t in tutorials
        ]
    })


# POST /api/tutorials
# Create new tutorial via API

@app.route('/api/tutorials', methods=['POST'])
@api_key_required
def api_create_tutorial():
    professional = g.api_professional

    # Audio file upload
    audio_file = request.files.get('audio')

    if not audio_file:
        return jsonify({'error': 'No audio file'}), 400

    # Upload audio
    audio_url = upload_audio(audio_file, professional.id)

    # Transcribe
    transcript = transcribe_audio(audio_url)

    # Generate HTML
    html_content = generate_html_from_transcript(transcript)

    # Create tutorial
    tutorial = Tutorial(
        professional_id=professional.id,
        audio_url=audio_url,
        transcript=transcript,
        html_content=html_content,
        status='published'
    )
    db.session.add(tutorial)
    db.session.commit()

    # Generate pSEO pages
    generate_pseo_landing_pages(tutorial.id)

    return jsonify(tutorial.to_dict()), 201


# GET /api/leads
# List leads for professional

@app.route('/api/leads')
@api_key_required
def api_list_leads():
    professional = g.api_professional

    # Optional filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    query = Lead.query.filter_by(professional_id=professional.id)

    if start_date:
        query = query.filter(Lead.created_at >= start_date)
    if end_date:
        query = query.filter(Lead.created_at <= end_date)
    if status:
        query = query.filter_by(status=status)

    leads = query.all()

    return jsonify({
        'leads': [
            {
                'id': lead.id,
                'name': lead.name,
                'phone': lead.phone,
                'email': lead.email,
                'message': lead.message,
                'source': lead.source,
                'status': lead.status,
                'created_at': lead.created_at.isoformat()
            }
            for lead in leads
        ]
    })


# PATCH /api/leads/<lead_id>
# Update lead status (CRM integration)

@app.route('/api/leads/<int:lead_id>', methods=['PATCH'])
@api_key_required
def api_update_lead(lead_id):
    professional = g.api_professional

    lead = Lead.query.filter_by(
        id=lead_id,
        professional_id=professional.id
    ).first()

    if not lead:
        return jsonify({'error': 'Lead not found'}), 404

    # Update status
    status = request.json.get('status')
    if status:
        lead.status = status

    db.session.commit()

    return jsonify(lead.to_dict())
```

---

## Comparison: Subdomain vs Custom Domain

| Feature | Pro Subdomain | Enterprise Custom Domain |
|---------|--------------|--------------------------|
| **URL** | joesplumbing.cringeproof.com | joesplumbing.com |
| **Cost** | $49/mo | $199/mo |
| **Setup time** | Instant | 24-48 hours (DNS propagation) |
| **SEO impact** | Good (subdomain has authority) | Better (root domain ownership) |
| **Branding** | Shared brand (CringeProof visible) | Full white-label |
| **SSL** | Auto (wildcard cert) | Auto (Let's Encrypt per domain) |
| **Mobile app** | No | Yes |
| **API access** | No | Yes |
| **Custom domain** | No | Yes |

---

## Future Enhancements

### Multi-Location Support
**For franchises with 10+ locations**

```python
# One professional, multiple subdomains
class ProfessionalLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional_profile.id'))

    # Location info
    subdomain = db.Column(db.String(50), unique=True)  # joesplumbing-tampa
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))

    # Localized content
    phone = db.Column(db.String(20))
    address = db.Column(db.String(500))
```

### White-Label Email
**Enterprise: Send lead notifications from custom domain**

```python
# Use SendGrid/Mailgun with custom domain
def send_lead_notification_whitelabel(professional, lead):
    """
    Send email from: leads@joesplumbing.com (not noreply@cringeproof.com)
    """
    from_email = f'leads@{professional.custom_domain.domain}'
    to_email = professional.email

    send_email(
        from_email=from_email,
        to_email=to_email,
        subject=f'New lead from {lead.name}',
        body=f'{lead.message}\n\nContact: {lead.phone}'
    )
```

### A/B Testing Landing Pages
**Pro/Enterprise: Test different headlines/CTAs**

```python
class PSEOVariant(db.Model):
    """
    A/B test different versions of landing pages
    """
    id = db.Column(db.Integer, primary_key=True)
    landing_page_id = db.Column(db.Integer, db.ForeignKey('pseo_landing_page.id'))

    variant = db.Column(db.String(1))  # 'A' or 'B'
    h1_headline = db.Column(db.String(500))
    cta_text = db.Column(db.String(100))

    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    leads = db.Column(db.Integer, default=0)
```

---

## Conclusion

**White-label architecture enables:**

1. **Professional credibility** - Each pro has their own branded site
2. **SEO ownership** - Pros rank on THEIR domains, not a marketplace
3. **Lead exclusivity** - Leads go direct to pro, not shared/sold
4. **Scalability** - One codebase serves unlimited professionals
5. **Profitability** - 96-99% profit margins (low infra cost per professional)

**Implementation status:**
- ✅ Subdomain routing (already exists in `subdomain_router.py`)
- ✅ Database schema designed
- ⏳ Custom domain verification (needs implementation)
- ⏳ White-label mobile app generator (needs implementation)
- ⏳ API endpoints (partial implementation)

**Next steps:**
1. Implement custom domain verification flow
2. Build branding settings UI (logo upload, color picker)
3. Create pSEO landing page generator (see `GENERATIVE_SITE_SYSTEM.md`)
4. Set up mobile app build pipeline (Expo + App Store automation)

---

**Created:** 2026-01-09
**By:** Claude Code
**See also:**
- `PLATFORM_INTEGRATION_STRATEGY.md` - How Soulfra + CringeProof connect
- `GENERATIVE_SITE_SYSTEM.md` - Voice → auto-generate full website
- `PRICING_STRATEGY.md` - Free/$49/$199 pricing tiers
- `subdomain_router.py` - Existing subdomain routing implementation
