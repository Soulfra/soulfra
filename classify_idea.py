#!/usr/bin/env python3
"""
CringeProof Idea Classifier - Domain Routing Engine

Routes voice ideas to the correct domain based on semantic similarity.

Uses simple keyword overlap scoring between transcription and domain wordmaps.
No ML needed - just word frequency matching.

Example:
- Transcription: "I hate social media cringe, be authentic, build real community"
- Keywords: social, media, cringe, authentic, community
- Best match: cringeproof.com (contains: social, cringe, authentic, community)
- Score: 5/6 keywords = 83%

Domains:
- cringeproof.com: authentic, social, cringe, genuine, trust, community...
- soulfra.com: soul, infrastructure, meaning, purpose, growth...
- deathtodata.com: privacy, data, surveillance, freedom, encryption...
"""

import json
import re
from typing import List, Dict, Tuple
from collections import Counter
from database import get_db


def extract_keywords(text: str, min_length: int = 4) -> List[str]:
    """
    Extract meaningful keywords from text

    Filters out:
    - Stop words (the, is, and, of, to, a, in, that, it...)
    - Short words (< 4 chars)
    - Numbers
    """
    # Common stop words to ignore
    stop_words = {
        'the', 'is', 'and', 'of', 'to', 'a', 'in', 'that', 'it', 'with',
        'for', 'as', 'was', 'on', 'are', 'be', 'this', 'which', 'or', 'from',
        'but', 'not', 'have', 'had', 'has', 'will', 'would', 'could', 'should',
        'been', 'being', 'can', 'their', 'they', 'them', 'were', 'said', 'about',
        'into', 'than', 'your', 'you', 'like', 'just', 'know', 'think', 'want',
        'need', 'make', 'really', 'very', 'some', 'any', 'all', 'when', 'where',
        'what', 'who', 'how', 'why', 'there', 'here', 'going', 'gonna', 'yeah',
        'thats', 'dont', 'cant', 'wont', 'aint'
    }

    # Lowercase and extract words
    words = re.findall(r'\b[a-z]+\b', text.lower())

    # Filter
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]

    return keywords


def calculate_domain_match(keywords: List[str], domain_wordmap: Dict[str, int]) -> float:
    """
    Calculate match score between keywords and domain wordmap

    Score = (number of matching keywords) / (total keywords)

    Returns: 0.0 to 1.0 (percentage match)
    """
    if not keywords:
        return 0.0

    domain_words = set(domain_wordmap.keys())
    matching_keywords = [kw for kw in keywords if kw in domain_words]

    match_count = len(matching_keywords)
    total_count = len(keywords)

    score = match_count / total_count if total_count > 0 else 0.0

    return score


def classify_idea(transcription: str) -> List[Dict[str, any]]:
    """
    Classify idea to best-matching domain(s)

    Args:
        transcription: Voice recording transcription text

    Returns:
        [
            {'domain': 'cringeproof.com', 'score': 0.87, 'matches': ['social', 'cringe', 'authentic']},
            {'domain': 'soulfra.com', 'score': 0.34, 'matches': ['community']},
            ...
        ]

        Sorted by score (highest first)
    """
    # Get all domain wordmaps
    db = get_db()

    domains = db.execute('''
        SELECT domain, wordmap_json
        FROM domain_wordmaps
    ''').fetchall()

    if not domains:
        print("⚠️  No domain wordmaps found - run seed_domain_wordmaps.py")
        return []

    # Extract keywords from transcription
    keywords = extract_keywords(transcription)

    if not keywords:
        print(f"⚠️  No keywords extracted from: {transcription[:100]}")
        return []

    # Calculate match for each domain
    results = []

    for domain_row in domains:
        domain = domain_row['domain']
        wordmap = json.loads(domain_row['wordmap_json'])

        score = calculate_domain_match(keywords, wordmap)

        # Find which keywords matched
        domain_words = set(wordmap.keys())
        matches = [kw for kw in keywords if kw in domain_words]

        results.append({
            'domain': domain,
            'score': score,
            'matches': matches,
            'total_keywords': len(keywords),
            'matched_keywords': len(matches)
        })

    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)

    db.close()

    return results


def get_best_domain(transcription: str) -> str:
    """
    Get single best-matching domain for idea

    Returns: 'cringeproof.com' (or None if no match)
    """
    results = classify_idea(transcription)

    if not results or results[0]['score'] == 0:
        return None

    return results[0]['domain']


def classify_and_store(idea_id: int, transcription: str, threshold: float = 0.2) -> List[str]:
    """
    Classify idea and store domain assignment in database

    Args:
        idea_id: Voice idea ID
        transcription: Transcription text
        threshold: Minimum score to assign domain (0.0-1.0)

    Returns: List of assigned domain names
    """
    results = classify_idea(transcription)

    if not results:
        return []

    # Get domains above threshold
    assigned_domains = [r['domain'] for r in results if r['score'] >= threshold]

    if not assigned_domains:
        # If nothing matches threshold, use best match anyway
        assigned_domains = [results[0]['domain']]

    db = get_db()

    # For now, just store the best match in domain_id
    # (Later could expand to many-to-many relationship)
    best_domain = assigned_domains[0]

    # Get domain ID
    domain_id_row = db.execute('''
        SELECT id FROM brands WHERE domain = ?
    ''', (best_domain,)).fetchone()

    if domain_id_row:
        domain_id = domain_id_row['id']

        # Update voice_ideas
        db.execute('''
            UPDATE voice_ideas
            SET domain_id = ?, auto_assigned = 1
            WHERE id = ?
        ''', (domain_id, idea_id))

        db.commit()

        print(f"✅ Idea #{idea_id} → {best_domain} (score: {results[0]['score']:.2f})")

    db.close()

    return assigned_domains


if __name__ == '__main__':
    # Test classification
    test_transcriptions = [
        "I hate cringe on social media. Everyone's so fake. We need authentic community where people can be real.",
        "Privacy is a human right. Data surveillance capitalism must end. We need encrypted, decentralized systems.",
        "Building infrastructure for human flourishing. Systems that support growth, meaning, and purpose.",
    ]

    for i, text in enumerate(test_transcriptions, 1):
        print(f"\n{'='*60}")
        print(f"Test #{i}: {text[:60]}...")
        print(f"{'='*60}")

        results = classify_idea(text)

        for result in results:
            print(f"\n{result['domain']}: {result['score']:.0%}")
            print(f"   Matches ({len(result['matches'])}/{result['total_keywords']}): {', '.join(result['matches'][:10])}")

        best = get_best_domain(text)
        print(f"\n🎯 Best match: {best}")
