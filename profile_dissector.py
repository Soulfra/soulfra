#!/usr/bin/env python3
"""
Profile Dissector - Extracts personality/insights from voice recordings

Takes transcriptions from voice memos and generates:
- Top keywords (from wordmap)
- Personality traits (from language patterns)
- Topics of interest
- Communication style
- Profile bio (auto-generated)

This connects voice recordings → user_profiles table
"""

from database import get_db
import json
import re
from collections import Counter
from datetime import datetime

class ProfileDissector:
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = get_db()

    def get_all_transcriptions(self):
        """Get all transcriptions for this user"""
        rows = self.db.execute('''
            SELECT transcription, created_at
            FROM simple_voice_recordings
            WHERE user_id = ? AND transcription IS NOT NULL
            ORDER BY created_at DESC
        ''', (self.user_id,)).fetchall()

        return [(row['transcription'], row['created_at']) for row in rows]

    def extract_keywords(self, text_list):
        """Extract top keywords from all transcriptions"""
        # Combine all text
        combined = ' '.join(text_list)

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', combined.lower())

        # Filter stop words
        filtered = [w for w in words if w not in stop_words]

        # Count occurrences
        counter = Counter(filtered)

        return counter.most_common(20)

    def detect_personality_traits(self, text_list):
        """Detect personality traits from language patterns"""
        combined = ' '.join(text_list).lower()

        traits = []

        # Analytical thinker
        if any(word in combined for word in ['because', 'therefore', 'analyze', 'data', 'logic', 'reason']):
            traits.append('analytical')

        # Creative
        if any(word in combined for word in ['imagine', 'create', 'design', 'art', 'idea', 'innovation']):
            traits.append('creative')

        # Technical
        if any(word in combined for word in ['code', 'python', 'api', 'database', 'system', 'algorithm', 'function']):
            traits.append('technical')

        # Communicative
        if len(text_list) >= 5 and sum(len(t.split()) for t in text_list) / len(text_list) > 50:
            traits.append('communicative')

        # Privacy-focused
        if any(word in combined for word in ['privacy', 'security', 'anonymous', 'data', 'tracking', 'surveillance']):
            traits.append('privacy-conscious')

        # Entrepreneurial
        if any(word in combined for word in ['startup', 'business', 'launch', 'product', 'market', 'revenue']):
            traits.append('entrepreneurial')

        return traits

    def detect_topics(self, keywords):
        """Detect topics of interest from keywords"""
        topics = []

        keyword_dict = dict(keywords)

        # Tech topics
        tech_words = ['code', 'python', 'javascript', 'api', 'database', 'web', 'app', 'software']
        if any(w in keyword_dict for w in tech_words):
            topics.append('Technology')

        # AI/ML topics
        ai_words = ['ai', 'machine', 'learning', 'model', 'neural', 'network', 'llm', 'gpt']
        if any(w in keyword_dict for w in ai_words):
            topics.append('Artificial Intelligence')

        # Business topics
        biz_words = ['business', 'startup', 'revenue', 'market', 'product', 'customer']
        if any(w in keyword_dict for w in biz_words):
            topics.append('Business')

        # Privacy/Security
        privacy_words = ['privacy', 'security', 'encryption', 'anonymous', 'data']
        if any(w in keyword_dict for w in privacy_words):
            topics.append('Privacy & Security')

        # Blockchain/Crypto
        crypto_words = ['blockchain', 'crypto', 'bitcoin', 'ethereum', 'web3', 'decentralized']
        if any(w in keyword_dict for w in crypto_words):
            topics.append('Blockchain')

        return topics

    def generate_bio(self, keywords, traits, topics):
        """Generate auto-bio from profile data"""
        bio_parts = []

        if traits:
            bio_parts.append(f"A {', '.join(traits[:3])} individual")

        if topics:
            bio_parts.append(f"interested in {', '.join(topics[:3])}")

        if keywords:
            top_word = keywords[0][0]
            bio_parts.append(f"who talks about {top_word}")

        return '. '.join(bio_parts) + '.'

    def dissect_profile(self):
        """Full profile dissection - extract everything"""
        # Get all transcriptions
        transcriptions = self.get_all_transcriptions()

        if not transcriptions:
            return {
                'has_data': False,
                'message': 'No voice recordings yet'
            }

        text_list = [t[0] for t in transcriptions]

        # Extract insights
        keywords = self.extract_keywords(text_list)
        traits = self.detect_personality_traits(text_list)
        topics = self.detect_topics(keywords)
        bio = self.generate_bio(keywords, traits, topics)

        # Recording stats
        total_recordings = len(transcriptions)
        total_words = sum(len(t.split()) for t in text_list)
        avg_words = total_words // total_recordings if total_recordings else 0

        return {
            'has_data': True,
            'keywords': keywords[:10],  # Top 10
            'traits': traits,
            'topics': topics,
            'bio': bio,
            'stats': {
                'total_recordings': total_recordings,
                'total_words': total_words,
                'avg_words_per_recording': avg_words,
                'first_recording': transcriptions[-1][1],
                'last_recording': transcriptions[0][1]
            }
        }

    def update_user_profile(self):
        """Update user_profiles table with dissected insights"""
        insights = self.dissect_profile()

        if not insights['has_data']:
            return insights

        # Convert insights to JSON for storage
        profile_data = {
            'bio': insights['bio'],
            'keywords': insights['keywords'],
            'traits': insights['traits'],
            'topics': insights['topics'],
            'stats': insights['stats']
        }

        # Check if profile exists
        existing = self.db.execute('''
            SELECT id FROM user_profiles WHERE user_id = ?
        ''', (self.user_id,)).fetchone()

        if existing:
            # Update existing profile
            self.db.execute('''
                UPDATE user_profiles
                SET bio = ?, keywords = ?, traits = ?, topics = ?, updated_at = ?
                WHERE user_id = ?
            ''', (
                insights['bio'],
                json.dumps(insights['keywords']),
                json.dumps(insights['traits']),
                json.dumps(insights['topics']),
                datetime.now().isoformat(),
                self.user_id
            ))
        else:
            # Create new profile
            self.db.execute('''
                INSERT INTO user_profiles (user_id, bio, keywords, traits, topics, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.user_id,
                insights['bio'],
                json.dumps(insights['keywords']),
                json.dumps(insights['traits']),
                json.dumps(insights['topics']),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        self.db.commit()

        return {
            **insights,
            'profile_updated': True
        }

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def dissect_and_update_profile(user_id):
    """Helper function - dissect profile and update database"""
    dissector = ProfileDissector(user_id)
    try:
        result = dissector.update_user_profile()
        return result
    finally:
        dissector.close()


if __name__ == '__main__':
    # Test with user ID 1
    import sys

    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = 1

    print(f"Dissecting profile for user {user_id}...")

    result = dissect_and_update_profile(user_id)

    if result['has_data']:
        print(f"\n✅ Profile Updated")
        print(f"\nBio: {result['bio']}")
        print(f"\nTop Keywords:")
        for word, count in result['keywords'][:5]:
            print(f"  - {word}: {count}")
        print(f"\nTraits: {', '.join(result['traits'])}")
        print(f"\nTopics: {', '.join(result['topics'])}")
        print(f"\nStats: {result['stats']['total_recordings']} recordings, {result['stats']['total_words']} words")
    else:
        print(f"\n⚠️  {result['message']}")
