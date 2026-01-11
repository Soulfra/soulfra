#!/usr/bin/env python3
"""
Canvas Integration - The Glue Code

Connects existing systems:
- QR Faucet → Canvas entry
- User Workspace → Chapter system
- API Keys → Feature unlocks
- Brand system → Forkable themes

This is the "Kubernetes for ideas" infrastructure.
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db


# =============================================================================
# CANVAS ENTRY - QR Scan → Workspace
# =============================================================================

def generate_canvas_qr(user_id: Optional[int] = None, ttl_minutes: int = 5) -> Dict:
    """
    Generate QR code for Canvas entry (Netflix-style pairing)

    Args:
        user_id: Specific user (or None for guest)
        ttl_minutes: Token expiration time

    Returns:
        Dict with QR payload and pairing token
    """
    from qr_faucet import generate_qr_payload

    # Create pairing token
    pairing_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)

    # Store pairing session
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS canvas_pairing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pairing_token TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            status TEXT DEFAULT 'pending',
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paired_at TIMESTAMP
        )
    ''')

    db.execute('''
        INSERT INTO canvas_pairing (pairing_token, user_id, expires_at)
        VALUES (?, ?, ?)
    ''', (pairing_token, user_id, expires_at))

    db.commit()
    db.close()

    # Generate QR faucet payload
    payload = generate_qr_payload(
        payload_type='canvas_entry',
        data={'pairing_token': pairing_token},
        ttl_seconds=ttl_minutes * 60
    )

    print(f"✅ Generated Canvas QR")
    print(f"   Token: {pairing_token[:20]}...")
    print(f"   Expires: {expires_at}")

    return {
        'pairing_token': pairing_token,
        'qr_payload': payload,
        'expires_at': expires_at.isoformat()
    }


def verify_canvas_pairing(pairing_token: str) -> Optional[Dict]:
    """
    Verify Canvas pairing token from QR scan

    Returns:
        Pairing session if valid, None otherwise
    """
    db = get_db()

    pairing = db.execute('''
        SELECT * FROM canvas_pairing
        WHERE pairing_token = ? AND status = 'pending'
          AND expires_at > datetime('now')
    ''', (pairing_token,)).fetchone()

    db.close()

    if pairing:
        return dict(pairing)

    return None


def complete_canvas_pairing(pairing_token: str, user_id: int) -> bool:
    """
    Complete pairing (phone scanned → computer logged in)

    Args:
        pairing_token: Token from QR scan
        user_id: User who scanned

    Returns:
        True if successful
    """
    db = get_db()

    db.execute('''
        UPDATE canvas_pairing
        SET status = 'paired', paired_at = datetime('now'), user_id = ?
        WHERE pairing_token = ? AND status = 'pending'
    ''', (user_id, pairing_token))

    rows_updated = db.total_changes
    db.commit()
    db.close()

    return rows_updated > 0


# =============================================================================
# WORKSPACE ← → CHAPTER INTEGRATION
# =============================================================================

def get_canvas_workspace(user_id: int) -> Dict:
    """
    Get workspace data optimized for Canvas view

    Shows:
    - Available chapters to learn
    - Forkable brands
    - Current progress
    - Unlocked features
    - Raw ideas awaiting processing
    """
    from user_workspace import get_workspace_data
    from chapter_version_control import get_chapter_history

    # Get base workspace
    workspace = get_workspace_data(user_id)

    # Get chapter progress
    db = get_db()
    learning_progress = db.execute('''
        SELECT current_chapter, chapters_completed, neural_network_built
        FROM user_learning_progress
        WHERE user_id = ?
    ''', (user_id,)).fetchone()

    if learning_progress:
        workspace['learning'] = dict(learning_progress)
        workspace['learning']['chapters_completed'] = json.loads(
            learning_progress['chapters_completed'] or '[]'
        )
    else:
        workspace['learning'] = {
            'current_chapter': 1,
            'chapters_completed': [],
            'neural_network_built': 0
        }

    # Get forkable brands
    brands = db.execute('''
        SELECT id, slug, name, emoji, tagline, config_json
        FROM brands
        WHERE id IN (1, 2, 3, 4)
    ''').fetchall()

    workspace['forkable_brands'] = [dict(b) for b in brands]

    # Get user's forked chapters
    user_forks = db.execute('''
        SELECT * FROM user_chapter_forks
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    workspace['my_forks'] = [dict(f) for f in user_forks]

    # Get raw ideas (unprocessed)
    raw_ideas = db.execute('''
        SELECT id, idea_text, theme, created_at, status
        FROM ideas
        WHERE submitted_by = (SELECT email FROM users WHERE id = ?)
          AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()

    workspace['raw_ideas'] = [dict(i) for i in raw_ideas]

    db.close()

    return workspace


# =============================================================================
# IDEA PROCESSOR - Raw Input → Structured Content
# =============================================================================

def process_raw_idea(idea_text: str, user_id: int, brand_slug: Optional[str] = None) -> Dict:
    """
    Transform raw idea into structured content

    Pipeline:
    1. Raw text input
    2. AI structures it (using Ollama)
    3. Apply brand theme (CalRiven, DeathToData, etc.)
    4. Save as draft post
    5. Track in version control

    Args:
        idea_text: Raw user input
        user_id: User submitting
        brand_slug: Which brand theme to apply

    Returns:
        Dict with processed post data
    """
    from llm_router import LLMRouter

    router = LLMRouter()

    # Step 1: AI structures the idea
    structuring_prompt = f"""You're helping a user structure their raw idea into a blog post.

Raw idea: {idea_text}

Please output JSON with:
{{
    "title": "catchy title",
    "introduction": "hook paragraph",
    "main_points": ["point 1", "point 2", "point 3"],
    "conclusion": "summary",
    "tags": ["tag1", "tag2"]
}}

Be creative but stay true to the original idea."""

    response = router.generate_text(
        prompt=structuring_prompt,
        persona='calriven',
        max_tokens=500
    )

    # Parse AI response
    try:
        structured = json.loads(response)
    except json.JSONDecodeError:
        # Fallback if AI didn't return valid JSON
        structured = {
            'title': 'Untitled Idea',
            'introduction': idea_text[:200],
            'main_points': [idea_text],
            'conclusion': '',
            'tags': ['ideas']
        }

    # Step 2: Get brand theme (if specified)
    brand_config = {}
    if brand_slug:
        db = get_db()
        brand = db.execute(
            'SELECT * FROM brands WHERE slug = ?',
            (brand_slug,)
        ).fetchone()
        db.close()

        if brand and brand['config_json']:
            try:
                brand_config = json.loads(brand['config_json'])
            except:
                pass

    # Step 3: Create draft post
    db = get_db()

    # Generate slug
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', structured['title'].lower()).strip('-')
    slug = f"{slug}-{secrets.token_hex(4)}"

    # Combine structured parts into content
    content = f"""# {structured['title']}

{structured['introduction']}

## Key Points

"""
    for point in structured['main_points']:
        content += f"- {point}\n"

    content += f"\n## Conclusion\n\n{structured['conclusion']}"

    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO posts
        (user_id, title, content, slug, status, created_at)
        VALUES (?, ?, ?, ?, 'draft', datetime('now'))
    ''', (user_id, structured['title'], content, slug))

    post_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Processed idea into post #{post_id}")
    print(f"   Title: {structured['title']}")
    print(f"   Slug: {slug}")

    return {
        'post_id': post_id,
        'title': structured['title'],
        'slug': slug,
        'content': content,
        'status': 'draft',
        'brand_slug': brand_slug,
        'brand_config': brand_config
    }


# =============================================================================
# API KEY ← → FEATURE UNLOCKS
# =============================================================================

def unlock_feature_for_user(user_id: int, feature_key: str, source: str = 'system') -> int:
    """
    Unlock feature for user (like completing a chapter)

    Features:
    - 'qr_faucet_advanced' - Can create custom QR payloads
    - 'brand_fork' - Can fork brands
    - 'api_access' - Gets API key
    - 'chapter_X_completed' - Completed chapter X
    """
    db = get_db()

    # Check if already unlocked
    existing = db.execute('''
        SELECT id FROM user_unlocks
        WHERE user_id = ? AND feature_key = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))
    ''', (user_id, feature_key)).fetchone()

    if existing:
        db.close()
        return existing['id']

    # Create unlock
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO user_unlocks
        (user_id, feature_key, unlock_source, unlocked_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (user_id, feature_key, source))

    unlock_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"🔓 Unlocked: {feature_key} for user #{user_id}")

    return unlock_id


def check_feature_unlock(user_id: int, feature_key: str) -> bool:
    """Check if user has feature unlocked"""
    db = get_db()

    unlock = db.execute('''
        SELECT id FROM user_unlocks
        WHERE user_id = ? AND feature_key = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))
    ''', (user_id, feature_key)).fetchone()

    db.close()

    return unlock is not None


def generate_api_key_for_user(user_id: int) -> str:
    """
    Generate API key for user (unlocked after completing chapters)

    Returns:
        API key string
    """
    api_key = f"sk_soulfra_{secrets.token_urlsafe(32)}"

    db = get_db()

    # Get user email
    user = db.execute(
        'SELECT email, username FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if not user:
        db.close()
        return None

    # Create API key
    db.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            user_email TEXT NOT NULL,
            tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    db.execute('''
        INSERT INTO api_keys (api_key, user_email, tier)
        VALUES (?, ?, 'free')
    ''', (api_key, user['email']))

    db.commit()
    db.close()

    print(f"🔑 Generated API key for {user['username']}")
    print(f"   Key: {api_key[:30]}...")

    return api_key


# =============================================================================
# BRAND FORK DEPLOYER
# =============================================================================

def fork_brand_for_user(user_id: int, source_brand_slug: str, fork_name: str) -> Dict:
    """
    Fork a brand (like forking CalRiven)

    Creates:
    - New brand record
    - User's custom config
    - Subdomain mapping (future)
    - Version control tracking

    Args:
        user_id: User forking
        source_brand_slug: Brand to fork (calriven, deathtodata, etc.)
        fork_name: Custom name for fork

    Returns:
        Dict with forked brand info
    """
    db = get_db()

    # Get source brand
    source = db.execute(
        'SELECT * FROM brands WHERE slug = ?',
        (source_brand_slug,)
    ).fetchone()

    if not source:
        db.close()
        return {'error': 'Source brand not found'}

    # Create fork slug
    import re
    fork_slug = re.sub(r'[^a-z0-9]+', '-', fork_name.lower()).strip('-')
    fork_slug = f"{fork_slug}-{secrets.token_hex(4)}"

    # Clone brand config
    source_config = json.loads(source['config_json'] or '{}')

    # Insert forked brand
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO brands
        (slug, name, emoji, tagline, config_json, created_by, is_fork, fork_source_id)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        fork_slug,
        fork_name,
        source['emoji'],
        f"{fork_name} (forked from {source['name']})",
        json.dumps(source_config),
        user_id,
        source['id']
    ))

    brand_id = cursor.lastrowid

    db.commit()
    db.close()

    # Unlock brand customization features
    unlock_feature_for_user(user_id, f'brand_fork_{brand_id}', 'brand_fork')

    print(f"🍴 Forked brand: {source['name']} → {fork_name}")
    print(f"   New slug: {fork_slug}")
    print(f"   Brand ID: {brand_id}")

    return {
        'brand_id': brand_id,
        'slug': fork_slug,
        'name': fork_name,
        'source_brand': source['name'],
        'subdomain_url': f"https://{fork_slug}.soulfra.com"  # Future feature
    }


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'canvas-qr':
            result = generate_canvas_qr()
            print(f"\n✅ Canvas QR generated!")
            print(f"   Payload: {result['qr_payload'][:50]}...")
            print(f"   URL: http://localhost:5001/qr/faucet/{result['qr_payload']}")

        elif command == 'process-idea' and len(sys.argv) > 2:
            idea_text = ' '.join(sys.argv[2:])
            result = process_raw_idea(idea_text, user_id=1, brand_slug='calriven')
            print(f"\n✅ Idea processed!")
            print(f"   Post ID: {result['post_id']}")
            print(f"   Title: {result['title']}")

        elif command == 'fork-brand' and len(sys.argv) > 3:
            source_slug = sys.argv[2]
            fork_name = sys.argv[3]
            result = fork_brand_for_user(1, source_slug, fork_name)
            print(f"\n✅ Brand forked!")
            print(f"   New brand: {result['name']}")
            print(f"   Slug: {result['slug']}")

        else:
            print(__doc__)
            print("\nUsage:")
            print("  python canvas_integration.py canvas-qr")
            print("  python canvas_integration.py process-idea 'Your idea here'")
            print("  python canvas_integration.py fork-brand calriven 'My Custom CalRiven'")

    else:
        print(__doc__)
