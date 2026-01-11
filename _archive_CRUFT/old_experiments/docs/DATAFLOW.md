# Data Flow Architecture

**Understanding: "Color Spectrum Vertically, Ports/Formats Horizontally"**

---

## The Big Picture

Think of Soulfra like a **prism** that splits white light into a spectrum:

```
         WHITE LIGHT (User Input)
                  │
                  ↓
            ┌─────────┐
            │  PRISM  │  ← Soulfra Platform
            │ (Split) │
            └─────────┘
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
     RED       GREEN      BLUE    ← Different Outputs
   (JSON)     (CSV)      (HTML)
```

**VERTICAL = Data Transformation** (white → spectrum)
**HORIZONTAL = Output Formats** (red, green, blue wavelengths)

---

## Vertical Axis: Data Transformation Layers

**From raw input → final output (like colors in a spectrum)**

```
LAYER 0: Raw Input
┌───────────────────────────────────────────┐
│  User clicks color square                 │
│  RGB(255, 0, 0)                            │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 1: Normalization
┌───────────────────────────────────────────┐
│  Normalize RGB to [0, 1]                   │
│  [1.0, 0.0, 0.0]                           │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 2: Feature Extraction
┌───────────────────────────────────────────┐
│  RGB → HSV conversion                      │
│  RGB → Temperature score                   │
│  RGB → Dominance calculation               │
│                                            │
│  Features: [H, S, V, temp, r_dom, ...]     │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 3: Neural Network
┌───────────────────────────────────────────┐
│  Input Layer (3 neurons: R, G, B)         │
│      ↓                                     │
│  Hidden Layer (6 neurons)                  │
│      ↓                                     │
│  Output Layer (1 neuron: warm prob)        │
│                                            │
│  Prediction: 0.9996 (WARM)                 │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 4: Interpretation
┌───────────────────────────────────────────┐
│  Threshold: > 0.5 = WARM                   │
│  Confidence: 0.9996 → 99.96%               │
│  Reasoning: "Hue 0° = Red = Warm"          │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 5: Formatting
┌───────────────────────────────────────────┐
│  Apply format_converter.py                 │
│  JSON / CSV / TXT / HTML / RTF / Binary    │
└───────────────────────────────────────────┘
         │
         ↓
LAYER 6: Delivery
┌───────────────────────────────────────────┐
│  HTTP Response                             │
│  Port 5001, 8888, etc.                     │
└───────────────────────────────────────────┘
```

**Like a color spectrum:**
- Layer 0 = White light (raw input)
- Layer 1-2 = Prism (feature extraction)
- Layer 3-4 = Diffraction (neural network)
- Layer 5-6 = Rainbow (multiple formats)

---

## Horizontal Axis: Output Formats

**Same data, different representations (like wavelengths)**

```
         PREDICTION DATA
         {"prediction": "WARM", "confidence": 0.9996, ...}
                         │
         ┌───────────────┼───────────────┬───────────────┬──────────────┐
         ↓               ↓               ↓               ↓              ↓
      JSON            CSV             TXT            HTML           Binary
   (Machines)    (Spreadsheets)   (Humans)       (Browsers)      (Efficient)

   Port 5001      Port 8888       Port 8888      Port 8888       Port 8888
   ?format=json   ?format=csv     ?format=txt    ?format=html    ?format=bin
```

**Different "wavelengths" of the same information:**

| Format | Wavelength Analogy | Use Case |
|--------|-------------------|----------|
| JSON | Infrared (invisible, machine-readable) | APIs, automation |
| CSV | Red (structured, spreadsheet-friendly) | Excel, data analysis |
| TXT | Yellow (human-readable) | Logs, documentation |
| HTML | Green (visual) | Web browsers |
| RTF | Blue (formatted text) | Word processors |
| Binary | Ultraviolet (compressed) | Efficient storage |

---

## The Complete Flow: Vertical × Horizontal

```
USER INPUT
    │
    ├─→ Port 5001 (Flask)          ├─→ Port 8888 (stdlib)       ├─→ Port 8000 (static)
    │       │                       │       │                     │       │
    │       ↓                       │       ↓                     │       ↓
    │   SQLite DB                   │   SQLite DB                 │   Filesystem
    │   soulfra.db                  │   (same DB)                 │   docs/
    │       │                       │       │                     │       │
    │       ↓                       │       ↓                     │       ↓
    │   Python Features             │   Python Features           │   HTML files
    │   (HSV, temp, etc)            │   (HSV, temp, etc)          │   (pre-built)
    │       │                       │       │                     │       │
    │       ↓                       │       ↓                     │       │
    │   Neural Network              │   Neural Network            │   (No processing)
    │   color_network.json          │   color_network.json        │       │
    │       │                       │       │                     │       │
    │       ↓                       │       ↓                     │       ↓
    │   Jinja2 Templates            │   String Templates          │   Static HTML
    │   (Flask renders)             │   (Regex replaces)          │   (Already rendered)
    │       │                       │       │                     │       │
    │       └───────────────────────┴───────┴─────────────────────┴───────┘
    │                                       │
    │                                       ↓
    │                              FORMAT CONVERTER
    │                              (Horizontal split)
    │                                       │
    │                       ┌───────────────┼───────────────┬────────┐
    │                       ↓               ↓               ↓        ↓
    └─────────────────→  JSON            CSV             TXT      HTML ...
                        (API)         (Export)        (Logs)    (Web)
```

---

## Diffusion Model Analogy

You mentioned "diffusion and wordmaps" - here's how Soulfra relates:

### Forward Diffusion (Input → Features)
```
Raw RGB → Add "noise" (features) → Latent space

RGB(255,0,0)
    ↓ (add HSV features)
[1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, ...]
    ↓ (add temperature)
[1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, ...]
    ↓ (add dominance)
[1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.33, 0.33, 0.33]
```

### Reverse Diffusion (Features → Prediction)
```
Latent features → Neural network → Denoised output

[12 features] → [6 hidden neurons] → [1 output: WARM]
```

**Like Stable Diffusion:**
- Text → Features (tokenization, embeddings)
- Features → Image (denoising network)

**Soulfra:**
- RGB → Features (HSV, temperature, dominance)
- Features → Prediction (neural network)

---

## Word Embeddings Analogy

**Traditional word embeddings:**
```
"king" → [0.2, 0.5, 0.1, ...]  (300-dim vector)
"queen" → [0.3, 0.4, 0.1, ...]
```

**Soulfra color embeddings:**
```
RGB(255,0,0) → [H:0°, S:100%, V:100%, temp:100%, ...]  (12-dim vector)
RGB(0,0,255) → [H:240°, S:100%, V:100%, temp:0%, ...]
```

**Same concept:**
- Compress complex input (word/color) into feature vector
- Neural network operates on vector
- Output is classification/prediction

---

## Port Communication (Or Lack Thereof)

**Ports DON'T talk to each other:**

```
Port 5001         Port 8888         Port 8000
(Flask)           (stdlib)          (static)
   │                 │                 │
   │                 │                 │
   └────────┬────────┴─────────────────┘
            │
      soulfra.db
   (shared database)
```

**Each port is independent:**
- Port 5001 → Reads DB → Processes → Returns
- Port 8888 → Reads same DB → Processes → Returns
- Port 8000 → Serves pre-built files → Returns

**No inter-port communication!**
- They don't call each other's APIs
- They don't share memory
- They only share the database file

**Like microservices:**
- Multiple services (ports)
- Single data source (SQLite)
- Independent processing

---

## Tier System Architecture (Stdlib-Only Approach)

**NEW PATTERN: Zero External Dependencies**

We're rebuilding everything using a consistent **tier system** where each layer uses ONLY Python stdlib:

```
TIER 0: Binary/Raw Data
├── HTTP requests (http.server)
├── File I/O (open(), read())
└── Database queries (sqlite3)

TIER 1: Data Layer (READ)
├── sqlite3.connect('soulfra.db')
├── cursor.execute('''SELECT ...''')
├── Pure SQL queries
└── No ORM, no Flask db helpers

TIER 2: Transform Layer (PROCESS)
├── Pure Python list/dict operations
├── json.loads(), json.dumps()
├── Mathematical transformations
└── No external libraries

TIER 3: Format Layer (OUTPUT)
├── String templates (f-strings)
├── Regex-based templating
├── format_converter.py
└── No Jinja2, no template engines
```

### Example: Dashboard on Port 8888 (Stdlib-Only)

**soulfra_zero.py:930-1154** - `/dashboard` route

```python
@router.route('/dashboard')
def dashboard(query_params, post_data):
    # TIER 1: Data (sqlite3 stdlib)
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, model_name, description, input_size, hidden_sizes,
               output_size, model_data, trained_at
        FROM neural_networks
        ORDER BY trained_at DESC
    ''')
    networks_raw = cursor.fetchall()
    conn.close()

    # TIER 2: Transform (pure Python)
    networks = []
    for net in networks_raw:
        model_data = json.loads(net[6]) if net[6] else {}
        accuracy_history = model_data.get('accuracy_history', [])

        networks.append({
            'name': net[1],
            'accuracy': f"{accuracy_history[-1] * 100:.2f}" if accuracy_history else "0",
            # ... more transformations
        })

    # TIER 3: Format (string templates)
    network_cards_html = ''
    for net in networks:
        network_cards_html += f'''
        <div class="network-card">
            <div class="network-name">{net['name']}</div>
            <div class="network-stat-value">{net['accuracy']}%</div>
        </div>
        '''

    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title></head>
    <body>
        {network_cards_html}
    </body>
    </html>
    '''

    return ('text/html', html)
```

**Benefits:**
- ✅ Zero external dependencies (no pip install)
- ✅ No supply chain vulnerabilities
- ✅ Easy to audit and understand
- ✅ Runs anywhere Python runs
- ✅ Consistent pattern across all routes

### OLD vs NEW Approach

**OLD (Flask + Jinja2) - Port 5001:**
```python
# app.py
from flask import Flask, render_template, get_db

@app.route('/dashboard')
def dashboard():
    db = get_db()  # Flask helper
    networks = db.execute('SELECT ...').fetchall()
    return render_template('dashboard.html', networks=networks)  # Jinja2
```

**Problems:**
- ❌ External dependencies (Flask, Jinja2)
- ❌ Two different templating systems
- ❌ Flask database helpers not working
- ❌ Architectural inconsistency

**NEW (Stdlib Only) - Port 8888:**
```python
# soulfra_zero.py
import sqlite3

@router.route('/dashboard')
def dashboard(query_params, post_data):
    conn = sqlite3.connect('soulfra.db')  # Direct connection
    # ... process data ...
    html = f'<html>{content}</html>'  # f-string template
    return ('text/html', html)
```

**Benefits:**
- ✅ Consistent with rest of port 8888
- ✅ No external dependencies
- ✅ Direct database access works
- ✅ One templating approach (f-strings)

### Tier System in Action

**All port 8888 routes follow this pattern:**

| Route | TIER 1 (Data) | TIER 2 (Transform) | TIER 3 (Format) |
|-------|--------------|-------------------|----------------|
| `/api/classify-color` | Load neural network JSON | Run prediction | format_converter.py |
| `/tiers` | N/A | Demo data | String template |
| `/dashboard` | Query neural_networks table | Build stats/charts | f-string HTML |

**Consistency = Reliability**

Every route uses the same pattern, making the codebase:
- Easy to understand
- Easy to debug
- Easy to extend
- Easy to audit

---

## Format Selection: Query Parameter

**Horizontal axis selection via URL:**

```bash
# Default: JSON
curl http://localhost:8888/api/classify-color \
  -d '{"r":255,"g":0,"b":0}'
# Returns: JSON

# Explicit JSON
curl http://localhost:8888/api/classify-color?format=json \
  -d '{"r":255,"g":0,"b":0}'

# CSV format
curl http://localhost:8888/api/classify-color?format=csv \
  -d '{"r":255,"g":0,"b":0}'
# Returns: r,g,b,prediction,confidence
#          255,0,0,WARM,0.9996

# Plain text
curl http://localhost:8888/api/classify-color?format=txt \
  -d '{"r":255,"g":0,"b":0}'
# Returns: Prediction: WARM
#          Confidence: 99.96%

# HTML card
curl http://localhost:8888/api/classify-color?format=html \
  -d '{"r":255,"g":0,"b":0}'
# Returns: <div class="data-card">...</div>

# Binary (efficient)
curl http://localhost:8888/api/classify-color?format=binary \
  -d '{"r":255,"g":0,"b":0}'
# Returns: \xff\x00\x00\x3f\x7f\xe1\x48 (8 bytes)
```

**Single endpoint, multiple representations!**

---

## Data Persistence Layers

**Where data lives:**

```
LAYER 1: SQLite Database (soulfra.db)
├── posts table (markdown content)
├── users table (accounts)
├── comments table (discussions)
└── reasoning_threads table (AI verdicts)

LAYER 2: JSON Files (neural networks)
├── color_network.json (trained weights)
├── xor_network.json (XOR demo)
└── *_classifier.json (future models)

LAYER 3: Filesystem (static files)
├── static/style.css (CSS)
├── static/avatars/ (generated images)
├── docs/ (built static site)
└── themes/ (CSS themes)

LAYER 4: Memory (runtime state)
├── Flask session (user state)
├── Loaded neural networks (in RAM)
└── Template cache (rendered HTML)
```

**Vertical flow through layers:**
```
User request → SQLite → Python → Neural Network → Memory → Format → Response
```

---

## The "Prism" Analogy Summary

```
                  ╭─────────────────╮
                  │  USER INPUT     │  ← White Light
                  │  (Any request)  │
                  ╰────────┬────────╯
                           │
                           ↓
                  ╭─────────────────╮
                  │    SOULFRA      │  ← Prism
                  │   (Platform)    │
                  │                 │
                  │  • SQLite       │
                  │  • Features     │
                  │  • Neural Net   │
                  │  • Converter    │
                  ╰────────┬────────╯
                           │
           ┌───────────────┼───────────────┐
           ↓               ↓               ↓
        JSON             CSV             HTML        ← Rainbow
     (Infrared)        (Red)           (Green)      (Different wavelengths)
```

**VERTICAL = Transformation** (light → spectrum)
**HORIZONTAL = Representation** (wavelengths)

---

## Next Steps

**To add new formats:**
1. Add to `format_converter.py` (e.g., `to_xml()`, `to_yaml()`)
2. Update `soulfra_zero.py` to support `?format=xml`
3. Test with `test_formats.sh`

**To add new endpoints:**
1. Create route in `soulfra_zero.py`
2. Extract features (vertical axis)
3. Use `FormatConverter` for output (horizontal axis)

**To add new ports:**
1. Clone server to new port
2. Point to same `soulfra.db`
3. Implement custom processing
4. Return results in multiple formats

---

**The key insight: Data flows VERTICALLY (transformation), outputs flow HORIZONTALLY (formats)**

Just like light through a prism! 🌈
