"""
Database migration: Add chat transcripts table
Stores Ollama chat conversations for persistence and review
"""

import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), 'soulfra.db')


def migrate():
    """Add chat transcripts table"""
    conn = sqlite3.connect(DB_PATH)

    # Create chat_transcripts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT,
            file_path TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT DEFAULT 'llama3.2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create chat_sessions table for grouping related messages
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            domain TEXT,
            file_path TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add session_id to chat_transcripts
    try:
        conn.execute('ALTER TABLE chat_transcripts ADD COLUMN session_id INTEGER REFERENCES chat_sessions(id)')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create index for faster lookups
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chat_user_domain ON chat_transcripts(user_id, domain)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_transcripts(session_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)')

    conn.commit()
    conn.close()

    print("✅ Chat transcripts tables created successfully")


if __name__ == '__main__':
    migrate()
