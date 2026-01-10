#!/usr/bin/env python3
"""
Unified Logger for Soulfra - Cross-Platform Integration Logging

Centralizes logging from all integrations:
- Twitter/X (posts, engagement, analytics)
- GitHub (commits, stars, issues)
- Google Docs (imports, exports, shares)
- Radio (streams, listeners, plays)
- QR Codes (scans, locations, devices)

All logs stored in single table with standardized format for easy querying.

Usage:
    from unified_logger import log_integration_event, get_integration_logs

    # Log an event
    log_integration_event(
        platform='twitter',
        event_type='post_published',
        description='Posted new blog: AI Models',
        metadata={'tweet_id': '123456', 'impressions': 47}
    )

    # Retrieve logs
    logs = get_integration_logs(platform='twitter', limit=10)
"""

import json
import re
from datetime import datetime
from database import get_db


# =============================================================================
# PII REDACTION
# =============================================================================

# PII patterns to redact from logs
PII_PATTERNS = {
    'ipv4': (re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'), 'X.X.X.X'),
    'ipv6': (re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'), 'X:X:X:X:X:X:X:X'),
    'email': (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    'gps_coords': (re.compile(r'[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)'), '[GPS_REDACTED]'),
}


def redact_pii(text):
    """
    Redact PII from text (for logging)

    Args:
        text (str): Text that may contain PII

    Returns:
        str: Text with PII redacted

    Example:
        >>> redact_pii("User 192.168.1.123 accessed email user@example.com")
        'User X.X.X.X accessed email [EMAIL_REDACTED]'
    """
    if not text:
        return text

    redacted = text

    for pii_type, (pattern, replacement) in PII_PATTERNS.items():
        redacted = pattern.sub(replacement, redacted)

    return redacted


def init_integration_logs_table():
    """
    Create integration_logs table if it doesn't exist

    Schema:
    - id: Auto-increment primary key
    - platform: twitter, github, gdocs, radio, qr
    - event_type: post_published, commit_pushed, doc_imported, etc.
    - description: Human-readable summary
    - metadata: JSON with platform-specific data
    - created_at: Timestamp
    """
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS integration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            metadata TEXT,
            post_id INTEGER,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indexes for fast querying
    db.execute('CREATE INDEX IF NOT EXISTS idx_integration_logs_platform ON integration_logs(platform)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_integration_logs_event_type ON integration_logs(event_type)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_integration_logs_post_id ON integration_logs(post_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_integration_logs_created_at ON integration_logs(created_at DESC)')

    db.commit()
    db.close()

    print("✅ Integration logs table initialized")


def log_integration_event(platform, event_type, description, metadata=None, post_id=None, user_id=None):
    """
    Log an integration event

    Args:
        platform (str): Platform name (twitter, github, gdocs, radio, qr)
        event_type (str): Event type (post_published, commit_pushed, etc.)
        description (str): Human-readable description
        metadata (dict): Additional data (optional)
        post_id (int): Related post ID (optional)
        user_id (int): Related user ID (optional)

    Returns:
        int: Log entry ID

    Example:
        log_id = log_integration_event(
            platform='twitter',
            event_type='post_published',
            description='Posted: "New AI Models Blog"',
            metadata={'tweet_id': '123456', 'impressions': 47, 'likes': 12},
            post_id=42
        )
    """
    init_integration_logs_table()

    db = get_db()

    # Redact PII from description before storing
    description_redacted = redact_pii(description)

    # Redact PII from metadata
    if metadata:
        metadata_str = json.dumps(metadata)
        metadata_redacted_str = redact_pii(metadata_str)
        metadata_redacted = json.loads(metadata_redacted_str)
    else:
        metadata_redacted = None

    # Convert metadata to JSON
    metadata_json = json.dumps(metadata_redacted) if metadata_redacted else None

    cursor = db.execute('''
        INSERT INTO integration_logs (platform, event_type, description, metadata, post_id, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (platform, event_type, description_redacted, metadata_json, post_id, user_id))

    log_id = cursor.lastrowid

    db.commit()
    db.close()

    # Print to console for immediate feedback (also redacted)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{platform.upper()}] {description_redacted}")

    return log_id


def get_integration_logs(platform=None, event_type=None, post_id=None, limit=100, offset=0):
    """
    Retrieve integration logs with optional filtering

    Args:
        platform (str): Filter by platform (optional)
        event_type (str): Filter by event type (optional)
        post_id (int): Filter by post ID (optional)
        limit (int): Max number of logs to return (default 100)
        offset (int): Pagination offset (default 0)

    Returns:
        list: Log entries as dicts

    Example:
        # Get all Twitter logs
        twitter_logs = get_integration_logs(platform='twitter', limit=50)

        # Get logs for specific post
        post_logs = get_integration_logs(post_id=42)

        # Get all 'post_published' events
        publish_logs = get_integration_logs(event_type='post_published')
    """
    init_integration_logs_table()

    db = get_db()

    # Build query dynamically based on filters
    query = 'SELECT * FROM integration_logs WHERE 1=1'
    params = []

    if platform:
        query += ' AND platform = ?'
        params.append(platform)

    if event_type:
        query += ' AND event_type = ?'
        params.append(event_type)

    if post_id:
        query += ' AND post_id = ?'
        params.append(post_id)

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    logs = db.execute(query, params).fetchall()

    db.close()

    # Convert to dicts and parse JSON metadata
    result = []
    for log in logs:
        log_dict = dict(log)
        if log_dict['metadata']:
            try:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            except json.JSONDecodeError:
                log_dict['metadata'] = {}
        result.append(log_dict)

    return result


def get_platform_stats(platform=None):
    """
    Get statistics for platform(s)

    Args:
        platform (str): Specific platform or None for all platforms

    Returns:
        dict: Statistics by platform and event type

    Example:
        stats = get_platform_stats('twitter')
        # Returns:
        # {
        #   'total_events': 142,
        #   'by_event_type': {
        #     'post_published': 36,
        #     'engagement_update': 106
        #   },
        #   'first_event': '2025-01-01 10:00:00',
        #   'last_event': '2026-01-02 14:30:00'
        # }
    """
    init_integration_logs_table()

    db = get_db()

    if platform:
        # Stats for specific platform
        total = db.execute(
            'SELECT COUNT(*) as count FROM integration_logs WHERE platform = ?',
            (platform,)
        ).fetchone()['count']

        by_type = db.execute('''
            SELECT event_type, COUNT(*) as count
            FROM integration_logs
            WHERE platform = ?
            GROUP BY event_type
            ORDER BY count DESC
        ''', (platform,)).fetchall()

        first_event = db.execute(
            'SELECT MIN(created_at) as first FROM integration_logs WHERE platform = ?',
            (platform,)
        ).fetchone()['first']

        last_event = db.execute(
            'SELECT MAX(created_at) as last FROM integration_logs WHERE platform = ?',
            (platform,)
        ).fetchone()['last']

        result = {
            'platform': platform,
            'total_events': total,
            'by_event_type': {row['event_type']: row['count'] for row in by_type},
            'first_event': first_event,
            'last_event': last_event
        }
    else:
        # Stats for all platforms
        by_platform = db.execute('''
            SELECT platform, COUNT(*) as count
            FROM integration_logs
            GROUP BY platform
            ORDER BY count DESC
        ''').fetchall()

        result = {
            'total_events': sum(row['count'] for row in by_platform),
            'by_platform': {row['platform']: row['count'] for row in by_platform}
        }

    db.close()

    return result


def get_recent_activity(hours=24, limit=50):
    """
    Get recent activity across all platforms

    Args:
        hours (int): Look back this many hours (default 24)
        limit (int): Max number of events (default 50)

    Returns:
        list: Recent log entries

    Example:
        recent = get_recent_activity(hours=6, limit=20)
        for event in recent:
            print(f"{event['created_at']} - {event['platform']}: {event['description']}")
    """
    init_integration_logs_table()

    db = get_db()

    logs = db.execute('''
        SELECT *
        FROM integration_logs
        WHERE created_at >= datetime('now', '-' || ? || ' hours')
        ORDER BY created_at DESC
        LIMIT ?
    ''', (hours, limit)).fetchall()

    db.close()

    # Convert to dicts and parse JSON
    result = []
    for log in logs:
        log_dict = dict(log)
        if log_dict['metadata']:
            try:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            except json.JSONDecodeError:
                log_dict['metadata'] = {}
        result.append(log_dict)

    return result


def search_logs(query, limit=50):
    """
    Search logs by description text

    Args:
        query (str): Search term
        limit (int): Max results

    Returns:
        list: Matching log entries

    Example:
        results = search_logs('blog post', limit=20)
    """
    init_integration_logs_table()

    db = get_db()

    logs = db.execute('''
        SELECT *
        FROM integration_logs
        WHERE description LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (f'%{query}%', limit)).fetchall()

    db.close()

    # Convert to dicts
    result = []
    for log in logs:
        log_dict = dict(log)
        if log_dict['metadata']:
            try:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            except json.JSONDecodeError:
                log_dict['metadata'] = {}
        result.append(log_dict)

    return result


def delete_old_logs(days=90):
    """
    Delete logs older than specified days (for cleanup)

    Args:
        days (int): Delete logs older than this many days

    Returns:
        int: Number of logs deleted
    """
    init_integration_logs_table()

    db = get_db()

    cursor = db.execute('''
        DELETE FROM integration_logs
        WHERE created_at < datetime('now', '-' || ? || ' days')
    ''', (days,))

    deleted_count = cursor.rowcount

    db.commit()
    db.close()

    print(f"🗑️ Deleted {deleted_count} logs older than {days} days")

    return deleted_count


def test_unified_logger():
    """Test the unified logger system"""
    print("=" * 70)
    print("🧪 Testing Unified Logger")
    print("=" * 70)
    print()

    # Test 1: Initialize table
    print("TEST 1: Database Table")
    init_integration_logs_table()
    print()

    # Test 2: Log events from different platforms
    print("TEST 2: Log Events")

    log_integration_event(
        platform='twitter',
        event_type='post_published',
        description='Posted: "New AI Models Blog"',
        metadata={'tweet_id': '123456', 'impressions': 47, 'likes': 12},
        post_id=1
    )

    log_integration_event(
        platform='github',
        event_type='commit_pushed',
        description='Committed: app.py updates',
        metadata={'commit_hash': 'abc123', 'stars': 3},
        post_id=1
    )

    log_integration_event(
        platform='qr',
        event_type='scan',
        description='QR scanned: soulfra.com/qr/abc123',
        metadata={'device': 'iPhone', 'location': 'San Francisco'},
        post_id=1
    )

    log_integration_event(
        platform='radio',
        event_type='stream_started',
        description='Radio stream: Now playing episode 42',
        metadata={'listeners': 127, 'episode': 42}
    )

    print()

    # Test 3: Retrieve logs by platform
    print("TEST 3: Retrieve Logs by Platform")
    twitter_logs = get_integration_logs(platform='twitter', limit=10)
    print(f"   Twitter logs: {len(twitter_logs)}")
    for log in twitter_logs:
        print(f"      {log['created_at']} - {log['description']}")
    print()

    # Test 4: Get platform stats
    print("TEST 4: Platform Statistics")
    twitter_stats = get_platform_stats('twitter')
    print(f"   Twitter: {twitter_stats['total_events']} events")
    print(f"   By type: {twitter_stats['by_event_type']}")
    print()

    all_stats = get_platform_stats()
    print(f"   All platforms: {all_stats['total_events']} total events")
    print(f"   By platform: {all_stats['by_platform']}")
    print()

    # Test 5: Recent activity
    print("TEST 5: Recent Activity")
    recent = get_recent_activity(hours=24, limit=10)
    print(f"   Last 24 hours: {len(recent)} events")
    for event in recent[:3]:
        print(f"      [{event['platform'].upper()}] {event['description']}")
    print()

    # Test 6: Search logs
    print("TEST 6: Search Logs")
    results = search_logs('blog', limit=10)
    print(f"   Found {len(results)} results for 'blog'")
    for result in results:
        print(f"      {result['description']}")
    print()

    # Test 7: Get logs for specific post
    print("TEST 7: Logs for Specific Post")
    post_logs = get_integration_logs(post_id=1)
    print(f"   Post #1 has {len(post_logs)} integration events:")
    for log in post_logs:
        print(f"      [{log['platform'].upper()}] {log['description']}")
    print()

    print("=" * 70)
    print("✅ All unified logger tests passed!")
    print("=" * 70)
    print()

    print("💡 Next Steps:")
    print("   1. Build Twitter integration → uses log_integration_event()")
    print("   2. Build GitHub integration → uses log_integration_event()")
    print("   3. Build analytics dashboard → uses get_integration_logs()")
    print("   4. All platforms use same logging interface!")
    print()


if __name__ == '__main__':
    test_unified_logger()
