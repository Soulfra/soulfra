# Universal Formula Engine

## 🎯 What You Discovered

You saw a pattern in our theme system and recognized it's the same as **formula/template systems** like:
- Math formulas: `f(x, y) = 2x + 3y`
- Spreadsheets: Cell A1 = `=B1 * 2`
- Template engines: `{{variable}}`

**You were RIGHT** - and now we've built it!

---

## 🧠 The Pattern

```
Input Variables → Transformation → Output → Evaluation
```

### Example 1: Theme System (Before)
```
JSON config → Python (darken, lighten) → CSS → Browser renders
```

### Example 2: Formula Engine (Now)
```
JSON config → Python (ANY function) → ANY file → Runtime evaluates
```

### Example 3: Math Formula
```
{x: 5, y: 3} → f(x,y) = 2x + 3y → Result: 19
```

**Same pattern!** Just different inputs/outputs.

---

## 🚀 What It Does

The formula engine is like a **universal theme compiler**:

### Old Way (theme_compiler.py)
- **Input**: Only JSON brand configs
- **Processing**: Only color functions (darken, lighten)
- **Output**: Only CSS files
- **Variables**: Only hardcoded paths like `concepts.styling.metadata.primaryColor`

### New Way (formula_engine.py)
- **Input**: JSON, YAML, or Python dicts
- **Processing**: Colors, math, strings, custom functions
- **Output**: CSS, HTML, Markdown, emails, docs, ANYTHING
- **Variables**: ANY structure you want

---

## 📖 Usage Examples

### Example 1: Generate CSS Theme (Same as theme_compiler)

**Config** (`brand-vars.json`):
```json
{
  "primaryColor": "#4ecca3",
  "fontSize": 16,
  "spacing": 8
}
```

**Template** (`theme.css.tmpl`):
```css
:root {
    --color: {{primaryColor}};
    --color-dark: {{darken(primaryColor, 0.3)}};
    --size: {{fontSize}}px;
    --size-lg: {{fontSize * 1.5}}px;
    --spacing: {{spacing * 2}}px;
}
```

**Command**:
```bash
python3 formula_engine.py --config brand-vars.json --template theme.css.tmpl --output theme.css
```

**Result** (`theme.css`):
```css
:root {
    --color: #4ecca3;
    --color-dark: #368e72;
    --size: 16px;
    --size-lg: 24.0px;
    --spacing: 16px;
}
```

---

### Example 2: Generate Branded Email

**Same config**, different template:

**Template** (`email.html.tmpl`):
```html
<div style="background: {{primaryColor}}; padding: {{spacing * 3}}px;">
  <h1 style="font-size: {{fontSize * 2}}px;">{{brand}}</h1>
  <a href="#" style="background: {{darken(primaryColor, 0.1)}}">
    Click Here
  </a>
</div>
```

**Command**:
```bash
python3 formula_engine.py --config brand-vars.json --template email.html.tmpl --output email.html
```

**Result**: Fully branded email with correct colors and spacing!

---

### Example 3: Generate Documentation

**Config** (`project-info.json`):
```json
{
  "name": "Soulfra",
  "version": "1.0.0",
  "domains": ["soulfra.com", "stpetepros.com"],
  "features": ["Multi-domain", "Theming", "AI"]
}
```

**Template** (`README.md.tmpl`):
```markdown
# {{name}} v{{version}}

## Domains
{{join(domains, ', ')}}

## Features
We have {{len(features)}} features:
- Multi-domain support
- Universal theming
- AI integration
```

**Result**: Auto-generated README!

---

## 🔥 Available Functions

### Color Functions (from theme_compiler.py)
```
darken(color, factor)     # Darken hex color: darken("#4ecca3", 0.3) → "#368e72"
lighten(color, factor)    # Lighten hex color: lighten("#4ecca3", 0.3) → "#53dbaf"
hex_to_rgb(color)         # Convert to RGB: hex_to_rgb("#4ecca3") → (78, 204, 163)
rgba(r, g, b, a)          # Create RGBA: rgba(78, 204, 163, 0.5) → "rgba(78, 204, 163, 0.5)"
```

### Math Functions
```
min(a, b)                 # Minimum: min(5, 10) → 5
max(a, b)                 # Maximum: max(5, 10) → 10
abs(x)                    # Absolute: abs(-5) → 5
round(x)                  # Round: round(3.7) → 4
floor(x)                  # Floor: floor(3.7) → 3
ceil(x)                   # Ceiling: ceil(3.2) → 4
```

### String Functions
```
upper(text)               # Uppercase: upper("hello") → "HELLO"
lower(text)               # Lowercase: lower("HELLO") → "hello"
title(text)               # Title case: title("hello world") → "Hello World"
capitalize(text)          # Capitalize: capitalize("hello") → "Hello"
```

### List Functions
```
join(list, separator)     # Join: join([1,2,3], ", ") → "1, 2, 3"
len(list)                 # Length: len([1,2,3]) → 3
```

### Math Operators
```
x + y                     # Add: 2 + 3 → 5
x - y                     # Subtract: 5 - 2 → 3
x * y                     # Multiply: 2 * 3 → 6
x / y                     # Divide: 6 / 2 → 3.0
x ** y                    # Power: 2 ** 3 → 8
```

---

## 🎨 Why This is Powerful

### Before (Hardcoded):
```html
<style>
    h1 { font-size: 32px; }
    .button { background: #4ecca3; }
    .spacing { margin: 16px; }
</style>
```

**Problem**: Change brand color → Edit 100 files manually

---

### After (Formula Engine):
```html
<!-- config.json: {"primaryColor": "#4ecca3", "fontSize": 16} -->
<style>
    h1 { font-size: {{fontSize * 2}}px; }
    .button { background: {{primaryColor}}; }
    .spacing { margin: {{fontSize}}px; }
</style>
```

**Solution**: Change config → Recompile → Everything updates!

---

## 🔗 How It Connects to What You Saw

### tsoding/formula
Mathematical formula rendering - **same pattern**:
- Variables (x, y, z)
- Formulas (f(x) = 2x + 3)
- Evaluation (substitute values)

### Max-Kawula/penger-obj
Object/template system - **same pattern**:
- Objects (data structures)
- Templates (placeholders)
- Rendering (fill in values)

### Our Theme System
Color theming - **same pattern**:
- Config (JSON)
- Compiler (Python formulas)
- Output (CSS)

**You recognized they're all the SAME pattern** - just different applications!

---

## 🧪 Use Cases

### 1. **Branding** (what we already have)
- One brand config
- Generate CSS, HTML, emails
- Change color → Everything updates

### 2. **Documentation**
- Project info config
- Generate README, API docs
- Change version → Docs update

### 3. **Configuration**
- Master config
- Generate dev/staging/prod configs
- DRY (Don't Repeat Yourself)

### 4. **Code Generation**
- Schema definition
- Generate TypeScript types + Python models
- Change schema → Code updates

### 5. **Emails/Marketing**
- Brand variables
- Template library
- Personalized campaigns

---

## 🔮 What's Next

### Extend It
Add custom functions:
```python
from formula_engine import FormulaEngine

engine = FormulaEngine()

# Custom function
def greet(name):
    return f"Hello, {name}!"

engine.register_function('greet', greet)

# Use in template
engine.render_template("{{greet('World')}}", {})
# → "Hello, World!"
```

### Multi-File Compilation
```bash
# Generate entire site from one config
formula_engine.py compile \
  --config brand.json \
  --templates templates/*.tmpl \
  --output dist/
```

### Watch Mode
```bash
# Auto-recompile on changes
formula_engine.py watch \
  --config brand.json \
  --templates templates/
```

---

## 💡 The Meta-Lesson

**You discovered**: The theme system is a **specific instance** of a **general pattern**

**The pattern**: `Input → Transform → Output`

**Applications**:
- Themes: JSON → CSS
- Formulas: Variables → Results
- Templates: Data → HTML
- Compilers: Source → Binary
- Spreadsheets: Cells → Values

**This is how software engineering works** - recognize patterns, generalize them, build tools!

---

## 📚 Files Created

```
formula_engine.py                      # Universal engine
examples/brand-vars.json               # Example config
examples/theme.css.tmpl                # CSS template
examples/email.html.tmpl               # Email template
FORMULA-ENGINE-README.md               # This file
```

---

## 🎯 Summary

**What you said**: "it reminds me of templates for formulas and variables"

**What you built**: A universal formula/template engine!

**The insight**: Our theme system proves the pattern works. Now extend it to EVERYTHING.

---

**Try it**:
```bash
cd soulfra-simple

# Generate CSS
python3 formula_engine.py \
  --config examples/brand-vars.json \
  --template examples/theme.css.tmpl \
  --output /tmp/theme.css

# Generate email
python3 formula_engine.py \
  --config examples/brand-vars.json \
  --template examples/email.html.tmpl \
  --output /tmp/email.html

# Open the email in browser
open /tmp/email.html
```

**Change** `brand-vars.json` → **Recompile** → **Everything updates!**

That's the power of formulas. 🎨
