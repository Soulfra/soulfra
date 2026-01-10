# Brands - Multi-Tenant Platform Guide

This Flask app serves **5 different brands** from ONE codebase running on port 5001.

## Quick Access

### Local Development (localhost:5001)

```bash
# Switch brands with ?brand= parameter:
https://localhost:5001?brand=soulfra       # Default - Authentic Community
https://localhost:5001?brand=stpetepros    # St. Petersburg Professionals
https://localhost:5001?brand=cringeproof   # Voice Ideas Platform
https://localhost:5001?brand=calriven      # Real Estate Intelligence
https://localhost:5001?brand=deathtodata   # Privacy & Crypto Truth
```

**Default:** Accessing `https://localhost:5001` without `?brand=` shows **StPetePros** by default.

### Production Domains

| Brand | Domain | Purpose |
|-------|--------|---------|
| **Soulfra** | soulfra.com | Main platform - authentic community |
| **StPetePros** | stpetepros.com | Local professional directory (Tampa Bay) |
| **CringeProof** | cringeproof.com | Voice recording with gamification |
| **CalRiven** | calriven.com | Real estate market analysis |
| **DeathToData** | deathtodata.com | Privacy/crypto skepticism |

---

## Brand Details

### 🟣 Soulfra
**Tagline:** Authentic Community
**Domain:** soulfra.com
**Color:** #667eea (Purple)
**Personality:** Warm, authentic, community-focused, thoughtful

**Features:**
- User profiles ("souls")
- Post feed with AI reasoning
- Voice memos
- Debate/tribunal system
- Leaderboard & achievements

**Navigation:**
- Posts, Souls, Games, Reasoning, ML Dashboard, About, Feedback

---

### 🔵 StPetePros
**Tagline:** St. Petersburg Professional Directory
**Domain:** stpetepros.com
**Color:** #0EA5E9 (Sky Blue)
**Personality:** Professional, local-focused, community-driven, verified

**Geographic Restriction:**
- ✅ Only accessible in **Tampa Bay area** (727/813 area codes)
- ✅ Within **30 miles** of St. Petersburg, FL
- ✅ **Florida license/IP verification** (planned)
- ⚙️ Override for dev: `?geo_override=true` on localhost

**Features:**
- Professional directory (plumbers, electricians, lawyers, etc.)
- QR-verified business cards
- Customer reviews
- Category browsing
- Search by profession

**Navigation:**
- Browse, Categories, About, Login, Join as Pro

**Template:** `templates/stpetepros/base.html` (clean, no Soulfra clutter)

---

### 🎀 CringeProof
**Tagline:** Voice Ideas, No Cringe
**Domain:** cringeproof.com
**Color:** #ff006e (Hot Pink)
**Personality:** Playful, creative, gamified, encouraging

**Features:**
- QR-sized voice interface (400x400px)
- Real-time interest detection
- Adaptive game prompts
- Visual rewards (stars, fireworks, badges)
- Achievement system
- 5-minute voice recording limit

**Key Files:**
- `voice-archive/qr-idea.html` - Main interface
- `voice-archive/js/voice-analyzer.js` - Interest detection
- `voice-archive/js/game-prompts.js` - Adaptive prompts
- `voice-archive/js/animations.js` - Visual effects

---

### 🏡 CalRiven
**Tagline:** Real Estate Intelligence
**Domain:** calriven.com
**Color:** #2C5F2D (Forest Green)
**Personality:** Professional, data-driven, market-focused

**Features:**
- Real estate predictions
- MLS data analysis
- Market trend debates
- Property insights

---

### ⚫ DeathToData
**Tagline:** Privacy & Crypto Truth
**Domain:** deathtodata.com
**Color:** #1A1A1A (Dark Gray)
**Personality:** Skeptical, analytical, privacy-focused, anti-surveillance

**Features:**
- Crypto market analysis
- Privacy breach tracking
- Data leak documentation
- Anti-surveillance advocacy

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│     Flask App (ONE codebase on port 5001)       │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────┐  ┌──────────┐  ┌───────────┐         │
│  │Soulfra│  │StPetePros│  │CringeProof│ ...    │
│  └───┬───┘  └─────┬────┘  └─────┬─────┘         │
│      │            │             │               │
│      └────────────┴─────────────┘               │
│                   │                             │
│         ┌─────────▼──────────┐                  │
│         │  Shared Database   │                  │
│         │  (soulfra.db)      │                  │
│         └────────────────────┘                  │
└─────────────────────────────────────────────────┘
```

### How It Works

1. **Request arrives** → `@app.before_request`
2. **Brand detection** → Checks `?brand=` param OR Host header
3. **Sets `g.active_brand`** → Available in all routes/templates
4. **Geo-check** (StPetePros only) → Blocks if outside Tampa Bay
5. **Route renders** → Uses brand-specific templates if they exist

### Brand Detection Code

```python
# brand_router.py
def detect_brand_from_request(request):
    # 1. Check ?brand= parameter
    brand_param = request.args.get('brand')
    if brand_param in BRANDS:
        return brand_param

    # 2. Check Host header
    host = request.headers.get('Host')
    if 'stpetepros.com' in host:
        return 'stpetepros'

    # 3. Default for localhost
    if 'localhost' in host:
        return 'stpetepros'

    # 4. Fallback
    return 'soulfra'
```

---

## File Structure

```
soulfra-simple/
├── app.py                        # Main Flask app
├── brand_router.py               # Brand detection & configs
├── templates/
│   ├── base.html                 # Soulfra base template
│   ├── index.html                # Soulfra homepage
│   ├── stpetepros/
│   │   ├── base.html            # StPetePros clean template
│   │   └── homepage.html        # StPetePros directory
│   └── ...
└── voice-archive/
    ├── qr-idea.html             # CringeProof voice interface
    └── js/
        ├── voice-analyzer.js
        ├── game-prompts.js
        └── animations.js
```

---

## Development Workflow

### 1. Run Flask Server

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

Server runs at: `https://localhost:5001` (HTTPS with self-signed cert)

### 2. Access Different Brands

```bash
# StPetePros (default)
open https://localhost:5001

# Soulfra
open https://localhost:5001?brand=soulfra

# CringeProof
open https://localhost:5001?brand=cringeproof

# With geo override (for StPetePros testing outside FL)
open "https://localhost:5001?brand=stpetepros&geo_override=true"
```

### 3. Test from Phone (Same WiFi)

```bash
# Get your laptop's local IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Access from phone (replace with your IP)
https://192.168.1.87:5001?brand=cringeproof
```

---

## Adding a New Brand

1. **Update `brand_router.py`:**
   ```python
   configs = {
       'newbrand': {
           'name': 'NewBrand',
           'slug': 'newbrand',
           'tagline': 'Your tagline here',
           'domain': 'newbrand.com',
           'primary_color': '#HEXCODE',
           'personality': 'Description here'
       }
   }
   ```

2. **Create templates:**
   ```bash
   mkdir templates/newbrand
   touch templates/newbrand/base.html
   touch templates/newbrand/homepage.html
   ```

3. **Add route in `app.py`:**
   ```python
   if g.active_brand.get('slug') == 'newbrand':
       return render_template('newbrand/homepage.html')
   ```

4. **Test:**
   ```bash
   open https://localhost:5001?brand=newbrand
   ```

---

## Troubleshooting

### "I see Soulfra navigation on StPetePros!"
✅ **Fixed!** StPetePros now uses `templates/stpetepros/base.html` with clean navigation.

### "Brand switcher not working"
Check that:
1. `brand_router.py` has the brand in `detect_brand_from_request()`
2. `app.py` has `@app.before_request` handler
3. Flask server was restarted after code changes

### "Geo-restriction blocking me on localhost"
Add `?geo_override=true`:
```
https://localhost:5001?brand=stpetepros&geo_override=true
```

### "Can't access from phone"
1. Make sure phone is on same WiFi
2. Accept the security warning (self-signed cert)
3. Use your laptop's local IP: `192.168.x.x:5001`

---

## What's Next?

### Planned Features

- [ ] Real IP geolocation for StPetePros (ipapi.co integration)
- [ ] OAuth wiring (Google/GitHub/Apple login buttons)
- [ ] Brand-specific dashboards
- [ ] Cross-brand user accounts
- [ ] Cloudflare tunnel for public access

### Current Status

- ✅ Brand detection via `?brand=` parameter
- ✅ Clean StPetePros template (no Soulfra clutter)
- ✅ Geo-restriction framework (not yet enforced)
- ✅ Multi-brand configs in `brand_router.py`
- ⏳ OAuth integration (backend exists, frontend not wired)

---

## Quick Reference

| What | Where | How |
|------|-------|-----|
| **Switch brands** | URL | `?brand=soulfra` |
| **Override geo** | URL | `?geo_override=true` |
| **Brand configs** | Code | `brand_router.py` |
| **Brand detection** | Code | `app.py` @app.before_request |
| **Templates** | Files | `templates/{brand}/` |
| **Current brand** | Template | `{{ g.active_brand.name }}` |

---

Generated on 2025-01-04 🤖
