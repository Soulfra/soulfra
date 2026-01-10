#!/usr/bin/env python3
"""
SSL Local Server - Self-Signed HTTPS for Development

Generates self-signed SSL certificates for local development so you can:
- Use microphone on iPhone/mobile (requires HTTPS)
- Test voice recording at https://192.168.1.87:5001/voice
- Run Flask with SSL enabled

Usage:
    # Generate certificate
    python3 ssl_local_server.py --generate

    # Start Flask with HTTPS
    python3 ssl_local_server.py --serve

    # One command (generate + serve)
    python3 ssl_local_server.py --auto

On iPhone:
    1. Visit https://192.168.1.87:5001/voice
    2. Accept security warning (self-signed cert)
    3. Microphone will now work!

Certificate valid for:
- localhost
- 127.0.0.1
- 192.168.1.87 (your local IP)
- 0.0.0.0

Security Note:
- Self-signed certs are ONLY for local development
- Browser will show security warning (this is expected)
- For production, use Let's Encrypt or similar
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional


# ==============================================================================
# CONFIG
# ==============================================================================

CERT_DIR = Path('./ssl_certs')
CERT_FILE = CERT_DIR / 'cert.pem'
KEY_FILE = CERT_DIR / 'key.pem'
CERT_VALIDITY_DAYS = 365


# ==============================================================================
# SSL CERTIFICATE GENERATOR
# ==============================================================================

def get_local_ip() -> str:
    """Get local network IP address"""
    import socket
    try:
        # Create dummy socket to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.87"  # Fallback to your known IP


def generate_self_signed_cert(
    cert_file: Path = CERT_FILE,
    key_file: Path = KEY_FILE,
    validity_days: int = CERT_VALIDITY_DAYS,
    local_ip: Optional[str] = None
) -> bool:
    """
    Generate self-signed SSL certificate using openssl

    Args:
        cert_file: Output certificate file
        key_file: Output private key file
        validity_days: Certificate validity in days
        local_ip: Local IP address (auto-detected if None)

    Returns:
        True if successful
    """
    if local_ip is None:
        local_ip = get_local_ip()

    print(f"\n🔐 Generating Self-Signed SSL Certificate")
    print(f"{'='*70}")
    print(f"Certificate: {cert_file}")
    print(f"Private Key: {key_file}")
    print(f"Valid for: {validity_days} days")
    print(f"Local IP: {local_ip}")
    print(f"{'='*70}\n")

    # Create directory
    cert_file.parent.mkdir(parents=True, exist_ok=True)

    # Create OpenSSL config for Subject Alternative Names (SAN)
    # This allows the cert to work for multiple hostnames/IPs
    config_file = cert_file.parent / 'openssl.cnf'

    config_content = f"""
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C = US
ST = Development
L = Localhost
O = Soulfra
OU = Development
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = {local_ip}
IP.3 = 0.0.0.0
"""

    config_file.write_text(config_content.strip())

    # Generate certificate using openssl
    cmd = [
        'openssl', 'req',
        '-x509',
        '-newkey', 'rsa:2048',
        '-keyout', str(key_file),
        '-out', str(cert_file),
        '-days', str(validity_days),
        '-nodes',  # No password
        '-config', str(config_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print("✅ Certificate generated successfully!\n")
        print(f"Certificate Info:")

        # Show certificate details
        info_cmd = ['openssl', 'x509', '-in', str(cert_file), '-text', '-noout']
        info_result = subprocess.run(info_cmd, capture_output=True, text=True)

        # Extract relevant info
        info_lines = info_result.stdout.split('\n')
        for line in info_lines:
            if 'Subject:' in line or 'Not Before' in line or 'Not After' in line or 'DNS:' in line or 'IP Address:' in line:
                print(f"  {line.strip()}")

        print(f"\n{'='*70}")
        print(f"📱 iPhone Setup Instructions:")
        print(f"{'='*70}")
        print(f"1. On iPhone, visit: https://{local_ip}:5001/voice")
        print(f"2. Tap 'Advanced' or 'Show Details'")
        print(f"3. Tap 'Visit this website' or 'Proceed'")
        print(f"4. Microphone access will now work!")
        print(f"\nNote: You'll see a security warning (expected for self-signed certs)")
        print(f"{'='*70}\n")

        # Clean up config
        config_file.unlink()

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate certificate:")
        print(f"   {e.stderr}")
        return False

    except FileNotFoundError:
        print(f"❌ OpenSSL not found!")
        print(f"   Install: brew install openssl  (macOS)")
        print(f"   Install: apt install openssl   (Linux)")
        return False


def check_certificate_exists() -> bool:
    """Check if certificate files exist"""
    return CERT_FILE.exists() and KEY_FILE.exists()


def get_certificate_info() -> dict:
    """Get info about existing certificate"""
    if not check_certificate_exists():
        return {'exists': False}

    try:
        # Get certificate expiry
        cmd = [
            'openssl', 'x509',
            '-in', str(CERT_FILE),
            '-noout',
            '-enddate'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse expiry date: "notAfter=Jan  3 01:23:45 2027 GMT"
        expiry_str = result.stdout.strip().split('=')[1]

        return {
            'exists': True,
            'cert_file': str(CERT_FILE),
            'key_file': str(KEY_FILE),
            'expiry': expiry_str
        }
    except Exception as e:
        return {'exists': True, 'error': str(e)}


# ==============================================================================
# FLASK SSL SERVER
# ==============================================================================

def serve_flask_with_ssl(
    host: str = '0.0.0.0',
    port: int = 5001,
    cert_file: Path = CERT_FILE,
    key_file: Path = KEY_FILE
):
    """
    Start Flask app with SSL enabled

    Args:
        host: Host to bind (0.0.0.0 = all interfaces)
        port: Port number
        cert_file: SSL certificate file
        key_file: SSL private key file
    """
    if not check_certificate_exists():
        print("❌ Certificate not found!")
        print("   Run: python3 ssl_local_server.py --generate")
        return

    local_ip = get_local_ip()

    print(f"\n🚀 Starting Flask with HTTPS")
    print(f"{'='*70}")
    print(f"HTTPS URLs:")
    print(f"  • https://localhost:{port}/voice")
    print(f"  • https://127.0.0.1:{port}/voice")
    print(f"  • https://{local_ip}:{port}/voice  ← Use this on iPhone!")
    print(f"{'='*70}")
    print(f"\nCertificate: {cert_file}")
    print(f"Private Key: {key_file}")
    print(f"\nStarting server...\n")

    # Import Flask app
    try:
        from app import app

        # Run with SSL context
        app.run(
            host=host,
            port=port,
            ssl_context=(str(cert_file), str(key_file)),
            debug=False,
            threaded=True
        )

    except ImportError:
        print("❌ Could not import Flask app from app.py")
        print("   Make sure app.py exists in the current directory")

    except Exception as e:
        print(f"❌ Server error: {e}")


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='SSL Local Server - Self-Signed HTTPS for Development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate certificate
  python3 ssl_local_server.py --generate

  # Start HTTPS server
  python3 ssl_local_server.py --serve

  # Generate + serve
  python3 ssl_local_server.py --auto

  # Check certificate status
  python3 ssl_local_server.py --info
        """
    )

    parser.add_argument(
        '--generate', '-g',
        action='store_true',
        help='Generate self-signed SSL certificate'
    )

    parser.add_argument(
        '--serve', '-s',
        action='store_true',
        help='Start Flask with HTTPS'
    )

    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='Generate certificate and start server'
    )

    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Show certificate information'
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5001,
        help='Port number (default: 5001)'
    )

    parser.add_argument(
        '--ip',
        type=str,
        default=None,
        help='Local IP address (auto-detected if not specified)'
    )

    args = parser.parse_args()

    # Default to showing help
    if not any([args.generate, args.serve, args.auto, args.info]):
        parser.print_help()
        print("\n" + "="*70)
        print("Quick Start:")
        print("  python3 ssl_local_server.py --auto")
        print("="*70 + "\n")
        return

    try:
        if args.info:
            # Show certificate info
            info = get_certificate_info()

            print(f"\n📋 Certificate Status")
            print(f"{'='*70}")

            if info.get('exists'):
                print(f"✅ Certificate exists")
                print(f"   Certificate: {info.get('cert_file')}")
                print(f"   Private Key: {info.get('key_file')}")

                if 'expiry' in info:
                    print(f"   Expires: {info['expiry']}")

                if 'error' in info:
                    print(f"   ⚠️  Error reading: {info['error']}")
            else:
                print(f"❌ Certificate not found")
                print(f"   Run: python3 ssl_local_server.py --generate")

            print(f"{'='*70}\n")

        if args.generate or args.auto:
            # Generate certificate
            success = generate_self_signed_cert(
                cert_file=CERT_FILE,
                key_file=KEY_FILE,
                local_ip=args.ip
            )

            if not success:
                sys.exit(1)

        if args.serve or args.auto:
            # Start server
            serve_flask_with_ssl(
                host='0.0.0.0',
                port=args.port,
                cert_file=CERT_FILE,
                key_file=KEY_FILE
            )

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
