#!/usr/bin/env python3
"""
Setup founder account for CringeProof

Creates the founder account with special privileges:
- is_founder = 1
- is_admin = 1
- Unlimited storage
- Reserved domain ownership (cringeproof, soulfra, calriven, deathtodata)
"""

import sqlite3
import hashlib
import sys

DB_PATH = 'soulfra.db'

def hash_password(password):
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_founder(username, password, email='founder@cringeproof.com'):
    """
    Create or upgrade founder account

    Args:
        username: Username for founder account
        password: Password for founder account
        email: Email (optional)
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Check if user exists
    existing = db.execute('SELECT id, username FROM users WHERE username = ?', (username,)).fetchone()

    if existing:
        print(f"✅ User '{username}' exists (ID: {existing['id']})")
        print(f"   Upgrading to founder status...")

        db.execute('''
            UPDATE users
            SET is_founder = 1,
                is_admin = 1,
                email = ?
            WHERE username = ?
        ''', (email, username))

        user_id = existing['id']
    else:
        print(f"🆕 Creating new founder account: {username}")

        password_hash = hash_password(password)

        cursor = db.execute('''
            INSERT INTO users (username, email, password_hash, display_name, is_admin, is_founder)
            VALUES (?, ?, ?, ?, 1, 1)
        ''', (username, email, password_hash, username.title()))

        user_id = cursor.lastrowid

    db.commit()

    # Verify founder status
    founder = db.execute('''
        SELECT id, username, email, is_admin, is_founder
        FROM users
        WHERE id = ?
    ''', (user_id,)).fetchone()

    print(f"\n🎉 Founder Account Ready!")
    print(f"=" * 50)
    print(f"  ID: {founder['id']}")
    print(f"  Username: {founder['username']}")
    print(f"  Email: {founder['email']}")
    print(f"  Is Admin: {bool(founder['is_admin'])}")
    print(f"  Is Founder: {bool(founder['is_founder'])}")
    print(f"=" * 50)

    # Reserve domains for founder
    print(f"\n🔒 Reserving domains for founder...")
    reserved_domains = ['cringeproof', 'soulfra', 'calriven', 'deathtodata']

    for domain_slug in reserved_domains:
        # Check if domain ownership table exists
        try:
            db.execute('''
                CREATE TABLE IF NOT EXISTS domain_ownership (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    domain_slug TEXT NOT NULL,
                    is_official INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(domain_slug),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            # Try to insert domain ownership
            try:
                db.execute('''
                    INSERT INTO domain_ownership (user_id, domain_slug, is_official)
                    VALUES (?, ?, 1)
                ''', (user_id, domain_slug))
                print(f"   ✅ Reserved: {domain_slug}")
            except sqlite3.IntegrityError:
                # Domain already reserved, update to founder
                db.execute('''
                    UPDATE domain_ownership
                    SET user_id = ?, is_official = 1
                    WHERE domain_slug = ?
                ''', (user_id, domain_slug))
                print(f"   ✅ Updated: {domain_slug}")

        except Exception as e:
            print(f"   ⚠️  Error reserving {domain_slug}: {e}")

    db.commit()
    db.close()

    print(f"\n✅ Founder setup complete!")
    print(f"\nNext steps:")
    print(f"  1. Login at /login.html with username: {username}")
    print(f"  2. Access god-mode at /god-mode.html")
    print(f"  3. Create official posts for reserved domains")
    print(f"  4. Setup leaderboards and analytics")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python setup_founder.py <username> <password> [email]")
        print("\nExample:")
        print("  python setup_founder.py matt mypassword123 matt@cringeproof.com")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) > 3 else 'founder@cringeproof.com'

    setup_founder(username, password, email)
