#!/usr/bin/env python3
"""Initialize QR authentication database table"""

from qr_auth import QRAuthManager

print("Initializing QR authentication database...")
manager = QRAuthManager()
print("✅ Database initialized successfully!")
print("\nTable 'qr_auth_tokens' created with schema:")
print("  - id (PRIMARY KEY)")
print("  - token (UNIQUE)")
print("  - user_id (FOREIGN KEY)")
print("  - device_fingerprint")
print("  - expires_at")
print("  - used")
print("  - used_at")
print("  - created_at")
print("\nQR login is now ready to use at /login-qr")
