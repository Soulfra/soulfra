#!/usr/bin/env python3
"""
Show Admin Credentials - Quick Login Helper

Can't access /admin pages? This shows you the admin login credentials!

Usage:
    python3 show_admin_credentials.py

Then:
    1. Visit: http://localhost:5001/login
    2. Enter the username/password shown below
    3. Access admin pages!
"""

import sqlite3
from pathlib import Path


def show_admin_credentials():
    """Show admin user credentials"""
    print("=" * 60)
    print("🔑 ADMIN LOGIN CREDENTIALS")
    print("=" * 60)
    print()

    db_path = Path('soulfra.db')

    if not db_path.exists():
        print("❌ Database not found: soulfra.db")
        print("   Run: python3 database.py")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Get all admin users
        admins = conn.execute('''
            SELECT username, email, is_admin, created_at
            FROM users
            WHERE is_admin = 1
            ORDER BY created_at
        ''').fetchall()

        conn.close()

        if not admins:
            print("❌ No admin users found in database!")
            print()
            print("Create an admin user:")
            print("  1. Visit: http://localhost:5001/signup")
            print("  2. Create account")
            print("  3. Manually set is_admin=1 in database:")
            print()
            print("     sqlite3 soulfra.db")
            print("     UPDATE users SET is_admin = 1 WHERE username = 'your_username';")
            print()
            return

        print(f"Found {len(admins)} admin user(s):")
        print()

        for admin in admins:
            print(f"📧 Username: {admin['username']}")
            print(f"   Email: {admin['email']}")
            print(f"   Admin: {'✅ Yes' if admin['is_admin'] else '❌ No'}")
            print(f"   Created: {admin['created_at']}")
            print()

        print("-" * 60)
        print()
        print("⚠️  PASSWORD NOTE:")
        print("   Passwords are hashed - cannot be shown!")
        print()
        print("If you forgot your password:")
        print("  1. Create a new admin account at /signup")
        print("  2. Or reset password in database directly")
        print()
        print("-" * 60)
        print()
        print("🔐 TO LOGIN:")
        print(f"   1. Visit: http://localhost:5001/login")
        print(f"   2. Username: {admins[0]['username']}")
        print(f"   3. Password: (your password)")
        print()
        print("AFTER LOGIN, you can access:")
        print("   • http://localhost:5001/admin")
        print("   • http://localhost:5001/admin/automation")
        print("   • http://localhost:5001/admin/brand-status  ← YOUR GOAL!")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        print()


def create_test_admin():
    """Create a test admin user"""
    print("=" * 60)
    print("👤 CREATE TEST ADMIN USER")
    print("=" * 60)
    print()

    db_path = Path('soulfra.db')

    if not db_path.exists():
        print("❌ Database not found!")
        return

    print("Creating test admin user...")
    print()

    try:
        import hashlib

        # Test credentials
        username = "admin"
        email = "admin@soulfra.local"
        password = "admin123"  # CHANGE THIS IN PRODUCTION!

        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(db_path)

        # Check if admin user exists
        existing = conn.execute(
            'SELECT id FROM users WHERE username = ?',
            (username,)
        ).fetchone()

        if existing:
            print(f"⚠️  User '{username}' already exists!")
            print("   Updating to admin...")
            conn.execute(
                'UPDATE users SET is_admin = 1 WHERE username = ?',
                (username,)
            )
        else:
            print(f"Creating new user '{username}'...")
            conn.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (?, ?, ?, 1, datetime('now'))
            ''', (username, email, password_hash))

        conn.commit()
        conn.close()

        print()
        print("✅ TEST ADMIN CREATED!")
        print()
        print("LOGIN CREDENTIALS:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print()
        print("⚠️  IMPORTANT: Change this password in production!")
        print()
        print("Now visit: http://localhost:5001/login")
        print()

    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        print()


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'create':
        create_test_admin()
    else:
        show_admin_credentials()

        print()
        print("💡 TIP: If you need a test admin user, run:")
        print("   python3 show_admin_credentials.py create")
        print()


if __name__ == '__main__':
    main()
