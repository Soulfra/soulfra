#!/usr/bin/env python3
"""
Create SoulAssistant User Account

Creates the SoulAssistant AI persona user account in the database.
This account will be used by the floating widget to post comments.
"""

import sqlite3
import hashlib

def create_assistant_user():
    """Create the SoulAssistant user if it doesn't exist"""

    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Check if user already exists
    existing = cursor.execute(
        'SELECT id FROM users WHERE username = ?',
        ('soulassistant',)
    ).fetchone()

    if existing:
        print(f"✅ SoulAssistant user already exists (ID: {existing['id']})")
        db.close()
        return existing['id']

    # Create password hash (using simple hash for AI account)
    password = 'soul-assistant-ai-2025'
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Insert user
    cursor.execute('''
        INSERT INTO users (
            username,
            password_hash,
            email,
            display_name,
            bio,
            is_ai_persona
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'soulassistant',
        password_hash,
        'assistant@soulfra.com',
        'Soul Assistant',
        'Universal AI assistant that helps with QR codes, neural networks, research, and more. Powered by Ollama and the Soulfra stack.',
        1  # Mark as AI persona
    ))

    user_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Created SoulAssistant user (ID: {user_id})")
    print(f"   Username: soulassistant")
    print(f"   Display Name: Soul Assistant")
    print(f"   Password: {password}")
    print(f"   Is AI Persona: True")

    return user_id


if __name__ == '__main__':
    print("🤖 Creating SoulAssistant User Account")
    print("=" * 70)
    user_id = create_assistant_user()
    print()
    print(f"Account ready! User ID: {user_id}")
