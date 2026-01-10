#!/usr/bin/env python3
"""
Cleanup Orphaned Brand-Post Associations - Pure Python Stdlib

Finds and removes brand_posts entries that reference non-existent brands.
This happens when brands are deleted but their associations remain.

Usage:
    python3 cleanup_orphaned_associations.py

Or with dry-run:
    python3 cleanup_orphaned_associations.py --dry-run
"""

import sys
from database import get_db


def find_orphaned_associations():
    """
    Find brand_posts entries pointing to non-existent brands

    Returns:
        list: [(brand_id, post_id, relevance_score), ...]
    """
    db = get_db()

    # Get all brand_posts associations
    all_associations = db.execute('''
        SELECT brand_id, post_id, relevance_score
        FROM brand_posts
    ''').fetchall()

    # Get valid brand IDs
    valid_brand_ids = set()
    for row in db.execute('SELECT id FROM brands').fetchall():
        valid_brand_ids.add(row['id'])

    db.close()

    # Find orphaned ones
    orphaned = []

    for assoc in all_associations:
        if assoc['brand_id'] not in valid_brand_ids:
            orphaned.append((assoc['brand_id'], assoc['post_id'], assoc['relevance_score']))

    return orphaned


def cleanup_orphaned_associations(dry_run=False):
    """
    Remove orphaned brand-post associations

    Args:
        dry_run: If True, just report what would be deleted

    Returns:
        int: Number of associations deleted
    """
    print("=" * 60)
    print("🧹 Cleanup Orphaned Brand-Post Associations")
    print("=" * 60)
    print()

    # Find orphaned
    orphaned = find_orphaned_associations()

    if not orphaned:
        print("✅ No orphaned associations found!")
        print("   All brand_posts entries point to valid brands.")
        return 0

    print(f"⚠️  Found {len(orphaned)} orphaned associations")
    print()

    # Group by brand_id
    by_brand = {}
    for brand_id, post_id, score in orphaned:
        if brand_id not in by_brand:
            by_brand[brand_id] = []
        by_brand[brand_id].append((post_id, score))

    print("📋 Orphaned associations by brand ID:")
    for brand_id, posts in sorted(by_brand.items()):
        print(f"  Brand ID {brand_id}: {len(posts)} posts")

    print()

    if dry_run:
        print("🔍 DRY RUN - No changes made")
        print()
        print("To actually delete these, run without --dry-run:")
        print("  python3 cleanup_orphaned_associations.py")
        return 0

    # Delete orphaned associations
    print("🗑️  Deleting orphaned associations...")

    db = get_db()

    # Delete where brand_id not in valid brands
    cursor = db.execute('''
        DELETE FROM brand_posts
        WHERE brand_id NOT IN (SELECT id FROM brands)
    ''')

    deleted_count = cursor.rowcount

    db.commit()
    db.close()

    print(f"✅ Deleted {deleted_count} orphaned associations")
    print()

    return deleted_count


def verify_cleanup():
    """Verify cleanup was successful"""
    print("🔍 Verifying cleanup...")

    orphaned = find_orphaned_associations()

    if orphaned:
        print(f"⚠️  Still found {len(orphaned)} orphaned associations!")
        return False
    else:
        print("✅ All brand_posts associations are now valid!")
        return True


def suggest_reclassification():
    """
    Suggest re-classifying posts to correct brands

    Returns:
        dict: Suggestions for re-classification
    """
    print()
    print("💡 Suggestion: Re-classify posts to correct brands")
    print()
    print("After cleanup, you can re-run classification:")
    print("  python3 classify_posts_by_brand.py")
    print()
    print("This will:")
    print("  1. Analyze content of unlinked posts")
    print("  2. Match to appropriate brands based on keywords")
    print("  3. Create new brand_posts associations")
    print()


def main():
    """CLI interface"""
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("🔍 Running in DRY RUN mode")
        print()

    # Run cleanup
    deleted = cleanup_orphaned_associations(dry_run=dry_run)

    if not dry_run and deleted > 0:
        # Verify
        print()
        verify_cleanup()

        # Suggest reclassification
        suggest_reclassification()


if __name__ == '__main__':
    main()
