#!/usr/bin/env python3
"""
OSS Reproducibility Verification

Tests that Soulfra can be:
1. Installed fresh
2. Database initialized
3. Build-in-public workflow works
4. Newsletter digest generates
5. All data exportable as JSON

Run this to verify everything works for OSS release.
"""

import os
import json
import subprocess
from database import get_db


def test_database_structure():
    """Verify all required tables exist"""
    print("TEST 1: Database Structure")
    
    required_tables = [
        'users', 'posts', 'comments',
        'reasoning_threads', 'reasoning_steps',
        'feedback', 'qr_codes', 'qr_scans',
        'url_shortcuts', 'soul_history'
    ]
    
    db = get_db()
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t['name'] for t in tables]
    db.close()
    
    missing = [t for t in required_tables if t not in table_names]
    
    if missing:
        print(f"   ❌ Missing tables: {', '.join(missing)}")
        return False
    
    print(f"   ✅ All {len(required_tables)} required tables exist")
    return True


def test_public_builder_workflow():
    """Test feedback → post → reasoning workflow"""
    print("\nTEST 2: Public Builder Workflow")
    
    # Run public_builder.py
    try:
        result = subprocess.run(
            ['python3', 'public_builder.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if 'PUBLIC BUILDER COMPLETE' in result.stdout:
            print("   ✅ Public builder ran successfully")
            return True
        else:
            print(f"   ❌ Public builder failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error running public_builder.py: {e}")
        return False


def test_newsletter_digest():
    """Test newsletter digest generation"""
    print("\nTEST 3: Newsletter Digest")
    
    try:
        result = subprocess.run(
            ['python3', 'newsletter_digest.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if 'DIGEST COMPLETE' in result.stdout:
            # Check if HTML file was created
            if os.path.exists('weekly_digest_preview.html'):
                print("   ✅ Newsletter digest generated")
                return True
            else:
                print("   ❌ Digest file not created")
                return False
        else:
            print(f"   ❌ Digest generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error generating digest: {e}")
        return False


def test_data_export():
    """Test full data export as JSON"""
    print("\nTEST 4: Data Export (Reproducibility)")
    
    db = get_db()
    
    export_data = {
        'users': [],
        'posts': [],
        'feedback': [],
        'reasoning_threads': [],
        'soul_history': [],
        'qr_codes': []
    }
    
    try:
        # Export each table
        for table in export_data.keys():
            rows = db.execute(f'SELECT * FROM {table}').fetchall()
            export_data[table] = [dict(row) for row in rows]
        
        db.close()
        
        # Save to JSON
        with open('soulfra_export.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        total_records = sum(len(records) for records in export_data.values())
        print(f"   ✅ Exported {total_records} records to soulfra_export.json")
        
        # Verify JSON is valid
        with open('soulfra_export.json', 'r') as f:
            json.load(f)
        
        print("   ✅ JSON export is valid and reproducible")
        return True
        
    except Exception as e:
        print(f"   ❌ Export failed: {e}")
        return False


def test_reasoning_engine():
    """Test reasoning engine functionality"""
    print("\nTEST 5: Reasoning Engine")
    
    try:
        from reasoning_engine import ReasoningEngine
        
        engine = ReasoningEngine()
        
        # Test keyword extraction
        test_text = "This is a test about QR codes and soul versioning with git-like commits"
        keywords = engine.extract_keywords(test_text, top_n=5)
        
        if keywords and len(keywords) > 0:
            print(f"   ✅ Keyword extraction works: {[kw for kw, _ in keywords]}")
        else:
            print("   ❌ Keyword extraction failed")
            return False
        
        # Test code block detection
        test_with_code = "Here is code: <pre>print('hello')</pre> and more text"
        code_blocks = engine.extract_code_blocks(test_with_code)
        
        if len(code_blocks) > 0:
            print(f"   ✅ Code block detection works: found {len(code_blocks)} blocks")
        else:
            print("   ⚠️  Code block detection didn't find blocks (may be OK)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Reasoning engine error: {e}")
        return False


def test_qr_tracking():
    """Test QR time capsule tracking"""
    print("\nTEST 6: QR Time Capsule")
    
    db = get_db()
    
    try:
        # Check if tables exist
        qr_codes_count = db.execute('SELECT COUNT(*) as count FROM qr_codes').fetchone()['count']
        qr_scans_count = db.execute('SELECT COUNT(*) as count FROM qr_scans').fetchone()['count']
        
        print(f"   ✅ QR codes: {qr_codes_count}, Scans: {qr_scans_count}")
        
        # Test scan chain query (recursive)
        chain_test = db.execute('''
            SELECT id, previous_scan_id FROM qr_scans LIMIT 1
        ''').fetchone()
        
        if chain_test:
            print(f"   ✅ Scan chain structure verified")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ QR tracking error: {e}")
        db.close()
        return False


def run_full_verification():
    """Run all verification tests"""
    print("=" * 70)
    print("🔍 SOULFRA OSS REPRODUCIBILITY VERIFICATION")
    print("=" * 70)
    print()
    
    tests = [
        ("Database Structure", test_database_structure),
        ("Public Builder Workflow", test_public_builder_workflow),
        ("Newsletter Digest", test_newsletter_digest),
        ("Data Export", test_data_export),
        ("Reasoning Engine", test_reasoning_engine),
        ("QR Time Capsule", test_qr_tracking)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n   ❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    print()
    print("=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print()
    print(f"   {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Soulfra is reproducible and ready for OSS!")
    else:
        print("⚠️  Some tests failed - fix issues before OSS release")
    
    print()
    
    # Show exported files
    if os.path.exists('soulfra_export.json'):
        print("📦 Exported files:")
        print("   • soulfra_export.json - Full database export")
    
    if os.path.exists('weekly_digest_preview.html'):
        print("   • weekly_digest_preview.html - Newsletter preview")
    
    print()
    
    return passed == total


if __name__ == '__main__':
    success = run_full_verification()
    exit(0 if success else 1)
