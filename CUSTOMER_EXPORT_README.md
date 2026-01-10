# Custom Customer Export & Workflow System

Clean, decentralized customer data management built specifically for your domains (cringeproof.com, soulfra.com, soulfra.github.io).

**No bloat. No pre-built workflows. Just what you need.**

## ✅ What You Got

### 1. **Customer Data Aggregator** (`customer_export.py`)
Pulls customer data from multiple sources and filters out test accounts:

**Data Sources:**
- `users` table (filters out @qr.local, @soulfra.ai)
- `subscribers` table
- `qr_scans` table (when emails collected)
- Voice recordings metadata

**Export Formats:**
- **Mailchimp CSV** - Ready to import to Mailchimp
- **SendGrid CSV** - Ready for SendGrid
- **Plain Text** - Just emails, one per line
- **JSON** - Full data for custom automation

### 2. **Batch Workflows** (`batch_workflows.py`)
Automated syncing across your domains using GitHub Pages (free):

**Workflows:**
- **Daily Sync** - Export new signups → JSON file → Push to GitHub Pages
- **Weekly Report** - Generate HTML report → Host on cringeproof.com
- **AI Segmentation** - Ollama analyzes customers → Suggests marketing segments
- **GitHub Push** - Automatically push data files to voice-archive repo

### 3. **Product Tracking** (`product_tracking.py`)
Link QR codes to products and track performance:

**Features:**
- Create products with UPC codes
- Link QR codes to products
- Track scan counts, location, device type
- Export product performance reports
- View top scanned products

### 4. **Beautiful Dashboards**

**Customer Dashboard**: `http://localhost:5001/customers/dashboard`
- Live stats (users, subscribers, QR scans)
- One-click exports
- Batch workflow controls
- Product tracking access

**Database Admin**: `http://localhost:5001/admin/database`
- SharePoint-like table viewer
- Search and filter
- Export any table to CSV

## 🚀 Quick Start

### 1. Start the Backend
```bash
./START_BACKEND.sh
```

This will show you all the URLs you need:
```
📊 Admin Dashboards:
   Database Admin: http://localhost:5001/admin/database
   Customer Export: http://localhost:5001/customers/dashboard

📧 Customer Export:
   Mailchimp CSV: http://localhost:5001/api/customers/export/mailchimp
   SendGrid CSV: http://localhost:5001/api/customers/export/sendgrid
   Stats API: http://localhost:5001/api/customers/stats

⚙️  Batch Workflows:
   Daily Sync: http://localhost:5001/api/batch/sync-daily
   Weekly Report: http://localhost:5001/api/batch/weekly-report
   Run All: http://localhost:5001/api/batch/run-all

📦 Product Tracking:
   List Products: http://localhost:5001/api/products/list
   Top Scanned: http://localhost:5001/api/products/top-scanned
```

### 2. View Your Customers
Go to: `http://localhost:5001/customers/dashboard`

See live stats:
- 23 total users
- 19 real customers (filters out test accounts)
- 2 subscribers
- 25 QR scans

### 3. Export Customer Lists

**For Mailchimp:**
Click "Mailchimp CSV" → Downloads `mailchimp_customers_YYYYMMDD.csv`

**For SendGrid:**
Click "SendGrid CSV" → Downloads `sendgrid_customers_YYYYMMDD.csv`

**For Custom Use:**
Click "JSON" → Downloads full customer data with tags, sources, timestamps

### 4. Run Batch Workflows

**Daily Sync to GitHub Pages:**
```bash
curl http://localhost:5001/api/batch/sync-daily
```
Creates: `voice-archive/data/daily_sync_YYYYMMDD.json`

**Weekly Report:**
```bash
curl http://localhost:5001/api/batch/weekly-report
```
Creates: `voice-archive/reports/weekly_YYYYMMDD.html`
View at: `https://cringeproof.com/reports/weekly_YYYYMMDD.html` (after push)

**AI Customer Segmentation:**
```bash
curl http://localhost:5001/api/batch/ai-segment
```
Uses Ollama to analyze customer patterns and suggest marketing segments.

**Push Everything to GitHub:**
```bash
curl http://localhost:5001/api/batch/push-to-github
```
Commits and pushes all data files to your GitHub Pages repo.

### 5. Track Products (UPC/QR)

**Create a Product:**
```bash
curl -X POST http://localhost:5001/api/products/create \
  -H "Content-Type: application/json" \
  -d '{"upc": "123456789012", "name": "My Product", "qr_code_id": 1}'
```

**Track a Scan:**
```bash
curl -X POST http://localhost:5001/api/products/1/track-scan \
  -H "Content-Type: application/json" \
  -d '{"location_city": "NYC", "device_type": "iPhone"}'
```

**View Top Products:**
```bash
curl http://localhost:5001/api/products/top-scanned
```

**Export Performance Report:**
```bash
curl http://localhost:5001/api/products/export/performance > products.csv
```

## 📊 Your Current Data

**Customers:**
- 19 real customers (filtered from 23 total users)
- 2 newsletter subscribers
- 0 emails from QR scans (start collecting!)

**Activity:**
- 25 QR code scans
- 11 voice recordings
- All data aggregated from soulfra.db

## 🌐 Decentralized Architecture

**GitHub Pages (Free Hosting):**
- Daily customer syncs → `cringeproof.com/data/`
- Weekly reports → `cringeproof.com/reports/`
- Static JSON APIs for your domains to fetch

**Your Domains Can Fetch:**
```javascript
// On cringeproof.com, soulfra.com, etc.
fetch('https://cringeproof.com/data/daily_sync_20260103.json')
  .then(r => r.json())
  .then(data => console.log(`${data.new_customers_count} new signups!`))
```

**Ollama AI (Local):**
- Customer segmentation analysis
- Marketing campaign suggestions
- Zero API costs, runs on your laptop

## 🔥 Benefits

✅ **No Bloat** - Only 3 Python files, clean code
✅ **Decentralized** - Data synced across your domains via GitHub Pages (free)
✅ **AI-Powered** - Ollama analyzes customer patterns locally
✅ **Cheap** - GitHub Pages = free, Ollama = free, no monthly fees
✅ **Your Own** - Full control, no pre-built workflows
✅ **Clean Data** - Filters test accounts automatically

## 📝 Next Steps

1. **Set up daily cron job** to run batch workflows:
   ```bash
   # Add to crontab
   0 0 * * * curl http://localhost:5001/api/batch/run-all
   ```

2. **Start collecting emails from QR scans** - Update QR scan forms to capture email

3. **Create products** - Link your physical products to QR codes for tracking

4. **Deploy backend online** - Use Railway/Fly.io to make APIs accessible from cringeproof.com

## 🗑️ Clean Up Bloat (Optional)

Your database has 200+ tables. Most are unused. To clean up:

1. Go to Database Admin: `http://localhost:5001/admin/database`
2. Click on unused tables (battle_*, betting_*, game_* if you're not using them)
3. Export data you want to keep
4. Delete unused tables to speed up queries

**Tables to Keep:**
- `users`, `subscribers`, `qr_scans`, `qr_codes`
- `simple_voice_recordings`, `voice_ideas`
- `products`, `product_scans` (new tables created by product tracking)

**Safe to Delete (if not using):**
- All `battle_*` tables (150+ gaming tables)
- `betting_*`, `story_*`, `game_*` tables
- Neural network/AI tables if not using

## 📞 Support

All your customer export tools are now at:
- **Dashboard**: `http://localhost:5001/customers/dashboard`
- **Database Admin**: `http://localhost:5001/admin/database`

Run `./START_BACKEND.sh` to see all available URLs.
