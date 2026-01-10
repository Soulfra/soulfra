#!/usr/bin/env python3
"""
Test Mesh Network Flow - Live Demo

Creates test user and voice recording, then triggers the full cascade:
Voice → Wordmap → Domain Matching → Content Generation → Ownership

Watch the magic happen!
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict

# Import the mesh network cascade engine
from economy_mesh_network import on_voice_transcribed
from domain_wordmap_aggregator import get_domain_wordmap
from text_encoder import add_tier_emoji


def create_test_user() -> int:
    """Create test user 'matt' if doesn't exist"""

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if user exists
    existing = cursor.execute('SELECT id FROM users WHERE username = ?', ('matt',)).fetchone()
    if existing:
        user_id = existing[0]
        print(f"✅ User 'matt' already exists (ID: {user_id})")
    else:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', ('matt', 'matt@soulfra.com', 'test_hash', datetime.now().isoformat()))
        user_id = cursor.lastrowid
        print(f"✅ Created test user 'matt' (ID: {user_id})")

    conn.commit()
    conn.close()

    return user_id


def insert_test_voice_recording(user_id: int) -> int:
    """Insert a test voice recording with transcription"""

    # Test transcription about cringeproof topics
    test_transcription = """
    You know what I really hate? The cringe on social media. Everyone's trying so hard to be
    authentic but it all feels so fake. I want genuine connection, real community, people being
    vulnerable and honest. That's the only way to build trust and belonging. The whole validation
    game is broken. We need spaces where people can express their true identity without fear.
    Social acceptance shouldn't be based on performance. It's about being real, being yourself,
    finding your truth. That's what authentic social interaction looks like.
    """

    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO simple_voice_recordings
        (user_id, filename, audio_data, file_size, transcription, transcription_method, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        'test_cringeproof_voice.wav',
        b'test_audio_data',  # Dummy audio data
        len(test_transcription),  # Use transcription length as file size
        test_transcription,
        'test_demo',
        datetime.now().isoformat()
    ))

    recording_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"\n✅ Created test voice recording (ID: {recording_id})")
    print(f"📝 Transcription: {test_transcription[:100]}...")

    return recording_id


def trigger_cascade(recording_id: int):
    """Trigger the full mesh network cascade"""

    print(f"\n{'='*70}")
    print("🚀 TRIGGERING MESH NETWORK CASCADE")
    print(f"{'='*70}\n")

    # This is the main entry point that triggers everything
    result = on_voice_transcribed(recording_id)

    print("\n📊 CASCADE RESULTS:")
    print(f"{'='*70}")

    # Show wordmap extraction
    if 'user_wordmap' in result:
        wordmap = result['user_wordmap']['wordmap']
        vocab_size = len(wordmap)
        print(f"\n🗺️  USER WORDMAP CREATED:")
        print(f"   Vocabulary size: {vocab_size} unique words")
        print(f"   Top 10 words:")
        top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:10]
        for word, count in top_words:
            print(f"      • {word}: {count}")

    # Show domain matches
    if 'matched_domains' in result:
        matches = result['matched_domains']
        print(f"\n🎯 DOMAIN MATCHES FOUND: {len(matches)}")
        for match in matches:
            domain = match['domain']
            tier = match.get('tier', 'unknown')
            alignment = match['alignment_score']
            domain_with_emoji = add_tier_emoji(domain, tier)

            print(f"\n   {domain_with_emoji}")
            print(f"      Alignment: {alignment*100:.1f}%")
            print(f"      Tier: {tier.upper()}")

            # Show matched keywords
            if 'matched_keywords' in match:
                print(f"      Matched words: {', '.join(match['matched_keywords'][:5])}")

    # Show content generated
    if 'generated_content' in result:
        content_items = result['generated_content']
        print(f"\n📄 CONTENT GENERATED: {len(content_items)} items")
        for item in content_items:
            print(f"\n   Type: {item['content_type']}")
            print(f"   Domain: {item['domain']}")
            print(f"   Alignment: {item.get('alignment_score', 0)*100:.1f}%")

    # Show ownership earned
    if 'ownership_rewards' in result:
        rewards = result['ownership_rewards']
        print(f"\n💎 OWNERSHIP EARNED: {len(rewards)} domains")
        for reward in rewards:
            print(f"\n   {reward['domain']}: +{reward['reward_pct']:.2f}%")

    print(f"\n{'='*70}")
    print("✅ CASCADE COMPLETE!")
    print(f"{'='*70}\n")


def show_final_state():
    """Show final state of domains and ownership"""

    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n🌐 FINAL DOMAIN STATE:")
    print(f"{'='*70}")

    # Get all domains
    domains = cursor.execute('''
        SELECT domain, tier, description
        FROM domain_contexts
        ORDER BY tier DESC, domain
    ''').fetchall()

    for domain_row in domains:
        domain = domain_row['domain']
        tier = domain_row['tier']
        domain_with_emoji = add_tier_emoji(domain, tier)

        # Get wordmap
        wordmap_data = get_domain_wordmap(domain)
        wordmap = wordmap_data.get('wordmap', {}) if wordmap_data else {}

        # Get contributors
        contributors = cursor.execute('''
            SELECT COUNT(*) as count
            FROM domain_ownership
            WHERE domain_id = (SELECT id FROM domain_contexts WHERE domain = ?)
            AND ownership_percentage > 0
        ''', (domain,)).fetchone()['count']

        print(f"\n{domain_with_emoji}")
        print(f"   Wordmap: {len(wordmap)} words")
        print(f"   Contributors: {contributors}")

        if wordmap:
            top_5 = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"   Top words: {', '.join([f'{w}({c})' for w, c in top_5])}")

    conn.close()

    print(f"\n{'='*70}")
    print("🎉 MESH NETWORK IS LIVE!")
    print(f"{'='*70}\n")

    print("Next steps:")
    print("  1. Visit http://localhost:5001/debug")
    print("  2. Visit http://localhost:5001/domains")
    print("  3. Visit http://localhost:5001/cringeproof")
    print("  4. Login as 'matt' and visit http://localhost:5001/me")
    print()


def main():
    """Run the full test flow"""

    print(f"\n{'='*70}")
    print("🧪 MESH NETWORK FLOW TEST")
    print(f"{'='*70}\n")

    # Step 1: Create test user
    print("Step 1: Creating test user...")
    user_id = create_test_user()

    # Step 2: Insert voice recording
    print("\nStep 2: Inserting test voice recording...")
    recording_id = insert_test_voice_recording(user_id)

    # Step 3: Trigger cascade
    print("\nStep 3: Triggering mesh network cascade...")
    trigger_cascade(recording_id)

    # Step 4: Show final state
    print("\nStep 4: Showing final domain state...")
    show_final_state()


if __name__ == '__main__':
    main()
