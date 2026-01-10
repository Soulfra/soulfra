"""
Test Complete Vanity QR Flow

Tests the end-to-end flow:
1. Create vanity QR code
2. Test redirect route
3. Test canvas export API
"""

import requests
import json
from vanity_qr import create_and_save_vanity_qr, init_vanity_qr_db

print("=" * 70)
print("Testing Complete Vanity QR Flow")
print("=" * 70)
print()

# Initialize database
print("1. Initializing vanity QR database...")
init_vanity_qr_db()
print("✅ Database initialized")
print()

# Test 1: Create vanity QR code
print("2. Creating vanity QR code...")
result = create_and_save_vanity_qr(
    full_url='https://cringeproof.com/blog/test-post-123',
    brand_slug='cringeproof',
    label='SCAN ME'
)

vanity_url = result['vanity_url']
short_code = result['short_code']
full_url = result['full_url']

print(f"✅ Created QR code:")
print(f"   Vanity URL: {vanity_url}")
print(f"   Short Code: {short_code}")
print(f"   Full URL: {full_url}")
print()

# Save QR image
with open('test_flow_qr.png', 'wb') as f:
    f.write(result['qr_image'])
print(f"✅ Saved QR image: test_flow_qr.png")
print()

# Test 2: Test redirect route (requires Flask server running)
print("3. Testing redirect route...")
try:
    # Note: This will make an actual HTTP request to localhost:5001
    redirect_url = f'http://localhost:5001/v/{short_code}'
    response = requests.get(redirect_url, allow_redirects=False)

    if response.status_code == 302:
        redirect_to = response.headers.get('Location', '')
        print(f"✅ Redirect working!")
        print(f"   Requested: {redirect_url}")
        print(f"   Redirects to: {redirect_to}")

        if redirect_to == full_url:
            print(f"   ✅ Correct redirect URL!")
        else:
            print(f"   ⚠️  Redirect URL mismatch!")
            print(f"   Expected: {full_url}")
            print(f"   Got: {redirect_to}")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")

except requests.exceptions.ConnectionError:
    print("⚠️  Flask server not running on localhost:5001")
    print("   Start server with: python3 app.py")
except Exception as e:
    print(f"⚠️  Error testing redirect: {e}")
print()

# Test 3: Test canvas export API
print("4. Testing canvas export API...")
try:
    composition = {
        'brand': 'soulfra',
        'size': [800, 600],
        'layers': [
            {
                'type': 'gradient',
                'colors': ['#8B5CF6', '#3B82F6'],
                'angle': 45,
                'opacity': 1,
                'visible': True
            },
            {
                'type': 'text',
                'content': 'Test Export',
                'font': 'Arial',
                'fontSize': 48,
                'color': '#FFFFFF',
                'x': 100,
                'y': 200,
                'opacity': 1,
                'visible': True
            }
        ]
    }

    response = requests.post(
        'http://localhost:5001/api/generate/custom',
        json=composition,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        # Save exported image
        with open('test_flow_export.jpg', 'wb') as f:
            f.write(response.content)

        print(f"✅ Canvas export working!")
        print(f"   Saved image: test_flow_export.jpg")
        print(f"   Size: {len(response.content):,} bytes")
    else:
        print(f"⚠️  API returned status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

except requests.exceptions.ConnectionError:
    print("⚠️  Flask server not running on localhost:5001")
except Exception as e:
    print(f"⚠️  Error testing export: {e}")
print()

print("=" * 70)
print("✅ Flow Test Complete!")
print()
print("Summary:")
print("  1. ✅ Vanity QR code created and saved to database")
print("  2. Check redirect test above")
print("  3. Check canvas export test above")
print()
print("Next Steps:")
print("  - Open http://localhost:5001/admin/canvas in browser")
print("  - Create an image and click 'Export'")
print("  - Print the QR code and scan with phone")
print("  - Verify redirect works")
print()
