#!/usr/bin/env python3
"""
Initialize User Roles/Tiers System

Adds role column to users table for permission tiers:
- sysadmin: Full access to automation, system settings
- admin: Can create posts, manage subscribers
- user: Regular user (posts, comments)
"""

from database import get_db


def init_user_roles():
    """Add role column to users table"""
    db = get_db()

    # Check if role column exists
    cursor = db.execute("PRAGMA table_info(users)")
    columns = [row['name'] for row in cursor.fetchall()]

    if 'role' not in columns:
        print("Adding 'role' column to users table...")

        # Add role column (default to 'user')
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

        # Set existing admins to 'admin' role
        db.execute('''
            UPDATE users
            SET role = 'admin'
            WHERE is_admin = 1
        ''')

        # You can manually set a sysadmin:
        # db.execute("UPDATE users SET role = 'sysadmin' WHERE username = 'calriven'")

        db.commit()
        print("✅ Role column added successfully")

        # Show current roles
        users = db.execute('SELECT username, role, is_admin FROM users').fetchall()
        print("\n📊 Current user roles:")
        for user in users:
            print(f"   • {user['username']}: {user['role']} (is_admin: {user['is_admin']})")
    else:
        print("✅ Role column already exists")

        # Show current roles
        users = db.execute('SELECT username, role FROM users').fetchall()
        print("\n📊 Current user roles:")
        for user in users:
            print(f"   • {user['username']}: {user['role']}")

    db.close()

    print("\n💡 To set a user as sysadmin:")
    print("   UPDATE users SET role = 'sysadmin' WHERE username = 'your_username';")


if __name__ == '__main__':
    init_user_roles()
