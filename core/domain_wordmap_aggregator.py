#!/usr/bin/env python3
"""
Domain Wordmap Aggregator - Collective Brand Voice

Combines all user wordmaps into a single domain wordmap based on ownership %.

Example:
- Alice owns 60% of soulfra.com, her wordmap = 60% of domain voice
- Bob owns 30% of soulfra.com, his wordmap = 30% of domain voice
- Charlie owns 10% of soulfra.com, his wordmap = 10% of domain voice

Result: Domain wordmap = weighted average of all owners' voices

This creates AUTHENTIC brand voice that evolves as ownership changes.

Tables:
- domain_wordmaps: domain, wordmap_json, contributor_count, last_updated
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter
from database import get_db


def init_domain_wordmap_table():
    """Create domain_wordmaps table"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS domain_wordmaps (
            domain TEXT PRIMARY KEY,
            wordmap_json TEXT NOT NULL,
            contributor_count INTEGER DEFAULT 0,
            total_recordings INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    print("✅ domain_wordmaps table created")


def get_domain_wordmap(domain: str) -> Optional[Dict]:
    """
    Get domain's current wordmap

    Returns:
        {
            'wordmap': {'word': weighted_frequency, ...},
            'contributor_count': number of users contributing,
            'last_updated': timestamp
        }
    """
    db = get_db()

    result = db.execute('''
        SELECT wordmap_json, contributor_count, total_recordings, last_updated
        FROM domain_wordmaps
        WHERE domain = ?
    ''', (domain,)).fetchone()

    if not result:
        return None

    return {
        'wordmap': json.loads(result['wordmap_json']),
        'contributor_count': result['contributor_count'],
        'total_recordings': result['total_recordings'],
        'last_updated': result['last_updated']
    }


def recalculate_domain_wordmap(domain: str) -> Dict:
    """
    Recalculate domain wordmap from all owners' wordmaps

    Process:
    1. Get all users who own this domain + their ownership %
    2. Get each user's personal wordmap
    3. Weight each wordmap by ownership %
    4. Merge into collective domain wordmap

    Returns:
        {
            'domain': domain name,
            'wordmap': weighted wordmap,
            'contributors': list of contributing users,
            'total_ownership': should = 100%
        }
    """
    from user_wordmap_engine import get_user_wordmap
    from domain_unlock_engine import get_user_domains

    db = get_db()

    # Get all owners of this domain
    owners = db.execute('''
        SELECT do.user_id, do.ownership_percentage
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE dc.domain = ?
        AND do.ownership_percentage > 0
    ''', (domain,)).fetchall()

    if not owners:
        return {
            'error': f'No owners found for {domain}',
            'domain': domain
        }

    # Aggregate wordmaps
    aggregated = {}
    contributors = []
    total_ownership = 0
    total_recordings = 0

    for owner in owners:
        user_id = owner['user_id']
        ownership_pct = owner['ownership_percentage'] / 100.0  # Convert to 0.0-1.0

        # Get user's wordmap
        user_wordmap_data = get_user_wordmap(user_id)

        if not user_wordmap_data:
            continue  # Skip users without wordmaps

        user_wordmap = user_wordmap_data['wordmap']

        # Weight each word by user's ownership percentage
        for word, count in user_wordmap.items():
            weighted_count = count * ownership_pct

            if word in aggregated:
                aggregated[word] += weighted_count
            else:
                aggregated[word] = weighted_count

        contributors.append({
            'user_id': user_id,
            'ownership_pct': owner['ownership_percentage'],
            'recordings': user_wordmap_data['recording_count']
        })

        total_ownership += owner['ownership_percentage']
        total_recordings += user_wordmap_data['recording_count']

    # Round weighted counts and sort
    final_wordmap = {
        word: int(count)
        for word, count in aggregated.items()
        if count >= 1.0  # Filter out words with very low weight
    }

    # Sort by weighted frequency
    sorted_wordmap = dict(
        sorted(final_wordmap.items(), key=lambda x: x[1], reverse=True)[:200]
    )

    # Update database
    db.execute('''
        INSERT OR REPLACE INTO domain_wordmaps
        (domain, wordmap_json, contributor_count, total_recordings, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        domain,
        json.dumps(sorted_wordmap),
        len(contributors),
        total_recordings,
        datetime.now().isoformat()
    ))
    db.commit()

    return {
        'domain': domain,
        'wordmap': sorted_wordmap,
        'contributors': contributors,
        'total_ownership': total_ownership,
        'vocabulary_size': len(sorted_wordmap),
        'total_recordings': total_recordings
    }


def get_user_contribution_to_domain(user_id: int, domain: str) -> Dict:
    """
    Calculate how much a specific user contributes to a domain's wordmap

    Returns:
        {
            'user_id': int,
            'domain': str,
            'ownership_pct': ownership percentage,
            'words_contributed': words from user's wordmap in domain wordmap,
            'influence_score': 0.0-1.0 (how much their voice shapes the domain)
        }
    """
    from user_wordmap_engine import get_user_wordmap
    from domain_unlock_engine import get_user_domains

    db = get_db()

    # Get user's ownership
    ownership = db.execute('''
        SELECT ownership_percentage
        FROM domain_ownership
        WHERE user_id = ? AND domain = ?
    ''', (user_id, domain)).fetchone()

    if not ownership:
        return {
            'error': f'User {user_id} does not own {domain}',
            'user_id': user_id,
            'domain': domain
        }

    # Get user's wordmap
    user_wordmap_data = get_user_wordmap(user_id)
    if not user_wordmap_data:
        return {
            'error': f'User {user_id} has no wordmap',
            'user_id': user_id,
            'domain': domain
        }

    user_wordmap = set(user_wordmap_data['wordmap'].keys())

    # Get domain's wordmap
    domain_wordmap_data = get_domain_wordmap(domain)
    if not domain_wordmap_data:
        return {
            'error': f'Domain {domain} has no wordmap',
            'user_id': user_id,
            'domain': domain
        }

    domain_wordmap = set(domain_wordmap_data['wordmap'].keys())

    # Calculate contribution
    words_in_common = user_wordmap & domain_wordmap
    influence_score = (ownership['ownership_percentage'] / 100.0) * (len(words_in_common) / len(domain_wordmap) if domain_wordmap else 0)

    return {
        'user_id': user_id,
        'domain': domain,
        'ownership_pct': ownership['ownership_percentage'],
        'words_contributed': list(words_in_common)[:20],
        'contribution_count': len(words_in_common),
        'domain_vocabulary_size': len(domain_wordmap),
        'influence_score': influence_score
    }


def update_all_domain_wordmaps() -> List[Dict]:
    """
    Recalculate wordmaps for all domains that have owners

    Returns list of results for each domain
    """
    db = get_db()

    # Get all domains with ownership
    domains = db.execute('''
        SELECT DISTINCT domain
        FROM domain_ownership
        WHERE ownership_percentage > 0
    ''').fetchall()

    results = []
    for domain_row in domains:
        domain = domain_row['domain']
        result = recalculate_domain_wordmap(domain)
        results.append(result)

    return results


def compare_domain_wordmaps(domain1: str, domain2: str) -> Dict:
    """
    Compare two domains' wordmaps

    Returns:
        {
            'overlap_words': words both domains use,
            'domain1_unique': words only domain1 uses,
            'domain2_unique': words only domain2 uses,
            'similarity_score': 0.0-1.0
        }
    """
    wordmap1_data = get_domain_wordmap(domain1)
    wordmap2_data = get_domain_wordmap(domain2)

    if not wordmap1_data or not wordmap2_data:
        return {'error': 'One or both domains have no wordmap'}

    words1 = set(wordmap1_data['wordmap'].keys())
    words2 = set(wordmap2_data['wordmap'].keys())

    overlap = words1 & words2
    unique1 = words1 - words2
    unique2 = words2 - words1

    # Jaccard similarity
    similarity = len(overlap) / len(words1 | words2) if (words1 | words2) else 0.0

    return {
        'domain1': domain1,
        'domain2': domain2,
        'overlap_words': list(overlap)[:20],
        'domain1_unique': list(unique1)[:20],
        'domain2_unique': list(unique2)[:20],
        'similarity_score': similarity,
        'overlap_count': len(overlap),
        'total_unique_words': len(words1 | words2)
    }


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 domain_wordmap_aggregator.py init                    # Create table")
        print("  python3 domain_wordmap_aggregator.py calculate <domain>      # Recalculate domain wordmap")
        print("  python3 domain_wordmap_aggregator.py show <domain>           # Show domain wordmap")
        print("  python3 domain_wordmap_aggregator.py update-all              # Update all domains")
        print("  python3 domain_wordmap_aggregator.py compare <d1> <d2>       # Compare two domains")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        init_domain_wordmap_table()

    elif command == 'calculate' and len(sys.argv) > 2:
        domain = sys.argv[2]
        result = recalculate_domain_wordmap(domain)
        print(json.dumps(result, indent=2))

    elif command == 'show' and len(sys.argv) > 2:
        domain = sys.argv[2]
        wordmap = get_domain_wordmap(domain)
        print(json.dumps(wordmap, indent=2))

    elif command == 'update-all':
        results = update_all_domain_wordmaps()
        print(json.dumps(results, indent=2))

    elif command == 'compare' and len(sys.argv) > 3:
        d1 = sys.argv[2]
        d2 = sys.argv[3]
        comparison = compare_domain_wordmaps(d1, d2)
        print(json.dumps(comparison, indent=2))

    else:
        print("Unknown command")
        sys.exit(1)
