#!/usr/bin/env python3
"""
QR Code Generator for Soulfra Triple Domain System

Generates QR code pointing to soulfraapi.com/qr-signup endpoint.
Saves QR code to Soulfra.com/qr-code.png for static site deployment.

Usage:
    python3 generate-qr.py              # Generate for localhost
    python3 generate-qr.py --prod       # Generate for production
"""

import sys
import os

try:
    import qrcode
except ImportError:
    print("❌ qrcode library not installed")
    print("Install with: pip3 install qrcode[pil]")
    sys.exit(1)

# Configuration
LOCALHOST_URL = "http://localhost:5002/qr-signup?ref=landing"
PRODUCTION_URL = "https://soulfraapi.com/qr-signup?ref=landing"

# Determine URL based on argument
if len(sys.argv) > 1 and sys.argv[1] == '--prod':
    URL = PRODUCTION_URL
    MODE = "production"
else:
    URL = LOCALHOST_URL
    MODE = "localhost"

# Output path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'Soulfra.com', 'qr-code.png')

print(f"\n{'='*70}")
print(f"Generating QR Code for {MODE.upper()}")
print(f"{'='*70}")
print(f"URL: {URL}")
print(f"Output: {OUTPUT_PATH}")
print(f"{'='*70}\n")

# Generate QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr.add_data(URL)
qr.make(fit=True)

# Create image
img = qr.make_image(fill_color="black", back_color="white")

# Save image
img.save(OUTPUT_PATH)

print(f"✅ QR code generated successfully!")
print(f"   Saved to: {OUTPUT_PATH}")
print(f"\nWhat happens when scanned:")
print(f"1. Opens: {URL}")
print(f"2. Creates account in soulfraapi.com database")
print(f"3. Redirects to soulfra.ai/?session=TOKEN")
print(f"4. User can start chatting with AI")
print(f"\n{'='*70}\n")

# Display QR code in terminal (optional)
try:
    print("QR Code (ASCII):")
    print(qr.get_matrix())
except:
    pass
