#!/usr/bin/env python3
"""
User Profile QR Codes - Scan to Visit Someone's Page

Generate QR codes that link to user profiles.
Like business cards but digital - scan someone's QR to visit their page!

Use Cases:
1. Business cards: Print QR, people scan to see your profile
2. Event networking: Show QR on phone, others scan to connect
3. Social media: Share QR instead of username
4. Profile sharing: Embed QR in email signature

Usage:
    from qr_user_profile import generate_user_qr, get_user_qr_url

    # Generate QR for user
    qr_data = generate_user_qr('alice')

    # Get URL
    url = get_user_qr_url('alice')
    # Returns: http://localhost:5001/qr/user/alice

Flow:
    User visits: /user/alice
        ↓
    Page displays QR code
        ↓
    Someone scans with phone
        ↓
    Opens: /qr/faucet/eyJ0eXBlIjoidXNlcl9wcm9maWxlIi4uLg==
        ↓
    Server decodes → Redirects to /user/alice
        ↓
    Visitor sees Alice's profile!
"""

from typing import Dict, Optional
from pathlib import Path
import json


def generate_user_qr(username: str, base_url: str = None) -> Dict:
    """
    Generate QR code for user profile

    Args:
        username: Username
        base_url: Base URL (defaults to config.BASE_URL)

    Returns:
        Dict with QR data:
        {
            'encoded_payload': '...',
            'qr_url': '/qr/faucet/...',
            'profile_url': '/user/alice',
            'full_url': 'http://localhost:5001/user/alice',
            'qr_image_base64': 'data:image/png;base64,...' (if qrcode available)
        }
    """
    from qr_faucet import generate_qr_payload

    if base_url is None:
        try:
            from config import BASE_URL
            base_url = BASE_URL
        except:
            base_url = 'http://localhost:5001'

    # Generate QR payload
    encoded = generate_qr_payload(
        payload_type='user_profile',
        data={
            'username': username,
            'type': 'profile_visit'
        },
        ttl_seconds=31536000  # 1 year (semi-permanent link)
    )

    qr_url = f"/qr/faucet/{encoded}"
    profile_url = f"/user/{username}"
    full_url = f"{base_url}{profile_url}"

    result = {
        'encoded_payload': encoded,
        'qr_url': qr_url,
        'profile_url': profile_url,
        'full_url': full_url,
        'username': username
    }

    # Generate QR image if qrcode library available
    try:
        import qrcode
        from io import BytesIO
        import base64

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Use full URL for scanning
        qr.add_data(full_url)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        result['qr_image_base64'] = f"data:image/png;base64,{img_base64}"
        result['has_image'] = True

    except ImportError:
        result['has_image'] = False

    return result


def get_user_qr_url(username: str, base_url: str = None) -> str:
    """
    Get QR code URL for user

    Args:
        username: Username
        base_url: Base URL

    Returns:
        Full URL to QR code endpoint
    """
    if base_url is None:
        try:
            from config import BASE_URL
            base_url = BASE_URL
        except:
            base_url = 'http://localhost:5001'

    return f"{base_url}/qr/user/{username}"


def get_user_qr_stats(username: str) -> Dict:
    """
    Get QR scan statistics for user

    Args:
        username: Username

    Returns:
        Dict with stats:
        {
            'total_scans': 42,
            'unique_devices': 15,
            'recent_scans': [...]
        }
    """
    from database import get_db

    db = get_db()

    # Get user QR scans
    scans = db.execute('''
        SELECT
            COUNT(*) as total_scans,
            COUNT(DISTINCT device_fingerprint) as unique_devices
        FROM qr_faucet_scans s
        JOIN qr_faucets f ON s.faucet_id = f.id
        WHERE f.payload_data LIKE ?
    ''', (f'%"username":"{username}"%',)).fetchone()

    # Get recent scans
    recent = db.execute('''
        SELECT
            s.scanned_at,
            s.ip_address,
            s.device_type
        FROM qr_faucet_scans s
        JOIN qr_faucets f ON s.faucet_id = f.id
        WHERE f.payload_data LIKE ?
        ORDER BY s.scanned_at DESC
        LIMIT 10
    ''', (f'%"username":"{username}"%',)).fetchall()

    return {
        'total_scans': scans['total_scans'] if scans else 0,
        'unique_devices': scans['unique_devices'] if scans else 0,
        'recent_scans': [dict(r) for r in recent] if recent else []
    }


def generate_user_vcard_qr(username: str, full_name: str = None,
                           email: str = None, phone: str = None) -> Dict:
    """
    Generate QR code with vCard format for contact import

    Args:
        username: Username
        full_name: Full name (optional)
        email: Email (optional)
        phone: Phone (optional)

    Returns:
        QR data with vCard format
    """
    from qr_faucet import generate_qr_payload

    # Create vCard data
    vcard_data = f"""BEGIN:VCARD
VERSION:3.0
FN:{full_name or username}
URL:{get_user_qr_url(username)}
"""

    if email:
        vcard_data += f"EMAIL:{email}\n"
    if phone:
        vcard_data += f"TEL:{phone}\n"

    vcard_data += "END:VCARD"

    # Generate QR with vCard
    encoded = generate_qr_payload(
        payload_type='vcard',
        data={
            'username': username,
            'vcard': vcard_data
        },
        ttl_seconds=31536000
    )

    return {
        'encoded_payload': encoded,
        'vcard_data': vcard_data,
        'username': username
    }


# Flask integration helper
def add_user_qr_routes(app):
    """
    Add user QR routes to Flask app

    Usage:
        from qr_user_profile import add_user_qr_routes
        add_user_qr_routes(app)
    """
    from flask import render_template, Response, jsonify, redirect, url_for
    import qrcode
    from io import BytesIO

    @app.route('/qr/user/<username>')
    def user_qr_code(username):
        """Generate QR code image for user profile"""
        qr_data = generate_user_qr(username)

        if qr_data.get('has_image'):
            # Return as image
            import base64
            from io import BytesIO

            # Decode base64
            img_data = qr_data['qr_image_base64'].split(',')[1]
            img_bytes = base64.b64decode(img_data)

            return Response(
                img_bytes,
                mimetype='image/png',
                headers={'Content-Disposition': f'inline; filename={username}-qr.png'}
            )
        else:
            return jsonify({'error': 'QR code generation not available'}), 500

    @app.route('/api/qr/user/<username>')
    def user_qr_api(username):
        """Get user QR data as JSON"""
        qr_data = generate_user_qr(username)
        return jsonify(qr_data)

    @app.route('/api/qr/user/<username>/stats')
    def user_qr_stats_api(username):
        """Get QR scan stats for user"""
        stats = get_user_qr_stats(username)
        return jsonify(stats)


# CLI for testing
if __name__ == '__main__':
    import sys

    print("User Profile QR Codes\n")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'generate' and len(sys.argv) >= 3:
            # Generate QR for user
            username = sys.argv[2]
            qr_data = generate_user_qr(username)

            print(f"✓ Generated QR code for user: {username}")
            print(f"  Profile URL: {qr_data['profile_url']}")
            print(f"  Full URL: {qr_data['full_url']}")
            print(f"  QR URL: {qr_data['qr_url']}")

            if qr_data.get('has_image'):
                print(f"  Image: Available")

                # Save to file
                import base64
                img_data = qr_data['qr_image_base64'].split(',')[1]
                img_bytes = base64.b64decode(img_data)

                filename = f"{username}-profile-qr.png"
                with open(filename, 'wb') as f:
                    f.write(img_bytes)

                print(f"  Saved to: {filename}")

        elif command == 'stats' and len(sys.argv) >= 3:
            # Get stats
            username = sys.argv[2]
            stats = get_user_qr_stats(username)

            print(f"QR Stats for {username}:")
            print(f"  Total scans: {stats['total_scans']}")
            print(f"  Unique devices: {stats['unique_devices']}")

            if stats['recent_scans']:
                print(f"\n  Recent scans:")
                for scan in stats['recent_scans'][:5]:
                    print(f"    • {scan['scanned_at']} - {scan['device_type']} ({scan['ip_address']})")

        elif command == 'vcard' and len(sys.argv) >= 3:
            # Generate vCard QR
            username = sys.argv[2]
            full_name = sys.argv[3] if len(sys.argv) > 3 else None
            email = sys.argv[4] if len(sys.argv) > 4 else None

            vcard_qr = generate_user_vcard_qr(username, full_name, email)

            print(f"✓ Generated vCard QR for: {username}")
            print(f"\nvCard Data:")
            print(vcard_qr['vcard_data'])

        else:
            print("Unknown command")

    else:
        print("User Profile QR Commands:\n")
        print("  python3 qr_user_profile.py generate <username>")
        print("      Generate QR code for user\n")
        print("  python3 qr_user_profile.py stats <username>")
        print("      Get scan statistics\n")
        print("  python3 qr_user_profile.py vcard <username> [name] [email]")
        print("      Generate vCard QR\n")
        print("Examples:")
        print("  python3 qr_user_profile.py generate alice")
        print("  python3 qr_user_profile.py stats alice")
        print("  python3 qr_user_profile.py vcard alice 'Alice Smith' alice@example.com")
