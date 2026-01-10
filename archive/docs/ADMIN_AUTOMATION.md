# Admin Automation - Integrated Build-in-Public System

## Overview

Instead of running separate Python scripts via cron, you can now run all automation **from within the admin panel**. This integrates the build-in-public workflow directly into Soulfra's web interface.

---

## Access the Automation Panel

1. Login to admin: http://localhost:5001/admin/login
2. Navigate to: **Admin → Automation**
3. Or visit directly: http://localhost:5001/admin/automation

---

## User Roles & Permissions

### Role Tiers

| Role | Permissions |
|------|------------|
| **sysadmin** | Full access: automation, system settings, all features |
| **admin** | Can run automation, create posts, manage subscribers |
| **user** | Regular user: posts, comments (no admin access) |

### Set User Role

```sql
-- Make a user sysadmin
UPDATE users SET role = 'sysadmin' WHERE username = 'your_username';

-- Make a user admin
UPDATE users SET role = 'admin' WHERE username = 'someone';

-- Set back to regular user
UPDATE users SET role = 'user' WHERE username = 'someone';
```

Or via Python:
```python
from database import get_db

db = get_db()
db.execute("UPDATE users SET role = 'sysadmin' WHERE username = ?", ('calriven',))
db.commit()
db.close()
```

---

## Automation Features

### 1. Public Builder 🏗️

**What it does:**
- Checks feedback for high-priority items (bugs, features)
- CalRiven auto-creates posts documenting fixes
- Reasoning engine analyzes posts
- Updates feedback status to "in-progress"

**Run from admin panel:**
1. Go to Admin → Automation
2. Click "▶️ Run Now" under Public Builder
3. See results immediately

**Or run manually:**
```bash
python3 public_builder.py
```

**Or via cron:**
```bash
# Hourly
0 * * * * cd /path/to/soulfra && python3 public_builder.py
```

---

### 2. Weekly Newsletter Digest 📧

**What it does:**
- Groups feedback by theme (keyword similarity)
- Analyzes AI consensus/disagreement
- Creates decision questions with clickable buttons
- Saves preview to `weekly_digest_preview.html`

**Run from admin panel:**
1. Go to Admin → Automation
2. Click "📝 Generate Preview" to create HTML preview
3. Click "📤 Send to Subscribers" to email all subscribers

**Or run manually:**
```bash
# Generate preview only
python3 newsletter_digest.py

# Or import and call
python3 -c "from newsletter_digest import send_weekly_digest; send_weekly_digest(dry_run=True)"
```

**Or via cron:**
```bash
# Weekly (Sunday 8pm)
0 20 * * 0 cd /path/to/soulfra && python3 newsletter_digest.py
```

---

### 3. QR Time Capsule 🔗

**Status:** Auto-tracking (always active)

Automatically tracks all QR code scans:
- Records who/when/where each scan happened
- Links scans together (chain tracking)
- Shows "Last scanned by X in Y, Z hours ago"

**View stats:**
- Admin → Automation → "📊 View Stats" (coming soon)
- Or query directly:

```sql
-- Count total scans
SELECT COUNT(*) FROM qr_scans;

-- View scan chain for QR code #1
WITH RECURSIVE chain AS (
    SELECT *, 0 as depth FROM qr_scans WHERE qr_code_id = 1
    ORDER BY scanned_at DESC LIMIT 1
    UNION ALL
    SELECT s.*, c.depth + 1
    FROM qr_scans s JOIN chain c ON s.id = c.previous_scan_id
)
SELECT * FROM chain ORDER BY depth;
```

---

### 4. Reasoning Engine 💭

**Status:** Auto-analyzing (always active)

AI personas automatically analyze all new posts:
- **CalRiven**: Technical analysis
- **TheAuditor**: Validation
- **Soulfra**: Platform perspective
- **DeathToData**: Critical questions

**View threads:**
- Navigate to: http://localhost:5001/reasoning

---

## Integration vs Scripts

### Before (Separate Scripts)
```
❌ Run public_builder.py manually
❌ Run newsletter_digest.py manually
❌ No visibility into automation status
❌ No role-based permissions
❌ Cron jobs only (no web interface)
```

### After (Integrated)
```
✅ Run from admin panel with one click
✅ See results immediately with flash messages
✅ Role-based permissions (sysadmin/admin/user)
✅ Can still use cron for scheduling
✅ All automation in one place
```

---

## The Full Integrated Stack

```
┌─────────────────────────────────────────┐
│         PUBLIC INTERACTION              │
│  /feedback (no login required)          │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│    ADMIN AUTOMATION PANEL               │
│  /admin/automation                      │
│                                         │
│  ▶️ Run Public Builder                  │
│  📝 Generate Digest                     │
│  📤 Send to Subscribers                 │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│      EXISTING SYSTEM                    │
│  • emails.py (send_post_email)          │
│  • database.py (get_subscribers)        │
│  • reasoning_engine.py (analyze)        │
│  • QR tracking (auto)                   │
└─────────────────────────────────────────┘
```

**Everything is integrated.** No more separate scripts that feel disconnected!

---

## Quick Start

1. **Initialize roles:**
   ```bash
   python3 init_user_roles.py
   ```

2. **Set yourself as sysadmin:**
   ```python
   from database import get_db
   db = get_db()
   db.execute("UPDATE users SET role = 'sysadmin' WHERE username = 'admin'")
   db.commit()
   db.close()
   ```

3. **Start the app:**
   ```bash
   python3 app.py
   ```

4. **Login and visit:**
   - http://localhost:5001/admin/automation

5. **Run automation:**
   - Click "▶️ Run Now" to test public builder
   - Click "📝 Generate Preview" to test digest

---

## Files Changed

| File | Changes |
|------|---------|
| `app.py` | Added `/admin/automation` routes |
| `public_builder.py` | Returns results dict for web interface |
| `templates/admin_automation.html` | New automation panel UI |
| `templates/admin_dashboard.html` | Added "Automation" nav link |
| `templates/admin_subscribers.html` | Added "Automation" nav link |
| `init_user_roles.py` | Migration to add role column |
| `database.py` | Users now have `role` field |

---

## Next Steps

### Enable Scheduled Automation

Set up cron jobs to run automation on a schedule:

```bash
crontab -e
```

Add:
```bash
# Public builder - hourly
0 * * * * cd /path/to/soulfra && python3 public_builder.py >> logs/builder.log 2>&1

# Newsletter digest - weekly (Sunday 8pm)
0 20 * * 0 cd /path/to/soulfra && python3 newsletter_digest.py >> logs/digest.log 2>&1
```

### Monitor Logs

```bash
mkdir -p logs
tail -f logs/builder.log
tail -f logs/digest.log
```

---

## Philosophy

**Before:** Scripts felt like external tools bolted onto the platform

**After:** Automation is built INTO the platform, using the existing newsletter/email system

**This is dogfooding.** The platform automates itself using its own systems. 🚀
