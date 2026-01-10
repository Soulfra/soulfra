# 🔒 SECURITY AUDIT REPORT
**Date:** 2026-01-02
**System:** Soulfra Multi-Domain Publishing Platform

---

## 🚨 Executive Summary

**Severity:** 🔴 **HIGH**
**Total PII Exposures Found:** 65+

### Critical Findings
1. ✅ **Email addresses** stored in plaintext (10+ in users table)
2. ✅ **IP addresses** stored in plaintext (10+ in qr_scans table)
3. ✅ **IP addresses** leaked in log files (53+ instances in Flask logs, 6+ in Ollama logs)
4. ⚠️ **GPS coordinates** table exists (dm_channels has location_lat/lon columns)
5. ⚠️ **Voice encryption** infrastructure exists but usage unknown

---

## 📊 Detailed Findings

### 1. Database - Users Table
**Table:** `users`
**PII Type:** Email Addresses
**Status:** 🔓 **PLAINTEXT (NOT ENCRYPTED)**

**Exposed Emails:**
- `admin@soulfra.local`
- `soul_tester@soulfra.local`
- `user_e0e5bd30@qr.local`
- `calriven@soulfra.ai`
- `deathtodata@soulfra.ai`
- `soulfra@soulfra.ai`
- `howtocookathome@soulfra.ai`
- `system@soulfra.com`
- `voice_calriven_9@voice.soulfra.local`
- `voice_calriven_10@voice.soulfra.local`

**Risk Level:** MEDIUM
**Justification:** These appear to be system/test accounts, not real user emails. However, if real users are added, their emails would be exposed.

**Recommendation:**
- Hash or encrypt email addresses in database
- Use email hashing for lookups (SHA-256 + salt)
- Consider pseudonymization (store hash, not plaintext)

---

### 2. Database - QR Scans Table
**Table:** `qr_scans`
**PII Type:** IP Addresses
**Status:** 🔓 **PLAINTEXT (NOT ENCRYPTED)**

**Exposed IPs:**
- `127.0.0.1` (localhost - safe)
- `192.168.1.123` (6+ instances - **REAL NETWORK IP**)
- `192.168.1.122` (1 instance - **REAL NETWORK IP**)
- `192.168.1.87` (your laptop IP - **EXPOSED IN LOGS**)

**Risk Level:** HIGH
**Justification:** These are REAL network IPs from your roommates/network devices scanning QR codes. If this database is ever compromised, attackers know:
- Who scanned what QR code
- When they scanned it
- Their device's network IP
- Can correlate scans to identify individuals

**Recommendation:**
1. **Hash IP addresses** before storing:
   ```python
   import hashlib
   ip_hash = hashlib.sha256(f"{ip_address}:salt".encode()).hexdigest()[:16]
   # Store ip_hash instead of ip_address
   ```
2. **Or pseudonymize** - store first 2 octets only: `192.168.x.x`
3. **Add encryption** for full IP if needed for analytics

---

### 3. Log Files - Flask Logs
**File:** `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/logs/assistant_errors.log`
**PII Type:** IP Addresses
**Status:** 🔓 **PLAINTEXT IN LOGS**
**Instances:** 53+

**Sample Log Lines:**
```
2025-12-26 13:20:27,124 - werkzeug - INFO - 127.0.0.1 - - [26/Dec/2025 13:20:27] "POST /api/assistant...
2025-12-26 13:20:37,224 - werkzeug - INFO - 127.0.0.1 - - [26/Dec/2025 13:20:37] "GET /@docs/ENCRYPT...
```

**Risk Level:** MEDIUM
**Justification:** Logs contain request details with IP addresses. If logs are shared, backed up to cloud, or accessed by unauthorized users, IPs are exposed.

**Recommendation:**
1. **Redact IPs in logs:**
   ```python
   # In unified_logger.py or Flask logger config
   ip_redacted = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'X.X.X.X', log_message)
   ```
2. **Use log rotation** - delete logs older than 30 days
3. **Store logs securely** - encrypt log files at rest

---

### 4. Log Files - Ollama Logs
**File:** `/tmp/ollama.log`
**PII Type:** IP Addresses
**Status:** 🔓 **PLAINTEXT IN LOGS**
**Instances:** 6+

**Sample Log Lines:**
```
[GIN] 2026/01/02 - 12:25:41 | 200 |    8.561625ms |    192.168.1.87 | GET      "/api/tags"
[GIN] 2026/01/02 - 12:25:44 | 200 |      3.6145ms |    192.168.1.87 | GET      "/api/tags"
[GIN] 2026/01/02 - 12:25:45 | 404 |       5.875µs |    192.168.1.87 | GET      "/favicon.ico"
```

**Risk Level:** MEDIUM-HIGH
**Justification:** Your laptop's IP (`192.168.1.87`) is logged in Ollama. This confirms network access is working, but also means **every API call to Ollama logs the client IP**.

**Recommendation:**
1. **Configure Ollama to disable IP logging** (if possible)
2. **Rotate /tmp/ollama.log frequently** (it's in /tmp so it clears on reboot, but could grow large)
3. **Filter Ollama logs** before backing up or sharing

---

### 5. Database - DM Channels (GPS Coordinates)
**Table:** `dm_channels`
**Columns:** `location_lat`, `location_lon`
**Status:** ⚠️ **TABLE EXISTS (usage unknown)**

**Risk Level:** POTENTIALLY CRITICAL
**Justification:** If GPS coordinates are being stored when users scan QR codes for DMs, this is **highly sensitive PII**. GPS coordinates can:
- Reveal home addresses
- Track user movements
- Identify locations of in-person meetings
- Be used for stalking/harassment

**Recommendation:**
1. **Verify if GPS coords are being collected** - check dm_via_qr.py
2. **If collected: ENCRYPT IMMEDIATELY:**
   ```python
   from voice_encryption import encrypt_voice_memo

   # Encrypt GPS coords before storing
   encrypted = encrypt_voice_memo(f"{lat},{lon}".encode())
   # Store: encrypted_data, encryption_key, encryption_iv
   ```
3. **Or use geohashing** - store coarse location (city-level) instead of precise coords
4. **Add user consent** - explicitly ask permission to store location

---

## 🔐 Encryption Status

### Voice Encryption System
**File:** `voice_encryption.py`
**Status:** ✅ **EXISTS**
**Algorithm:** AES-256-GCM (authenticated encryption)
**Usage:** ⚠️ **UNKNOWN**

**Findings:**
- `voice_encryption.py` implements proper AES-256-GCM encryption
- No evidence that it's being used for voice memos (voice_memos table columns not found)
- **Recommendation:** Use this same encryption for GPS coordinates, sensitive user data

---

## 💡 Recommendations (Priority Order)

### 🔴 CRITICAL (Fix Immediately)
1. **Hash IP addresses** in `qr_scans` table before storage
2. **Verify GPS coordinate storage** in `dm_channels` table
3. **Encrypt GPS coordinates** if being collected
4. **Add IP redaction** to Flask logging

### 🟡 HIGH (Fix This Week)
5. **Implement email hashing** for new users
6. **Add log rotation** (30-day retention max)
7. **Filter Ollama logs** before backup
8. **Test API endpoints** for PII leaks (manual testing required)

### 🟢 MEDIUM (Fix This Month)
9. **Document encryption policies** in SOC2-GDPR-COMPLIANCE.md
10. **Add PII detection** to CI/CD pipeline
11. **Implement auto-redaction** in unified_logger.py
12. **Create privacy policy** for users

---

## 🧪 Testing Recommendations

### Manual API Testing Required
Test these endpoints for PII exposure:
```bash
# Test each endpoint and check response for PII
curl http://localhost:5001/api/chat/send | grep -E 'email|ip_address|location'
curl http://localhost:5001/api/questions/submit | grep -E 'email|ip_address|location'
curl http://localhost:5001/api/analytics/qr | grep -E 'email|ip_address|location'
curl http://localhost:5001/status | grep -E 'email|ip_address|location'
```

### Network Testing
Test from roommate device (192.168.1.x):
```bash
# From roommate's computer
curl http://192.168.1.87:5001/api/tags | grep ip
curl http://192.168.1.87:5001/status | grep -E 'location|ip_address'
```

---

## 📝 Summary

### What's Good ✅
- Voice encryption infrastructure exists (AES-256-GCM)
- System/test emails (not real user data)
- Localhost IPs in logs (127.0.0.1) - acceptable

### What's Concerning ⚠️
- Real network IPs stored in plaintext (192.168.1.x)
- IP addresses in log files (53+ instances)
- GPS coordinate columns exist (potential PII storage)

### What Needs Immediate Action 🚨
1. Hash IP addresses in qr_scans table
2. Verify GPS coordinate usage
3. Encrypt GPS if being used
4. Redact IPs from logs

---

## 🔄 Next Steps

1. **Fix IP storage** in qr_scans table
2. **Update unified_logger.py** with PII redaction
3. **Re-run audit** to verify fixes
4. **Test on localhost + network** (192.168.1.87)
5. **Document encryption policies**

---

**Audit Completed:** 2026-01-02
**Audited By:** audit_pii_exposure.py v1.0
**Re-audit Recommended:** After fixes applied
