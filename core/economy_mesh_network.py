#!/usr/bin/env python3
"""
Economy Mesh Network - Minesweeper-Style Automation

The "click one cell, reveal the whole region" automation you've been asking for.

What This Does:
================
Record voice → EVERYTHING cascades automatically:
1. Update user wordmap
2. Match against ALL domains
3. Generate content for matching domains
4. Claim ownership rewards
5. (Optional) Publish to GitHub Pages

This is the mesh network / minesweeper propagation you wanted.

Usage:
======
```python
from economy_mesh_network import on_voice_transcribed

# Automatically called after voice transcription completes
on_voice_transcribed(recording_id=42)

# Result: Everything propagates automatically
```

Manual Trigger:
===============
```bash
python3 economy_mesh_network.py --user 1
```
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db

# Import all economy modules
from user_wordmap_engine import update_user_wordmap, get_user_wordmap
from domain_wordmap_aggregator import recalculate_domain_wordmap, get_domain_wordmap
from voice_content_generator import VoiceContentGenerator
from ownership_rewards import claim_content_reward
from domain_unlock_engine import unlock_domain, get_user_domains


# Configuration
MIN_ALIGNMENT_THRESHOLD = 0.10  # 10% match required (Jaccard similarity)
AUTO_GENERATE_CONTENT = True
AUTO_CLAIM_REWARDS = True
AUTO_PUBLISH = False  # Set to True to auto-publish to GitHub


def on_voice_transcribed(recording_id: int) -> Dict:
    """
    Main entry point: Called when voice transcription completes

    This triggers the entire mesh network cascade:
    Voice → Wordmap → Domains → Content → Rewards

    Args:
        recording_id: ID of the voice recording that was just transcribed

    Returns:
        {
            'success': bool,
            'user_id': int,
            'wordmap_updated': bool,
            'domains_matched': [...],
            'content_generated': {...},
            'rewards_claimed': {...},
            'message': str
        }
    """
    print(f"\n{'='*70}")
    print(f"🎭 MESH NETWORK CASCADE - Recording #{recording_id}")
    print(f"{'='*70}")

    # Get recording info
    db = get_db()
    recording = db.execute('''
        SELECT id, user_id, transcription, filename
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return {'error': 'Recording not found'}

    if not recording['transcription']:
        return {'error': 'No transcription available'}

    user_id = recording['user_id']
    transcription = recording['transcription']

    print(f"✓ Recording: {recording['filename']}")
    print(f"✓ User ID: {user_id}")
    print(f"✓ Transcription: {len(transcription)} chars\n")

    # Step 1: Update user wordmap
    print("🧠 Step 1: Updating personal wordmap...")
    try:
        update_user_wordmap(user_id, recording_id, transcription)
        print("✓ Personal wordmap updated\n")
        wordmap_updated = True
    except Exception as e:
        print(f"✗ Error updating wordmap: {e}\n")
        wordmap_updated = False

    # Step 2: Auto-propagate to all owned domains
    print("🌐 Step 2: Propagating to owned domains...")
    propagated_domains = auto_propagate_wordmap(user_id)
    print(f"✓ Propagated to {len(propagated_domains)} domains\n")

    # Step 3: Match against ALL domains (find new opportunities)
    print("🎯 Step 3: Matching against all domains...")
    matched_domains = auto_match_domains(user_id)
    print(f"✓ Found {len(matched_domains)} matching domains (>{MIN_ALIGNMENT_THRESHOLD*100}%)\n")

    for match in matched_domains[:5]:
        print(f"   {match['domain_with_emoji']} - {match['alignment_score']*100:.1f}% match")
    if len(matched_domains) > 5:
        print(f"   ... and {len(matched_domains) - 5} more")
    print()

    # Step 4: Auto-generate content for matching domains
    content_results = {}
    if AUTO_GENERATE_CONTENT and matched_domains:
        print("📄 Step 4: Generating content for matching domains...")
        content_results = auto_generate_content(user_id, recording_id, matched_domains[:3])  # Top 3 matches
        print(f"✓ Generated content for {len(content_results)} domains\n")

    # Step 5: Auto-claim rewards
    reward_results = {}
    if AUTO_CLAIM_REWARDS and content_results:
        print("💰 Step 5: Claiming ownership rewards...")
        reward_results = auto_claim_rewards(user_id, content_results)
        print(f"✓ Claimed rewards for {len(reward_results)} pieces of content\n")

    # Step 6: Optional auto-publish
    publish_results = {}
    if AUTO_PUBLISH and reward_results:
        print("🚀 Step 6: Publishing to GitHub Pages...")
        publish_results = auto_publish_domains(list(content_results.keys()))
        print(f"✓ Published {len(publish_results)} domains\n")

    # Summary
    print(f"{'='*70}")
    print("🎉 MESH NETWORK CASCADE COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Wordmap updated: {wordmap_updated}")
    print(f"✓ Domains propagated: {len(propagated_domains)}")
    print(f"✓ New matches found: {len(matched_domains)}")
    print(f"✓ Content generated: {len(content_results)}")
    print(f"✓ Rewards claimed: {len(reward_results)}")

    total_rewards = sum(r.get('reward_claimed', 0) for r in reward_results.values())
    if total_rewards > 0:
        print(f"💎 Total ownership earned: +{total_rewards:.2f}%")

    print(f"{'='*70}\n")

    return {
        'success': True,
        'user_id': user_id,
        'recording_id': recording_id,
        'wordmap_updated': wordmap_updated,
        'domains_propagated': propagated_domains,
        'domains_matched': matched_domains,
        'content_generated': content_results,
        'rewards_claimed': reward_results,
        'publish_results': publish_results,
        'message': f"Mesh network cascade complete: {len(matched_domains)} matches, {len(content_results)} content pieces, +{total_rewards:.2f}% ownership"
    }


def auto_propagate_wordmap(user_id: int) -> List[str]:
    """
    Auto-propagate user wordmap to all domains they own

    This updates domain wordmaps based on updated user wordmap + ownership %

    Returns:
        List of domain names that were updated
    """
    # Get user's owned domains
    user_domains = get_user_domains(user_id)

    if not user_domains or 'domains' not in user_domains:
        return []

    updated_domains = []

    for domain_info in user_domains['domains']:
        domain = domain_info['domain']

        try:
            # Recalculate domain wordmap (which includes this user's updated wordmap)
            result = recalculate_domain_wordmap(domain)

            if 'error' not in result:
                updated_domains.append(domain)
                print(f"   ✓ {domain} updated")
        except Exception as e:
            print(f"   ✗ {domain} error: {e}")

    return updated_domains


def get_domain_matching_wordmap(domain: str) -> Optional[Dict[str, int]]:
    """
    Get wordmap for domain matching purposes

    For domains with no owners: use initial_keywords from seed data
    For domains with owners: use dynamic wordmap from contributors

    This prevents the chicken-egg problem where you need ownership to match,
    but you need matching to get ownership.
    """
    db = get_db()

    # Check if domain has any owners
    owner_count = db.execute('''
        SELECT COUNT(*) as count
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE dc.domain = ? AND do.ownership_percentage > 0
    ''', (domain,)).fetchone()['count']

    if owner_count > 0:
        # Domain has owners - use dynamic wordmap
        domain_wordmap_data = get_domain_wordmap(domain)
        if domain_wordmap_data and 'wordmap' in domain_wordmap_data:
            return domain_wordmap_data['wordmap']
        return None
    else:
        # Domain has no owners - use initial_keywords seed data
        domain_data = db.execute('''
            SELECT initial_keywords
            FROM domain_contexts
            WHERE domain = ?
        ''', (domain,)).fetchone()

        if not domain_data or not domain_data['initial_keywords']:
            return None

        # Parse initial_keywords JSON and convert to wordmap format
        keywords = json.loads(domain_data['initial_keywords'])
        # Give each keyword equal weight for matching
        return {word: 10 for word in keywords}


def auto_match_domains(user_id: int, min_alignment: float = MIN_ALIGNMENT_THRESHOLD) -> List[Dict]:
    """
    Match user's wordmap against ALL domains to find opportunities

    This is the "minesweeper reveal" - show ALL connected domains

    Args:
        user_id: User ID
        min_alignment: Minimum alignment score (0.0-1.0)

    Returns:
        List of domains sorted by alignment score:
        [
            {
                'domain': 'cringeproof.com',
                'domain_with_emoji': '🟡 cringeproof.com',
                'tier': 'legendary',
                'alignment_score': 0.92,
                'is_owned': True,
                'ownership_pct': 5.5
            },
            ...
        ]
    """
    from text_encoder import add_tier_emoji

    # Get user's wordmap
    user_wordmap_data = get_user_wordmap(user_id)

    if not user_wordmap_data:
        return []

    user_wordmap = user_wordmap_data['wordmap']

    # Get all domains
    db = get_db()
    all_domains = db.execute('''
        SELECT domain, tier
        FROM domain_contexts
        ORDER BY domain
    ''').fetchall()

    # Get user's owned domains
    owned_domains = {}
    user_domains = get_user_domains(user_id)
    if user_domains and 'domains' in user_domains:
        owned_domains = {
            d['domain']: d['ownership_percentage']
            for d in user_domains['domains']
        }

    # Match against each domain
    matches = []

    for domain_row in all_domains:
        domain = domain_row['domain']
        tier = domain_row['tier']

        # Get domain wordmap (initial keywords if no owners, dynamic if owned)
        domain_wordmap = get_domain_matching_wordmap(domain)

        if not domain_wordmap:
            continue

        # Calculate alignment (Jaccard similarity between wordmaps)
        user_words = set(user_wordmap.keys())
        domain_words = set(domain_wordmap.keys())
        intersection = len(user_words & domain_words)
        union = len(user_words | domain_words)
        alignment_score = intersection / union if union > 0 else 0.0

        # Only include if meets threshold
        if alignment_score >= min_alignment:
            matched_words = user_words & domain_words
            matches.append({
                'domain': domain,
                'domain_with_emoji': add_tier_emoji(domain, tier),
                'tier': tier,
                'alignment_score': alignment_score,
                'is_owned': domain in owned_domains,
                'ownership_pct': owned_domains.get(domain, 0.0),
                'matched_keywords': list(matched_words)[:10]  # Show top 10 matched words
            })

    # Sort by alignment score (highest first)
    matches.sort(key=lambda x: x['alignment_score'], reverse=True)

    return matches


def auto_generate_content(user_id: int, recording_id: int, matched_domains: List[Dict]) -> Dict[str, Dict]:
    """
    Auto-generate content for matching domains

    Args:
        user_id: User ID
        recording_id: Source voice recording ID
        matched_domains: List of matched domains from auto_match_domains()

    Returns:
        {
            'cringeproof.com': {
                'pitch_deck': '...',
                'landing_page': '...',
                'tweet_thread': '...'
            },
            'soulfra.com': {...},
            ...
        }
    """
    # Get transcript from recording
    db = get_db()
    recording = db.execute('''
        SELECT transcription FROM simple_voice_recordings WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording or not recording['transcription']:
        print(f"   ⚠️  No transcript found for recording #{recording_id}")
        return {}

    transcript = recording['transcription']
    generator = VoiceContentGenerator(model='llama3.2:3b')
    content_results = {}

    for match in matched_domains:
        domain = match['domain']
        alignment = match['alignment_score']

        print(f"   📝 Generating for {match['domain_with_emoji']} ({alignment*100:.1f}% match)...")

        try:
            # Generate content using actual methods
            domain_content = {}

            # Generate pitch deck
            pitch_result = generator.generate_pitch_deck(transcript, domain, recording_id)
            if pitch_result and 'error' not in pitch_result:
                domain_content['pitch_deck'] = pitch_result

            # Generate blog post
            blog_result = generator.generate_blog_post(transcript, domain, recording_id)
            if blog_result and 'error' not in blog_result:
                domain_content['blog_post'] = blog_result

            if domain_content:
                content_results[domain] = domain_content
                print(f"      ✓ Generated {len(domain_content)} content types")
            else:
                print(f"      ✗ Generation failed")
                if pitch_result and 'error' in pitch_result:
                    print(f"         Pitch error: {pitch_result['error']}")
                if blog_result and 'error' in blog_result:
                    print(f"         Blog error: {blog_result['error']}")

        except Exception as e:
            print(f"      ✗ Error: {e}")

    return content_results


def content_dict_to_text(content_dict: Dict, content_type: str) -> str:
    """
    Convert structured content dict to plain text for alignment calculation

    Args:
        content_dict: Generated content dict (pitch_deck or blog_post structure)
        content_type: 'pitch_deck' or 'blog_post'

    Returns:
        Plain text string with all content
    """
    text_parts = []

    if content_type == 'pitch_deck':
        # Extract: title + all slide titles + all bullets
        if 'title' in content_dict:
            text_parts.append(content_dict['title'])

        for slide in content_dict.get('slides', []):
            if 'title' in slide:
                text_parts.append(slide['title'])
            for bullet in slide.get('bullets', []):
                text_parts.append(bullet)

    elif content_type == 'blog_post':
        # Extract: title + intro + all sections + conclusion
        if 'title' in content_dict:
            text_parts.append(content_dict['title'])
        if 'intro' in content_dict:
            text_parts.append(content_dict['intro'])

        for section in content_dict.get('sections', []):
            if 'heading' in section:
                text_parts.append(section['heading'])
            if 'content' in section:
                text_parts.append(section['content'])

        if 'conclusion' in content_dict:
            text_parts.append(content_dict['conclusion'])

    return ' '.join(text_parts)


def auto_claim_rewards(user_id: int, content_results: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Auto-claim rewards for generated content

    Args:
        user_id: User ID
        content_results: Results from auto_generate_content()

    Returns:
        {
            'cringeproof.com_pitch_deck': {
                'success': True,
                'alignment_score': 0.92,
                'reward_claimed': 0.5,
                'new_ownership': 6.0
            },
            ...
        }
    """
    reward_results = {}

    for domain, content_dict in content_results.items():
        for content_type, content_data in content_dict.items():
            print(f"   💰 Claiming reward for {domain} ({content_type})...")

            try:
                # Convert content dict to text
                content_text = content_dict_to_text(content_data, content_type)

                result = claim_content_reward(
                    user_id=user_id,
                    domain=domain,
                    content_text=content_text,
                    content_type=content_type
                )

                key = f"{domain}_{content_type}"
                reward_results[key] = result

                if result.get('success'):
                    print(f"      ✓ +{result['reward_claimed']:.2f}% ownership ({result['alignment_score']*100:.1f}% alignment)")
                else:
                    print(f"      ⚠️  {result.get('error', 'Failed')}")

            except Exception as e:
                print(f"      ✗ Error: {e}")

    return reward_results


def auto_publish_domains(domains: List[str]) -> Dict[str, bool]:
    """
    Auto-publish domains to GitHub Pages

    Args:
        domains: List of domain names to publish

    Returns:
        {'cringeproof.com': True, 'soulfra.com': False, ...}
    """
    # This would call publish_all_brands.py or similar
    # For now, just return placeholder
    print("   (Auto-publish not implemented yet - manual: python3 publish_all_brands.py)")
    return {domain: False for domain in domains}


def get_mesh_network_status(user_id: int) -> Dict:
    """
    Get current mesh network status for user

    This powers the /economy/mesh dashboard

    Returns:
        {
            'user': {...},
            'wordmap': {...},
            'matched_domains': [...],
            'owned_domains': [...],
            'recent_content': [...],
            'recent_rewards': [...],
            'network_map': {
                'nodes': [...],
                'edges': [...]
            }
        }
    """
    from user_economy import get_economy_data

    # Get full economy data
    economy = get_economy_data(user_id)

    # Get matched domains
    matched_domains = auto_match_domains(user_id)

    # Build network graph (for visualization)
    network_map = build_network_graph(user_id, economy, matched_domains)

    return {
        'user': economy.get('user', {}),
        'wordmap': economy.get('wordmap', {}),
        'matched_domains': matched_domains,
        'owned_domains': economy.get('domains', []),
        'recent_content': [],  # TODO: Get from content generation history
        'recent_rewards': economy.get('rewards', []),
        'stats': economy.get('stats', {}),
        'network_map': network_map
    }


def build_network_graph(user_id: int, economy: Dict, matched_domains: List[Dict]) -> Dict:
    """
    Build network graph for visualization

    Returns:
        {
            'nodes': [
                {'id': 'user_1', 'type': 'user', 'label': 'username'},
                {'id': 'domain_cringeproof', 'type': 'domain', 'label': '🟡 cringeproof.com', 'tier': 'legendary'},
                ...
            ],
            'edges': [
                {'from': 'user_1', 'to': 'domain_cringeproof', 'label': '92% match', 'weight': 0.92},
                ...
            ]
        }
    """
    nodes = []
    edges = []

    # User node
    username = economy.get('user', {}).get('username', f'user_{user_id}')
    nodes.append({
        'id': f'user_{user_id}',
        'type': 'user',
        'label': username
    })

    # Domain nodes and edges
    for match in matched_domains:
        domain_id = f"domain_{match['domain'].replace('.', '_')}"

        nodes.append({
            'id': domain_id,
            'type': 'domain',
            'label': match['domain_with_emoji'],
            'tier': match['tier'],
            'alignment': match['alignment_score']
        })

        edges.append({
            'from': f'user_{user_id}',
            'to': domain_id,
            'label': f"{match['alignment_score']*100:.0f}% match",
            'weight': match['alignment_score']
        })

    return {
        'nodes': nodes,
        'edges': edges
    }


if __name__ == '__main__':
    """
    Manual trigger for testing

    Usage:
        python3 economy_mesh_network.py --user 1
        python3 economy_mesh_network.py --recording 42
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 economy_mesh_network.py --user <user_id>")
        print("  python3 economy_mesh_network.py --recording <recording_id>")
        sys.exit(1)

    if '--recording' in sys.argv:
        idx = sys.argv.index('--recording')
        recording_id = int(sys.argv[idx + 1])
        result = on_voice_transcribed(recording_id)

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            sys.exit(1)

    elif '--user' in sys.argv:
        idx = sys.argv.index('--user')
        user_id = int(sys.argv[idx + 1])

        # Get most recent recording
        db = get_db()
        recording = db.execute('''
            SELECT id FROM simple_voice_recordings
            WHERE user_id = ? AND transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()

        if not recording:
            print(f"❌ No transcribed recordings found for user {user_id}")
            sys.exit(1)

        result = on_voice_transcribed(recording['id'])

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            sys.exit(1)
