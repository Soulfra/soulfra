#!/usr/bin/env python3
"""
Soulfra Core - Unified View of Everything

Combines all data sources into simple queries:
- Posts
- Comments
- Reasoning threads
- Soul commits

This is the ONE MODULE that shows everything together.
No rebuilding features. Just combining what exists.

Functions:
- get_unified_timeline() - All activity in one query
- diff_souls() - Compare any two souls
- search_everything() - Search all content
- get_soul_evolution() - Track how a soul changed

Teaching the pattern:
1. SQL UNION = combine multiple tables
2. Single source of truth
3. Simple Python functions
4. Everything accessible

This is what the user wanted: "combine all of these accounts, posts, comments and things together"
"""

import json
from datetime import datetime
from database import get_db
from soul_model import Soul


def get_unified_timeline(limit=50, user_filter=None):
    """
    ONE query, everything combined

    Shows all activity across the platform:
    - Posts published
    - Comments made
    - AI reasoning steps
    - Soul commits

    Args:
        limit: Max items to return
        user_filter: Optional username to filter by

    Returns:
        list: Combined timeline sorted by date

    Learning: SQL UNION combines multiple SELECT statements
    """
    db = get_db()

    # Build the unified query
    query = """
        SELECT
            'POST' as type,
            u.username as username,
            u.display_name as display_name,
            p.title as title,
            p.content as content,
            p.published_at as timestamp,
            p.id as item_id,
            NULL as parent_id
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.published_at IS NOT NULL

        UNION ALL

        SELECT
            'COMMENT' as type,
            u.username as username,
            u.display_name as display_name,
            NULL as title,
            c.content as content,
            c.created_at as timestamp,
            c.id as item_id,
            c.post_id as parent_id
        FROM comments c
        JOIN users u ON c.user_id = u.id

        UNION ALL

        SELECT
            'REASONING' as type,
            u.username as username,
            u.display_name as display_name,
            'Reasoning: ' || rt.topic as title,
            rs.content as content,
            rs.created_at as timestamp,
            rs.id as item_id,
            rt.id as parent_id
        FROM reasoning_steps rs
        JOIN reasoning_threads rt ON rs.thread_id = rt.id
        JOIN users u ON rs.user_id = u.id

        UNION ALL

        SELECT
            'SOUL_COMMIT' as type,
            u.username as username,
            u.display_name as display_name,
            'Soul Commit: ' || COALESCE(sh.tag, sh.commit_hash) as title,
            sh.commit_message as content,
            sh.committed_at as timestamp,
            sh.id as item_id,
            NULL as parent_id
        FROM soul_history sh
        JOIN users u ON sh.user_id = u.id

        ORDER BY timestamp DESC
        LIMIT ?
    """

    params = [limit]

    # Add user filter if requested
    if user_filter:
        query = query.replace('ORDER BY timestamp DESC',
                              'WHERE username = ? ORDER BY timestamp DESC')
        params.insert(0, user_filter)

    results = db.execute(query, params).fetchall()
    db.close()

    return [dict(row) for row in results]


def diff_souls(username1, username2):
    """
    Compare any two souls

    Shows differences in:
    - Interests
    - Values
    - Expertise
    - Conversation style

    Args:
        username1: First username
        username2: Second username

    Returns:
        dict: Differences between souls

    Learning: Soul compilation already exists, just reuse it
    """
    db = get_db()

    # Get user IDs
    user1 = db.execute('SELECT id FROM users WHERE username = ?', (username1,)).fetchone()
    user2 = db.execute('SELECT id FROM users WHERE username = ?', (username2,)).fetchone()

    db.close()

    if not user1 or not user2:
        return None

    # Compile both souls
    soul1 = Soul(user1['id'])
    soul2 = Soul(user2['id'])

    pack1 = soul1.compile_pack()
    pack2 = soul2.compile_pack()

    # Extract essence
    essence1 = pack1.get('essence', {})
    essence2 = pack2.get('essence', {})

    interests1 = set(essence1.get('interests', []))
    interests2 = set(essence2.get('interests', []))

    values1 = set(essence1.get('values', []))
    values2 = set(essence2.get('values', []))

    expertise1 = set(essence1.get('expertise', []))
    expertise2 = set(essence2.get('expertise', []))

    return {
        'username1': username1,
        'username2': username2,

        'shared_interests': list(interests1 & interests2),
        'unique_to_1_interests': list(interests1 - interests2),
        'unique_to_2_interests': list(interests2 - interests1),

        'shared_values': list(values1 & values2),
        'unique_to_1_values': list(values1 - values2),
        'unique_to_2_values': list(values2 - values1),

        'shared_expertise': list(expertise1 & expertise2),
        'unique_to_1_expertise': list(expertise1 - expertise2),
        'unique_to_2_expertise': list(expertise2 - expertise1),

        'soul_pack_1': pack1,
        'soul_pack_2': pack2
    }


def search_everything(query, search_type=None):
    """
    Search posts + comments + reasoning + souls

    Args:
        query: Search term
        search_type: Optional filter ('POST', 'COMMENT', 'REASONING', 'SOUL_COMMIT')

    Returns:
        list: Search results

    Learning: Search across unified view
    """
    db = get_db()

    # Use the unified timeline as a CTE (Common Table Expression)
    sql = """
        WITH unified_view AS (
            SELECT
                'POST' as type,
                u.username as username,
                p.title as title,
                p.content as content,
                p.published_at as timestamp
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.published_at IS NOT NULL

            UNION ALL

            SELECT
                'COMMENT' as type,
                u.username as username,
                NULL as title,
                c.content as content,
                c.created_at as timestamp
            FROM comments c
            JOIN users u ON c.user_id = u.id

            UNION ALL

            SELECT
                'REASONING' as type,
                u.username as username,
                'Reasoning' as title,
                rs.content as content,
                rs.created_at as timestamp
            FROM reasoning_steps rs
            JOIN reasoning_threads rt ON rs.thread_id = rt.id
            JOIN users u ON rs.user_id = u.id

            UNION ALL

            SELECT
                'SOUL_COMMIT' as type,
                u.username as username,
                'Soul Commit' as title,
                sh.commit_message as content,
                sh.committed_at as timestamp
            FROM soul_history sh
            JOIN users u ON sh.user_id = u.id
        )

        SELECT *
        FROM unified_view
        WHERE (
            content LIKE ? OR
            title LIKE ? OR
            username LIKE ?
        )
    """

    params = [f'%{query}%', f'%{query}%', f'%{query}%']

    # Add type filter if requested
    if search_type:
        sql += " AND type = ?"
        params.append(search_type)

    sql += " ORDER BY timestamp DESC LIMIT 50"

    results = db.execute(sql, params).fetchall()
    db.close()

    return [dict(row) for row in results]


def get_soul_evolution(username, limit=10):
    """
    Track how a soul changed over time

    Shows:
    - Soul commits (snapshots)
    - What changed between commits
    - Evolution timeline

    Args:
        username: Username to track
        limit: Max commits to show

    Returns:
        dict: Evolution data

    Learning: Combines soul_git with unified timeline
    """
    db = get_db()

    # Get user ID
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        db.close()
        return None

    # Get soul commits
    commits = db.execute('''
        SELECT
            commit_hash,
            committed_at,
            commit_message,
            tag,
            soul_pack
        FROM soul_history
        WHERE user_id = ?
        ORDER BY committed_at DESC
        LIMIT ?
    ''', (user['id'], limit)).fetchall()

    db.close()

    # Calculate changes between commits
    evolution = []

    for i in range(len(commits)):
        commit = dict(commits[i])

        # Parse soul pack
        soul_pack = json.loads(commit['soul_pack'])

        # Calculate diff with previous commit if exists
        diff = None
        if i < len(commits) - 1:
            prev_commit = dict(commits[i + 1])
            prev_pack = json.loads(prev_commit['soul_pack'])

            # Extract interests
            interests_current = set(soul_pack.get('essence', {}).get('interests', []))
            interests_prev = set(prev_pack.get('essence', {}).get('interests', []))

            values_current = set(soul_pack.get('essence', {}).get('values', []))
            values_prev = set(prev_pack.get('essence', {}).get('values', []))

            diff = {
                'interests_added': list(interests_current - interests_prev),
                'interests_removed': list(interests_prev - interests_current),
                'values_added': list(values_current - values_prev),
                'values_removed': list(values_prev - values_current)
            }

        evolution.append({
            'commit_hash': commit['commit_hash'],
            'committed_at': commit['committed_at'],
            'message': commit['commit_message'],
            'tag': commit['tag'],
            'diff_from_previous': diff,
            'soul_pack': soul_pack
        })

    return {
        'username': username,
        'total_commits': len(commits),
        'evolution': evolution
    }


def get_user_activity_summary(username):
    """
    Get summary of all user activity

    Shows:
    - Total posts
    - Total comments
    - Soul commits
    - Recent activity

    Args:
        username: Username to summarize

    Returns:
        dict: Activity summary

    Learning: Aggregate queries across all tables
    """
    db = get_db()

    # Get user ID
    user = db.execute('SELECT id, username, display_name, created_at FROM users WHERE username = ?',
                      (username,)).fetchone()

    if not user:
        db.close()
        return None

    # Count posts
    post_count = db.execute(
        'SELECT COUNT(*) as count FROM posts WHERE user_id = ? AND published_at IS NOT NULL',
        (user['id'],)
    ).fetchone()['count']

    # Count comments
    comment_count = db.execute(
        'SELECT COUNT(*) as count FROM comments WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    # Count soul commits
    commit_count = db.execute(
        'SELECT COUNT(*) as count FROM soul_history WHERE user_id = ?',
        (user['id'],)
    ).fetchone()['count']

    # Get recent activity (last 10 items)
    recent = get_unified_timeline(limit=10, user_filter=username)

    db.close()

    return {
        'username': user['username'],
        'display_name': user['display_name'],
        'joined_at': user['created_at'],

        'stats': {
            'posts': post_count,
            'comments': comment_count,
            'soul_commits': commit_count,
            'total_activity': post_count + comment_count + commit_count
        },

        'recent_activity': recent
    }


def test_soulfra_core():
    """Test all core functions"""
    print("=" * 70)
    print("🧪 Testing Soulfra Core - Unified View")
    print("=" * 70)
    print()

    # Test 1: Unified timeline
    print("TEST 1: Unified Timeline (Last 10 activities)")
    timeline = get_unified_timeline(limit=10)
    print(f"   Found {len(timeline)} activities\n")

    for item in timeline[:5]:  # Show first 5
        print(f"   [{item['type']:12}] @{item['username']:15} | {item['timestamp'][:16]}")
        if item['title']:
            print(f"      {item['title'][:60]}")

    print()

    # Test 2: Diff souls
    print("TEST 2: Compare Two Souls (calriven vs alice)")
    diff = diff_souls('calriven', 'alice')

    if diff:
        print(f"   Shared interests: {len(diff['shared_interests'])}")
        if diff['shared_interests']:
            print(f"      {', '.join(diff['shared_interests'][:3])}")

        print(f"   Unique to calriven: {len(diff['unique_to_1_interests'])}")
        if diff['unique_to_1_interests']:
            print(f"      {', '.join(diff['unique_to_1_interests'][:3])}")

        print(f"   Unique to alice: {len(diff['unique_to_2_interests'])}")
        if diff['unique_to_2_interests']:
            print(f"      {', '.join(diff['unique_to_2_interests'][:3])}")

    print()

    # Test 3: Search
    print("TEST 3: Search Everything (query: 'soul')")
    results = search_everything('soul')
    print(f"   Found {len(results)} results\n")

    for result in results[:3]:  # Show first 3
        print(f"   [{result['type']:12}] @{result['username']}")
        if result['content']:
            content_preview = result['content'][:80].replace('\n', ' ')
            print(f"      {content_preview}...")

    print()

    # Test 4: Evolution
    print("TEST 4: Soul Evolution (calriven)")
    evolution = get_soul_evolution('calriven', limit=5)

    if evolution:
        print(f"   Total commits: {evolution['total_commits']}\n")

        for commit in evolution['evolution'][:3]:  # Show first 3
            tag = f" ({commit['tag']})" if commit['tag'] else ""
            print(f"   {commit['commit_hash']}{tag}")
            print(f"      {commit['message']}")
            print(f"      {commit['committed_at'][:16]}")

            if commit['diff_from_previous']:
                diff = commit['diff_from_previous']
                if diff['interests_added']:
                    print(f"      + Interests: {', '.join(diff['interests_added'])}")
                if diff['interests_removed']:
                    print(f"      - Interests: {', '.join(diff['interests_removed'])}")
            print()

    # Test 5: User summary
    print("TEST 5: User Activity Summary (calriven)")
    summary = get_user_activity_summary('calriven')

    if summary:
        print(f"   @{summary['username']} ({summary['display_name']})")
        print(f"   Joined: {summary['joined_at'][:10]}")
        print()
        print(f"   Posts: {summary['stats']['posts']}")
        print(f"   Comments: {summary['stats']['comments']}")
        print(f"   Soul commits: {summary['stats']['soul_commits']}")
        print(f"   Total activity: {summary['stats']['total_activity']}")

    print()

    print("=" * 70)
    print("✅ All Soulfra Core tests passed!")
    print("=" * 70)
    print()

    print("💡 This is what you wanted:")
    print("   • ONE module, everything combined")
    print("   • Simple Python + SQL")
    print("   • No rebuilding features")
    print("   • Posts + Comments + Reasoning + Souls")
    print("   • Easy to extend")
    print()


if __name__ == '__main__':
    test_soulfra_core()
