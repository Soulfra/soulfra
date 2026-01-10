# QR Systems Architecture Map

## Overview

This codebase contains **29 QR-related files** implementing 15+ distinct QR code systems. This document maps all QR systems, their purposes, routes, and how they integrate.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SOULFRA QR ECOSYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ Business QR     │  │  Vanity QR       │  │ Gallery   │ │
│  │ (Invoices/POs)  │  │  (URL Shortener) │  │ QR System │ │
│  └────────┬────────┘  └────────┬─────────┘  └─────┬─────┘ │
│           │                    │                   │        │
│           └────────────────────┼───────────────────┘        │
│                                │                            │
│                    ┌───────────▼──────────┐                 │
│                    │  unified_content     │                 │
│                    │  vanity_qr_codes     │                 │
│                    │  (SQLite Database)   │                 │
│                    └──────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Core QR Systems (Active)

### 1. **Business QR System** ⭐ NEW

**Purpose**: Embed full JSON data in QR codes for offline-first business documents

**Files**:
- `business_qr.py` - QR generator with full JSON embedding
- `business_routes.py` - Flask routes
- `business_schemas.py` - JSON schemas (InvoiceSchema, ReceiptSchema, PurchaseOrderSchema)
- `payment_integrations.py` - Stripe/Square/QuickBooks connectors
- `templates/business_dashboard.html` - Dashboard UI
- `templates/business_view.html` - Document viewer

**Routes**:
```
GET  /business                         - Dashboard
GET  /business/view/<id>               - View document with QR
POST /api/business/invoice             - Create invoice
POST /api/business/receipt             - Create receipt
POST /api/business/purchase-order      - Create PO
GET  /api/business/documents           - List documents
GET  /api/business/stats               - Statistics
GET  /api/business/qr/<id>             - Download QR PNG
POST /api/business/stripe/webhook      - Stripe webhook
```

**Database Tables**:
- `unified_content` (documents)
- `vanity_qr_codes` (QR images)

**Key Features**:
- ✅ Offline-first: All data embedded in QR code
- ✅ Bloomberg-style HMAC signatures
- ✅ Automatic QR version selection (V1-V40)
- ✅ Compression for large documents
- ✅ SHA-256 content hashing
- ✅ No internet required to verify

**Example Use Cases**:
- Restaurant receipts
- Contractor invoices
- Event tickets
- Product compliance docs

---

### 2. **Vanity QR System** ⭐ EXISTING

**Purpose**: Branded URL shortening with styled QR codes

**Files**:
- `vanity_qr.py` - Branded QR generator with styling

**Routes** (via `image_admin_routes.py`):
```
GET  /qr/create                        - Public QR builder
POST /api/qr/create                    - Create vanity QR
GET  /api/qr/<short_code>              - Get QR metadata
GET  /v/<short_code>                   - Redirect to full URL
```

**Database Tables**:
- `vanity_qr_codes` (shared with business system)
- `qr_chat_transcripts` (chat logs from QR scans)

**Supported Brands**:
1. **cringeproof**: Minimal style, dark gray + red
2. **soulfra**: Rounded style, purple + blue + green
3. **howtocookathome**: Circles style, orange + yellow + green

**QR Styles**:
- **minimal**: Square modules (clean, corporate)
- **rounded**: Rounded corners (modern, friendly)
- **circles**: Circular dots (playful, creative)

**Key Features**:
- ✅ Custom short URLs (cringeproof.com/qr/xxx)
- ✅ Brand colors and styling
- ✅ Logo embedding support
- ✅ Click analytics
- ✅ Chat transcript logging

---

### 3. **Gallery QR System**

**Purpose**: QR codes that open rich interactive galleries

**Files**:
- `qr_gallery_system.py` - Gallery QR generator

**Routes** (via `gallery_routes.py`):
```
GET  /galleries                        - All galleries
GET  /gallery/<slug>                   - View gallery
GET  /dm/scan                          - DM via QR scan
GET  /qr/track/<qr_id>                 - QR analytics
```

**Key Features**:
- ✅ Image carousel from post
- ✅ Soul ratings from neural networks
- ✅ AI agent chat interface
- ✅ In-person DM QR code
- ✅ Share buttons

---

### 4. **Advanced QR Generator**

**Purpose**: Modern QR codes with advanced styling (2025/2026 features)

**Files**:
- `advanced_qr.py` - Advanced QR styling engine

**Key Features**:
- ✅ Animated QR codes (GIF with pulsing effects)
- ✅ Gradient overlays (dual-color linear gradients)
- ✅ Logo embedding (center placement)
- ✅ Custom shapes (rounded corners, circular dots)

**Use Cases**:
- Marketing campaigns (attention-grabbing)
- Brand-heavy materials
- Event promotions

---

### 5. **DM via QR System**

**Purpose**: In-person direct messaging with security verification

**Files**:
- `dm_via_qr.py` - Secure DM QR generator

**Security Features**:
- ✅ QR codes expire after 5 minutes
- ✅ Cryptographic signature prevents tampering
- ✅ One-time use tokens
- ✅ Optional GPS proximity verification
- ✅ Screenshot detection

**Workflow**:
```
1. User A generates DM QR → Expires in 5 min
2. User B scans QR in person → Token verified
3. DM channel created → High trust score
4. Messages encrypted → No online DMs allowed
```

---

## 🔧 Utility QR Systems

### 6. **QR Authentication** (`qr_auth.py`)
- Scan QR to log in (passwordless auth)
- Time-limited session tokens
- Device fingerprinting

### 7. **QR Analytics** (`qr_analytics.py`)
- Track QR scan metrics
- Geographic heatmaps
- Device type analysis
- Time-series engagement

### 8. **QR Auto-Generate** (`qr_auto_generate.py`)
- Event-driven QR creation
- Batch QR generation
- Template-based QR

### 9. **QR Voice Integration** (`qr_voice_integration.py`)
- Scan QR → Start voice call
- Voice-to-QR encoding
- Audio QR codes

### 10. **QR Learning Session** (`qr_learning_session.py`)
- Educational QR codes
- Progress tracking
- Quiz QR codes

### 11. **QR Image Overlay** (`qr_image_overlay.py`)
- Overlay QR on product images
- Watermark QR codes
- Dynamic QR positioning

### 12. **QR to ASCII** (`qr_to_ascii.py`)
- Terminal-friendly QR codes
- ASCII art QR
- Plain-text QR transmission

### 13. **QR User Profile** (`qr_user_profile.py`)
- Digital business cards
- Profile QR codes
- Social media QR links

### 14. **QR Faucet** (`qr_faucet.py`)
- Rate-limited QR requests
- Anti-spam QR generation
- Quota management

### 15. **Widget QR Bridge** (`widget_qr_bridge.py`)
- Embed QR in widgets
- Cross-platform QR sharing
- Widget-to-web bridge

---

## 🗄️ Database Schema

### `unified_content` (Business Documents)

```sql
CREATE TABLE unified_content (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,                   -- JSON document
    content_type TEXT,              -- 'business_invoice', 'business_receipt', etc.
    content_hash TEXT,              -- SHA-256 hash
    brand_slug TEXT,
    metadata TEXT,                  -- JSON metadata (signature, qr_version, etc.)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### `vanity_qr_codes` (QR Images & Metadata)

```sql
CREATE TABLE vanity_qr_codes (
    id INTEGER PRIMARY KEY,
    short_code TEXT UNIQUE,         -- e.g., 'biz-123', 'pMD2vH'
    brand_slug TEXT,                -- 'cringeproof', 'soulfra', etc.
    full_url TEXT,                  -- Original URL
    vanity_url TEXT,                -- Short URL
    qr_image BLOB,                  -- PNG image data
    style TEXT,                     -- 'minimal', 'rounded', 'circles'
    created_at TIMESTAMP,
    clicks INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMP,
    metadata TEXT                   -- JSON metadata
);
```

### `qr_chat_transcripts` (Chat Logs)

```sql
CREATE TABLE qr_chat_transcripts (
    id INTEGER PRIMARY KEY,
    short_code TEXT,                -- Links to vanity_qr_codes
    user_ip TEXT,
    device_type TEXT,
    sender TEXT,
    message TEXT,
    created_at TIMESTAMP
);
```

---

## 🔀 Integration Points

### 1. **Business QR + Vanity QR**

Business system **reuses** vanity QR infrastructure:
- Uses same `vanity_qr_codes` table
- Different short codes: `biz-<id>` vs `<hash>`
- Shares QR image storage

### 2. **Gallery QR + Vanity QR**

Gallery system generates vanity QR codes:
- QR points to `/gallery/<slug>`
- Uses branded styling
- Tracks clicks via `qr_analytics.py`

### 3. **Payment Webhooks + Business QR**

Auto-generate receipts on payment:
```
Stripe Payment → Webhook → Create Receipt → Generate QR → Email Customer
```

Supported integrations:
- Stripe (`STRIPE_ENABLED=true`)
- Square (`SQUARE_ENABLED=true`)
- QuickBooks (`QUICKBOOKS_ENABLED=true`)

---

## 🎯 When to Use Which System

| Use Case | System | Why |
|----------|--------|-----|
| Invoice with full data embedded | **Business QR** | Offline-first, cryptographic verification |
| Shorten long URL | **Vanity QR** | Branded, trackable, styled |
| Product gallery | **Gallery QR** | Rich media, interactive |
| Marketing campaign | **Advanced QR** | Animated, gradients, attention-grabbing |
| In-person verification | **DM QR** | Security, time-limited, GPS proximity |
| Login/auth | **QR Auth** | Passwordless, session tokens |
| Analytics tracking | **QR Analytics** | Heatmaps, device analysis |
| Business card | **QR User Profile** | Social links, contact info |
| Educational content | **QR Learning Session** | Progress tracking, quizzes |

---

## 🚀 Quick Start Guide

### Create a Business Invoice QR

```bash
# 1. Initialize database
python3 init_business_db.py

# 2. Start server
python3 app.py

# 3. Open dashboard
open http://localhost:5001/business

# 4. Create invoice via UI or API
curl -X POST http://localhost:5001/api/business/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "INV-2025-001",
    "from_entity": {
      "name": "Soulfra LLC",
      "email": "billing@soulfra.com"
    },
    "to_entity": {
      "name": "Customer Name",
      "email": "customer@example.com"
    },
    "items": [{
      "description": "Consulting Services",
      "quantity": 10,
      "unit_price": 100.00
    }],
    "due_date": "2026-01-28"
  }'
```

### Create a Vanity QR Code

```python
from vanity_qr import create_and_save_vanity_qr

# Generate QR
qr_id = create_and_save_vanity_qr(
    full_url='https://soulfra.com/blog/post',
    brand_slug='soulfra',
    custom_code='blog-post-1'  # Optional
)

# QR now available at: https://soulfra.com/v/blog-post-1
```

### Create a Gallery QR

```bash
python3 qr_gallery_system.py --post 29
# Generates QR → https://soulfra.com/gallery/post-29
```

---

## 📊 System Comparison

| Feature | Business QR | Vanity QR | Gallery QR |
|---------|-------------|-----------|------------|
| **Data Storage** | Embedded in QR | Database only | Database only |
| **Offline Verify** | ✅ Yes | ❌ No | ❌ No |
| **Capacity** | Up to 4,296 bytes | Unlimited (URL only) | Unlimited |
| **Signatures** | ✅ HMAC | ❌ No | ❌ No |
| **Branding** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Analytics** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | Invoices, receipts | URL shortening | Image galleries |

---

## 🔐 Security Considerations

### Business QR (Offline-First)

**Threat Model**: Tampered QR codes, fake invoices

**Mitigations**:
1. HMAC signature verification (Bloomberg-style)
2. SHA-256 content hashing
3. Timestamp validation
4. Issuer verification

**Verification Steps**:
```python
1. Scan QR → Extract JSON
2. Verify HMAC signature with secret key
3. Recompute SHA-256 hash
4. Compare hashes
5. Check timestamp freshness
6. ✅ Valid if all checks pass
```

### Vanity QR (URL Shortening)

**Threat Model**: Malicious URLs, phishing

**Mitigations**:
1. URL validation before shortening
2. Blocklist for known malicious domains
3. Click-through warnings for external sites
4. Rate limiting on QR creation

### DM QR (In-Person Verification)

**Threat Model**: Screenshot sharing, token replay

**Mitigations**:
1. 5-minute expiry window
2. One-time use tokens
3. GPS proximity verification (optional)
4. Timestamp verification (detect screenshots)
5. Cryptographic signatures

---

## 🛠️ Development Roadmap

### Phase 1: Consolidation (Current)

- ✅ Audit all QR systems
- ✅ Document architecture
- ⏳ Create unified factory (`qr_unified.py`)
- ⏳ Event-based automation (`qr_events.py`)

### Phase 2: Enhancement

- [ ] Migrate to PostgreSQL (multi-tenant support)
- [ ] Add QR code versioning (track changes)
- [ ] Implement QR expiration (auto-delete old codes)
- [ ] Add QR code templates (pre-configured styles)
- [ ] Blockchain verification (tamper-proof QR)

### Phase 3: Distribution

- [ ] Extract to OSS library
- [ ] Create npm package for frontend
- [ ] Publish API documentation (OpenAPI spec)
- [ ] Build hosted SaaS platform

---

## 📖 References

- **Business QR README**: `BUSINESS_QR_README.md`
- **QR Technology Guide**: `QR_CODE_GUIDE.md`
- **Vanity QR Docs**: `vanity_qr.py` (docstrings)
- **Gallery System**: `qr_gallery_system.py` (docstrings)

---

## 🎯 Summary

**Total QR Systems**: 15 active + 14 archived = **29 files**

**Database Tables**: 3 (unified_content, vanity_qr_codes, qr_chat_transcripts)

**Flask Routes**: 20+ QR-related endpoints

**Key Insight**: Business QR is **unique** because it embeds full data in the QR code itself (offline-first), while other systems use QR as a pointer to database-stored content.

---

**Built with Soulfra** 🚀
