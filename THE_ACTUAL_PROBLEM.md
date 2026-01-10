# THE ACTUAL PROBLEMS (Both Found)

## Error
```
Upload error: Failed to fetch
```

## Root Causes (TWO problems)

### Problem 1: Duplicate Flask Processes ✅ FIXED
**TWO Flask processes running on same port**

```bash
$ lsof -i :5001
Python  20012 matthewmauer   14u  IPv4 *:commplex-link (LISTEN)
Python  22407 matthewmauer   14u  IPv4 *:commplex-link (LISTEN)
```

They're fighting over port 5001 → requests randomly fail.

**Fix**: Kill all duplicates, run single instance
```bash
pkill -f "python3 app.py"
python3 app.py
```

### Problem 2: Missing `brands` Table ⚠️ CURRENT ISSUE
Flask app crashes on startup with:
```
sqlite3.OperationalError: no such table: brands
```

**Why**: The `brands` table doesn't exist in `soulfra.db`. Flask app queries it on index route (line 854).

**Tables that DO exist**:
- posts
- users
- simple_voice_recordings
- voice_suggestions
- workflow_templates
- (70+ other tables)

**No brands table found.**

## The Fix

### Step 1: Create brands table
Need to either:
1. Find the original schema/migration for brands table
2. Create minimal brands table to unblock voice upload
3. Comment out brands-dependent code in app.py temporarily

### Step 2: Voice upload endpoint
CringeProof voice-archive expects: `POST /api/voice/upload`

Check if this endpoint exists and works.

## What We DIDN'T Need

- ❌ Shadow branch
- ❌ 337 lines of store-and-forward code
- ❌ New CORS config (already worked)
- ❌ IndexedDB system
- ❌ QR/POAP generator

## What We DID Need

✅ Kill duplicate processes (DONE)
⚠️ Create brands table (IN PROGRESS)
⏳ Test voice upload endpoint

## Lesson

**Before building new systems:**
1. Check if service is even running ✅
2. Check for port conflicts ✅
3. Check database schema ⚠️
4. Fix the actual errors
5. THEN add features

We built solutions for problems that didn't exist while ignoring the real problems:
1. **duplicate processes** ✅
2. **missing database table** ⚠️
