#!/usr/bin/env python3
"""
Dogfood Script: Build Cringeproof.com Using The Wordmap Economy

This script PROVES the system works by using it to build cringeproof.com:
1. Initialize cringeproof.com domain
2. Check for existing voice recordings about cringeproof
3. Build cringeproof wordmap from your voice
4. Generate pitch deck using wordmap-aligned content
5. Claim ownership rewards
6. Publish to GitHub Pages / IPFS

Usage:
    python3 build_cringeproof.py                    # Guided mode
    python3 build_cringeproof.py --auto             # Fully automated
    python3 build_cringeproof.py --publish-ipfs     # Auto-publish to IPFS
"""

import sys
import json
from datetime import datetime
from database import get_db

# Import economy modules
from user_wordmap_engine import update_user_wordmap, get_user_wordmap
from domain_wordmap_aggregator import recalculate_domain_wordmap, get_domain_wordmap
from domain_unlock_engine import unlock_domain, increase_ownership, get_user_domains
from ownership_rewards import claim_content_reward
from voice_content_generator import VoiceContentGenerator


CRINGEPROOF_DOMAIN = 'cringeproof.com'
BOOTSTRAP_USER_ID = 1  # Admin/bootstrap user


def init_cringeproof_domain():
    """Initialize cringeproof.com in the database"""
    print("🏗️  Initializing cringeproof.com domain...")

    db = get_db()

    # Check if domain context exists
    existing = db.execute('''
        SELECT domain FROM domain_contexts WHERE domain = ?
    ''', (CRINGEPROOF_DOMAIN,)).fetchone()

    if not existing:
        # Create domain context using correct schema
        db.execute('''
            INSERT OR IGNORE INTO domain_contexts
            (domain, domain_slug, context_type, content, tier, unlock_cost, takeover_threshold_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (CRINGEPROOF_DOMAIN, 'cringeproof', 'definition', 'Intent vs Intuition - The Cringe Filter', 'legendary', 200, 365))
        db.commit()
        print(f"✅ Created domain context for {CRINGEPROOF_DOMAIN}")

    # Unlock domain for bootstrap user
    try:
        success = unlock_domain(BOOTSTRAP_USER_ID, CRINGEPROOF_DOMAIN, source='dogfood_script')

        if success:
            print(f"✅ Unlocked {CRINGEPROOF_DOMAIN} for user {BOOTSTRAP_USER_ID}")
            return True
        else:
            # Check if already unlocked
            existing_ownership = db.execute('''
                SELECT ownership_percentage FROM domain_ownership
                WHERE user_id = ? AND domain = ?
            ''', (BOOTSTRAP_USER_ID, CRINGEPROOF_DOMAIN)).fetchone()

            if existing_ownership:
                print(f"✅ {CRINGEPROOF_DOMAIN} already unlocked ({existing_ownership['ownership_percentage']}% ownership)")
                return True
            else:
                print(f"❌ Failed to unlock {CRINGEPROOF_DOMAIN}")
                return False

    except Exception as e:
        print(f"❌ Error initializing domain: {e}")
        return False


def check_voice_recordings():
    """Check for existing voice recordings about cringeproof"""
    print("\n🎤 Checking for voice recordings...")

    db = get_db()

    # Get all voice recordings for bootstrap user
    recordings = db.execute('''
        SELECT id, filename, transcription, created_at
        FROM simple_voice_recordings
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (BOOTSTRAP_USER_ID,)).fetchall()

    if not recordings:
        print("⚠️  No voice recordings found")
        print("\n📝 To build cringeproof wordmap, record voice memos:")
        print("   1. Go to /voice in your browser")
        print("   2. Record 3-5 voice memos explaining:")
        print("      - What is cringeproof?")
        print("      - Why does it matter?")
        print("      - Who is it for?")
        print("   3. Run this script again")
        return None

    # Filter recordings mentioning "cringeproof"
    cringeproof_recordings = [
        r for r in recordings
        if r['transcription'] and 'cringeproof' in r['transcription'].lower()
    ]

    if cringeproof_recordings:
        print(f"✅ Found {len(cringeproof_recordings)} recordings mentioning cringeproof")
        for r in cringeproof_recordings[:3]:
            snippet = r['transcription'][:80] + '...' if r['transcription'] else 'No transcription'
            print(f"   - {r['filename']}: {snippet}")
        return cringeproof_recordings
    else:
        print(f"⚠️  Found {len(recordings)} recordings, but none mention 'cringeproof'")
        print("   Record voice memos about cringeproof and try again")
        return None


def build_wordmap(user_id: int):
    """Build user wordmap from all their recordings"""
    print("\n🧠 Building personal wordmap...")

    db = get_db()

    # Get all recordings
    recordings = db.execute('''
        SELECT id, transcription
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at ASC
    ''', (user_id,)).fetchall()

    if not recordings:
        print("❌ No transcribed recordings found")
        return False

    # Update wordmap with each recording
    for recording in recordings:
        update_user_wordmap(user_id, recording['id'], recording['transcription'])

    # Get final wordmap
    wordmap_data = get_user_wordmap(user_id)

    if wordmap_data:
        word_count = len(wordmap_data['wordmap'])
        print(f"✅ Wordmap built: {word_count} unique words")
        print(f"   Top 10 words: {list(wordmap_data['wordmap'].items())[:10]}")
        return True
    else:
        print("❌ Failed to build wordmap")
        return False


def build_domain_wordmap():
    """Build cringeproof.com domain wordmap"""
    print("\n🌐 Building domain wordmap...")

    # Recalculate domain wordmap (ownership already exists from unlock)
    result = recalculate_domain_wordmap(CRINGEPROOF_DOMAIN)

    if 'error' in result:
        print(f"❌ {result['error']}")
        return False

    word_count = len(result['wordmap'])
    print(f"✅ Domain wordmap built: {word_count} unique words")
    print(f"   Contributors: {result['contributor_count']}")
    print(f"   Top 10 words: {list(result['wordmap'].items())[:10]}")

    return True


def generate_pitch_deck():
    """Generate pitch deck for cringeproof.com"""
    print("\n📄 Generating pitch deck...")

    db = get_db()

    # Get latest voice recording as source
    recording = db.execute('''
        SELECT id, transcription, filename
        FROM simple_voice_recordings
        WHERE user_id = ? AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
    ''', (BOOTSTRAP_USER_ID,)).fetchone()

    if not recording:
        print("❌ No voice recording found to generate from")
        return None

    try:
        generator = VoiceContentGenerator()

        # Generate pitch deck
        print(f"   Using recording: {recording['filename']}")
        result = generator.generate_from_recording(
            recording_id=recording['id'],
            content_types=['pitch_deck'],
            target_domains=[CRINGEPROOF_DOMAIN]
        )

        if result and 'pitch_deck' in result:
            pitch = result['pitch_deck']
            print(f"✅ Pitch deck generated ({len(pitch)} chars)")
            print(f"   Preview: {pitch[:200]}...")
            return pitch
        else:
            print("❌ Pitch deck generation failed")
            return None

    except Exception as e:
        print(f"❌ Error generating pitch deck: {e}")
        return None


def claim_rewards(content_text: str):
    """Claim ownership rewards for generated content"""
    print("\n💰 Claiming ownership rewards...")

    result = claim_content_reward(
        user_id=BOOTSTRAP_USER_ID,
        domain=CRINGEPROOF_DOMAIN,
        content_text=content_text,
        content_type='pitch_deck'
    )

    if result.get('success'):
        print(f"✅ Reward claimed!")
        print(f"   Alignment score: {result['alignment_score']:.2%}")
        print(f"   Reward: +{result['reward_claimed']}%")
        print(f"   New ownership: {result['new_ownership']}%")
        print(f"   Tier: {result['tier']}")
        return True
    else:
        print(f"⚠️  {result.get('error', 'Could not claim reward')}")
        print(f"   Alignment score: {result.get('alignment_score', 0):.2%}")
        return False


def publish_to_github():
    """Publish to GitHub Pages (placeholder)"""
    print("\n🚀 Publishing to GitHub Pages...")
    print("   (This would call publish_all_brands.py with cringeproof)")
    print("   Manual step: Run `python3 publish_all_brands.py --brand cringeproof`")
    return True


def show_summary():
    """Show final summary"""
    print("\n" + "="*60)
    print("🎉 CRINGEPROOF.COM BUILD COMPLETE!")
    print("="*60)

    # Get current state
    domain_wordmap = get_domain_wordmap(CRINGEPROOF_DOMAIN)
    user_domains = get_user_domains(BOOTSTRAP_USER_ID)

    if domain_wordmap:
        print(f"\n📊 Domain Wordmap:")
        print(f"   Words: {len(domain_wordmap['wordmap'])}")
        print(f"   Contributors: {domain_wordmap['contributor_count']}")
        print(f"   Recordings: {domain_wordmap['total_recordings']}")

    if user_domains and 'domains' in user_domains:
        for d in user_domains['domains']:
            if d['domain'] == CRINGEPROOF_DOMAIN:
                print(f"\n💎 Your Ownership:")
                print(f"   Domain: {d['domain']}")
                print(f"   Ownership: {d['ownership_percentage']}%")
                print(f"   Unlocked: {d['unlocked_at']}")

    print("\n✨ Next Steps:")
    print("   1. View your economy dashboard: http://localhost:5001/me")
    print("   2. Generate more content to increase ownership")
    print("   3. Publish: python3 publish_all_brands.py --brand cringeproof")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Build cringeproof.com using wordmap economy')
    parser.add_argument('--auto', action='store_true', help='Fully automated mode')
    parser.add_argument('--publish-ipfs', action='store_true', help='Auto-publish to IPFS')

    args = parser.parse_args()

    print("🎭 DOGFOOD: Building Cringeproof.com Using The System")
    print("="*60)

    # Step 1: Init domain
    if not init_cringeproof_domain():
        sys.exit(1)

    # Step 2: Check voice recordings
    recordings = check_voice_recordings()
    if not recordings and not args.auto:
        sys.exit(0)  # Exit gracefully - user needs to record

    # Step 3: Build personal wordmap
    if not build_wordmap(BOOTSTRAP_USER_ID):
        print("❌ Failed to build wordmap")
        sys.exit(1)

    # Step 4: Build domain wordmap
    if not build_domain_wordmap():
        print("❌ Failed to build domain wordmap")
        sys.exit(1)

    # Step 5: Generate content
    pitch_deck = generate_pitch_deck()
    if not pitch_deck:
        print("❌ Failed to generate content")
        sys.exit(1)

    # Step 6: Claim rewards
    claim_rewards(pitch_deck)

    # Step 7: Publish (optional)
    if args.publish_ipfs:
        publish_to_github()

    # Show summary
    show_summary()


if __name__ == '__main__':
    main()
