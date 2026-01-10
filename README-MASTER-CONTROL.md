# Soulfra Control Hub - Master README

## What This Is:

A **local control panel** for managing 200+ domains from one codebase.

**Soulfra.com = The Hub** that controls everything else.

---

## Quick Start:

### 1. Add Your Domains
```bash
# Edit this file and add all your domains:
nano domains-master.csv

# Add one line per domain (200+ lines total)
```

### 2. Import Domains to Database
```bash
python3 import_domains_csv.py
# Imports all domains from CSV → SQLite database
# Validates: no nulls, no duplicates
```

### 3. Start Control Panel
```bash
./RESTART-FLASK-CLEAN.sh
# Or: python3 app.py

# Visit: http://localhost:5001/control
```

### 4. Manage Everything
- View all 200+ domains
- Chat with Ollama about each domain
- Generate SSL certs
- Deploy to production
- Migrate SQLite → Postgres

---

## Architecture Overview:

```
┌─────────────────────────────────────────────┐
│   SOULFRA.COM (Control Hub)                │
│   http://localhost:5001/control             │
│                                             │
│   - Manage 200+ domains                    │
│   - Chat with Ollama                        │
│   - Generate SSL certs                     │
│   - Deploy to production                   │
└─────────────────────────────────────────────┘
                     │
                     ├─→ SQLite (Development)
                     ├─→ Postgres (Production)
                     ├─→ domains-master.csv (Source of truth)
                     │
        ┌────────────┴────────────┐
        │                         │
   ┌────▼─────┐            ┌─────▼─────┐
   │Domain #1 │            │Domain #200│
   │cooking   │    ...     │tech       │
   └──────────┘            └───────────┘
```

---

## File Structure:

### Current (CHAOS - 415 files):
```
soulfra-simple/
├── 190 Python scripts (scattered)
├── 133 Markdown docs (redundant)
├── app.py (6000+ lines)
└── Everything mixed together
```

### Clean (ORGANIZED):
```
soulfra-simple/
├── README-MASTER-CONTROL.md (This file - start here)
├── domains-master.csv (All 200+ domains)
├── app.py (Main Flask app)
├── import_domains_csv.py (CSV → Database)
│
├── control/ (Control panel code)
│   ├── __init__.py
│   ├── panel.py (Control panel routes)
│   ├── ssl.py (SSL cert management)
│   └── deploy.py (Deployment tools)
│
├── database/
│   ├── soulfra.db (SQLite - development)
│   ├── migrate.py (SQLite ↔ Postgres)
│   └── schema.sql (Database schema)
│
├── domains/ (Per-domain configs - auto-generated from CSV)
│   ├── soulfra.com/
│   ├── howtocookathome.com/
│   └── ... (200+ folders)
│
└── archive/ (Old stuff moved here)
    ├── old-scripts/ (190 Python files)
    └── old-docs/ (133 Markdown files)
```

---

## Database Strategy:

### Development (Now):
- **SQLite**: Simple, local, no setup required
- **File**: `database/soulfra.db`
- **Pros**: Easy, fast, works locally
- **Cons**: Single file, not for production

### Production (Later):
- **Postgres**: Robust, scalable, production-ready
- **Hosted**: Digital Ocean, AWS RDS, or self-hosted
- **Migration**: One command (`python3 database/migrate.py`)

### Migration Path:
```bash
# Export SQLite → SQL file
python3 database/migrate.py export

# Import SQL file → Postgres
python3 database/migrate.py import --postgres-url="postgresql://user:pass@host/db"
```

---

## Control Panel Features:

### Visit: `http://localhost:5001/control`

**Dashboard**:
- 📊 Total domains: 200+
- ✅ Deployed: X
- ⏳ Staging: Y
- 🔧 Development: Z

**Domain Management**:
- View all 200+ domains in table
- Search/filter by category, tier, status
- Add/edit/delete domains
- Bulk operations

**Chat with Ollama**:
- Click "💬 Chat" on any domain
- Discuss purpose, audience, strategy
- Ollama suggests articles, features, connections
- Approve/reject suggestions

**SSL Certificates**:
- Generate Let's Encrypt certs
- Renew expiring certs
- View cert status for all domains

**Deployment**:
- Deploy specific domain to production
- Deploy all domains at once
- Rollback if needed
- View deployment logs

**Database**:
- View database stats
- Run migrations
- Export SQLite → Postgres
- Validate data integrity

---

## How To Add Your 200+ Domains:

### Option 1: Manual CSV Editing

1. Open `domains-master.csv`
2. Copy the template line
3. Fill in all 200+ domains
4. Save
5. Run `python3 import_domains_csv.py`

**Example CSV line**:
```csv
MyBlog,myblog.com,cooking,creative,🍳,blog,"Quick recipes","Parents 25-45","30-min meals",false,false
```

### Option 2: Programmatic Generation

If you have domains in another format (Excel, JSON, database):

```python
import csv

# Your existing domain list
domains = [
    {"name": "Domain1", "url": "domain1.com", ...},
    {"name": "Domain2", "url": "domain2.com", ...},
    # ... 200+ more
]

# Write to CSV
with open('domains-master.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'domain', 'category', ...])
    writer.writeheader()
    for domain in domains:
        writer.writerow(domain)

# Then import
import_domains_csv.py
```

### Option 3: Web UI Bulk Add

Visit control panel:
1. Go to `/control/domains/bulk-add`
2. Paste all 200 domain names (one per line)
3. Ollama analyzes each domain
4. You approve/edit suggested details
5. Bulk import to database

---

## Frontend vs Backend Refresh:

### Why You Don't See Changes:

**Backend (Flask)**:
- You edit `app.py` or templates
- Flask needs to restart to load new code
- Multiple Flask instances can run simultaneously
- You might hit an old instance

**Frontend (Browser)**:
- Browser caches HTML/CSS/JS
- Even after Flask restarts, browser shows old page
- Need to hard refresh

### How To Fix:

1. **Kill all Flask instances**:
   ```bash
   ./RESTART-FLASK-CLEAN.sh
   ```

2. **Hard refresh browser**:
   - Mac: `Cmd+Shift+R`
   - Windows: `Ctrl+Shift+R`
   - Or: Open DevTools → Disable cache

3. **Verify latest code loaded**:
   ```bash
   curl http://localhost:5001/control | grep "Control Panel"
   ```

---

## Deployment Path:

### Step 1: Development (Local)
```
Database: SQLite (database/soulfra.db)
URL: http://localhost:5001
SSL: No (localhost doesn't need it)
Domains: Test with 5-10 domains first
```

### Step 2: Staging (Optional)
```
Database: Postgres (hosted)
URL: https://staging.soulfra.com
SSL: Let's Encrypt (auto-generated)
Domains: All 200+ domains
```

### Step 3: Production
```
Database: Postgres (production)
URL: https://soulfra.com + 200 other domains
SSL: Let's Encrypt for all domains
Domains: All 200+ live
```

### Deployment Script:
```bash
# From control panel:
python3 control/deploy.py --env=production

# Or manually:
python3 database/migrate.py export
# Upload to production server
python3 database/migrate.py import --postgres-url="..."
# Configure Nginx/Caddy for 200+ domains
# Generate SSL certs for all
```

---

## SSL Certificate Management:

### For All 200+ Domains:

**Control panel handles this**:
1. Reads all domains from database
2. For each domain:
   - Generates Let's Encrypt cert
   - Configures web server (Nginx/Caddy)
   - Renews before expiration
3. Status dashboard shows cert health

**Manual (if needed)**:
```bash
# Generate cert for one domain
certbot certonly --standalone -d example.com

# Generate for all domains
python3 control/ssl.py generate-all

# Renew all expiring certs
python3 control/ssl.py renew
```

---

## Database Schema:

### Core Tables:

**brands** - All 200+ domains
```sql
- id, name, slug, domain
- category, tier, emoji, brand_type
- tagline, target_audience, purpose
- ssl_enabled, deployed
- created_at
```

**domain_conversations** - Chat history with Ollama
```sql
- id, brand_id, role, message
- created_at
```

**domain_suggestions** - Ollama recommendations
```sql
- id, brand_id, suggestion_type
- title, description, status
- created_at, approved_at
```

**ssl_certificates** - SSL cert tracking
```sql
- id, domain, cert_path
- expires_at, last_renewed
```

**deployments** - Deployment history
```sql
- id, brand_id, environment
- deployed_at, status, logs
```

---

## What To Do Next:

### Day 1: Setup
1. ✅ Read this README
2. Fill in `domains-master.csv` with all 200+ domains
3. Run `python3 import_domains_csv.py`
4. Start control panel: `./RESTART-FLASK-CLEAN.sh`
5. Visit: `http://localhost:5001/control`

### Day 2-7: Domain Onboarding
1. For each domain, click "💬 Chat"
2. Tell Ollama about the domain (2-3 min conversation)
3. Approve suggestions
4. Move to next domain
5. After 200 domains: Ollama knows your entire empire

### Week 2: Deploy Staging
1. Setup Postgres database
2. Migrate SQLite → Postgres
3. Deploy to staging.soulfra.com
4. Test with real domains
5. Generate SSL certs

### Week 3: Production
1. Deploy to soulfra.com
2. Configure all 200+ domains
3. Generate SSL for all
4. Go live!

---

## Troubleshooting:

### Chat buttons don't appear
1. Run `./RESTART-FLASK-CLEAN.sh`
2. Hard refresh browser (`Cmd+Shift+R`)
3. Check Flask logs for errors

### Database errors
1. Check `database/soulfra.db` exists
2. Run `python3 import_domains_csv.py` to rebuild
3. Check schema: `sqlite3 database/soulfra.db ".schema"`

### Ollama not responding
1. Check Ollama is running: `curl http://localhost:11434/api/version`
2. Start Ollama: `ollama serve`
3. Check model exists: `ollama list`

### Deployment fails
1. Check Postgres connection
2. Verify SSL certs generated
3. Check web server config (Nginx/Caddy)
4. View logs: `tail -f control/deploy.log`

---

## Summary:

**This is your domain empire control center.**

- **One codebase** manages 200+ domains
- **One database** stores all domain data
- **One control panel** (`/control`) manages everything
- **One CSV file** (`domains-master.csv`) is source of truth
- **Soulfra.com** is the hub that controls all others

**Start with**: Filling in `domains-master.csv` with all your domains.

**Then**: Import, chat with Ollama, deploy.

**Questions**: This README has all the answers. Read it thoroughly.
