# 🔧 Debugging SOP - Standard Operating Procedure

**Last Updated**: 2025-12-25
**Purpose**: Step-by-step process for identifying, debugging, and auto-fixing issues in the Soulfra platform

---

## 📋 Quick Start Checklist

```bash
# Daily Health Check (30 seconds)
python3 check_templates.py

# Weekly Deep Scan (2 minutes)
python3 check_templates.py --detailed
python3 check_routes.py
python3 check_db.py
```

---

## 🩺 Phase 1: Run Health Checks

### 1.1 Template Health Check

**Command:**
```bash
python3 check_templates.py
```

**What it checks:**
- ✓ Total templates in `/templates` directory
- ✓ Templates actually used by Flask routes
- ✓ Templates referenced in code but missing files
- ✓ Unused templates (candidates for cleanup)

**Expected Output:**
```
=== Template Health Check ===
Total Templates: 78
Used Templates: 69
Unused Templates: 12
Missing Templates: 0  # ← THIS SHOULD BE 0

✓ All templates are healthy!
```

**If Missing Templates > 0:**
→ Proceed to Phase 2 (Identify Missing Files)

### 1.2 Route Health Check

**Command:**
```bash
# Check sitemap for route health
open http://localhost:5000/sitemap
```

**Visual Indicators:**
- 🟢 **Green Badge (✓)**: Route is healthy
- 🔵 **Blue Badge (API)**: API endpoint (no template needed)
- 🟡 **Yellow Badge (⚠️)**: Warning - may have issues
- 🔴 **Red Badge (✗)**: Error - missing template

**If you see red badges:**
→ Proceed to Phase 2

### 1.3 Database Health Check

**Command:**
```bash
python3 check_db.py
```

**What it checks:**
- Schema integrity
- Missing tables
- Foreign key constraints
- Index health

---

## 🔍 Phase 2: Identify Missing Files

### 2.1 Analyze check_templates.py Output

**Example problematic output:**
```
Missing Templates: 3
- ai_network_visualize.html (referenced in app.py:2099)
- ai_persona_detail.html (referenced in app.py:2137)
- brand_qr_stats.html (referenced in app.py:2193)
```

**Key Information:**
1. **Template name**: What file is missing
2. **Line number**: Where it's referenced in code
3. **Route context**: What functionality needs this template

### 2.2 Inspect the Route Code

**Command:**
```bash
# View the route that needs the template
grep -n "ai_network_visualize.html" app.py
```

**Look for:**
- Route decorator (`@app.route('/some-path')`)
- Function name
- What data is being passed to `render_template()`
- Expected variables in template context

**Example:**
```python
@app.route('/ai/network/visualize/<model_name>')
def ai_network_visualize(model_name):
    network = get_network_data(model_name)
    weights = network.get('weights', {})
    biases = network.get('biases', {})
    return render_template('ai_network_visualize.html',
                         model_name=model_name,
                         network=network,
                         weights=weights,
                         biases=biases)
```

### 2.3 Find a Similar Template (Pattern Matching)

**Strategy**: Find an existing template with similar functionality

**Command:**
```bash
# List all templates by category
ls -lh templates/ | grep -i "network\|debug\|visualize"
```

**Common Patterns:**

| Missing Template | Similar Pattern | Use As Base |
|-----------------|----------------|-------------|
| `*_detail.html` | Profile pages | `soul.html`, `brand_page.html` |
| `*_stats.html` | Analytics dashboards | `brand_status.html`, `sitemap.html` |
| `*_visualize.html` | Data displays | `ai_network_debug.html` |
| `*_edit.html` | Forms | `brand_upload.html`, `profile_edit.html` |
| `admin_*.html` | Tables/lists | `admin_souls.html` |

---

## 🛠️ Phase 3: Fix Issues Using Generators

### 3.1 Auto-Generate Template (Recommended)

**Command:**
```bash
# Generate template from similar pattern
python3 template_generator.py generate-page \
    --name "ai_network_visualize" \
    --type "visualization" \
    --base "ai_network_debug.html"
```

**What this does:**
1. Copies structure from base template
2. Updates title, headings, variable names
3. Preserves styling patterns
4. Creates new file in `/templates`

### 3.2 Manual Creation (When Generator Not Sufficient)

**Step-by-step:**

1. **Copy similar template as starting point:**
```bash
cp templates/ai_network_debug.html templates/ai_network_visualize.html
```

2. **Open in editor:**
```bash
# Use your preferred editor
code templates/ai_network_visualize.html
# or
nano templates/ai_network_visualize.html
```

3. **Update template structure:**

```html
{% extends "base.html" %}

{% block title %}[New Title] - {{ variable_name }}{% endblock %}

{% block content %}
<div class="container">
    <!-- Copy relevant sections from similar template -->
    <!-- Update variable names to match route context -->
    <!-- Preserve styling patterns -->
</div>

<style>
/* Copy and adapt CSS from similar template */
</style>

<script>
// Copy and adapt JavaScript if needed
</script>
{% endblock %}
```

4. **Key things to update:**
   - `{% block title %}` - Page title
   - Variable names - Match what route passes to template
   - Headings and text - Update to new context
   - Section IDs - Make unique
   - JavaScript function names - Avoid conflicts

5. **Verify template extends base:**
```html
{% extends "base.html" %}
```

### 3.3 Generate Missing Routes

**If you need a route too (not just template):**

```bash
# Auto-generate CRUD routes for a table
python3 route_generator.py generate \
    --table "qr_scans" \
    --include-api \
    --include-admin
```

**What this creates:**
- List view route
- Detail view route
- Create/Edit routes
- Delete route
- API endpoints (JSON)

---

## ✅ Phase 4: Verify Fixes

### 4.1 Re-run Health Check

**Command:**
```bash
python3 check_templates.py
```

**Expected:**
```
Missing Templates: 0  # ← Should be 0 now
```

### 4.2 Test in Browser

**Visit the route:**
```bash
# Start server if not running
python3 app.py

# Visit the fixed route
open http://localhost:5000/[route-path]
```

**Check for:**
- ✓ Page loads without 500 error
- ✓ Template renders correctly
- ✓ No Jinja2 template errors
- ✓ Variables display properly
- ✓ Styling looks consistent

### 4.3 Check Sitemap Health Badge

**Visit:**
```
http://localhost:5000/sitemap
```

**Find the route and verify:**
- Badge should be 🟢 Green (✓) for regular routes
- Badge should be 🔵 Blue (API) for API endpoints
- No more 🔴 Red (✗) badges

---

## 🤖 Auto-Fix Scripts

### Auto-Heal Missing Templates

**Command:**
```bash
# Automatically generate all missing templates using AI pattern matching
python3 auto_heal_templates.py
```

**What it does:**
1. Runs `check_templates.py` to find missing templates
2. For each missing template:
   - Analyzes the route code
   - Finds the most similar existing template
   - Generates new template using pattern
   - Saves to `/templates`
3. Re-runs health check
4. Reports results

**Safety:** Creates backups before modifying files

### Auto-Fix Route Errors

**Command:**
```bash
# Fix common route issues
python3 auto_fix_routes.py
```

**Fixes:**
- Missing `render_template()` imports
- Incorrect template names
- Missing route decorators
- Typos in template paths

---

## 📊 Monitoring Checklist

### Daily (30 seconds)
- [ ] Run `python3 check_templates.py`
- [ ] Check for 0 missing templates
- [ ] Verify server starts without errors

### Weekly (5 minutes)
- [ ] Visit `/sitemap` and check for red badges
- [ ] Run `python3 check_db.py`
- [ ] Review unused templates (cleanup candidates)
- [ ] Check error logs: `tail -f logs/error.log`

### Monthly (15 minutes)
- [ ] Run full test suite
- [ ] Review and update generators
- [ ] Clean up unused templates
- [ ] Update documentation
- [ ] Review auto-heal script effectiveness

---

## 🚨 Common Issues & Solutions

### Issue: "Template not found" error

**Symptoms:**
```
jinja2.exceptions.TemplateNotFound: ai_network_visualize.html
```

**Solution:**
1. Run `python3 check_templates.py` to confirm missing
2. Find similar template: `ls templates/ | grep -i network`
3. Generate new template: `python3 template_generator.py generate-page --name "ai_network_visualize" --base "ai_network_debug.html"`
4. Verify: Re-run health check

---

### Issue: Missing template variables

**Symptoms:**
```
jinja2.exceptions.UndefinedError: 'model_name' is undefined
```

**Solution:**
1. Check what route passes to template:
```bash
grep -A 10 "render_template('ai_network_visualize.html'" app.py
```

2. Update template to use correct variable names:
```html
<!-- If route passes 'model_name', use it in template -->
<h1>{{ model_name }}</h1>
```

3. Add safety checks for optional variables:
```html
{% if variable %}{{ variable }}{% else %}N/A{% endif %}
```

---

### Issue: Unused templates cluttering `/templates`

**Symptoms:**
```
Unused Templates: 25
```

**Solution:**
1. Review unused list: `python3 check_templates.py --list-unused`
2. Move to archive folder (don't delete yet):
```bash
mkdir -p templates/_archive
mv templates/old_template.html templates/_archive/
```
3. Test for 1 week
4. If no issues, safe to delete

---

## 🎯 Best Practices

### 1. Always Use Existing Patterns
- **DON'T**: Create totally new template structures
- **DO**: Copy similar templates and adapt them
- **WHY**: Maintains consistency, faster development

### 2. Run Health Checks Before Committing
```bash
# Pre-commit check
python3 check_templates.py && \
python3 check_routes.py && \
git commit -m "your message"
```

### 3. Use Generators Over Manual Creation
- **Generators are**: Consistent, tested, faster
- **Manual creation**: Error-prone, inconsistent styling
- **Exception**: Complex custom pages with unique functionality

### 4. Document New Patterns
- If you create a unique template, add it to the pattern matching table
- Update `template_generator.py` with new patterns
- Add examples to this SOP

---

## 🔗 Related Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `check_templates.py` | Health checker | Daily monitoring |
| `template_generator.py` | Generate templates | When missing templates |
| `route_generator.py` | Generate routes | When adding new features |
| `route_discovery.py` | Auto-discover routes | For sitemap updates |
| `auto_heal_templates.py` | Auto-fix missing templates | Weekly maintenance |
| `WIDGET_QUICKSTART.md` | Soul Assistant docs | When building widgets |

---

## 📞 Getting Help

### Template Issues
1. Check this SOP first
2. Review similar existing templates
3. Use template generator
4. Check `/sitemap` for examples

### Route Issues
1. Visit `/sitemap` for all routes
2. Check `route_discovery.py` for auto-generation
3. Review `app.py` for route patterns

### Database Issues
1. Run `python3 check_db.py`
2. Review schema in `schema.sql`
3. Check migrations history

---

## 🎨 Future Enhancements

### Planned Features (See Feature Factory Plan)
- [ ] Visual template browser (Pinterest-style)
- [ ] One-click template generation from UI
- [ ] Real-time health monitoring dashboard
- [ ] AI-powered pattern matching
- [ ] Automated weekly health reports
- [ ] Template version control

---

**Remember**: The goal is **automation** and **self-healing**. If you find yourself doing something manually more than twice, create a generator for it!
