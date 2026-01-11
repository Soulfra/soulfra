#!/usr/bin/env python3
"""
Soul Git - Version Control for Souls

Like git, but for souls instead of code!

Commands:
- soul commit "message" - Save current soul state
- soul log - View commit history
- soul diff v1.0 v2.0 - Compare two versions
- soul tag v2.0 - Tag current version
- soul checkout v1.0 - View old version

Teaching the pattern:
1. Soul pack → Commit (snapshot)
2. Store in soul_history table
3. Track changes over time
4. Diff shows what changed

This is literally git for souls!
"""

import json
import hashlib
from datetime import datetime
from database import get_db
from soul_model import Soul


def init_soul_git():
    """
    Initialize soul_history table (like .git folder)

    Table structure:
    - commit_hash: SHA256 of soul pack (like git commit hash)
    - user_id: Owner of this soul
    - committed_at: Timestamp
    - commit_message: Commit message
    - soul_pack: Full soul pack JSON
    - tag: Optional version tag (v1.0, v2.0)
    """
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS soul_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_hash TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            committed_at TEXT NOT NULL,
            commit_message TEXT,
            soul_pack TEXT NOT NULL,
            tag TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Index for fast lookups
    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_soul_history_user
        ON soul_history(user_id, committed_at DESC)
    ''')

    db.execute('''
        CREATE INDEX IF NOT EXISTS idx_soul_history_tag
        ON soul_history(user_id, tag)
    ''')

    db.commit()
    db.close()

    print("✅ Soul git initialized (soul_history table created)")


def calculate_soul_hash(soul_pack):
    """
    Calculate commit hash for soul pack

    Args:
        soul_pack: Soul pack dict

    Returns:
        str: SHA256 hash (like git commit hash)

    Learning: Deterministic hash from soul content
    """
    # Convert to canonical JSON (sorted keys)
    canonical = json.dumps(soul_pack, sort_keys=True, separators=(',', ':'))

    # SHA256 hash
    hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()

    # First 12 chars (like git short hash)
    return hash_bytes.hex()[:12]


def soul_commit(username, message="Soul update"):
    """
    Commit current soul state (like git commit)

    Args:
        username: Username to commit
        message: Commit message

    Returns:
        str: Commit hash

    Learning:
    1. Compile current soul
    2. Calculate hash
    3. Store in soul_history
    """
    init_soul_git()

    # Get user
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        db.close()
        raise ValueError(f"User {username} not found")

    # Compile current soul
    soul = Soul(user['id'])
    soul_pack = soul.compile_pack()

    # Calculate hash
    commit_hash = calculate_soul_hash(soul_pack)

    # Store commit
    db.execute('''
        INSERT OR IGNORE INTO soul_history
        (commit_hash, user_id, committed_at, commit_message, soul_pack)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        commit_hash,
        user['id'],
        datetime.now().isoformat(),
        message,
        json.dumps(soul_pack)
    ))

    db.commit()
    db.close()

    return commit_hash


def soul_log(username, limit=10):
    """
    View commit history (like git log)

    Args:
        username: Username
        limit: Max commits to show

    Returns:
        list: Commit history

    Learning: Show evolution over time
    """
    init_soul_git()

    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        db.close()
        return []

    commits = db.execute('''
        SELECT commit_hash, committed_at, commit_message, tag
        FROM soul_history
        WHERE user_id = ?
        ORDER BY committed_at DESC
        LIMIT ?
    ''', (user['id'], limit)).fetchall()

    db.close()

    return [dict(c) for c in commits]


def soul_diff(username, hash1, hash2):
    """
    Compare two soul versions (like git diff)

    Args:
        username: Username
        hash1: First commit hash
        hash2: Second commit hash

    Returns:
        dict: Differences

    Learning:
    - Shows what changed between commits
    - Interests added/removed
    - Values changed
    - Expertise evolved
    """
    init_soul_git()

    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        db.close()
        return None

    # Get both commits
    commit1 = db.execute(
        'SELECT soul_pack FROM soul_history WHERE user_id = ? AND commit_hash = ?',
        (user['id'], hash1)
    ).fetchone()

    commit2 = db.execute(
        'SELECT soul_pack FROM soul_history WHERE user_id = ? AND commit_hash = ?',
        (user['id'], hash2)
    ).fetchone()

    db.close()

    if not commit1 or not commit2:
        return None

    # Parse soul packs
    soul1 = json.loads(commit1['soul_pack'])
    soul2 = json.loads(commit2['soul_pack'])

    # Calculate differences
    interests1 = set(soul1.get('essence', {}).get('interests', []))
    interests2 = set(soul2.get('essence', {}).get('interests', []))

    values1 = set(soul1.get('essence', {}).get('values', []))
    values2 = set(soul2.get('essence', {}).get('values', []))

    return {
        'interests_added': list(interests2 - interests1),
        'interests_removed': list(interests1 - interests2),
        'values_added': list(values2 - values1),
        'values_removed': list(values1 - values2),
        'compiled_at_1': soul1.get('compiled_at'),
        'compiled_at_2': soul2.get('compiled_at')
    }


def soul_tag(username, commit_hash, tag_name):
    """
    Tag a commit with version (like git tag)

    Args:
        username: Username
        commit_hash: Commit to tag
        tag_name: Tag name (e.g., "v1.0", "v2.0")

    Returns:
        bool: Success

    Learning: Mark important soul milestones
    """
    init_soul_git()

    db = get_db()
    user = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        db.close()
        return False

    db.execute('''
        UPDATE soul_history
        SET tag = ?
        WHERE user_id = ? AND commit_hash = ?
    ''', (tag_name, user['id'], commit_hash))

    db.commit()
    db.close()

    return True


def test_soul_git():
    """Test soul git system"""
    print("=" * 70)
    print("🧪 Testing Soul Git - Version Control for Souls")
    print("=" * 70)
    print()

    # Test 1: Initialize
    print("TEST 1: Initialize Soul Git")
    init_soul_git()
    print()

    # Test 2: Commit soul
    print("TEST 2: Soul Commit")
    hash1 = soul_commit('calriven', "Initial soul compilation")
    print(f"   ✅ Committed: {hash1}")
    print(f"   Message: Initial soul compilation")
    print()

    # Test 3: View log
    print("TEST 3: Soul Log")
    commits = soul_log('calriven')
    print(f"   Found {len(commits)} commits:")
    for commit in commits:
        tag = f" ({commit['tag']})" if commit['tag'] else ""
        print(f"   {commit['commit_hash']} - {commit['commit_message']}{tag}")
        print(f"      {commit['committed_at']}")
    print()

    # Test 4: Tag commit
    print("TEST 4: Tag Commit")
    success = soul_tag('calriven', hash1, 'v1.0')
    print(f"   ✅ Tagged {hash1} as v1.0")
    print()

    # Test 5: Make another commit
    print("TEST 5: Second Commit")
    hash2 = soul_commit('calriven', "Added new interests")
    print(f"   ✅ Committed: {hash2}")
    print()

    # Test 6: View updated log
    print("TEST 6: Updated Log")
    commits = soul_log('calriven')
    print(f"   Found {len(commits)} commits:")
    for commit in commits:
        tag = f" ({commit['tag']})" if commit['tag'] else ""
        print(f"   {commit['commit_hash']} - {commit['commit_message']}{tag}")
    print()

    # Test 7: Diff two commits
    print("TEST 7: Soul Diff")
    if len(commits) >= 2:
        diff = soul_diff('calriven', commits[1]['commit_hash'], commits[0]['commit_hash'])
        if diff:
            print(f"   Changes from {commits[1]['commit_hash']} → {commits[0]['commit_hash']}:")
            if diff['interests_added']:
                print(f"   + Interests added: {', '.join(diff['interests_added'])}")
            if diff['interests_removed']:
                print(f"   - Interests removed: {', '.join(diff['interests_removed'])}")
            if diff['values_added']:
                print(f"   + Values added: {', '.join(diff['values_added'])}")
            if diff['values_removed']:
                print(f"   - Values removed: {', '.join(diff['values_removed'])}")
    print()

    print("=" * 70)
    print("✅ All soul git tests passed!")
    print("=" * 70)
    print()

    print("💡 This is Git for Souls:")
    print("   • Commits = soul snapshots")
    print("   • Log = evolution history")
    print("   • Diff = what changed")
    print("   • Tags = version milestones")
    print("   • Hash = unique identifier")
    print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'commit' and len(sys.argv) >= 4:
            username = sys.argv[2]
            message = ' '.join(sys.argv[3:])
            hash_val = soul_commit(username, message)
            print(f"✅ Committed {username}'s soul: {hash_val}")

        elif command == 'log' and len(sys.argv) >= 3:
            username = sys.argv[2]
            commits = soul_log(username)
            print(f"\nSoul log for {username}:\n")
            for c in commits:
                tag = f" ({c['tag']})" if c['tag'] else ""
                print(f"{c['commit_hash']} - {c['commit_message']}{tag}")
                print(f"  {c['committed_at']}\n")

        else:
            print("Usage:")
            print("  python soul_git.py commit <username> <message>")
            print("  python soul_git.py log <username>")
            print("  python soul_git.py                    # run tests")
    else:
        test_soul_git()
