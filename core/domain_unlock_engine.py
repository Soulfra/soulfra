#!/usr/bin/env python3
"""
Domain Unlock Engine - Fractionalized Ownership System

Gamified domain progression where users unlock domains through contributions:
- Answer 10 questions → Unlock random domain
- Post 5 ideas → Unlock domain matching theme
- Record 3 voice memos → Unlock domain from daily rotation
- Idea reaches 80+ score → Unlock premium domain

Ownership increases with continued engagement:
- Each contribution → +0.5% ownership
- High-quality ideas → +2% ownership
- Consistent engagement → bonus multipliers

Day-based rotation themes:
- Monday: Privacy (deathtodata.com, niceleak.com)
- Tuesday: Cooking (howtocookathome.com)
- Wednesday: Tech (calriven.com)
- Thursday: Creative (oofbox.com, hollowtown.com)
- Friday: Mixed/Random
- Weekend: Soulfra + user's top domains
"""

from database import get_db
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import random


# Day-of-week theme mapping
DAY_THEMES = {
    0: 'privacy',      # Monday
    1: 'cooking',      # Tuesday
    2: 'tech',         # Wednesday
    3: 'creative',     # Thursday
    4: 'mixed',        # Friday
    5: 'user_top',     # Saturday
    6: 'user_top'      # Sunday
}

# Domain categories (expand based on domains-simple.txt)
DOMAIN_CATEGORIES = {
    'privacy': ['deathtodata.com', 'niceleak.com'],
    'cooking': ['howtocookathome.com'],
    'tech': ['calriven.com'],
    'creative': ['oofbox.com', 'hollowtown.com'],
    'home': ['soulfra.com']  # Always accessible
}

# Unlock thresholds
UNLOCK_THRESHOLDS = {
    'questions_answered': 10,
    'ideas_posted': 5,
    'voice_memos': 3,
    'high_score_idea': 80
}


def ensure_default_domain(user_id: int) -> None:
    """
    Ensure user has soulfra.com (home domain) unlocked and set as primary

    Args:
        user_id: User ID
    """
    db = get_db()

    # Get soulfra domain_id
    soulfra = db.execute('''
        SELECT id FROM domain_contexts
        WHERE domain = 'soulfra.com' OR domain_slug = 'soulfra'
        LIMIT 1
    ''').fetchone()

    if not soulfra:
        # Create soulfra domain context if doesn't exist
        cursor = db.execute('''
            INSERT INTO domain_contexts (domain_slug, context_type, content, domain)
            VALUES ('soulfra', 'domain', 'soulfra.com', 'soulfra.com')
        ''')
        soulfra_id = cursor.lastrowid
    else:
        soulfra_id = soulfra['id']

    # Check if user already owns soulfra
    existing = db.execute('''
        SELECT id FROM domain_ownership
        WHERE user_id = ? AND domain_id = ?
    ''', (user_id, soulfra_id)).fetchone()

    if not existing:
        # Grant default ownership and set as primary
        db.execute('''
            INSERT INTO domain_ownership (user_id, domain_id, ownership_percentage, unlock_source, is_primary)
            VALUES (?, ?, 5.0, 'default', 1)
        ''', (user_id, soulfra_id))

        # Update users table with primary domain
        db.execute('''
            UPDATE users
            SET primary_domain_id = ?
            WHERE id = ?
        ''', (soulfra_id, user_id))

        db.commit()

    db.close()


def get_user_domains(user_id: int) -> List[Dict]:
    """
    Get all domains owned by user

    Args:
        user_id: User ID

    Returns:
        List of domain dicts with ownership info
    """
    ensure_default_domain(user_id)

    db = get_db()

    domains = db.execute('''
        SELECT
            do.id,
            do.domain_id,
            dc.domain,
            dc.domain_slug,
            do.ownership_percentage,
            do.unlock_date,
            do.contribution_score,
            do.unlock_source
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE do.user_id = ?
        ORDER BY do.ownership_percentage DESC, do.unlock_date ASC
    ''', (user_id,)).fetchall()

    db.close()

    return [dict(d) for d in domains]


def get_daily_rotation_pool() -> List[str]:
    """
    Get today's themed domain pool based on day of week

    Returns:
        List of domain slugs for today
    """
    today = datetime.now().weekday()
    theme = DAY_THEMES.get(today, 'mixed')

    if theme == 'mixed':
        # Friday - random mix
        all_domains = []
        for domains in DOMAIN_CATEGORIES.values():
            all_domains.extend(domains)
        return random.sample(all_domains, min(3, len(all_domains)))
    elif theme == 'user_top':
        # Weekend - returns empty, will use user's top domains
        return []
    else:
        return DOMAIN_CATEGORIES.get(theme, ['soulfra.com'])


def check_unlock_eligibility(user_id: int) -> Dict:
    """
    Check if user is eligible to unlock new domains

    Args:
        user_id: User ID

    Returns:
        Dict with eligibility status and available unlocks
    """
    db = get_db()

    # Count questions answered
    questions = db.execute('''
        SELECT COUNT(*) as count FROM user_question_answers
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    questions_count = questions['count'] if questions else 0

    # Count ideas posted
    ideas = db.execute('''
        SELECT COUNT(*) as count FROM voice_ideas
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    ideas_count = ideas['count'] if ideas else 0

    # Count voice recordings
    recordings = db.execute('''
        SELECT COUNT(*) as count FROM simple_voice_recordings
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    recordings_count = recordings['count'] if recordings else 0

    # Count high-score ideas
    high_score = db.execute('''
        SELECT COUNT(*) as count FROM voice_ideas
        WHERE user_id = ? AND score >= ?
    ''', (user_id, UNLOCK_THRESHOLDS['high_score_idea'])).fetchone()
    high_score_count = high_score['count'] if high_score else 0

    # Count currently owned domains
    owned_count = db.execute('''
        SELECT COUNT(*) as count FROM domain_ownership
        WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    db.close()

    # Calculate how many domains user can unlock
    unlocks_available = 0
    unlock_reasons = []

    if questions_count >= UNLOCK_THRESHOLDS['questions_answered']:
        unlocks_available += questions_count // UNLOCK_THRESHOLDS['questions_answered']
        unlock_reasons.append(f"questions ({questions_count}/{UNLOCK_THRESHOLDS['questions_answered']})")

    if ideas_count >= UNLOCK_THRESHOLDS['ideas_posted']:
        unlocks_available += ideas_count // UNLOCK_THRESHOLDS['ideas_posted']
        unlock_reasons.append(f"ideas ({ideas_count}/{UNLOCK_THRESHOLDS['ideas_posted']})")

    if recordings_count >= UNLOCK_THRESHOLDS['voice_memos']:
        unlocks_available += recordings_count // UNLOCK_THRESHOLDS['voice_memos']
        unlock_reasons.append(f"recordings ({recordings_count}/{UNLOCK_THRESHOLDS['voice_memos']})")

    if high_score_count > 0:
        unlocks_available += high_score_count
        unlock_reasons.append(f"high-score ideas ({high_score_count})")

    # Subtract already owned domains
    unlocks_available -= owned_count
    unlocks_available = max(0, unlocks_available)

    return {
        'can_unlock': unlocks_available > 0,
        'unlocks_available': unlocks_available,
        'owned_count': owned_count,
        'stats': {
            'questions': questions_count,
            'ideas': ideas_count,
            'recordings': recordings_count,
            'high_score': high_score_count
        },
        'reasons': unlock_reasons,
        'next_threshold': {
            'questions': UNLOCK_THRESHOLDS['questions_answered'] - (questions_count % UNLOCK_THRESHOLDS['questions_answered']),
            'ideas': UNLOCK_THRESHOLDS['ideas_posted'] - (ideas_count % UNLOCK_THRESHOLDS['ideas_posted']),
            'recordings': UNLOCK_THRESHOLDS['voice_memos'] - (recordings_count % UNLOCK_THRESHOLDS['voice_memos'])
        }
    }


def unlock_domain(user_id: int, domain: str, source: str = 'manual') -> bool:
    """
    Unlock a domain for user

    Args:
        user_id: User ID
        domain: Domain name (e.g., 'deathtodata.com')
        source: How domain was unlocked ('questions', 'ideas', 'voice', 'manual')

    Returns:
        True if unlocked successfully
    """
    db = get_db()

    # Get or create domain_context
    domain_ctx = db.execute('''
        SELECT id FROM domain_contexts
        WHERE domain = ? OR domain_slug = ?
        LIMIT 1
    ''', (domain, domain.split('.')[0])).fetchone()

    if not domain_ctx:
        # Create domain context
        cursor = db.execute('''
            INSERT INTO domain_contexts (domain_slug, context_type, content, domain)
            VALUES (?, 'domain', ?, ?)
        ''', (domain.split('.')[0], domain, domain))
        domain_id = cursor.lastrowid
    else:
        domain_id = domain_ctx['id']

    # Check if already owned
    existing = db.execute('''
        SELECT id FROM domain_ownership
        WHERE user_id = ? AND domain_id = ?
    ''', (user_id, domain_id)).fetchone()

    if existing:
        db.close()
        return False  # Already owned

    # Grant ownership
    db.execute('''
        INSERT INTO domain_ownership (user_id, domain_id, ownership_percentage, unlock_source)
        VALUES (?, ?, 1.0, ?)
    ''', (user_id, domain_id, source))

    db.commit()
    db.close()

    print(f"✅ User {user_id} unlocked {domain} (source: {source})")
    return True


def increase_ownership(user_id: int, domain: str, amount: float = 0.5) -> bool:
    """
    Increase user's ownership percentage of a domain

    Args:
        user_id: User ID
        domain: Domain name
        amount: Percentage increase (default: 0.5%)

    Returns:
        True if increased successfully
    """
    db = get_db()

    # Get domain_id
    domain_ctx = db.execute('''
        SELECT id FROM domain_contexts
        WHERE domain = ? OR domain_slug = ?
        LIMIT 1
    ''', (domain, domain.split('.')[0])).fetchone()

    if not domain_ctx:
        db.close()
        return False

    domain_id = domain_ctx['id']

    # Update ownership
    db.execute('''
        UPDATE domain_ownership
        SET ownership_percentage = MIN(100.0, ownership_percentage + ?),
            contribution_score = contribution_score + 1,
            last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ? AND domain_id = ?
    ''', (amount, user_id, domain_id))

    db.commit()
    db.close()

    return True


def auto_unlock_next_domain(user_id: int, source: str = 'auto') -> Optional[str]:
    """
    Automatically unlock next domain for user based on eligibility

    Args:
        user_id: User ID
        source: Unlock source

    Returns:
        Domain name if unlocked, None otherwise
    """
    eligibility = check_unlock_eligibility(user_id)

    if not eligibility['can_unlock']:
        return None

    # Get today's rotation pool
    rotation_pool = get_daily_rotation_pool()

    # Get already owned domains
    owned = get_user_domains(user_id)
    owned_domains = [d['domain'] for d in owned]

    # Filter out owned domains
    available = [d for d in rotation_pool if d not in owned_domains]

    if not available:
        # Fall back to any domain from all categories
        all_domains = []
        for domains in DOMAIN_CATEGORIES.values():
            all_domains.extend(domains)
        available = [d for d in all_domains if d not in owned_domains]

    if not available:
        return None  # All domains owned!

    # Pick random domain
    next_domain = random.choice(available)

    # Unlock it
    if unlock_domain(user_id, next_domain, source):
        return next_domain

    return None


def get_primary_domain(user_id: int) -> Optional[Dict]:
    """
    Get user's primary domain (handle)

    Args:
        user_id: User ID

    Returns:
        Dict with domain info or None if no primary domain set
    """
    db = get_db()

    primary = db.execute('''
        SELECT
            do.domain_id,
            dc.domain,
            dc.domain_slug,
            do.ownership_percentage,
            dc.tier,
            dc.prestige_multiplier
        FROM domain_ownership do
        JOIN domain_contexts dc ON do.domain_id = dc.id
        WHERE do.user_id = ? AND do.is_primary = 1
        LIMIT 1
    ''', (user_id,)).fetchone()

    db.close()

    return dict(primary) if primary else None


def set_primary_domain(user_id: int, domain: str) -> bool:
    """
    Set user's primary domain (handle)

    Args:
        user_id: User ID
        domain: Domain name (e.g., 'soulfra.com')

    Returns:
        True if set successfully
    """
    db = get_db()

    # Get domain_id
    domain_ctx = db.execute('''
        SELECT id FROM domain_contexts
        WHERE domain = ? OR domain_slug = ?
        LIMIT 1
    ''', (domain, domain.split('.')[0])).fetchone()

    if not domain_ctx:
        db.close()
        return False

    domain_id = domain_ctx['id']

    # Check if user owns this domain
    ownership = db.execute('''
        SELECT id FROM domain_ownership
        WHERE user_id = ? AND domain_id = ?
    ''', (user_id, domain_id)).fetchone()

    if not ownership:
        db.close()
        return False  # User doesn't own this domain

    # Unset current primary
    db.execute('''
        UPDATE domain_ownership
        SET is_primary = 0
        WHERE user_id = ?
    ''', (user_id,))

    # Set new primary
    db.execute('''
        UPDATE domain_ownership
        SET is_primary = 1
        WHERE user_id = ? AND domain_id = ?
    ''', (user_id, domain_id))

    # Update users table
    db.execute('''
        UPDATE users
        SET primary_domain_id = ?
        WHERE id = ?
    ''', (domain_id, user_id))

    db.commit()
    db.close()

    print(f"✅ User {user_id} set primary domain to {domain}")
    return True


def get_user_handle(user_id: int) -> str:
    """
    Get user's handle (formatted as @domain)

    Args:
        user_id: User ID

    Returns:
        Handle string (e.g., '@soulfra') or '@user{id}' if no primary domain
    """
    primary = get_primary_domain(user_id)

    if primary:
        return f"@{primary['domain_slug']}"
    else:
        return f"@user{user_id}"


def get_domain_leaderboard(domain: str, limit: int = 10) -> List[Dict]:
    """
    Get top owners of a domain

    Args:
        domain: Domain name
        limit: Number of owners to return

    Returns:
        List of dicts with user_id, ownership_percentage, contribution_score
    """
    db = get_db()

    # Get domain_id
    domain_ctx = db.execute('''
        SELECT id FROM domain_contexts
        WHERE domain = ? OR domain_slug = ?
        LIMIT 1
    ''', (domain, domain.split('.')[0])).fetchone()

    if not domain_ctx:
        db.close()
        return []

    domain_id = domain_ctx['id']

    # Get top owners
    owners = db.execute('''
        SELECT
            do.user_id,
            do.ownership_percentage,
            do.contribution_score,
            do.unlock_date,
            do.last_contribution_date,
            u.username
        FROM domain_ownership do
        JOIN users u ON do.user_id = u.id
        WHERE do.domain_id = ?
        ORDER BY do.ownership_percentage DESC, do.contribution_score DESC
        LIMIT ?
    ''', (domain_id, limit)).fetchall()

    db.close()

    return [dict(o) for o in owners]


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])

        print(f"\n{'='*60}")
        print(f"DOMAIN OWNERSHIP - User #{user_id}")
        print(f"{'='*60}\n")

        # Check eligibility
        eligibility = check_unlock_eligibility(user_id)

        print(f"📊 Stats:")
        for key, value in eligibility['stats'].items():
            print(f"   • {key}: {value}")

        print(f"\n🏆 Ownership:")
        print(f"   Domains owned: {eligibility['owned_count']}")
        print(f"   Can unlock: {eligibility['unlocks_available']} more")

        if eligibility['reasons']:
            print(f"\n   Earned through: {', '.join(eligibility['reasons'])}")

        print(f"\n📍 Next Unlock:")
        for key, remaining in eligibility['next_threshold'].items():
            print(f"   • {remaining} more {key}")

        # Show owned domains
        domains = get_user_domains(user_id)
        if domains:
            print(f"\n💎 Your Domains:")
            for d in domains:
                print(f"   • {d['domain']}: {d['ownership_percentage']:.1f}% (unlocked: {d['unlock_date']})")

        # Show today's rotation
        rotation = get_daily_rotation_pool()
        if rotation:
            print(f"\n🔄 Today's Rotation ({datetime.now().strftime('%A')}):")
            for domain in rotation:
                print(f"   → {domain}")

        print()
    else:
        print("Usage: python3 domain_unlock_engine.py <user_id>")
        print("\nDaily Rotation Themes:")
        for day, theme in DAY_THEMES.items():
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
            print(f"   {day_name}: {theme}")
