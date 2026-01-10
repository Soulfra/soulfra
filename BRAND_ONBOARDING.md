# Brand Onboarding System - Complete Guide

## Overview

The Soulfra QR system supports **multi-brand QR code generation** with custom styling, colors, and templates for each brand. This allows you to generate branded QR codes for multiple companies/products from a single codebase.

---

## Current Brands

### 1. **Cringeproof** (cringeproof.com)

**Domain**: `cringeproof.com`
**Style**: Minimal (clean, corporate)
**Colors**:
- Primary: `#2D3748` (Dark Gray)
- Secondary: `#E53E3E` (Red)
- Accent: `#EDF2F7` (Light Gray)

**Use Cases**: Professional invoices, corporate receipts, B2B documents

**Example URLs**:
- Vanity: `https://cringeproof.com/v/abc123`
- QR Builder: `https://cringeproof.com/qr/create`

---

### 2. **Soulfra** (soulfra.com)

**Domain**: `soulfra.com`
**Style**: Rounded (modern, friendly)
**Colors**:
- Primary: `#8B5CF6` (Purple)
- Secondary: `#3B82F6` (Blue)
- Accent: `#10B981` (Green)

**Use Cases**: Tech products, SaaS invoices, modern brands

**Example URLs**:
- Vanity: `https://soulfra.com/v/abc123`
- Business Dashboard: `https://soulfra.com/business`
- Gallery: `https://soulfra.com/gallery/post-1`

---

### 3. **How To Cook At Home** (howtocookathome.com)

**Domain**: `howtocookathome.com`
**Style**: Circles (fun, friendly)
**Colors**:
- Primary: `#F97316` (Orange)
- Secondary: `#EAB308` (Yellow)
- Accent: `#84CC16` (Lime Green)

**Use Cases**: Food & beverage, cooking classes, restaurant receipts

**Example URLs**:
- Vanity: `https://howtocookathome.com/v/abc123`
- Recipe Gallery: `https://howtocookathome.com/gallery/recipe-1`

---

## Adding a New Brand

### Step 1: Update `vanity_qr.py`

Edit `vanity_qr.py` and add your brand to the `BRAND_DOMAINS` dictionary:

```python
BRAND_DOMAINS = {
    'cringeproof': { ... },
    'soulfra': { ... },
    'howtocookathome': { ... },

    # Add your new brand
    'yourbrand': {
        'domain': 'yourbrand.com',
        'colors': {
            'primary': '#FF5733',    # Main brand color
            'secondary': '#C70039',  # Accent color
            'accent': '#FFC300'      # Highlight color
        },
        'style': 'rounded'  # 'minimal', 'rounded', or 'circles'
    }
}
```

### Step 2: Choose QR Style

Select one of three styles:

1. **`minimal`**: Square modules (clean, corporate look)
   - Best for: Professional services, law firms, consultants
   - QR Module Shape: Square
   - Example: Cringeproof

2. **`rounded`**: Rounded corners (modern, friendly)
   - Best for: Tech companies, SaaS products, modern brands
   - QR Module Shape: Rounded rectangles
   - Example: Soulfra

3. **`circles`**: Circular dots (playful, creative)
   - Best for: Food & beverage, creative agencies, lifestyle brands
   - QR Module Shape: Circles
   - Example: How To Cook At Home

### Step 3: Color Selection Guide

**Primary Color**:
- Main brand color (appears in QR modules)
- Should have high contrast with white background
- Recommended: Dark colors (#000000 to #666666) for best scanning

**Secondary Color**:
- Accent color (used for gradients, borders)
- Can be brighter than primary
- Complements primary color

**Accent Color**:
- Highlight color (used for labels, call-to-actions)
- High contrast with primary/secondary
- Often a complementary color

**Color Contrast Tips**:
- Test QR codes with different lighting conditions
- Ensure primary color has ≥4.5:1 contrast ratio with white
- Avoid red on green or blue on yellow (color-blind accessibility)

### Step 4: Register Brand in System

No database changes needed! The brand configuration in `vanity_qr.py` is automatically picked up by:

- `business_qr.py` - Business invoice/receipt generation
- `qr_unified.py` - Unified QR factory
- `image_admin_routes.py` - Image generation
- `advanced_qr.py` - Advanced styled QR codes

### Step 5: Test Brand QR Generation

```python
from qr_unified import QRFactory

# Generate branded QR code
qr_bytes, metadata = QRFactory.create(
    'vanity',
    url='https://yourbrand.com/product',
    brand='yourbrand'  # Your brand slug
)

# Save to file for testing
with open('test_yourbrand_qr.png', 'wb') as f:
    f.write(qr_bytes)

# Test scanning with phone camera
print("Scan test_yourbrand_qr.png with your phone!")
```

---

## Brand Use Cases

### **When to Use Multi-Brand QR System**

✅ **Good Use Cases**:
- **Agency managing multiple clients**: Generate branded QR codes for each client
- **Multi-brand portfolio company**: Different QR styles for each product line
- **White-label SaaS**: Offer branded QR generation to customers
- **Franchise business**: Consistent QR styling across locations

❌ **Not Recommended For**:
- Single-brand business (just use one brand config)
- Non-commercial personal projects (use 'simple' QR type)

---

## Brand Onboarding Workflow

### Automated Onboarding Process

```
1. Brand fills out onboarding form
   ↓
2. System creates brand config:
   - Brand slug (e.g., 'acme-corp')
   - Domain (e.g., 'acmecorp.com')
   - Colors (primary, secondary, accent)
   - Style preference (minimal, rounded, circles)
   ↓
3. Brand config added to BRAND_DOMAINS
   ↓
4. Brand receives:
   - QR Builder URL: https://acmecorp.com/qr/create
   - API Key for programmatic access
   - Sample QR codes in brand colors
   ↓
5. Brand can start generating QR codes immediately
```

### Onboarding Form Fields

**Required**:
- Brand Name
- Domain (must be owned by brand)
- Primary Color (hex code)
- Contact Email

**Optional**:
- Secondary Color (defaults to primary)
- Accent Color (defaults to complementary)
- QR Style (defaults to 'rounded')
- Logo File (for logo embedding)

---

## Brand Templates

### Pre-Configured Templates

Speed up onboarding with pre-designed color schemes:

#### **Template 1: Corporate Blue**
```python
{
    'primary': '#1E3A8A',    # Navy Blue
    'secondary': '#3B82F6',  # Sky Blue
    'accent': '#60A5FA',     # Light Blue
    'style': 'minimal'
}
```

#### **Template 2: Startup Purple**
```python
{
    'primary': '#7C3AED',    # Purple
    'secondary': '#A78BFA',  # Light Purple
    'accent': '#DDD6FE',     # Lavender
    'style': 'rounded'
}
```

#### **Template 3: Eco Green**
```python
{
    'primary': '#047857',    # Forest Green
    'secondary': '#10B981',  # Emerald
    'accent': '#6EE7B7',     # Mint
    'style': 'circles'
}
```

#### **Template 4: Bold Red**
```python
{
    'primary': '#B91C1C',    # Dark Red
    'secondary': '#EF4444',  # Red
    'accent': '#FCA5A5',     # Pink
    'style': 'minimal'
}
```

#### **Template 5: Sunset Orange**
```python
{
    'primary': '#C2410C',    # Dark Orange
    'secondary': '#F97316',  # Orange
    'accent': '#FDBA74',     # Light Orange
    'style': 'rounded'
}
```

---

## Brand Management

### Updating Brand Configuration

**Change Colors**:
```python
# Edit vanity_qr.py
BRAND_DOMAINS['yourbrand']['colors']['primary'] = '#NEW_COLOR'
```

**Change Style**:
```python
BRAND_DOMAINS['yourbrand']['style'] = 'minimal'  # or 'rounded', 'circles'
```

**No server restart needed** - changes take effect immediately on next QR generation.

### Deprecating a Brand

To remove a brand from the system:

1. Comment out brand config in `vanity_qr.py`:
```python
# 'oldbrand': {
#     'domain': 'oldbrand.com',
#     ...
# }
```

2. Existing QR codes will still work (data in database)
3. New QR codes cannot be generated for this brand

### Migrating Brand Data

To transfer QR codes from one brand to another:

```sql
UPDATE vanity_qr_codes
SET brand_slug = 'newbrand'
WHERE brand_slug = 'oldbrand';
```

---

## Brand Analytics

### Track Brand Usage

**QR Codes Generated per Brand**:
```sql
SELECT brand_slug, COUNT(*) as qr_count
FROM vanity_qr_codes
GROUP BY brand_slug
ORDER BY qr_count DESC;
```

**QR Code Clicks per Brand**:
```sql
SELECT brand_slug, SUM(clicks) as total_clicks
FROM vanity_qr_codes
GROUP BY brand_slug
ORDER BY total_clicks DESC;
```

**Top Performing QR Codes**:
```sql
SELECT short_code, brand_slug, clicks, vanity_url
FROM vanity_qr_codes
WHERE brand_slug = 'yourbrand'
ORDER BY clicks DESC
LIMIT 10;
```

---

## API Integration

### Create Branded QR via API

**Endpoint**: `POST /api/qr/create`

**Request**:
```json
{
  "url": "https://yourbrand.com/product",
  "brand": "yourbrand",
  "style": "rounded",
  "custom_code": "summer-sale"
}
```

**Response**:
```json
{
  "qr_id": 123,
  "short_code": "summer-sale",
  "vanity_url": "https://yourbrand.com/v/summer-sale",
  "qr_image_url": "https://yourbrand.com/api/qr/summer-sale"
}
```

### Generate QR Programmatically

```python
from qr_unified import QRFactory

# Invoice QR
qr, meta = QRFactory.create(
    'invoice',
    data=invoice_data,
    brand='yourbrand'
)

# Vanity QR
qr, meta = QRFactory.create(
    'vanity',
    url='https://yourbrand.com/promo',
    brand='yourbrand',
    custom_code='spring2025'
)
```

---

## Brand Compliance

### Trademark Guidelines

**Using Brand Logos in QR Codes**:
- Obtain written permission from brand owner
- Logo must be provided in high-resolution PNG (transparent background)
- Logo size: ≤20% of QR code area (to maintain scannability)
- Use error correction level H (30% damage tolerance)

**Brand Color Usage**:
- Use exact hex codes from brand guidelines
- Do not modify brand colors for QR codes
- Maintain sufficient contrast (primary color ≥4.5:1 ratio with white)

### Legal Requirements

**Terms of Service**:
- Each brand must accept QR system TOS
- Responsibility for QR code content
- Compliance with local laws (GDPR, CCPA, etc.)

**Data Ownership**:
- Brand owns QR code content
- Soulfra owns QR generation infrastructure
- Analytics data shared with brand

---

## Troubleshooting

### "Brand not found" Error

**Problem**: `ValueError: Unknown brand: yourbrand`

**Solution**:
1. Check spelling of brand slug (case-sensitive)
2. Ensure brand exists in `vanity_qr.py` → `BRAND_DOMAINS`
3. Restart server if using environment variables

### QR Code Not Scanning

**Problem**: QR code won't scan on phone

**Solutions**:
1. **Low Contrast**: Use darker primary color (try #000000)
2. **Logo Too Large**: Reduce logo size to <15% of QR area
3. **Low Resolution**: Increase QR size parameter (try 1024px)
4. **Heavy Styling**: Switch to 'minimal' style temporarily

### Colors Look Different on Print

**Problem**: QR code colors appear different when printed

**Solutions**:
1. Use CMYK color profile for print design
2. Test print samples before bulk printing
3. Increase contrast between primary and background colors
4. Use RGB colors only for digital QR codes

---

## Advanced Features

### Logo Embedding

Add brand logo to center of QR code:

```python
from advanced_qr import AdvancedQRGenerator

qr = AdvancedQRGenerator(
    data='https://yourbrand.com',
    style='rounded',
    primary_color='#8B5CF6',
    logo_path='/path/to/logo.png',  # PNG with transparent background
    size=1024
)

qr_bytes = qr.generate()
```

### Animated QR Codes

Generate GIF QR codes with pulsing effects:

```python
from advanced_qr import AdvancedQRGenerator

qr = AdvancedQRGenerator(
    data='https://yourbrand.com/promo',
    style='rounded',
    primary_color='#8B5CF6',
    secondary_color='#3B82F6',
    size=512
)

animated_qr = qr.generate_animated(duration=3)  # 3-second loop
```

---

## Summary

**Total Brands**: 3 (cringeproof, soulfra, howtocookathome)

**Supported Styles**: 3 (minimal, rounded, circles)

**QR Types per Brand**: 8 (invoice, receipt, purchase order, vanity, gallery, advanced, dm, simple)

**Configuration File**: `vanity_qr.py` → `BRAND_DOMAINS`

**No Database Changes Needed**: Brand config is code-based

**API Integration**: Full REST API + Python SDK

---

## Next Steps

1. ✅ Review existing brands (cringeproof, soulfra, howtocookathome)
2. ⏳ Add your brand to `BRAND_DOMAINS`
3. ⏳ Test QR generation with `QRFactory.create()`
4. ⏳ Deploy to production
5. ⏳ Monitor analytics via SQL queries

---

**Questions?** Check `QR_SYSTEMS_MAP.md` for architecture overview or `QR_CODE_GUIDE.md` for QR technology fundamentals.

**Built with Soulfra** 🚀
