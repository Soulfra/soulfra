# Soulfra Database Tables - Active Systems

## ✅ Idea Submission System (Active)

**Core Tables:**
- `idea_submissions` - Main idea records with tracking IDs
- `idea_feedback` - Feedback on submitted ideas
- `idea_status_history` - Status change timeline

**Supporting Tables:**
- `device_multipliers` - Device rewards tracking
- `device_activity` - Device scan history
- `device_scans` - Individual scan records
- `qr_faucets` - QR code payloads (signed JSON)
- `qr_faucet_scans` - Scan tracking for faucets

## 🔄 QR Faucet System (Active)

**Tables:**
- `qr_faucets` - Generated QR payloads with HMAC signatures
- `qr_faucet_scans` - Scan history with device fingerprints

**Payload Types:**
1. `blog` - Generate blog posts
2. `auth` - Authentication tokens
3. `post` - Pre-written content
4. `plot_action` - Game actions
5. `question_response` - Question responses
6. `idea_submission` - Idea submissions ⭐ NEW

## 🧠 Neural Networks (Active)

**Tables:**
- `neural_networks` - Model weights and metadata
- `ml_models` - ML model configurations
- `predictions` - Prediction results
- `feedback` - User corrections for training

**Models:**
1. calriven_technical_classifier
2. deathtodata_privacy_classifier
3. theauditor_validation_classifier
4. soulfra_judge

## 🏢 Brands & Products (Active)

**Tables:**
- `brands` - Brand metadata
- `brand_territory` - Territory scores
- `user_brand_loyalty` - Soul tokens & steering power
- `contribution_scores` - AI validation scores
- `products` - Merch, APIs, services
- `brand_licenses` - Licensing info
- `brand_downloads` - Download tracking

## 📊 Key Integrations

### Idea Submission Flow:
1. **QR Generation**: `/qr/idea/privacy` → generates QR with signed faucet payload
2. **Scan**: User scans → `/qr/faucet/<payload>` → verifies HMAC
3. **Transform**: Payload → redirects to `/submit-idea?theme=privacy&domain=ocean-dreams`
4. **Submit**: Form submission → creates `idea_submissions` record
5. **Track**: User visits `/track/IDEA-ABC123` → shows status

### Security Features:
- ✅ HMAC signatures prevent tampering
- ✅ Timestamp expiration (24 hours default)
- ✅ Device fingerprinting for tracking
- ✅ Nonces prevent replay attacks

## 🗄️ Database File
**Location**: `soulfra.db` (SQLite)

**Table Count**: 62+ tables
**Python Files**: 177 files (32 create tables)

## 📝 Notes

- Tables are created on-demand by their respective Python modules
- Use `python3 <module>.py --init` to initialize module-specific tables
- QR Faucet tables auto-create when first payload is generated
- Device multiplier tables auto-create on first device pairing
