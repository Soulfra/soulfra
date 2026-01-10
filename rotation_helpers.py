#!/usr/bin/env python3
"""
Rotation Helpers

Functions for domain context rotation (questions, themes, profiles)
and template version management.

Each domain has rotating contexts that cycle periodically:
- Questions: "What would you build if you had unlimited time?"
- Themes: ocean, sunset, starlight
- Profiles: personality/context configurations

Template versions follow ship tier progression:
- v1_dinghy: ~26 lines, minimal
- v2_schooner: 50-80 lines, enhanced
- v3_frigate: 120-180 lines, advanced
- v4_galleon: 250+ lines, complete
"""

from datetime import datetime, timedelta
from database import get_db


def get_domain_slug_from_brand(brand):
    """
    Extract domain slug from brand object

    Args:
        brand: Brand dict from subdomain router

    Returns:
        Domain slug string (e.g., 'ocean-dreams', 'cringeproof')
    """
    if not brand:
        return 'soulfra'  # Default domain

    return brand.get('slug', 'soulfra')


def get_rotation_context(domain_slug, context_type='question'):
    """
    Get current rotation context for a domain

    Args:
        domain_slug: Domain identifier (e.g., 'ocean-dreams', 'cringeproof')
        context_type: Type of context ('question', 'theme', 'profile')

    Returns:
        Context string or None
    """
    db = get_db()

    # Get rotation state
    state_row = db.execute('''
        SELECT current_question_index, current_theme_index, current_profile_index,
               last_rotated_at, rotation_interval_hours
        FROM domain_rotation_state
        WHERE domain_slug = ?
    ''', (domain_slug,)).fetchone()

    if not state_row:
        return None

    state = dict(state_row)

    # Determine which index to use based on context_type
    index_map = {
        'question': 'current_question_index',
        'theme': 'current_theme_index',
        'profile': 'current_profile_index'
    }

    current_index = state.get(index_map.get(context_type, 'current_question_index'), 0)

    # Get the context at current rotation order
    context_row = db.execute('''
        SELECT content, metadata
        FROM domain_contexts
        WHERE domain_slug = ?
          AND context_type = ?
          AND rotation_order = ?
          AND active = 1
    ''', (domain_slug, context_type, current_index)).fetchone()

    if not context_row:
        # No context at current index, get first available
        context_row = db.execute('''
            SELECT content, metadata
            FROM domain_contexts
            WHERE domain_slug = ?
              AND context_type = ?
              AND active = 1
            ORDER BY rotation_order
            LIMIT 1
        ''', (domain_slug, context_type)).fetchone()

    if not context_row:
        return None

    return dict(context_row)['content']


def rotate_context(domain_slug, force=False):
    """
    Rotate to next context in rotation cycle

    Args:
        domain_slug: Domain identifier
        force: Force rotation even if interval hasn't passed

    Returns:
        True if rotated, False if not time yet
    """
    db = get_db()

    # Get rotation state
    state_row = db.execute('''
        SELECT current_question_index, current_theme_index, current_profile_index,
               last_rotated_at, rotation_interval_hours
        FROM domain_rotation_state
        WHERE domain_slug = ?
    ''', (domain_slug,)).fetchone()

    if not state_row:
        return False

    state = dict(state_row)

    # Check if rotation interval has passed
    last_rotated = datetime.fromisoformat(state['last_rotated_at'])
    interval_hours = state['rotation_interval_hours']
    next_rotation = last_rotated + timedelta(hours=interval_hours)

    if not force and datetime.now() < next_rotation:
        return False  # Not time to rotate yet

    # Get max rotation orders for each context type
    question_count = db.execute('''
        SELECT COUNT(*) as count FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'question' AND active = 1
    ''', (domain_slug,)).fetchone()['count']

    theme_count = db.execute('''
        SELECT COUNT(*) as count FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'theme' AND active = 1
    ''', (domain_slug,)).fetchone()['count']

    profile_count = db.execute('''
        SELECT COUNT(*) as count FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'profile' AND active = 1
    ''', (domain_slug,)).fetchone()['count']

    # Rotate to next index (wrap around)
    new_question_idx = (state['current_question_index'] + 1) % max(question_count, 1)
    new_theme_idx = (state['current_theme_index'] + 1) % max(theme_count, 1)
    new_profile_idx = (state['current_profile_index'] + 1) % max(profile_count, 1)

    # Update rotation state
    db.execute('''
        UPDATE domain_rotation_state
        SET current_question_index = ?,
            current_theme_index = ?,
            current_profile_index = ?,
            last_rotated_at = ?
        WHERE domain_slug = ?
    ''', (new_question_idx, new_theme_idx, new_profile_idx,
          datetime.now().isoformat(), domain_slug))

    db.commit()

    return True


def get_template_version(template_name, version_number=None, ship_class=None):
    """
    Get template version information

    Args:
        template_name: Template name (e.g., 'signup', 'leaderboard')
        version_number: Specific version (e.g., 'v1', 'v2') or None for active
        ship_class: Ship class filter (e.g., 'dinghy', 'schooner')

    Returns:
        Template version dict or None
    """
    db = get_db()

    if version_number:
        # Get specific version
        version_row = db.execute('''
            SELECT id, template_name, version_number, ship_class, file_path,
                   changelog, line_count, active, created_at
            FROM template_versions
            WHERE template_name = ? AND version_number = ?
        ''', (template_name, version_number)).fetchone()
    elif ship_class:
        # Get latest of ship class
        version_row = db.execute('''
            SELECT id, template_name, version_number, ship_class, file_path,
                   changelog, line_count, active, created_at
            FROM template_versions
            WHERE template_name = ? AND ship_class = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (template_name, ship_class)).fetchone()
    else:
        # Get active version
        version_row = db.execute('''
            SELECT id, template_name, version_number, ship_class, file_path,
                   changelog, line_count, active, created_at
            FROM template_versions
            WHERE template_name = ? AND active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''', (template_name,)).fetchone()

    if not version_row:
        return None

    return dict(version_row)


def inject_rotation_context(brand):
    """
    Get rotation context to inject into template

    Args:
        brand: Brand dict from subdomain router

    Returns:
        Dict with rotation context variables
    """
    domain_slug = get_domain_slug_from_brand(brand)

    # Get current rotation contexts
    question = get_rotation_context(domain_slug, 'question')
    theme = get_rotation_context(domain_slug, 'theme')
    profile = get_rotation_context(domain_slug, 'profile')

    # Get brand/domain info
    domain_name = brand['name'] if brand else 'Soulfra'
    domain_emoji = brand.get('emoji', '🌊') if brand else '🌊'

    # Get brand colors for theming
    if brand and brand.get('colors_list'):
        colors = list(brand['colors_list'])  # Ensure it's a list, not dict_items
        theme_primary = colors[0] if len(colors) > 0 else '#667eea'
        theme_secondary = colors[1] if len(colors) > 1 else '#764ba2'
        theme_accent = colors[2] if len(colors) > 2 else theme_secondary
        theme_background = '#f8f9fa'
        theme_text = '#333333'
    else:
        # Default theme
        theme_primary = '#667eea'
        theme_secondary = '#764ba2'
        theme_accent = '#764ba2'
        theme_background = '#f8f9fa'
        theme_text = '#333333'

    return {
        'domain_slug': domain_slug,
        'domain_name': domain_name,
        'domain_emoji': domain_emoji,
        'domain_question': question,
        'domain_theme': theme,
        'domain_profile': profile,
        'theme_primary': theme_primary,
        'theme_secondary': theme_secondary,
        'theme_accent': theme_accent,
        'theme_background': theme_background,
        'theme_text': theme_text
    }


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("\n🧪 Testing Rotation Helpers\n")

    # Test getting rotation context
    print("Test 1: Get Rotation Context")
    domain = 'ocean-dreams'
    question = get_rotation_context(domain, 'question')
    theme = get_rotation_context(domain, 'theme')

    print(f"  Domain: {domain}")
    print(f"  Question: {question}")
    print(f"  Theme: {theme}")

    # Test template version lookup
    print("\nTest 2: Get Template Version")
    version = get_template_version('signup', version_number='v1')

    if version:
        print(f"  Template: {version['template_name']}")
        print(f"  Version: {version['version_number']}")
        print(f"  Ship Class: {version['ship_class']}")
        print(f"  File: {version['file_path']}")
        print(f"  Lines: {version['line_count']}")

    # Test rotation
    print("\nTest 3: Rotate Context")
    rotated = rotate_context(domain, force=True)

    if rotated:
        print(f"  ✅ Rotated {domain}")
        new_question = get_rotation_context(domain, 'question')
        print(f"  New question: {new_question}")
    else:
        print(f"  ⏭️  Not time to rotate yet")

    print("\n✅ Rotation helpers tests complete!\n")
