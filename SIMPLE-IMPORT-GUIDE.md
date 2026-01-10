# Simple Domain Import - Quick Guide

## TL;DR:

1. **Paste your domain names** in `domains-simple.txt`
2. **Run**: `python3 import_domains_simple.py`
3. **Approve** Ollama's suggestions
4. **Done!**

---

## What This Does:

Takes a simple text file with **just domain names** (one per line) and:
- Uses Ollama AI to analyze each domain
- Suggests category, emoji, tagline, audience, purpose
- Shows you a preview of all suggestions
- You approve, then imports to database

**No complex CSV needed!**

---

## Step-by-Step:

### 1. Add Your Domain Names

Open the file:
```bash
nano domains-simple.txt
```

Paste your domains (one per line):
```
myblog.com
techsite.com
howtocookathome.com
privacyfirst.com
gamedev.com
... (200+ more)
```

Save and close.

### 2. Run Import Script

```bash
python3 import_domains_simple.py
```

### 3. Wait for Ollama Analysis

Takes 30-60 seconds per domain. You'll see:
```
🤖 Analyzing domains with Ollama...
   [1/200] Analyzing myblog.com... ✅ MyBlog (cooking)
   [2/200] Analyzing techsite.com... ✅ TechSite (tech)
   ...
```

### 4. Review Preview

Script shows all suggestions:
```
📋 PREVIEW OF SUGGESTED DOMAIN DETAILS

1. 🍳 MyBlog (myblog.com)
   Category: cooking
   Type: blog
   Tagline: Quick recipes for busy parents
   Audience: Parents age 25-45
   Purpose: 30-minute meal ideas

2. 💻 TechSite (techsite.com)
   Category: tech
   Type: blog
   Tagline: Developer tutorials and guides
   Audience: Software engineers
   Purpose: Learn to code

...
```

### 5. Approve and Import

```
Do you want to import these domains? (y/n): y
```

Press `y` to import all domains to database.

---

## What Ollama Suggests For Each Domain:

Based on domain name, Ollama analyzes and suggests:

- **Category**: cooking, tech, privacy, business, health, art, education, gaming, finance, local
- **Brand Name**: Readable version (e.g., "myblog.com" → "MyBlog")
- **Brand Type**: blog, game, community, platform, directory
- **Emoji**: One emoji that fits the brand
- **Tagline**: 3-7 word catchy phrase
- **Target Audience**: Who visits this site
- **Purpose**: What the site does

---

## Requirements:

### Ollama Must Be Running:

```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if needed
ollama serve

# Make sure model is installed
ollama list
# Should show: llama3.2:3b
```

### Domain File Must Exist:

```bash
# Check file exists
ls -lh domains-simple.txt

# If missing, create it
touch domains-simple.txt
```

---

## Common Issues:

### "Ollama is not running"

**Fix**:
```bash
ollama serve
```

In another terminal, run import again.

### "No domains found in file"

**Fix**:
- Open `domains-simple.txt`
- Make sure there are domain names (one per line)
- Remove any extra blank lines at top
- Save and try again

### "Invalid domain format"

**Fix**:
- Domain names must have a `.` (e.g., `example.com`)
- Must be at least 4 characters
- Remove `http://` or `https://` - just the domain name

### Ollama analysis fails for a domain

Script will use defaults:
- Category: tech
- Emoji: 🌐
- Type: blog
- Empty tagline/audience/purpose

You can edit these later in the control panel.

---

## After Import:

### View Your Domains:

```bash
# Restart Flask
./RESTART-FLASK-CLEAN.sh

# Visit in browser
http://localhost:5001/admin/domains
```

### Check Database:

```bash
# Count domains
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands"

# View all domains
sqlite3 soulfra.db "SELECT name, domain, category FROM brands"
```

### Chat With Ollama About Each Domain:

1. Go to: `http://localhost:5001/admin/domains`
2. Click "💬 Chat" on any domain
3. Have a 2-3 minute conversation
4. Approve suggestions
5. Repeat for all domains

---

## Comparison: Simple vs CSV

### Simple Method (domains-simple.txt):
**Pros**:
- Just paste domain names
- Ollama suggests everything
- Fast and easy
- No formatting errors

**Cons**:
- Less control
- Ollama might guess wrong category
- Need to review suggestions

### CSV Method (domains-master.csv):
**Pros**:
- Full control over all fields
- Exact categories/taglines you want
- No AI guessing

**Cons**:
- 11 columns to fill per domain
- Easy to make formatting errors
- Slow and tedious

---

## When To Use Which:

### Use Simple Method If:
- You have 50+ domains to add
- You don't know categories/taglines yet
- You want to get started fast
- You trust Ollama to suggest reasonable defaults

### Use CSV Method If:
- You have < 20 domains
- You already know exact details for each
- You want precise control
- You're migrating from existing database/spreadsheet

---

## Example Session:

```bash
$ cat domains-simple.txt
myblog.com
techsite.com
privacyfirst.com

$ python3 import_domains_simple.py

📖 Reading domains from domains-simple.txt...
   Found 3 domains

🤖 Analyzing domains with Ollama...
   (This may take 30-60 seconds per domain)

   [1/3] Analyzing myblog.com... ✅ MyBlog (cooking)
   [2/3] Analyzing techsite.com... ✅ TechSite (tech)
   [3/3] Analyzing privacyfirst.com... ✅ PrivacyFirst (privacy)

📋 PREVIEW OF SUGGESTED DOMAIN DETAILS
================================================================================

1. 🍳 MyBlog (myblog.com)
   Category: cooking
   Type: blog
   Tagline: Quick recipes for busy parents
   Audience: Parents age 25-45
   Purpose: 30-minute meal ideas

2. 💻 TechSite (techsite.com)
   Category: tech
   Type: blog
   Tagline: Developer tutorials and guides
   Audience: Software engineers
   Purpose: Learn to code

3. 🔒 PrivacyFirst (privacyfirst.com)
   Category: privacy
   Type: blog
   Tagline: Take control of your data
   Audience: Privacy advocates
   Purpose: Privacy tools and guides

================================================================================

Do you want to import these domains? (y/n): y

📥 Importing to database...
✅ Imported: MyBlog (myblog.com)
✅ Imported: TechSite (techsite.com)
✅ Imported: PrivacyFirst (privacyfirst.com)

================================================================================
📊 Import Summary:
   Imported: 3
   Skipped:  0
   Total:    3
================================================================================

✅ Success! 3 domains imported to database
   Visit: http://localhost:5001/admin/domains
   Or: http://localhost:5001/control
```

---

## Next Steps:

1. **Import your domains** using simple method
2. **Restart Flask**: `./RESTART-FLASK-CLEAN.sh`
3. **View domains**: http://localhost:5001/admin/domains
4. **Chat with Ollama** about each domain
5. **Approve suggestions** and build out content
6. **Deploy** when ready

---

## Summary:

This simple import method makes adding 200+ domains **effortless**:
- Just paste domain names
- Ollama does the analysis
- Review and approve
- Import to database

**Use this method to get started quickly, then refine details later through chat.**
