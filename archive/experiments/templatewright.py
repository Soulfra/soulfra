#!/usr/bin/env python3
"""
templatewright.py - Template Version Management CLI

Manages template versioning, testing, and domain rotation contexts.
Similar to shipwright.py but for templates.

Usage:
  ./templatewright.py list <template_name>
  ./templatewright.py upgrade <template_name> --to <ship_class> --changelog "Description"
  ./templatewright.py test <template_name> <version>
  ./templatewright.py changelog <template_name> <version>
  ./templatewright.py rotate <domain> --add-question "What to build?"
  ./templatewright.py rotate <domain> --add-theme "ocean"
  ./templatewright.py rotate <domain> --status
"""

import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = 'soulfra.db'

SHIP_CLASSES = {
    'dinghy': {'lines': '~26 lines', 'description': 'Minimal - emoji + colors'},
    'schooner': {'lines': '50-80 lines', 'description': 'Enhanced - adds layout'},
    'frigate': {'lines': '120-180 lines', 'description': 'Advanced - full features'},
    'galleon': {'lines': '250+ lines', 'description': 'Complete - all bells and whistles'}
}

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def list_versions(template_name):
    """List all versions of a template"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT version_number, ship_class, line_count, active, created_at
        FROM template_versions
        WHERE template_name = ?
        ORDER BY created_at DESC
    """, (template_name,))

    versions = cursor.fetchall()

    if not versions:
        print(f"❌ No versions found for template: {template_name}")
        return

    print(f"\n📄 Template: {template_name}")
    print("=" * 70)

    for version, ship_class, lines, active, created_at in versions:
        status = "✅ ACTIVE" if active else "  "
        print(f"{status} {version:8} | {ship_class:10} | {lines or '?':5} lines | {created_at[:10]}")

    conn.close()

def upgrade_template(template_name, ship_class, changelog):
    """Create a new version of a template"""
    if ship_class not in SHIP_CLASSES:
        print(f"❌ Invalid ship class. Choose from: {', '.join(SHIP_CLASSES.keys())}")
        return

    conn = get_db()
    cursor = conn.cursor()

    # Get current highest version
    cursor.execute("""
        SELECT version_number FROM template_versions
        WHERE template_name = ?
        ORDER BY version_number DESC
        LIMIT 1
    """, (template_name,))

    result = cursor.fetchone()
    if result:
        current = result[0]
        # Extract number from v1, v2, etc.
        version_num = int(current.replace('v', '')) + 1
        new_version = f'v{version_num}'
    else:
        new_version = 'v1'

    file_path = f'templates/{template_name}/{new_version}_{ship_class}.html'

    # Create the version record
    cursor.execute("""
        INSERT INTO template_versions
        (template_name, version_number, ship_class, file_path, changelog, active)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (template_name, new_version, ship_class, file_path, changelog))

    conn.commit()
    version_id = cursor.lastrowid

    print(f"✅ Created {template_name} {new_version} ({ship_class})")
    print(f"📁 File path: {file_path}")
    print(f"📝 Next: Create the template file at {file_path}")

    # Create directory if needed
    template_dir = Path(f'templates/{template_name}')
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder template if it doesn't exist
    template_file = Path(file_path)
    if not template_file.exists():
        placeholder = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template_name.title()} - {new_version} {ship_class}</title>
    <style>
        /* {ship_class} class styles - {SHIP_CLASSES[ship_class]['description']} */
        body {{
            font-family: system-ui, sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <h1>{template_name.title()} - {new_version}</h1>
    <p>Ship class: <strong>{ship_class}</strong></p>

    <!-- TODO: Add template content here -->

    <footer>
        <small>Template: {template_name} | Version: {new_version} | Class: {ship_class}</small>
    </footer>
</body>
</html>
"""
        template_file.write_text(placeholder)
        print(f"📝 Created placeholder template at {file_path}")

    conn.close()

def show_changelog(template_name, version):
    """Show changelog for a specific version"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT changelog, ship_class, created_at
        FROM template_versions
        WHERE template_name = ? AND version_number = ?
    """, (template_name, version))

    result = cursor.fetchone()

    if not result:
        print(f"❌ Version {version} not found for {template_name}")
        return

    changelog, ship_class, created_at = result

    print(f"\n📄 {template_name} {version} ({ship_class})")
    print(f"📅 Created: {created_at}")
    print("=" * 70)
    print(changelog or "No changelog available")

    conn.close()

def test_template(template_name, version):
    """Run tests for a template version"""
    conn = get_db()
    cursor = conn.cursor()

    # Get version ID
    cursor.execute("""
        SELECT id, file_path FROM template_versions
        WHERE template_name = ? AND version_number = ?
    """, (template_name, version))

    result = cursor.fetchone()
    if not result:
        print(f"❌ Version {version} not found for {template_name}")
        return

    version_id, file_path = result

    # Check if template file exists
    if not Path(file_path).exists():
        print(f"❌ Template file not found: {file_path}")
        return

    print(f"🧪 Testing {template_name} {version}...")

    # Basic test: can we read the file?
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            line_count = len(content.split('\n'))

        # Record test result
        cursor.execute("""
            INSERT INTO template_tests
            (template_version_id, test_name, test_file, status)
            VALUES (?, ?, ?, ?)
        """, (version_id, 'test_file_readable', 'templatewright.py:basic_tests', 'pass'))

        # Update line count
        cursor.execute("""
            UPDATE template_versions
            SET line_count = ?
            WHERE id = ?
        """, (line_count, version_id))

        conn.commit()

        print(f"  ✅ File readable: {line_count} lines")
        print(f"  ✅ Tests passed for {template_name} {version}")

    except Exception as e:
        cursor.execute("""
            INSERT INTO template_tests
            (template_version_id, test_name, test_file, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (version_id, 'test_file_readable', 'templatewright.py:basic_tests', 'fail', str(e)))

        conn.commit()
        print(f"  ❌ Test failed: {e}")

    conn.close()

def rotate_add_question(domain, question):
    """Add a rotating question to a domain"""
    conn = get_db()
    cursor = conn.cursor()

    # Get current max rotation order
    cursor.execute("""
        SELECT COALESCE(MAX(rotation_order), 0)
        FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'question'
    """, (domain,))

    max_order = cursor.fetchone()[0]
    new_order = max_order + 1

    cursor.execute("""
        INSERT INTO domain_contexts
        (domain_slug, context_type, content, rotation_order, active)
        VALUES (?, 'question', ?, ?, 1)
    """, (domain, question, new_order))

    conn.commit()
    print(f"✅ Added question #{new_order} to {domain}: \"{question}\"")
    conn.close()

def rotate_add_theme(domain, theme):
    """Add a rotating theme to a domain"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(MAX(rotation_order), 0)
        FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'theme'
    """, (domain,))

    max_order = cursor.fetchone()[0]
    new_order = max_order + 1

    cursor.execute("""
        INSERT INTO domain_contexts
        (domain_slug, context_type, content, rotation_order, active)
        VALUES (?, 'theme', ?, ?, 1)
    """, (domain, theme, new_order))

    conn.commit()
    print(f"✅ Added theme #{new_order} to {domain}: \"{theme}\"")
    conn.close()

def rotate_status(domain):
    """Show rotation status for a domain"""
    conn = get_db()
    cursor = conn.cursor()

    # Get rotation state
    cursor.execute("""
        SELECT current_question_index, current_theme_index, last_rotated_at
        FROM domain_rotation_state
        WHERE domain_slug = ?
    """, (domain,))

    state = cursor.fetchone()
    if not state:
        print(f"❌ No rotation state found for domain: {domain}")
        return

    q_idx, t_idx, last_rotated = state

    # Get questions
    cursor.execute("""
        SELECT rotation_order, content, active
        FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'question'
        ORDER BY rotation_order
    """, (domain,))

    questions = cursor.fetchall()

    # Get themes
    cursor.execute("""
        SELECT rotation_order, content, active
        FROM domain_contexts
        WHERE domain_slug = ? AND context_type = 'theme'
        ORDER BY rotation_order
    """, (domain,))

    themes = cursor.fetchall()

    print(f"\n🔄 Rotation Status: {domain}")
    print("=" * 70)
    print(f"Last rotated: {last_rotated}")
    print(f"\n❓ Questions (current: #{q_idx}):")
    for order, content, active in questions:
        marker = "→" if order == q_idx else " "
        status = "✓" if active else "✗"
        print(f"  {marker} {status} #{order}: {content}")

    print(f"\n🎨 Themes (current: #{t_idx}):")
    for order, content, active in themes:
        marker = "→" if order == t_idx else " "
        status = "✓" if active else "✗"
        print(f"  {marker} {status} #{order}: {content}")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Template Version Management')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # list command
    list_parser = subparsers.add_parser('list', help='List versions of a template')
    list_parser.add_argument('template_name', help='Template name (e.g., signup, leaderboard)')

    # upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Create new version of template')
    upgrade_parser.add_argument('template_name', help='Template name')
    upgrade_parser.add_argument('--to', dest='ship_class', required=True,
                                choices=SHIP_CLASSES.keys(), help='Ship class')
    upgrade_parser.add_argument('--changelog', required=True, help='Changelog description')

    # changelog command
    changelog_parser = subparsers.add_parser('changelog', help='Show changelog for version')
    changelog_parser.add_argument('template_name', help='Template name')
    changelog_parser.add_argument('version', help='Version (e.g., v1, v2)')

    # test command
    test_parser = subparsers.add_parser('test', help='Run tests for template version')
    test_parser.add_argument('template_name', help='Template name')
    test_parser.add_argument('version', help='Version (e.g., v1, v2)')

    # rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Manage domain rotation')
    rotate_parser.add_argument('domain', help='Domain slug (e.g., ocean-dreams)')
    rotate_parser.add_argument('--add-question', dest='question', help='Add rotating question')
    rotate_parser.add_argument('--add-theme', dest='theme', help='Add rotating theme')
    rotate_parser.add_argument('--status', action='store_true', help='Show rotation status')

    args = parser.parse_args()

    if args.command == 'list':
        list_versions(args.template_name)
    elif args.command == 'upgrade':
        upgrade_template(args.template_name, args.ship_class, args.changelog)
    elif args.command == 'changelog':
        show_changelog(args.template_name, args.version)
    elif args.command == 'test':
        test_template(args.template_name, args.version)
    elif args.command == 'rotate':
        if args.question:
            rotate_add_question(args.domain, args.question)
        elif args.theme:
            rotate_add_theme(args.domain, args.theme)
        elif args.status:
            rotate_status(args.domain)
        else:
            print("❌ Specify --add-question, --add-theme, or --status")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
