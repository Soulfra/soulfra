# Database Migrations - "Schema is Code"

This folder contains SQL migrations that define the entire Soulfra database schema.

## Philosophy

**The database schema IS the code.** No manual SQL. No hidden setup. Just numbered SQL files that build the platform from scratch.

This proves:
- ✅ **Reproducible** - Anyone can rebuild the exact same schema
- ✅ **Versioned** - Schema changes tracked like git commits
- ✅ **Auditable** - See exactly what changed and when
- ✅ **OSS-ready** - Standard migration pattern (like Rails/Django)

## Migration Files

Migrations run in numerical order:

```
001_initial_schema.sql        - Core 6 tables (users, posts, comments, etc.)
002_add_excerpt_to_posts.sql  - Post excerpts for homepage previews
003_add_reasoning_tables.sql  - AI reasoning, categories, tags
004_add_qr_tracking.sql       - QR codes and scan tracking
005_add_images_table.sql      - Database-first image storage
006_add_soul_history.sql      - Git for souls (version control)
007_add_url_shortcuts.sql     - Short URLs for QR codes
008_add_reputation_system.sql - Perfect Bits reputation tracking
009_add_ml_tables.sql         - ML models (Python stdlib only)
010_add_feedback_table.sql    - Public bug reporting
```

**Total:** 22 tables + schema_migrations tracking table = 23 tables

## Usage

### Apply Migrations

```bash
# Apply all pending migrations
python3 migrate.py

# Show migration status
python3 migrate.py status

# Reset database (WARNING: deletes all data!)
python3 migrate.py reset
```

### Verify Reproducibility

Prove the platform can be built "from scratch":

```bash
python3 verify_from_scratch.py
```

This script:
1. Backs up existing database
2. Deletes database
3. Rebuilds from migrations alone
4. Verifies all 22 tables exist
5. Reports success/failure

### Adding New Migrations

1. Create new file: `migrations/011_your_change.sql`
2. Write SQL (CREATE TABLE, ALTER TABLE, etc.)
3. Run `python3 migrate.py` to apply
4. Commit migration file to git

**Example migration:**

```sql
-- Migration 011: Add Email Verification
-- Track email verification tokens

CREATE TABLE IF NOT EXISTS email_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_email_verifications_token
ON email_verifications(token);
```

## Migration Tracking

The `schema_migrations` table tracks which migrations have been applied:

```sql
SELECT * FROM schema_migrations ORDER BY version;
```

Output:
```
version | name              | applied_at
--------|-------------------|---------------------------
001     | initial_schema    | 2025-12-21T23:11:16.890817
002     | add_excerpt       | 2025-12-21T23:11:16.892875
...
010     | add_feedback      | 2025-12-21T23:11:16.942262
```

## Current Schema Version

Check current version:

```bash
python3 migrate.py status
```

Output shows:
- ✅ Applied migrations
- ⏳ Pending migrations
- Current schema version (e.g., `010_add_feedback_table`)

## Rollback

**There is no rollback.** Migrations are forward-only.

If you need to undo a change:
1. Create a new migration that reverses it
2. Example: `011_remove_field.sql` with `ALTER TABLE DROP COLUMN`

This maintains full audit trail.

## Production Deployment

Before deploying:

1. **Backup database:**
   ```bash
   cp soulfra.db soulfra.db.backup
   ```

2. **Test migrations locally:**
   ```bash
   python3 migrate.py
   ```

3. **Verify no errors:**
   ```bash
   python3 migrate.py status
   ```

4. **Deploy:**
   - Push migration files to server
   - Run `python3 migrate.py` on server
   - Migrations are idempotent (safe to re-run)

## Why This Matters

Before migrations:
- ❌ Schema scattered across 10+ init scripts
- ❌ No version tracking
- ❌ Can't prove reproducibility
- ❌ "It works on my machine"

After migrations:
- ✅ Schema is code (SQL files)
- ✅ Version tracked in database
- ✅ Provably reproducible from scratch
- ✅ Standard OSS pattern
- ✅ "Fork repo, run migrations, it works"

## Verification Proof

Run `verify_from_scratch.py` - this proves:

```
✅ SUCCESS - Platform is reproducible from scratch!

Schema version: 010_add_feedback_table
Total tables: 23

🎉 OSS Principle Validated:
   • Schema is code (migrations/*.sql)
   • Reproducible (delete DB, run migrations, everything works)
   • Versioned (schema_migrations tracks state)
   • Auditable (see exactly what changed when)
```

That's the answer to: "how do we know this was all working or whatever then and oss or something from scratch?"

**This is how.**
