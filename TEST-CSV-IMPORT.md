# Test CSV Import - Prove It Works at Scale

**Created:** December 31, 2024
**Status:** ✅ Ready to test!

---

## 🎯 What We're Testing

**Question:** Does CSV import really work with 50, 200+ domains?

**Answer:** Yes! Let's prove it.

---

## 📁 Your Domain Files (Explained)

You have 4 domain files - here's which to use:

| File | Lines | Use For |
|------|-------|---------|
| **domains-master.csv** ✅ | 37 | YOUR REAL DOMAINS (use this!) |
| test-domains-50.csv | 51 | Testing with 50 domains |
| test-domains-200.csv | 201 | Testing with 200 domains |
| domains-simple.txt | 11 | Ollama import (slower) |
| domains.txt | 14 | Old format (ignore) |

**Bottom line:** Use `domains-master.csv` for your real domains!

---

## 🧪 Test 1: Import 50 Domains (30 seconds)

### Step 1: View the test CSV
```bash
head -10 test-domains-50.csv
```

You'll see:
```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
Simpledinner,simpledinner.org,cooking,creative,🍳,blog,"The cooking experts","Home cooks","Share recipes",false,false
Websolutions,websolutions.io,tech,business,💻,platform,"Making tech simple","Developers","Tech solutions",false,false
...
```

### Step 2: Copy the CSV
```bash
# macOS
cat test-domains-50.csv | pbcopy

# Linux
cat test-domains-50.csv | xclip -selection clipboard

# Manual
open test-domains-50.csv  # Copy manually
```

### Step 3: Import
```bash
open http://localhost:5001/admin/domains/csv
```

1. Paste CSV into text area
2. Click **"📋 Parse & Preview"**
3. See table with 50 domains
4. Click **"✅ Import All Domains"**
5. Wait ~5-10 seconds
6. **Done!**

### Step 4: Verify
```bash
# Open domains page
open http://localhost:5001/admin/domains

# Or check database
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"
# Should show: 55 (5 existing + 50 new)
```

**Time:** ~30 seconds total

---

## 🧪 Test 2: Import 200 Domains (1 minute)

### Clean up test 1 first
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE domain LIKE 'simple%' OR domain LIKE 'web%' OR domain LIKE 'secure%';"
```

Or keep them - duplicates will get numbered slugs.

### Step 1: Copy the large CSV
```bash
cat test-domains-200.csv | pbcopy
```

### Step 2: Import
```bash
open http://localhost:5001/admin/domains/csv
```

1. Paste 200 domains
2. Click Parse
3. See table with 200 rows
4. Click Import
5. Wait ~20-30 seconds
6. **Done!**

### Step 3: Verify
```bash
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"
# Should show: 205 (5 existing + 200 new)

# Check database size
ls -lh soulfra.db
# Before: 3.0M
# After: ~3.5M (500KB growth for 200 domains)
```

**Time:** ~1 minute total

---

## 📊 Performance Comparison

| Method | 50 Domains | 200 Domains |
|--------|-----------|-------------|
| **CSV Import** | 30 seconds | 1 minute |
| **Ollama Import** | 25-50 minutes | 1.6-3.3 hours |

**CSV is 100-200x faster!**

---

## ✅ Verification Checklist

After import, check these:

### 1. Domain Count
```bash
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"
```

### 2. Sample Domains
```bash
sqlite3 soulfra.db "SELECT name, domain, category, emoji FROM brands LIMIT 10;"
```

### 3. Categories
```bash
sqlite3 soulfra.db "SELECT category, COUNT(*) as count FROM brands GROUP BY category;"
```

Expected output:
```
cooking|25
tech|25
privacy|25
business|25
health|25
finance|25
education|25
gaming|25
local|25
art|25
```

### 4. Web UI
```bash
open http://localhost:5001/admin/domains
```

Should see all domains with emojis, categories, tiers.

---

## 🧹 Clean Up Test Data

### Remove all test domains
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE domain LIKE '%.org' OR domain LIKE '%.io';"
sqlite3 soulfra.db "VACUUM;"
```

### Or remove by category
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE domain LIKE 'simple%' OR domain LIKE 'web%';"
```

### Or keep existing domains, remove new ones
```bash
sqlite3 soulfra.db "DELETE FROM brands WHERE id > 5;"
```

---

## 🚀 Next: Import Your Real Domains

### Step 1: Update domains-master.csv

Open the file:
```bash
open domains-master.csv
```

Current content (4 domains + header):
```csv
name,domain,category,tier,emoji,brand_type,tagline,target_audience,purpose,ssl_enabled,deployed
Soulfra,soulfra.com,tech,foundation,🌟,platform,"AI-powered development platform",...
HowToCookAtHome,howtocookathome.com,cooking,creative,👨‍🍳,blog,"Simple recipes",...
DeathToData,deathtodata.com,privacy,foundation,💀,blog,"Privacy-first",...
Calriven,calriven.com,tech,foundation,🔧,blog,"Technical excellence",...
```

**Add your 200+ domains below!**

### Step 2: Import in batches (recommended)

**Why batches?** Catch errors early, verify as you go.

**Batch 1: First 50 domains**
```bash
# Copy lines 1-51 from domains-master.csv (header + 50 domains)
open http://localhost:5001/admin/domains/csv
# Paste → Import → Verify
```

**Batch 2: Next 50 domains**
```bash
# Copy header + lines 52-101
# Import → Verify
```

**Continue until all domains imported!**

### Step 3: Verify all imported
```bash
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"
# Should show: 200+ domains

open http://localhost:5001/admin/domains
# Scroll through - all domains present!
```

---

## 💡 Tips

### Missing Data?

If CSV row is incomplete:
- No name → Uses domain (e.g., "mycooking.com" → "Mycooking")
- No category → Defaults to "tech"
- No emoji → Defaults to 🌐
- No tier → Defaults to "creative"

**Still imports!**

### Duplicate Domains?

If domain exists:
- Slug gets number: `mycooking` → `mycooking-1`
- No conflict!

### Excel/Google Sheets?

1. Open your spreadsheet
2. File → Export → CSV
3. Use exported CSV file

### Edit After Import?

Yes! Go to `/admin/domains`, click "Edit" on any domain.

---

## 🎯 Success Criteria

**You'll know it works when:**
1. ✅ 50 domains import in 30 seconds
2. ✅ 200 domains import in 1 minute
3. ✅ All domains show in /admin/domains
4. ✅ Database grows ~2KB per domain
5. ✅ Emojis, categories, tiers all correct

---

## 🐛 Troubleshooting

### "No domains to import"
- Check CSV has header row
- Check domains column has valid domains
- Try: `cat test-domains-50.csv` to verify file

### "Failed to import domains"
- Check Flask is running: `curl http://localhost:5001`
- Check database exists: `ls -lh soulfra.db`
- Check logs in terminal running Flask

### Import button doesn't work
- Check browser console (F12)
- Refresh page
- Try different browser

---

## 📝 Files Reference

**Test data (pre-generated):**
- `test-domains-50.csv` - 50 test domains
- `test-domains-200.csv` - 200 test domains

**Your real data:**
- `domains-master.csv` - YOUR DOMAINS GO HERE ✅

**Tools:**
- `generate_test_csv.py` - Generate more test data
- `CSV-IMPORT-QUICKSTART.md` - CSV import guide

**Old files (ignore):**
- `domains-simple.txt` - Simple format (for Ollama)
- `domains.txt` - Old format

---

## 🎉 You're Ready!

**Test workflow:**
```bash
# 1. Test with 50 domains
cat test-domains-50.csv | pbcopy
open http://localhost:5001/admin/domains/csv
# Paste → Parse → Import

# 2. Verify
open http://localhost:5001/admin/domains

# 3. Clean up
sqlite3 soulfra.db "DELETE FROM brands WHERE id > 5;"

# 4. Test with 200 domains
cat test-domains-200.csv | pbcopy
open http://localhost:5001/admin/domains/csv
# Paste → Parse → Import

# 5. Verify scale
sqlite3 soulfra.db "SELECT COUNT(*) FROM brands;"

# 6. Import your real domains!
open domains-master.csv  # Add your domains
open http://localhost:5001/admin/domains/csv  # Import!
```

**Let's prove CSV import works at scale!**
