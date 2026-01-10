#!/usr/bin/env python3
"""
Full Flow Test - Proof of Concept

Tests the complete waitlist + domain system:
1. Initialize database
2. Sign up test users (Alice, Wu, and 10 more)
3. Show letter assignments
4. Show launch date acceleration
5. Test domain randomization
6. Test API endpoints (/api/domains/add, /api/domains/connections)
7. Test Alice's dashboard
8. Export results

Usage:
    python3 test_full_flow.py
    python3 test_full_flow.py --api-only  # Only test API endpoints
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from database import get_db, init_db
from domain_randomizer import assign_domain_smart
from launch_calculator import calculate_launch_date, get_letter_allocation

BASE_URL = "http://localhost:5001"

# Test users
TEST_USERS = [
    {'email': 'alice@example.com', 'lang': 'en', 'prefer_domain': 'calriven', 'name': 'Alice (Coder)'},
    {'email': 'wu@example.com', 'lang': 'zh', 'prefer_domain': None, 'name': 'Wu (Chinese Market)'},
    {'email': 'bob@soulfra.ai', 'lang': 'en', 'prefer_domain': 'soulfra', 'name': 'Bob (Hub User)'},
    {'email': 'maria@ejemplo.es', 'lang': 'es', 'prefer_domain': None, 'name': 'Maria (Spanish)'},
    {'email': 'yuki@example.jp', 'lang': 'ja', 'prefer_domain': 'cringeproof', 'name': 'Yuki (Voice User)'},
    {'email': 'wang@example.com', 'lang': 'zh', 'prefer_domain': None, 'name': 'Wang (Chinese #2)'},
    {'email': 'pierre@exemple.fr', 'lang': 'fr', 'prefer_domain': 'calriven', 'name': 'Pierre (French Blogger)'},
    {'email': 'sarah@data.com', 'lang': 'en', 'prefer_domain': 'deathtodata', 'name': 'Sarah (Data Analyst)'},
    {'email': 'carlos@blog.es', 'lang': 'es', 'prefer_domain': 'calriven', 'name': 'Carlos (Spanish Blogger)'},
    {'email': 'li@example.com', 'lang': 'zh', 'prefer_domain': None, 'name': 'Li (Chinese #3)'},
]


def init_test_database():
    """Initialize database with fresh domain_launches"""
    print("\n" + "="*60)
    print("🗄️  INITIALIZING TEST DATABASE")
    print("="*60)

    # Initialize schema
    init_db()

    db = get_db()

    # Clear existing data
    db.execute('DELETE FROM waitlist')
    db.execute('DELETE FROM domain_launches')
    db.commit()

    # Insert domain_launches (matching actual schema from database.py)
    domains = ['soulfra', 'calriven', 'deathtodata', 'cringeproof']
    for domain in domains:
        db.execute('''
            INSERT INTO domain_launches (domain_name, base_launch_days, current_signups, instant_launch_threshold)
            VALUES (?, 90, 0, 900)
        ''', (domain,))

    db.commit()
    db.close()

    print("✅ Database initialized with 4 domains")
    print(f"   Domains: {', '.join(domains)}")


def signup_user(email, lang='en', prefer_domain=None):
    """Sign up a user for a domain"""
    # Use domain randomizer to get smart assignment
    assignment = assign_domain_smart(email, lang, prefer_domain)

    if not assignment['domain']:
        return None

    # Insert into waitlist
    db = get_db()

    # Generate referral code
    import hashlib
    import secrets
    salt = secrets.token_hex(8)
    hash_input = f"{email}{assignment['domain']}{salt}".encode('utf-8')
    referral_code = hashlib.sha256(hash_input).hexdigest()[:8].upper()

    db.execute('''
        INSERT INTO waitlist (email, domain_name, letter_code, referral_code, signup_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, assignment['domain'], assignment['letter'], referral_code, datetime.now(timezone.utc).isoformat()))

    # Update domain signup count
    db.execute('''
        UPDATE domain_launches
        SET current_signups = current_signups + 1
        WHERE domain_name = ?
    ''', (assignment['domain'],))

    db.commit()
    db.close()

    # Get launch date
    launch_info = calculate_launch_date(assignment['domain'])

    return {
        **assignment,
        'referral_code': referral_code,
        'launch_info': launch_info
    }


def run_test():
    """Run the full test"""
    print("\n" + "="*60)
    print("🧪 SOULFRA WAITLIST - FULL FLOW TEST")
    print("="*60)

    # Init database
    init_test_database()

    # Sign up users
    print("\n" + "="*60)
    print("📝 SIGNING UP TEST USERS")
    print("="*60)

    results = []

    for i, user in enumerate(TEST_USERS, 1):
        print(f"\n{i}. {user['name']} ({user['email']})")

        result = signup_user(
            user['email'],
            user['lang'],
            user['prefer_domain']
        )

        if result:
            print(f"   ✅ Domain: {result['domain']}")
            print(f"   ✅ Letter: {result['letter']}")
            print(f"   ✅ Referral: {result['referral_code']}")
            print(f"   ✅ Launch in: {result['launch_info']['days_until']} days")
            print(f"   📋 Reason: {result['reason']}")

            results.append({
                'user': user['name'],
                'email': user['email'],
                'domain': result['domain'],
                'letter': result['letter'],
                'referral_code': result['referral_code'],
                'days_until_launch': result['launch_info']['days_until']
            })
        else:
            print(f"   ❌ Failed to assign domain (all full)")

    # Show domain stats
    print("\n" + "="*60)
    print("📊 DOMAIN STATISTICS")
    print("="*60)

    db = get_db()
    domains = db.execute('SELECT * FROM domain_launches').fetchall()

    total_signups = 0
    for domain in domains:
        allocation = get_letter_allocation(domain['domain_name'])

        pct = (domain['current_signups'] / 26) * 100
        status = "🔴 FULL" if allocation['is_full'] else "🟢 Open"

        print(f"\n{domain['domain_name'].upper()}")
        print(f"  Signups: {domain['current_signups']}/26 ({pct:.1f}%)")
        print(f"  Status: {status}")
        print(f"  Available: {', '.join(allocation['available'][:5])}...")

        total_signups += domain['current_signups']

    db.close()

    print(f"\n{'='*60}")
    print(f"Total Signups: {total_signups}/104 (4 domains × 26 letters)")

    # Show letter distribution
    print("\n" + "="*60)
    print("🔤 LETTER DISTRIBUTION")
    print("="*60)

    db = get_db()
    letters = db.execute('''
        SELECT letter_code, domain_name, COUNT(*) as count
        FROM waitlist
        GROUP BY letter_code, domain_name
        ORDER BY letter_code
    ''').fetchall()

    letter_map = {}
    for row in letters:
        if row['letter_code'] not in letter_map:
            letter_map[row['letter_code']] = []
        letter_map[row['letter_code']].append(f"{row['domain_name']}({row['count']})")

    for letter, domains in sorted(letter_map.items()):
        print(f"  {letter}: {', '.join(domains)}")

    db.close()

    # Export results
    print("\n" + "="*60)
    print("💾 EXPORTING RESULTS")
    print("="*60)

    output_file = './test_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_users': results,
            'total_signups': total_signups,
            'domains': {
                'soulfra': [r for r in results if r['domain'] == 'soulfra'],
                'calriven': [r for r in results if r['domain'] == 'calriven'],
                'deathtodata': [r for r in results if r['domain'] == 'deathtodata'],
                'cringeproof': [r for r in results if r['domain'] == 'cringeproof']
            }
        }, f, indent=2)

    print(f"✅ Results exported to: {output_file}")

    # Show Alice's info specifically
    print("\n" + "="*60)
    print("👩‍💻 ALICE'S ASSIGNMENT")
    print("="*60)

    alice_result = next((r for r in results if 'alice' in r['email']), None)
    if alice_result:
        print(f"  Email: {alice_result['email']}")
        print(f"  Domain: {alice_result['domain']}")
        print(f"  Letter: {alice_result['letter']}")
        print(f"  Referral: {alice_result['referral_code']}")
        print(f"  Launch: {alice_result['days_until_launch']} days")
        print(f"\n  Personal URL: https://{alice_result['domain']}.com/alice/")
        print(f"  API Endpoint: /api/users/alice/request")

    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Check test_results.json for full data")
    print("  2. Run: python3 build_waitlist.py")
    print("  3. Run: python3 deploy_all.py --push")
    print("  4. Visit: soulfra.github.io/waitlist/")


def test_api_endpoints():
    """Test the Flask API endpoints"""
    print("\n" + "="*60)
    print("🔌 TESTING API ENDPOINTS")
    print("="*60)

    session = requests.Session()
    results = {}

    # Test 1: /api/domains/add
    print("\n1. Testing /api/domains/add")
    try:
        response = session.post(f"{BASE_URL}/api/domains/add", json={
            "email": "alice@example.com",
            "custom_domain": "alicewonderland.com",
            "brand": "personal_blog"
        })

        if response.status_code == 200:
            print("   ✅ /api/domains/add works")
            results['domains_add'] = 'PASS'
        elif response.status_code == 404:
            print("   ❌ /api/domains/add endpoint missing")
            results['domains_add'] = 'MISSING'
        else:
            print(f"   ❌ Failed: {response.status_code}")
            results['domains_add'] = 'FAIL'

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Flask (localhost:5001)")
        results['domains_add'] = 'NO_SERVER'

    # Test 2: /api/domains/connections
    print("\n2. Testing /api/domains/connections")
    try:
        response = session.get(f"{BASE_URL}/api/domains/connections?email=alice@example.com")

        if response.status_code == 200:
            data = response.json()
            connections = data.get('connections', [])
            print(f"   ✅ /api/domains/connections works ({len(connections)} connections)")
            results['domains_connections'] = 'PASS'
        elif response.status_code == 404:
            print("   ❌ /api/domains/connections endpoint missing")
            results['domains_connections'] = 'MISSING'
        else:
            print(f"   ❌ Failed: {response.status_code}")
            results['domains_connections'] = 'FAIL'

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Flask")
        results['domains_connections'] = 'NO_SERVER'

    # Test 3: /me (Alice's dashboard)
    print("\n3. Testing /me (Alice's Dashboard)")
    try:
        response = session.get(f"{BASE_URL}/me?email=alice@example.com")

        if response.status_code == 200:
            html = response.text
            if 'alice' in html.lower() and 'domain' in html.lower():
                print("   ✅ /me dashboard works")
                results['dashboard'] = 'PASS'
            else:
                print("   ⚠️  Dashboard loads but missing content")
                results['dashboard'] = 'PARTIAL'
        elif response.status_code == 404:
            print("   ❌ /me endpoint missing")
            results['dashboard'] = 'MISSING'
        else:
            print(f"   ❌ Failed: {response.status_code}")
            results['dashboard'] = 'FAIL'

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Flask")
        results['dashboard'] = 'NO_SERVER'

    # Test 4: /api/users/alice@example.com
    print("\n4. Testing /api/users/:email")
    try:
        response = session.get(f"{BASE_URL}/api/users/alice@example.com")

        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User API works (username: {user.get('username', 'N/A')})")
            results['user_api'] = 'PASS'
        elif response.status_code == 404:
            print("   ⚠️  Alice doesn't exist in database yet")
            results['user_api'] = 'NO_USER'
        else:
            print(f"   ❌ Failed: {response.status_code}")
            results['user_api'] = 'FAIL'

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to Flask")
        results['user_api'] = 'NO_SERVER'

    # Summary
    print("\n" + "="*60)
    print("📊 API TEST SUMMARY")
    print("="*60)

    for endpoint, status in results.items():
        icon = "✅" if status == 'PASS' else "⚠️" if status in ['PARTIAL', 'NO_USER'] else "❌"
        print(f"{icon} {endpoint}: {status}")

    return results


if __name__ == '__main__':
    if '--api-only' in sys.argv:
        test_api_endpoints()
    else:
        run_test()
        print("\n" + "="*60)
        print("🔌 NOW TESTING API ENDPOINTS")
        print("="*60)
        test_api_endpoints()
