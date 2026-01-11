# Soulfra Automation Guide

## Build-in-Public Automation

Soulfra builds itself in public using automated workflows that connect feedback, posts, reasoning, and QR codes.

---

## public_builder.py - The Core Engine

**What it does:**
1. Checks feedback table for high-priority items
2. CalRiven auto-creates posts documenting fixes/features
3. Reasoning engine analyzes posts (TheAuditor, Soulfra, DeathToData respond)
4. Updates feedback status to "in-progress"
5. Links feedback → post for traceability

**Run manually:**
```bash
python3 public_builder.py
```

**Run via cron (every hour):**
```bash
# Edit crontab
crontab -e

# Add this line
0 * * * * cd /path/to/soulfra-simple && /usr/bin/python3 public_builder.py >> logs/public_builder.log 2>&1
```

---

## QR Time Capsule

**How it works:**
- Each QR code has unique ID
- When scanned, records: who, when, where, device
- Links to previous scan (creates chain)
- Shows "Last scanned by X in Y, Z hours ago"

**Generate QR:**
```python
from database import get_db

db = get_db()
db.execute('''
    INSERT INTO qr_codes (code_type, code_data, target_url, created_by)
    VALUES (?, ?, ?, ?)
''', ('soul', 'calriven', 'http://soulfra.com/soul/calriven', 1))
db.commit()
qr_id = db.lastrowid
db.close()

# QR URL: http://soulfra.com/qr/{qr_id}
```

**View scan chain:**
```sql
-- Get full scan chain for QR code
WITH RECURSIVE scan_chain AS (
    -- Start with latest scan
    SELECT id, scanned_by_name, location_city, scanned_at, previous_scan_id, 0 as depth
    FROM qr_scans
    WHERE qr_code_id = 1
    ORDER BY scanned_at DESC
    LIMIT 1
    
    UNION ALL
    
    -- Follow chain backwards
    SELECT s.id, s.scanned_by_name, s.location_city, s.scanned_at, s.previous_scan_id, sc.depth + 1
    FROM qr_scans s
    JOIN scan_chain sc ON s.id = sc.previous_scan_id
)
SELECT * FROM scan_chain ORDER BY depth;
```

---

## Feedback → Post → Reasoning Loop

**Automatic workflow:**

```
1. User submits feedback
   ↓
2. public_builder.py runs (hourly cron)
   ↓
3. High-priority feedback triggers post creation
   ↓
4. CalRiven creates post with quote from feedback
   ↓
5. Reasoning engine analyzes post
   ↓
6. TheAuditor, Soulfra, DeathToData comment
   ↓
7. Feedback status updated to "in-progress"
   ↓
8. Post shows up on homepage
```

**Priority scoring:**
- Bug keywords (bug, broken, error): +10 points
- Feature keywords (should, could, want): +5 points
- Critical components (Reasoning Engine, Admin): +5 points
- Threshold: 10+ points = auto-create post

---

## Email Digests

**Weekly digest (run Sunday night):**
```bash
# Add to crontab
0 20 * * 0 cd /path/to/soulfra-simple && /usr/bin/python3 -c "from emails import send_weekly_digest; send_weekly_digest()" >> logs/digest.log 2>&1
```

**What it includes:**
- Feedback received this week
- Posts created from feedback
- Reasoning highlights
- QR scan stats

---

## Test Automation

**Daily test runs:**
```bash
# Run all tests daily at 2am
0 2 * * * cd /path/to/soulfra-simple && /usr/bin/python3 -m pytest test_*.py >> logs/tests.log 2>&1
```

**Auto-report failures:**
```python
# If tests fail, auto-submit feedback
import subprocess
result = subprocess.run(['pytest'], capture_output=True)
if result.returncode != 0:
    # Submit feedback about test failure
    db.execute('''
        INSERT INTO feedback (name, component, message, status)
        VALUES (?, ?, ?, ?)
    ''', ('Automated Tests', 'Testing', f'Tests failed:\n{result.stderr}', 'new'))
```

---

## Monitoring

**Log files:**
```bash
mkdir -p logs
tail -f logs/public_builder.log
tail -f logs/digest.log
tail -f logs/tests.log
```

**Check automation status:**
```bash
# List cron jobs
crontab -l

# Check if public_builder ran recently
ls -lah logs/public_builder.log

# Count posts created by automation
sqlite3 soulfra.db "SELECT COUNT(*) FROM posts WHERE content LIKE '%auto-generated%'"
```

---

## Production Setup

**systemd service (alternative to cron):**

```ini
# /etc/systemd/system/soulfra-builder.service
[Unit]
Description=Soulfra Public Builder
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/var/www/soulfra-simple
ExecStart=/usr/bin/python3 public_builder.py

[Install]
WantedBy=multi-user.target
```

**systemd timer:**
```ini
# /etc/systemd/system/soulfra-builder.timer
[Unit]
Description=Run Soulfra Builder hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable:**
```bash
sudo systemctl enable soulfra-builder.timer
sudo systemctl start soulfra-builder.timer
sudo systemctl status soulfra-builder.timer
```

---

## The Full Build-in-Public Stack

```
┌─────────────────┐
│  Public Feedback│  ← Users report bugs/features
└────────┬────────┘
         ↓
┌─────────────────┐
│ public_builder  │  ← Runs hourly (cron/systemd)
│   (automation)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  CalRiven Posts │  ← Auto-creates posts
└────────┬────────┘
         ↓
┌─────────────────┐
│ Reasoning Engine│  ← AIs analyze & comment
└────────┬────────┘
         ↓
┌─────────────────┐
│   QR Codes      │  ← Generate tracking QRs
└────────┬────────┘
         ↓
┌─────────────────┐
│ Email Digest    │  ← Weekly summary
└─────────────────┘
```

**This is Soulfra building itself in public!** 🚀
