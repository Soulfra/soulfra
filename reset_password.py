#!/usr/bin/env python3
"""
Reset admin password - Simple and direct

Usage:
    python3 reset_password.py <username> <new_password>

Example:
    python3 reset_password.py admin mynewpass123
"""

import sqlite3
import hashlib
import sys

DB_PATH = 'soulfra.db'

def hash_password(password):
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def reset_password(username, new_password):
    """Reset user password"""
    db = sqlite3.connect(DB_PATH)

    # Check if user exists
    user = db.execute('SELECT id, username FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        print(f"❌ User '{username}' not found")
        db.close()
        return False

    # Update password
    password_hash = hash_password(new_password)
    db.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, username))
    db.commit()
    db.close()

    print(f"✅ Password reset for user: {username}")
    print(f"   New password: {new_password}")
    print(f"\n🔐 You can now login at:")
    print(f"   https://192.168.1.87:5002/login.html")
    print(f"   Username: {username}")
    print(f"   Password: {new_password}")

    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 reset_password.py <username> <new_password>")
        print("\nExample:")
        print("  python3 reset_password.py admin mynewpass123")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    reset_password(username, new_password)
