# Database Encryption Guide
**Soulfra Multi-Domain Network - Sensitive Data Protection**

This guide explains how to encrypt sensitive database fields using AES-256-GCM encryption.

---

## Overview

All sensitive data in the Soulfra database is encrypted at rest using **AES-256-GCM**:

- ✅ Email addresses (soulfra_master_users, professionals)
- ✅ Phone numbers (professionals)
- ✅ Message content (messages)
- ✅ Session tokens (sessions)
- ✅ Voice memos (already encrypted via voice_encryption.py)

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│  Application Layer                                 │
│  - Encrypts before INSERT/UPDATE                  │
│  - Decrypts on SELECT                              │
└────────────────────┬───────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────┐
│  database_encryption.py                            │
│  - encrypt_field() → AES-256-GCM                  │
│  - decrypt_field() → Plaintext                     │
│  - Uses voice_encryption.py for consistency        │
└────────────────────┬───────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────┐
│  Database (soulfra.db)                             │
│  ┌──────────────────────────────────────────────┐ │
│  │ soulfra_master_users                         │ │
│  │ - email (plaintext - deprecated)             │ │
│  │ - email_encrypted (AES-256-GCM)              │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │ professionals                                 │ │
│  │ - phone_encrypted (AES-256-GCM)              │ │
│  │ - email_encrypted (AES-256-GCM)              │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │ messages                                      │ │
│  │ - content_encrypted (AES-256-GCM)            │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Run database migration to add encrypted columns
sqlite3 soulfra.db < migrations/add_encryption_columns.sql

# 2. Generate encryption key
python3 database_encryption.py --key

# Output: DB_ENCRYPTION_KEY=a1b2c3d4e5f6...
# Save this to domain_config/secrets.env

# 3. Encrypt existing data
python3 database_encryption.py --encrypt

# 4. Verify encryption works
python3 database_encryption.py --test
```

---

## Step-by-Step Setup

### Step 1: Run Database Migration

Add encrypted columns to your database:

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

sqlite3 soulfra.db < migrations/add_encryption_columns.sql
```

**What this does:**
- Adds `email_encrypted`, `phone_encrypted`, `content_encrypted` columns
- Creates `encryption_metadata` table (tracks what's encrypted)
- Creates `encryption_audit_log` table (tracks access)
- Preserves existing plaintext columns (for rollback safety)

**Verify migration:**

```bash
sqlite3 soulfra.db "PRAGMA table_info(soulfra_master_users);"
```

You should see `email_encrypted` column.

### Step 2: Generate Encryption Key

```bash
python3 database_encryption.py --key
```

Output:
```
DB_ENCRYPTION_KEY=Zf3k9mP2nQ5rT8wY1xC4vB7nM0aS6dF9gH2jK5lN8pO3qR7tU1wV4yA6zC3eF==
```

**Save this key** to `domain_config/secrets.env`:

```bash
echo "DB_ENCRYPTION_KEY=Zf3k9mP2nQ5rT8wY1xC4vB7nM0aS6dF9gH2jK5lN8pO3qR7tU1wV4yA6zC3eF==" >> domain_config/secrets.env
```

**⚠️  CRITICAL: Keep this key safe!**
- Without this key, encrypted data CANNOT be decrypted
- Store it in a password manager
- Add it to GitHub Secrets (for production)
- NEVER commit it to git (already in .gitignore)

### Step 3: Encrypt Existing Data

Migrate plaintext data to encrypted columns:

```bash
python3 database_encryption.py --encrypt
```

Output:
```
🔐 Starting database encryption migration...

📧 Encrypting soulfra_master_users.email...
   ✅ Encrypted 42 emails

📞 Encrypting professionals.phone...
   ✅ Encrypted 15 phone numbers

📧 Encrypting professionals.email...
   ✅ Encrypted 15 professional emails

💬 Encrypting messages.content...
   ✅ Encrypted 127 messages

✅ Database encryption migration complete!
```

**What this does:**
- Reads plaintext values from original columns
- Encrypts each value with AES-256-GCM
- Stores encrypted value in `_encrypted` column
- Preserves original plaintext (for verification)

### Step 4: Verify Encryption

Test that encryption/decryption works:

```bash
python3 database_encryption.py --test
```

Output:
```
🔍 Verifying encryption...

Testing soulfra_master_users.email_encrypted...
   ✅ Email: user@example.com → [ENCRYPTED] → user@example.com

Testing professionals.phone_encrypted...
   ✅ Phone: (727) 555-1234 → [ENCRYPTED] → (727) 555-1234

Testing messages.content_encrypted...
   ✅ Message: Hi, I'm interested in your plumbing services... → [ENCRYPTED] → Hi, I'm interested in your plumbing services...

✅ Verification complete!
```

---

## Using Encryption in Application Code

### Encrypting Data on Write

```python
from database_encryption import DatabaseEncryption

db_enc = DatabaseEncryption()

# When creating a new professional
email = "joe@example.com"
phone = "(727) 555-1234"

encrypted_email = db_enc.encrypt_field(email)
encrypted_phone = db_enc.encrypt_field(phone)

db.execute('''
    INSERT INTO professionals (business_name, email_encrypted, phone_encrypted)
    VALUES (?, ?, ?)
''', ("Joe's Plumbing", encrypted_email, encrypted_phone))
```

### Decrypting Data on Read

```python
from database_encryption import DatabaseEncryption

db_enc = DatabaseEncryption()

# When displaying professional profile
row = db.execute('SELECT email_encrypted, phone_encrypted FROM professionals WHERE id = ?', (11,)).fetchone()

email = db_enc.decrypt_field(row['email_encrypted'])
phone = db_enc.decrypt_field(row['phone_encrypted'])

print(f"Email: {email}")
print(f"Phone: {phone}")
```

### Transparent Encryption Layer (Recommended)

Create a wrapper that automatically encrypts/decrypts:

```python
class EncryptedDatabase:
    def __init__(self):
        self.db_enc = DatabaseEncryption()

    def insert_professional(self, business_name, email, phone):
        encrypted_email = self.db_enc.encrypt_field(email)
        encrypted_phone = self.db_enc.encrypt_field(phone)

        db.execute('''
            INSERT INTO professionals (business_name, email_encrypted, phone_encrypted)
            VALUES (?, ?, ?)
        ''', (business_name, encrypted_email, encrypted_phone))

    def get_professional(self, professional_id):
        row = db.execute('''
            SELECT id, business_name, email_encrypted, phone_encrypted
            FROM professionals WHERE id = ?
        ''', (professional_id,)).fetchone()

        return {
            'id': row['id'],
            'business_name': row['business_name'],
            'email': self.db_enc.decrypt_field(row['email_encrypted']),
            'phone': self.db_enc.decrypt_field(row['phone_encrypted'])
        }
```

---

## Production Deployment

### Add Encryption Key to GitHub Secrets

1. Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/settings/secrets/actions`
2. Click **"New repository secret"**
3. Name: `DB_ENCRYPTION_KEY`
4. Value: `Zf3k9mP2nQ5rT8wY1xC4vB7nM0aS6dF9gH2jK5lN8pO3qR7tU1wV4yA6zC3eF==`
5. Click **"Add secret"**

### Update Production Server

```bash
# SSH into production server
ssh your-user@YOUR_SERVER_IP

cd /var/www/soulfra-simple

# Add encryption key to secrets.env
echo "DB_ENCRYPTION_KEY=YOUR_KEY_HERE" >> domain_config/secrets.env

# Run migration
sqlite3 soulfra.db < migrations/add_encryption_columns.sql

# Encrypt data
python3 database_encryption.py --encrypt

# Verify
python3 database_encryption.py --test

# Restart Flask
sudo systemctl restart soulfra
```

---

## Security Best Practices

### Key Management

1. **Generate unique key per environment:**
   - Development: One key
   - Staging: Different key
   - Production: Different key

2. **Rotate keys periodically:**
   - Generate new key
   - Re-encrypt all data with new key
   - Replace old key in secrets.env

3. **Key rotation script** (create `scripts/rotate_encryption_key.sh`):
   ```bash
   #!/bin/bash
   # Generate new key
   NEW_KEY=$(python3 -c "from database_encryption import DatabaseEncryption; import base64; db_enc = DatabaseEncryption(); print(base64.b64encode(db_enc.master_key).decode())")

   # Decrypt all data with old key
   python3 database_encryption.py --decrypt-all > /tmp/decrypted_data.json

   # Update key in secrets.env
   sed -i.bak "s/DB_ENCRYPTION_KEY=.*/DB_ENCRYPTION_KEY=$NEW_KEY/" domain_config/secrets.env

   # Re-encrypt all data with new key
   python3 database_encryption.py --re-encrypt < /tmp/decrypted_data.json

   # Verify
   python3 database_encryption.py --test

   # Clean up
   rm /tmp/decrypted_data.json
   ```

### Access Control

1. **Audit log** all decryption operations:
   ```python
   def decrypt_with_audit(encrypted_value, user_id, ip_address):
       decrypted = db_enc.decrypt_field(encrypted_value)

       # Log access
       db.execute('''
           INSERT INTO encryption_audit_log (table_name, column_name, action, user_id, ip_address)
           VALUES (?, ?, ?, ?, ?)
       ''', ('professionals', 'email', 'decrypt', user_id, ip_address))

       return decrypted
   ```

2. **Limit who can decrypt:**
   - Only authenticated users can decrypt their own data
   - Admins can decrypt all data (with audit log)
   - API endpoints require authentication

### Backup Encrypted Data

```bash
# Backup database (encrypted)
sqlite3 soulfra.db ".backup /var/backups/soulfra_encrypted_$(date +%Y%m%d).db"

# Backup encryption key separately (offline storage)
echo "DB_ENCRYPTION_KEY=$(grep DB_ENCRYPTION_KEY domain_config/secrets.env)" > /secure/offline/location/encryption_key_backup.txt
```

---

## Troubleshooting

### Issue: "Decryption error"

**Cause:** Wrong encryption key or corrupted data

**Solution:**
1. Verify key in `domain_config/secrets.env` matches the one used to encrypt
2. Check if data was encrypted with a different key
3. Restore from backup if data is corrupted

### Issue: "Column email_encrypted does not exist"

**Cause:** Migration not run

**Solution:**
```bash
sqlite3 soulfra.db < migrations/add_encryption_columns.sql
```

### Issue: "Some fields still plaintext"

**Cause:** Encryption migration not run, or new data inserted after migration

**Solution:**
```bash
python3 database_encryption.py --encrypt
```

---

## Performance Considerations

**Encryption overhead:**
- Encrypt: ~0.5ms per field
- Decrypt: ~0.5ms per field
- AES-256-GCM is hardware-accelerated on modern CPUs

**Optimization strategies:**
1. **Cache decrypted values** (in memory, per request)
2. **Batch operations** (encrypt multiple fields at once)
3. **Index encrypted columns** (already done in migration)

---

## Next Steps

After setting up encryption:

1. **Update application code** to use encrypted columns
2. **Test thoroughly** in development
3. **Deploy to production** with GitHub workflow
4. **Monitor audit logs** for suspicious access
5. **Set up key rotation** (quarterly recommended)

---

## Support

**Documentation:**
- Voice Encryption: `voice_encryption.py`
- Database Module: `database_encryption.py`
- Migration: `migrations/add_encryption_columns.sql`

**Testing:**
```bash
# Test encryption/decryption
python3 database_encryption.py

# Encrypt existing data
python3 database_encryption.py --encrypt

# Verify encryption
python3 database_encryption.py --test

# Show encryption key
python3 database_encryption.py --key
```

---

**Your sensitive data is now encrypted at rest!** 🔐
