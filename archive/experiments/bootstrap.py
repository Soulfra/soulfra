#!/usr/bin/env python3
"""
Bootstrap Soulfra Brand System - Pure Python Stdlib

Master initialization script that sets up the complete brand voice ML system.
Runs all necessary migrations, syncs, and validations in correct order.

Usage:
    python3 bootstrap.py

This is the ONE command to set up everything!

Steps:
1. Create database tables (migrate_brands.py)
2. Sync themes from manifest.yaml to database
3. Cleanup orphaned associations
4. Verify system integrity
5. Report status

Self-healing: Safe to run multiple times.
"""

import os
import sys
from datetime import datetime


def print_header(title):
    """Print formatted section header"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_step(step_num, total_steps, description):
    """Print step indicator"""
    print(f"[{step_num}/{total_steps}] {description}...")
    print()


def step_1_create_tables():
    """Create database tables"""
    print_step(1, 5, "Creating database tables")

    try:
        from migrate_brands import migrate
        migrate()
        print("✅ Tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def step_2_sync_brands():
    """Sync brands from manifest.yaml"""
    print_step(2, 5, "Syncing brands from manifest.yaml")

    try:
        from init_brands_from_manifest import sync_brands_from_manifest
        stats = sync_brands_from_manifest()

        if stats['added'] > 0 or stats['updated'] > 0:
            print(f"✅ Synced {stats['added']} new brands, updated {stats['updated']}")
        else:
            print("✅ All brands already synced")

        return True
    except Exception as e:
        print(f"❌ Error syncing brands: {e}")
        return False


def step_3_cleanup_orphans():
    """Cleanup orphaned associations"""
    print_step(3, 5, "Cleaning up orphaned associations")

    try:
        from cleanup_orphaned_associations import cleanup_orphaned_associations, verify_cleanup

        deleted = cleanup_orphaned_associations(dry_run=False)

        if deleted > 0:
            print(f"✅ Cleaned up {deleted} orphaned associations")
            verify_cleanup()
        else:
            print("✅ No orphaned associations found")

        return True
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
        return False


def step_4_verify_system():
    """Verify system integrity"""
    print_step(4, 5, "Verifying system integrity")

    try:
        from database import get_db

        db = get_db()

        # Count brands
        brands_count = db.execute('SELECT COUNT(*) as count FROM brands').fetchone()['count']

        # Count posts
        posts_count = db.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count']

        # Count brand-post associations
        associations_count = db.execute('SELECT COUNT(*) as count FROM brand_posts').fetchone()['count']

        # Count valid associations
        valid_associations = db.execute('''
            SELECT COUNT(*) as count
            FROM brand_posts
            WHERE brand_id IN (SELECT id FROM brands)
        ''').fetchone()['count']

        # Check ML models
        ml_models_count = db.execute('''
            SELECT COUNT(*) as count
            FROM ml_models
            WHERE model_type IN ('brand_voice_classifier', 'brand_emoji_patterns')
        ''').fetchone()['count']

        db.close()

        # Print report
        print("📊 System Status:")
        print(f"  Brands: {brands_count}")
        print(f"  Posts: {posts_count}")
        print(f"  Brand-post associations: {associations_count}")
        print(f"  Valid associations: {valid_associations}")
        print(f"  ML models trained: {ml_models_count}")
        print()

        # Check if ready
        if brands_count == 0:
            print("⚠️  No brands found! Check manifest.yaml")
            return False

        if associations_count != valid_associations:
            print(f"⚠️  {associations_count - valid_associations} orphaned associations remain!")
            return False

        print("✅ System integrity verified")
        return True

    except Exception as e:
        print(f"❌ Error verifying system: {e}")
        return False


def step_5_ready_check():
    """Check if system is ready for training"""
    print_step(5, 5, "Checking if ready for ML training")

    try:
        from database import get_db

        db = get_db()

        # Check minimum requirements
        brands_count = db.execute('SELECT COUNT(*) FROM brands').fetchone()[0]
        posts_with_brands = db.execute('''
            SELECT COUNT(DISTINCT post_id)
            FROM brand_posts
            WHERE brand_id IN (SELECT id FROM brands)
        ''').fetchone()[0]

        db.close()

        print(f"  Brands available: {brands_count}")
        print(f"  Posts linked to brands: {posts_with_brands}")
        print()

        if brands_count < 2:
            print("⚠️  Need at least 2 brands for training")
            print("   Add more themes to manifest.yaml")
            return False

        if posts_with_brands < 5:
            print("⚠️  Need at least 5 posts linked to brands")
            print("   Run: python3 classify_posts_by_brand.py")
            return False

        print("✅ System ready for ML training!")
        print()
        print("Next steps:")
        print("  1. Visit http://localhost:5001/admin/automation")
        print("  2. Click '🎭 Train Models' button")
        print("  3. Test predictions at /api/brand/predict")
        print()

        return True

    except Exception as e:
        print(f"❌ Error in ready check: {e}")
        return False


def main():
    """Run complete bootstrap process"""
    print_header("🚀 Soulfra Brand System Bootstrap")

    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Track success
    steps_passed = 0
    total_steps = 5

    # Run steps
    if step_1_create_tables():
        steps_passed += 1

    if step_2_sync_brands():
        steps_passed += 1

    if step_3_cleanup_orphans():
        steps_passed += 1

    if step_4_verify_system():
        steps_passed += 1

    if step_5_ready_check():
        steps_passed += 1

    # Final report
    print_header("📊 Bootstrap Summary")

    print(f"Steps completed: {steps_passed}/{total_steps}")
    print()

    if steps_passed == total_steps:
        print("✅ BOOTSTRAP SUCCESSFUL!")
        print()
        print("🎉 Your brand voice ML system is ready!")
        print()
        print("Try these commands:")
        print("  python3 brand_vocabulary_trainer.py")
        print("  python3 emoji_pattern_analyzer.py")
        print("  python3 brand_voice_generator.py")
        print()
    else:
        print("⚠️  BOOTSTRAP INCOMPLETE")
        print()
        print(f"Failed at step {steps_passed + 1}")
        print("Check error messages above for details")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
