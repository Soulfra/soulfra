# Simple Workflow - Clean Lines of Action

**Created:** December 31, 2024
**Purpose:** Dead simple explanation of how domains work in your system

---

## The Confusion (What the fuck is going on?)

You have **TWO SEPARATE PLACES** for domain stuff:

```
Place 1: DATABASE (soulfra.db)
└── Stores domain INFORMATION (name, category, etc.)

Place 2: OUTPUT FOLDER (output/)
└── Stores domain HTML FILES (the actual websites)
```

**The problem:** They're NOT connected yet!

---

## The Clean Lines of Action

### Line 1: Add Domain to Database

**WHERE:** http://localhost:5001/admin/domains

**WHAT YOU DO:**
1. Enter domain name: "howtocookathome.com"
2. Click "Add Domain"
3. Ollama researches it
4. Saves to database

**RESULT:**
- Domain added to `soulfra.db` → brands table
- You can now see it in domain manager
- But NO HTML files exist yet!

---

### Line 2: Generate HTML for Domain

**WHERE:** http://localhost:5001/templates/browse

**WHAT YOU DO:**
1. Open template browser
2. Pick a template
3. Prompt Ollama: "Generate homepage for howtocookathome.com"
4. Click "Deploy"

**RESULT:**
- HTML saved to `output/howtocookathome/index.html`
- Now the domain HAS a website!

---

### Line 3: Push to GitHub

**WHERE:** Terminal (command line)

**WHAT YOU DO:**
```bash
cd output/howtocookathome
git init
git add .
git commit -m "Initial site"
gh repo create howtocookathome --public
git push -u origin main
```

**RESULT:**
- Website now on GitHub
- Can deploy to GitHub Pages
- Domain goes live!

---

## The Visual Flow (How It All Connects)

```
┌──────────────────────────────────────────────────────┐
│ STEP 1: Add to Database                              │
│ http://localhost:5001/admin/domains                  │
│                                                       │
│ Enter: howtocookathome.com                           │
│   ↓                                                   │
│ Ollama researches                                    │
│   ↓                                                   │
│ Saved to: soulfra.db → brands table                  │
│   ↓                                                   │
│ You now see it in domain list                        │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│ STEP 2: Generate HTML                                │
│ http://localhost:5001/templates/browse               │
│                                                       │
│ Pick template                                        │
│   ↓                                                   │
│ Ollama generates homepage                            │
│   ↓                                                   │
│ Click "Deploy to howtocookathome"                    │
│   ↓                                                   │
│ Saved to: output/howtocookathome/index.html          │
│   ↓                                                   │
│ Website now exists!                                  │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│ STEP 3: Push to GitHub                               │
│ Terminal                                             │
│                                                       │
│ cd output/howtocookathome                            │
│ git init                                             │
│ git add .                                            │
│ git commit -m "Initial site"                         │
│ gh repo create howtocookathome --public              │
│ git push                                             │
│   ↓                                                   │
│ Live on GitHub!                                      │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│ STEP 4: Deploy to Web                                │
│ GitHub Pages settings                                │
│                                                       │
│ Enable Pages → main branch                           │
│   ↓                                                   │
│ Live at: username.github.io/howtocookathome          │
│   ↓                                                   │
│ Point DNS: howtocookathome.com → GitHub Pages        │
│   ↓                                                   │
│ Website LIVE!                                        │
└──────────────────────────────────────────────────────┘
```

---

## The File Structure (Where Shit Lives)

```
soulfra-simple/
│
├── soulfra.db  ← DATABASE (domain info)
│   └── brands table:
│       ├── id=1, name="Soulfra", domain="soulfra.com"
│       ├── id=2, name="DeathToData", domain="deathtodata.com"
│       ├── id=3, name="Calriven", domain="calriven.com"
│       └── id=4, name="HowToCookAtHome", domain="howtocookathome.com"
│
├── output/  ← HTML FILES (actual websites)
│   ├── soulfra/
│   │   ├── index.html  ✅
│   │   ├── feed.xml    ✅
│   │   ├── .git/       ✅
│   │   └── post/
│   │       ├── post1.html
│   │       └── post2.html
│   │
│   ├── calriven/
│   │   ├── index.html  ✅
│   │   └── .git/       ✅
│   │
│   ├── deathtodata/
│   │   ├── index.html  ✅
│   │   └── .git/       ✅
│   │
│   └── howtocookathome/  ← DOESN'T EXIST YET ❌
│       (need to generate!)
│
├── templates/  ← TEMPLATES (for generating HTML)
│   ├── template_browser.html
│   └── brand_template/
│       ├── index.tmpl
│       └── blog.tmpl
│
└── app.py  ← THE GLUE (connects database to HTML)
```

---

## The Current Status (What Works, What Doesn't)

### ✅ WORKS:

**1. Add Domain to Database**
- Go to: http://localhost:5001/admin/domains
- Enter domain name
- Ollama researches it
- Saves to database

**2. Generate HTML with Templates**
- Go to: http://localhost:5001/templates/browse
- Pick template
- Ollama fills it with content
- See preview

**3. View Existing Websites**
- `output/soulfra/index.html` exists ✅
- `output/calriven/index.html` exists ✅
- `output/deathtodata/index.html` exists ✅

### ❌ DOESN'T WORK YET:

**1. Deploy Button Doesn't Know Domain**
- Template browser has "Deploy" button
- But doesn't know WHICH domain to deploy to
- Need dropdown: "Deploy to which domain?"

**2. No Status Indicator**
- Domain manager doesn't show: "✅ Has HTML" vs "❌ No HTML"
- Can't tell which domains need websites generated

**3. No "Generate Website" Button**
- Have to manually go to template browser
- Should have button: "Generate Website for this domain"
- One-click flow: domain → template → deploy

---

## The Simple Fix (What We're Building)

### Fix 1: Add Domain Dropdown to Template Browser

**Before:**
```html
<button>Deploy</button>  ← Where does it go?
```

**After:**
```html
<select id="target-domain">
  <option>howtocookathome</option>
  <option>soulfra</option>
  <option>calriven</option>
</select>
<button>Deploy</button>  ← Now knows where to save!
```

### Fix 2: Show Status in Domain Manager

**Before:**
```
Domain: howtocookathome.com
Category: cooking
```

**After:**
```
Domain: howtocookathome.com
Category: cooking
Status: ❌ No website generated yet
[Generate Website]  ← Click to create HTML
```

### Fix 3: One-Click Website Generation

**Before:**
```
1. Go to domain manager
2. Manually open template browser
3. Generate HTML
4. Remember which domain it's for
5. Save somewhere
```

**After:**
```
1. Click "Generate Website" in domain manager
2. Template browser opens PRE-FILLED for that domain
3. Ollama generates homepage
4. Click "Deploy" → Automatically saves to output/howtocookathome/
5. Done!
```

---

## Example: Adding a New Domain (The Complete Flow)

### Scenario: You want to add "healthytips.com"

**Step 1: Add to Database**
```
1. Visit: http://localhost:5001/admin/domains
2. Enter: healthytips.com
3. Click "Research with Ollama"
4. Ollama suggests:
   - Category: health
   - Emoji: 💪
   - Tagline: "Daily health tips for busy people"
5. Click "Add Domain"
6. Now in database! (soulfra.db → brands table)
```

**Step 2: Generate Website**
```
1. Click "Generate Website" button (NEW!)
2. Template browser opens
3. Pre-filled with:
   - Brand: HealthyTips
   - Emoji: 💪
   - Category: health
4. Prompt Ollama: "Write homepage about daily health tips"
5. Ollama generates full HTML
6. Preview looks good
7. Domain dropdown shows: "healthytips"
8. Click "Deploy"
9. Saved to: output/healthytips/index.html
```

**Step 3: Create Git Repo**
```bash
cd output/healthytips
git init
git add .
git commit -m "Generated homepage with Ollama"
```

**Step 4: Push to GitHub**
```bash
gh repo create healthytips --public
git push -u origin main
```

**Step 5: Enable GitHub Pages**
```
1. Go to: github.com/yourname/healthytips
2. Settings → Pages
3. Source: main branch
4. Save
5. Live at: yourname.github.io/healthytips
```

**Step 6: Point DNS**
```
1. Buy healthytips.com (if you don't own it)
2. Add DNS record:
   - Type: CNAME
   - Name: @
   - Value: yourname.github.io
3. Wait for DNS propagation
4. Live at: healthytips.com!
```

---

## The Database Records (How to View Them)

### Method 1: SQLite Command Line

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# View all domains
sqlite3 soulfra.db "SELECT * FROM brands"

# View domains with their chat history
sqlite3 soulfra.db "
  SELECT b.name, COUNT(dc.id) as num_conversations
  FROM brands b
  LEFT JOIN domain_conversations dc ON b.id = dc.brand_id
  GROUP BY b.id
"

# View domains with Ollama suggestions
sqlite3 soulfra.db "
  SELECT b.name, ds.suggestion_type, ds.title
  FROM brands b
  JOIN domain_suggestions ds ON b.id = ds.brand_id
  WHERE ds.status = 'pending'
"
```

### Method 2: Web UI (Admin Panel)

**Current:** http://localhost:5001/admin/domains
- Shows list of all domains
- But doesn't show content/HTML status

**What We're Building:**
- Click domain name → See full details
- Shows: Database info + HTML files + Git status + Ollama chats
- Visual dashboard of everything

---

## The Integration (How Database ↔ HTML Connect)

### Current State (Disconnected):

```
DATABASE                     HTML FILES
┌──────────────┐            ┌──────────────┐
│ soulfra.db   │            │ output/      │
│              │            │              │
│ brands:      │     ❌     │ soulfra/     │
│ - soulfra    │   (no      │ calriven/    │
│ - calriven   │  connection)│ deathtodata/ │
│ - etc        │            │              │
└──────────────┘            └──────────────┘
```

### Goal State (Connected):

```
DATABASE                     HTML FILES
┌──────────────┐            ┌──────────────┐
│ soulfra.db   │            │ output/      │
│              │            │              │
│ brands:      │     ✅     │ soulfra/     │
│ - soulfra    │───────────▶│ calriven/    │
│   slug=soulfra  (slug    │ deathtodata/ │
│              │   matches  │              │
│              │   folder)  │              │
└──────────────┘            └──────────────┘
```

**The connection:** `slug` field in database matches folder name in `output/`

**Example:**
- Database: `slug="howtocookathome"`
- HTML: `output/howtocookathome/index.html`

---

## Summary: The 3 Simple Steps

**1. Database First**
- Add domain info to `soulfra.db`
- Use: http://localhost:5001/admin/domains

**2. Generate HTML**
- Create website with templates + Ollama
- Saves to: `output/{slug}/`

**3. Deploy to Web**
- Push to GitHub
- Enable GitHub Pages
- Point DNS

**Everything connects through the `slug` field!**

---

## What We're Building Next

**Priority 1:** Domain dropdown in template browser
**Priority 2:** Status indicator (has HTML vs needs HTML)
**Priority 3:** One-click "Generate Website" button
**Priority 4:** Content dashboard (database records → HTML visualization)
**Priority 5:** Auto git commit on deploy

**Result:** Clean workflow where everything is connected and visual!
