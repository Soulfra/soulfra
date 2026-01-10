# Fresh Start Guide - CringeProof

Clean proof-of-concept with **0 users** to prove the customer export system works.

## What You Got

**Two Separate Databases:**
- `cringeproof.db` - Fresh database with 0 users (7 tables only)
- `soulfra.db` - Existing database with 23 users (200+ tables, development work)

**Two Separate Startup Scripts:**
- `START_CRINGEPROOF.sh` - Port 5001, uses cringeproof.db
- `START_SOULFRA.sh` - Port 5002, uses soulfra.db

**Environment Variable Switching:**
Your `database.py` already supports `SOULFRA_DB` env var:
```python
DB_NAME = os.environ.get('SOULFRA_DB', 'soulfra.db')
```

This means you can run **both backends simultaneously** on different ports!

## Proof-of-Concept: 0 → 1 User → Export Works

### Step 1: Start Fresh Backend (0 Users)

```bash
./START_CRINGEPROOF.sh
```

You'll see:
```
🗄️  Database: cringeproof.db
📊 Database Status:
   Users: 0
   Subscribers: 0
   QR Scans: 0
```

Backend running at: `http://localhost:5001`

### Step 2: Be the First User

**Option A: Register via Web UI**
Go to: `http://localhost:5001/register`
- Username: your_username
- Email: your_real_email@gmail.com (or whatever)
- Password: secure_password

**Option B: Register via API**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "email": "your_email@gmail.com", "password": "secure_password"}'
```

### Step 3: Verify You're in the Database

```bash
sqlite3 cringeproof.db "SELECT * FROM users;"
```

Should show:
```
1|your_username|your_email@gmail.com|password_hash|your_username|2026-01-03 ...
```

### Step 4: Check Customer Dashboard

Go to: `http://localhost:5001/customers/dashboard`

Should show:
- **Total Users:** 1
- **Real Customers:** 1
- **Subscribers:** 0
- **QR Scans:** 0

### Step 5: Export to CSV

Click **Mailchimp CSV** button or go to:
`http://localhost:5001/api/customers/export/mailchimp`

Download will show:
```csv
Email Address,First Name,Last Name,Tags
your_email@gmail.com,your_username,,user; registered
```

### Step 6: Check API Stats

```bash
curl http://localhost:5001/api/customers/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "total_users": 1,
    "real_users": 1,
    "subscribers": 0,
    "qr_scans": 0,
    "unique_customers": 1,
    "voice_recordings": 0
  }
}
```

## ✅ Proof Complete!

You've proven:
1. ✅ Fresh database starts at 0 users
2. ✅ User registration works
3. ✅ Customer aggregation works (finds your email)
4. ✅ CSV export works (downloads your email)
5. ✅ API stats work (shows 1 real customer)
6. ✅ Filters work (no test accounts like @qr.local)

## Run Both Backends Simultaneously

**Terminal 1: CringeProof (Port 5001)**
```bash
./START_CRINGEPROOF.sh
```

**Terminal 2: Soulfra (Port 5002)**
```bash
./START_SOULFRA.sh
```

Now you have:
- `http://localhost:5001` - cringeproof.db (0 users, production-ready)
- `http://localhost:5002` - soulfra.db (23 users, development)

## Database Comparison

**cringeproof.db (Fresh):**
- 7 tables: users, subscribers, qr_codes, qr_scans, products, product_scans, simple_voice_recordings
- 0 users
- 0 KB file size
- Clean schema for production

**soulfra.db (Existing):**
- 200+ tables: battle_*, betting_*, game_*, neural_*, etc.
- 23 users (mostly test accounts)
- 4.7 MB file size
- Development/testing database

## Next Steps

### 1. Test on cringeproof.com (iPhone Registration)

Deploy backend to **Railway** or **Fly.io** (free tier):

**Railway:**
```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Deploy
railway login
railway init
railway up
```

Set environment variable on Railway:
```
SOULFRA_DB=cringeproof.db
```

Your iPhone can then register at: `https://your-app.railway.app/register`

### 2. Add Email Collection to QR Scans

Update your QR scan form to ask for email (optional):
```html
<form action="/api/qr-scan" method="POST">
  <input type="text" name="name" placeholder="Your name (optional)">
  <input type="email" name="email" placeholder="Email (optional)">
  <button type="submit">Submit</button>
</form>
```

These emails will automatically appear in customer exports!

### 3. Set Up Daily Cron Job

On your laptop/server:
```bash
# Add to crontab (runs daily at midnight)
crontab -e

# Add this line:
0 0 * * * curl http://localhost:5001/api/batch/run-all
```

This will:
- Export new signups to JSON
- Generate weekly reports
- Push to GitHub Pages
- Make data accessible on cringeproof.com

### 4. Clean Up soulfra.db (Optional)

If you want to slim down soulfra.db:

1. Go to: `http://localhost:5002/admin/database`
2. Click on unused tables (battle_*, betting_*, etc.)
3. Export any data you want to keep
4. Delete unused tables:

```bash
sqlite3 soulfra.db
```

```sql
-- See all tables
.tables

-- Drop unused tables
DROP TABLE battle_cards;
DROP TABLE battle_decks;
-- ... (repeat for all unused tables)
```

## Decentralized Architecture

Your customer data can now sync across all your domains:

**GitHub Pages (Free):**
```bash
# Daily sync creates JSON files
curl http://localhost:5001/api/batch/sync-daily
# Creates: voice-archive/data/daily_sync_20260103.json

# Push to GitHub
curl http://localhost:5001/api/batch/push-to-github
```

**Your Domains Fetch:**
```javascript
// On cringeproof.com, soulfra.com, etc.
fetch('https://cringeproof.com/data/daily_sync_20260103.json')
  .then(r => r.json())
  .then(data => {
    console.log(`${data.new_customers_count} new signups!`);
    // Display on homepage, send to AI, etc.
  });
```

**Ollama AI (Local):**
```bash
# Analyze customer patterns
curl http://localhost:5001/api/batch/ai-segment
```

Uses Ollama to suggest marketing segments - zero API costs!

## Files Created

- `minimal_schema.sql` - Clean 7-table schema
- `cringeproof.db` - Fresh database (0 users)
- `START_CRINGEPROOF.sh` - Fresh backend startup
- `START_SOULFRA.sh` - Existing backend startup
- `PROOF_TEST.sh` - Automated proof-of-concept test
- `FRESH_START.md` - This guide

## Support

All your tools at:
- **Fresh Backend:** `./START_CRINGEPROOF.sh` (port 5001)
- **Dev Backend:** `./START_SOULFRA.sh` (port 5002)
- **Database Admin:** `/admin/database`
- **Customer Export:** `/customers/dashboard`
- **Full Docs:** `CUSTOMER_EXPORT_README.md`
