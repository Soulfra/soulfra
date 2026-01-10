# Testing Strategy - Safe Domain Import Testing

**Created:** December 31, 2024
**Purpose:** Test domain import with 200 fake domains BEFORE using real domains

---

## 🎯 Your Request

> "how do we test this and make sure its working and build out profiles in a database in a folder or something and be able to merge that database or table into the main one... can we test it with 200 fake domains before i use my real ones?"

**Answer:** Yes! Here's the complete safe testing strategy.

---

## 📋 Testing Plan

### Phase 1: Single Domain Test (hollowtown.com)
**Purpose:** Verify the system works with 1 real domain
**Time:** ~2 minutes
**Risk:** Very low (can easily delete 1 domain)

### Phase 2: 200 Fake Domains Test
**Purpose:** Stress test with realistic fake data
**Time:** 1-3 hours (Ollama processing)
**Risk:** Zero (fake data only)

### Phase 3: Import Real Domains
**Purpose:** Import your real 200+ domains
**Time:** 1-3 hours
**Risk:** Low (tested workflow)

---

## 🗄️ Database Strategy

### Option 1: Use Main Database (RECOMMENDED)
**Why:** Simplest approach, easy to clean up

**Steps:**
1. Test with hollowtown.com → verify it works
2. Delete hollowtown.com if needed
3. Test with 200 fake domains → verify performance
4. Delete all 200 fake domains
5. Import real domains

**Cleanup:**
```sql
-- Delete single domain
DELETE FROM brands WHERE domain = 'hollowtown.com';

-- Delete all fake domains (tagged with category 'test-fake')
DELETE FROM brands WHERE category = 'test-fake';
```

### Option 2: Separate Test Database (ADVANCED)
**Why:** Keep test data completely isolated

**Steps:**
1. Copy soulfra.db → soulfra-test.db
2. Modify app.py to use test database
3. Test everything in test database
4. Export successful domains as CSV
5. Import CSV to main database

**Files Created:**
- `setup_test_database.py` - Creates test database
- `merge_test_to_main.py` - Merges successful test data

---

## 🤖 Fake Domain Generator

**Script:** `generate_fake_domains.py`

**What it does:**
- Generates 200 realistic fake domain names
- Covers all categories: cooking, tech, privacy, business, health, etc.
- Outputs to `test-domains.txt`
- Ready to paste into domain import form

**Example output:**
```
quickcookingrecipes.com
healthymealprep.net
techstartupguide.io
privacymatters.org
businessgrowthtools.com
fitnesstrackerpro.app
...
```

---

## 📊 Resource Consumption

### Disk Space
**Per domain:**
- Database entry: ~2KB
- Generated HTML (if published): ~50-200KB
- Total per domain: ~200KB average

**200 domains:**
- Database growth: ~400KB (negligible)
- Published HTML (if all): ~40MB
- Total: ~40-50MB

**Current available:** 24Gi (plenty of space!)

### Memory
**Ollama analysis:**
- ~500MB-1GB RAM per request
- Processes one domain at a time (sequential)
- No memory buildup

### Time
**Ollama processing:**
- 30-60 seconds per domain
- 200 domains = 100-200 minutes (1.6-3.3 hours)
- Runs in background (can close browser)

### File System Operations
**mkdirs:** None (uses existing database)
**File creation:** Only if you publish HTML
**Kernel:** No kernel-level operations
**Network:** HTTP requests to Ollama (localhost only)

---

## ✅ Testing Workflow

### Step 1: Test with hollowtown.com (2 minutes)

**Actions:**
1. Visit: `http://localhost:5001/admin/domains/import`
2. Paste: `hollowtown.com`
3. Click: "🤖 Analyze with Ollama"
4. Wait: ~30-60 seconds
5. Review: Ollama's suggestions
6. Click: "✅ Import All Domains"
7. Verify: Shows in `/admin/domains`

**Expected result:**
```
✅ Hollowtown (hollowtown.com)
Category: [whatever Ollama suggests]
Emoji: [relevant emoji]
Tagline: [catchy phrase]
```

**Cleanup (if needed):**
```bash
# If you want to remove it
sqlite3 soulfra.db "DELETE FROM brands WHERE domain = 'hollowtown.com';"
```

### Step 2: Generate 200 Fake Domains (30 seconds)

**Actions:**
```bash
python generate_fake_domains.py
```

**Output:**
- Creates `test-domains.txt` with 200 fake domains
- Opens file automatically (or cat test-domains.txt)

### Step 3: Import Fake Domains (1-3 hours)

**Actions:**
1. Visit: `http://localhost:5001/admin/domains/import`
2. Open: `test-domains.txt` and copy all 200 domains
3. Paste into form
4. See: "200 domains ready to analyze"
5. Click: "🤖 Analyze with Ollama"
6. Wait: 1-3 hours (you can close browser, it runs server-side)
7. Check back: Refresh page to see progress
8. Review: All 200 suggestions
9. Click: "✅ Import All Domains"

**Expected result:**
- Database grows by ~400KB
- All 200 domains tagged with category 'test-fake'
- Can see all in `/admin/domains`

### Step 4: Verify Performance

**Check database size:**
```bash
ls -lh soulfra.db
# Before: 3.0M
# After: 3.4M (expected)
```

**Check domains imported:**
```bash
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands WHERE category = 'test-fake';"
# Should show: 200
```

**Check Ollama suggestions:**
```bash
sqlite3 soulfra.db "SELECT domain, emoji, tagline FROM brands WHERE category = 'test-fake' LIMIT 5;"
```

### Step 5: Cleanup Fake Data

**Remove all fake domains:**
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE category = 'test-fake';"
sqlite3 soulfra.db "VACUUM;"  # Reclaim disk space
```

**Verify cleanup:**
```bash
ls -lh soulfra.db
# Should be back to ~3.0M
```

### Step 6: Import Real Domains

**Now you're confident! Import your real domains:**
1. Visit: `http://localhost:5001/admin/domains/import`
2. Paste your 200+ real domains
3. Click: "🤖 Analyze with Ollama"
4. Wait: 1-3 hours
5. Review suggestions
6. Click: "✅ Import All Domains"
7. Done!

---

## 🔧 Scripts Provided

### 1. `generate_fake_domains.py`
**Purpose:** Generate 200 realistic fake domains for testing

**Usage:**
```bash
python generate_fake_domains.py
```

**Output:**
- `test-domains.txt` (200 fake domains)

### 2. `setup_test_database.py` (OPTIONAL)
**Purpose:** Create separate test database

**Usage:**
```bash
python setup_test_database.py
```

**Output:**
- `soulfra-test.db` (copy of main database)
- Modifies `app.py` to use test database (commented out by default)

### 3. `merge_test_to_main.py` (OPTIONAL)
**Purpose:** Merge successful test data to main database

**Usage:**
```bash
python merge_test_to_main.py
```

**What it does:**
- Exports domains from soulfra-test.db
- Imports to soulfra.db
- Avoids duplicates

### 4. `cleanup_fake_domains.py`
**Purpose:** Quick cleanup of fake test data

**Usage:**
```bash
python cleanup_fake_domains.py
```

**What it does:**
- Deletes all domains with category 'test-fake'
- Runs VACUUM to reclaim space
- Shows before/after stats

---

## 💡 Master CSV Integration

**You mentioned:** "we also have the master csv of domains and shit too"

**File:** `domains-master.csv` (currently has 4 domains)

**Strategy:**
1. **Option A: Paste into import form**
   - Copy domain column from CSV
   - Paste into `/admin/domains/import`
   - Let Ollama re-analyze everything
   - Compare Ollama suggestions vs CSV data

2. **Option B: Direct CSV import**
   - Create `import_from_csv.py` script
   - Reads domains-master.csv
   - Imports directly to database
   - Skips Ollama (uses CSV data as-is)

**Recommendation:** Option A (let Ollama analyze)
- CSV data might be outdated
- Ollama gives fresh suggestions
- You can review before importing

---

## ❓ FAQ

### Q: Will this break my existing 5 domains?
**A:** No! Existing domains (Soulfra, DeathToData, etc.) are untouched.

### Q: Can I stop Ollama analysis mid-way?
**A:** Yes, but partial results won't be saved. Refresh page to start over.

### Q: What if Ollama is slow?
**A:** It processes one domain at a time (sequential). Just wait or reduce domain count.

### Q: Can I edit Ollama suggestions before importing?
**A:** Not yet, but you can edit domains after import in `/admin/domains`.

### Q: What if I accidentally import bad data?
**A:** Use cleanup script or SQL DELETE command to remove.

---

## 🎯 Recommended Approach

**Simplest (RECOMMENDED):**
1. ✅ Test with hollowtown.com
2. ✅ Generate 200 fake domains
3. ✅ Import fake domains to MAIN database (tagged 'test-fake')
4. ✅ Verify performance
5. ✅ Delete fake domains
6. ✅ Import real domains

**Why:** No separate database needed, easy cleanup, tests real workflow.

**Advanced (OPTIONAL):**
1. Create test database (soulfra-test.db)
2. Test everything in isolation
3. Merge successful results
4. More complex but safer

---

## 🚀 Ready to Start?

**Run this first:**
```bash
# Generate 200 fake domains
python generate_fake_domains.py

# You'll get test-domains.txt
# Then visit: http://localhost:5001/admin/domains/import
# And paste the contents!
```

**When done testing:**
```bash
# Clean up fake domains
python cleanup_fake_domains.py
```

**Then import real domains:**
```bash
# Just paste your real domains in the same form!
```

---

## 📝 Summary

**Before testing:** 5 real domains in database (3.0M)
**After fake test:** 205 domains (5 real + 200 fake) (~3.4M)
**After cleanup:** 5 real domains (3.0M) - back to normal
**After real import:** 205+ real domains (~3.4M+)

**Disk needed:** ~50MB for 200 domains
**Time needed:** 1-3 hours for Ollama analysis
**Risk:** Zero (easy to delete fake data)

**Let's do this! 🚀**
