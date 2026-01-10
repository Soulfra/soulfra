#!/usr/bin/env python3
"""
Seed CringeProof Feed with Sample Data

Creates sample voice recordings + news articles + pairings
for testing the TikTok-style feed
"""

import sqlite3
from datetime import datetime, timedelta

def seed_feed():
    db = sqlite3.connect('soulfra.db')

    # Sample news articles
    articles = [
        {
            'title': 'OpenAI Announces GPT-5 Release Date',
            'url': 'https://techcrunch.com/2024/01/15/openai-gpt5',
            'source': 'TechCrunch',
            'summary': 'OpenAI CEO Sam Altman announces GPT-5 will launch in Q2 2024',
            'topics': 'ai'
        },
        {
            'title': 'Bitcoin Hits New All-Time High',
            'url': 'https://coindesk.com/bitcoin-ath',
            'source': 'CoinDesk',
            'summary': 'Bitcoin surpasses previous record, reaching $75,000',
            'topics': 'crypto'
        },
        {
            'title': 'Apple Vision Pro Launches Next Month',
            'url': 'https://9to5mac.com/vision-pro-launch',
            'source': '9to5Mac',
            'summary': 'Apple sets February 2 as launch date for Vision Pro headset',
            'topics': 'tech'
        }
    ]

    # Insert articles
    for article in articles:
        db.execute("""
            INSERT OR IGNORE INTO news_articles (title, url, source, summary, topics, article_hash, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            article['title'],
            article['url'],
            article['source'],
            article['summary'],
            article['topics'],
            hash(article['url'])
        ))

    db.commit()

    # Get article IDs
    article_ids = [row[0] for row in db.execute("SELECT id FROM news_articles ORDER BY scraped_at DESC LIMIT 3").fetchall()]

    # Sample voice predictions
    predictions = [
        ("GPT-5 is complete vaporware. No way it ships in Q2. Probably delayed until 2025.", article_ids[0] if len(article_ids) > 0 else None),
        ("Bitcoin will crash back to $40K within 30 days. This is the top.", article_ids[1] if len(article_ids) > 1 else None),
        ("Vision Pro will be Apple's biggest flop since the Newton. Mark my words.", article_ids[2] if len(article_ids) > 2 else None)
    ]

    # Create sample voice recordings
    for i, (prediction, article_id) in enumerate(predictions):
        # Insert voice recording
        cursor = db.execute("""
            INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, created_at)
            VALUES (?, ?, ?, ?, datetime('now', ?))
        """, (
            f'sample_prediction_{i+1}.webm',
            b'',  # Empty audio data for demo
            0,
            prediction,
            f'-{i} hours'  # Stagger timestamps
        ))

        recording_id = cursor.lastrowid

        # Create voice-article pairing
        if article_id:
            # Some unlocked, some time-locked
            time_locked_until = None if i % 2 == 0 else (datetime.now() + timedelta(days=30)).isoformat()
            unlocked_at = datetime.now().isoformat() if i % 2 == 0 else None

            cursor = db.execute("""
                INSERT INTO voice_article_pairings (recording_id, article_id, prediction_text, time_locked_until, unlocked_at, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', ?))
            """, (
                recording_id,
                article_id,
                prediction,
                time_locked_until,
                unlocked_at,
                f'-{i} hours'
            ))

            pairing_id = cursor.lastrowid

            # Add sample votes for unlocked items
            if unlocked_at:
                # Add some cringe votes
                for j in range(3):
                    db.execute("""
                        INSERT OR IGNORE INTO cringe_votes (pairing_id, user_id, vote_type)
                        VALUES (?, ?, 'cringe')
                    """, (pairing_id, f'user_{j}'))

                # Add some based votes
                for j in range(7):
                    db.execute("""
                        INSERT OR IGNORE INTO cringe_votes (pairing_id, user_id, vote_type)
                        VALUES (?, ?, 'based')
                    """, (pairing_id, f'user_{j+10}'))

                # Update score (3 cringe / 10 total = 0.3)
                db.execute("""
                    UPDATE voice_article_pairings
                    SET cringeproof_score = 0.3
                    WHERE id = ?
                """, (pairing_id,))

    db.commit()
    db.close()

    print('✅ Sample data created!')
    print('   - 3 news articles')
    print('   - 3 voice recordings')
    print('   - 3 voice-article pairings')
    print('   - Sample votes on unlocked items')
    print('')
    print('Test the feed at: http://192.168.1.87:5001/feed')

if __name__ == '__main__':
    seed_feed()
