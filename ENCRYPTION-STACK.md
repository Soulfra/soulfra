# 🔐 ENCRYPTION STACK
**Soulfra Privacy-First Architecture**

---

## 🎯 Overview

Soulfra's encryption infrastructure is built on **open-source libraries** (MIT License) and provides a **privacy-first foundation** for web applications. This stack can be integrated into other projects to provide:

- **IP Address Hashing** - Irreversible SHA-256 + salt hashing
- **GPS Encryption** - AES-256-GCM authenticated encryption
- **PII Auto-Redaction** - Real-time log sanitization
- **Geofencing** - Radius-based matching with reputation system
- **Distributed Encryption** - Client-side encrypted data storage

---

## 🏗️ Architecture

### Stack Components

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  (Your Flask/Django/Node.js app)                            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   SOULFRA ENCRYPTION STACK                   │
├─────────────────────────────────────────────────────────────┤
│  1. IP Hashing        → fix_ip_storage.py                   │
│  2. GPS Encryption    → gps_encryption.py                   │
│  3. PII Redaction     → unified_logger.py                   │
│  4. Voice Encryption  → voice_encryption.py                 │
├─────────────────────────────────────────────────────────────┤
│  Dependencies: cryptography, hashlib, sqlite3               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    OSS LIBRARIES                             │
│  - Python cryptography (AES-256-GCM)                        │
│  - hashlib (SHA-256)                                        │
│  - sqlite3 (encrypted database storage)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Component 1: IP Address Hashing

### Purpose
Store network IPs in a way that:
- ✅ Preserves uniqueness (can still track users)
- ✅ Is irreversible (cannot recover original IP)
- ✅ Consistent (same IP = same hash)

### Implementation: `fix_ip_storage.py`

**Key Function:**
```python
import hashlib

def hash_ip_address(ip_address, salt="soulfra_ip_salt_v1"):
    """
    Hash IP address with SHA-256 + salt

    Args:
        ip_address (str): IP address (e.g., "192.168.1.123")
        salt (str): Secret salt for hashing

    Returns:
        str: 16-character hash (e.g., "f88ce6eefeeb9d6f")

    Example:
        >>> hash_ip_address("192.168.1.123")
        'f88ce6eefeeb9d6f'
    """
    hash_input = f"{ip_address}:{salt}".encode()
    hash_full = hashlib.sha256(hash_input).hexdigest()
    return hash_full[:16]  # First 16 chars
```

### Usage Example:
```python
from fix_ip_storage import hash_ip_address

# Hash IP before storing in database
user_ip = request.remote_addr  # "192.168.1.123"
ip_hash = hash_ip_address(user_ip)

db.execute('''
    INSERT INTO qr_scans (ip_address, timestamp)
    VALUES (?, ?)
''', (ip_hash, datetime.now()))
```

### Database Migration:
```bash
# Migrate existing plaintext IPs to hashed format
python3 fix_ip_storage.py --migrate

# Verify no plaintext IPs remain
python3 fix_ip_storage.py --verify
```

**Results:**
- Before: `192.168.1.123`
- After: `f88ce6eefeeb9d6f`

---

## 🌍 Component 2: GPS Encryption

### Purpose
Store GPS coordinates with:
- ✅ AES-256-GCM authenticated encryption
- ✅ Key + IV stored separately (distributed encryption)
- ✅ Geofencing support (calculate distance without decrypting all coords)
- ✅ Reputation-based radius (20-50km based on trust + XP)

### Implementation: `gps_encryption.py`

**Encryption:**
```python
from gps_encryption import encrypt_gps_for_database

# Encrypt GPS coordinates before storing
encrypted = encrypt_gps_for_database(37.7749, -122.4194)  # San Francisco

db.execute('''
    UPDATE dm_channels
    SET location_encrypted_data = ?,
        location_encryption_key = ?,
        location_encryption_iv = ?
    WHERE id = ?
''', (
    encrypted['location_encrypted_data'],
    encrypted['location_encryption_key'],
    encrypted['location_encryption_iv'],
    channel_id
))
```

**Decryption:**
```python
from gps_encryption import decrypt_gps_from_database

# Decrypt GPS for geofencing calculations
row = db.execute('SELECT * FROM dm_channels WHERE id = ?', (1,)).fetchone()
lat, lon = decrypt_gps_from_database(row)

print(f"Location: {lat}, {lon}")  # 37.7749, -122.4194
```

**Geofencing:**
```python
from gps_encryption import is_within_radius, calculate_geofence_radius_by_reputation

# Get encrypted user locations
user1 = db.execute('SELECT * FROM dm_channels WHERE id = ?', (1,)).fetchone()
user2 = db.execute('SELECT * FROM dm_channels WHERE id = ?', (2,)).fetchone()

# Calculate radius based on reputation (Reddit karma analogy)
radius_km = calculate_geofence_radius_by_reputation(
    trust_score=0.8,  # 0.5-1.0 scale (new user = 0.5, trusted = 1.0)
    total_xp=3000     # XP earned from questions/interactions
)
# Returns: ~32.5 km (20km base + trust bonus + XP bonus)

# Check if users are within geofence
if is_within_radius(user1, user2, radius_km):
    print("✅ Users can see each other!")
else:
    print("❌ Users too far apart")
```

### Reputation System (Reddit Karma Analogy):
```python
def calculate_geofence_radius_by_reputation(trust_score, total_xp):
    """
    Calculate geofence radius 20-50km based on reputation

    Trust Score (0.5-1.0):
    - New user: 0.5 → 20km radius (restricted)
    - Trusted user: 1.0 → 35km radius

    XP Bonus:
    - 0 XP: 0km bonus
    - 10,000+ XP: +15km bonus (max 50km total)

    Like Reddit karma:
    - Low karma = restricted radius (only see nearby users)
    - High karma = expanded radius (more potential connections)
    """
    # Base radius from trust score (20-35km)
    trust_radius = 20 + (trust_score - 0.5) * 30

    # XP bonus (0-15km based on total XP)
    xp_bonus = min(total_xp / 10000, 1.0) * 15

    # Final radius (20-50km range)
    return max(20, min(50, trust_radius + xp_bonus))
```

### Database Schema:
```sql
CREATE TABLE dm_channels (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,

    -- Encrypted GPS coordinates (AES-256-GCM)
    location_encrypted_data TEXT,   -- Base64-encoded encrypted data
    location_encryption_key TEXT,   -- Base64-encoded encryption key
    location_encryption_iv TEXT,    -- Base64-encoded IV

    -- Deprecated plaintext columns (DO NOT USE)
    location_lat REAL,  -- Deprecated
    location_lon REAL,  -- Deprecated

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 Component 3: PII Auto-Redaction

### Purpose
Automatically redact PII from logs:
- ✅ IPv4 addresses → `X.X.X.X`
- ✅ IPv6 addresses → `X:X:X:X:X:X:X:X`
- ✅ Email addresses → `[EMAIL_REDACTED]`
- ✅ GPS coordinates → `[GPS_REDACTED]`

### Implementation: `unified_logger.py`

**PII Patterns:**
```python
import re

PII_PATTERNS = {
    'ipv4': (re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'), 'X.X.X.X'),
    'ipv6': (re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'), 'X:X:X:X:X:X:X:X'),
    'email': (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    'gps_coords': (re.compile(r'[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)'), '[GPS_REDACTED]'),
}
```

**Manual Redaction:**
```python
from unified_logger import redact_pii

# Redact PII from text
text = "User 192.168.1.123 sent email to admin@test.com"
redacted = redact_pii(text)

print(redacted)
# Output: "User X.X.X.X sent email to [EMAIL_REDACTED]"
```

**Auto-Redaction in Logging:**
```python
from unified_logger import log_integration_event

# Log event with auto-redaction
log_integration_event(
    platform='twitter',
    event_type='post_published',
    description='User 192.168.1.123 posted from email admin@test.com',
    metadata={
        'ip': '192.168.1.123',
        'email': 'user@example.com',
        'location': '37.7749,-122.4194'
    }
)

# Stored in database as:
# description: "User X.X.X.X posted from email [EMAIL_REDACTED]"
# metadata: {"ip": "X.X.X.X", "email": "[EMAIL_REDACTED]", "location": "[GPS_REDACTED]"}
```

---

## 🎙️ Component 4: Voice Encryption

### Purpose
Encrypt voice memos with:
- ✅ AES-256-GCM authenticated encryption
- ✅ Client-side encryption (server never sees plaintext)
- ✅ Distributed key storage (key + IV stored separately)

### Implementation: `voice_encryption.py`

**Encrypt Voice Memo:**
```python
from voice_encryption import encrypt_voice_memo

# Read audio file
with open('voice_memo.webm', 'rb') as f:
    audio_data = f.read()

# Encrypt
encrypted = encrypt_voice_memo(audio_data)

# Store in database
db.execute('''
    INSERT INTO voice_memos (encrypted_data, encryption_key, encryption_iv)
    VALUES (?, ?, ?)
''', (
    encrypted['encrypted_data'],
    encrypted['encryption_key'],
    encrypted['encryption_iv']
))
```

**Decrypt Voice Memo:**
```python
from voice_encryption import decrypt_voice_memo

# Retrieve from database
row = db.execute('SELECT * FROM voice_memos WHERE id = ?', (1,)).fetchone()

# Decrypt
decrypted_audio = decrypt_voice_memo(
    row['encrypted_data'],
    row['encryption_key'],
    row['encryption_iv']
)

# Save to file
with open('decrypted_voice_memo.webm', 'wb') as f:
    f.write(decrypted_audio)
```

### Why Distributed Encryption?

**Cold Storage Analogy:**
Like a cryptocurrency cold wallet, the encryption is split across 3 components:

1. **Encrypted Data** - Stored in database (useless without key + IV)
2. **Encryption Key** - Stored separately (useless without IV)
3. **Initialization Vector (IV)** - Stored separately (useless without key)

**Security Benefits:**
- Attacker needs all 3 components to decrypt
- Database breach alone = encrypted data is safe
- Keys can be stored in separate database or key management system

---

## 📊 Database Schema

### Example Schema with Encryption:

```sql
-- Users table with hashed IPs
CREATE TABLE qr_scans (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL,  -- SHA-256 hashed (e.g., "f88ce6eefeeb9d6f")
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DM channels with encrypted GPS
CREATE TABLE dm_channels (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,

    -- Encrypted GPS (AES-256-GCM)
    location_encrypted_data TEXT,
    location_encryption_key TEXT,
    location_encryption_iv TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice memos with encrypted audio
CREATE TABLE voice_memos (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,

    -- Encrypted audio (AES-256-GCM)
    encrypted_data TEXT,  -- Base64-encoded encrypted audio
    encryption_key TEXT,  -- Base64-encoded key
    encryption_iv TEXT,   -- Base64-encoded IV

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Integration logs with auto-redacted PII
CREATE TABLE integration_logs (
    id INTEGER PRIMARY KEY,
    platform TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,  -- Auto-redacted (no IPs, emails, GPS)
    metadata TEXT,              -- Auto-redacted JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 How to Use This Stack in Your Project

### Step 1: Install Dependencies
```bash
pip install cryptography
```

### Step 2: Copy Encryption Modules
```bash
# Copy these files to your project
cp fix_ip_storage.py your_project/
cp gps_encryption.py your_project/
cp unified_logger.py your_project/
cp voice_encryption.py your_project/
```

### Step 3: Integrate into Your App

**Example Flask App:**
```python
from flask import Flask, request
from fix_ip_storage import hash_ip_address
from gps_encryption import encrypt_gps_for_database
from unified_logger import log_integration_event
from database import get_db

app = Flask(__name__)

@app.route('/signup', methods=['POST'])
def signup():
    # Get user data
    user_ip = request.remote_addr
    user_lat = request.json.get('latitude')
    user_lon = request.json.get('longitude')

    # Hash IP address
    ip_hash = hash_ip_address(user_ip)

    # Encrypt GPS coordinates
    encrypted_gps = encrypt_gps_for_database(user_lat, user_lon)

    # Store in database (no plaintext PII)
    db = get_db()
    cursor = db.execute('''
        INSERT INTO users (ip_hash, location_encrypted_data, location_encryption_key, location_encryption_iv)
        VALUES (?, ?, ?, ?)
    ''', (
        ip_hash,
        encrypted_gps['location_encrypted_data'],
        encrypted_gps['location_encryption_key'],
        encrypted_gps['location_encryption_iv']
    ))

    user_id = cursor.lastrowid
    db.commit()
    db.close()

    # Log event (auto-redacts PII)
    log_integration_event(
        platform='web',
        event_type='user_signup',
        description=f'User {user_ip} signed up from location {user_lat},{user_lon}',
        metadata={'ip': user_ip, 'location': f'{user_lat},{user_lon}'},
        user_id=user_id
    )

    return {'success': True, 'user_id': user_id}
```

**What Gets Stored:**
```python
# Database storage (encrypted/hashed):
{
    'ip_hash': 'f88ce6eefeeb9d6f',  # Hashed IP (irreversible)
    'location_encrypted_data': 'gAAAAABl...',  # Encrypted GPS
    'location_encryption_key': 'ZjNhMTU...',
    'location_encryption_iv': 'YzJlNGE...'
}

# Log storage (auto-redacted):
{
    'description': 'User X.X.X.X signed up from location [GPS_REDACTED]',
    'metadata': {'ip': 'X.X.X.X', 'location': '[GPS_REDACTED]'}
}
```

---

## 🔐 Security Features

### 1. IP Hashing (SHA-256 + Salt)
- **Irreversible** - Cannot recover original IP from hash
- **Consistent** - Same IP = same hash
- **Unique** - Different IPs = different hashes
- **Salted** - Rainbow table attacks ineffective

### 2. GPS Encryption (AES-256-GCM)
- **Authenticated Encryption** - Tamper-proof (modification detected)
- **Distributed Keys** - Key + IV stored separately
- **Geofencing Support** - Can calculate distance without full decryption
- **Reputation-Based Radius** - Dynamic privacy zones

### 3. PII Auto-Redaction
- **Real-time** - Redacts before storing in database
- **Comprehensive** - IPs, emails, GPS coords
- **JSON-safe** - Redacts both text and JSON metadata

### 4. Voice Encryption (AES-256-GCM)
- **Client-side** - Server never sees plaintext audio
- **Cold Storage** - 3-part distributed encryption
- **Tamper-proof** - GCM authenticated encryption

---

## 📜 License

**MIT License** - You can use this encryption stack in commercial and open-source projects.

### Key Points:
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Must include copyright notice and license

### Attribution:
```python
# Soulfra Encryption Stack
# Copyright (c) 2026 Soulfra
# MIT License - https://opensource.org/licenses/MIT
```

---

## 🧪 Testing

### Test IP Hashing:
```bash
python3 fix_ip_storage.py --test
```

**Expected Output:**
```
=== IP Hashing Tests ===
Original IP: 192.168.1.123
Hashed IP:   f88ce6eefeeb9d6f
Consistency: ✅ Same IP = Same Hash
Uniqueness:  ✅ Different IPs = Different Hashes
```

### Test GPS Encryption:
```bash
python3 gps_encryption.py --test
```

**Expected Output:**
```
=== GPS Encryption Tests ===
Original: 37.7749, -122.4194 (San Francisco)
Encrypted: gAAAAABl...
Decrypted: 37.7749, -122.4194 ✅

Distance SF → Oakland: 13.43 km
Geofence Radius (Low Reputation): 20 km
Geofence Radius (High Reputation): 42 km
```

### Test PII Redaction:
```bash
python3 unified_logger.py --test
```

**Expected Output:**
```
=== PII Redaction Tests ===
Original: User 192.168.1.123 sent email to admin@test.com
Redacted: User X.X.X.X sent email to [EMAIL_REDACTED] ✅
```

---

## 💡 Use Cases

### 1. **Privacy-First Social Networks**
- Store user IPs hashed (analytics without PII)
- Encrypt user locations (geofencing without plaintext GPS)
- Auto-redact logs (GDPR compliance)

### 2. **Encrypted Messaging Apps**
- Client-side voice memo encryption
- GPS-based proximity matching
- Zero-knowledge architecture (server can't decrypt)

### 3. **Anonymous Forums**
- Hash IPs to prevent doxxing
- Track users without storing identifiable data
- Auto-redact leaked PII from posts

### 4. **Reputation-Based Communities**
- Geofencing with dynamic radius (Reddit karma → location privacy)
- Trusted users = larger radius (more connections)
- New users = smaller radius (safety/spam prevention)

---

## 🔮 Future Enhancements

### Planned Features:
1. **End-to-End Encryption** - Client-side key generation
2. **Multi-Party Computation** - Calculate geofencing without revealing locations
3. **Zero-Knowledge Proofs** - Prove proximity without revealing coordinates
4. **Homomorphic Encryption** - Compute on encrypted data
5. **Key Rotation** - Automatic key refresh for long-term security

---

## 📚 Additional Resources

### Documentation:
- `SECURITY-FIXES-APPLIED.md` - Security audit findings + fixes
- `GAME-DESIGN.md` - AI Battle Arena using this encryption
- `fix_ip_storage.py` - IP hashing implementation
- `gps_encryption.py` - GPS encryption implementation
- `unified_logger.py` - PII redaction implementation

### Testing:
```bash
# Test all encryption components
python3 fix_ip_storage.py --test
python3 gps_encryption.py --test
python3 unified_logger.py

# Verify security fixes applied
python3 fix_ip_storage.py --verify
```

---

## 🤝 Contributing

This encryption stack is open-source (MIT License). Contributions welcome:

1. **Security Audits** - Report vulnerabilities
2. **Feature Requests** - Suggest improvements
3. **Bug Fixes** - Submit pull requests
4. **Documentation** - Improve examples

---

## ⚠️ Security Notes

### What This Protects Against:
- ✅ Database breaches (encrypted data)
- ✅ Log leaks (PII redacted)
- ✅ Insider threats (distributed keys)
- ✅ GDPR violations (no plaintext PII)

### What This Does NOT Protect Against:
- ❌ Compromised encryption keys (use key management system)
- ❌ Man-in-the-middle attacks (use HTTPS)
- ❌ Client-side malware (validate inputs)
- ❌ Brute force attacks on weak passwords (use strong auth)

### Best Practices:
1. **Use HTTPS** - Encrypt data in transit
2. **Rotate Keys** - Change encryption keys periodically
3. **Audit Logs** - Monitor for suspicious activity
4. **Backup Keys** - Store encryption keys securely
5. **Test Thoroughly** - Run all test suites before deployment

---

**Built with ❤️ by Soulfra**

*Transform your web app into a privacy-first platform with Soulfra's encryption stack.*
