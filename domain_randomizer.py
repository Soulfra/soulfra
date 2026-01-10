#!/usr/bin/env python3
"""
Domain Randomizer - Smart assignment of users to domains

Features:
1. Language-based routing (Chinese → zh site, Spanish → es site)
2. Letter collision handling (Wu, Wang, Li all want 'W' → randomize)
3. Load balancing (distribute evenly across domains)
4. Spillover (if domain full, assign to next available)

Usage:
    python3 domain_randomizer.py assign john@example.com en
    python3 domain_randomizer.py assign wu@example.com zh
    python3 domain_randomizer.py stats
"""

import hashlib
import random
from database import get_db
from launch_calculator import get_letter_allocation


# Domain preferences by language
LANGUAGE_DOMAIN_MAP = {
    'en': ['soulfra', 'calriven'],       # English: Hub or Blog
    'es': ['calriven', 'soulfra'],       # Spanish: Blog first
    'ja': ['soulfra', 'cringeproof'],    # Japanese: Hub or Filter
    'zh': ['deathtodata', 'soulfra'],    # Chinese: Data or Hub
    'fr': ['calriven', 'soulfra'],       # French: Blog first
}


def get_name_letter(email):
    """
    Get first letter from email username for letter slot assignment

    Args:
        email (str): User email

    Returns:
        str: First letter (A-Z)
    """
    username = email.split('@')[0]
    first_char = username[0].upper()

    # Ensure it's A-Z
    if first_char.isalpha():
        return first_char
    else:
        # Fallback: hash email to get consistent letter
        hash_val = int(hashlib.md5(email.encode()).hexdigest(), 16)
        return chr(ord('A') + (hash_val % 26))


def assign_domain_smart(email, lang='en', prefer_domain=None):
    """
    Smart domain assignment based on language, availability, and load

    Args:
        email (str): User email
        lang (str): Language code (en, es, ja, zh, fr)
        prefer_domain (str): Optional preferred domain

    Returns:
        dict: Assignment result with domain, letter, reason
    """
    db = get_db()

    # Get preferred domains for language
    preferred_domains = LANGUAGE_DOMAIN_MAP.get(lang, ['soulfra', 'calriven'])

    # If user specified preference, try that first
    if prefer_domain and prefer_domain in ['soulfra', 'calriven', 'deathtodata', 'cringeproof']:
        preferred_domains = [prefer_domain] + [d for d in preferred_domains if d != prefer_domain]

    # Get user's letter
    user_letter = get_name_letter(email)

    # Try each domain in order of preference
    for domain in preferred_domains:
        allocation = get_letter_allocation(domain)

        # Check if letter available
        if user_letter in allocation['available']:
            return {
                'domain': domain,
                'letter': user_letter,
                'reason': f'Language preference ({lang}) + letter available ({user_letter})',
                'available_slots': allocation['remaining_slots']
            }

    # Letter not available in preferred domains → spillover
    all_domains = ['soulfra', 'calriven', 'deathtodata', 'cringeproof']
    random.shuffle(all_domains)  # Randomize to distribute load

    for domain in all_domains:
        allocation = get_letter_allocation(domain)

        if allocation['remaining_slots'] > 0:
            # Assign next available letter
            next_letter = allocation['available'][0]

            return {
                'domain': domain,
                'letter': next_letter,
                'reason': f'Spillover (preferred full) → assigned {next_letter}',
                'available_slots': allocation['remaining_slots']
            }

    # All domains full
    return {
        'domain': None,
        'letter': None,
        'reason': 'ALL DOMAINS FULL (104/104 total slots)',
        'available_slots': 0
    }


def get_assignment_stats():
    """
    Get statistics on domain assignments

    Returns:
        dict: Stats per domain
    """
    db = get_db()

    stats = {}

    for domain in ['soulfra', 'calriven', 'deathtodata', 'cringeproof']:
        signups = db.execute('''
            SELECT COUNT(*) as count FROM waitlist WHERE domain_name = ?
        ''', (domain,)).fetchone()['count']

        allocation = get_letter_allocation(domain)

        # Count by language (based on email TLD or referral)
        lang_breakdown = {
            'en': 0,
            'es': 0,
            'ja': 0,
            'zh': 0,
            'fr': 0,
            'other': 0
        }

        # TODO: Track language in database for more accurate stats

        stats[domain] = {
            'signups': signups,
            'slots_used': 26 - allocation['remaining_slots'],
            'slots_available': allocation['remaining_slots'],
            'is_full': allocation['is_full'],
            'language_breakdown': lang_breakdown
        }

    return stats


def display_stats():
    """
    Display assignment statistics in console
    """
    stats = get_assignment_stats()

    print(f"\n{'='*60}")
    print(f"DOMAIN ASSIGNMENT STATISTICS")
    print(f"{'='*60}")
    print(f"{'Domain':<15} {'Signups':<10} {'Slots':<15} {'Status':<10}")
    print(f"{'-'*60}")

    total_signups = 0

    for domain, data in stats.items():
        slots_str = f"{data['slots_used']}/26"
        status = "🔴 FULL" if data['is_full'] else "🟢 Open"

        print(f"{domain:<15} {data['signups']:<10} {slots_str:<15} {status:<10}")

        total_signups += data['signups']

    print(f"{'-'*60}")
    print(f"Total Signups: {total_signups}/104 (4 domains × 26 letters)")
    print(f"{'='*60}\n")


def simulate_assignments(num_users=100, lang_distribution=None):
    """
    Simulate domain assignments to test distribution

    Args:
        num_users (int): Number of users to simulate
        lang_distribution (dict): % distribution by language

    Returns:
        dict: Simulation results
    """
    if lang_distribution is None:
        lang_distribution = {
            'en': 0.40,
            'es': 0.20,
            'zh': 0.20,
            'ja': 0.10,
            'fr': 0.10
        }

    results = {
        'soulfra': 0,
        'calriven': 0,
        'deathtodata': 0,
        'cringeproof': 0
    }

    langs = []
    for lang, pct in lang_distribution.items():
        langs.extend([lang] * int(num_users * pct))

    random.shuffle(langs)

    for i, lang in enumerate(langs):
        email = f"user{i}@example.com"
        assignment = assign_domain_smart(email, lang)

        if assignment['domain']:
            results[assignment['domain']] += 1

    print(f"\n{'='*60}")
    print(f"SIMULATION RESULTS ({num_users} users)")
    print(f"{'='*60}")

    for domain, count in results.items():
        pct = (count / num_users) * 100
        print(f"{domain:<15} {count:<5} ({pct:.1f}%)")

    print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 domain_randomizer.py assign <email> <lang>")
        print("  python3 domain_randomizer.py stats")
        print("  python3 domain_randomizer.py simulate [num_users]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "assign":
        if len(sys.argv) < 4:
            print("Usage: python3 domain_randomizer.py assign <email> <lang>")
            sys.exit(1)

        email = sys.argv[2]
        lang = sys.argv[3]

        assignment = assign_domain_smart(email, lang)

        print(f"\n{'='*60}")
        print(f"ASSIGNMENT FOR: {email}")
        print(f"{'='*60}")
        print(f"Domain: {assignment['domain']}")
        print(f"Letter: {assignment['letter']}")
        print(f"Reason: {assignment['reason']}")
        print(f"Slots Remaining: {assignment['available_slots']}/26")
        print(f"{'='*60}\n")

    elif command == "stats":
        display_stats()

    elif command == "simulate":
        num_users = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        simulate_assignments(num_users)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
