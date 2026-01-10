#!/usr/bin/env python3
"""
Simple Voice - Just a table to store recordings

No encryption, no keys, no complexity.
"""

import sqlite3


def init_simple_voice_table():
    """Create simple voice recordings table"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS simple_voice_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            audio_data BLOB NOT NULL,
            file_size INTEGER NOT NULL,
            transcription TEXT,
            transcription_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add transcription columns if table already exists
    try:
        cursor.execute('ALTER TABLE simple_voice_recordings ADD COLUMN transcription TEXT')
        print("✅ Added transcription column")
    except:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE simple_voice_recordings ADD COLUMN transcription_method TEXT')
        print("✅ Added transcription_method column")
    except:
        pass  # Column already exists

    # Add user_id column for QR auth integration
    try:
        cursor.execute('ALTER TABLE simple_voice_recordings ADD COLUMN user_id INTEGER REFERENCES users(id)')
        print("✅ Added user_id column for QR auth integration")
    except:
        pass  # Column already exists

    conn.commit()
    conn.close()

    print("✅ Simple voice recordings table created")


if __name__ == '__main__':
    init_simple_voice_table()
    print("")
    print("Ready to record!")
    print("Go to: /voice")
