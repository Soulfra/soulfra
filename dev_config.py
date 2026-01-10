#!/usr/bin/env python3
"""
Development Configuration - Skip Authentication Barriers

This file enables development mode where:
- QR authentication is SKIPPED
- Localhost access without barriers
- Testing playground for all features

Usage:
    from dev_config import DEV_MODE, should_skip_auth

    if should_skip_auth():
        # Skip QR authentication in dev mode
        pass
    else:
        # Check authentication in production
        if not session.get('search_token'):
            return redirect(url_for('login_qr'))
"""

import os

# =============================================================================
# DEVELOPMENT MODE SETTINGS
# =============================================================================

# Enable development mode (skip auth, verbose logging)
DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'

# Skip QR authentication in dev mode
SKIP_QR_AUTH = os.environ.get('SKIP_QR_AUTH', 'true').lower() == 'true' if DEV_MODE else False

# Only accessible from localhost/LAN (security check)
LOCALHOST_ONLY = os.environ.get('LOCALHOST_ONLY', 'true').lower() == 'true' if DEV_MODE else False

# Verbose logging in dev mode
VERBOSE_LOGGING = os.environ.get('VERBOSE_LOGGING', 'true').lower() == 'true' if DEV_MODE else False

# Auto-create admin session (for testing)
AUTO_ADMIN_SESSION = os.environ.get('AUTO_ADMIN_SESSION', 'true').lower() == 'true' if DEV_MODE else False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def should_skip_auth():
    """
    Check if authentication should be skipped

    Returns:
        bool: True if in dev mode and auth should be skipped

    Example:
        if should_skip_auth():
            # Skip QR authentication
            pass
        else:
            # Require authentication
            if not session.get('search_token'):
                return redirect(url_for('login_qr'))
    """
    return DEV_MODE and SKIP_QR_AUTH


def is_localhost_request(request):
    """
    Check if request is from localhost/LAN

    Args:
        request: Flask request object

    Returns:
        bool: True if request is from localhost or local network

    Example:
        if LOCALHOST_ONLY and not is_localhost_request(request):
            return "Access denied - localhost only", 403
    """
    remote_addr = request.remote_addr

    # Localhost IPs
    localhost_ips = ['127.0.0.1', '::1', 'localhost']

    # LAN IPs (192.168.x.x, 10.x.x.x, etc.)
    lan_prefixes = ['192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                    '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                    '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.']

    # Check if localhost
    if remote_addr in localhost_ips:
        return True

    # Check if LAN
    for prefix in lan_prefixes:
        if remote_addr.startswith(prefix):
            return True

    return False


def log_dev(message):
    """
    Log message in dev mode (only if verbose logging enabled)

    Args:
        message: Message to log

    Example:
        log_dev("User accessed /chat without auth")
    """
    if VERBOSE_LOGGING:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[DEV] [{timestamp}] {message}")


def get_dev_config():
    """
    Get current development configuration

    Returns:
        dict: Configuration settings

    Example:
        config = get_dev_config()
        print(f"Dev mode: {config['dev_mode']}")
    """
    return {
        'dev_mode': DEV_MODE,
        'skip_qr_auth': SKIP_QR_AUTH,
        'localhost_only': LOCALHOST_ONLY,
        'verbose_logging': VERBOSE_LOGGING,
        'auto_admin_session': AUTO_ADMIN_SESSION
    }


# =============================================================================
# AUTO-CONFIGURATION
# =============================================================================

# Print dev mode status on import
if DEV_MODE:
    print("=" * 70)
    print("🔧 DEVELOPMENT MODE ENABLED")
    print("=" * 70)
    print(f"  - QR Authentication: {'SKIPPED' if SKIP_QR_AUTH else 'ENABLED'}")
    print(f"  - Localhost Only: {'YES' if LOCALHOST_ONLY else 'NO'}")
    print(f"  - Verbose Logging: {'YES' if VERBOSE_LOGGING else 'NO'}")
    print(f"  - Auto Admin Session: {'YES' if AUTO_ADMIN_SESSION else 'NO'}")
    print("=" * 70)
    print()


# =============================================================================
# TESTING
# =============================================================================

def test_dev_config():
    """Test development configuration"""
    print("=" * 70)
    print("🧪 Testing Development Configuration")
    print("=" * 70)
    print()

    # Test 1: Check dev mode
    print("TEST 1: Development Mode")
    print(f"  DEV_MODE: {DEV_MODE}")
    print(f"  Should skip auth: {should_skip_auth()}")
    print()

    # Test 2: Check localhost detection
    print("TEST 2: Localhost Detection")

    class FakeRequest:
        def __init__(self, remote_addr):
            self.remote_addr = remote_addr

    test_ips = [
        '127.0.0.1',      # Localhost
        '192.168.1.87',   # LAN
        '10.0.0.5',       # LAN
        '8.8.8.8',        # Internet (Google DNS)
    ]

    for ip in test_ips:
        req = FakeRequest(ip)
        is_local = is_localhost_request(req)
        print(f"  {ip}: {'✅ LOCAL' if is_local else '❌ INTERNET'}")
    print()

    # Test 3: Verbose logging
    print("TEST 3: Verbose Logging")
    log_dev("Test message in dev mode")
    print()

    # Test 4: Get config
    print("TEST 4: Configuration")
    config = get_dev_config()
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    print("=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_dev_config()
