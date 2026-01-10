# Domain → Brand Mapping - Visual Architecture

**How domains, subdomains, and brands connect in the system**

---

## 🌐 The Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INCOMING HTTP REQUEST                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        SUBDOMAIN DETECTION                               │
│                    (subdomain_router.py:detect)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
                          ┌─────────┴─────────┐
                          │                   │
                    NO SUBDOMAIN         HAS SUBDOMAIN
                          │                   │
                          ↓                   ↓
              ┌───────────────────┐  ┌────────────────────┐
              │  DEFAULT DOMAIN   │  │  BRANDED DOMAIN    │
              │  localhost:5001   │  │  {slug}.localhost  │
              └───────────────────┘  └────────────────────┘
                          │                   │
                          ↓                   ↓
              ┌───────────────────┐  ┌────────────────────┐
              │   No Branding     │  │  Query Database    │
              │   brand_css=None  │  │  for brand slug    │
              └───────────────────┘  └────────────────────┘
                          │                   │
                          │                   ↓
                          │          ┌────────────────────┐
                          │          │  Compile CSS       │
                          │          │  from brand config │
                          │          └────────────────────┘
                          │                   │
                          ↓                   ↓
              ┌───────────────────────────────────────────┐
              │         TEMPLATE RENDERING                │
              │    (base.html + route template)           │
              └───────────────────────────────────────────┘
                                    ↓
              ┌───────────────────────────────────────────┐
              │  {% if brand_css %}                       │
              │    {{ brand_css|safe }}  ← Injection!     │
              │  {% endif %}                              │
              └───────────────────────────────────────────┘
                                    ↓
              ┌───────────────────────────────────────────┐
              │          FINAL HTML RESPONSE               │
              │   (with or without brand CSS)             │
              └───────────────────────────────────────────┘
```

---

## 📊 Domain → Brand Examples

### Example 1: Default Domain (Control)

```
Request:  http://localhost:5001/
          ↓
Subdomain: None
          ↓
Brand:    None
          ↓
CSS:      Default Soulfra purple (#667eea)
          ↓
Result:   Generic platform with purple theme
```

### Example 2: Ocean Dreams Subdomain (Treatment)

```
Request:  http://ocean-dreams.localhost:5001/
          ↓
Subdomain: "ocean-dreams"
          ↓
Query:    SELECT * FROM brands WHERE slug='ocean-dreams'
          ↓
Brand:    Ocean Dreams (id=1)
          ↓
Config:   {"colors": ["#003366", "#0066cc", ...], "values": [...]}
          ↓
Compile:  generate_brand_css(config)
          ↓
CSS:      <style>:root { --brand-primary: #003366; }...</style>
          ↓
Result:   Entire site themed with ocean blue colors
```

### Example 3: Brand Detail Page on Default Domain

```
Request:  http://localhost:5001/brand/ocean-dreams
          ↓
Subdomain: None (default domain)
          ↓
Route:    /brand/<slug> → brand_page(slug='ocean-dreams')
          ↓
Query:    SELECT * FROM brands WHERE slug='ocean-dreams'
          ↓
CSS:      Generated for this page only
          ↓
Result:   Page showing Ocean Dreams info WITH blue theme
          (but rest of site still purple!)
```

### Example 4: Brand Detail Page on Branded Domain

```
Request:  http://ocean-dreams.localhost:5001/brand/ocean-dreams
          ↓
Subdomain: "ocean-dreams" (branded domain)
          ↓
Global:   apply_brand_theming() sets brand_css for ALL pages
          ↓
Route:    /brand/<slug> → brand_page(slug='ocean-dreams')
          ↓
CSS:      ALREADY applied via subdomain + page-specific CSS
          ↓
Result:   Entire site blue + brand detail page also blue
          (double branding!)
```

---

## 🗺️ Complete Routing Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              DOMAINS                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  localhost:5001                    ocean-dreams.localhost:5001          │
│  ├─ /                              ├─ /                                 │
│  │  └─ index() → no brand          │  └─ index() → Ocean Dreams        │
│  │                                 │                                     │
│  ├─ /brand/ocean-dreams            ├─ /brand/ocean-dreams               │
│  │  └─ brand_page() → page CSS    │  └─ brand_page() → global+page CSS │
│  │                                 │                                     │
│  ├─ /post/some-post                ├─ /post/some-post                   │
│  │  └─ post_page() → no brand     │  └─ post_page() → Ocean Dreams     │
│  │                                 │                                     │
│  └─ /ai-network                    └─ /ai-network                        │
│     └─ ai_network() → no brand       └─ ai_network() → Ocean Dreams     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Insight:** The SUBDOMAIN determines global theming, the ROUTE determines page content!

---

## 🎨 Visual Delta Between Domains

### localhost:5001 (Control)

```css
:root {
  --brand-primary: #667eea;      /* Soulfra purple */
  --brand-secondary: #764ba2;    /* Purple gradient */
  --brand-accent: #f093fb;       /* Pink accent */
}

header { background: #667eea; }  /* Purple header */
a { color: #667eea; }            /* Purple links */
```

**Visual:** Purple gradients, pink accents, generic platform feel

### ocean-dreams.localhost:5001 (Treatment)

```css
:root {
  --brand-primary: #003366;      /* Ocean blue */
  --brand-secondary: #0066cc;    /* Lighter blue */
  --brand-accent: #3399ff;       /* Bright blue */
}

header { background: #003366; }  /* Blue header */
a { color: #003366; }            /* Blue links */
```

**Visual:** Blue gradients, aqua accents, calm ocean feel

**Delta:** 100% of theme attributes changed! (proven by test_control_vs_treatment.py)

---

## 🔧 How Subdomain Routing Works

### Code Flow (subdomain_router.py)

```python
# Step 1: Detect subdomain
def detect_brand_from_subdomain(request):
    """
    Extract brand slug from subdomain

    ocean-dreams.localhost:5001 → "ocean-dreams"
    localhost:5001 → None
    """
    host = request.host
    subdomain = extract_subdomain(host)

    if subdomain:
        # Query database
        brand = db.execute(
            'SELECT * FROM brands WHERE slug = ?',
            (subdomain,)
        ).fetchone()
        return brand

    return None

# Step 2: Apply brand theming
def apply_brand_theming(brand):
    """
    Generate CSS for brand

    Returns brand_css to inject into base.html
    """
    if not brand:
        return None

    config = json.loads(brand['config_json'])
    brand_css = generate_brand_css(config)

    return brand_css
```

### Integration with Flask

```python
@app.before_request
def handle_subdomain():
    """Run before every request"""

    # Detect brand from subdomain
    brand = detect_brand_from_subdomain(request)

    if brand:
        # Make brand_css available to ALL templates
        g.brand_css = apply_brand_theming(brand)
    else:
        g.brand_css = None
```

### Template Usage (base.html)

```html
<html>
<head>
    <title>{% block title %}Soulfra{% endblock %}</title>

    <!-- Default styles -->
    <link rel="stylesheet" href="/static/style.css">

    <!-- Brand override (if present) -->
    {% if brand_css %}
        {{ brand_css|safe }}  <!-- Inject brand CSS! -->
    {% endif %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

**This is the KEY injection point where branding happens!**

---

## 📍 Database Schema

### brands table

```sql
CREATE TABLE brands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,                  -- "Ocean Dreams"
    slug TEXT NOT NULL UNIQUE,           -- "ocean-dreams"
    personality TEXT,                    -- "calm, deep, flowing"
    tone TEXT,                           -- "peaceful and contemplative"
    config_json TEXT NOT NULL,           -- JSON config with colors, values, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Slug = Subdomain Identifier

```
slug: "ocean-dreams"
    ↓
Subdomain: ocean-dreams.localhost:5001
    ↓
Query: WHERE slug='ocean-dreams'
    ↓
Brand: Ocean Dreams (with all config)
```

The `slug` field is the CONNECTOR between domain and database!

---

## 🧪 Testing the Mapping

### Test 1: Verify Subdomain Detection

```bash
# Start server
python3 app.py

# Visit default domain
curl http://localhost:5001/ | grep "brand-primary"
# Should find: #667eea (purple)

# Visit branded domain
curl http://ocean-dreams.localhost:5001/ | grep "brand-primary"
# Should find: #003366 (ocean blue)
```

### Test 2: Verify Database Connection

```bash
# Check brand exists
sqlite3 soulfra.db "SELECT slug, name FROM brands WHERE slug='ocean-dreams';"
# Should output: ocean-dreams|Ocean Dreams

# Check config
sqlite3 soulfra.db "SELECT config_json FROM brands WHERE slug='ocean-dreams';"
# Should output: JSON with colors array
```

### Test 3: Verify CSS Compilation

```bash
# Prove compilation works
python3 prove_compilation.py ocean-dreams
# Should output: ✅ COMPILATION PROVEN!
```

### Test 4: Verify Control vs Treatment

```bash
# Compare domains
python3 test_control_vs_treatment.py
# Should output: 100% visual delta
```

---

## 🎯 The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER TYPES URL                                   │
│                  ocean-dreams.localhost:5001                             │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLASK RECEIVES REQUEST                                │
│                    @app.before_request                                   │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   SUBDOMAIN DETECTION                                    │
│         detect_brand_from_subdomain(request)                            │
│                                                                          │
│         host = "ocean-dreams.localhost:5001"                            │
│         subdomain = "ocean-dreams"                                      │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE QUERY                                      │
│         SELECT * FROM brands WHERE slug='ocean-dreams'                   │
│                                                                          │
│         Returns: Brand row with config_json                             │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      CONFIG PARSING                                      │
│         config = json.loads(brand['config_json'])                       │
│                                                                          │
│         Extracts: colors, values, personality, etc.                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      CSS COMPILATION                                     │
│         brand_css = generate_brand_css(config)                          │
│                                                                          │
│         Transforms: JSON → CSS with variables                           │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   STORE IN FLASK CONTEXT                                 │
│         g.brand_css = brand_css                                         │
│                                                                          │
│         Now available to ALL templates!                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      ROUTE EXECUTION                                     │
│         @app.route('/') → index()                                       │
│         return render_template('index.html')                            │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   TEMPLATE RENDERING                                     │
│         base.html extends + fills blocks                                │
│         {% if brand_css %}{{ brand_css|safe }}{% endif %}              │
│                                                                          │
│         Injects CSS into <head>!                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      HTTP RESPONSE                                       │
│         Status: 200 OK                                                  │
│         Content-Type: text/html                                         │
│         Body: HTML with injected brand CSS                              │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    BROWSER RENDERING                                     │
│         Parses HTML                                                     │
│         Applies CSS (including brand overrides)                         │
│         Displays: Ocean Dreams themed page!                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Insights

### 1. Slug is the Connector

```
Database slug ←→ Subdomain ←→ Brand identity
"ocean-dreams" in DB = ocean-dreams.localhost subdomain
```

### 2. Two Levels of Branding

**Global (Subdomain):**
- Applies to ALL pages on that domain
- Set via `@app.before_request` hook
- Stored in `g.brand_css`

**Page-Specific (Route):**
- Applies to specific page (e.g., /brand/ocean-dreams)
- Set in route function
- Passed to `render_template()`

### 3. Template Inheritance is the Key

```
base.html (parent)
  └─ Has {% if brand_css %} injection point
  └─ Defines structure

brand_page.html (child)
  └─ Extends base.html
  └─ Fills content blocks
  └─ Gets brand_css from parent!
```

### 4. The "Taint/Tint" Works via CSS Cascade

```
Default styles (style.css)
  ↓
Base template loads default
  ↓
{% if brand_css %} overrides defaults
  ↓
Brand colors "tint" the entire UI!
```

The tint is VISIBLE because we have both default and override!

---

## 🔗 Related Documentation

- `DECONSTRUCTION_GUIDE.md` - How to deconstruct any system
- `THE_NEED_FOR_OPPOSITES.md` - Philosophy of control vs treatment
- `CONTROL_VS_TREATMENT_RESULTS.md` - Proof of 100% delta
- `subdomain_router.py` - Actual routing code
- `brand_css_generator.py` - CSS compilation code
- `templates/base.html` - Injection point

---

## 🚀 How to Use This Map

### As a Developer:

1. **Understand the flow:** Follow the diagrams top to bottom
2. **Find your place:** Locate which part you're working on
3. **Trace connections:** See how components connect
4. **Verify behavior:** Use test tools to prove it works

### As a Debugger:

1. **Start at symptom:** What's broken?
2. **Find stage:** Which stage of flow is failing?
3. **Check inputs/outputs:** Verify data at that stage
4. **Trace backward:** Find where data got corrupted

### As a Learner:

1. **Read examples:** Follow the example flows
2. **Run tests:** Execute the proof tools
3. **Experiment:** Try different domains
4. **Modify:** Change colors and see results

---

## 📚 Testing Tools

```bash
# 1. Analyze template structure
python3 template_anatomy.py brand_page.html

# 2. Map data flow for route
python3 compilation_flow_map.py /brand/ocean-dreams

# 3. Prove compilation works
python3 prove_compilation.py ocean-dreams

# 4. Compare control vs treatment
python3 test_control_vs_treatment.py
```

Each tool PROVES a different aspect of the domain → brand mapping!

---

**This map shows how EVERYTHING connects - from URL typed in browser to final CSS applied to page!** 🗺️
