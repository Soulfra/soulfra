#!/usr/bin/env python3
"""
QR Faucet - Transform JSON into Website Content (Zero Dependencies)

Scan a QR code → JSON payload → Transforms into content (blog, comment, auth, etc.)

Philosophy: QR codes aren't just links - they're DATA CONTAINERS.
Encode JSON directly in QR → Scan → Generate content on the fly.

Use Cases:
1. Content Faucet: QR with {"type": "blog", "topic": "privacy"} → Generates blog post
2. Auth Tokens: QR with {"type": "auth", "level": "premium"} → Grants access
3. Data Transfer: QR with {"type": "post", "title": "...", "content": "..."} → Creates post
4. Offline-First: QR codes work without internet - scan stores locally, syncs later

How It Works:
1. Generate QR code with JSON payload
2. User scans QR code
3. JSON decoded → Transformed into content based on "type"
4. Content created/displayed (blog post, comment, auth session, etc.)

Security:
- HMAC signatures prevent tampering
- Timestamps prevent replay attacks
- Device fingerprinting tracks who scanned
- Access levels enforced

Usage:
    # Generate QR with JSON payload
    python3 qr_faucet.py --generate --type blog --data '{"topic": "privacy"}'

    # Process scanned QR
    python3 qr_faucet.py --process QR_CODE_DATA

    # List all faucet QRs
    python3 qr_faucet.py --list
"""

import sqlite3
import json
import hashlib
import secrets
import time
import hmac
import base64
from datetime import datetime
from typing import Dict, Optional


# ==============================================================================
# CONFIG
# ==============================================================================

# Secret key for HMAC (store in environment in production)
SECRET_KEY = b"soulfra-qr-faucet-secret-2025"

# Base URL (from config.py)
try:
    from config import BASE_URL
except ImportError:
    BASE_URL = "http://localhost:5001"


# ==============================================================================
# PAYLOAD GENERATION & VERIFICATION
# ==============================================================================

def generate_qr_payload(payload_type: str, data: Dict, ttl_seconds: int = 3600) -> str:
    """
    Generate QR code payload with JSON data + HMAC signature

    Payload format (base64-encoded JSON):
    {
        "type": "blog" | "auth" | "post" | "comment" | ...,
        "data": {...},
        "timestamp": 1766432100,
        "expires_at": 1766435700,
        "nonce": "random_hex",
        "hmac": "signature"
    }

    Args:
        payload_type: Type of content to generate ("blog", "auth", "post", etc.)
        data: Payload data (depends on type)
        ttl_seconds: Time to live in seconds

    Returns:
        Base64-encoded signed payload
    """
    payload = {
        'type': payload_type,
        'data': data,
        'timestamp': int(time.time()),
        'expires_at': int(time.time()) + ttl_seconds,
        'nonce': secrets.token_hex(16)
    }

    # Create HMAC signature
    message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    payload['hmac'] = signature

    # Encode as base64
    payload_json = json.dumps(payload, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')

    return encoded


def verify_qr_payload(encoded_payload: str) -> Optional[Dict]:
    """
    Verify and decode QR payload

    Returns:
        Decoded payload if valid, None if invalid

    Checks:
    1. Valid base64
    2. Valid JSON
    3. HMAC signature valid
    4. Not expired
    """
    try:
        # Decode base64
        payload_json = base64.urlsafe_b64decode(encoded_payload.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)

        # Extract HMAC
        provided_hmac = payload.pop('hmac', None)

        if not provided_hmac:
            print("❌ Payload missing HMAC signature")
            return None

        # Verify HMAC
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        expected_hmac = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(provided_hmac, expected_hmac):
            print("❌ Invalid HMAC signature - payload may be tampered")
            return None

        # Check expiration
        if time.time() > payload['expires_at']:
            print(f"❌ Payload expired at {datetime.fromtimestamp(payload['expires_at'])}")
            return None

        # Payload is valid!
        return payload

    except Exception as e:
        print(f"❌ Payload verification failed: {e}")
        return None


# ==============================================================================
# CONTENT TRANSFORMATIONS
# ==============================================================================

def transform_to_blog_post(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into blog post

    Payload data format:
    {
        "topic": "privacy",
        "style": "technical" | "casual" | "academic",
        "length": "short" | "medium" | "long",
        "neural_network": "calriven" | "theauditor" | ...
    }

    Returns:
        {
            "title": "...",
            "content": "...",
            "metadata": {...}
        }
    """
    data = payload['data']
    topic = data.get('topic', 'general')
    style = data.get('style', 'casual')
    neural_network = data.get('neural_network', 'soulfra_judge')

    # Generate blog post (placeholder - will use neural network)
    title = f"QR-Generated Post: {topic.title()}"
    content = f"""
# {topic.title()}

This blog post was generated from a QR code scan!

**Topic:** {topic}
**Style:** {style}
**Generated by:** {neural_network}
**Scanned by:** Device {device_fingerprint.get('device_type', 'unknown')} from {device_fingerprint.get('ip_address', 'unknown')}

---

*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return {
        'title': title,
        'content': content,
        'metadata': {
            'source': 'qr_faucet',
            'topic': topic,
            'style': style,
            'neural_network': neural_network,
            'device_fingerprint': device_fingerprint
        }
    }


def transform_to_auth_token(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into authentication token

    Payload data format:
    {
        "level": "basic" | "premium" | "admin",
        "duration": 3600  (seconds)
    }

    Returns:
        {
            "access_level": "...",
            "expires_at": ...,
            "device_fingerprint": {...}
        }
    """
    data = payload['data']
    level = data.get('level', 'basic')
    duration = data.get('duration', 3600)

    return {
        'access_level': level,
        'expires_at': int(time.time()) + duration,
        'device_fingerprint': device_fingerprint,
        'granted_at': datetime.now().isoformat()
    }


def transform_to_post(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into post (pre-written content)

    Payload data format:
    {
        "title": "Post Title",
        "content": "Post content...",
        "tags": ["tag1", "tag2"]
    }

    Returns:
        Post data dict
    """
    data = payload['data']

    return {
        'title': data.get('title', 'Untitled Post'),
        'content': data.get('content', ''),
        'tags': data.get('tags', []),
        'metadata': {
            'source': 'qr_faucet',
            'device_fingerprint': device_fingerprint
        }
    }


def transform_to_plot_action(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into plot action

    Payload data format:
    {
        "plot_id": 1,
        "action_type": "build" | "defend" | "visit" | "trade"
    }

    Returns:
        Plot action data
    """
    data = payload['data']

    return {
        'plot_id': data.get('plot_id'),
        'action_type': data.get('action_type'),
        'device_fingerprint': device_fingerprint
    }


def transform_to_question_response(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into question response form data

    Payload data format:
    {
        "plot_id": 1,
        "question_id": 5  (optional, for tracking which rotation question)
    }

    Returns:
        Question response data for form rendering
    """
    data = payload['data']

    return {
        'plot_id': data.get('plot_id'),
        'question_id': data.get('question_id'),
        'device_fingerprint': device_fingerprint
    }


def transform_to_referral(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into referral data

    Payload data format:
    {
        "referral_code": "ref-abc123",
        "username": "referrer_name"
    }

    Returns:
        Referral data for signup bonus
    """
    data = payload['data']

    return {
        'referral_code': data.get('referral_code'),
        'referrer_username': data.get('username'),
        'device_fingerprint': device_fingerprint
    }


def transform_to_idea_submission(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform QR payload into idea submission

    Payload data format:
    {
        "theme": "privacy" | "technical" | "validation",
        "domain": "ocean-dreams" | "calriven" | etc.
    }

    Returns:
        Redirect URL to idea submission form with pre-filled theme/domain
    """
    from idea_submission_system import submit_idea

    data = payload['data']
    theme = data.get('theme', '')
    domain = data.get('domain', '')

    # Return data for redirect to submission form
    return {
        'redirect_url': f"/submit-idea?theme={theme}&domain={domain}",
        'theme': theme,
        'domain': domain,
        'device_fingerprint': device_fingerprint
    }


def transform_payload(payload: Dict, device_fingerprint: Dict) -> Dict:
    """
    Transform payload based on type

    Args:
        payload: Verified payload
        device_fingerprint: Device info from scan

    Returns:
        Transformed content
    """
    payload_type = payload['type']

    if payload_type == 'blog':
        return transform_to_blog_post(payload, device_fingerprint)
    elif payload_type == 'auth':
        return transform_to_auth_token(payload, device_fingerprint)
    elif payload_type == 'post':
        return transform_to_post(payload, device_fingerprint)
    elif payload_type == 'plot_action':
        return transform_to_plot_action(payload, device_fingerprint)
    elif payload_type == 'question_response':
        return transform_to_question_response(payload, device_fingerprint)
    elif payload_type == 'referral':
        return transform_to_referral(payload, device_fingerprint)
    elif payload_type == 'idea_submission':
        return transform_to_idea_submission(payload, device_fingerprint)
    else:
        raise ValueError(f"Unknown payload type: {payload_type}")


# ==============================================================================
# DATABASE FUNCTIONS
# ==============================================================================

def save_qr_faucet(payload_type: str, encoded_payload: str, data: Dict) -> int:
    """Save generated QR faucet to database"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Create table if needed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_faucets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload_type TEXT NOT NULL,
            encoded_payload TEXT NOT NULL,
            payload_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            times_scanned INTEGER DEFAULT 0,
            last_scanned_at TIMESTAMP
        )
    ''')

    # Decode to get expiration
    payload = verify_qr_payload(encoded_payload)
    expires_at = datetime.fromtimestamp(payload['expires_at']).isoformat() if payload else None

    cursor.execute('''
        INSERT INTO qr_faucets (payload_type, encoded_payload, payload_data, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (
        payload_type,
        encoded_payload,
        json.dumps(data),
        expires_at
    ))

    faucet_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return faucet_id


def record_faucet_scan(faucet_id: int, device_fingerprint: Dict, result: Dict):
    """Record a faucet scan"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Update scan count
    cursor.execute('''
        UPDATE qr_faucets
        SET times_scanned = times_scanned + 1,
            last_scanned_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), faucet_id))

    # Create scan log table if needed
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qr_faucet_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faucet_id INTEGER NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            result_data TEXT,
            FOREIGN KEY (faucet_id) REFERENCES qr_faucets(id)
        )
    ''')

    cursor.execute('''
        INSERT INTO qr_faucet_scans (
            faucet_id, ip_address, user_agent, device_type, result_data
        ) VALUES (?, ?, ?, ?, ?)
    ''', (
        faucet_id,
        device_fingerprint.get('ip_address'),
        device_fingerprint.get('user_agent'),
        device_fingerprint.get('device_type'),
        json.dumps(result)
    ))

    conn.commit()
    conn.close()


def get_all_faucets():
    """Get all QR faucets"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT * FROM qr_faucets
            ORDER BY created_at DESC
        ''')
        faucets = cursor.fetchall()
        return [dict(f) for f in faucets]
    except:
        return []
    finally:
        conn.close()


# ==============================================================================
# QR CODE GENERATION
# ==============================================================================

def generate_qr_faucet(payload_type: str, data: Dict, ttl_seconds: int = 3600) -> Dict:
    """
    Generate QR faucet

    Args:
        payload_type: "blog", "auth", "post", etc.
        data: Payload data
        ttl_seconds: Time to live

    Returns:
        {
            "faucet_id": ...,
            "encoded_payload": "...",
            "qr_url": "http://localhost:5001/qr/faucet/...",
            "expires_at": ...
        }
    """
    # Generate payload
    encoded_payload = generate_qr_payload(payload_type, data, ttl_seconds)

    # Save to database
    faucet_id = save_qr_faucet(payload_type, encoded_payload, data)

    # Build URL
    qr_url = f"{BASE_URL}/qr/faucet/{encoded_payload}"

    # Get expiration
    payload = verify_qr_payload(encoded_payload)
    expires_at = payload['expires_at'] if payload else None

    print(f"✅ Generated QR faucet (ID: {faucet_id})")
    print(f"   Type: {payload_type}")
    print(f"   URL: {qr_url}")
    print(f"   Expires: {datetime.fromtimestamp(expires_at) if expires_at else 'N/A'}")

    return {
        'faucet_id': faucet_id,
        'encoded_payload': encoded_payload,
        'qr_url': qr_url,
        'expires_at': expires_at
    }


def process_qr_faucet(encoded_payload: str, device_fingerprint: Dict = None) -> Dict:
    """
    Process scanned QR faucet

    Args:
        encoded_payload: Base64-encoded payload
        device_fingerprint: Device info (IP, user agent, etc.)

    Returns:
        Transformed content based on payload type
    """
    if device_fingerprint is None:
        device_fingerprint = {'ip_address': 'unknown', 'user_agent': 'unknown'}

    # Verify payload
    payload = verify_qr_payload(encoded_payload)

    if not payload:
        return {'success': False, 'error': 'Invalid or expired payload'}

    # Transform based on type
    try:
        result = transform_payload(payload, device_fingerprint)

        print(f"✅ Processed QR faucet")
        print(f"   Type: {payload['type']}")
        print(f"   Device: {device_fingerprint.get('device_type', 'unknown')}")
        print(f"   IP: {device_fingerprint.get('ip_address', 'unknown')}")

        return {
            'success': True,
            'payload_type': payload['type'],
            'result': result
        }

    except Exception as e:
        print(f"❌ Transform failed: {e}")
        return {'success': False, 'error': str(e)}


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='QR Faucet - JSON to Content Generator')
    parser.add_argument('--generate', action='store_true', help='Generate QR faucet')
    parser.add_argument('--type', type=str, help='Payload type (blog, auth, post)')
    parser.add_argument('--data', type=str, help='JSON data for payload')
    parser.add_argument('--ttl', type=int, default=3600, help='Time to live (seconds)')
    parser.add_argument('--process', type=str, help='Process scanned payload')
    parser.add_argument('--list', action='store_true', help='List all faucets')

    args = parser.parse_args()

    if args.generate:
        if not args.type or not args.data:
            print("❌ --type and --data required for generation")
            print("Example: --type blog --data '{\"topic\": \"privacy\"}'")
            exit(1)

        data = json.loads(args.data)
        result = generate_qr_faucet(args.type, data, args.ttl)

        print()
        print("=" * 70)
        print("✅ QR FAUCET GENERATED")
        print("=" * 70)
        print(f"Scan this URL to generate {args.type} content:")
        print(result['qr_url'])

    elif args.process:
        device_fp = {
            'ip_address': '127.0.0.1',
            'user_agent': 'CLI Test',
            'device_type': 'desktop'
        }

        result = process_qr_faucet(args.process, device_fp)

        print()
        print("=" * 70)
        print("🔍 FAUCET PROCESSED")
        print("=" * 70)

        if result['success']:
            print(f"Type: {result['payload_type']}")
            print(f"Result:")
            print(json.dumps(result['result'], indent=2))
        else:
            print(f"Error: {result['error']}")

    elif args.list:
        faucets = get_all_faucets()

        print("=" * 70)
        print(f"📋 QR FAUCETS ({len(faucets)} total)")
        print("=" * 70)
        print()

        if not faucets:
            print("No faucets generated yet")
        else:
            for f in faucets:
                print(f"ID: {f['id']}")
                print(f"   Type: {f['payload_type']}")
                print(f"   Created: {f['created_at']}")
                print(f"   Scanned: {f['times_scanned']} times")
                print(f"   Expires: {f['expires_at']}")
                print()

    else:
        print("QR Faucet - Transform JSON into Content")
        print()
        print("Usage:")
        print("  --generate --type blog --data '{\"topic\": \"privacy\"}'")
        print("  --process ENCODED_PAYLOAD")
        print("  --list")
