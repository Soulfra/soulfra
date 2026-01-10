# System Deconstruction Guide - The Meta-Template

**"How do we prove it in templates? How do we deconstruct, interpret, and compile these things?"**

This is the **META-LEVEL GUIDE** - a template for understanding templates themselves.

---

## 🎯 The Universal Pattern

Every web system follows this pattern:

```
1. DATA SOURCE
   (Database, config files, JSON)
   ↓
2. COMPILER/TRANSFORMER
   (Python function that processes data)
   ↓
3. TEMPLATE
   (HTML with injection points {{ variables }})
   ↓
4. ROUTER
   (Flask route that connects them)
   ↓
5. HTTP RESPONSE
   (Final HTML sent to browser)
   ↓
6. BROWSER RENDERING
   (What user actually sees)
```

**This is UNIVERSAL.** Once you understand this pattern, you can deconstruct ANY system!

---

## 📚 Example: Brand Page System

Let's use `/brand/ocean-dreams` as our example to demonstrate the deconstruction process.

### Step 1: Start at the End (What User Sees)

```
User visits: http://localhost:5001/brand/ocean-dreams

Sees:
- Page titled "Ocean Dreams - Brand Vault"
- Blue header (#003366)
- Blue links
- Brand info (personality, tone, colors)
- Download button
- Ratings section
```

**Question:** How did this get here?

---

### Step 2: Find the Template

**How to find:** Look in `/templates` directory

```bash
ls templates/ | grep brand
```

**Found:** `brand_page.html`

**Open it and identify key parts:**

```html
{% extends "base.html" %}                    ← Inherits from base template

{% block title %}{{ brand.name }}{% endblock %}    ← Variable: brand.name

{{ brand_css|safe }}                         ← Variable: brand_css

<h1>{{ brand.name }}</h1>                    ← Variable: brand.name
<p>{{ brand.personality }}</p>               ← Variable: brand.personality
```

**What we learned:**
- Template extends `base.html`
- Uses variables: `brand` (object), `brand_css` (string)
- Variables come from somewhere else (WHERE?)

---

### Step 3: Find the Route (Flask Connector)

**How to find:** Search for the URL pattern in `app.py`

```bash
grep "'/brand/<" app.py
```

**Found:** Line 1389

```python
@app.route('/brand/<slug>')
def brand_page(slug):
    """Brand detail page"""
    db = get_db()

    # Get brand from database
    brand_row = db.execute('''
        SELECT * FROM brands WHERE slug = ?
    ''', (slug,)).fetchone()

    brand_dict = dict(brand_row)

    # Parse config
    brand_config = json.loads(brand_dict['config_json'])

    # Generate CSS
    brand_css = generate_brand_css(brand_config)

    return render_template('brand_page.html',
                          brand=brand_dict,
                          brand_css=brand_css)
```

**What we learned:**
- Route `/brand/<slug>` maps to `brand_page()` function
- Function queries database for brand
- Calls `generate_brand_css()` compiler
- Passes `brand` and `brand_css` to template
- Returns rendered HTML

---

### Step 4: Find the Data Source

**From route, we saw:** `SELECT * FROM brands WHERE slug = ?`

**Database:** `soulfra.db`
**Table:** `brands`

**Inspect schema:**

```bash
sqlite3 soulfra.db "PRAGMA table_info(brands);"
```

**Found columns:**
- `id` - Primary key
- `name` - Brand name ("Ocean Dreams")
- `slug` - URL-safe identifier ("ocean-dreams")
- `personality` - Brand personality traits
- `tone` - Communication tone
- `config_json` - JSON with colors, values, etc.

**Sample data:**

```sql
SELECT name, slug, personality, config_json FROM brands WHERE slug='ocean-dreams';
```

**Result:**
```
name: Ocean Dreams
slug: ocean-dreams
personality: calm, deep, flowing
config_json: {"colors": ["#003366", "#0066cc", ...], "values": [...]}
```

**What we learned:**
- Data starts as JSON in database
- Contains raw configuration (colors, personality, etc.)
- Not yet CSS - needs to be COMPILED!

---

### Step 5: Find the Compiler

**From route, we saw:** `generate_brand_css(brand_config)`

**How to find:** Search for function definition

```bash
grep "def generate_brand_css" *.py
```

**Found:** `brand_css_generator.py:76`

```python
def generate_brand_css(brand_config, include_style_tag=True):
    """Generate CSS from brand configuration"""

    # Extract colors
    colors = brand_config.get('colors', {})
    primary = colors.get('primary', '#667eea')
    secondary = colors.get('secondary', '#764ba2')

    # Generate variations
    primary_light = adjust_lightness(primary, 1.2)
    primary_dark = adjust_lightness(primary, 0.8)

    # Build CSS
    css = f"""
    :root {{
        --brand-primary: {primary};
        --brand-secondary: {secondary};
        ...
    }}

    header {{ background: var(--brand-primary); }}
    a {{ color: var(--brand-primary); }}
    ...
    """

    return css
```

**What we learned:**
- Compiler transforms JSON → CSS
- Takes config data, processes it
- Outputs CSS string with variables
- THIS IS THE "MAGIC" - pure data becomes visual styling!

---

### Step 6: Find the Base Template

**From brand_page.html, we saw:** `{% extends "base.html" %}`

**How template inheritance works:**

**base.html:**
```html
<html>
<head>
    {% if brand_css %}
        {{ brand_css|safe }}    ← Injection point!
    {% endif %}
</head>
<body>
    {% block content %}{% endblock %}    ← Child fills this
</body>
</html>
```

**brand_page.html:**
```html
{% extends "base.html" %}    ← Inherits structure

{% block content %}          ← Fills the block
    <h1>{{ brand.name }}</h1>
{% endblock %}
```

**Final rendered HTML:**
```html
<html>
<head>
    <style>
        :root { --brand-primary: #003366; }
        header { background: var(--brand-primary); }
    </style>
</head>
<body>
    <h1>Ocean Dreams</h1>
</body>
</html>
```

**What we learned:**
- Templates use inheritance (DRY principle)
- Parent defines structure
- Child fills specific blocks
- Variables injected at render time

---

## 🔧 The Complete Flow (Traced Backwards)

Now we can trace the ENTIRE flow from user request to browser render:

```
1. USER REQUEST
   http://localhost:5001/brand/ocean-dreams
   ↓
2. FLASK ROUTING (app.py:1389)
   URL pattern matched: /brand/<slug>
   Calls: brand_page(slug='ocean-dreams')
   ↓
3. DATABASE QUERY (app.py:1391-1397)
   SQL: SELECT * FROM brands WHERE slug='ocean-dreams'
   Returns: Row with id, name, slug, config_json, etc.
   ↓
4. DATA PARSING (app.py:1399-1405)
   brand_dict = dict(brand_row)
   brand_config = json.loads(brand_dict['config_json'])
   ↓
5. CSS COMPILATION (brand_css_generator.py:76)
   Input: {"colors": ["#003366", "#0066cc", ...]}
   Processing: Extract colors, generate variations, build CSS
   Output: "<style>:root { --brand-primary: #003366; }...</style>"
   ↓
6. TEMPLATE RENDERING (app.py:1410)
   render_template('brand_page.html',
                  brand=brand_dict,
                  brand_css=brand_css)
   ↓
7. TEMPLATE INHERITANCE (templates/brand_page.html:1)
   {% extends "base.html" %}
   Merges: base structure + brand content
   ↓
8. VARIABLE INJECTION (templates/brand_page.html:7)
   {{ brand_css|safe }} → Injects CSS
   {{ brand.name }} → "Ocean Dreams"
   {{ brand.personality }} → "calm, deep, flowing"
   ↓
9. HTTP RESPONSE
   Status: 200 OK
   Content-Type: text/html
   Body: [Complete HTML with CSS]
   ↓
10. BROWSER RENDERING
    Parses HTML, applies CSS, shows blue theme
    User sees: Ocean Dreams branded page!
```

**PROVEN:** Data → Compiler → Template → HTML → Browser!

---

## 🧬 The Deconstruction Algorithm

Use this algorithm to deconstruct ANY system:

### Phase 1: Start at the Output

1. What does the user see?
2. View page source (browser dev tools)
3. Identify dynamic parts (brand colors, data, etc.)

### Phase 2: Find the Template

1. Look in `/templates` directory
2. Grep for text you see in output
3. Open template file
4. Identify:
   - What it extends (`{% extends "..." %}`)
   - What variables it uses (`{{ ... }}`)
   - What blocks it defines (`{% block ... %}`)

### Phase 3: Find the Route

1. Look at URL pattern (e.g., `/brand/ocean-dreams`)
2. Search `app.py` for route decorator
3. Find the function that handles it
4. Trace:
   - What data it queries
   - What it computes
   - What it passes to template

### Phase 4: Find the Data Source

1. Look at database queries in route
2. Inspect table schema
3. Look at sample data
4. Understand data format (JSON, etc.)

### Phase 5: Find the Compilers

1. Look for function calls in route
2. Search for function definitions
3. Understand transformations:
   - Input format
   - Processing steps
   - Output format

### Phase 6: Trace the Complete Flow

1. Draw diagram: Data → Compiler → Template → Output
2. Document each step
3. Prove it works (test with real data)

---

## 🔍 Proving It Works

### Method 1: Manual Trace

1. Start with data:
   ```json
   {"colors": ["#003366"]}
   ```

2. Run compiler:
   ```python
   css = generate_brand_css({"colors": ["#003366"]})
   print(css)
   ```

3. Verify output:
   ```css
   :root { --brand-primary: #003366; }
   ```

4. Check template injection:
   ```html
   {{ brand_css|safe }} → <style>:root { --brand-primary: #003366; }</style>
   ```

5. View in browser:
   - Header is #003366 blue ✅

### Method 2: Automated Proof

```python
# prove_compilation.py
def prove_brand_compilation(brand_slug):
    # Step 1: Get raw data
    db = get_db()
    brand = db.execute('SELECT * FROM brands WHERE slug=?', (brand_slug,)).fetchone()
    print(f"RAW DATA: {brand['config_json']}")

    # Step 2: Parse config
    config = json.loads(brand['config_json'])
    print(f"PARSED CONFIG: {config}")

    # Step 3: Compile CSS
    css = generate_brand_css(config)
    print(f"COMPILED CSS: {css[:200]}...")

    # Step 4: Verify injection
    assert '#003366' in css
    print("✅ PROOF: Data compiled to CSS successfully!")
```

---

## 📊 Common Patterns

### Pattern 1: Database → Template

```
Data: users table
Route: @app.route('/user/<id>')
Query: SELECT * FROM users WHERE id=?
Template: user.html
Variables: {{ user.name }}, {{ user.email }}
```

### Pattern 2: Config → CSS

```
Data: brand config_json
Compiler: generate_brand_css()
Output: CSS variables
Injection: {{ brand_css|safe }}
```

### Pattern 3: Subdomain → Theme

```
Request: ocean-dreams.localhost:5001
Detect: subdomain_router.py
Apply: Brand CSS to ALL pages
Result: Entire site themed
```

### Pattern 4: API → JSON

```
Request: /api/ai/test-relevance/1
Route: @app.route('/api/ai/test-relevance/<post_id>')
Processing: orchestrate_brand_comments()
Output: JSON response
Browser: Parses with JavaScript
```

---

## 🎨 Visual Metaphor: The Assembly Line

Think of it like a car factory:

```
STATION 1: RAW MATERIALS
   - Database tables
   - Config files
   - JSON data

STATION 2: PARTS EXTRACTION
   - SQL queries
   - JSON parsing
   - Data validation

STATION 3: ASSEMBLY
   - Compilers (CSS generation)
   - Transformers (data → HTML)
   - Formatters

STATION 4: PAINTING
   - Template inheritance
   - Variable injection
   - Block filling

STATION 5: QUALITY CHECK
   - Flask rendering
   - HTML validation
   - HTTP response

STATION 6: DELIVERY
   - Browser receives HTML
   - Parses and renders
   - User sees final product!
```

Each station has:
- **Input**: What comes in
- **Process**: What happens
- **Output**: What goes out

To deconstruct, trace backwards from output to input!

---

## 🧪 How to Interpret Templates

### Template Syntax Guide

**Jinja2 (Flask's template engine):**

```python
{{ variable }}                # Print variable
{% if condition %}{% endif %} # Conditional
{% for item in list %}{% endfor %} # Loop
{% extends "base.html" %}     # Inherit
{% block name %}{% endblock %} # Define/fill block
{{ var|safe }}                # Don't escape HTML
{{ var|default('fallback') }} # Default value
```

**Examples:**

```html
<!-- Variable from route -->
<h1>{{ brand.name }}</h1>
Where: brand = {"name": "Ocean Dreams"} from Flask

<!-- Loop over list -->
{% for color in brand.colors %}
    <div style="background: {{ color }}"></div>
{% endfor %}
Where: brand.colors = ["#003366", "#0066cc"]

<!-- Conditional -->
{% if brand.ratings %}
    <p>Rated {{ brand.avg_rating }} stars</p>
{% else %}
    <p>No ratings yet</p>
{% endif %}

<!-- Inheritance -->
Parent (base.html):
    {% block content %}Default{% endblock %}

Child (brand_page.html):
    {% extends "base.html" %}
    {% block content %}Brand specific!{% endblock %}

Result:
    Brand specific!  (child overrides parent)
```

---

## 🗺️ How Systems Map to Domains

### Localhost (Default) vs Subdomain (Branded)

**Request to:** `localhost:5001/brand/ocean-dreams`
- Route: `/brand/<slug>` in app.py
- Loads: ocean-dreams brand data
- Injects: brand_css into template
- Result: Page showing Ocean Dreams info WITH blue theme

**Request to:** `ocean-dreams.localhost:5001/` (any page)
- Subdomain detected: "ocean-dreams"
- Lookup: brands table for slug='ocean-dreams'
- Apply: brand_css to ALL pages (via base.html)
- Result: Entire site has Ocean Dreams blue theme

**Request to:** `localhost:5001/` (default)
- No subdomain detected
- No brand CSS applied
- Result: Default Soulfra purple theme

**The Contrast:**
```
DEFAULT DOMAIN           BRANDED DOMAIN
localhost:5001           ocean-dreams.localhost:5001
─────────────────────    ──────────────────────────────
No brand_css variable    brand_css = "<style>...</style>"
base.html renders plain  base.html injects brand CSS
Purple theme (#667eea)   Ocean blue theme (#003366)
```

This is THE OPPOSITE pattern - control vs treatment!

---

## 📖 Compilation Process Explained

### What "Compilation" Means

**Source code → Compiler → Machine code**

In our system:
**Brand config → CSS generator → Stylesheet**

### Compilation Stages

**Stage 1: Lexing (Tokenization)**
```
Input: {"colors": ["#003366", "#0066cc"]}
Parse: Extract 'colors' key, get array
Tokens: primary=#003366, secondary=#0066cc
```

**Stage 2: Processing**
```
Compute: primary_light = adjust_lightness(#003366, 1.2)
Result: primary_light = #004488
Compute: primary_rgb = hex_to_rgb(#003366)
Result: primary_rgb = (0, 51, 102)
```

**Stage 3: Code Generation**
```
Template: ":root { --brand-primary: {primary}; }"
Substitute: {primary} → #003366
Output: ":root { --brand-primary: #003366; }"
```

**Stage 4: Optimization**
```
Minify: Remove extra whitespace (optional)
Prefix: Add vendor prefixes (optional)
```

**Stage 5: Output**
```
Return: Complete CSS string
Wrap: <style>...</style> tags
Ready: For injection into HTML
```

---

## 🎯 Summary: The Deconstruction Recipe

1. **Start at the output** (what user sees)
2. **Find the template** (HTML with {{ variables }})
3. **Find the route** (Flask @app.route)
4. **Trace the data flow** (database → route → template)
5. **Find the compilers** (functions that transform data)
6. **Map the connections** (how pieces fit together)
7. **Prove it works** (test with real data)

**This pattern is UNIVERSAL!**

Works for:
- ✅ Brand pages
- ✅ Post pages
- ✅ API endpoints
- ✅ Subdomain routing
- ✅ AI comment generation
- ✅ Any web system!

---

## 🚀 Next Steps

Use the tools:

```bash
# Visualize template structure
python3 template_anatomy.py brand_page.html

# Trace compilation flow
python3 compilation_flow_map.py /brand/ocean-dreams

# Prove it works
python3 prove_compilation.py ocean-dreams
```

Each tool PROVES a different aspect of the system!

---

**This is the "user manual for the user manual" - the meta-template that explains templates themselves!** 🎓
