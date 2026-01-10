#!/usr/bin/env python3
"""
Add Ollama processing fields to domain_messages table
"""

from database import get_db

def add_ollama_fields():
    """Add Ollama-related columns to domain_messages table"""
    db = get_db()

    # Add columns (SQLite uses ALTER TABLE ADD COLUMN)
    try:
        db.execute('''
            ALTER TABLE domain_messages
            ADD COLUMN ollama_processed INTEGER DEFAULT 0
        ''')
        print("✅ Added ollama_processed column")
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print("ℹ️  ollama_processed column already exists")
        else:
            print(f"❌ Error adding ollama_processed: {e}")

    try:
        db.execute('''
            ALTER TABLE domain_messages
            ADD COLUMN ollama_generated_content TEXT
        ''')
        print("✅ Added ollama_generated_content column")
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print("ℹ️  ollama_generated_content column already exists")
        else:
            print(f"❌ Error adding ollama_generated_content: {e}")

    try:
        db.execute('''
            ALTER TABLE domain_messages
            ADD COLUMN ollama_persona TEXT
        ''')
        print("✅ Added ollama_persona column")
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print("ℹ️  ollama_persona column already exists")
        else:
            print(f"❌ Error adding ollama_persona: {e}")

    try:
        db.execute('''
            ALTER TABLE domain_messages
            ADD COLUMN ollama_processed_at TEXT
        ''')
        print("✅ Added ollama_processed_at column")
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print("ℹ️  ollama_processed_at column already exists")
        else:
            print(f"❌ Error adding ollama_processed_at: {e}")

    db.commit()
    print("\n✅ Database schema updated for Ollama integration")


if __name__ == '__main__':
    add_ollama_fields()
