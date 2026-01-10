# Route Map - Complete URL Reference

**Total Routes:** 55+
**Framework:** Flask (Python)
**Architecture:** Monolithic with context processors

---

## Navigation Integration

**Header Nav:**
- Posts | Souls | Reasoning | ML | Dashboard | Tags ▾ | About | Feedback | Login/Signup

**Footer Nav:**
- Subscribe | Status | Showcase | **🚢 Shipyard** | **Brands** | **Tiers** | Code | Admin

**New Routes (2025-12-22):**
- `/shipyard` - Theme browser
- `/sitemap` - Visual route map
- `/sitemap.xml` - SEO XML sitemap
- `/robots.txt` - Crawler instructions

---

## Content & Posts

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage - Posts feed with AI predictions |
| `/post/<slug>` | GET | Individual post with comments |
| `/post/<slug>/comment` | POST | Submit comment on post |
| `/category/<slug>` | GET | Posts filtered by category |
| `/tag/<slug>` | GET | Posts filtered by tag |
| `/live` | GET | Real-time comment stream (Twitch-style) |

---

## Theme System 🚢⛵

| Route | Method | Description |
|-------|--------|-------------|
| `/shipyard` | GET | **Theme browser - Dinghy → Galleon classification** |
| `/brands` | GET | Brand marketplace - Downloadable themes |
| `/brand/<slug>` | GET | Individual brand identity page |
| `/brand/<slug>/export` | GET | Download brand ZIP package |
| `/tiers` | GET | Tier showcase - Binary → Images → Anime |

**Ship Classes:**
- ⛵ Dinghy: ~26 lines (emoji + colors)
- 🚤 Schooner: 50-80 lines (typography + components)
- ⚓ Frigate: 120-180 lines (full components + animations)
- 🚢 Galleon: 250+ lines (complete design system)

---

## Users & Souls

| Route | Method | Description |
|-------|--------|-------------|
| `/souls` | GET | Soul index - All user personas |
| `/soul/<username>` | GET | Soul profile - Individual visualization |
| `/soul/<username>/similar` | GET | Find similar souls |
| `/user/<username>` | GET | User profile - Posts and activity |
| `/login` | GET/POST | User authentication |
| `/signup` | GET/POST | Create account |
| `/logout` | GET | End session |

---

## AI & Machine Learning

| Route | Method | Description |
|-------|--------|-------------|
| `/train` | GET | Training interface - Colors/posts modes |
| `/train/predict` | POST | Get AI prediction for post |
| `/train/feedback` | POST | Submit training feedback |
| `/reasoning` | GET | Reasoning dashboard - AI threads |
| `/ml` | GET | ML dashboard - Neural network training |
| `/ml/train` | POST | Train model |
| `/ml/predict` | POST | Get prediction |
| `/dashboard` | GET | Live dashboard - Real-time predictions |

**Networks:**
- CalRiven Technical Classifier
- TheAuditor Validation Classifier
- DeathToData Privacy Classifier
- Soulfra Judge

---

## Showcases & Visual

| Route | Method | Description |
|-------|--------|-------------|
| `/showcase` | GET | Soul showcase gallery - Visual proof |
| `/code` | GET | Code browser - Navigate source |
| `/code/<path:filepath>` | GET | View specific file |
| `/status` | GET | Status dashboard - System health |

---

## Admin & Management

| Route | Method | Description |
|-------|--------|-------------|
| `/admin` | GET | Admin dashboard |
| `/admin/login` | GET/POST | Admin authentication |
| `/admin/dashboard` | GET/POST | Main admin interface |
| `/admin/automation` | GET | Scheduled tasks management |
| `/admin/automation/run-builder` | POST | Run weekly builder |
| `/admin/automation/generate-digest` | POST | Generate email digest |
| `/admin/automation/send-digest` | POST | Send newsletter |
| `/admin/subscribers` | GET | Newsletter subscribers list |
| `/admin/subscribers/export` | GET | Download subscribers CSV |
| `/admin/subscribers/import` | GET/POST | Upload subscribers CSV |
| `/admin/logout` | GET | End admin session |

---

## API Endpoints (JSON)

| Route | Method | Description |
|-------|--------|-------------|
| `/api/health` | GET | Server status check |
| `/api/posts` | GET | All posts with metadata |
| `/api/posts/<int:post_id>` | GET | Post with AI predictions |
| `/api/reasoning/threads` | GET | All reasoning threads |
| `/api/reasoning/threads/<int:thread_id>` | GET | Thread detail with turns |
| `/api/feedback` | POST | Submit user feedback |

---

## Utilities

| Route | Method | Description |
|-------|--------|-------------|
| `/subscribe` | GET/POST | Newsletter subscription |
| `/unsubscribe` | GET | Remove from newsletter |
| `/about` | GET | Platform information |
| `/feedback` | GET/POST | Submit user feedback |
| `/feed.xml` | GET | RSS/Atom feed |
| `/sitemap` | GET | **Visual route map (this page)** |
| `/sitemap.xml` | GET | **SEO XML sitemap** |
| `/robots.txt` | GET | **Crawler instructions** |
| `/s/<short_id>` | GET | URL shortener - Redirect to profile |
| `/qr/<qr_id>` | GET | Generate QR code image |
| `/i/<hash>` | GET | Serve uploaded images |

---

## How Python/Flask Works With This

### Route Definition

```python
@app.route('/shipyard')          # URL endpoint
def shipyard():                   # Python function
    manifest = yaml.load(...)     # Load data
    return render_template(...)   # Return HTML
```

### Template Usage

```html
<!-- In templates, use url_for() -->
<a href="{{ url_for('shipyard') }}">Shipyard</a>
```

### Query Parameters

```python
# URL: /?brand=ocean-dreams
brand_name = request.args.get('brand')  # Get 'ocean-dreams'
```

### Dynamic Routes

```python
@app.route('/brand/<slug>')      # <slug> is variable
def brand_page(slug):            # Passed as argument
    brand = get_brand(slug)      # Use it
```

---

## URL Structure Philosophy

**Flat & Readable:**
- `/souls` (plural) = index
- `/soul/<username>` (singular) = detail

**RESTful Patterns:**
- GET = Read data
- POST = Create/update data

**Hierarchy:**
- `/brand/<slug>` = Brand detail
- `/brand/<slug>/export` = Action on brand

---

## Context Processors

**Global template variables** (automatically available in all templates):

```python
@app.context_processor
def inject_globals():
    return dict(
        all_tags=get_all_tags(),
        BASE_URL=BASE_URL,
        PLATFORM_VERSION=PLATFORM_VERSION,
        brand_css=load_brand_css()  # Dynamic theming!
    )
```

Used in templates:
```html
{{ BASE_URL }}            <!-- Automatic -->
{% for tag in all_tags %} <!-- Automatic -->
{{ brand_css|safe }}      <!-- Automatic -->
```

---

## SEO & Discovery

**Search Engines:**
- `/sitemap.xml` - Machine-readable URL list
- `/robots.txt` - Crawler rules

**Humans:**
- `/sitemap` - Visual route map
- `/shipyard` - Theme browser
- Footer links - Quick access

**Feeds:**
- `/feed.xml` - RSS for posts

---

## Special Routes

**Short URLs:**
- `/s/<short_id>` → Redirects to `/user/<username>`

**Image Serving:**
- `/i/<hash>` → Serves from `static/generated/` or database

**QR Codes:**
- `/qr/<qr_id>` → Generates QR code PNG

**Dynamic Branding:**
- `?brand=ocean-dreams` → Applies theme to any page

---

## Testing Routes

**Port 5001 (currently running):**

```bash
# New routes added today
open http://localhost:5001/shipyard      # Theme browser
open http://localhost:5001/sitemap       # Visual route map
open http://localhost:5001/sitemap.xml   # SEO XML
open http://localhost:5001/robots.txt    # Crawler rules

# Existing routes now in footer
open http://localhost:5001/brands        # Brand marketplace
open http://localhost:5001/tiers         # Tier showcase
```

---

## Route Count by Category

| Category | Count |
|----------|-------|
| Content & Posts | 6 |
| Theme System | 5 |
| Users & Souls | 7 |
| AI & Machine Learning | 8 |
| Showcases & Visual | 4 |
| Admin & Management | 11 |
| API Endpoints | 6 |
| Utilities | 11 |
| **Total** | **58** |

---

## Updates

**2025-12-22:** Added shipyard, sitemap, sitemap.xml, robots.txt routes. Integrated theme system into footer navigation.
