#!/usr/bin/env python3
"""
Lineage Router - Context-Aware URL Routing (Zero Dependencies)

VANITY ADDRESS CONCEPT FOR QR CODES

Same short URL → Different destinations based on WHO scanned it!

Philosophy:
----------
Just like Bitcoin vanity addresses or early DNS-less routing,
the SAME URL should behave differently based on CONTEXT.

Traditional routing:
  https://soulfra.com/s/ABC123 → ALWAYS goes to same place

Lineage routing:
  https://soulfra.com/s/ABC123
    ├─ Person A (privacy lineage) → privacy.soulfra.com
    ├─ Person B (tech lineage) → tech.soulfra.com
    ├─ Person C (platform lineage) → platform.soulfra.com
    └─ Unknown device → general.soulfra.com (default)

How It Works:
------------
1. User scans QR code with short URL
2. Capture device fingerprint (IP + User Agent)
3. Look up device's lineage in scan_lineage table
4. Use lineage metadata to determine faucet assignment
5. Redirect to appropriate subdomain/content

Lineage → Faucet Mapping:
-------------------------
Root lineage metadata can specify:
  - topic: "privacy" → privacy.soulfra.com
  - topic: "tech" → tech.soulfra.com
  - topic: "platform" → platform.soulfra.com
  - brand: "ocean-dreams" → ocean-dreams.soulfra.com

Example Flow:
------------
1. Alice creates root lineage with metadata: {"topic": "privacy"}
2. Alice shares QR code with short URL /s/ABC123
3. Bob scans → Creates child lineage → Gets privacy.soulfra.com
4. Bob shares same URL /s/ABC123
5. Charlie scans → Child of Bob's lineage → ALSO gets privacy.soulfra.com
6. Random person scans → No lineage → Gets general.soulfra.com

This creates VIRAL ROUTING where lineage propagates through shares!

Usage:
    # Route based on device fingerprint
    python3 lineage_router.py --route /s/ABC123 --ip 1.2.3.4 --user-agent "Mozilla..."

    # Create lineage-aware short URL
    python3 lineage_router.py --create --url "https://soulfra.com/blog/123" --lineage HASH

    # Show all routes for a short URL
    python3 lineage_router.py --show-routes ABC123
"""

import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from typing import Dict, Optional, List


# ==============================================================================
# DEVICE FINGERPRINTING (from qr_captcha.py)
# ==============================================================================

def generate_device_id(ip_address: str, user_agent: str, device_type: str = None) -> str:
    """Generate unique device ID from fingerprint"""
    fingerprint = f"{ip_address}|{user_agent}|{device_type or 'unknown'}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]


# ==============================================================================
# LINEAGE LOOKUP
# ==============================================================================

def get_device_lineage(device_fingerprint: Dict) -> Optional[Dict]:
    """
    Get lineage for a device based on its fingerprint

    Args:
        device_fingerprint: {ip_address, user_agent, device_type}

    Returns:
        Lineage dict or None if device has no lineage
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find most recent scan by this device
    cursor.execute('''
        SELECT sl.* FROM scan_lineage sl
        JOIN qr_scans qs ON sl.scan_id = qs.id
        WHERE qs.ip_address = ? AND qs.user_agent = ?
        ORDER BY sl.created_at DESC
        LIMIT 1
    ''', (device_fingerprint.get('ip_address'), device_fingerprint.get('user_agent')))

    lineage = cursor.fetchone()
    conn.close()

    if lineage:
        return dict(lineage)
    return None


def get_root_lineage(lineage_hash: str) -> Optional[Dict]:
    """
    Get root lineage for any lineage hash

    Follows parent chain up to root to get original metadata
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get current lineage
    cursor.execute('SELECT * FROM scan_lineage WHERE lineage_hash = ?', (lineage_hash,))
    current = cursor.fetchone()

    if not current:
        conn.close()
        return None

    current = dict(current)

    # If already root, return it
    if current['generation'] == 0:
        conn.close()
        return current

    # Get root via root_scan_id
    cursor.execute('''
        SELECT * FROM scan_lineage
        WHERE scan_id = ? AND generation = 0
    ''', (current['root_scan_id'],))

    root = cursor.fetchone()
    conn.close()

    if root:
        return dict(root)
    return None


# ==============================================================================
# FAUCET ASSIGNMENT (Lineage → Subdomain)
# ==============================================================================

def get_faucet_from_lineage(lineage: Dict) -> Dict:
    """
    Determine faucet (subdomain/route) from lineage metadata

    Args:
        lineage: Lineage dict with metadata

    Returns:
        {
            "subdomain": "privacy" | "tech" | "platform" | None,
            "brand": "ocean-dreams" | None,
            "route": "/blog/123",
            "full_url": "https://privacy.soulfra.com/blog/123"
        }
    """
    # Parse metadata
    metadata = {}
    if lineage.get('metadata'):
        try:
            metadata = json.loads(lineage['metadata'])
        except:
            pass

    # Default faucet
    faucet = {
        'subdomain': None,
        'brand': None,
        'route': '/',
        'full_url': None
    }

    # Topic-based subdomain assignment
    topic = metadata.get('topic')
    if topic:
        # Map topics to subdomains
        topic_map = {
            'privacy': 'privacy',
            'security': 'security',
            'tech': 'tech',
            'technical': 'tech',
            'platform': 'platform',
            'code': 'code'
        }
        faucet['subdomain'] = topic_map.get(topic.lower())

    # Brand-based subdomain
    brand = metadata.get('brand')
    if brand:
        faucet['brand'] = brand
        faucet['subdomain'] = brand  # Brand takes precedence

    # Custom route from metadata
    if metadata.get('route'):
        faucet['route'] = metadata['route']

    # Build full URL
    try:
        from config import BASE_URL
    except ImportError:
        BASE_URL = "http://localhost:5001"

    base_domain = BASE_URL.split('://')[1].split(':')[0]  # Extract domain

    if faucet['subdomain']:
        faucet['full_url'] = f"https://{faucet['subdomain']}.{base_domain}{faucet['route']}"
    else:
        faucet['full_url'] = f"{BASE_URL}{faucet['route']}"

    return faucet


def assign_faucet_for_device(device_fingerprint: Dict, fallback_subdomain: str = None) -> Dict:
    """
    Assign faucet for device based on its lineage

    Args:
        device_fingerprint: Device info
        fallback_subdomain: Default subdomain if no lineage

    Returns:
        Faucet dict
    """
    # Get device's lineage
    lineage = get_device_lineage(device_fingerprint)

    if not lineage:
        # No lineage → Default faucet
        print("⚠️  No lineage found for device → Using fallback")
        return {
            'subdomain': fallback_subdomain,
            'brand': None,
            'route': '/',
            'full_url': f"http://localhost:5001/" if not fallback_subdomain else f"https://{fallback_subdomain}.soulfra.com/"
        }

    # Get root lineage (contains original metadata)
    root = get_root_lineage(lineage['lineage_hash'])

    if not root:
        print("⚠️  Root lineage not found → Using current lineage")
        root = lineage

    # Assign faucet based on root metadata
    faucet = get_faucet_from_lineage(root)

    print(f"✅ Faucet assigned from lineage")
    print(f"   Lineage: {lineage['lineage_hash']}")
    print(f"   Root: {root['lineage_hash']}")
    print(f"   Generation: {lineage['generation']}")
    print(f"   Faucet: {faucet['full_url']}")

    return faucet


# ==============================================================================
# SHORT URL ROUTING
# ==============================================================================

def create_lineage_short_url(target_url: str, lineage_hash: str = None, ttl_days: int = 365) -> Dict:
    """
    Create short URL that routes based on lineage

    Args:
        target_url: Default URL to redirect to
        lineage_hash: Optional lineage to associate with this URL
        ttl_days: Time to live in days

    Returns:
        Short URL info
    """
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Create lineage_short_urls table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lineage_short_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE NOT NULL,
            target_url TEXT NOT NULL,
            lineage_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            clicks INTEGER DEFAULT 0
        )
    ''')

    # Generate short ID
    short_id = secrets.token_urlsafe(6)[:8]

    from datetime import timedelta
    expires_at = datetime.now() + timedelta(days=ttl_days)

    cursor.execute('''
        INSERT INTO lineage_short_urls (short_id, target_url, lineage_hash, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (short_id, target_url, lineage_hash, expires_at.isoformat()))

    conn.commit()
    conn.close()

    try:
        from config import BASE_URL
    except ImportError:
        BASE_URL = "http://localhost:5001"

    short_url = f"{BASE_URL}/s/{short_id}"

    print(f"✅ Created lineage short URL")
    print(f"   Short ID: {short_id}")
    print(f"   Target: {target_url}")
    print(f"   Lineage: {lineage_hash or 'None (uses device lineage)'}")
    print(f"   URL: {short_url}")

    return {
        'short_id': short_id,
        'short_url': short_url,
        'target_url': target_url,
        'lineage_hash': lineage_hash
    }


def route_short_url(short_id: str, device_fingerprint: Dict) -> Dict:
    """
    Route short URL based on device lineage

    This is the MAGIC: Same URL → Different destination!

    Args:
        short_id: Short URL ID (from /s/<short_id>)
        device_fingerprint: Device info from request

    Returns:
        {
            "short_id": ...,
            "redirect_url": ...,
            "faucet": {...},
            "lineage": {...}
        }
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get short URL info
    cursor.execute('''
        SELECT * FROM lineage_short_urls WHERE short_id = ?
    ''', (short_id,))

    short_url_record = cursor.fetchone()

    if not short_url_record:
        # Try old url_shortcuts table
        cursor.execute('''
            SELECT * FROM url_shortcuts WHERE short_id = ?
        ''', (short_id,))

        short_url_record = cursor.fetchone()

        if not short_url_record:
            conn.close()
            return {
                'error': 'Short URL not found',
                'short_id': short_id
            }

    short_url_record = dict(short_url_record)

    # Increment clicks
    cursor.execute('''
        UPDATE lineage_short_urls SET clicks = clicks + 1 WHERE short_id = ?
    ''', (short_id,))
    conn.commit()
    conn.close()

    # Get faucet for device based on lineage
    faucet = assign_faucet_for_device(device_fingerprint)

    # Get device lineage
    lineage = get_device_lineage(device_fingerprint)

    # Determine redirect URL
    # Priority: Lineage faucet > Target URL > Default
    redirect_url = faucet.get('full_url') or short_url_record.get('target_url') or '/'

    print()
    print("=" * 70)
    print(f"🔀 ROUTING SHORT URL: /s/{short_id}")
    print("=" * 70)
    print(f"Device: {device_fingerprint.get('ip_address')}")
    print(f"Lineage: {lineage['lineage_hash'] if lineage else 'None'}")
    print(f"Faucet: {faucet.get('subdomain') or 'default'}")
    print(f"Redirect: {redirect_url}")
    print()

    return {
        'short_id': short_id,
        'redirect_url': redirect_url,
        'faucet': faucet,
        'lineage': lineage,
        'short_url_record': short_url_record
    }


def show_all_routes_for_short_url(short_id: str) -> List[Dict]:
    """
    Show all possible routes for a short URL based on existing lineages

    Demonstrates how same URL routes differently for different users
    """
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all unique root lineages
    cursor.execute('''
        SELECT DISTINCT lineage_hash, metadata, generation
        FROM scan_lineage
        WHERE generation = 0
        ORDER BY created_at DESC
    ''')

    roots = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print()
    print("=" * 70)
    print(f"🗺️  ALL POSSIBLE ROUTES FOR /s/{short_id}")
    print("=" * 70)
    print()

    routes = []

    for root in roots:
        faucet = get_faucet_from_lineage(root)

        print(f"Lineage: {root['lineage_hash']}")
        print(f"  → {faucet['full_url']}")
        print()

        routes.append({
            'lineage_hash': root['lineage_hash'],
            'faucet': faucet,
            'metadata': root.get('metadata')
        })

    # Show default (no lineage)
    print(f"No Lineage (default)")
    print(f"  → http://localhost:5001/")
    print()

    return routes


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Lineage Router - Context-Aware URL Routing')
    parser.add_argument('--route', type=str, help='Route short URL (format: /s/ABC123 or ABC123)')
    parser.add_argument('--ip', type=str, help='IP address for routing')
    parser.add_argument('--user-agent', type=str, help='User agent for routing')
    parser.add_argument('--create', action='store_true', help='Create lineage short URL')
    parser.add_argument('--url', type=str, help='Target URL for short URL')
    parser.add_argument('--lineage', type=str, help='Lineage hash to associate')
    parser.add_argument('--show-routes', type=str, help='Show all routes for short URL')

    args = parser.parse_args()

    if args.route:
        if not args.ip or not args.user_agent:
            print("❌ --ip and --user-agent required for routing")
            exit(1)

        # Extract short_id
        short_id = args.route.replace('/s/', '')

        device_fp = {
            'ip_address': args.ip,
            'user_agent': args.user_agent,
            'device_type': 'desktop'
        }

        result = route_short_url(short_id, device_fp)

        if 'error' in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ Redirect to: {result['redirect_url']}")

    elif args.create:
        if not args.url:
            print("❌ --url required for creating short URL")
            exit(1)

        result = create_lineage_short_url(args.url, args.lineage)

    elif args.show_routes:
        short_id = args.show_routes.replace('/s/', '')
        show_all_routes_for_short_url(short_id)

    else:
        print("Lineage Router - Context-Aware URL Routing")
        print()
        print("SAME URL → DIFFERENT DESTINATIONS (Based on Lineage)")
        print()
        print("Usage:")
        print("  --route /s/ABC123 --ip 1.2.3.4 --user-agent 'Mozilla...'")
        print("  --create --url 'https://soulfra.com/blog/123' --lineage HASH")
        print("  --show-routes ABC123")
        print()
        print("Examples:")
        print()
        print("  # Create short URL tied to privacy lineage")
        print("  python3 lineage_router.py --create --url 'https://soulfra.com/blog/privacy' --lineage 6d70c7621427")
        print()
        print("  # Route based on device")
        print("  python3 lineage_router.py --route ABC123 --ip 192.168.1.1 --user-agent 'Mozilla/5.0...'")
        print()
        print("  # Show all possible routes")
        print("  python3 lineage_router.py --show-routes ABC123")
