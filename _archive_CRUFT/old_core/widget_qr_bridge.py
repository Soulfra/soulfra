#!/usr/bin/env python3
"""
Widget QR Bridge - Connect Chatbox Widget to QR Code System

Connects the embeddable chat widget (EMBEDDABLE_WIDGET.md) with QR codes:
- Widget can display QR codes
- Widget can trigger QR scans
- QR scans can open widget
- Practice rooms use widget + QR

Use Cases:
1. Widget shows QR to join chat
2. Scan QR → Opens widget automatically
3. Practice room: QR + widget combined
4. User profile: Widget with QR share button

Usage:
    from widget_qr_bridge import WidgetQRBridge

    # Initialize bridge
    bridge = WidgetQRBridge()

    # Generate widget with QR
    widget_config = bridge.generate_widget_with_qr(
        target_url='/practice/room/abc123'
    )

    # Handle QR scan → Open widget
    bridge.handle_qr_scan(qr_payload, device_fingerprint)
"""

import json
from typing import Dict, Optional, List
from database import get_db


class WidgetQRBridge:
    """Bridge between chat widget and QR code system"""

    def __init__(self, base_url: str = None):
        """
        Initialize bridge

        Args:
            base_url: Base URL for QR codes
        """
        if base_url is None:
            try:
                from config import BASE_URL
                self.base_url = BASE_URL
            except:
                self.base_url = 'http://localhost:5001'

    def generate_widget_with_qr(self, target_url: str,
                               widget_title: str = "Join Chat",
                               qr_prompt: str = "Scan to join from phone") -> Dict:
        """
        Generate widget configuration with embedded QR code

        Args:
            target_url: URL to open when QR scanned
            widget_title: Widget title
            qr_prompt: Text shown above QR

        Returns:
            Widget configuration with QR code
        """
        from qr_faucet import generate_qr_payload

        # Generate QR payload
        qr_payload = generate_qr_payload(
            'widget_join',
            {
                'target_url': target_url,
                'action': 'open_widget'
            },
            ttl_seconds=86400  # 24 hours
        )

        qr_url = f"/qr/faucet/{qr_payload}"
        full_qr_url = f"{self.base_url}{qr_url}"

        # Generate QR image
        try:
            import qrcode
            from io import BytesIO
            import base64

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(full_qr_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            qr_image = f"data:image/png;base64,{img_base64}"
        except:
            qr_image = None

        # Widget configuration
        widget_config = {
            'widget': {
                'title': widget_title,
                'apiEndpoint': self.base_url,
                'position': 'bottom-right',
                'primaryColor': '#667eea',
                'showQR': True,
                'qrConfig': {
                    'prompt': qr_prompt,
                    'url': full_qr_url,
                    'image': qr_image
                }
            },
            'qr_payload': qr_payload,
            'target_url': target_url
        }

        return widget_config

    def handle_qr_scan(self, encoded_payload: str, device_fingerprint: Dict) -> Dict:
        """
        Handle QR scan that should open widget

        Args:
            encoded_payload: QR payload
            device_fingerprint: Device info

        Returns:
            Action to take (open widget, redirect, etc.)
        """
        from qr_faucet import verify_qr_payload

        # Verify payload
        payload = verify_qr_payload(encoded_payload)

        if not payload:
            return {'success': False, 'error': 'Invalid QR code'}

        # Check if this is a widget QR
        if payload.get('type') == 'widget_join':
            data = payload.get('data', {})
            target_url = data.get('target_url')

            return {
                'success': True,
                'action': 'open_widget',
                'target_url': target_url,
                'widget_config': {
                    'autoOpen': True,
                    'initialUrl': target_url
                }
            }

        return {'success': False, 'error': 'Not a widget QR code'}

    def generate_practice_room_widget(self, room_id: str) -> Dict:
        """
        Generate widget for practice room

        Args:
            room_id: Practice room ID

        Returns:
            Widget configuration for room
        """
        room_url = f"/practice/room/{room_id}"

        return self.generate_widget_with_qr(
            target_url=room_url,
            widget_title="Join Practice Room",
            qr_prompt="Scan to join from phone"
        )

    def generate_user_profile_widget(self, username: str) -> Dict:
        """
        Generate widget for user profile

        Args:
            username: Username

        Returns:
            Widget configuration for user
        """
        profile_url = f"/user/{username}"

        return self.generate_widget_with_qr(
            target_url=profile_url,
            widget_title=f"Chat with {username}",
            qr_prompt=f"Scan to view {username}'s profile"
        )

    def embed_code(self, widget_config: Dict) -> str:
        """
        Generate HTML embed code for widget with QR

        Args:
            widget_config: Widget configuration

        Returns:
            HTML/JavaScript embed code
        """
        config_json = json.dumps(widget_config['widget'], indent=2)

        embed_code = f"""<!-- Soulfra Widget with QR Code -->
<div id="soulfra-widget-container"></div>
<script src="{self.base_url}/static/widget-embed.js"></script>
<script>
  SoulWidget.init({config_json});
</script>

<!-- Optional: Show QR code in widget -->
<style>
  #soulfra-qr-display {{
    text-align: center;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
    margin: 10px 0;
  }}
  #soulfra-qr-display img {{
    max-width: 200px;
    height: auto;
  }}
</style>
"""

        return embed_code

    def get_widget_analytics(self, widget_id: Optional[str] = None) -> Dict:
        """
        Get analytics for widget usage

        Args:
            widget_id: Optional widget ID to filter

        Returns:
            Analytics data
        """
        db = get_db()

        # Create analytics table if needed
        db.execute('''
            CREATE TABLE IF NOT EXISTS widget_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                widget_id TEXT,
                event_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_fingerprint TEXT,
                metadata TEXT
            )
        ''')

        # Get stats
        if widget_id:
            stats = db.execute('''
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT device_fingerprint) as unique_devices,
                    event_type,
                    COUNT(*) as event_count
                FROM widget_analytics
                WHERE widget_id = ?
                GROUP BY event_type
            ''', (widget_id,)).fetchall()
        else:
            stats = db.execute('''
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT device_fingerprint) as unique_devices
                FROM widget_analytics
            ''').fetchone()

        return {
            'total_events': stats['total_events'] if stats else 0,
            'unique_devices': stats['unique_devices'] if stats else 0
        }


# Flask integration
def add_widget_qr_routes(app):
    """
    Add widget+QR routes to Flask app

    Usage:
        from widget_qr_bridge import add_widget_qr_routes
        add_widget_qr_routes(app)
    """
    from flask import render_template, jsonify, request

    bridge = WidgetQRBridge()

    @app.route('/api/widget/qr/<path:target>')
    def widget_qr_api(target):
        """Generate widget with QR for target URL"""
        config = bridge.generate_widget_with_qr(f"/{target}")
        return jsonify(config)

    @app.route('/api/widget/practice/<room_id>')
    def widget_practice_room(room_id):
        """Get widget for practice room"""
        config = bridge.generate_practice_room_widget(room_id)
        return jsonify(config)

    @app.route('/api/widget/user/<username>')
    def widget_user_profile(username):
        """Get widget for user profile"""
        config = bridge.generate_user_profile_widget(username)
        return jsonify(config)

    @app.route('/api/widget/embed')
    def widget_embed_code():
        """Get embed code"""
        target = request.args.get('target', '/')
        config = bridge.generate_widget_with_qr(target)
        embed = bridge.embed_code(config)

        return jsonify({'embed_code': embed})


# CLI for testing
if __name__ == '__main__':
    import sys

    print("Widget QR Bridge - Connect Chat Widget to QR Codes\n")

    bridge = WidgetQRBridge()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'generate' and len(sys.argv) >= 3:
            # Generate widget with QR
            target_url = sys.argv[2]
            title = sys.argv[3] if len(sys.argv) > 3 else "Join Chat"

            config = bridge.generate_widget_with_qr(target_url, widget_title=title)

            print(f"✓ Generated widget with QR")
            print(f"  Target: {config['target_url']}")
            print(f"  Title: {config['widget']['title']}")
            print(f"  QR Image: {'✓' if config['widget']['qrConfig']['image'] else '✗'}")
            print(f"\nWidget Config:")
            print(json.dumps(config['widget'], indent=2))

        elif command == 'practice' and len(sys.argv) >= 3:
            # Generate for practice room
            room_id = sys.argv[2]

            config = bridge.generate_practice_room_widget(room_id)

            print(f"✓ Generated practice room widget")
            print(f"  Room ID: {room_id}")
            print(f"  Target: {config['target_url']}")

        elif command == 'user' and len(sys.argv) >= 3:
            # Generate for user
            username = sys.argv[2]

            config = bridge.generate_user_profile_widget(username)

            print(f"✓ Generated user profile widget")
            print(f"  Username: {username}")
            print(f"  Target: {config['target_url']}")

        elif command == 'embed' and len(sys.argv) >= 3:
            # Generate embed code
            target_url = sys.argv[2]

            config = bridge.generate_widget_with_qr(target_url)
            embed = bridge.embed_code(config)

            print("Embed Code:")
            print(embed)

        else:
            print("Unknown command")

    else:
        print("Widget QR Bridge Commands:\n")
        print("  python3 widget_qr_bridge.py generate <target_url> [title]")
        print("      Generate widget with QR\n")
        print("  python3 widget_qr_bridge.py practice <room_id>")
        print("      Generate for practice room\n")
        print("  python3 widget_qr_bridge.py user <username>")
        print("      Generate for user profile\n")
        print("  python3 widget_qr_bridge.py embed <target_url>")
        print("      Get embed code\n")
        print("Examples:")
        print("  python3 widget_qr_bridge.py generate /practice/room/abc123 'Join Room'")
        print("  python3 widget_qr_bridge.py practice abc123")
        print("  python3 widget_qr_bridge.py user alice")
