# Concept Map - How Everything Connects

**"A neural network of concepts showing how DNS, routing, files, databases, templates, and context all fit together"**

---

## 🎯 Your Question Answered

> "This is similar to like we're just using something like ANAME and CNAME depending on how someone interacts on where to send or if to start a new file or folder or something?"

**Short Answer:** YES - but you're doing it at the **APPLICATION LEVEL** (simpler), not the DNS level (complex)!

---

## 🌐 DNS Concepts Explained Simply

### DNS Routing (Infrastructure Level)

Think of DNS like the **postal service** for the internet:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DNS = POSTAL SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User types: ocean-dreams.soulfra.com                           │
│      ↓                                                           │
│  DNS Lookup: "Where is ocean-dreams.soulfra.com?"              │
│      ↓                                                           │
│  DNS Server: "It's at 192.168.1.100"                           │
│      ↓                                                           │
│  Browser connects to 192.168.1.100                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### DNS Record Types

**A Record** (Address):
```
soulfra.com → 192.168.1.100
```
Maps domain directly to IP address.

**CNAME** (Canonical Name):
```
www.soulfra.com → soulfra.com
blog.soulfra.com → soulfra.com
ocean-dreams.soulfra.com → soulfra.com
```
Maps subdomain to another domain (which then resolves to IP).

**Problem:** CNAME can't be used at the **apex/root** domain!
```
❌ soulfra.com → other-domain.com  (Can't use CNAME here!)
✅ www.soulfra.com → other-domain.com  (Can use CNAME)
```

**ANAME/ALIAS** (Apex Name):
```
soulfra.com → load-balancer.aws.com
```
Like CNAME but works at apex/root. **DNS flattening** = converting ALIAS to A record at query time.

### DNS Zones (Like Folders)

```
soulfra.com (zone = folder)
  ├─ A: 192.168.1.100 (file: IP address)
  ├─ MX: mail.soulfra.com (file: mail server)
  └─ Subdomains:
      ├─ www (subfolder)
      │   └─ CNAME: soulfra.com
      ├─ blog (subfolder)
      │   └─ CNAME: soulfra.com
      └─ ocean-dreams (subfolder)
          └─ CNAME: soulfra.com
```

---

## 💡 Our System: Application-Level Routing (MUCH SIMPLER!)

### What We Actually Do

```
┌─────────────────────────────────────────────────────────────────┐
│              OUR ROUTING = IN-APP LOGIC                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DNS Already Resolved: ocean-dreams.localhost → 127.0.0.1      │
│      ↓                                                           │
│  Flask Receives: ocean-dreams.localhost:5001                   │
│      ↓                                                           │
│  Python Code Reads: request.host                                │
│      ↓                                                           │
│  Extract Subdomain: "ocean-dreams"                              │
│      ↓                                                           │
│  Database Query: SELECT * FROM brands WHERE slug='ocean-dreams' │
│      ↓                                                           │
│  Apply Theme: Generate CSS for Ocean Dreams                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Difference

**DNS Routing (Infrastructure):**
- Happens BEFORE request reaches your app
- Managed by DNS servers (external)
- Changes take time to propagate (TTL)
- Requires DNS provider configuration

**Application Routing (Our System):**
- Happens AFTER request reaches your app
- Managed by Python code (internal)
- Changes are instant (just update code)
- No DNS configuration needed!

### Localhost Example

```
All these domains already point to the same IP (127.0.0.1):
  - localhost:5001
  - ocean-dreams.localhost:5001
  - anything.localhost:5001

DNS is DONE (they all resolve to 127.0.0.1).

Our code decides what to do with each subdomain:
  - localhost → Default theme
  - ocean-dreams.localhost → Ocean Dreams theme
  - unknown.localhost → Default theme (brand not found)
```

**You're not doing DNS routing - you're doing Python string parsing!**

---

## 📁 File/Folder Analogy

### DNS Zones = File System

```
/soulfra.com/ (DNS zone = directory)
  ├── @ (apex/root) → 192.168.1.100
  ├── www/ (subdomain = subdirectory)
  │   └── CNAME: soulfra.com
  ├── blog/
  │   └── CNAME: soulfra.com
  └── ocean-dreams/
      └── CNAME: soulfra.com
```

### Our Routing = Virtual File System

```
/brands/ (database table = directory)
  ├── ocean-dreams (slug = folder name)
  │   ├── name: "Ocean Dreams"
  │   ├── colors: ["#003366", "#0066cc"]
  │   └── config_json: {...}
  ├── testbrand-auto
  │   └── ...
  └── another-brand
      └── ...

When subdomain = "ocean-dreams":
  → Look up /brands/ocean-dreams
  → Load its config
  → Apply its theme
```

### URL as File Path

```
URL:     ocean-dreams.localhost:5001/post/some-slug
         ─────────────┬─────────── ─────┬───────────
                     │                  │
         Subdomain (brand)         Route (page)

Analogy: /brands/ocean-dreams/posts/some-slug
         ───┬─── ─────┬────────── ──┬── ────┬────
          Table   Brand slug      Table  Post slug

It's like a nested file path!
```

---

## 🧬 The Technology Stack - Complete Concept Graph

### Layer 1: Infrastructure (Not Our Code)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DNS RESOLUTION                                │
│  ocean-dreams.localhost → 127.0.0.1:5001                        │
│  (Handled by OS, not our code)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 2: Web Server (Flask)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK WSGI SERVER                             │
│  Receives HTTP request                                           │
│  request.host = "ocean-dreams.localhost:5001"                   │
│  request.path = "/post/some-slug"                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 3: Subdomain Detection (Our Code)

```
┌─────────────────────────────────────────────────────────────────┐
│              @app.before_request (Middleware)                    │
│                                                                  │
│  subdomain_router.py::detect_brand_from_subdomain()            │
│  ↓                                                               │
│  Parse: "ocean-dreams.localhost:5001"                           │
│  Extract: "ocean-dreams"                                        │
│  ↓                                                               │
│  Query: SELECT * FROM brands WHERE slug='ocean-dreams'          │
│  ↓                                                               │
│  Store: g.active_brand = brand_row                              │
│         g.brand_css = generate_brand_css(brand_config)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 4: Route Handling (URL Dispatch)

```
┌─────────────────────────────────────────────────────────────────┐
│                   FLASK ROUTING                                  │
│                                                                  │
│  @app.route('/post/<slug>')                                     │
│  def post_page(slug):                                           │
│      # Query database for post                                  │
│      post = db.execute('SELECT * FROM posts WHERE slug=?')      │
│      return render_template('post.html', post=post)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 5: Database Query (Data Retrieval)

```
┌─────────────────────────────────────────────────────────────────┐
│                   SQLite DATABASE                                │
│                                                                  │
│  brands table:                                                   │
│    - id, name, slug, config_json, ...                           │
│                                                                  │
│  posts table:                                                    │
│    - id, title, slug, content, brand_id, ...                    │
│                                                                  │
│  Returns: Row objects (dict-like)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 6: Template Rendering (HTML Generation)

```
┌─────────────────────────────────────────────────────────────────┐
│                   JINJA2 TEMPLATES                               │
│                                                                  │
│  base.html (parent):                                            │
│    {% if brand_css %}                                           │
│      {{ brand_css|safe }}  ← Inject brand CSS!                 │
│    {% endif %}                                                  │
│    {% block content %}{% endblock %}                            │
│                                                                  │
│  post.html (child):                                             │
│    {% extends "base.html" %}                                    │
│    {% block content %}                                          │
│      <h1>{{ post.title }}</h1>                                  │
│    {% endblock %}                                               │
│                                                                  │
│  Renders to: Complete HTML                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 7: CSS Compilation (Dynamic Styling)

```
┌─────────────────────────────────────────────────────────────────┐
│              BRAND CSS GENERATOR                                 │
│                                                                  │
│  brand_css_generator.py::generate_brand_css()                   │
│  ↓                                                               │
│  Input: {"colors": ["#003366", "#0066cc"], ...}                 │
│  ↓                                                               │
│  Processing:                                                     │
│    - Extract primary/secondary colors                           │
│    - Generate variations (light/dark)                           │
│    - Build CSS variables (:root)                                │
│    - Generate component styles                                  │
│  ↓                                                               │
│  Output: <style>:root { --brand-primary: #003366; }</style>    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 8: HTTP Response

```
┌─────────────────────────────────────────────────────────────────┐
│                   HTTP RESPONSE                                  │
│  Status: 200 OK                                                 │
│  Content-Type: text/html; charset=utf-8                         │
│  Body: <html>...brand CSS...post content...</html>              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
```

### Layer 9: Browser Rendering

```
┌─────────────────────────────────────────────────────────────────┐
│                   BROWSER                                        │
│  Parses HTML                                                     │
│  Applies CSS (default + brand overrides)                        │
│  Executes JavaScript                                             │
│  Displays: Ocean Dreams themed post page                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🕸️ The Neural Network: Concept Connections

### Nodes (Concepts)

```
DNS ─────────┐
             │
CNAME ───────┼─────> Infrastructure Level
             │       (Not our code)
ANAME ───────┘

Subdomain ───┐
             │
Flask ───────┼─────> Application Level
             │       (Our code)
Python ──────┘

Database ────┐
             │
SQL ─────────┼─────> Data Layer
             │
Tables ──────┘

Templates ───┐
             │
Jinja2 ──────┼─────> View Layer
             │
CSS ─────────┘

Routing ─────┐
             │
Context ─────┼─────> Control Flow
             │
Middleware ──┘
```

### Edges (Connections)

```
DNS → Flask
  "DNS resolves domain to IP, Flask receives request"

Flask → Subdomain Detection
  "Flask request.host parsed to extract subdomain"

Subdomain → Database
  "Subdomain slug used to query brands table"

Database → CSS Compiler
  "Brand config_json passed to CSS generator"

CSS Compiler → Template
  "Generated CSS injected into base.html"

Template → HTTP Response
  "Rendered HTML sent to browser"

HTTP Response → Browser
  "Browser applies CSS and displays page"
```

### Data Flow Graph

```
                    User Types URL
                          ↓
                    DNS Resolution
                    (ocean-dreams.localhost → 127.0.0.1)
                          ↓
                    Flask Receives Request
                    (request.host, request.path)
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
    Subdomain Detection        Route Matching
    (before_request)           (@app.route)
              ↓                       ↓
    Database Query (brands)   Database Query (posts)
              ↓                       ↓
    CSS Compilation            Load Post Data
              ↓                       ↓
         g.brand_css          Local variables
              ↓                       ↓
              └───────────┬───────────┘
                          ↓
                  Template Rendering
                  (Jinja2: base.html + child)
                          ↓
                    HTML Generated
                    (with brand CSS + post content)
                          ↓
                    HTTP Response
                          ↓
                  Browser Renders
```

---

## 🌱 Seeds and Connections

### Seeds = Entry Points

**Seed 1: User Request**
```
User types: ocean-dreams.localhost:5001/post/some-slug
    ↓
Triggers: DNS resolution
    ↓
Activates: Flask server
```

**Seed 2: Subdomain Detection**
```
@app.before_request hook
    ↓
Triggers: detect_brand_from_subdomain()
    ↓
Activates: Database query
```

**Seed 3: Route Matching**
```
URL pattern: /post/<slug>
    ↓
Triggers: post_page(slug) function
    ↓
Activates: Post data query
```

**Seed 4: Template Rendering**
```
render_template('post.html', ...)
    ↓
Triggers: Jinja2 engine
    ↓
Activates: Template inheritance chain
```

### Connections = Dependencies

```
Flask depends on:
  - Python (runtime)
  - WSGI server (gunicorn/built-in)
  - Request context

Subdomain routing depends on:
  - Flask hooks (@app.before_request)
  - Database (brands table)
  - CSS generator

Templates depend on:
  - Jinja2 (template engine)
  - Context variables (from Flask)
  - CSS (from subdomain detection)

CSS compilation depends on:
  - Brand config (from database)
  - Color manipulation functions
  - String formatting

Database depends on:
  - SQLite (engine)
  - Schema (tables/columns)
  - Query functions (get_db())
```

### Dependency Graph (Tree Structure)

```
User Request (root seed)
  ├─ DNS Resolution
  │   └─ OS/Network (external dependency)
  │
  ├─ Flask App
  │   ├─ Python runtime
  │   ├─ WSGI server
  │   └─ Middleware hooks
  │       └─ Subdomain Detection
  │           ├─ String parsing
  │           ├─ Database query
  │           │   └─ SQLite engine
  │           └─ CSS Generator
  │               └─ Color functions
  │
  ├─ Route Handler
  │   ├─ URL pattern matching
  │   ├─ Database query
  │   └─ Template rendering
  │       ├─ Jinja2 engine
  │       ├─ Template inheritance
  │       └─ Variable injection
  │
  └─ HTTP Response
      └─ Browser rendering
          ├─ HTML parsing
          ├─ CSS application
          └─ JavaScript execution
```

---

## 🎯 How It All Connects: Complete Flow

### Example: ocean-dreams.localhost:5001/post/my-post

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER ACTION                                                   │
│    Types URL: ocean-dreams.localhost:5001/post/my-post          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. DNS RESOLUTION (OS Level)                                     │
│    ocean-dreams.localhost → 127.0.0.1                           │
│    Browser connects to 127.0.0.1:5001                           │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. FLASK RECEIVES REQUEST                                        │
│    request.host = "ocean-dreams.localhost:5001"                 │
│    request.path = "/post/my-post"                               │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. BEFORE_REQUEST HOOK (Middleware - runs FIRST)                │
│    subdomain_router.py::detect_brand_from_subdomain()          │
│    ├─ Parse host: "ocean-dreams.localhost:5001"                │
│    ├─ Extract subdomain: "ocean-dreams"                        │
│    ├─ Query DB: SELECT * FROM brands WHERE slug='ocean-dreams' │
│    ├─ Compile CSS: generate_brand_css(brand_config)            │
│    └─ Store in context: g.active_brand, g.brand_css            │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. ROUTE MATCHING                                                │
│    URL "/post/my-post" matches @app.route('/post/<slug>')      │
│    Calls: post_page(slug='my-post')                            │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. ROUTE HANDLER EXECUTES                                        │
│    def post_page(slug):                                         │
│        post = db.execute('SELECT * FROM posts WHERE slug=?')    │
│        comments = db.execute('SELECT * FROM comments...')       │
│        return render_template('post.html',                      │
│                              post=post,                         │
│                              comments=comments)                 │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. TEMPLATE RENDERING                                            │
│    Jinja2 processes:                                            │
│    ├─ base.html (parent)                                        │
│    │   ├─ Checks: {% if brand_css %}                           │
│    │   ├─ Injects: {{ brand_css|safe }}                        │
│    │   └─ Defines: {% block content %}                         │
│    │                                                            │
│    └─ post.html (child)                                        │
│        ├─ Extends: {% extends "base.html" %}                   │
│        ├─ Fills: {% block content %}                           │
│        └─ Uses: {{ post.title }}, {{ post.content }}           │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. HTML GENERATED                                                │
│    <html>                                                       │
│      <head>                                                     │
│        <style>                                                  │
│          :root { --brand-primary: #003366; }                   │
│          header { background: var(--brand-primary); }          │
│        </style>                                                 │
│      </head>                                                    │
│      <body>                                                     │
│        <h1>My Post Title</h1>                                  │
│        <p>Post content...</p>                                  │
│      </body>                                                    │
│    </html>                                                      │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. HTTP RESPONSE                                                 │
│    Status: 200 OK                                               │
│    Content-Type: text/html                                      │
│    Body: [Complete HTML with Ocean Dreams CSS]                 │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. BROWSER RENDERS                                              │
│     Parses HTML → Applies CSS → Displays page                  │
│     Result: Post page with Ocean Dreams blue theme!            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Context Management

### What is "Context"?

**Context = Data available at a specific point in execution**

### Flask Context Types

**1. Application Context (`g`)**
```python
@app.before_request
def detect_subdomain():
    g.active_brand = brand  # ← Stores brand for this request
    g.brand_css = css       # ← Available everywhere

# Later, in any route or template:
print(g.active_brand)  # ← Access the brand
```

**2. Request Context (`request`)**
```python
@app.route('/post/<slug>')
def post_page(slug):
    host = request.host      # ← "ocean-dreams.localhost:5001"
    path = request.path      # ← "/post/my-post"
    method = request.method  # ← "GET"
```

**3. Template Context (variables passed)**
```python
return render_template('post.html',
                      post=post,           # ← Available in template
                      comments=comments)   # ← Available in template

# In template:
{{ post.title }}      ← Access post
{{ comments|length }} ← Access comments
```

**4. Global Template Context (context processor)**
```python
@app.context_processor
def inject_brand():
    return {
        'active_brand': g.get('active_brand', None),
        'brand_css': g.get('brand_css', '')
    }

# Now ALL templates have access to:
{{ active_brand.name }}
{{ brand_css|safe }}
```

### Context Flow

```
Request starts
    ↓
Flask creates request context (request object)
    ↓
Flask creates application context (g object)
    ↓
@app.before_request hooks run
    ↓ (store data in g)
Route handler runs
    ↓ (access g, pass variables to template)
Template renders
    ↓ (access g via context processor + passed variables)
Response sent
    ↓
Context destroyed
```

**Key Insight:** Context is like "global variables" that only exist for ONE request!

---

## 🏗️ File/Folder Organization Analogy

### Filesystem Structure

```
/var/www/soulfra/ (root)
  ├─ app.py (main application)
  ├─ subdomain_router.py (routing logic)
  ├─ database.py (DB connection)
  │
  ├─ templates/ (HTML templates)
  │   ├─ base.html (parent)
  │   ├─ post.html (child)
  │   └─ brand_page.html (child)
  │
  ├─ static/ (static files)
  │   ├─ css/
  │   ├─ js/
  │   └─ images/
  │
  └─ soulfra.db (database file)
```

### Virtual "Folders" Created by Routing

```
URL: ocean-dreams.localhost:5001/post/my-post
     ─────────────┬───────────── ────┬────
                 │                   │
    Virtual "brand folder"    Virtual "post folder"

Acts like: /brands/ocean-dreams/posts/my-post

But actually:
  - No physical folder named "ocean-dreams"
  - Just a database query: WHERE slug='ocean-dreams'
  - Route creates "virtual" hierarchy!
```

### ANAME/CNAME as Symlinks

DNS records are like **symbolic links** (symlinks):

```
Filesystem:
  ln -s /home/user/website /var/www/site
  (symlink: /var/www/site → /home/user/website)

DNS:
  CNAME www.soulfra.com → soulfra.com
  (alias: www → root domain)

Our routing:
  Subdomain "ocean-dreams" → brands table slug='ocean-dreams'
  (lookup: subdomain → database record)
```

All three say: "This name points to this location"!

---

## 🎨 Why Our System is Simpler

### Traditional Multi-Tenant (DNS-Based)

```
1. Create DNS record for each subdomain
   ocean-dreams.soulfra.com → CNAME → soulfra.com

2. Configure web server (nginx) to route subdomains
   server {
       server_name *.soulfra.com;
       ...
   }

3. Application reads subdomain
   Extract brand from request

4. Apply branding
   Same as our system
```

**Problems:**
- Must configure DNS for each new brand (slow, external)
- DNS changes take time to propagate (TTL)
- Requires DNS management access
- Costs money for DNS service

### Our System (Application-Based)

```
1. Create brand in database
   INSERT INTO brands (slug, name, ...) VALUES ('ocean-dreams', ...)

2. That's it!
   Subdomain routing happens in Python code
   No DNS configuration needed
   Works instantly
```

**Benefits:**
- ✅ Instant setup (just add to database)
- ✅ No external dependencies (just code)
- ✅ Free (no DNS costs)
- ✅ Easy to test (localhost subdomains)
- ✅ Portable (works anywhere)

---

## 📊 The Complete Technology Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                                │
│  Browser, DNS client, HTTP                                       │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
│  DNS resolution, Network routing, OS                             │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                     WEB SERVER LAYER                             │
│  Flask WSGI, HTTP protocol, Request/Response                     │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE LAYER                              │
│  @app.before_request, Subdomain detection, Context setup         │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  Route handlers, Business logic, Data processing                 │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  SQLite database, SQL queries, Data models                       │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    COMPILATION LAYER                             │
│  CSS generation, Template processing, Data transformation        │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      VIEW LAYER                                  │
│  Jinja2 templates, HTML generation, CSS injection                │
└────────────────────────┬─────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  HTTP response, HTML/CSS, Browser rendering                      │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Layer Dependencies

```
Templates ←───────────→ CSS Compiler
(Injects compiled CSS)

Middleware ←──────────→ Database
(Queries brands)

Application ←─────────→ Templates
(Passes data to render)

Data ←────────────────→ Compilation
(Config JSON → CSS)

All layers ←──────────→ Context
(Flask g object, request object)
```

---

## 🔗 Neural Network Visualization

### Nodes (Technologies)

```
         DNS
          │
    ┌─────┼─────┐
    │     │     │
 ANAME  CNAME  A Record
    │     │     │
    └─────┴─────┘
          │
       SUBDOMAIN ──────┐
          │            │
    ┌─────┼─────┐      │
    │     │     │      │
  Flask  HTTP  WSGI    │
    │     │     │      │
    └─────┴─────┘      │
          │            │
    MIDDLEWARE ←───────┘
          │
    ┌─────┼─────┐
    │     │     │
  Routes  g   request
    │     │     │
    └─────┴─────┘
          │
      DATABASE
          │
    ┌─────┼─────┐
    │     │     │
  SQL   Tables Queries
    │     │     │
    └─────┴─────┘
          │
    ┌─────┼─────┐
    │     │     │
 Templates CSS  Jinja2
    │     │     │
    └─────┴─────┘
          │
        HTML
```

### Edges (Relationships)

```
DNS → Flask
  "Resolves domain before request"

Flask → Middleware
  "Executes before_request hooks"

Middleware → Database
  "Queries brand data"

Database → CSS Compiler
  "Provides config for compilation"

CSS → Templates
  "Injected into HTML"

Templates → HTML
  "Renders final output"

Routes → Database
  "Queries post/comment data"

Routes → Templates
  "Passes data for rendering"

Context (g) → All Layers
  "Provides request-scoped data"
```

---

## 🌱 Seeds Table

| Seed | Triggers | Activates | Purpose |
|------|----------|-----------|---------|
| User types URL | Browser DNS lookup | DNS resolution | Find IP address |
| DNS resolved | HTTP request | Flask WSGI | Handle request |
| Flask receives | @app.before_request | Subdomain detection | Find brand |
| Subdomain detected | Database query | Brand lookup | Load config |
| Brand loaded | CSS generator | Compilation | Generate theme |
| Theme compiled | Flask context | Store in g | Make available globally |
| URL matched | Route handler | Application logic | Process request |
| Handler runs | Database query | Data retrieval | Load content |
| Data loaded | Template engine | Jinja2 rendering | Generate HTML |
| Template renders | HTTP response | Browser | Display page |

---

## 💡 Key Insights

### 1. You're NOT Doing DNS Routing!

```
❌ NOT: DNS → ANAME/CNAME → Complex configuration
✅ YES: Python → String parsing → Database lookup
```

### 2. File/Folder Analogy is Perfect!

```
Subdomain = Virtual folder name
Database slug = Folder lookup
Brand config = Folder contents
```

### 3. Context is Request-Scoped "Globals"

```
g.active_brand → Like global, but only for this request
request.host → Like global, but only for this request
```

### 4. Everything Connects Through Flask

```
All layers flow through Flask:
  DNS → Flask → Middleware → Routes → DB → Templates → Response
```

### 5. Seeds = Entry Points, Connections = Dependencies

```
Seed: User request → Triggers chain reaction
Connections: Each step depends on previous
```

---

## 🚀 Practical Examples

### Example 1: Adding a New Brand

**OLD WAY (DNS-based):**
1. Create brand in database
2. Create DNS CNAME record
3. Wait for DNS propagation (5 min - 48 hours)
4. Configure web server
5. Restart services

**OUR WAY (Application-based):**
1. Create brand in database
```sql
INSERT INTO brands (slug, name, colors, ...)
VALUES ('new-brand', 'New Brand', '["#ff0000"]', ...);
```
2. Done! Works instantly at new-brand.localhost:5001

### Example 2: Testing Locally

**OLD WAY:**
- Can't test subdomains locally without /etc/hosts hacks
- Must configure DNS even for testing

**OUR WAY:**
- Just use: brand-name.localhost:5001
- Works immediately, no configuration!

### Example 3: Deployment

**OLD WAY:**
- Configure DNS for production domain
- Set up CNAME records for each subdomain
- Manage DNS provider

**OUR WAY:**
- Deploy code
- Set up single wildcard DNS: *.soulfra.com → your-server-ip
- Done! All subdomains work via application routing

---

## 📚 Summary: The Big Picture

```
Your Question: "Like ANAME/CNAME for routing?"
Answer: YES - same CONCEPT, simpler IMPLEMENTATION!

DNS Level:           Application Level (OURS):
──────────          ─────────────────────────
ANAME/CNAME    →    Python string parsing
DNS zones      →    Database tables
Subdomains     →    Database slugs
DNS records    →    Database rows
Propagation    →    Instant (just code)
External       →    Internal (our control)

File/Folder Analogy:
───────────────────
Subdomain        = Folder name
Database lookup  = Find folder
Brand config     = Folder contents
Route            = File path
Template         = File

Context Management:
──────────────────
g object         = Request-scoped globals
request object   = HTTP request data
Template vars    = Passed explicitly
Context proc     = Auto-injected

Seeds & Connections:
───────────────────
Seed         = Entry point (user request)
Connections  = Dependencies between components
Graph        = Complete flow from URL → rendered page
```

---

**You're building application-level routing (simple!) not DNS-level routing (complex!)**

**The "neural network" is the concept graph showing how everything connects through Flask, context, databases, and templates!**

**Seeds = Entry points, Connections = Data flow between components!** 🧠
