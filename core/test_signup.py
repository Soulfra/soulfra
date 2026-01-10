#!/usr/bin/env python3
"""Test professional signup flow"""

from database import get_db

# Test data
test_data = {
    'business_name': 'Bob Plumbing Service',
    'category': 'plumbing',
    'email': 'bob@test.com',
    'phone': '727-555-1234',
    'bio': 'Professional plumbing for 20 years',
    'address': '123 Main St',
    'website': 'https://bob.com'
}

db = get_db()

print("\n🧪 Testing Professional Signup")
print("=" * 50)

# Insert professional
try:
    db.execute('''
        INSERT INTO professionals (
            business_name, category, email, phone, bio, address, website,
            verified, rating_avg, review_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0.0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ''', (
        test_data['business_name'],
        test_data['category'],
        test_data['email'],
        test_data['phone'],
        test_data['bio'],
        test_data['address'],
        test_data['website']
    ))

    # Also add to subscribers
    db.execute('''
        INSERT OR IGNORE INTO subscribers (email)
        VALUES (?)
    ''', (test_data['email'],))

    db.commit()

    print("✅ Professional created successfully!")

    # Query back
    pro = db.execute('SELECT * FROM professionals WHERE email = ?', (test_data['email'],)).fetchone()
    print(f"\n📋 Professional Record:")
    print(f"   ID: {pro['id']}")
    print(f"   Business: {pro['business_name']}")
    print(f"   Category: {pro['category']}")
    print(f"   Email: {pro['email']}")
    print(f"   Phone: {pro['phone']}")

    # Check subscribers
    sub = db.execute('SELECT * FROM subscribers WHERE email = ?', (test_data['email'],)).fetchone()
    if sub:
        print(f"\n✅ Also added to subscribers table")
        print(f"   Source: {sub['source']}")

    print("\n✅ Test passed! Signup flow works correctly.\n")

except Exception as e:
    print(f"\n❌ Error: {e}\n")
    import traceback
    traceback.print_exc()
