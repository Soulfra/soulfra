#!/usr/bin/env python3
"""
Database Encryption Module
Encrypts sensitive columns in SQLite database using AES-256-GCM

Uses the existing voice_encryption.py module for consistent encryption across all Soulfra data.

Encrypted Fields:
- emails (soulfra_master_users, professionals, users)
- phone numbers (professionals)
- message content (messages table)
- session tokens (sessions table)

Usage:
    from database_encryption import DatabaseEncryption

    db_enc = DatabaseEncryption()

    # Encrypt a value
    encrypted = db_enc.encrypt_field("secret@example.com")

    # Decrypt a value
    decrypted = db_enc.decrypt_field(encrypted)

    # Batch encrypt existing data
    db_enc.encrypt_existing_data()
"""

import os
import base64
from typing import Optional, Tuple
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import voice_encryption
from database import get_db

class DatabaseEncryption:
    """
    Database encryption handler using AES-256-GCM

    Leverages voice_encryption.py for consistent encryption across:
    - Voice memos
    - Database fields
    - QR codes
    - Session tokens
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize database encryption

        Args:
            master_key: Optional master encryption key. If not provided,
                       loads from environment variable DB_ENCRYPTION_KEY
        """
        # Get or generate master key
        if master_key:
            self.master_key = master_key
        else:
            # Try to load from environment
            key_b64 = os.environ.get('DB_ENCRYPTION_KEY')
            if key_b64:
                self.master_key = base64.b64decode(key_b64)
            else:
                # Generate new key (should be saved to env)
                self.master_key = voice_encryption.generate_encryption_key()
                print(f"⚠️  Generated new DB encryption key: {base64.b64encode(self.master_key).decode()}")
                print("   Save this to environment variable DB_ENCRYPTION_KEY")

    def encrypt_field(self, plaintext: str) -> str:
        """
        Encrypt a database field

        Args:
            plaintext: Plain text to encrypt

        Returns:
            Base64-encoded encrypted value in format: iv:ciphertext
        """
        if not plaintext or plaintext == "":
            return ""

        # Generate IV
        iv = voice_encryption.generate_iv()

        # Encrypt using AES-256-GCM
        cipher = AES.new(self.master_key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))

        # Combine ciphertext and tag
        encrypted_data = ciphertext + tag

        # Format: base64(iv):base64(ciphertext+tag)
        iv_b64 = base64.b64encode(iv).decode('utf-8')
        cipher_b64 = base64.b64encode(encrypted_data).decode('utf-8')

        return f"{iv_b64}:{cipher_b64}"

    def decrypt_field(self, encrypted: str) -> str:
        """
        Decrypt a database field

        Args:
            encrypted: Encrypted value in format: iv:ciphertext

        Returns:
            Decrypted plaintext
        """
        if not encrypted or encrypted == "":
            return ""

        try:
            # Parse format: base64(iv):base64(ciphertext+tag)
            iv_b64, cipher_b64 = encrypted.split(':', 1)
            iv = base64.b64decode(iv_b64)
            encrypted_data = base64.b64decode(cipher_b64)

            # Split ciphertext and tag (tag is last 16 bytes)
            ciphertext = encrypted_data[:-16]
            tag = encrypted_data[-16:]

            # Decrypt using AES-256-GCM
            cipher = AES.new(self.master_key, AES.MODE_GCM, nonce=iv)
            plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)

            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            print(f"⚠️  Decryption error: {e}")
            return "[ENCRYPTED]"

    def encrypt_existing_data(self):
        """
        Migrate existing plaintext data to encrypted format

        This is a ONE-TIME operation to encrypt existing data.
        Should be run after adding encryption columns to database.

        Steps:
        1. Check if encrypted columns exist
        2. For each sensitive field, if encrypted version is NULL:
           - Encrypt plaintext value
           - Save to encrypted column
           - Optionally clear plaintext column
        """
        db = get_db()

        print("🔐 Starting database encryption migration...")
        print()

        # 1. Encrypt emails in soulfra_master_users
        print("📧 Encrypting soulfra_master_users.email...")
        rows = db.execute('''
            SELECT master_user_id, email
            FROM soulfra_master_users
            WHERE email IS NOT NULL AND email != ''
              AND (email_encrypted IS NULL OR email_encrypted = '')
        ''').fetchall()

        encrypted_count = 0
        for row in rows:
            encrypted_email = self.encrypt_field(row['email'])
            db.execute('''
                UPDATE soulfra_master_users
                SET email_encrypted = ?
                WHERE master_user_id = ?
            ''', (encrypted_email, row['master_user_id']))
            encrypted_count += 1

        db.commit()
        print(f"   ✅ Encrypted {encrypted_count} emails")

        # 2. Encrypt phone numbers in professionals table
        print("📞 Encrypting professionals.phone...")
        rows = db.execute('''
            SELECT id, phone
            FROM professionals
            WHERE phone IS NOT NULL AND phone != ''
              AND (phone_encrypted IS NULL OR phone_encrypted = '')
        ''').fetchall()

        encrypted_count = 0
        for row in rows:
            encrypted_phone = self.encrypt_field(row['phone'])
            db.execute('''
                UPDATE professionals
                SET phone_encrypted = ?
                WHERE id = ?
            ''', (encrypted_phone, row['id']))
            encrypted_count += 1

        db.commit()
        print(f"   ✅ Encrypted {encrypted_count} phone numbers")

        # 3. Encrypt email in professionals table
        print("📧 Encrypting professionals.email...")
        rows = db.execute('''
            SELECT id, email
            FROM professionals
            WHERE email IS NOT NULL AND email != ''
              AND (email_encrypted IS NULL OR email_encrypted = '')
        ''').fetchall()

        encrypted_count = 0
        for row in rows:
            encrypted_email = self.encrypt_field(row['email'])
            db.execute('''
                UPDATE professionals
                SET email_encrypted = ?
                WHERE id = ?
            ''', (encrypted_email, row['id']))
            encrypted_count += 1

        db.commit()
        print(f"   ✅ Encrypted {encrypted_count} professional emails")

        # 4. Encrypt message content
        print("💬 Encrypting messages.content...")
        rows = db.execute('''
            SELECT id, content
            FROM messages
            WHERE content IS NOT NULL AND content != ''
              AND (content_encrypted IS NULL OR content_encrypted = '')
        ''').fetchall()

        encrypted_count = 0
        for row in rows:
            encrypted_content = self.encrypt_field(row['content'])
            db.execute('''
                UPDATE messages
                SET content_encrypted = ?
                WHERE id = ?
            ''', (encrypted_content, row['id']))
            encrypted_count += 1

        db.commit()
        print(f"   ✅ Encrypted {encrypted_count} messages")

        print()
        print("✅ Database encryption migration complete!")
        print()
        print("Next steps:")
        print("  1. Update application code to use encrypted columns")
        print("  2. Test decryption with: python3 database_encryption.py --test")
        print("  3. Optionally clear plaintext columns (BACKUP FIRST!)")

    def verify_encryption(self):
        """
        Verify that encryption/decryption works correctly
        """
        db = get_db()

        print("🔍 Verifying encryption...")
        print()

        # Test soulfra_master_users emails
        print("Testing soulfra_master_users.email_encrypted...")
        row = db.execute('''
            SELECT email, email_encrypted
            FROM soulfra_master_users
            WHERE email_encrypted IS NOT NULL AND email_encrypted != ''
            LIMIT 1
        ''').fetchone()

        if row:
            decrypted = self.decrypt_field(row['email_encrypted'])
            if decrypted == row['email']:
                print(f"   ✅ Email: {row['email']} → [ENCRYPTED] → {decrypted}")
            else:
                print(f"   ❌ Mismatch! Original: {row['email']}, Decrypted: {decrypted}")
        else:
            print("   ⚠️  No encrypted emails found")

        # Test professionals phone
        print("Testing professionals.phone_encrypted...")
        row = db.execute('''
            SELECT phone, phone_encrypted
            FROM professionals
            WHERE phone_encrypted IS NOT NULL AND phone_encrypted != ''
            LIMIT 1
        ''').fetchone()

        if row:
            decrypted = self.decrypt_field(row['phone_encrypted'])
            if decrypted == row['phone']:
                print(f"   ✅ Phone: {row['phone']} → [ENCRYPTED] → {decrypted}")
            else:
                print(f"   ❌ Mismatch! Original: {row['phone']}, Decrypted: {decrypted}")
        else:
            print("   ⚠️  No encrypted phone numbers found")

        # Test messages
        print("Testing messages.content_encrypted...")
        row = db.execute('''
            SELECT content, content_encrypted
            FROM messages
            WHERE content_encrypted IS NOT NULL AND content_encrypted != ''
            LIMIT 1
        ''').fetchone()

        if row:
            decrypted = self.decrypt_field(row['content_encrypted'])
            if decrypted == row['content']:
                print(f"   ✅ Message: {row['content'][:50]}... → [ENCRYPTED] → {decrypted[:50]}...")
            else:
                print(f"   ❌ Mismatch! Original: {row['content']}, Decrypted: {decrypted}")
        else:
            print("   ⚠️  No encrypted messages found")

        print()
        print("✅ Verification complete!")


if __name__ == "__main__":
    import sys

    db_enc = DatabaseEncryption()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--encrypt":
            db_enc.encrypt_existing_data()
        elif command == "--test":
            db_enc.verify_encryption()
        elif command == "--key":
            print(f"DB_ENCRYPTION_KEY={base64.b64encode(db_enc.master_key).decode()}")
        else:
            print("Unknown command")
            print("Usage:")
            print("  python3 database_encryption.py --encrypt   # Encrypt existing data")
            print("  python3 database_encryption.py --test      # Verify encryption")
            print("  python3 database_encryption.py --key       # Show encryption key")
    else:
        # Interactive demo
        print("🔐 Database Encryption Demo")
        print()

        # Test encryption/decryption
        plaintext = "test@example.com"
        encrypted = db_enc.encrypt_field(plaintext)
        decrypted = db_enc.decrypt_field(encrypted)

        print(f"Plaintext:  {plaintext}")
        print(f"Encrypted:  {encrypted}")
        print(f"Decrypted:  {decrypted}")
        print()

        if plaintext == decrypted:
            print("✅ Encryption working correctly!")
        else:
            print("❌ Encryption mismatch!")

        print()
        print("Run with:")
        print("  --encrypt  # Migrate existing data to encrypted columns")
        print("  --test     # Verify encryption on real data")
        print("  --key      # Show encryption key (save to .env)")
