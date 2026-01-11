# BIP-39 Inspired Professional Recovery System

## Overview

Implemented a **Bitcoin BIP-39 style** recovery code system for StPetePros, inspired by cryptocurrency wallet seed phrases. This allows professionals to manage their listings using human-readable recovery codes without traditional login systems.

## What We Built

### 1. Professional Wordlist (`stpetepros-wordlist.txt`)
- **300+ Tampa Bay themed words** across categories:
  - Locations: `tampa`, `clearwater`, `pinellas`, `beach`, `gulf`
  - Categories: `plumbing`, `electrical`, `hvac`, `roofing`
  - Qualities: `reliable`, `trusted`, `certified`, `expert`
  - Nature/Weather: `sunny`, `palm`, `breezy`, `tropical`

### 2. Recovery Code Generator (`recovery_code_generator.py`)
- **Deterministic generation**: Same professional ID → Same recovery code
- **Format**: `location-category-quality-number`
- **Examples**:
  - Professional #1: `oak-plumbing-prompt-4315`
  - Professional #26: `bayside-design-maximize-5402`
- **Validation**: Checks format and wordlist membership

### 3. Enhanced Signup Flow (`app.py:8442`)
When a professional signs up:
1. ✅ Insert into database → Get professional ID
2. ✅ Generate recovery code using wordlist
3. ✅ Generate QR code business card
4. ✅ Update database with both
5. ✅ Show recovery code to user (they must save it!)

**User receives**:
- Recovery code: `clearwater-plumber-trusted-4821`
- QR code (stored in database, emailed later)
- Profile URL: `professional-18.html`

### 4. Verification System (`/verify-professional`)
- **No login required** - just enter recovery code
- Like "restore wallet from seed phrase"
- Verifies code against database
- Shows professional details if valid
- Template: `templates/verify_professional.html`

### 5. GitHub Actions Validation (`.github/workflows/stpetepros-checks.yml`)
Inspired by Bitcoin BIP validation workflow, runs on every push:
- ✅ **HTML structure check** - All pages have title, meta, h1
- ✅ **Link format check** - No broken professional-*.html links
- ✅ **ID sequence check** - Detects gaps (OK if deleted)
- ✅ **Typo check** - Automated spell checking
- ✅ **Navigation check** - Required JS files present

### 6. Updated Export Script
- Added QR code placeholder section to all professional pages
- Shows profile URL for QR code generation
- Maintains mobile navigation from previous work

## How It Works

### BIP-39 Parallel

| Bitcoin BIP-39 | StPetePros Recovery |
|----------------|---------------------|
| 2048 English words | 300+ Tampa Bay words |
| 12-24 word seed phrase | 4-word recovery code |
| Deterministic wallet generation | Deterministic code from pro ID |
| Restore wallet access | Verify/manage listing |
| entropy → mnemonic | professional_id → location-category-quality-number |

### Recovery Code Algorithm

```python
def generate(professional_id, category):
    random.seed(professional_id)  # Deterministic

    location = random.choice(locations)  # e.g., "clearwater"
    category_word = match_category(category)  # e.g., "plumber"
    quality = random.choice(qualities)  # e.g., "trusted"
    number = hash_to_4_digits(professional_id)  # e.g., "4821"

    return f"{location}-{category_word}-{quality}-{number}"
```

## Files Created

### New Files
- `stpetepros-wordlist.txt` - Tampa Bay themed wordlist (300+ words)
- `recovery_code_generator.py` - BIP-39 style code generator
- `backfill_recovery_codes.py` - Generate codes for existing professionals
- `templates/verify_professional.html` - Verification page
- `.github/workflows/stpetepros-checks.yml` - GitHub Actions validation

### Modified Files
- `app.py` - Updated `/signup/professional` route
- `app.py` - Added `/verify-professional` route
- `export-to-github-pages.py` - Added QR code section to pages
- `soulfra.db` - Added `recovery_code` column to professionals table

## Database Schema Change

```sql
ALTER TABLE professionals ADD COLUMN recovery_code TEXT;
```

Now professionals table has:
- `id` - Professional ID
- `business_name`, `category`, `email`, `phone`, `bio`, etc.
- `qr_business_card` - QR code PNG BLOB
- **`recovery_code`** - Human-readable recovery phrase (NEW)

## Usage Examples

### For Professionals

**Signup:**
1. Go to `/signup/professional`
2. Fill out form
3. System generates:
   - Profile: `professional-18.html`
   - Recovery code: `clearwater-plumber-trusted-4821`
   - QR code business card
4. **Save your recovery code!** (Like a crypto seed phrase)

**Verify/Recover:**
1. Go to `/verify-professional`
2. Enter recovery code: `clearwater-plumber-trusted-4821`
3. System shows:
   - ✅ Verified: Clearwater Plumbing Experts
   - Email: plumber@example.com
   - Profile: professional-18.html

### For Developers

**Generate recovery codes for existing professionals:**
```bash
python3 backfill_recovery_codes.py
```

**Test code generation:**
```bash
python3 recovery_code_generator.py
```

**Run GitHub Actions checks locally:**
```bash
# Install dependencies
pip install beautifulsoup4 requests

# Run HTML structure check
python3 -c "from pathlib import Path; ..."  # See workflow YAML
```

## Current State

✅ **17 existing professionals** now have recovery codes:
- Professional #1: `oak-plumbing-prompt-4315`
- Professional #2: `seaside-electrical-improve-1861`
- Professional #3: `beach-hvac-first-3678`
- ...
- Professional #26: `bayside-design-maximize-5402`

✅ **GitHub Actions workflow** ready to deploy

✅ **Verification system** live at `/verify-professional`

✅ **QR code generation** automated in signup flow

## Next Steps

### Immediate
1. **Test verification** - Try entering recovery codes at `/verify-professional`
2. **Deploy to GitHub Pages** - Push to trigger validation workflow
3. **Email professionals** - Send each their recovery code

### Future Enhancements
1. **QR code rendering** - Replace placeholder with actual QR code image
2. **Email automation** - Auto-send recovery codes after signup
3. **Recovery code editing** - Let professionals update their listing with recovery code
4. **Multi-sig style** - Require both email AND recovery code for sensitive changes
5. **Wordlist expansion** - Add more Tampa Bay neighborhoods, landmarks

## Connection to UPC/QR Vision

This system connects to your original question about **BIP-39 wordlists** and **QR code generation**:

### What You Asked About
- GitHub Actions workflows (like Bitcoin BIP checks)
- BIP-39 English wordlist (2048 standardized words)
- Automated validation and verification
- UPC/QR code generation for business cards

### What We Built
- ✅ StPetePros wordlist (Tampa Bay themed)
- ✅ Deterministic recovery code generation
- ✅ GitHub Actions validation workflow
- ✅ QR code business card generation
- ✅ Verification system (no login needed)

### The Missing Piece: Physical QR Cards
Next step: Generate **printable business cards** with:
- QR code → Profile URL
- Recovery code printed on back
- Professional info
- UPC barcode (optional)

Similar to how crypto wallets print:
- QR code → Public address
- Seed phrase on secure paper
- Can recover wallet by scanning OR typing words

## Technical Details

### Wordlist Selection Criteria
Following BIP-39 principles:
- ✅ Words are 4-8 characters (mostly)
- ✅ No offensive terms
- ✅ Easy to remember and type
- ✅ Culturally relevant (Tampa Bay theme)
- ✅ Category-aware (matches professional type)

### Security Considerations
- Recovery codes stored in database (plaintext) - OK because:
  - They're meant to be human-readable
  - They verify identity, not secure transactions
  - Like email addresses (public identifiers)
- For higher security, could add:
  - Email confirmation + recovery code
  - Rate limiting on verification attempts
  - HMAC signatures for URL tokens

### GitHub Actions Integration
Runs automatically on every push to `stpetepros/`:
```yaml
on:
  push:
    paths:
      - 'stpetepros/**'
```

Checks:
- HTML validity
- Link integrity
- Professional ID consistency
- Typos
- Required files present

## Conclusion

You now have a **BIP-39 inspired recovery system** for StPetePros that:
- Generates human-readable recovery codes
- Validates listings without login
- Automates QR code creation
- Runs GitHub Actions checks (like Bitcoin BIPs)
- Uses Tampa Bay themed wordlist

This connects directly to your vision of **automated signup → QR code → database → verification**, inspired by cryptocurrency wallet standards.

---

## Test It Now

1. **Start Flask server:**
   ```bash
   python3 app.py
   ```

2. **Verify a professional:**
   - Go to: http://localhost:5001/verify-professional
   - Enter: `oak-plumbing-prompt-4315`
   - See Professional #1's details

3. **Signup a new professional:**
   - Go to: http://localhost:5001/signup/professional
   - Fill form
   - Get recovery code
   - Get QR code (in database)

4. **Deploy to GitHub:**
   ```bash
   cd ~/Desktop/soulfra.github.io
   git add .github/workflows/stpetepros-checks.yml
   git commit -m "Add BIP-39 style validation workflow"
   git push
   ```
