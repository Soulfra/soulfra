#!/usr/bin/env python3
"""
Launch Calculator - Gamified waitlist with acceleration mechanics

Each domain starts with a 90-day launch countdown.
For every 10 signups, the launch date accelerates by 1 day.
At 900+ signups, the domain launches instantly.

Formula:
    days_until_launch = max(0, 90 - (signups // 10))

Examples:
    0 signups → 90 days
    100 signups → 80 days
    500 signups → 40 days
    900 signups → 0 days (INSTANT LAUNCH)

Usage:
    python3 launch_calculator.py calculate soulfra
    python3 launch_calculator.py leaderboard
    python3 launch_calculator.py launch soulfra
"""

from datetime import datetime, timezone, timedelta
from database import get_db
import json


def calculate_launch_date(domain_name):
    """
    Calculate launch date for a domain based on signups

    Args:
        domain_name (str): Domain name (soulfra, calriven, etc.)

    Returns:
        dict: Launch info (days_until, launch_date, signups, is_launched)
    """
    db = get_db()

    # Get domain launch config
    domain = db.execute('''
        SELECT * FROM domain_launches WHERE domain_name = ?
    ''', (domain_name,)).fetchone()

    if not domain:
        return None

    # Count current signups
    signups = db.execute('''
        SELECT COUNT(*) as count FROM waitlist WHERE domain_name = ?
    ''', (domain_name,)).fetchone()['count']

    # Update signup count
    db.execute('''
        UPDATE domain_launches SET current_signups = ? WHERE domain_name = ?
    ''', (signups, domain_name))
    db.commit()

    # Already launched? (check if launched_at is set)
    if domain['launched_at'] is not None:
        return {
            'domain_name': domain_name,
            'is_launched': True,
            'launched_at': domain['launched_at'],
            'signups': signups,
            'days_until': 0
        }

    # Calculate days until launch
    base_days = domain['base_launch_days']
    acceleration = signups // 10  # 1 day off per 10 signups
    days_until = max(0, base_days - acceleration)

    # Instant launch at threshold
    if signups >= domain['instant_launch_threshold']:
        days_until = 0

    # Calculate exact launch date
    now = datetime.now(timezone.utc)
    launch_date = now + timedelta(days=days_until)

    return {
        'domain_name': domain_name,
        'is_launched': False,
        'signups': signups,
        'days_until': days_until,
        'launch_date': launch_date.isoformat(),
        'acceleration': acceleration,
        'instant_threshold': domain['instant_launch_threshold'],
        'progress_pct': min(100, (signups / domain['instant_launch_threshold']) * 100)
    }


def mark_domain_launched(domain_name):
    """
    Mark a domain as launched

    Args:
        domain_name (str): Domain name

    Returns:
        bool: Success
    """
    db = get_db()

    launched_at = datetime.now(timezone.utc).isoformat()

    db.execute('''
        UPDATE domain_launches
        SET is_live = 1, launched_at = ?
        WHERE domain_name = ?
    ''', (launched_at, domain_name))

    db.commit()

    print(f"🚀 {domain_name.upper()} HAS LAUNCHED!")
    print(f"Launched at: {launched_at}")

    return True


def get_leaderboard():
    """
    Get competitive leaderboard of all domains

    Returns:
        list: Domains sorted by signups (descending)
    """
    domains = ['soulfra', 'calriven', 'deathtodata', 'cringeproof']

    leaderboard = []
    for domain in domains:
        info = calculate_launch_date(domain)
        if info:
            leaderboard.append(info)

    # Sort by signups (descending)
    leaderboard.sort(key=lambda x: x['signups'], reverse=True)

    return leaderboard


def display_leaderboard():
    """
    Display leaderboard in console
    """
    leaderboard = get_leaderboard()

    print(f"\n{'='*70}")
    print(f"DOMAIN LAUNCH LEADERBOARD")
    print(f"{'='*70}")
    print(f"{'Rank':<6} {'Domain':<15} {'Signups':<10} {'Days Until':<12} {'Progress':<10}")
    print(f"{'-'*70}")

    for rank, domain in enumerate(leaderboard, 1):
        if domain['is_launched']:
            status = "🚀 LIVE"
        else:
            status = f"{domain['days_until']} days"

        progress = f"{domain['progress_pct']:.1f}%"

        print(f"{rank:<6} {domain['domain_name']:<15} {domain['signups']:<10} {status:<12} {progress:<10}")

    print(f"{'='*70}\n")


def get_letter_allocation(domain_name):
    """
    Get letter allocation for a domain (A-Z, 26 slots)

    Args:
        domain_name (str): Domain name

    Returns:
        dict: Available letters and allocated letters
    """
    db = get_db()

    # Get all allocated letters
    allocated = db.execute('''
        SELECT letter_code FROM waitlist
        WHERE domain_name = ? AND letter_code IS NOT NULL
        ORDER BY signup_at ASC
    ''', (domain_name,)).fetchall()

    allocated_letters = [row['letter_code'] for row in allocated]

    # All possible letters
    all_letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    # Available letters
    available = [l for l in all_letters if l not in allocated_letters]

    return {
        'allocated': allocated_letters,
        'available': available,
        'total_slots': 26,
        'remaining_slots': len(available),
        'is_full': len(available) == 0
    }


def assign_letter_to_signup(waitlist_id):
    """
    Assign next available letter to a waitlist signup

    Args:
        waitlist_id (int): Waitlist entry ID

    Returns:
        str: Assigned letter code or None if full
    """
    db = get_db()

    # Get waitlist entry
    entry = db.execute('SELECT * FROM waitlist WHERE id = ?', (waitlist_id,)).fetchone()
    if not entry:
        return None

    # Get next available letter
    allocation = get_letter_allocation(entry['domain_name'])

    if allocation['is_full']:
        print(f"❌ {entry['domain_name']} is FULL (26/26 letters allocated)")
        return None

    # Assign first available letter
    next_letter = allocation['available'][0]

    db.execute('''
        UPDATE waitlist SET letter_code = ? WHERE id = ?
    ''', (next_letter, waitlist_id))
    db.commit()

    print(f"✅ Assigned letter '{next_letter}' to signup {waitlist_id}")

    return next_letter


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 launch_calculator.py calculate <domain>")
        print("  python3 launch_calculator.py leaderboard")
        print("  python3 launch_calculator.py launch <domain>")
        print("  python3 launch_calculator.py letters <domain>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "calculate":
        if len(sys.argv) < 3:
            print("Usage: python3 launch_calculator.py calculate <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        info = calculate_launch_date(domain)

        if info:
            print(json.dumps(info, indent=2))

    elif command == "leaderboard":
        display_leaderboard()

    elif command == "launch":
        if len(sys.argv) < 3:
            print("Usage: python3 launch_calculator.py launch <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        mark_domain_launched(domain)

    elif command == "letters":
        if len(sys.argv) < 3:
            print("Usage: python3 launch_calculator.py letters <domain>")
            sys.exit(1)

        domain = sys.argv[2]
        allocation = get_letter_allocation(domain)

        print(f"\nLetter Allocation for {domain.upper()}:")
        print(f"Allocated: {', '.join(allocation['allocated']) if allocation['allocated'] else 'None'}")
        print(f"Available: {', '.join(allocation['available'])}")
        print(f"Remaining: {allocation['remaining_slots']}/26")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
