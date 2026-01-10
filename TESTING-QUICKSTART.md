# Testing Quick Start - Test Before You Import Real Domains

**Created:** December 31, 2024
**Purpose:** Quick commands to safely test with fake domains

---

## 🚀 Simple Testing (RECOMMENDED)

### Step 1: Test with hollowtown.com (2 minutes)

```bash
# Just visit the form
open http://localhost:5001/admin/domains/import

# Paste: hollowtown.com
# Click: Analyze
# Wait: 30-60 seconds
# Click: Import
# Done!
```

**Cleanup:**
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE domain = 'hollowtown.com';"
```

---

### Step 2: Generate 200 Fake Domains (30 seconds)

```bash
python3 generate_fake_domains.py
```

**Output:** `test-domains.txt` with 200 fake domains

**View the file:**
```bash
cat test-domains.txt
# or
head -20 test-domains.txt  # First 20 domains
```

---

### Step 3: Import Fake Domains (1-3 hours)

```bash
# Open the import form
open http://localhost:5001/admin/domains/import

# Then:
# 1. Copy ALL contents of test-domains.txt
# 2. Paste into the form
# 3. See "200 domains ready to analyze"
# 4. Click "Analyze with Ollama"
# 5. Wait 1-3 hours (can close browser)
# 6. Come back, review suggestions
# 7. Click "Import All Domains"
```

**Or copy to clipboard directly:**
```bash
# macOS
cat test-domains.txt | pbcopy

# Linux
cat test-domains.txt | xclip -selection clipboard
```

---

### Step 4: Verify Import

```bash
# Check database size
ls -lh soulfra.db
# Before: 3.0M
# After: ~3.4M

# Count fake domains
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands WHERE category = 'test-fake';"
# Should show: 200

# View sample domains
sqlite3 soulfra.db "SELECT domain, emoji, tagline FROM brands WHERE category = 'test-fake' LIMIT 10;"
```

---

### Step 5: Clean Up Fake Data

```bash
python3 cleanup_fake_domains.py
```

**What it does:**
- Deletes all 200 fake domains
- Runs VACUUM to reclaim disk space
- Shows before/after stats
- Preserves your real domains

**Manual cleanup:**
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE category = 'test-fake';"
sqlite3 soulfra.db "VACUUM;"
```

---

### Step 6: Import Real Domains

```bash
# Visit the form again
open http://localhost:5001/admin/domains/import

# Paste your REAL domains
# Click Analyze
# Review suggestions
# Click Import
# Done!
```

---

## 🗄️ Advanced Testing (Separate Database)

### Create Test Database

```bash
python3 setup_test_database.py
```

**What it does:**
- Copies `soulfra.db` → `soulfra-test.db`
- Shows instructions to switch database

### Use Test Database

**Option 1: Edit app.py**
```python
# Find line:
DATABASE = 'soulfra.db'

# Change to:
DATABASE = 'soulfra-test.db'

# Restart Flask
```

**Option 2: Environment variable**
```bash
export DATABASE=soulfra-test.db
python3 app.py
```

### Test Everything

```bash
# Now do all your testing
# All data goes to soulfra-test.db
# Main database (soulfra.db) is untouched!
```

### Merge Back to Main

```bash
python3 merge_test_to_main.py
```

**What it does:**
- Exports successful domains from test DB
- Imports to main DB
- Avoids duplicates
- Shows confirmation prompt

### Clean Up

```bash
# Delete test database when done
rm soulfra-test.db
```

---

## 📊 Resource Consumption

### Disk Space
- **200 domains:** ~50MB total
- **Current available:** 24Gi (plenty!)
- **Database growth:** ~400KB

### Time
- **Ollama analysis:** 30-60 seconds per domain
- **200 domains:** 1.6-3.3 hours total
- **Processing:** Sequential (one at a time)

### Memory
- **Ollama:** ~500MB-1GB per request
- **No buildup:** Sequential processing
- **Safe:** Can run in background

### File Operations
- **mkdirs:** None (uses existing database)
- **File creation:** Only database entries (no HTML files unless you publish)
- **Network:** Localhost only (Ollama API)

---

## 🎯 Recommended Workflow

```bash
# 1. Test single domain first
Visit: http://localhost:5001/admin/domains/import
Paste: hollowtown.com
Import!

# 2. Generate fake domains
python3 generate_fake_domains.py

# 3. Import fake domains
Visit: http://localhost:5001/admin/domains/import
Paste: (all 200 from test-domains.txt)
Wait 1-3 hours
Import!

# 4. Verify it worked
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"

# 5. Clean up fake data
python3 cleanup_fake_domains.py

# 6. Import real domains
Visit: http://localhost:5001/admin/domains/import
Paste: (your real domains)
Import!

# 7. Celebrate! 🎉
```

---

## 💡 Tips

### During Import
- You can close browser while Ollama analyzes
- Server keeps processing in background
- Refresh page to check progress
- Takes 1-3 hours for 200 domains (normal!)

### After Import
- View all domains: `http://localhost:5001/admin/domains`
- Edit any domain: Click "Edit" button
- Generate content: Go to Studio, select domain, create debate

### Troubleshooting
- **Ollama slow?** It processes one at a time (normal)
- **Import failed?** Check Ollama is running: `curl http://localhost:11434`
- **Database locked?** Close other connections to database

---

## 📄 Files Created

**Testing scripts:**
- `generate_fake_domains.py` - Generate 200 fake domains
- `cleanup_fake_domains.py` - Delete fake domains
- `setup_test_database.py` - Create separate test database (optional)
- `merge_test_to_main.py` - Merge test to main (optional)

**Documentation:**
- `TESTING-STRATEGY.md` - Full testing strategy (detailed)
- `TESTING-QUICKSTART.md` - This file (quick commands)
- `DOMAIN-IMPORT-QUICKSTART.md` - Domain import guide

**Core files:**
- `test-domains.txt` - 200 fake domains (created by generate script)
- `soulfra-test.db` - Test database (optional, created by setup script)

---

## 🎉 You're Ready!

**Start here:**
```bash
python3 generate_fake_domains.py
open http://localhost:5001/admin/domains/import
```

**Questions?**
- Read `TESTING-STRATEGY.md` for full details
- Read `DOMAIN-IMPORT-QUICKSTART.md` for form usage
- Check existing 5 domains: `sqlite3 soulfra.db "SELECT * FROM brands;"`

**Let's test! 🚀**
