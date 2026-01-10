"""
Domain API Routes for Soulfra
Provides endpoints for:
- /api/domains/add - Add custom domain
- /api/domains/connections - Get email web connections
- /api/domains/assign - Assign subdomain to user
- /api/domains/brand - Detect brand from domain
"""

from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime, timezone
import hashlib

domain_api_bp = Blueprint('domain_api', __name__, url_prefix='/api/domains')

# Brand mappings for domain detection
BRAND_MAP = {
    'cringeproof': 'call_out_cringe',
    'calriven': 'federated_publishing',
    'deathtodata': 'privacy_focused',
    'soulfra': 'hub',
}

def detect_brand(domain):
    """Detect brand/theme from domain name"""
    domain_lower = domain.lower()

    for brand_domain, brand_name in BRAND_MAP.items():
        if brand_domain in domain_lower:
            return brand_name

    # Default fallback
    return 'personal_blog'


@domain_api_bp.route('/add', methods=['POST', 'OPTIONS'])
def add_custom_domain():
    """
    POST /api/domains/add

    Add a custom domain for a user

    Body:
    {
        "email": "alice@example.com",
        "custom_domain": "alicewonderland.com",
        "brand": "personal_blog"  # optional, will be auto-detected
    }

    Returns:
    {
        "success": true,
        "domain": "alicewonderland.com",
        "verified": false,
        "brand": "personal_blog",
        "verification_code": "ABC123..."
    }
    """

    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()

    if not data or 'email' not in data or 'custom_domain' not in data:
        return jsonify({
            'error': 'Missing required fields: email, custom_domain'
        }), 400

    email = data['email']
    custom_domain = data['custom_domain'].lower().strip()
    brand = data.get('brand') or detect_brand(custom_domain)

    # Generate verification code
    hash_input = f"{email}{custom_domain}{datetime.now().isoformat()}".encode('utf-8')
    verification_code = hashlib.sha256(hash_input).hexdigest()[:16].upper()

    db = get_db()

    try:
        # Check if user exists
        user = db.execute('SELECT id, email FROM users WHERE email = ?', (email,)).fetchone()

        if not user:
            # Create shadow user
            db.execute('''
                INSERT INTO users (username, email, created_at)
                VALUES (?, ?, ?)
            ''', (email.split('@')[0], email, datetime.now(timezone.utc).isoformat()))
            db.commit()
            user_id = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()['id']
        else:
            user_id = user['id']

        # Check if custom_domains table exists
        tables = db.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='custom_domains'
        ''').fetchone()

        if not tables:
            # Create custom_domains table
            db.execute('''
                CREATE TABLE custom_domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    domain TEXT NOT NULL UNIQUE,
                    brand TEXT,
                    verified BOOLEAN DEFAULT 0,
                    verification_code TEXT,
                    added_at TEXT,
                    verified_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            db.commit()

        # Insert custom domain
        db.execute('''
            INSERT INTO custom_domains (user_id, domain, brand, verified, verification_code, added_at)
            VALUES (?, ?, ?, 0, ?, ?)
        ''', (user_id, custom_domain, brand, verification_code, datetime.now(timezone.utc).isoformat()))

        db.commit()

        return jsonify({
            'success': True,
            'domain': custom_domain,
            'verified': False,
            'brand': brand,
            'verification_code': verification_code,
            'message': f'Add TXT record: soulfra-verify={verification_code}'
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to add domain: {str(e)}'
        }), 500
    finally:
        db.close()


@domain_api_bp.route('/connections', methods=['GET', 'OPTIONS'])
def get_connections():
    """
    GET /api/domains/connections?email=alice@example.com

    Get email web connections (GitHub-style graph)

    Returns:
    {
        "success": true,
        "email": "alice@example.com",
        "connections": [
            {
                "domain": "alice.soulfra.com",
                "brand": "hub",
                "type": "subdomain",
                "activity_count": 42
            },
            {
                "domain": "alicewonderland.com",
                "brand": "personal_blog",
                "type": "custom",
                "activity_count": 15
            }
        ]
    }
    """

    if request.method == 'OPTIONS':
        return '', 204

    email = request.args.get('email')

    if not email:
        return jsonify({'error': 'Missing email parameter'}), 400

    db = get_db()

    try:
        # Get user
        user = db.execute('SELECT id, email FROM users WHERE email = ?', (email,)).fetchone()

        if not user:
            return jsonify({
                'success': True,
                'email': email,
                'connections': []
            }), 200

        connections = []

        # Get subdomain assignment (from waitlist)
        waitlist_entry = db.execute('''
            SELECT domain_name, letter_code FROM waitlist WHERE email = ?
        ''', (email,)).fetchone()

        if waitlist_entry:
            domain_name = waitlist_entry['domain_name']
            letter = waitlist_entry['letter_code']

            # Count activities (posts, voice recordings, etc.)
            activity_count = db.execute('''
                SELECT COUNT(*) as count FROM posts WHERE author_id = ?
            ''', (user['id'],)).fetchone()['count']

            connections.append({
                'domain': f"{email.split('@')[0]}.{domain_name}.com",
                'brand': BRAND_MAP.get(domain_name, 'hub'),
                'type': 'subdomain',
                'letter': letter,
                'activity_count': activity_count
            })

        # Get custom domains
        custom_domains = db.execute('''
            SELECT domain, brand, verified FROM custom_domains WHERE user_id = ?
        ''', (user['id'],)).fetchall()

        for cd in custom_domains:
            connections.append({
                'domain': cd['domain'],
                'brand': cd['brand'],
                'type': 'custom',
                'verified': bool(cd['verified']),
                'activity_count': 0  # TODO: track per-domain activity
            })

        return jsonify({
            'success': True,
            'email': email,
            'connections': connections
        }), 200

    except Exception as e:
        return jsonify({
            'error': f'Failed to get connections: {str(e)}'
        }), 500
    finally:
        db.close()


@domain_api_bp.route('/assign', methods=['POST', 'OPTIONS'])
def assign_subdomain():
    """
    POST /api/domains/assign

    Assign subdomain to user (e.g., alice.soulfra.com)

    Body:
    {
        "email": "alice@example.com",
        "subdomain": "alice",
        "domain": "soulfra.com"
    }

    Returns:
    {
        "success": true,
        "url": "alice.soulfra.com",
        "letter_code": "a"
    }
    """

    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()

    if not data or 'email' not in data or 'subdomain' not in data:
        return jsonify({
            'error': 'Missing required fields: email, subdomain'
        }), 400

    email = data['email']
    subdomain = data['subdomain'].lower().strip()
    domain = data.get('domain', 'soulfra.com').replace('.com', '')

    db = get_db()

    try:
        # Check waitlist entry
        waitlist_entry = db.execute('''
            SELECT letter_code, domain_name FROM waitlist WHERE email = ?
        ''', (email,)).fetchone()

        if waitlist_entry:
            letter = waitlist_entry['letter_code']
            assigned_domain = waitlist_entry['domain_name']

            return jsonify({
                'success': True,
                'url': f"{subdomain}.{assigned_domain}.com",
                'letter_code': letter,
                'domain': assigned_domain
            }), 200
        else:
            return jsonify({
                'error': 'User not found in waitlist'
            }), 404

    except Exception as e:
        return jsonify({
            'error': f'Failed to assign subdomain: {str(e)}'
        }), 500
    finally:
        db.close()


@domain_api_bp.route('/brand', methods=['GET', 'OPTIONS'])
def detect_brand_api():
    """
    GET /api/domains/brand?domain=cringeproof.com

    Detect brand/theme from domain name

    Returns:
    {
        "success": true,
        "domain": "cringeproof.com",
        "brand": "call_out_cringe"
    }
    """

    if request.method == 'OPTIONS':
        return '', 204

    domain = request.args.get('domain')

    if not domain:
        return jsonify({'error': 'Missing domain parameter'}), 400

    brand = detect_brand(domain)

    return jsonify({
        'success': True,
        'domain': domain,
        'brand': brand
    }), 200
