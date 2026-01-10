#!/usr/bin/env python3
"""
Domain Verification - Proof of Ownership via DNS TXT Records

Like Google Analytics verification, but for domain ownership in the platform.

How it works:
1. User claims: "I own howtocookathome.com"
2. Platform generates: TXT soulfra-verify=abc123xyz789
3. User adds TXT to their DNS
4. Platform checks DNS → verified ownership
5. User can now:
   - Cross-post content to their domain
   - Earn ownership % for their domain
   - Join liquidity pools with their domain
   - Prove it's theirs (cryptographically)

Like ICP (Internet Computer Protocol) but using DNS as the trust layer.
"""

import dns.resolver
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from database import get_db

# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_domain_verification_tables():
    """Initialize domain verification tables"""
    conn = get_db()

    # Verified domains
    conn.execute('''
        CREATE TABLE IF NOT EXISTS verified_domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_name TEXT UNIQUE NOT NULL,
            verification_token TEXT UNIQUE NOT NULL,
            verification_method TEXT DEFAULT 'dns_txt',
            verified_at TIMESTAMP,
            last_checked TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Verification attempts (for debugging)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS verification_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN,
            error_message TEXT,
            FOREIGN KEY (domain_id) REFERENCES verified_domains(id)
        )
    ''')

    conn.commit()
    conn.close()


# ==============================================================================
# GENERATE VERIFICATION TOKEN
# ==============================================================================

def generate_verification_token(domain_name: str, user_id: int) -> str:
    """
    Generate unique verification token for domain

    Args:
        domain_name: Domain to verify (e.g., howtocookathome.com)
        user_id: User claiming ownership

    Returns:
        Token like: soulfra_abc123xyz789
    """

    # Create deterministic but unique token
    # Hash: domain + user_id + random salt
    salt = secrets.token_hex(16)
    data = f"{domain_name}{user_id}{salt}".encode()
    hash_hex = hashlib.sha256(data).hexdigest()[:16]

    return f"soulfra_{hash_hex}"


def create_verification_record(user_id: int, domain_name: str) -> Dict:
    """
    Create verification record for user's domain

    Args:
        user_id: User ID
        domain_name: Domain to verify

    Returns:
        {
            'domain_id': int,
            'verification_token': str,
            'txt_record': str (what to add to DNS)
        }
    """

    conn = get_db()

    # Check if already exists
    existing = conn.execute(
        'SELECT id, verification_token FROM verified_domains WHERE domain_name = ?',
        (domain_name,)
    ).fetchone()

    if existing:
        conn.close()
        return {
            'domain_id': existing['id'],
            'verification_token': existing['verification_token'],
            'txt_record': existing['verification_token'],
            'status': 'already_claimed'
        }

    # Generate token
    token = generate_verification_token(domain_name, user_id)

    # Create record
    cursor = conn.execute('''
        INSERT INTO verified_domains (user_id, domain_name, verification_token)
        VALUES (?, ?, ?)
    ''', (user_id, domain_name, token))

    domain_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        'domain_id': domain_id,
        'verification_token': token,
        'txt_record': token,
        'instructions': f'Add this TXT record to {domain_name}: {token}'
    }


# ==============================================================================
# DNS VERIFICATION
# ==============================================================================

def verify_domain_dns(domain_id: int) -> Dict:
    """
    Verify domain ownership via DNS TXT record

    Args:
        domain_id: Verified domain ID

    Returns:
        {
            'success': bool,
            'verified_at': str or None,
            'error': str or None
        }
    """

    conn = get_db()

    domain = conn.execute(
        'SELECT * FROM verified_domains WHERE id = ?',
        (domain_id,)
    ).fetchone()

    if not domain:
        conn.close()
        return {'success': False, 'error': 'Domain not found'}

    domain_name = domain['domain_name']
    expected_token = domain['verification_token']

    try:
        # Query DNS TXT records
        answers = dns.resolver.resolve(domain_name, 'TXT')

        # Check if our token exists
        for rdata in answers:
            txt_value = str(rdata).strip('"')
            if expected_token in txt_value:
                # Verified!
                verified_at = datetime.utcnow()

                conn.execute('''
                    UPDATE verified_domains
                    SET status = 'verified', verified_at = ?, last_checked = ?
                    WHERE id = ?
                ''', (verified_at, verified_at, domain_id))

                # Record success
                conn.execute('''
                    INSERT INTO verification_attempts (domain_id, success)
                    VALUES (?, 1)
                ''', (domain_id,))

                conn.commit()
                conn.close()

                return {
                    'success': True,
                    'verified_at': verified_at.isoformat(),
                    'domain_name': domain_name
                }

        # Token not found
        error = f'TXT record not found. Expected: {expected_token}'

        conn.execute('''
            UPDATE verified_domains
            SET last_checked = ?
            WHERE id = ?
        ''', (datetime.utcnow(), domain_id))

        conn.execute('''
            INSERT INTO verification_attempts (domain_id, success, error_message)
            VALUES (?, 0, ?)
        ''', (domain_id, error))

        conn.commit()
        conn.close()

        return {'success': False, 'error': error}

    except dns.resolver.NXDOMAIN:
        error = f'Domain {domain_name} does not exist'
    except dns.resolver.NoAnswer:
        error = f'No TXT records found for {domain_name}'
    except dns.resolver.Timeout:
        error = 'DNS query timed out'
    except Exception as e:
        error = str(e)

    # Record failure
    conn.execute('''
        UPDATE verified_domains
        SET last_checked = ?
        WHERE id = ?
    ''', (datetime.utcnow(), domain_id))

    conn.execute('''
        INSERT INTO verification_attempts (domain_id, success, error_message)
        VALUES (?, 0, ?)
    ''', (domain_id, error))

    conn.commit()
    conn.close()

    return {'success': False, 'error': error}


# ==============================================================================
# ALTERNATIVE VERIFICATION METHODS
# ==============================================================================

def verify_domain_file(domain_id: int) -> Dict:
    """
    Verify domain ownership via file upload

    User uploads file to: https://domain.com/soulfra-verify.txt
    File contains verification token
    """

    conn = get_db()

    domain = conn.execute(
        'SELECT * FROM verified_domains WHERE id = ?',
        (domain_id,)
    ).fetchone()

    if not domain:
        conn.close()
        return {'success': False, 'error': 'Domain not found'}

    domain_name = domain['domain_name']
    expected_token = domain['verification_token']

    try:
        import requests

        # Check for verification file
        url = f'https://{domain_name}/soulfra-verify.txt'
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            content = response.text.strip()
            if expected_token in content:
                # Verified!
                verified_at = datetime.utcnow()

                conn.execute('''
                    UPDATE verified_domains
                    SET status = 'verified', verified_at = ?,
                        verification_method = 'file_upload'
                    WHERE id = ?
                ''', (verified_at, domain_id))

                conn.commit()
                conn.close()

                return {
                    'success': True,
                    'verified_at': verified_at.isoformat(),
                    'method': 'file_upload'
                }

        error = f'Verification file not found or incorrect at {url}'

    except Exception as e:
        error = str(e)

    conn.close()
    return {'success': False, 'error': error}


def verify_domain_meta_tag(domain_id: int) -> Dict:
    """
    Verify domain ownership via HTML meta tag

    User adds to <head>:
    <meta name="soulfra-verify" content="abc123xyz789">
    """

    conn = get_db()

    domain = conn.execute(
        'SELECT * FROM verified_domains WHERE id = ?',
        (domain_id,)
    ).fetchone()

    if not domain:
        conn.close()
        return {'success': False, 'error': 'Domain not found'}

    domain_name = domain['domain_name']
    expected_token = domain['verification_token']

    try:
        import requests
        from bs4 import BeautifulSoup

        # Fetch homepage
        url = f'https://{domain_name}'
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for meta tag
            meta = soup.find('meta', {'name': 'soulfra-verify'})
            if meta and meta.get('content') == expected_token:
                # Verified!
                verified_at = datetime.utcnow()

                conn.execute('''
                    UPDATE verified_domains
                    SET status = 'verified', verified_at = ?,
                        verification_method = 'meta_tag'
                    WHERE id = ?
                ''', (verified_at, domain_id))

                conn.commit()
                conn.close()

                return {
                    'success': True,
                    'verified_at': verified_at.isoformat(),
                    'method': 'meta_tag'
                }

        error = f'Meta tag not found at {url}'

    except Exception as e:
        error = str(e)

    conn.close()
    return {'success': False, 'error': error}


# ==============================================================================
# USER QUERIES
# ==============================================================================

def get_user_verified_domains(user_id: int) -> list:
    """Get all verified domains for user"""

    conn = get_db()

    domains = conn.execute('''
        SELECT
            id,
            domain_name,
            verification_token,
            verification_method,
            verified_at,
            status
        FROM verified_domains
        WHERE user_id = ?
        ORDER BY verified_at DESC
    ''', (user_id,)).fetchall()

    conn.close()

    return [dict(d) for d in domains]


def is_domain_verified(domain_name: str) -> bool:
    """Check if domain is verified"""

    conn = get_db()

    verified = conn.execute(
        'SELECT id FROM verified_domains WHERE domain_name = ? AND status = "verified"',
        (domain_name,)
    ).fetchone()

    conn.close()

    return verified is not None


def get_domain_owner(domain_name: str) -> Optional[int]:
    """Get user_id of domain owner"""

    conn = get_db()

    owner = conn.execute(
        'SELECT user_id FROM verified_domains WHERE domain_name = ? AND status = "verified"',
        (domain_name,)
    ).fetchone()

    conn.close()

    return owner['user_id'] if owner else None


# ==============================================================================
# EXPORTS
# ==============================================================================

if __name__ == '__main__':
    print("Initializing domain verification tables...")
    init_domain_verification_tables()
    print("✅ Domain verification tables initialized")
    print()
    print("Domain Verification - Proof of Ownership")
    print()
    print("Verification methods:")
    print("  1. DNS TXT record (recommended)")
    print("  2. File upload (soulfra-verify.txt)")
    print("  3. HTML meta tag (<meta name='soulfra-verify'>)")
    print()
    print("Example:")
    print("  User claims: howtocookathome.com")
    print("  Token: soulfra_abc123xyz789")
    print("  Add TXT: howtocookathome.com TXT 'soulfra_abc123xyz789'")
    print("  Verify → Ownership proven cryptographically")
