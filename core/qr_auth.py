#!/usr/bin/env python3
"""
QR Code Authentication System

Passwordless login via QR codes with device fingerprinting and session encryption.

Flow:
1. User clicks "Login with QR"
2. Server generates auth token + QR code
3. User scans QR with phone
4. Phone opens /qr/faucet/<auth_payload>
5. Server verifies token, creates session
6. User logged in on phone!

Security:
- Tokens expire after 5 minutes
- One-time use only
- Device fingerprinting (optional)
- Secure session cookies (httponly, secure, samesite)

Usage:
    from qr_auth import QRAuthManager

    # Generate QR for login
    manager = QRAuthManager()
    qr_data = manager.generate_login_qr()

    # Verify and login
    success = manager.verify_and_login(token, device_fingerprint)
"""

import secrets
import time
import json
import base64
import hashlib
import io
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from database import get_db

# QR code generation
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    print("⚠️  qrcode library not installed. Install with: pip install qrcode[pil]")


class QRAuthManager:
    """Manage QR code authentication"""

    def __init__(self):
        """Initialize QR auth manager"""
        self.init_database()

    def init_database(self):
        """Create qr_auth_tokens table if not exists"""
        db = get_db()

        db.execute('''
            CREATE TABLE IF NOT EXISTS qr_auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                device_fingerprint TEXT,
                expires_at INTEGER NOT NULL,
                used BOOLEAN DEFAULT 0,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        db.commit()

        # Clean up expired tokens (older than 1 hour)
        one_hour_ago = int(time.time()) - 3600
        db.execute('''
            DELETE FROM qr_auth_tokens
            WHERE created_at < ?
        ''', (datetime.fromtimestamp(one_hour_ago),))
        db.commit()

    def generate_login_qr(self, user_id: Optional[int] = None, expires_minutes: int = 5) -> Dict:
        """
        Generate QR code for login

        Args:
            user_id: Optional user ID (for authenticated QR regeneration)
            expires_minutes: Token expiration time in minutes (default: 5)

        Returns:
            Dict with:
            - token: Auth token
            - qr_url: URL for QR code
            - qr_image: QR code image (if qrcode library available)
            - expires_at: Expiration timestamp
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = int(time.time()) + (expires_minutes * 60)

        # Store in database
        db = get_db()
        db.execute('''
            INSERT INTO qr_auth_tokens (token, user_id, expires_at, used)
            VALUES (?, ?, ?, 0)
        ''', (token, user_id, expires_at))
        db.commit()

        # Create payload
        payload = {
            'type': 'auth',
            'token': token,
            'expires': expires_at,
            'v': 1  # Version
        }

        # Encode as base64
        payload_json = json.dumps(payload)
        payload_encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()

        # Create QR URL
        qr_url = f"/qr/faucet/{payload_encoded}"

        result = {
            'token': token,
            'qr_url': qr_url,
            'expires_at': expires_at,
            'expires_in': expires_minutes * 60
        }

        # Generate QR code image
        if HAS_QRCODE:
            result['qr_image'] = self._generate_qr_image(qr_url)
            result['qr_image_base64'] = self._generate_qr_image_base64(qr_url)

        return result

    def _generate_qr_image(self, url: str, full_url: bool = False):
        """Generate QR code image"""
        if not HAS_QRCODE:
            return None

        # Use full URL if requested (for external access)
        if full_url:
            from config import BASE_URL
            url = f"{BASE_URL}{url}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def _generate_qr_image_base64(self, url: str, full_url: bool = False) -> str:
        """Generate QR code as base64 string for embedding in HTML"""
        if not HAS_QRCODE:
            return None

        img = self._generate_qr_image(url, full_url)

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        import base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify QR auth token

        Args:
            token: Auth token from QR code

        Returns:
            Tuple of (success, token_data, error_message)
        """
        db = get_db()

        # Get token from database
        token_row = db.execute('''
            SELECT * FROM qr_auth_tokens
            WHERE token = ?
        ''', (token,)).fetchone()

        if not token_row:
            return False, None, "Invalid token"

        token_data = dict(token_row)

        # Check if already used
        if token_data['used']:
            return False, None, "Token already used"

        # Check expiration
        current_time = int(time.time())
        if current_time > token_data['expires_at']:
            return False, None, "Token expired"

        return True, token_data, None

    def verify_and_login(self, token: str, device_fingerprint: Optional[str] = None) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Verify token and create login session

        Args:
            token: Auth token
            device_fingerprint: Optional device fingerprint for additional security

        Returns:
            Tuple of (success, user_id, error_message)
        """
        # Verify token
        valid, token_data, error = self.verify_token(token)

        if not valid:
            return False, None, error

        # Mark token as used
        db = get_db()
        db.execute('''
            UPDATE qr_auth_tokens
            SET used = 1, used_at = ?, device_fingerprint = ?
            WHERE token = ?
        ''', (datetime.now(), device_fingerprint, token))
        db.commit()

        # Return user_id (None if unauthenticated QR code)
        user_id = token_data['user_id']

        if user_id:
            # Existing user logging in
            return True, user_id, None
        else:
            # New/anonymous login - create session without user
            # App can prompt for username/signup
            return True, None, None

    def create_device_fingerprint(self, request) -> str:
        """
        Create device fingerprint from request

        Args:
            request: Flask request object

        Returns:
            SHA-256 hash of device characteristics
        """
        fingerprint_data = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'accept_language': request.headers.get('Accept-Language', ''),
            'accept_encoding': request.headers.get('Accept-Encoding', ''),
        }

        # Hash fingerprint
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()

        return fingerprint_hash

    def cleanup_expired_tokens(self):
        """Clean up expired and old tokens"""
        db = get_db()

        # Delete tokens older than 1 hour
        one_hour_ago = int(time.time()) - 3600

        db.execute('''
            DELETE FROM qr_auth_tokens
            WHERE expires_at < ?
        ''', (one_hour_ago,))

        db.commit()

    def get_token_stats(self) -> Dict:
        """Get statistics about QR auth usage"""
        db = get_db()

        stats = {}

        # Total tokens generated
        stats['total_generated'] = db.execute(
            'SELECT COUNT(*) FROM qr_auth_tokens'
        ).fetchone()[0]

        # Used tokens
        stats['total_used'] = db.execute(
            'SELECT COUNT(*) FROM qr_auth_tokens WHERE used = 1'
        ).fetchone()[0]

        # Expired tokens
        current_time = int(time.time())
        stats['total_expired'] = db.execute(
            'SELECT COUNT(*) FROM qr_auth_tokens WHERE expires_at < ? AND used = 0',
            (current_time,)
        ).fetchone()[0]

        # Active tokens
        stats['total_active'] = db.execute(
            'SELECT COUNT(*) FROM qr_auth_tokens WHERE expires_at >= ? AND used = 0',
            (current_time,)
        ).fetchone()[0]

        return stats


def generate_login_qr_code(user_id: Optional[int] = None) -> Dict:
    """
    Helper function to generate login QR code

    Args:
        user_id: Optional user ID

    Returns:
        QR code data dict
    """
    manager = QRAuthManager()
    return manager.generate_login_qr(user_id)


def verify_qr_login(token: str, device_fingerprint: Optional[str] = None) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Helper function to verify QR login

    Args:
        token: Auth token
        device_fingerprint: Optional device fingerprint

    Returns:
        Tuple of (success, user_id, error_message)
    """
    manager = QRAuthManager()
    return manager.verify_and_login(token, device_fingerprint)


# CLI for testing
if __name__ == "__main__":
    import sys

    print("QR Authentication System\n")

    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        # Generate test QR code
        manager = QRAuthManager()
        qr_data = manager.generate_login_qr()

        print(f"✓ Generated QR code")
        print(f"  Token: {qr_data['token']}")
        print(f"  URL: {qr_data['qr_url']}")
        print(f"  Expires in: {qr_data['expires_in']} seconds")

        if 'qr_image' in qr_data:
            print(f"\n✓ QR code image generated")
            print(f"  Scan with phone to test!")

            # Save to file
            qr_data['qr_image'].save('qr_login_test.png')
            print(f"  Saved to: qr_login_test.png")

    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Show stats
        manager = QRAuthManager()
        stats = manager.get_token_stats()

        print("QR Auth Statistics:")
        print(f"  Total generated: {stats['total_generated']}")
        print(f"  Total used: {stats['total_used']}")
        print(f"  Expired (unused): {stats['total_expired']}")
        print(f"  Active (valid): {stats['total_active']}")

    else:
        print("Usage:")
        print("  python3 qr_auth.py generate  # Generate test QR code")
        print("  python3 qr_auth.py stats     # Show usage statistics")
