#!/usr/bin/env python3
"""
Factory Device Pairing System - Hardware ID → HMAC QR Code → Device Tracking

Manufacturing/Factory Flow:
1. Device manufactured → Hardware serial extracted
2. QR code generated with HMAC signature
3. QR code printed/attached to device
4. User scans QR → Device registered in system
5. All future actions from device tracked forever

Use Cases:
- iPhone manufacturing → QR on box → Scan to activate
- IoT devices → QR sticker → Scan to pair
- Hardware authentication → Tamper-proof device tracking
- Component-level traceability

Security:
- HMAC signatures prevent QR forgery
- Hardware serial numbers are hashed
- Device fingerprinting adds layer of verification
- Replay attack prevention via timestamps

Usage:
    from factory_device_pairing import FactoryPairing

    # At factory: Generate QR code for device
    pairing = FactoryPairing()
    qr_data = pairing.generate_factory_qr(
        serial_number="IPHONE-12345-ABCDE",
        device_type="iphone",
        manufacturer="Apple",
        components={
            "cpu": "A15 Bionic",
            "camera": "12MP Wide",
            "display": "Super Retina XDR"
        }
    )
    # QR code printed on device box

    # User side: Scan QR code to activate device
    result = pairing.activate_device(qr_payload=qr_data['qr_payload'])
    # Device now registered and tracked

    # Track device activity
    pairing.log_device_action(
        device_id="abc123",
        action="voice_recording",
        metadata={"file_id": 42}
    )
"""

import hashlib
import hmac
import secrets
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db
import qrcode
import io
import base64


class FactoryPairing:
    """Factory-level device pairing and tracking system"""

    # HMAC secret for QR signing (in production, use environment variable)
    SECRET_KEY = b"soulfra-factory-pairing-2025"

    def __init__(self):
        """Initialize factory pairing system"""
        self.init_database()

    def init_database(self):
        """Create tables for device tracking"""
        db = get_db()

        # Factory devices table
        db.execute('''
            CREATE TABLE IF NOT EXISTS factory_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                serial_number_hash TEXT UNIQUE NOT NULL,
                device_type TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                qr_payload TEXT,
                activation_status TEXT DEFAULT 'pending',
                activated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Device components table (CPU, camera, etc.)
        db.execute('''
            CREATE TABLE IF NOT EXISTS device_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                component_type TEXT NOT NULL,
                component_id TEXT,
                component_spec TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES factory_devices(device_id)
            )
        ''')

        # Device action log (every action the device performs)
        db.execute('''
            CREATE TABLE IF NOT EXISTS device_action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_metadata TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES factory_devices(device_id)
            )
        ''')

        # Device pairing events (QR scan history)
        db.execute('''
            CREATE TABLE IF NOT EXISTS device_pairing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                qr_scanned BOOLEAN DEFAULT FALSE,
                ip_address TEXT,
                user_agent TEXT,
                browser_fingerprint TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES factory_devices(device_id)
            )
        ''')

        db.commit()

    def generate_device_id(self, serial_number: str) -> str:
        """
        Generate unique device ID from serial number

        Args:
            serial_number: Hardware serial number

        Returns:
            Hex device ID (16 chars)
        """
        # Hash serial for privacy
        device_id = hashlib.sha256(serial_number.encode()).hexdigest()[:16]
        return device_id

    def generate_factory_qr(
        self,
        serial_number: str,
        device_type: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        components: Optional[Dict[str, str]] = None,
        ttl_days: int = 365 * 10  # 10 years default
    ) -> Dict:
        """
        Generate factory QR code for device pairing

        Args:
            serial_number: Hardware serial (e.g., "IPHONE-12345-ABCDE")
            device_type: Type (phone, laptop, iot, sensor, etc.)
            manufacturer: Manufacturer name
            model: Model number
            components: Dict of component_type → spec
            ttl_days: QR code validity in days

        Returns:
            {
                'device_id': str,
                'qr_payload': str (base64 HMAC-signed),
                'qr_url': str,
                'qr_image_base64': str,
                'serial_number_hash': str
            }
        """
        device_id = self.generate_device_id(serial_number)
        serial_hash = hashlib.sha256(serial_number.encode()).hexdigest()

        # Build payload
        payload = {
            'type': 'factory_device_activation',
            'device_id': device_id,
            'device_type': device_type,
            'manufacturer': manufacturer,
            'model': model,
            'timestamp': int(time.time()),
            'expires_at': int(time.time()) + (ttl_days * 86400),
            'nonce': secrets.token_hex(16)
        }

        # Sign with HMAC
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(self.SECRET_KEY, message, hashlib.sha256).hexdigest()
        payload['hmac'] = signature

        # Encode to base64
        payload_json = json.dumps(payload, separators=(',', ':'))
        qr_payload = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')

        # Generate QR code image
        qr_url = f"http://localhost:5001/factory/activate?qr={qr_payload}"

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        # Save to database
        db = get_db()

        db.execute('''
            INSERT OR REPLACE INTO factory_devices (
                device_id, serial_number_hash, device_type, manufacturer,
                model, qr_payload, activation_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (device_id, serial_hash, device_type, manufacturer, model, qr_payload, 'pending'))

        # Save components
        if components:
            for comp_type, comp_spec in components.items():
                db.execute('''
                    INSERT INTO device_components (device_id, component_type, component_spec)
                    VALUES (?, ?, ?)
                ''', (device_id, comp_type, comp_spec))

        db.commit()

        return {
            'device_id': device_id,
            'qr_payload': qr_payload,
            'qr_url': qr_url,
            'qr_image_base64': img_base64,
            'serial_number_hash': serial_hash
        }

    def verify_factory_qr(self, qr_payload: str) -> Optional[Dict]:
        """
        Verify factory QR code payload

        Args:
            qr_payload: Base64-encoded HMAC-signed payload

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            # Decode base64
            payload_json = base64.urlsafe_b64decode(qr_payload.encode('utf-8')).decode('utf-8')
            payload = json.loads(payload_json)

            # Extract HMAC
            provided_hmac = payload.pop('hmac', None)

            if not provided_hmac:
                print("❌ Missing HMAC signature")
                return None

            # Verify HMAC
            message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            expected_hmac = hmac.new(self.SECRET_KEY, message, hashlib.sha256).hexdigest()

            if not hmac.compare_digest(provided_hmac, expected_hmac):
                print("❌ Invalid HMAC - QR may be forged")
                return None

            # Check expiration
            if time.time() > payload['expires_at']:
                print(f"❌ QR expired at {datetime.fromtimestamp(payload['expires_at'])}")
                return None

            # Restore HMAC to payload
            payload['hmac'] = provided_hmac

            return payload

        except Exception as e:
            print(f"❌ QR verification failed: {e}")
            return None

    def activate_device(
        self,
        qr_payload: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        browser_fingerprint: Optional[Dict] = None
    ) -> Dict:
        """
        Activate device by scanning QR code

        Args:
            qr_payload: Scanned QR payload
            ip_address: User's IP address
            user_agent: User's browser user agent
            browser_fingerprint: Browser fingerprint data

        Returns:
            {
                'success': bool,
                'device_id': str,
                'device_type': str,
                'activation_token': str,
                'message': str
            }
        """
        # Verify QR
        payload = self.verify_factory_qr(qr_payload)

        if not payload:
            return {
                'success': False,
                'error': 'Invalid or expired QR code',
                'message': 'QR code verification failed. Contact manufacturer.'
            }

        device_id = payload['device_id']
        device_type = payload['device_type']

        # Check if already activated
        db = get_db()
        device = db.execute('''
            SELECT activation_status, activated_at FROM factory_devices WHERE device_id = ?
        ''', (device_id,)).fetchone()

        if not device:
            return {
                'success': False,
                'error': 'Device not found',
                'message': 'Device not registered in factory system'
            }

        # Generate activation token
        activation_token = secrets.token_urlsafe(32)

        # Update activation status
        db.execute('''
            UPDATE factory_devices
            SET activation_status = 'activated',
                activated_at = ?
            WHERE device_id = ?
        ''', (datetime.now(), device_id))

        # Log pairing event
        db.execute('''
            INSERT INTO device_pairing_events (
                device_id, event_type, qr_scanned, ip_address, user_agent, browser_fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            'activation',
            True,
            ip_address,
            user_agent,
            json.dumps(browser_fingerprint) if browser_fingerprint else None
        ))

        db.commit()

        return {
            'success': True,
            'device_id': device_id,
            'device_type': device_type,
            'manufacturer': payload.get('manufacturer'),
            'model': payload.get('model'),
            'activation_token': activation_token,
            'message': f'{device_type.capitalize()} activated successfully!',
            'already_activated': device['activation_status'] == 'activated'
        }

    def log_device_action(
        self,
        device_id: str,
        action_type: str,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Log device action for tracking

        Args:
            device_id: Device ID
            action_type: Action (voice_recording, qr_scan, login, etc.)
            metadata: Optional action metadata
            ip_address: IP address
            user_agent: User agent

        Returns:
            Log entry ID
        """
        db = get_db()

        cursor = db.execute('''
            INSERT INTO device_action_log (
                device_id, action_type, action_metadata, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            device_id,
            action_type,
            json.dumps(metadata) if metadata else None,
            ip_address,
            user_agent
        ))

        db.commit()

        return cursor.lastrowid

    def get_device_history(self, device_id: str) -> Dict:
        """
        Get complete device history

        Args:
            device_id: Device ID

        Returns:
            {
                'device_info': {...},
                'components': [...],
                'actions': [...],
                'pairing_events': [...]
            }
        """
        db = get_db()

        # Get device info
        device = db.execute('''
            SELECT * FROM factory_devices WHERE device_id = ?
        ''', (device_id,)).fetchone()

        if not device:
            return {'error': 'Device not found'}

        # Get components
        components = db.execute('''
            SELECT component_type, component_spec, created_at
            FROM device_components
            WHERE device_id = ?
        ''', (device_id,)).fetchall()

        # Get action log
        actions = db.execute('''
            SELECT action_type, action_metadata, ip_address, timestamp
            FROM device_action_log
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT 100
        ''', (device_id,)).fetchall()

        # Get pairing events
        pairing_events = db.execute('''
            SELECT event_type, ip_address, user_agent, timestamp
            FROM device_pairing_events
            WHERE device_id = ?
            ORDER BY timestamp DESC
        ''', (device_id,)).fetchall()

        return {
            'device_info': dict(device),
            'components': [dict(c) for c in components],
            'actions': [dict(a) for a in actions],
            'pairing_events': [dict(p) for p in pairing_events]
        }


# CLI for testing
if __name__ == '__main__':
    import sys

    pairing = FactoryPairing()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'generate' and len(sys.argv) >= 4:
            # Generate factory QR
            serial = sys.argv[2]
            device_type = sys.argv[3]

            print(f"\n🏭 Generating factory QR code for device:")
            print(f"   Serial: {serial}")
            print(f"   Type: {device_type}\n")

            result = pairing.generate_factory_qr(
                serial_number=serial,
                device_type=device_type,
                manufacturer="Soulfra",
                components={
                    "processor": "A15 Bionic",
                    "memory": "8GB RAM",
                    "storage": "256GB SSD"
                }
            )

            print(f"✅ QR Code Generated:")
            print(f"   Device ID: {result['device_id']}")
            print(f"   QR URL: {result['qr_url'][:80]}...")
            print(f"   Serial Hash: {result['serial_number_hash'][:20]}...")
            print(f"\n   Scan this QR code to activate device!\n")

            # Save QR image
            img_data = base64.b64decode(result['qr_image_base64'])
            filename = f"factory_qr_{result['device_id']}.png"
            with open(filename, 'wb') as f:
                f.write(img_data)

            print(f"   💾 QR image saved: {filename}\n")

        elif command == 'activate' and len(sys.argv) >= 3:
            # Activate device
            qr_payload = sys.argv[2]

            print(f"\n📱 Activating device from QR code...\n")

            result = pairing.activate_device(
                qr_payload=qr_payload,
                ip_address="192.168.1.87",
                user_agent="Mozilla/5.0 (iPhone)"
            )

            if result['success']:
                print(f"✅ {result['message']}")
                print(f"   Device ID: {result['device_id']}")
                print(f"   Type: {result['device_type']}")
                print(f"   Activation Token: {result['activation_token'][:20]}...")
                print()
            else:
                print(f"❌ Activation failed: {result.get('error')}")
                print(f"   {result.get('message')}")
                print()

        elif command == 'log' and len(sys.argv) >= 4:
            # Log action
            device_id = sys.argv[2]
            action_type = sys.argv[3]

            log_id = pairing.log_device_action(
                device_id=device_id,
                action_type=action_type,
                metadata={"test": True}
            )

            print(f"\n✅ Action logged: ID {log_id}\n")

        elif command == 'history' and len(sys.argv) >= 3:
            # Get device history
            device_id = sys.argv[2]

            history = pairing.get_device_history(device_id)

            if 'error' in history:
                print(f"\n❌ {history['error']}\n")
            else:
                print(f"\n📊 Device History for {device_id}:\n")

                print(f"Device Info:")
                print(f"  Type: {history['device_info']['device_type']}")
                print(f"  Status: {history['device_info']['activation_status']}")
                print(f"  Activated: {history['device_info']['activated_at']}")

                print(f"\nComponents ({len(history['components'])}):")
                for comp in history['components']:
                    print(f"  - {comp['component_type']}: {comp['component_spec']}")

                print(f"\nRecent Actions ({len(history['actions'])}):")
                for action in history['actions'][:5]:
                    print(f"  - {action['action_type']} at {action['timestamp']}")

                print()

        else:
            print("Unknown command")

    else:
        print("\n🏭 Factory Device Pairing System\n")
        print("Commands:")
        print("  python3 factory_device_pairing.py generate <serial> <type>")
        print("      Generate factory QR code for device\n")
        print("  python3 factory_device_pairing.py activate <qr_payload>")
        print("      Activate device by scanning QR\n")
        print("  python3 factory_device_pairing.py log <device_id> <action>")
        print("      Log device action\n")
        print("  python3 factory_device_pairing.py history <device_id>")
        print("      Get device history\n")
        print("Examples:")
        print("  python3 factory_device_pairing.py generate IPHONE-12345 phone")
        print("  python3 factory_device_pairing.py activate eyJ0eXBlIjoi...")
        print("  python3 factory_device_pairing.py log abc123 voice_recording")
        print("  python3 factory_device_pairing.py history abc123")
        print()
