"""
Soulfra Configuration System

Centralized configuration for domain-agnostic deployment.
Makes platform reproducible on any domain (localhost, custom domains, widgets).

Environment Variables:
- BASE_URL: Full base URL (e.g., "https://myplatform.com", "http://localhost:5001")
- PLATFORM_VERSION: Semantic version (default: "0.1.0")
- SECRET_KEY: Flask secret key
- ADMIN_PASSWORD: Admin login password

Usage:
    from config import BASE_URL, PLATFORM_VERSION

    qr_url = f"{BASE_URL}/s/{short_id}"
"""

import os

# ===========================================
# CORE CONFIGURATION
# ===========================================

# Platform version (semantic versioning)
PLATFORM_VERSION = os.environ.get('PLATFORM_VERSION', '0.1.0')

# Base URL for the platform (domain-agnostic)
# Examples:
#   - Production: https://soulfra.com
#   - Development: http://localhost:5001
#   - Custom: https://myplatform.com
#   - Widget: https://widget.example.com
def get_server_ip():
    """Auto-detect server IP address for LAN access"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

# Auto-detect IP for mobile/LAN access if BASE_URL not set
if 'BASE_URL' not in os.environ:
    server_ip = get_server_ip()
    BASE_URL = f'http://{server_ip}:5001'
else:
    BASE_URL = os.environ.get('BASE_URL')

# Remove trailing slash for consistency
BASE_URL = BASE_URL.rstrip('/')

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'soulfra2025')

# ===========================================
# AI / OLLAMA (Treat as a Node/Service)
# ===========================================

# Ollama host (domain-agnostic, like BASE_URL)
# Examples:
#   - Local: http://localhost:11434
#   - Remote: https://ollama.mycompany.com
#   - Service: http://ollama-service:11434
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_HOST = OLLAMA_HOST.rstrip('/')

# ===========================================
# DATABASE
# ===========================================

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'soulfra.db')
DATABASE_VERSION = os.environ.get('DATABASE_VERSION', '2')  # Schema version

# ===========================================
# EMAIL (SMTP)
# ===========================================

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

# ===========================================
# FEATURES
# ===========================================

# Enable/disable features
ENABLE_AI_REASONING = os.environ.get('ENABLE_AI_REASONING', 'true').lower() == 'true'
ENABLE_ML = os.environ.get('ENABLE_ML', 'true').lower() == 'true'
ENABLE_QR_TRACKING = os.environ.get('ENABLE_QR_TRACKING', 'true').lower() == 'true'
ENABLE_SEARCH = os.environ.get('ENABLE_SEARCH', 'true').lower() == 'true'

# ===========================================
# DEPLOYMENT INFO
# ===========================================

def get_deployment_info():
    """Get deployment environment info"""
    return {
        'platform_version': PLATFORM_VERSION,
        'base_url': BASE_URL,
        'ollama_host': OLLAMA_HOST,
        'database_path': DATABASE_PATH,
        'database_version': DATABASE_VERSION,
        'features': {
            'ai_reasoning': ENABLE_AI_REASONING,
            'ml': ENABLE_ML,
            'qr_tracking': ENABLE_QR_TRACKING,
            'search': ENABLE_SEARCH,
        }
    }


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_full_url(path):
    """
    Get full URL for a path

    Args:
        path: Path (with or without leading slash)

    Returns:
        str: Full URL

    Examples:
        get_full_url('/soul/alice') → 'http://localhost:5001/soul/alice'
        get_full_url('s/ABC123') → 'http://localhost:5001/s/ABC123'
    """
    if not path.startswith('/'):
        path = '/' + path
    return f"{BASE_URL}{path}"


def get_short_url(short_id):
    """
    Get short URL for a short ID

    Args:
        short_id: Short code (e.g., "FUzHu9Lx")

    Returns:
        str: Full short URL

    Example:
        get_short_url('FUzHu9Lx') → 'http://localhost:5001/s/FUzHu9Lx'
    """
    return get_full_url(f'/s/{short_id}')


def get_soul_url(username):
    """
    Get soul URL for a username

    Args:
        username: Username

    Returns:
        str: Full soul URL

    Example:
        get_soul_url('alice') → 'http://localhost:5001/soul/alice'
    """
    return get_full_url(f'/soul/{username}')


# ===========================================
# VALIDATION
# ===========================================

def validate_config():
    """Validate configuration and warn about issues"""
    issues = []

    if BASE_URL == 'http://localhost:5001':
        issues.append("⚠️  BASE_URL is set to localhost (dev mode)")

    if SECRET_KEY == 'dev-secret-key-change-in-production':
        issues.append("⚠️  Using default SECRET_KEY (not secure for production!)")

    if ADMIN_PASSWORD == 'soulfra2025':
        issues.append("⚠️  Using default ADMIN_PASSWORD (not secure!)")

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        issues.append("ℹ️  SMTP not configured (emails won't send)")

    return issues


if __name__ == '__main__':
    print("=" * 70)
    print("🔧 Soulfra Configuration")
    print("=" * 70)
    print()
    print(f"Platform Version: {PLATFORM_VERSION}")
    print(f"Base URL: {BASE_URL}")
    print(f"Ollama Host: {OLLAMA_HOST}")
    print(f"Database: {DATABASE_PATH} (v{DATABASE_VERSION})")
    print()
    print("Features:")
    print(f"  - AI Reasoning: {ENABLE_AI_REASONING}")
    print(f"  - ML: {ENABLE_ML}")
    print(f"  - QR Tracking: {ENABLE_QR_TRACKING}")
    print(f"  - Search: {ENABLE_SEARCH}")
    print()

    issues = validate_config()
    if issues:
        print("Configuration Issues:")
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ All configuration looks good!")
        print()

    print("Example URLs:")
    print(f"  Short URL: {get_short_url('ABC123')}")
    print(f"  Soul URL: {get_soul_url('alice')}")
    print()
