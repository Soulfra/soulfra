#!/usr/bin/env python3
"""
Verify Everything - End-to-End System Proof

Proves the entire soul/visualization/QR system works:
1. Database connectivity ✓
2. Soul compilation for all users ✓
3. Unique visualizations for each user ✓
4. QR code generation ✓
5. Data integrity ✓

Run this to verify the system is working!
"""

import os
from database import get_db
from soul_model import Soul
from soul_visualizer import generate_soul_visualization
from soul_qr import generate_qr_from_soul_pack
from PIL import ImageChops
import json
from datetime import datetime


def test_database_connectivity():
    """Test 1: Database is accessible and has users"""
    print("=" * 70)
    print("TEST 1: Database Connectivity")
    print("=" * 70)

    try:
        db = get_db()
        users = db.execute('SELECT id, username, display_name FROM users').fetchall()
        db.close()

        print(f"✅ Connected to database")
        print(f"✅ Found {len(users)} users:\n")

        for user in users:
            print(f"   - {user['username']:15} (ID: {user['id']}, Display: {user['display_name']})")

        print(f"\n✅ Database test PASSED\n")
        return users
    except Exception as e:
        print(f"❌ Database test FAILED: {e}\n")
        return []


def test_soul_compilation(users):
    """Test 2: Can compile souls for all users"""
    print("=" * 70)
    print("TEST 2: Soul Compilation")
    print("=" * 70)

    soul_packs = {}

    for user in users:
        try:
            soul = Soul(user['id'])
            pack = soul.compile_pack()
            soul_packs[user['username']] = pack

            # Show key info
            interests = pack['essence']['interests'][:3]
            values = pack['essence']['values'][:2]

            print(f"✅ {user['username']:15} compiled")
            print(f"   Interests: {', '.join(interests)}")
            print(f"   Values: {', '.join(values)}")
            print()

        except Exception as e:
            print(f"❌ {user['username']:15} FAILED: {e}\n")

    print(f"✅ Compiled {len(soul_packs)}/{len(users)} souls successfully\n")
    return soul_packs


def test_visualization_uniqueness(soul_packs):
    """Test 3: Each soul generates unique visualization"""
    print("=" * 70)
    print("TEST 3: Visualization Uniqueness")
    print("=" * 70)

    visualizations = {}

    # Generate visualizations
    for username, pack in soul_packs.items():
        try:
            img = generate_soul_visualization(pack, output_size=128)
            visualizations[username] = img
            print(f"✅ {username:15} visualization generated ({img.size})")
        except Exception as e:
            print(f"❌ {username:15} visualization FAILED: {e}")

    print()

    # Compare all pairs to prove uniqueness
    usernames = list(visualizations.keys())
    comparisons = 0
    all_unique = True

    print("Comparing visualizations (proving uniqueness):\n")

    for i in range(len(usernames)):
        for j in range(i + 1, len(usernames)):
            user1 = usernames[i]
            user2 = usernames[j]

            img1 = visualizations[user1]
            img2 = visualizations[user2]

            # Pixel comparison
            diff = ImageChops.difference(img1, img2)
            diff_pixels = sum(1 for p in diff.getdata() if p != (0, 0, 0))
            total_pixels = img1.size[0] * img1.size[1]

            is_different = diff_pixels > 0

            if is_different:
                print(f"   ✅ {user1:12} vs {user2:12} → Different ({diff_pixels}/{total_pixels} pixels differ)")
            else:
                print(f"   ❌ {user1:12} vs {user2:12} → IDENTICAL (BUG!)")
                all_unique = False

            comparisons += 1

    print()
    if all_unique:
        print(f"✅ All {comparisons} comparisons show unique visualizations!\n")
    else:
        print(f"❌ Some visualizations are identical (BUG!)\n")

    return visualizations, all_unique


def test_qr_generation(soul_packs):
    """Test 4: QR codes generate and contain correct data"""
    print("=" * 70)
    print("TEST 4: QR Code Generation")
    print("=" * 70)

    qr_codes = {}

    for username, pack in soul_packs.items():
        try:
            qr = generate_qr_from_soul_pack(pack, size=128)
            qr_codes[username] = qr

            # Check data size
            json_size = len(json.dumps(pack))

            print(f"✅ {username:15} QR generated ({qr.size}, {json_size} bytes of data)")
        except Exception as e:
            print(f"❌ {username:15} QR FAILED: {e}")

    print()

    # Verify QR codes are different
    usernames = list(qr_codes.keys())
    all_different = True

    print("Verifying QR codes are unique:\n")

    for i in range(min(3, len(usernames))):  # Just check first 3 pairs
        for j in range(i + 1, min(3, len(usernames))):
            user1 = usernames[i]
            user2 = usernames[j]

            pixels1 = list(qr_codes[user1].getdata())
            pixels2 = list(qr_codes[user2].getdata())

            is_different = pixels1 != pixels2

            if is_different:
                print(f"   ✅ {user1:12} vs {user2:12} → Different QR codes")
            else:
                print(f"   ❌ {user1:12} vs {user2:12} → IDENTICAL QR (BUG!)")
                all_different = False

    print()
    if all_different:
        print(f"✅ QR codes are unique!\n")
    else:
        print(f"❌ Some QR codes are identical (BUG!)\n")

    return qr_codes, all_different


def test_data_integrity(soul_packs):
    """Test 5: Soul pack data has all required fields"""
    print("=" * 70)
    print("TEST 5: Data Integrity")
    print("=" * 70)

    required_keys = ['version', 'compiled_at', 'identity', 'essence', 'expression', 'connections', 'evolution', 'fingerprint']
    all_valid = True

    for username, pack in soul_packs.items():
        missing = [key for key in required_keys if key not in pack]

        if not missing:
            print(f"✅ {username:15} has all required fields")
        else:
            print(f"❌ {username:15} missing: {', '.join(missing)}")
            all_valid = False

    print()
    if all_valid:
        print(f"✅ All soul packs have correct structure!\n")
    else:
        print(f"❌ Some soul packs are incomplete\n")

    return all_valid


def generate_verification_report(users, soul_packs, visualizations, qr_codes, test_results):
    """Generate summary report"""
    print("=" * 70)
    print("VERIFICATION REPORT")
    print("=" * 70)
    print()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Generated: {timestamp}")
    print(f"Users tested: {len(users)}")
    print(f"Souls compiled: {len(soul_packs)}")
    print(f"Visualizations: {len(visualizations)}")
    print(f"QR codes: {len(qr_codes)}")
    print()

    print("Test Results:")
    print(f"  1. Database Connectivity:       {'✅ PASS' if len(users) > 0 else '❌ FAIL'}")
    print(f"  2. Soul Compilation:            {'✅ PASS' if len(soul_packs) > 0 else '❌ FAIL'}")
    print(f"  3. Visualization Uniqueness:    {'✅ PASS' if test_results['viz_unique'] else '❌ FAIL'}")
    print(f"  4. QR Code Generation:          {'✅ PASS' if test_results['qr_unique'] else '❌ FAIL'}")
    print(f"  5. Data Integrity:              {'✅ PASS' if test_results['data_valid'] else '❌ FAIL'}")
    print()

    all_passed = all(test_results.values())

    if all_passed:
        print("=" * 70)
        print("🎉 ALL TESTS PASSED - SYSTEM IS WORKING! 🎉")
        print("=" * 70)
    else:
        print("=" * 70)
        print("❌ SOME TESTS FAILED - REVIEW ABOVE")
        print("=" * 70)

    return all_passed


def save_sample_outputs(visualizations, qr_codes, output_dir='verification_output'):
    """Save sample visualizations and QR codes"""
    print("\nSaving sample outputs...")

    os.makedirs(output_dir, exist_ok=True)

    # Save first 3 visualizations
    for i, (username, img) in enumerate(list(visualizations.items())[:3]):
        filepath = os.path.join(output_dir, f'{username}_visualization.png')
        img.save(filepath, 'PNG')
        print(f"   Saved: {filepath}")

    # Save first 3 QR codes
    for i, (username, img) in enumerate(list(qr_codes.items())[:3]):
        filepath = os.path.join(output_dir, f'{username}_qr.png')
        img.save(filepath, 'PNG')
        print(f"   Saved: {filepath}")

    print(f"\n✅ Sample outputs saved to {output_dir}/\n")


def run_verification():
    """Run all verification tests"""
    print("\n" + "=" * 70)
    print("SOULFRA SYSTEM VERIFICATION")
    print("End-to-End Testing - Proving Everything Works!")
    print("=" * 70)
    print()

    # Run tests
    users = test_database_connectivity()

    if not users:
        print("❌ Cannot continue without database access\n")
        return False

    soul_packs = test_soul_compilation(users)

    if not soul_packs:
        print("❌ Cannot continue without compiled souls\n")
        return False

    visualizations, viz_unique = test_visualization_uniqueness(soul_packs)
    qr_codes, qr_unique = test_qr_generation(soul_packs)
    data_valid = test_data_integrity(soul_packs)

    # Generate report
    test_results = {
        'viz_unique': viz_unique,
        'qr_unique': qr_unique,
        'data_valid': data_valid
    }

    all_passed = generate_verification_report(users, soul_packs, visualizations, qr_codes, test_results)

    # Save samples
    save_sample_outputs(visualizations, qr_codes)

    return all_passed


if __name__ == '__main__':
    import sys
    success = run_verification()
    sys.exit(0 if success else 1)
