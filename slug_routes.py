"""
User Slug System - Let users claim their own subdomain/path slugs
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from datetime import datetime
import re
import json

slug_bp = Blueprint('slug', __name__)

def validate_slug(slug):
    """Validate slug format: lowercase letters, numbers, hyphens only"""
    if not slug:
        return False, "Slug cannot be empty"

    if len(slug) < 3:
        return False, "Slug must be at least 3 characters"

    if len(slug) > 32:
        return False, "Slug must be 32 characters or less"

    # Only lowercase letters, numbers, hyphens
    if not re.match(r'^[a-z0-9-]+$', slug):
        return False, "Slug can only contain lowercase letters, numbers, and hyphens"

    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False, "Slug cannot start or end with a hyphen"

    # Reserved slugs (protect important routes)
    reserved = [
        'api', 'admin', 'auth', 'login', 'logout', 'register', 'signup',
        'static', 'assets', 'css', 'js', 'img', 'images',
        'cringeproof', 'soulfra', 'calriven', 'deathtodata',  # Founder domains
        'www', 'blog', 'docs', 'help', 'support', 'contact',
        'dashboard', 'profile', 'settings', 'account'
    ]

    if slug in reserved:
        return False, f"Slug '{slug}' is reserved"

    return True, "Valid"

@slug_bp.route('/api/claim-slug', methods=['POST'])
def claim_slug():
    """
    Let users claim a slug for their personal page

    POST /api/claim-slug
    {
        "user_id": 123,
        "slug": "alice"
    }

    Returns:
    {
        "success": true,
        "slug": "alice",
        "url": "https://cringeproof.com/alice"
    }
    """
    data = request.get_json()

    user_id = data.get('user_id')
    slug = data.get('slug', '').lower().strip()

    if not user_id:
        return jsonify({'success': False, 'error': 'user_id required'}), 400

    # Validate slug format
    valid, message = validate_slug(slug)
    if not valid:
        return jsonify({'success': False, 'error': message}), 400

    db = get_db()

    # Check if user exists
    user = db.execute('SELECT id, user_slug FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Check if slug is already taken
    existing = db.execute('SELECT id, username FROM users WHERE user_slug = ?', (slug,)).fetchone()
    if existing:
        return jsonify({
            'success': False,
            'error': f"Slug '{slug}' is already taken by {existing['username']}"
        }), 409

    # Claim the slug
    db.execute('UPDATE users SET user_slug = ? WHERE id = ?', (slug, user_id))
    db.commit()

    return jsonify({
        'success': True,
        'slug': slug,
        'url': f'https://cringeproof.com/{slug}',
        'message': f'Successfully claimed slug: {slug}'
    })

@slug_bp.route('/api/check-slug', methods=['GET'])
def check_slug():
    """
    Check if a slug is available

    GET /api/check-slug?slug=alice

    Returns:
    {
        "available": false,
        "reason": "Already taken by alice_smith"
    }
    """
    slug = request.args.get('slug', '').lower().strip()

    # Validate format
    valid, message = validate_slug(slug)
    if not valid:
        return jsonify({'available': False, 'reason': message})

    db = get_db()
    existing = db.execute('SELECT username FROM users WHERE user_slug = ?', (slug,)).fetchone()

    if existing:
        return jsonify({
            'available': False,
            'reason': f"Already taken by {existing['username']}"
        })

    return jsonify({'available': True, 'reason': 'Available'})

@slug_bp.route('/api/my-slug', methods=['GET'])
def get_my_slug():
    """
    Get current user's claimed slug

    GET /api/my-slug?user_id=123

    Returns:
    {
        "slug": "alice",
        "url": "https://cringeproof.com/alice"
    }
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    db = get_db()
    user = db.execute('SELECT user_slug FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user['user_slug']:
        return jsonify({'slug': None, 'claimed': False})

    return jsonify({
        'slug': user['user_slug'],
        'url': f'https://cringeproof.com/{user["user_slug"]}',
        'claimed': True
    })

@slug_bp.route('/api/auth/link-provider', methods=['POST'])
def link_auth_provider():
    """
    Link an auth provider (GitHub, phone, email) to a user slug

    POST /api/auth/link-provider
    {
        "user_id": 123,
        "provider": "github",
        "provider_username": "soulfra",
        "provider_email": "matt@example.com"
    }
    """
    data = request.get_json()

    user_id = data.get('user_id')
    provider = data.get('provider')
    provider_username = data.get('provider_username')
    provider_email = data.get('provider_email')

    if not user_id or not provider:
        return jsonify({'success': False, 'error': 'user_id and provider required'}), 400

    db = get_db()

    # Verify user exists
    user = db.execute('SELECT id, user_slug FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Check if provider already linked to different user
    existing = db.execute('''
        SELECT user_id FROM auth_providers
        WHERE provider = ? AND provider_username = ?
    ''', (provider, provider_username)).fetchone()

    if existing and existing['user_id'] != user_id:
        return jsonify({
            'success': False,
            'error': f'{provider} account already linked to another user'
        }), 409

    # Insert or update auth provider
    db.execute('''
        INSERT OR REPLACE INTO auth_providers
        (user_id, provider, provider_username, provider_email, verified_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, provider, provider_username, provider_email, datetime.now()))
    db.commit()

    return jsonify({
        'success': True,
        'message': f'{provider} linked successfully',
        'user_slug': user['user_slug']
    })

@slug_bp.route('/api/auth/recover', methods=['GET'])
def recover_account():
    """
    Find user slug by auth provider

    GET /api/auth/recover?provider=github&username=soulfra

    Returns user's slug if found
    """
    provider = request.args.get('provider')
    username = request.args.get('username')

    if not provider or not username:
        return jsonify({'success': False, 'error': 'provider and username required'}), 400

    db = get_db()

    # Find user by auth provider
    result = db.execute('''
        SELECT u.id, u.username, u.user_slug, u.email,
               ap.provider_email, ap.verified_at
        FROM auth_providers ap
        JOIN users u ON ap.user_id = u.id
        WHERE ap.provider = ? AND ap.provider_username = ?
    ''', (provider, username)).fetchone()

    if not result:
        return jsonify({
            'success': False,
            'error': f'No account found for {provider} user {username}'
        }), 404

    # Update last login
    db.execute('''
        UPDATE auth_providers
        SET last_login_at = ?
        WHERE provider = ? AND provider_username = ?
    ''', (datetime.now(), provider, username))
    db.commit()

    return jsonify({
        'success': True,
        'user_id': result['id'],
        'username': result['username'],
        'slug': result['user_slug'],
        'url': f'https://cringeproof.com/{result["user_slug"]}',
        'email': result['email'],
        'provider': provider,
        'provider_username': username,
        'linked_at': result['verified_at']
    })

@slug_bp.route('/api/auth/providers', methods=['GET'])
def get_auth_providers():
    """
    Get all auth providers linked to current user

    GET /api/auth/providers?user_id=123

    Returns list of linked providers (GitHub, phone, email, etc.)
    """
    user_id = request.args.get('user_id') or session.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id required or login required'}), 400

    db = get_db()

    providers = db.execute('''
        SELECT provider, provider_username, provider_email,
               verified_at, last_login_at
        FROM auth_providers
        WHERE user_id = ?
        ORDER BY verified_at DESC
    ''', (user_id,)).fetchall()

    return jsonify({
        'success': True,
        'providers': [dict(p) for p in providers]
    })
