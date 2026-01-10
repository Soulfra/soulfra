# Soulfra System Architecture Map

**Generated:** 2025-12-23
**Purpose:** Complete map of all systems, connections, and integrations

---

## 🎯 Overview

You have **177 Python files** and **62 database tables** creating an extensive ecosystem.
Many systems exist but are **NOT YET CONNECTED**.

---

## 📊 System Inventory

### 1. Brand Competition System (NEW - ISOLATED)

**Files:**
- `contribution_validator.py` - Real-time on-brand scoring
- `neural_proxy.py` - ENSEMBLE classifier (runs all 3 networks, picks best)
- `brand_territory.py` - Territory tracking
- `migrate_brand_evolution.py` - Database migration

**Database Tables:**
- `brand_territory` - Territory scores, rankings
- `user_brand_loyalty` - Soul tokens, steering power
- `contribution_scores` - AI validation scores

**Status:** ✅ Working
**Connected To:** Neural networks (classification only)
**NOT Connected To:** QR codes, products, domain pairing, device tracking

---

###  2. QR Code System (EXISTING - 43 FILES!)

**Key Files:**
- `qr_faucet.py` - Transform JSON → Content (blog, auth, post)
- `brand_qr_generator.py` - Brand-specific QR codes with tracking
- `qr_captcha.py` - QR-based CAPTCHA
- `qr_auth.py` - Authentication via QR codes
- `qr_to_ascii.py` - ASCII QR rendering
- `soul_qr.py`, `soul_qr_signed.py` - Soul profile QR codes
- ...and 37 more QR-related files!

**Database Tables:**
- `qr_faucets` (1 record) - QR payloads with HMAC signatures
- `qr_scans` - Scan tracking
- `qr_auth_codes` - Auth tokens
- `scan_lineage` - Scan genealogy

**Status:** ✅ Working
**What It Does:**
- Generates QR codes with JSON payloads
- Tracks scans by IP, user agent, device fingerprint
- Routes dynamically (redirects with tracking)
- Works offline (stdlib only)

**Connected To:** Brands (via brand_qr_generator.py)
**NOT Connected To:** Neural networks, Ollama template generation, device ID multipliers

---

### 3. Domain Context System (EXISTING)

**Files:**
- `templatewright.py` - Template versioning, domain rotation
- `domain_rotation_state` tracking

**Database Tables:**
- `domain_contexts` (12 records) - Rotating questions/themes by domain
- `domain_rotation_state` - Current rotation state
- `template_versions` - Ship class versioning (dinghy→schooner→frigate→galleon)
- `template_tests` - Template test results

**Status:** ✅ Working
**What It Does:**
- Rotates questions/themes for each domain (ocean-dreams, cringeproof, soulfra)
- Manages template versions with "ship classes"
- Tests templates

**Connected To:** Templates
**NOT Connected To:** Device IDs, QR codes, brand competition

---

### 4. Workflow Engine (EXISTING)

**Files:**
- `workflow_engine.py` - Execute queued workflows
- `newsroom_scheduler.py` - Automated operations

**Database Tables:**
- `workflow_executions` (4 records) - Queued workflows

**Status:** ✅ Working
**Workflow Types:** auto_post_generation, content_moderation, user_lifecycle

**Connected To:** Content generation
**NOT Connected To:** Brands, QR codes, domains

---

### 5. Affiliate/Product System (EXISTING)

**Files:**
- Brand merch/API infrastructure

**Database Tables:**
- `products` (5 records) - Merch, APIs, services
  - Brand ID
  - Type (merch, api, email, service)
  - UPC/SKU barcodes
  - Ad tier (Google Ads, Facebook, Organic)
  - Stock quantity
- `brand_licenses` - Licensing (cc0, cc-by, proprietary, etc.)
- `brand_downloads` - Download tracking

**Status:** ✅ Working
**Products:**
1. Soulfra T-Shirt (merch, brand_id=1)
2. Soulfra Sticker (merch, brand_id=1)
3. Privacy Manifesto Poster (merch, brand_id=1)
4. Privacy Score API (api, brand_id=1)
5. Encryption Recommender API (api, brand_id=1)

**Connected To:** Brands
**NOT Connected To:** Brand territory/competition, soul tokens, QR rewards

---

### 6. Ollama AI System (EXISTING - 32 FILES!)

**Key Files:**
- `brand_ai_persona_generator.py` - Create AI personas from brands
- `brand_ai_orchestrator.py` - Orchestrate brand AI comments
- `ollama_auto_commenter.py` - Auto-generate comments
- `ollama_discussion.py` - Multi-brand discussions
- `neural_proxy.py` - Routes AI requests to Ollama or neural networks
- ...and 27 more Ollama files!

**What It Does:**
- Generates AI user accounts for each brand
- AI comments in brand's voice (personality + tone)
- Provides instant engagement for new creators
- System prompts from brand personality/tone

**Status:** ✅ Working
**Ollama Host:** http://localhost:11434

**Connected To:** Brands (generates personas), neural networks (via neural_proxy.py)
**NOT Connected To:** Template generation from neural networks, QR code generation

---

### 7. Neural Networks (EXISTING)

**Files:**
- `neural_network.py` - Pure Python neural networks
- `neural_proxy.py` - Classifier proxy
- `database_viewer.py` - View network stats

**Database Tables:**
- `neural_networks` (7 models)
  1. calriven_technical_classifier
  2. deathtodata_privacy_classifier
  3. theauditor_validation_classifier
  4. soulfra_judge
  5. even_odd_classifier
  6. color_classifier
  7. color_to_personality
- `ml_models` - ML model metadata
- `predictions` - Prediction results
- `feedback` - User corrections for training

**Status:** ✅ Working
**What It Does:**
- ENSEMBLE classification (runs all 3 brand classifiers, picks highest confidence)
- Technical, privacy, validation classification
- Training dashboard at `/dashboard`

**Connected To:** Contribution validator, Ollama (via neural_proxy.py)
**NOT Connected To:** Ollama template generation, QR code generation, real content training

---

### 8. Brands (5 TOTAL)

**Database:** `brands` table

1. **ocean-dreams** (ID: 1) - Ocean Dreams
2. **testbrand-auto** (ID: 3) - TestBrand Auto
3. **calriven** (ID: 4) - CalRiven 💻 (Technical)
4. **privacy-guard** (ID: 5) - Privacy Guard 🔒 (Privacy)
5. **the-auditor** (ID: 6) - The Auditor ✅ (Validation)

**Brand Features:**
- Personality + tone
- Neural network mapping
- Territory scores
- QR code generation
- AI personas
- Products
- Licenses

**Routes:**
- `/brands` - Marketplace
- `/brand/<slug>` - Individual brand page
- `/brand-arena` - Competition view

---

## ❌ Missing Connections

### Your Vision (from Message 2):
> "i thought we already had this working with the ollama model and getting ollama to build out our neural network from templates like images and qr codes and whatever else based on domains? thats what we had been trying to do almost like pair their domain with device id or something else where we can tie multipliers and all other random things together"

### Reality:
**THIS IS NOT YET BUILT!**

Here's what needs connecting:

1. **Ollama → Template Generation**
   - ❌ Ollama does NOT generate templates from neural networks
   - ❌ No QR code generation from Ollama
   - ❌ No image → template pipeline

2. **Domain + Device ID Pairing**
   - ❌ No device_id column in any table
   - ❌ No multiplier system
   - ❌ domain_contexts not paired with devices

3. **Brand Competition → Affiliate Rewards**
   - ❌ Soul tokens don't award product discounts
   - ❌ Territory scores don't affect affiliate commissions
   - ❌ QR scans don't earn soul tokens

4. **QR Codes → Neural Networks**
   - ❌ QR codes don't trigger neural network training
   - ❌ Scans don't generate templates

---

## 🔧 Integration Opportunities

### Connect: Brand Territory → Products
**Implementation:**
```python
# When user buys product, award territory points
product_purchase_points = price * 0.01  # $1 = 1 point
UPDATE brand_territory
SET territory_score = territory_score + product_purchase_points
WHERE brand_id = ?
```

### Connect: QR Scans → Soul Tokens
**Implementation:**
```python
# Add device_id tracking to qr_scans
ALTER TABLE qr_scans ADD COLUMN device_id TEXT;
ALTER TABLE qr_scans ADD COLUMN multiplier REAL DEFAULT 1.0;

# Award tokens on scan
tokens_earned = base_tokens * multiplier
UPDATE user_brand_loyalty
SET soul_tokens = soul_tokens + tokens_earned
WHERE user_id = ? AND brand_id = ?
```

### Connect: Domain → Device Pairing
**Implementation:**
```python
# Create device_multipliers table
CREATE TABLE device_multipliers (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    domain_slug TEXT,
    multiplier REAL DEFAULT 1.0,
    paired_at TIMESTAMP,
    FOREIGN KEY (domain_slug) REFERENCES domain_contexts(domain_slug)
);

# When device scans QR for domain → apply multiplier
```

### Connect: Ollama → Template Generation
**Implementation:**
```python
# In brand_ai_persona_generator.py
def generate_template_from_brand(brand_slug):
    """Use Ollama to generate HTML template from brand personality"""
    persona = get_brand_ai_persona_config(brand_slug)

    prompt = f"""
    Generate an HTML template for {persona['name']} brand.
    Personality: {persona['personality']}
    Tone: {persona['tone']}
    Colors: {persona['colors']}

    Create a landing page template that embodies this brand.
    """

    response = requests.post(f"{OLLAMA_HOST}/api/generate", json={
        'model': 'llama3',
        'prompt': prompt
    })

    return response.json()['response']
```

---

## 📁 File Organization

**Total:** 177 Python files

**QR System:** 43 files
**Ollama System:** 32 files
**Core App:** app.py (5780 lines!)
**Database:** 62 tables

---

## 🚨 Immediate Issues

### Dashboard/Menu Inconsistency
**From logs:** `/brand/ocean-dreams` was throwing 500 errors but **already fixed**

Last successful request:
```
127.0.0.1 - - [23/Dec/2025 09:11:36] "GET /brand/ocean-dreams HTTP/1.1" 200 -
```

### Missing:
- Device ID tracking
- Multiplier system
- Ollama → template generation
- QR → neural network training

---

## 🎯 Next Steps

1. **Create device tracking system**
2. **Connect brand territory → products → soul tokens**
3. **Implement multipliers**
4. **Build Ollama → template generation pipeline**
5. **Connect QR scans → neural network feedback**

---

## 💡 Your Existing Strengths

You have incredible infrastructure:
- ✅ 7 neural networks trained and working
- ✅ ENSEMBLE classification system
- ✅ 43 QR code files (comprehensive tracking)
- ✅ Ollama integration (32 files!)
- ✅ Workflow engine
- ✅ Template versioning with ship classes
- ✅ Affiliate/product system

**The pieces exist - they just need connecting!**
