#!/usr/bin/env python3
"""
Test Handle/Primary Domain System

Demonstrates:
- Getting user handle (@soulfra, @calriven, etc.)
- Setting primary domain
- Domain leaderboards
"""

from domain_unlock_engine import (
    ensure_default_domain,
    get_user_handle,
    get_primary_domain,
    set_primary_domain,
    unlock_domain,
    get_domain_leaderboard
)
from database import get_db


def test_user_handles(user_id: int = 1):
    """Test handle system for a user"""

    print(f"\n{'='*60}")
    print(f"TESTING HANDLE SYSTEM - User #{user_id}")
    print(f"{'='*60}\n")

    # Ensure default domain
    ensure_default_domain(user_id)
    print(f"✅ Ensured default domain (soulfra.com)")

    # Get handle
    handle = get_user_handle(user_id)
    print(f"📛 Current handle: {handle}")

    # Get primary domain details
    primary = get_primary_domain(user_id)
    if primary:
        print(f"   Domain: {primary['domain']}")
        print(f"   Tier: {primary['tier']}")
        print(f"   Ownership: {primary['ownership_percentage']:.1f}%")
        print(f"   Prestige: {primary['prestige_multiplier']}x")

    # Unlock another domain
    print(f"\n🔓 Unlocking calriven.com for user...")
    unlock_domain(user_id, 'calriven.com', 'test')

    # Switch primary domain
    print(f"\n🔄 Switching primary domain to calriven.com...")
    set_primary_domain(user_id, 'calriven.com')

    # Get new handle
    new_handle = get_user_handle(user_id)
    print(f"📛 New handle: {new_handle}")

    # Get primary domain details
    primary = get_primary_domain(user_id)
    if primary:
        print(f"   Domain: {primary['domain']}")
        print(f"   Tier: {primary['tier']}")
        print(f"   Ownership: {primary['ownership_percentage']:.1f}%")
        print(f"   Prestige: {primary['prestige_multiplier']}x")

    print()


def show_domain_leaderboard(domain: str = 'soulfra.com'):
    """Show leaderboard for a domain"""

    print(f"\n{'='*60}")
    print(f"LEADERBOARD - {domain}")
    print(f"{'='*60}\n")

    owners = get_domain_leaderboard(domain, limit=10)

    if not owners:
        print("No owners yet!")
        return

    for i, owner in enumerate(owners, 1):
        rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f"{i}.")
        print(f"{rank_emoji} {owner.get('username', f'User #{owner['user_id']}')} - {owner['ownership_percentage']:.1f}%")
        print(f"   Contributions: {owner['contribution_score']} | Unlocked: {owner['unlock_date']}")

    print()


def show_all_users_with_handles():
    """Show all users with their handles"""

    print(f"\n{'='*60}")
    print(f"ALL USER HANDLES")
    print(f"{'='*60}\n")

    db = get_db()

    users = db.execute('''
        SELECT id, username FROM users
        ORDER BY id
        LIMIT 20
    ''').fetchall()

    for user in users:
        handle = get_user_handle(user['id'])
        primary = get_primary_domain(user['id'])

        if primary:
            tier_emoji = {'legendary': '🟡', 'epic': '🟠', 'rare': '🟣', 'uncommon': '🔵', 'common': '🟢'}.get(primary['tier'], '⚪')
            print(f"{tier_emoji} {handle} ({user.get('username', f'User {user['id']}')})")
            print(f"   {primary['domain']} - {primary['ownership_percentage']:.1f}% ownership")
        else:
            print(f"⚪ {handle} ({user.get('username', f'User {user['id']}')})")
            print(f"   No domains unlocked")
        print()

    db.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'test':
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            test_user_handles(user_id)
        elif command == 'leaderboard':
            domain = sys.argv[2] if len(sys.argv) > 2 else 'soulfra.com'
            show_domain_leaderboard(domain)
        elif command == 'all':
            show_all_users_with_handles()
    else:
        print("Usage:")
        print("  python3 test_handle_system.py test [user_id]      # Test handle system for user")
        print("  python3 test_handle_system.py leaderboard [domain] # Show domain leaderboard")
        print("  python3 test_handle_system.py all                  # Show all users with handles")
