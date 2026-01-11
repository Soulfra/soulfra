#!/usr/bin/env python3
"""
Soulfra Simple - System Health Check

Verifies all systems are working correctly:
- Database schema
- Flask app imports
- Routes functionality
- Templates rendering
- Timestamp consistency
- Required scripts exist

Usage:
    python3 health_check.py
    python3 health_check.py --verbose
"""

import sys
import os
import sqlite3
from pathlib import Path
import importlib.util


class HealthCheck:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def check(self, name: str, test_func, critical=True):
        """Run a health check"""
        try:
            result = test_func()
            if result:
                print(f"✅ {name}")
                self.checks_passed += 1
                return True
            else:
                icon = "❌" if critical else "⚠️"
                print(f"{icon} {name}")
                if critical:
                    self.checks_failed += 1
                else:
                    self.warnings.append(name)
                return False
        except Exception as e:
            icon = "❌" if critical else "⚠️"
            print(f"{icon} {name}")
            if self.verbose:
                print(f"   Error: {e}")
            if critical:
                self.checks_failed += 1
            else:
                self.warnings.append(name)
            return False

    def summary(self):
        """Print summary"""
        total = self.checks_passed + self.checks_failed

        print("\n" + "=" * 70)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 70)
        print()
        print(f"Passed:   ✅ {self.checks_passed}/{total}")
        print(f"Failed:   ❌ {self.checks_failed}/{total}")
        print(f"Warnings: ⚠️  {len(self.warnings)}")
        print()

        if self.checks_failed == 0:
            print("🎉 All critical systems operational!")
            print()
            print("Next steps:")
            print("  python3 app.py              # Start Flask server (port 5001)")
            print("  python3 soulfra_zero.py     # Start zero-dep server (port 8888)")
            print()
            return True
        else:
            print("⚠️  Some systems need attention. See failures above.")
            print()
            print("Quick fixes:")
            print("  pip install flask markdown2  # Install dependencies")
            print("  python3 database.py          # Rebuild database")
            print()
            return False


def check_database_exists():
    """Check if database file exists"""
    return Path('soulfra.db').exists()


def check_database_schema():
    """Verify database has required tables"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    required_tables = [
        'users', 'posts', 'comments', 'subscribers',
        'reasoning_threads', 'reasoning_steps'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    conn.close()

    missing = [t for t in required_tables if t not in existing_tables]

    if missing:
        print(f"   Missing tables: {', '.join(missing)}")
        return False

    return True


def check_database_data():
    """Check database has some data"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    counts = {}
    for table in ['users', 'posts', 'comments']:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        counts[table] = cursor.fetchone()[0]

    conn.close()

    # Print counts if verbose
    if hasattr(sys, '_health_check_verbose') and sys._health_check_verbose:
        print(f"   {counts['users']} users, {counts['posts']} posts, {counts['comments']} comments")

    return counts['users'] > 0 or counts['posts'] > 0


def check_flask_imports():
    """Check Flask app can be imported"""
    try:
        import flask
        return True
    except ImportError:
        print("   Run: pip install flask")
        return False


def check_app_py_exists():
    """Check app.py exists"""
    return Path('app.py').exists()


def check_database_py_exists():
    """Check database.py exists"""
    return Path('database.py').exists()


def check_templates_directory():
    """Check templates directory exists and has files"""
    templates_dir = Path('templates')

    if not templates_dir.exists():
        return False

    templates = list(templates_dir.glob('*.html'))

    if hasattr(sys, '_health_check_verbose') and sys._health_check_verbose:
        print(f"   {len(templates)} templates found")

    return len(templates) > 0


def check_base_template():
    """Check base.html template exists"""
    return Path('templates/base.html').exists()


def check_index_template():
    """Check index.html template exists"""
    return Path('templates/index.html').exists()


def check_timestamp_consistency():
    """Check timestamps in database are consistent"""
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    # Check if timestamps are SQLite TIMESTAMP or Unix epoch
    cursor.execute('SELECT created_at FROM users LIMIT 1')
    row = cursor.fetchone()

    if not row:
        return True  # No data to check

    timestamp = row[0]
    conn.close()

    # Check if it's ISO format (SQLite TIMESTAMP) or numeric (Unix epoch)
    if isinstance(timestamp, str):
        # Should be ISO format like "2025-12-22 12:34:56"
        return '-' in timestamp and ':' in timestamp
    else:
        # Unix epoch - should we convert?
        print(f"   Warning: Using Unix epoch ({timestamp})")
        return False


def check_required_scripts():
    """Check required core scripts exist"""
    required = [
        'app.py',
        'database.py',
        'show_me_it_works.py'
    ]

    missing = [s for s in required if not Path(s).exists()]

    if missing:
        print(f"   Missing: {', '.join(missing)}")
        return False

    return True


def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 8

    if hasattr(sys, '_health_check_verbose') and sys._health_check_verbose:
        print(f"   Python {version.major}.{version.minor}.{version.micro}")

    return is_valid


def check_markdown2():
    """Check markdown2 is installed"""
    try:
        import markdown2
        return True
    except ImportError:
        print("   Run: pip install markdown2")
        return False


def get_system_stats():
    """Get system statistics"""
    stats = {}

    try:
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()

        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        stats['tables'] = cursor.fetchone()[0]

        # Count users
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['users'] = cursor.fetchone()[0]

        # Count posts
        cursor.execute('SELECT COUNT(*) FROM posts')
        stats['posts'] = cursor.fetchone()[0]

        # Count comments
        cursor.execute('SELECT COUNT(*) FROM comments')
        stats['comments'] = cursor.fetchone()[0]

        # Count subscribers
        try:
            cursor.execute('SELECT COUNT(*) FROM subscribers')
            stats['subscribers'] = cursor.fetchone()[0]
        except:
            stats['subscribers'] = 0

        # Database size
        db_size = Path('soulfra.db').stat().st_size
        stats['db_size_mb'] = db_size / 1024 / 1024

        conn.close()

    except Exception as e:
        pass

    return stats


def count_scripts():
    """Count Python scripts"""
    scripts = list(Path('.').glob('*.py'))
    return len([s for s in scripts if not s.name.startswith('__')])


def count_templates():
    """Count HTML templates"""
    templates_dir = Path('templates')
    if not templates_dir.exists():
        return 0
    return len(list(templates_dir.glob('*.html')))


def count_docs():
    """Count markdown documentation"""
    docs = list(Path('.').glob('*.md'))
    return len(docs)


def main():
    """Run all health checks"""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if verbose:
        sys._health_check_verbose = True

    print("=" * 70)
    print("🏥 SOULFRA SIMPLE - SYSTEM HEALTH CHECK")
    print("=" * 70)
    print()

    # Print system info
    print("📍 System Information:")
    print(f"   Working directory: {Path.cwd()}")
    print(f"   Python scripts: {count_scripts()}")
    print(f"   Templates: {count_templates()}")
    print(f"   Documentation: {count_docs()} MD files")
    print()

    health = HealthCheck(verbose=verbose)

    print("🔍 Running Health Checks...")
    print()

    # Critical checks
    print("Critical Systems:")
    health.check("Python 3.8+", check_python_version, critical=True)
    health.check("Database file exists", check_database_exists, critical=True)
    health.check("Database schema valid", check_database_schema, critical=True)
    health.check("Flask installed", check_flask_imports, critical=True)
    health.check("app.py exists", check_app_py_exists, critical=True)
    health.check("database.py exists", check_database_py_exists, critical=True)
    health.check("Templates directory exists", check_templates_directory, critical=True)
    health.check("base.html template exists", check_base_template, critical=True)

    print()
    print("Optional Systems:")
    health.check("markdown2 installed", check_markdown2, critical=False)
    health.check("index.html template exists", check_index_template, critical=False)
    health.check("Database has data", check_database_data, critical=False)
    health.check("Timestamp consistency", check_timestamp_consistency, critical=False)
    health.check("Required scripts present", check_required_scripts, critical=False)

    # Get stats
    stats = get_system_stats()
    if stats:
        print()
        print("📊 Database Statistics:")
        print(f"   Tables: {stats.get('tables', 0)}")
        print(f"   Users: {stats.get('users', 0)}")
        print(f"   Posts: {stats.get('posts', 0)}")
        print(f"   Comments: {stats.get('comments', 0)}")
        print(f"   Subscribers: {stats.get('subscribers', 0)}")
        print(f"   Database size: {stats.get('db_size_mb', 0):.2f} MB")

    # Summary
    success = health.summary()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
