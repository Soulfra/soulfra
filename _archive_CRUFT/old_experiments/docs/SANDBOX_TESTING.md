# Sandbox Testing Guide

Test the brand system safely without touching your production database!

## 🎯 Why Use Sandbox?

Your production database (`soulfra.db`) has 888KB of data. The bootstrap process will:
- Add 7 new brands (currently only has 1)
- Cleanup 69 orphaned brand_posts associations
- Train ML models on brand data

**DON'T TEST THIS ON PRODUCTION!** Use the sandbox first.

---

## 🏗️ Step 1: Create Sandbox

```bash
python3 test_bootstrap.py create-sandbox
```

This will:
- Copy `soulfra.db` → `soulfra_test.db` (creates isolated test database)
- Verify database integrity
- Show table count

**Output:**
```
🏗️  Creating Sandbox Test Environment
📦 Production database: 888.0 KB
📋 Copying soulfra.db → soulfra_test.db...
✅ Test database created: 888.0 KB
✅ 37 tables found in test database
✅ SANDBOX CREATED SUCCESSFULLY
```

---

## 🧪 Step 2: Run Sandbox Server

```bash
python3 test_bootstrap.py
```

**This runs Flask on PORT 5002 (not 5001!)**

```
🧪 Soulfra Sandbox Test Server
📦 Using test database: 888.0 KB
🔧 Configuration:
   Database: soulfra_test.db (SANDBOX)
   Port: 5002 (NOT production)
   Production: http://localhost:5001 (unchanged)

🚀 Starting Sandbox Server...
📍 Sandbox URL: http://localhost:5002
📍 Production URL: http://localhost:5001 (still safe!)

⚠️  ALL CHANGES HAPPEN IN SANDBOX ONLY
   Production database is NOT touched
```

---

## 🔍 Step 3: Check Status Dashboard

1. **Open sandbox**: http://localhost:5002/admin/brand-status
2. **You'll see**:
   - 🧪 "SANDBOX MODE" banner (confirms using test DB)
   - Health score (probably LOW - that's expected!)
   - ❌ Failed checks showing what's wrong
   - 📦 Brand Sync: 1/8 brands (missing 7!)
   - 🔗 Associations: 69 orphaned (needs cleanup)

**Expected Initial State:**
```
System Health: 20/100 (ERROR)

❌ Brands Synced: Only 1/8 brands synced. Run bootstrap!
❌ Associations Clean: 69 orphaned associations found. Run cleanup!
⚠️  Training Data: 1 brands have posts. Need at least 2!
❌ Brand Voice Model: Not trained.
❌ Prediction Accuracy: Cannot test - no model trained
```

---

## 🚀 Step 4: Run Bootstrap (IN SANDBOX)

Still on http://localhost:5002/admin/brand-status:

1. Click **"🚀 Run Bootstrap"** button
2. Confirm dialog
3. Wait for completion

**This will:**
- Sync 7 brands from `themes/manifest.yaml` → database
- Cleanup 69 orphaned associations
- Flash success message

**Refresh the page. You should now see:**
```
System Health: 60/100 (WARNING)

✅ Brands Synced: 8/8 brands synced from manifest
✅ Associations Clean: 0 orphaned associations
✅ Training Data: 8 brands have posts for training
❌ Brand Voice Model: Not trained. Click "Train Models" in admin!
❌ Prediction Accuracy: Cannot test - no model trained
```

---

## 🎭 Step 5: Train Models (IN SANDBOX)

Still on http://localhost:5002/admin/brand-status:

1. Click **"🎭 Train Models"** button
2. Confirm dialog
3. Wait ~5 seconds for training

**This will:**
- Train brand voice classifier on 8 brands
- Learn wordmaps for each brand
- Analyze emoji patterns
- Save models to `ml_models` table

**Refresh. Health score should be 100%:**
```
System Health: 100/100 (HEALTHY)

✅ Brands Synced: 8/8 brands synced from manifest
✅ Associations Clean: 0 orphaned associations
✅ Training Data: 8 brands have posts for training
✅ Brand Voice Model: Trained on 69 examples
✅ Prediction Accuracy: 6/8 predictions correct (75%)
```

**Test Predictions Section Shows:**
```
🧪 Test Predictions

✅ Expected: calriven, Got: calriven (85% confidence)
✅ Expected: ocean-dreams, Got: ocean-dreams (92% confidence)
❌ Expected: deathtodata, Got: calriven (68% confidence)
...
```

---

## ✅ Step 6: Verify Everything Works

### View Wordmaps
```bash
# In sandbox (port 5002)
curl http://localhost:5002/api/brand/wordmap/ocean-dreams
```

**Returns:**
```json
{
  "brand": "ocean-dreams",
  "wordmap": {
    "flowing": 45,
    "calm": 38,
    "peaceful": 32,
    ...
  },
  "top_words": ["flowing", "calm", "peaceful", "serene", "gentle"]
}
```

### Test Predictions
```bash
curl -X POST http://localhost:5002/api/brand/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Calm flowing updates with peaceful design"}'
```

**Returns:**
```json
{
  "brand": "ocean-dreams",
  "confidence": 0.92
}
```

### Check JSON Status
```bash
curl http://localhost:5002/api/brand/status | python3 -m json.tool
```

---

## 🎉 Step 7: Migrate to Production (ONLY IF SANDBOX WORKS!)

**IF** everything works in sandbox:

1. **Stop sandbox server** (Ctrl+C)
2. **Backup production database:**
   ```bash
   cp soulfra.db soulfra.db.backup
   ```
3. **Run bootstrap on production:**
   ```bash
   python3 bootstrap.py
   ```
4. **Start production server:**
   ```bash
   python3 app.py
   ```
5. **Train models on production:**
   - Go to http://localhost:5001/admin/brand-status
   - Click "🎭 Train Models"
6. **Verify health score is 100%**

---

## 🔄 Reset Sandbox

If you want to start over:

```bash
python3 test_bootstrap.py reset
```

This deletes `soulfra_test.db` and copies from production again.

---

## 📊 Compare Production vs Sandbox

```bash
python3 test_bootstrap.py status
```

**Shows:**
```
📊 Database Status

✅ Production (port 5001): soulfra.db (888.0 KB)
   Brands: 1
   ML models: 7

✅ Sandbox (port 5002): soulfra_test.db (888.0 KB)
   Brands: 8
   ML models: 8
```

---

## 🚨 Safety Rules

1. **ALWAYS test in sandbox first** (port 5002)
2. **NEVER run bootstrap on production** without testing in sandbox
3. **ALWAYS backup** before production changes: `cp soulfra.db soulfra.db.backup`
4. Sandbox uses `soulfra_test.db` - production uses `soulfra.db`
5. Look for "🧪 SANDBOX MODE" banner to confirm you're in sandbox

---

## 🐛 Troubleshooting

### "Test database not found"
```bash
python3 test_bootstrap.py create-sandbox
```

### Port 5002 already in use
```bash
lsof -ti :5002 | xargs kill -9
python3 test_bootstrap.py
```

### Want to see what changes will happen
1. Run sandbox
2. Check http://localhost:5002/admin/brand-status
3. See failed checks (shows exactly what bootstrap will fix)

### Sandbox looks good, but scared to run on production
**That's OK!** Keep using sandbox. Or:
1. Make production backup: `cp soulfra.db soulfra_prod.db`
2. Run bootstrap
3. If something breaks, restore: `mv soulfra_prod.db soulfra.db`

---

## 📚 Files Created

- `test_bootstrap.py` - Sandbox server runner
- `brand_status_dashboard.py` - Health check functions
- `templates/brand_status.html` - Visual dashboard UI
- `/admin/brand-status` route in `app.py`
- `/api/brand/status` API endpoint in `app.py`

---

## 🎯 Quick Reference

```bash
# Create sandbox
python3 test_bootstrap.py create-sandbox

# Run sandbox (port 5002)
python3 test_bootstrap.py

# Check status
python3 test_bootstrap.py status

# Reset sandbox
python3 test_bootstrap.py reset

# Production (port 5001)
python3 app.py
```

**Sandbox URL:** http://localhost:5002/admin/brand-status
**Production URL:** http://localhost:5001/admin/brand-status
