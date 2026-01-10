#!/usr/bin/env python3
"""
CringeProof Encyclopedia Engine

Connects:
- Voice transcriptions → Wordmaps
- Domain intelligence → Cross-domain insights
- Time tracking → Year in Review
- Feature unlocking → Usage-based progression

Like Pantone's "Color of the Year" but for:
- Word of the Year
- Goal of the Year
- Cringe of the Year
- Reflection analytics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import Counter
import re

class EncyclopediaEngine:
    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path

    def get_db(self):
        return sqlite3.connect(self.db_path)

    def extract_words_from_transcript(self, transcript):
        """Extract significant words from transcription (filter stop words)"""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

        # Extract words (lowercase, alpha only)
        words = re.findall(r'\b[a-z]{3,}\b', transcript.lower())

        # Filter stop words
        significant_words = [w for w in words if w not in stop_words]

        return significant_words

    def update_wordmap_from_recording(self, recording_id, user_id=None):
        """
        Update user's personal wordmap from a voice recording
        Returns: dict of added words and frequencies
        """
        db = self.get_db()

        # Get transcription
        result = db.execute('''
            SELECT transcription, created_at FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not result or not result[0]:
            return None

        transcription, created_at = result

        # Extract words
        words = self.extract_words_from_transcript(transcription)
        word_freq = Counter(words)

        # Get or create user wordmap
        user_id = user_id or 1  # Default user
        existing = db.execute('''
            SELECT wordmap_json FROM user_wordmaps WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if existing and existing[0]:
            wordmap = json.loads(existing[0])
        else:
            wordmap = {}

        # Merge new words
        for word, count in word_freq.items():
            wordmap[word] = wordmap.get(word, 0) + count

        # Save updated wordmap (schema has: user_id, wordmap_json, last_updated)
        db.execute('''
            INSERT OR REPLACE INTO user_wordmaps (user_id, wordmap_json, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, json.dumps(wordmap)))

        db.commit()
        db.close()

        print(f"📚 Added {len(word_freq)} unique words to encyclopedia from recording #{recording_id}")
        return word_freq

    def get_word_of_period(self, period='year', user_id=None):
        """
        Get top word for a time period
        period: 'day', 'week', 'month', 'year', 'all'
        """
        db = self.get_db()

        # Calculate date range
        now = datetime.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = datetime(2000, 1, 1)  # All time

        # Get all transcriptions in period
        query = '''
            SELECT transcription FROM simple_voice_recordings
            WHERE created_at >= ? AND transcription IS NOT NULL
        '''
        params = [start_date.isoformat()]

        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)

        results = db.execute(query, params).fetchall()
        db.close()

        # Combine all words
        all_words = []
        for (transcript,) in results:
            all_words.extend(self.extract_words_from_transcript(transcript))

        if not all_words:
            return None

        # Get top word
        word_counts = Counter(all_words)
        top_word, count = word_counts.most_common(1)[0]

        return {
            'word': top_word,
            'count': count,
            'period': period,
            'total_recordings': len(results)
        }

    def generate_year_in_review(self, year=None, user_id=None):
        """
        Generate "Year in Review" report
        Returns: dict with top words, themes, trends, cringe predictions
        """
        year = year or datetime.now().year
        db = self.get_db()

        # Get all transcriptions for the year
        query = '''
            SELECT id, transcription, created_at FROM simple_voice_recordings
            WHERE created_at >= ? AND created_at < ?
            AND transcription IS NOT NULL
        '''
        params = [f'{year}-01-01', f'{year+1}-01-01']

        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)

        recordings = db.execute(query, params).fetchall()
        db.close()

        if not recordings:
            return None

        # Analyze all transcriptions
        all_words = []
        monthly_words = {month: [] for month in range(1, 13)}

        for rec_id, transcript, created_at in recordings:
            words = self.extract_words_from_transcript(transcript)
            all_words.extend(words)

            # Track by month
            month = datetime.fromisoformat(created_at).month
            monthly_words[month].extend(words)

        # Generate insights
        word_counts = Counter(all_words)
        top_10_words = word_counts.most_common(10)

        # Find trending words (higher usage in later months)
        trending = []
        for word in [w for w, c in word_counts.most_common(50)]:
            h1_count = sum(monthly_words[m].count(word) for m in range(1, 7))
            h2_count = sum(monthly_words[m].count(word) for m in range(7, 13))

            if h2_count > h1_count * 1.5:  # 50% increase
                trending.append((word, h2_count - h1_count))

        trending = sorted(trending, key=lambda x: x[1], reverse=True)[:5]

        return {
            'year': year,
            'total_recordings': len(recordings),
            'total_words': len(all_words),
            'unique_words': len(word_counts),
            'word_of_the_year': top_10_words[0][0] if top_10_words else None,
            'top_10_words': [{'word': w, 'count': c} for w, c in top_10_words],
            'trending_words': [{'word': w, 'growth': g} for w, g in trending],
            'monthly_summary': {
                str(month): len(words) for month, words in monthly_words.items()
            }
        }

    def check_feature_unlock(self, user_id):
        """
        Check which features user has unlocked based on usage
        Returns: dict of unlocked features
        """
        db = self.get_db()

        # Get user stats
        stats = db.execute('''
            SELECT
                (SELECT COUNT(*) FROM simple_voice_recordings WHERE user_id = ?) as recording_count,
                (SELECT wordmap_json FROM user_wordmaps WHERE user_id = ?) as wordmap,
                (SELECT credits FROM users WHERE id = ?) as credits
        ''', (user_id, user_id, user_id)).fetchone()

        db.close()

        if not stats:
            return {'level': 0, 'features': []}

        recording_count, wordmap_json, credits = stats
        unique_words = len(json.loads(wordmap_json)) if wordmap_json else 0

        # Feature unlock tiers
        unlocked = []
        level = 0

        if recording_count >= 5:
            level = 1
            unlocked.extend(['basic_transcription', 'personal_wordmap'])

        if recording_count >= 10:
            level = 2
            unlocked.extend(['rss_feed', 'word_of_month', 'cross_domain_search'])

        if recording_count >= 50:
            level = 3
            unlocked.extend(['word_of_year', 'reflection_analytics', 'export_encyclopedia'])

        if recording_count >= 100:
            level = 4
            unlocked.extend(['custom_domain_wordmap', 'api_access', 'contributor_dashboard'])

        return {
            'level': level,
            'features': unlocked,
            'stats': {
                'recordings': recording_count,
                'unique_words': unique_words,
                'credits': credits or 0
            },
            'next_unlock': {
                'level': level + 1,
                'recordings_needed': [5, 10, 50, 100][level] - recording_count if level < 4 else 0
            }
        }


if __name__ == '__main__':
    print("🎓 CringeProof Encyclopedia Engine - Test Run\n")

    engine = EncyclopediaEngine()

    # Test: Update wordmap from latest recording
    print("1️⃣ Testing wordmap update from recording #11...")
    words = engine.update_wordmap_from_recording(11)
    if words:
        print(f"   Added words: {dict(words.most_common(5))}")

    # Test: Word of the Year
    print("\n2️⃣ Getting Word of the Year...")
    woty = engine.get_word_of_period('year')
    if woty:
        print(f"   🏆 Word of the Year: '{woty['word']}' (used {woty['count']} times)")

    # Test: Year in Review
    print("\n3️⃣ Generating Year in Review for 2026...")
    review = engine.generate_year_in_review(2026)
    if review:
        print(f"   📊 Total recordings: {review['total_recordings']}")
        print(f"   📝 Total words: {review['total_words']}")
        print(f"   🎯 Word of the Year: {review['word_of_the_year']}")
        print(f"   📈 Top 5 words: {[w['word'] for w in review['top_10_words'][:5]]}")

    # Test: Feature unlocks
    print("\n4️⃣ Checking feature unlocks for user...")
    unlocks = engine.check_feature_unlock(1)
    print(f"   🎮 Level: {unlocks['level']}")
    print(f"   ✅ Unlocked: {unlocks['features']}")
    print(f"   📊 Stats: {unlocks['stats']}")

    print("\n✅ Encyclopedia engine test complete!")
