#!/usr/bin/env python3
"""
Voice Table Migration Script

Syncs recordings from simple_voice_recordings → voice_suggestions
So all your voice memos appear in /suggestion-box

Run: python3 migrate_voice_tables.py
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def calculate_sha256(audio_data):
    """Calculate SHA256 hash of audio data"""
    return hashlib.sha256(audio_data).hexdigest()

def migrate_voices():
    """Migrate recordings from simple_voice_recordings to voice_suggestions"""

    db_path = 'soulfra.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all simple voice recordings
    recordings = cursor.execute('''
        SELECT * FROM simple_voice_recordings
        ORDER BY created_at
    ''').fetchall()

    print(f"📊 Found {len(recordings)} recordings in simple_voice_recordings")

    migrated_count = 0
    skipped_count = 0

    for rec in recordings:
        # Calculate SHA256 hash
        sha256_hash = calculate_sha256(rec['audio_data'])

        # Check if already exists in voice_suggestions
        existing = cursor.execute('''
            SELECT id FROM voice_suggestions WHERE sha256_hash = ?
        ''', (sha256_hash,)).fetchone()

        if existing:
            print(f"⏭️  Skipping #{rec['id']} (already migrated)")
            skipped_count += 1
            continue

        # Determine brand based on transcription keywords
        brand_slug = None
        if rec['transcription']:
            text = rec['transcription'].lower()

            # CalRiven keywords
            calriven_keywords = ['data', 'analysis', 'metrics', 'proof', 'game', 'scraped',
                               'articles', 'news', 'feeds', 'input', 'system', 'logic', 'cringeproof']
            calriven_score = sum(1 for kw in calriven_keywords if kw in text)

            # DeathToData keywords
            deathtodata_keywords = ['hate', 'broken', 'fake', 'cringe', 'burn', 'garbage',
                                   'destroy', 'corrupt', 'bullshit', 'scam']
            deathtodata_score = sum(1 for kw in deathtodata_keywords if kw in text)

            # Soulfra keywords
            soulfra_keywords = ['authentic', 'trust', 'community', 'genuine', 'connection',
                              'vulnerable', 'honest', 'belonging', 'real', 'truth']
            soulfra_score = sum(1 for kw in soulfra_keywords if kw in text)

            # Assign brand based on highest score
            if deathtodata_score > calriven_score and deathtodata_score > soulfra_score:
                brand_slug = 'deathtodata'
            elif calriven_score > soulfra_score:
                brand_slug = 'calriven'
            elif soulfra_score > 0:
                brand_slug = 'soulfra'

        # Save to suggestion-box folder (if not already there)
        audio_path = f"suggestion-box/{sha256_hash[:8]}.webm"
        os.makedirs("suggestion-box", exist_ok=True)

        # Write audio file
        with open(audio_path, 'wb') as f:
            f.write(rec['audio_data'])

        # Insert into voice_suggestions
        cursor.execute('''
            INSERT INTO voice_suggestions (
                user_id,
                filename,
                audio_path,
                transcription,
                sha256_hash,
                brand_slug,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec['user_id'],
            rec['filename'],
            audio_path,
            rec['transcription'],
            sha256_hash,
            brand_slug,
            rec['created_at']
        ))

        migrated_count += 1
        print(f"✅ Migrated #{rec['id']}: {rec['filename']} → {brand_slug or 'no brand'}")

    conn.commit()
    conn.close()

    print("")
    print("="*60)
    print(f"✅ Migration complete!")
    print(f"   Migrated: {migrated_count}")
    print(f"   Skipped:  {skipped_count}")
    print(f"   Total:    {len(recordings)}")
    print("="*60)
    print("")
    print("📍 Check results:")
    print("   http://localhost:5001/suggestion-box")
    print("   http://localhost:5001/@calriven/suggestions")
    print("   http://localhost:5001/@deathtodata/suggestions")
    print("")

if __name__ == '__main__':
    migrate_voices()
