#!/usr/bin/env python3
"""
Soulfra Compiler - Automation & Consistency Checks

The "compiler" ensures the platform maintains consistency and triggers
automated workflows. Like a build system, it:
- Validates structure (are posts/comments semantically correct?)
- Generates missing assets (avatars, thumbnails)
- Triggers automation (AI analysis, tests)
- Enforces standards

Usage:
    python compiler.py --check          # Check for issues
    python compiler.py --fix            # Auto-fix issues
    python compiler.py --generate-all   # Generate all missing assets
    python compiler.py --trigger-ai     # Trigger AI analysis on unprocessed posts
"""

import argparse
import sys
import os
from database import get_db
from db_helpers import get_user_by_id
from avatar_generator import save_avatar


class SoulframCompiler:
    """Main compiler class for consistency and automation"""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.issues = []
        self.fixes_applied = []

    def log(self, message):
        """Log message if verbose"""
        if self.verbose:
            print(message)

    def add_issue(self, issue_type, description, severity='warning'):
        """Record an issue found"""
        self.issues.append({
            'type': issue_type,
            'description': description,
            'severity': severity
        })

    def add_fix(self, description):
        """Record a fix applied"""
        self.fixes_applied.append(description)

    # ==================== AVATAR CHECKS ====================

    def check_avatars(self):
        """Ensure all users have pixel avatars"""
        self.log("🎨 Checking avatars...")

        conn = get_db()
        users = conn.execute('SELECT id, username FROM users').fetchall()
        conn.close()

        missing = []
        for user in users:
            username = user['username']
            avatar_path = f'static/avatars/generated/{username}.png'

            if not os.path.exists(avatar_path):
                missing.append(username)
                self.add_issue(
                    'missing_avatar',
                    f"User '{username}' missing pixel avatar",
                    severity='error'
                )

        if missing:
            self.log(f"   ❌ {len(missing)} users missing avatars: {', '.join(missing)}")
        else:
            self.log(f"   ✅ All {len(users)} users have pixel avatars")

        return missing

    def fix_avatars(self):
        """Generate missing avatars"""
        missing = self.check_avatars()

        if not missing:
            return

        self.log("\n🔧 Generating missing avatars...")

        for username in missing:
            try:
                output_path = save_avatar(username)
                self.add_fix(f"Generated avatar for {username}")
                self.log(f"   ✅ {username} → {output_path}")
            except Exception as e:
                self.log(f"   ❌ Failed to generate avatar for {username}: {e}")

    # ==================== AI PROCESSING ====================

    def check_ai_processing(self):
        """Find posts that haven't been processed by AI"""
        self.log("\n🤖 Checking AI processing...")

        conn = get_db()
        unprocessed = conn.execute('''
            SELECT id, title, user_id, ai_processed
            FROM posts
            WHERE ai_processed = 0
            ORDER BY id
        ''').fetchall()
        conn.close()

        if unprocessed:
            self.log(f"   ⚠️  {len(unprocessed)} posts not AI-processed:")
            for post in unprocessed:
                author = get_user_by_id(post['user_id'])
                self.log(f"      Post #{post['id']}: {post['title']} (by {author['username']})")
                self.add_issue(
                    'unprocessed_post',
                    f"Post #{post['id']} '{post['title']}' not AI-processed",
                    severity='warning'
                )
        else:
            self.log("   ✅ All posts have been AI-processed")

        return [dict(p) for p in unprocessed]

    def trigger_ai_processing(self, post_id):
        """Trigger AI analysis on a post"""
        from simulate_ai_analysis import simulate_ai_analysis_on_post

        self.log(f"\n🤖 Triggering AI analysis on Post #{post_id}...")

        try:
            success = simulate_ai_analysis_on_post(post_id)

            if success:
                self.add_fix(f"Triggered AI analysis on Post #{post_id}")
                self.log(f"   ✅ AI analysis complete")
            else:
                self.log(f"   ❌ AI analysis failed")

            return success
        except Exception as e:
            self.log(f"   ❌ Error: {e}")
            return False

    # ==================== STRUCTURE VALIDATION ====================

    def check_comment_structure(self):
        """Check for semantically incorrect comments"""
        self.log("\n📝 Checking comment structure...")

        conn = get_db()

        # Check for extremely long comments (likely dumped documentation)
        long_comments = conn.execute('''
            SELECT id, post_id, user_id, LENGTH(content) as length
            FROM comments
            WHERE LENGTH(content) > 5000
            ORDER BY length DESC
        ''').fetchall()

        conn.close()

        if long_comments:
            self.log(f"   ⚠️  {len(long_comments)} extremely long comments (likely docs dumped as comments):")
            for comment in long_comments:
                author = get_user_by_id(comment['user_id'])
                self.log(f"      Comment #{comment['id']} by {author['username']}: {comment['length']} chars")
                self.add_issue(
                    'oversized_comment',
                    f"Comment #{comment['id']} is {comment['length']} chars (should be < 5000)",
                    severity='warning'
                )
        else:
            self.log("   ✅ No oversized comments found")

        return long_comments

    # ==================== REASONING THREADS ====================

    def check_reasoning_threads(self):
        """Ensure reasoning threads are being used properly"""
        self.log("\n🧵 Checking reasoning threads...")

        conn = get_db()

        # Count posts with reasoning threads
        posts_with_threads = conn.execute('''
            SELECT COUNT(DISTINCT post_id) as count
            FROM reasoning_threads
        ''').fetchone()['count']

        total_ai_processed = conn.execute('''
            SELECT COUNT(*) as count
            FROM posts
            WHERE ai_processed = 1
        ''').fetchone()['count']

        conn.close()

        if posts_with_threads < total_ai_processed:
            self.log(f"   ⚠️  {total_ai_processed} posts AI-processed but only {posts_with_threads} have reasoning threads")
            self.add_issue(
                'missing_reasoning_threads',
                f"{total_ai_processed - posts_with_threads} AI-processed posts missing reasoning threads",
                severity='warning'
            )
        else:
            self.log(f"   ✅ {posts_with_threads} posts have reasoning threads")

    # ==================== MAIN CHECKS ====================

    def run_all_checks(self):
        """Run all consistency checks"""
        self.log("=" * 70)
        self.log("🔍 Soulfra Compiler - Running Consistency Checks")
        self.log("=" * 70)

        self.check_avatars()
        self.check_ai_processing()
        self.check_comment_structure()
        self.check_reasoning_threads()

        self.log("\n" + "=" * 70)
        self.log(f"📊 Summary: {len(self.issues)} issues found")
        self.log("=" * 70)

        if self.issues:
            # Group by severity
            errors = [i for i in self.issues if i['severity'] == 'error']
            warnings = [i for i in self.issues if i['severity'] == 'warning']

            if errors:
                self.log(f"\n❌ Errors ({len(errors)}):")
                for issue in errors:
                    self.log(f"   - {issue['description']}")

            if warnings:
                self.log(f"\n⚠️  Warnings ({len(warnings)}):")
                for issue in warnings:
                    self.log(f"   - {issue['description']}")

            return False
        else:
            self.log("\n✅ All checks passed! Platform is consistent.")
            return True

    def run_fixes(self):
        """Run all auto-fixes"""
        self.log("=" * 70)
        self.log("🔧 Soulfra Compiler - Auto-Fixing Issues")
        self.log("=" * 70)

        self.fix_avatars()

        # TODO: Add more auto-fixes as needed

        self.log("\n" + "=" * 70)
        self.log(f"✅ Applied {len(self.fixes_applied)} fixes")
        self.log("=" * 70)

        if self.fixes_applied:
            for fix in self.fixes_applied:
                self.log(f"   - {fix}")


def main():
    parser = argparse.ArgumentParser(
        description='Soulfra Compiler - Automation & Consistency Checks'
    )

    parser.add_argument('--check', action='store_true',
                       help='Run all consistency checks')
    parser.add_argument('--fix', action='store_true',
                       help='Auto-fix issues')
    parser.add_argument('--generate-avatars', action='store_true',
                       help='Generate missing avatars')
    parser.add_argument('--trigger-ai', type=int, metavar='POST_ID',
                       help='Trigger AI analysis on specific post')
    parser.add_argument('--trigger-all-ai', action='store_true',
                       help='Trigger AI analysis on all unprocessed posts')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress output')

    args = parser.parse_args()

    compiler = SoulframCompiler(verbose=not args.quiet)

    # Default: run checks
    if not any([args.check, args.fix, args.generate_avatars, args.trigger_ai, args.trigger_all_ai]):
        args.check = True

    if args.check:
        success = compiler.run_all_checks()
        sys.exit(0 if success else 1)

    if args.fix:
        compiler.run_fixes()

    if args.generate_avatars:
        compiler.fix_avatars()

    if args.trigger_ai:
        compiler.trigger_ai_processing(args.trigger_ai)

    if args.trigger_all_ai:
        unprocessed = compiler.check_ai_processing()
        for post in unprocessed:
            compiler.trigger_ai_processing(post['id'])


if __name__ == '__main__':
    main()
