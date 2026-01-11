#!/usr/bin/env python3
"""
Clean Test Data - Remove Auto-Generated Seed Data

Removes fake users and test content, keeping only:
- Admin user (the real human)
- Core AI personas (calriven, deathtodata, theauditor, soulfra)
- Clears test posts/comments from seed scripts

Usage:
    python3 clean_test_data.py --dry-run    # See what would be deleted
    python3 clean_test_data.py              # Actually delete test data
    python3 clean_test_data.py --keep-all-ai  # Keep ALL AI personas
"""

import sqlite3
import argparse
from datetime import datetime

DB_PATH = 'soulfra.db'

# Core users to KEEP
KEEP_USERS = [
    'admin',  # Real human user
    'calriven',  # Core AI persona
    'deathtodata',  # Core AI persona
    'theauditor',  # Core AI persona
    'soulfra',  # Core AI persona
]

# Test users to REMOVE (auto-generated from seed scripts)
TEST_USERS = [
    'alice',
    'philosopher_king',
    'data_skeptic',
    'science_explorer',
    'culture_critic',
    'freedom_builder',
    'ocean-dreams',
    'ollama',
    'soulassistant',
    'testbrand-auto',
]


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def show_current_state():
    """Display current database state"""
    conn = get_db()

    print("\n" + "=" * 70)
    print("CURRENT DATABASE STATE")
    print("=" * 70)

    # Users breakdown
    total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    ai_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_ai_persona = 1").fetchone()['count']
    human_users = total_users - ai_users

    print(f"\nUsers: {total_users} total ({human_users} human, {ai_users} AI)")

    # Show all users
    users = conn.execute("SELECT username, is_ai_persona, created_at FROM users ORDER BY created_at").fetchall()
    for user in users:
        persona_type = "AI" if user['is_ai_persona'] else "HUMAN"
        status = "KEEP" if user['username'] in KEEP_USERS else "DELETE"
        print(f"  [{persona_type:6}] [{status:6}] {user['username']:20} (created {user['created_at'][:10]})")

    # Content counts
    posts = conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']
    comments = conn.execute("SELECT COUNT(*) as count FROM comments").fetchone()['count']

    print(f"\nContent: {posts} posts, {comments} comments")

    conn.close()


def analyze_deletion(dry_run=True):
    """Show what would be deleted"""
    conn = get_db()

    print("\n" + "=" * 70)
    print("DELETION ANALYSIS" + (" (DRY RUN)" if dry_run else " (REAL)"))
    print("=" * 70)

    # Get user IDs to delete
    placeholders = ','.join(['?' for _ in TEST_USERS])
    users_to_delete = conn.execute(
        f"SELECT id, username FROM users WHERE username IN ({placeholders})",
        TEST_USERS
    ).fetchall()

    if not users_to_delete:
        print("\nNo test users found to delete.")
        conn.close()
        return 0, 0

    user_ids_to_delete = [u['id'] for u in users_to_delete]

    print(f"\nUsers to DELETE: {len(users_to_delete)}")
    for user in users_to_delete:
        # Count their content
        posts_count = conn.execute(
            "SELECT COUNT(*) as count FROM posts WHERE user_id = ?",
            (user['id'],)
        ).fetchone()['count']

        comments_count = conn.execute(
            "SELECT COUNT(*) as count FROM comments WHERE user_id = ?",
            (user['id'],)
        ).fetchone()['count']

        print(f"  - {user['username']:20} ({posts_count} posts, {comments_count} comments)")

    # Total content to delete
    id_placeholders = ','.join(['?' for _ in user_ids_to_delete])

    total_posts_to_delete = conn.execute(
        f"SELECT COUNT(*) as count FROM posts WHERE user_id IN ({id_placeholders})",
        user_ids_to_delete
    ).fetchone()['count']

    total_comments_to_delete = conn.execute(
        f"SELECT COUNT(*) as count FROM comments WHERE user_id IN ({id_placeholders})",
        user_ids_to_delete
    ).fetchone()['count']

    print(f"\nTotal Content to DELETE:")
    print(f"  - {total_posts_to_delete} posts")
    print(f"  - {total_comments_to_delete} comments")
    print(f"  - {len(users_to_delete)} users")

    # What will remain
    remaining_users = conn.execute(
        f"SELECT COUNT(*) as count FROM users WHERE username IN ({','.join(['?' for _ in KEEP_USERS])})",
        KEEP_USERS
    ).fetchone()['count']

    remaining_posts = conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count'] - total_posts_to_delete
    remaining_comments = conn.execute("SELECT COUNT(*) as count FROM comments").fetchone()['count'] - total_comments_to_delete

    print(f"\nAfter Cleanup (WILL KEEP):")
    print(f"  - {remaining_users} users (admin + 4 core AI personas)")
    print(f"  - {remaining_posts} posts")
    print(f"  - {remaining_comments} comments")

    conn.close()

    return len(users_to_delete), total_posts_to_delete + total_comments_to_delete


def clean_test_data(dry_run=True):
    """Remove test users and their content"""

    if dry_run:
        print("\n[DRY RUN MODE] No data will be deleted")
        analyze_deletion(dry_run=True)
        return

    conn = get_db()

    try:
        # Get user IDs to delete
        placeholders = ','.join(['?' for _ in TEST_USERS])
        users_to_delete = conn.execute(
            f"SELECT id, username FROM users WHERE username IN ({placeholders})",
            TEST_USERS
        ).fetchall()

        if not users_to_delete:
            print("\nNo test users found. Database is already clean!")
            return

        user_ids = [u['id'] for u in users_to_delete]
        id_placeholders = ','.join(['?' for _ in user_ids])

        print("\n" + "=" * 70)
        print("DELETING TEST DATA")
        print("=" * 70)

        # Delete comments by these users
        conn.execute(
            f"DELETE FROM comments WHERE user_id IN ({id_placeholders})",
            user_ids
        )
        print(f"[OK] Deleted comments by test users")

        # Delete posts by these users
        conn.execute(
            f"DELETE FROM posts WHERE user_id IN ({id_placeholders})",
            user_ids
        )
        print(f"[OK] Deleted posts by test users")

        # Delete the users themselves
        conn.execute(
            f"DELETE FROM users WHERE id IN ({id_placeholders})",
            user_ids
        )
        print(f"[OK] Deleted {len(user_ids)} test users")

        # Clean up related data
        conn.execute("DELETE FROM newsletter_subscribers WHERE user_id NOT IN (SELECT id FROM users)")
        print(f"[OK] Cleaned up orphaned newsletter subscriptions")

        conn.execute("DELETE FROM api_call_logs WHERE user_id NOT IN (SELECT id FROM users)")
        print(f"[OK] Cleaned up orphaned API logs")

        conn.commit()

        print("\n" + "=" * 70)
        print("CLEANUP COMPLETE!")
        print("=" * 70)

        # Show final state
        final_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        final_posts = conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()['count']
        final_comments = conn.execute("SELECT COUNT(*) as count FROM comments").fetchone()['count']

        print(f"\nFinal State:")
        print(f"  Users: {final_users}")
        print(f"  Posts: {final_posts}")
        print(f"  Comments: {final_comments}")

        print("\nRemaining users:")
        remaining = conn.execute("SELECT username, is_ai_persona FROM users ORDER BY username").fetchall()
        for user in remaining:
            persona_type = "AI" if user['is_ai_persona'] else "HUMAN"
            print(f"  - {user['username']:20} ({persona_type})")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Cleanup failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean test data from Soulfra database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--show-current', action='store_true', help='Show current database state only')
    parser.add_argument('--keep-all-ai', action='store_true', help='Keep all AI personas, only delete human test users')

    args = parser.parse_args()

    if args.keep_all_ai:
        # Modify TEST_USERS to only include human test accounts
        TEST_USERS = [u for u in TEST_USERS if u not in ['ocean-dreams', 'ollama', 'soulassistant', 'testbrand-auto']]

    if args.show_current:
        show_current_state()
    elif args.dry_run:
        show_current_state()
        clean_test_data(dry_run=True)
        print("\n[TIP] Run without --dry-run to actually delete the data")
    else:
        show_current_state()

        user_count, content_count = analyze_deletion(dry_run=False)

        if user_count == 0:
            print("\nNothing to delete. Exiting.")
            exit(0)

        print("\n" + "=" * 70)
        confirm = input(f"\nDelete {user_count} users and {content_count} pieces of content? (yes/no): ")

        if confirm.lower() in ['yes', 'y']:
            clean_test_data(dry_run=False)
        else:
            print("\nCancelled. No data was deleted.")
