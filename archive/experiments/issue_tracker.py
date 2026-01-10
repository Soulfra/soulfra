#!/usr/bin/env python3
"""
Issue Tracker with QR Codes - Offline-First Bug/Task Tracking

This implements a simple issue tracker with QR code integration:
1. Create and manage issues/tasks offline
2. Generate QR codes for each issue
3. Scan QR codes to view/update issues
4. Print QR codes for physical tracking
5. Export issues as QR sheets

WHY THIS EXISTS:
- Track bugs/tasks completely offline
- Physical QR codes on whiteboards/printouts
- No external issue tracker needed
- Scan QR code with phone to view issue
- Works on local network

Usage:
    # Create issue
    from issue_tracker import create_issue

    issue_id = create_issue(
        title='Fix login bug',
        description='Users cannot login with special characters in password',
        priority='high',
        tags=['bug', 'authentication']
    )

    # Generate QR code
    python3 issue_tracker.py qr <issue_id>

    # List issues
    python3 issue_tracker.py list
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import json


def _get_db():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def _init_database():
    """Initialize issue tracker tables"""
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            assignee TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            tags TEXT,
            metadata TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issue_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            author TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues (id)
        )
    ''')

    conn.commit()
    conn.close()


def create_issue(title: str, description: str = '', priority: str = 'medium',
                 assignee: str = None, tags: list = None, metadata: dict = None) -> int:
    """
    Create a new issue

    Args:
        title: Issue title
        description: Issue description
        priority: Priority ('low', 'medium', 'high', 'critical')
        assignee: Person assigned to issue
        tags: List of tags
        metadata: Optional metadata dict

    Returns:
        issue_id: ID of created issue
    """
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO issues
        (title, description, status, priority, assignee, tags, metadata)
        VALUES (?, ?, 'open', ?, ?, ?, ?)
    ''', (
        title,
        description,
        priority,
        assignee,
        json.dumps(tags) if tags else None,
        json.dumps(metadata) if metadata else None
    ))

    issue_id = cursor.lastrowid
    conn.commit()
    conn.close()

    print(f"✅ Created issue #{issue_id}: {title}")
    print(f"   Priority: {priority}")
    if tags:
        print(f"   Tags: {', '.join(tags)}")

    return issue_id


def update_issue(issue_id: int, **kwargs):
    """
    Update issue fields

    Args:
        issue_id: Issue ID
        **kwargs: Fields to update (title, description, status, priority, assignee)
    """
    allowed_fields = {'title', 'description', 'status', 'priority', 'assignee'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not updates:
        print("No valid fields to update")
        return

    # Build update query
    set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
    set_clause += ', updated_at = CURRENT_TIMESTAMP'

    conn = _get_db()
    cursor = conn.cursor()

    query = f'UPDATE issues SET {set_clause} WHERE id = ?'
    cursor.execute(query, list(updates.values()) + [issue_id])

    # Close issue if status changed to closed
    if updates.get('status') == 'closed':
        cursor.execute('UPDATE issues SET closed_at = CURRENT_TIMESTAMP WHERE id = ?', (issue_id,))

    conn.commit()
    conn.close()

    print(f"✅ Updated issue #{issue_id}")
    for k, v in updates.items():
        print(f"   {k}: {v}")


def add_comment(issue_id: int, comment: str, author: str = None):
    """Add comment to issue"""
    conn = _get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO issue_comments (issue_id, comment, author)
        VALUES (?, ?, ?)
    ''', (issue_id, comment, author))

    cursor.execute('UPDATE issues SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (issue_id,))

    conn.commit()
    conn.close()

    print(f"💬 Added comment to issue #{issue_id}")


def get_issue(issue_id: int) -> dict:
    """Get issue details"""
    conn = _get_db()
    cursor = conn.cursor()

    issue = cursor.execute('SELECT * FROM issues WHERE id = ?', (issue_id,)).fetchone()

    if not issue:
        conn.close()
        return None

    # Get comments
    comments = cursor.execute('''
        SELECT * FROM issue_comments
        WHERE issue_id = ?
        ORDER BY created_at
    ''', (issue_id,)).fetchall()

    conn.close()

    issue_dict = dict(issue)
    issue_dict['comments'] = [dict(c) for c in comments]

    # Parse JSON fields
    if issue_dict['tags']:
        issue_dict['tags'] = json.loads(issue_dict['tags'])
    if issue_dict['metadata']:
        issue_dict['metadata'] = json.loads(issue_dict['metadata'])

    return issue_dict


def list_issues(status: str = None, priority: str = None, limit: int = 20) -> list:
    """List issues with optional filters"""
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM issues WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status)

    if priority:
        query += ' AND priority = ?'
        params.append(priority)

    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)

    issues = cursor.execute(query, params).fetchall()
    conn.close()

    return [dict(i) for i in issues]


def generate_qr(issue_id: int, scale: int = 5):
    """
    Generate QR code for issue

    Args:
        issue_id: Issue ID
        scale: QR code scale (pixels per module)
    """
    issue = get_issue(issue_id)

    if not issue:
        print(f"❌ Issue #{issue_id} not found")
        return

    # Generate URL
    url = f"http://localhost:5001/issue/{issue_id}"

    # Use QR encoder
    try:
        from qr_encoder_stdlib import generate_data_matrix

        qr_binary = generate_data_matrix(url, size=25, scale=scale)

        # Save QR code
        qr_dir = Path('qr_codes')
        qr_dir.mkdir(exist_ok=True)

        qr_path = qr_dir / f"issue_{issue_id}.bmp"
        with open(qr_path, 'wb') as f:
            f.write(qr_binary)

        print(f"✅ Generated QR code for issue #{issue_id}")
        print(f"   File: {qr_path}")
        print(f"   URL: {url}")
        print(f"   Size: {len(qr_binary):,} bytes")

        return qr_path

    except ImportError:
        print("❌ qr_encoder_stdlib not found")
        print("   Run: python3 qr_encoder_stdlib.py to verify it exists")


def export_issues_sheet(output_file: str = 'issues_sheet.html'):
    """
    Export all open issues as printable HTML with QR codes

    Args:
        output_file: Output HTML file
    """
    issues = list_issues(status='open')

    if not issues:
        print("No open issues to export")
        return

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .issue-card {
                border: 2px solid #333;
                padding: 15px;
                margin-bottom: 20px;
                page-break-inside: avoid;
                display: flex;
                gap: 20px;
            }
            .issue-info { flex: 1; }
            .issue-qr { text-align: center; }
            .issue-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
            .issue-meta { color: #666; font-size: 14px; margin-bottom: 10px; }
            .issue-desc { margin-bottom: 10px; }
            .priority-high { border-color: #dc3545; }
            .priority-critical { border-color: #721c24; background: #f8d7da; }
            @media print {
                .issue-card { page-break-after: always; }
            }
        </style>
    </head>
    <body>
        <h1>📋 Open Issues</h1>
        <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    """

    for issue in issues:
        priority_class = f"priority-{issue['priority']}" if issue['priority'] in ['high', 'critical'] else ''

        # Generate QR code
        qr_path = generate_qr(issue['id'], scale=3)

        # Read QR code as data URI (if it exists)
        qr_data_uri = ''
        if qr_path and qr_path.exists():
            import base64
            with open(qr_path, 'rb') as f:
                qr_bytes = f.read()
                qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
                qr_data_uri = f'data:image/bmp;base64,{qr_base64}'

        html += f"""
        <div class="issue-card {priority_class}">
            <div class="issue-info">
                <div class="issue-title">#{issue['id']}: {issue['title']}</div>
                <div class="issue-meta">
                    Priority: <strong>{issue['priority']}</strong> |
                    Created: {issue['created_at']}
                    {f" | Assignee: {issue['assignee']}" if issue['assignee'] else ""}
                </div>
                <div class="issue-desc">{issue['description'] or '(no description)'}</div>
            </div>
            <div class="issue-qr">
                {"<img src='" + qr_data_uri + "' alt='QR Code' style='max-width: 150px;'>" if qr_data_uri else "(QR code unavailable)"}
                <div style="font-size: 12px; margin-top: 5px;">Issue #{issue['id']}</div>
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Exported {len(issues)} issues to {output_file}")
    print(f"   Open in browser to print")


def stats():
    """Show issue tracker statistics"""
    _init_database()

    conn = _get_db()
    cursor = conn.cursor()

    total = cursor.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    open_issues = cursor.execute('SELECT COUNT(*) FROM issues WHERE status = "open"').fetchone()[0]
    closed = cursor.execute('SELECT COUNT(*) FROM issues WHERE status = "closed"').fetchone()[0]

    by_priority = cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM issues
        WHERE status = 'open'
        GROUP BY priority
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END
    ''').fetchall()

    conn.close()

    print("=" * 70)
    print("📋 Issue Tracker Statistics")
    print("=" * 70)
    print()
    print(f"Total issues:  {total}")
    print(f"Open:          {open_issues}")
    print(f"Closed:        {closed}")
    print()

    if by_priority:
        print("Open issues by priority:")
        for row in by_priority:
            print(f"  {row['priority']:10s}: {row['count']}")
        print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create':
            if len(sys.argv) < 3:
                print("Usage: python3 issue_tracker.py create <title> [priority] [assignee]")
                sys.exit(1)

            title = sys.argv[2]
            priority = sys.argv[3] if len(sys.argv) > 3 else 'medium'
            assignee = sys.argv[4] if len(sys.argv) > 4 else None

            issue_id = create_issue(title, priority=priority, assignee=assignee)

            print()
            print(f"💡 Generate QR code: python3 issue_tracker.py qr {issue_id}")

        elif command == 'list':
            status = sys.argv[2] if len(sys.argv) > 2 else None
            issues = list_issues(status=status)

            print("=" * 70)
            print(f"📋 Issues{' (' + status + ')' if status else ''}")
            print("=" * 70)
            print()

            if not issues:
                print("   No issues found")
            else:
                for issue in issues:
                    priority_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(issue['priority'], '⚪')
                    status_icon = {'open': '📂', 'closed': '✅'}.get(issue['status'], '❓')

                    print(f"{status_icon} {priority_icon} #{issue['id']}: {issue['title']}")
                    print(f"   {issue['priority']} | {issue['created_at']}")

                    if issue['assignee']:
                        print(f"   👤 {issue['assignee']}")

                    print()

        elif command == 'view':
            if len(sys.argv) < 3:
                print("Usage: python3 issue_tracker.py view <issue_id>")
                sys.exit(1)

            issue_id = int(sys.argv[2])
            issue = get_issue(issue_id)

            if not issue:
                print(f"❌ Issue #{issue_id} not found")
                sys.exit(1)

            print("=" * 70)
            print(f"📋 Issue #{issue['id']}: {issue['title']}")
            print("=" * 70)
            print()
            print(f"Status:      {issue['status']}")
            print(f"Priority:    {issue['priority']}")
            print(f"Created:     {issue['created_at']}")
            print(f"Updated:     {issue['updated_at']}")

            if issue['assignee']:
                print(f"Assignee:    {issue['assignee']}")

            if issue['tags']:
                print(f"Tags:        {', '.join(issue['tags'])}")

            print()
            print("Description:")
            print(issue['description'] or '(no description)')

            if issue['comments']:
                print()
                print("Comments:")
                for comment in issue['comments']:
                    author = comment['author'] or 'Anonymous'
                    print(f"  [{comment['created_at']}] {author}:")
                    print(f"  {comment['comment']}")
                    print()

        elif command == 'update':
            if len(sys.argv) < 4:
                print("Usage: python3 issue_tracker.py update <issue_id> <field> <value>")
                print("Fields: title, description, status, priority, assignee")
                sys.exit(1)

            issue_id = int(sys.argv[2])
            field = sys.argv[3]
            value = sys.argv[4]

            update_issue(issue_id, **{field: value})

        elif command == 'comment':
            if len(sys.argv) < 4:
                print("Usage: python3 issue_tracker.py comment <issue_id> <comment> [author]")
                sys.exit(1)

            issue_id = int(sys.argv[2])
            comment = sys.argv[3]
            author = sys.argv[4] if len(sys.argv) > 4 else None

            add_comment(issue_id, comment, author)

        elif command == 'qr':
            if len(sys.argv) < 3:
                print("Usage: python3 issue_tracker.py qr <issue_id> [scale]")
                sys.exit(1)

            issue_id = int(sys.argv[2])
            scale = int(sys.argv[3]) if len(sys.argv) > 3 else 5

            generate_qr(issue_id, scale=scale)

        elif command == 'export':
            output_file = sys.argv[2] if len(sys.argv) > 2 else 'issues_sheet.html'
            export_issues_sheet(output_file)

        elif command == 'stats':
            stats()

        else:
            print(f"Unknown command: {command}")
            print()
            print("Available commands:")
            print("  create <title> [priority] [assignee]")
            print("  list [status]")
            print("  view <issue_id>")
            print("  update <issue_id> <field> <value>")
            print("  comment <issue_id> <comment> [author]")
            print("  qr <issue_id> [scale]")
            print("  export [output_file.html]")
            print("  stats")
            sys.exit(1)

    else:
        print("=" * 70)
        print("📋 Issue Tracker with QR Codes")
        print("=" * 70)
        print()
        print("Offline-first issue tracking with QR code integration.")
        print()
        print("Commands:")
        print("  create <title> [priority] [assignee]  - Create issue")
        print("  list [status]                          - List issues")
        print("  view <id>                              - View issue")
        print("  update <id> <field> <value>            - Update issue")
        print("  comment <id> <text> [author]           - Add comment")
        print("  qr <id> [scale]                        - Generate QR code")
        print("  export [file.html]                     - Export printable sheet")
        print("  stats                                  - Show statistics")
        print()
        print("Example:")
        print("  python3 issue_tracker.py create 'Fix login bug' high alice")
        print("  python3 issue_tracker.py qr 1")
        print("  python3 issue_tracker.py export issues.html")
        print()
        print("=" * 70)
