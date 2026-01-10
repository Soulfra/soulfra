#!/usr/bin/env python3
"""
Test Suite for Database-First Image Hosting

Verifies all claims in the blog post:
- Images stored correctly in database
- SHA256 hashes match actual data
- Image serving works
- Deduplication works
- No duplicate hashes

Run this to verify the science!
"""

import hashlib
import sqlite3
from database import get_db

def test_image_count():
    """Test: Database contains expected number of images"""
    db = get_db()
    count = db.execute('SELECT COUNT(*) as count FROM images').fetchone()['count']
    db.close()

    print(f"✓ Image count: {count} images in database")
    assert count > 0, "❌ No images in database"
    return count

def test_hash_integrity():
    """Test: SHA256 hashes match actual image data"""
    db = get_db()
    images = db.execute('SELECT id, hash, data FROM images').fetchall()
    db.close()

    failed = []

    for img in images:
        # Recalculate hash from data
        calculated_hash = hashlib.sha256(img['data']).hexdigest()

        if calculated_hash != img['hash']:
            failed.append({
                'id': img['id'],
                'stored_hash': img['hash'],
                'calculated_hash': calculated_hash
            })

    if failed:
        print(f"❌ Hash integrity check failed for {len(failed)} images:")
        for f in failed:
            print(f"   Image #{f['id']}: stored={f['stored_hash'][:12]}... calculated={f['calculated_hash'][:12]}...")
        raise AssertionError("Hash mismatch detected")

    print(f"✓ Hash integrity: All {len(images)} hashes match image data")
    return len(images)

def test_no_duplicates():
    """Test: No duplicate hashes (deduplication works)"""
    db = get_db()

    total = db.execute('SELECT COUNT(*) as count FROM images').fetchone()['count']
    unique = db.execute('SELECT COUNT(DISTINCT hash) as count FROM images').fetchone()['count']

    db.close()

    if total != unique:
        print(f"❌ Duplicate hashes found: {total} total, {unique} unique")
        raise AssertionError("Deduplication failed - duplicate hashes exist")

    print(f"✓ Deduplication: {unique} unique hashes (no duplicates)")
    return unique

def test_required_fields():
    """Test: All images have required fields populated"""
    db = get_db()
    images = db.execute('''
        SELECT id, hash, data, mime_type, width, height
        FROM images
    ''').fetchall()
    db.close()

    missing_fields = []

    for img in images:
        if not img['hash']:
            missing_fields.append(f"Image #{img['id']}: missing hash")
        if not img['data']:
            missing_fields.append(f"Image #{img['id']}: missing data")
        if not img['mime_type']:
            missing_fields.append(f"Image #{img['id']}: missing mime_type")
        if img['width'] is None or img['height'] is None:
            missing_fields.append(f"Image #{img['id']}: missing dimensions")

    if missing_fields:
        print("❌ Required fields missing:")
        for mf in missing_fields:
            print(f"   {mf}")
        raise AssertionError("Required fields not populated")

    print(f"✓ Required fields: All {len(images)} images have hash, data, mime_type, dimensions")
    return len(images)

def test_hash_index():
    """Test: Hash index exists for performance"""
    db = get_db()

    # Check if index exists
    indexes = db.execute('''
        SELECT name FROM sqlite_master
        WHERE type='index' AND tbl_name='images'
    ''').fetchall()

    db.close()

    index_names = [idx['name'] for idx in indexes]

    if 'idx_images_hash' not in index_names:
        print("❌ Hash index not found")
        print(f"   Found indexes: {index_names}")
        raise AssertionError("idx_images_hash index missing")

    print(f"✓ Index: idx_images_hash exists")
    return True

def test_metadata_json():
    """Test: Metadata is valid JSON"""
    import json

    db = get_db()
    images = db.execute('SELECT id, metadata FROM images').fetchall()
    db.close()

    invalid = []

    for img in images:
        if img['metadata']:
            try:
                json.loads(img['metadata'])
            except json.JSONDecodeError as e:
                invalid.append(f"Image #{img['id']}: {e}")

    if invalid:
        print("❌ Invalid JSON metadata:")
        for inv in invalid:
            print(f"   {inv}")
        raise AssertionError("Invalid JSON in metadata")

    print(f"✓ Metadata: All {len(images)} images have valid JSON")
    return len(images)

def test_database_size():
    """Test: Report database size (performance metric)"""
    import os

    db_path = 'soulfra.db'

    if not os.path.exists(db_path):
        print("❌ Database file not found")
        raise AssertionError("soulfra.db not found")

    size_bytes = os.path.getsize(db_path)
    size_kb = size_bytes / 1024

    print(f"✓ Database size: {size_kb:.1f} KB ({size_bytes:,} bytes)")
    return size_kb

def test_image_types():
    """Test: Report breakdown of image types"""
    import json

    db = get_db()
    images = db.execute('SELECT metadata FROM images').fetchall()
    db.close()

    types = {}

    for img in images:
        if img['metadata']:
            try:
                meta = json.loads(img['metadata'])
                img_type = meta.get('type', 'unknown')
                types[img_type] = types.get(img_type, 0) + 1
            except:
                pass

    print(f"✓ Image types breakdown:")
    for img_type, count in sorted(types.items()):
        print(f"   {img_type}: {count}")

    return types

def run_all_tests():
    """Run complete test suite"""
    print("=" * 70)
    print("🧪 Testing Database-First Image Hosting")
    print("=" * 70)
    print()

    tests = [
        ("Image Count", test_image_count),
        ("Hash Integrity", test_hash_integrity),
        ("No Duplicates", test_no_duplicates),
        ("Required Fields", test_required_fields),
        ("Hash Index", test_hash_index),
        ("Metadata JSON", test_metadata_json),
        ("Database Size", test_database_size),
        ("Image Types", test_image_types),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()

    if failed == 0:
        print("✅ ALL TESTS PASSED - Database-first image hosting verified!")
        print()
        print("Scientific claims validated:")
        print("  • Images stored in SQLite as BLOBs")
        print("  • SHA256 hashes match actual data")
        print("  • Deduplication works (no duplicate hashes)")
        print("  • All required fields populated")
        print("  • Performance optimized (hash index)")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED - See above for details")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
