# Lineage Routing: Vanity Addresses for QR Codes

## The Vision

**Same URL → Different Destinations Based on WHO Scans It**

Just like Bitcoin vanity addresses or pre-DNS routing, we've built a system where the SAME short URL redirects to DIFFERENT places based on the scanner's lineage.

## How It Works

### 1. Lineage Tracking (lineage_system.py)

Every QR scan creates a "commit" in a git-like tree:

```
Root Scan (Alice - Privacy topic)
  ├─ Child 1 (Bob) - Inherited privacy lineage
  │   ├─ Grandchild 1 (Charlie)
  │   └─ Grandchild 2 (Diana)
  └─ Child 2 (Eve) - Inherited privacy lineage
      └─ Grandchild 3 (Frank)
```

**Key Features:**
- SHA256 hashing: `hash = SHA256(parent_hash + scan_data)`
- UPC encoding: `RRRGGGHHHHHH` (Root + Generation + Hash)
- Unforgeable chain (like blockchain/git)
- Metadata propagates down the tree

### 2. Device Fingerprinting (qr_captcha.py)

Instead of cookies or sessions, we use device fingerprints:
- IP address
- User agent
- Device type
- Scan history

**Trust Score (0-100):**
- Previous scans: +5 each (max +30)
- Human-like UA: +10
- Bot UA: -20
- Known device type: +10

### 3. Lineage Router (lineage_router.py)

This is where the magic happens!

**Same Short URL Routes Differently:**

```python
URL: /s/ABC123

Device 1 (Privacy lineage):
  IP: 10.0.0.10
  Lineage: 6d70c7621427
  Metadata: {"topic": "privacy"}
  → Routes to: privacy.soulfra.com

Device 2 (Tech lineage):
  IP: 10.0.0.20
  Lineage: abc123def456
  Metadata: {"topic": "tech"}
  → Routes to: tech.soulfra.com

Device 3 (No lineage):
  IP: 192.168.1.1
  Lineage: None
  → Routes to: soulfra.com (default)
```

## The Vanity Address Concept

### What Are Vanity Addresses?

In cryptocurrency, a vanity address is a custom address like `1BitcoinEaterAddressDontSend` that looks unique but functions like any other address.

In pre-DNS internet, routing was based on identity/context rather than fixed URLs.

### Our Implementation

We've adapted this concept for QR codes:
- **Traditional routing:** URL → Fixed destination
- **Lineage routing:** URL + Device context → Dynamic destination

**This creates VIRAL ROUTING:**
1. Alice creates privacy lineage and shares QR
2. Bob scans → Gets privacy.soulfra.com
3. Bob shares SAME URL
4. Charlie scans → ALSO gets privacy.soulfra.com (inherited!)
5. Random person scans → Gets default

## Security Model

**Current Implementation: HMAC-SHA256**

### What We Use:
- **HMAC-SHA256** for payload signing (tamper prevention)
- **SHA256** for lineage hashing (unforgeable chains)
- **Device fingerprinting** instead of sessions

### What We DON'T Use:
- ❌ **bcrypt** - Not needed (no passwords)
- ❌ **Encryption** - Payloads are signed but readable
- ❌ **gRPC/RPC** - HTTP-based
- ❌ **Cookies/Sessions** - Device fingerprints instead

**This is "ROUGH level crypto":**
- ✅ Good for integrity (can't tamper)
- ✅ Good for authenticity (HMAC signatures)
- ❌ NOT for secrecy (payloads readable)

If you need encryption, add AES-256 on top. But for QR routing, HMAC is sufficient.

## Use Cases

### 1. Viral Marketing with Tracking
```
Brand creates root lineage → Influencer shares QR →
Followers scan → All route to influencer's custom subdomain
Track "who recruited who" through lineage tree
```

### 2. Personalized Content Delivery
```
Same QR code on poster → Different content based on scanner:
- Tech enthusiast → tech blog
- Privacy advocate → privacy blog
- First-time visitor → general landing page
```

### 3. Access Control Without Login
```
VIP gets QR with special lineage → Scans → VIP content
Regular user scans same QR → Regular content
NO login required - device fingerprint + lineage = auth
```

### 4. Knowledge Graphs from Scans
```
QR Scan → Creates node in graph
Edges = referral relationships
Analyze: Who shares most? Which topics spread fastest?
```

## Files Created

1. **lineage_system.py** (483 lines)
   - Git-like commit tracking for QR scans
   - UPC encoding
   - Tree visualization

2. **qr_captcha.py** (496 lines)
   - Device fingerprint CAPTCHA
   - Trust score calculation
   - Session management

3. **lineage_router.py** (520 lines)
   - Context-aware URL routing
   - Faucet assignment from lineage
   - Short URL management

4. **prove_lineage_routing.py** (150 lines)
   - End-to-end demonstration
   - Shows same URL → different destinations

## Testing

### Run Full Demo:
```bash
python3 prove_lineage_routing.py --demo
```

This will:
1. Create lineages with different topics
2. Create short URL
3. Route with 3 different devices
4. Show same URL → 3 different destinations

### Manual Testing:

```bash
# Create lineage
python3 lineage_system.py --create-root --qr-code 1

# Create short URL
python3 lineage_router.py --create --url "https://soulfra.com/blog/test" --lineage <HASH>

# Test routing
python3 lineage_router.py --route <SHORT_ID> --ip 10.0.0.1 --user-agent "Mozilla/5.0..."

# Show all routes
python3 lineage_router.py --show-routes <SHORT_ID>
```

## Database Schema

### scan_lineage
```sql
CREATE TABLE scan_lineage (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER NOT NULL,
    lineage_hash TEXT UNIQUE NOT NULL,
    parent_lineage_hash TEXT,
    generation INTEGER DEFAULT 0,
    root_scan_id INTEGER,
    upc_code TEXT,
    metadata TEXT  -- {"topic": "privacy", "brand": "ocean-dreams"}
)
```

### lineage_short_urls
```sql
CREATE TABLE lineage_short_urls (
    id INTEGER PRIMARY KEY,
    short_id TEXT UNIQUE NOT NULL,
    target_url TEXT NOT NULL,
    lineage_hash TEXT,
    clicks INTEGER DEFAULT 0,
    expires_at TIMESTAMP
)
```

## Next Steps

### Already Built (From Previous Session):
- ✅ QR Faucet (JSON → Content transformation)
- ✅ Neural Network Blog Generation (7 trained models)
- ✅ Template Generator (Universal templating)
- ✅ Complete proof system

### To Build Next:
1. **captcha_with_questions.py** - Interactive CAPTCHA with Q&A
2. **faucet_assignment.py** - Smart subdomain router
3. **user_confirmation_flow.py** - "Convert to blog?" approval
4. **knowledge_graph.py** - Visualize scan relationships

### Integration with Flask:
Add route to `app.py`:
```python
@app.route('/s/<short_id>')
def lineage_short_url(short_id):
    device_fp = {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'device_type': get_device_type(request)
    }

    result = route_short_url(short_id, device_fp)
    return redirect(result['redirect_url'])
```

## Philosophy

**Everything is traceable, everything is contextual**

- Traditional web: Stateless, context-free
- Our system: Stateful through lineage, context-aware through fingerprinting

**No external dependencies needed**
- Python stdlib only (hashlib, sqlite3, json, secrets)
- Zero npm packages
- Zero pip packages (except Flask)

**First principles approach (CS50 style)**
- Understand HMAC before using it
- Build lineage tracking from scratch
- No "magic" - pure Python + SQLite

## Credits

Built with:
- Python 3 standard library
- SQLite database
- Zero external AI (our own neural networks!)
- Zero npm packages
- First principles thinking

---

**TL;DR:** We built vanity addresses for QR codes. Same URL routes differently based on your lineage. Like Bitcoin addresses + Git commits + DNS-less routing, all in Python stdlib.
