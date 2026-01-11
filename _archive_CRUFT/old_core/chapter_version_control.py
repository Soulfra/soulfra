#!/usr/bin/env python3
"""
Chapter Version Control - "Git for CalRiven"

Alternative to using Git - tracks changes to tutorial chapters in SQLite.
Provides: snapshots, diffs, forks, merges, history viewing.

This is what users learn in Chapter 5: "Forking - Your first neural network clone"
"""

import json
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db


# =============================================================================
# SNAPSHOT CREATION (like "git commit")
# =============================================================================

def create_chapter_snapshot(
    chapter_num: int,
    title: str,
    content: Dict,  # Tutorial data from chapter_tutorials.py
    commit_message: str,
    created_by_user_id: int = 1,
    parent_snapshot_id: Optional[int] = None
) -> int:
    """
    Create a new chapter snapshot (version)

    This is like "git commit" - saves the current state of a chapter.

    Args:
        chapter_num: Chapter number (1-7)
        title: Chapter title
        content: Full tutorial data as dict
        commit_message: What changed
        created_by_user_id: User creating snapshot
        parent_snapshot_id: Previous version (if updating)

    Returns:
        snapshot_id: ID of created snapshot
    """
    db = get_db()

    # Get next version number for this chapter
    latest = db.execute('''
        SELECT MAX(version_num) as max_version
        FROM chapter_snapshots
        WHERE chapter_num = ?
    ''', (chapter_num,)).fetchone()

    next_version = (latest['max_version'] or 0) + 1

    # Create snapshot
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO chapter_snapshots
        (chapter_num, version_num, title, content, commit_message,
         created_by_user_id, parent_snapshot_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        chapter_num,
        next_version,
        title,
        json.dumps(content),
        commit_message,
        created_by_user_id,
        parent_snapshot_id
    ))

    snapshot_id = cursor.lastrowid

    # Generate diffs if there's a parent
    if parent_snapshot_id:
        generate_diffs(snapshot_id, parent_snapshot_id)

    db.commit()
    db.close()

    print(f"✅ Created snapshot v{next_version} for Chapter {chapter_num}")
    print(f"   Commit: {commit_message}")

    return snapshot_id


# =============================================================================
# DIFF GENERATION (like "git diff")
# =============================================================================

def generate_diffs(snapshot_id: int, parent_snapshot_id: int):
    """
    Generate diff between two snapshots

    This is like "git diff" - shows what changed between versions.
    Uses Python's difflib for line-by-line comparison.
    """
    db = get_db()

    # Get both snapshots
    current = db.execute(
        'SELECT content FROM chapter_snapshots WHERE id = ?',
        (snapshot_id,)
    ).fetchone()

    parent = db.execute(
        'SELECT content FROM chapter_snapshots WHERE id = ?',
        (parent_snapshot_id,)
    ).fetchone()

    if not current or not parent:
        return

    current_content = json.loads(current['content'])
    parent_content = json.loads(parent['content'])

    # Compare each section
    sections_to_compare = ['title', 'description', 'steps']

    for section in sections_to_compare:
        if section not in current_content and section not in parent_content:
            continue

        old_value = json.dumps(parent_content.get(section, ''), indent=2)
        new_value = json.dumps(current_content.get(section, ''), indent=2)

        if old_value != new_value:
            # Determine diff type
            if section not in parent_content:
                diff_type = 'added'
            elif section not in current_content:
                diff_type = 'removed'
            else:
                diff_type = 'modified'

            # Store diff
            db.execute('''
                INSERT INTO chapter_diffs
                (snapshot_id, parent_snapshot_id, diff_type, section, old_value, new_value)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (snapshot_id, parent_snapshot_id, diff_type, section, old_value, new_value))

    db.commit()
    db.close()


def get_chapter_diffs(snapshot_id: int) -> List[Dict]:
    """
    Get all diffs for a snapshot

    Returns:
        List of diff entries with visual diff output
    """
    db = get_db()

    diffs = db.execute('''
        SELECT * FROM chapter_diffs WHERE snapshot_id = ?
    ''', (snapshot_id,)).fetchall()

    db.close()

    result = []
    for diff in diffs:
        diff_dict = dict(diff)

        # Generate unified diff (like git diff output)
        if diff['old_value'] and diff['new_value']:
            old_lines = diff['old_value'].splitlines(keepends=True)
            new_lines = diff['new_value'].splitlines(keepends=True)

            unified_diff = list(difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"v{diff['parent_snapshot_id']}",
                tofile=f"v{diff['snapshot_id']}",
                lineterm=''
            ))

            diff_dict['unified_diff'] = ''.join(unified_diff)

        result.append(diff_dict)

    return result


# =============================================================================
# FORKING (like "git clone" or "git fork")
# =============================================================================

def fork_chapter(
    user_id: int,
    chapter_num: int,
    fork_name: str,
    description: Optional[str] = None,
    source_snapshot_id: Optional[int] = None
) -> int:
    """
    Fork a chapter to create user's custom version

    This is like GitHub's "Fork" - creates independent copy.
    Teaches users about cloning in Chapter 5!

    Args:
        user_id: User forking the chapter
        chapter_num: Chapter to fork
        fork_name: Custom name for fork
        description: Why they forked it
        source_snapshot_id: Specific version to fork (or latest)

    Returns:
        fork_id: ID of created fork
    """
    db = get_db()

    # Get source snapshot (latest if not specified)
    if not source_snapshot_id:
        source = db.execute('''
            SELECT id FROM chapter_snapshots
            WHERE chapter_num = ? AND is_fork = 0
            ORDER BY version_num DESC LIMIT 1
        ''', (chapter_num,)).fetchone()

        if not source:
            print(f"❌ No snapshots found for Chapter {chapter_num}")
            return None

        source_snapshot_id = source['id']

    # Create forked snapshot
    source_snapshot = db.execute(
        'SELECT * FROM chapter_snapshots WHERE id = ?',
        (source_snapshot_id,)
    ).fetchone()

    if not source_snapshot:
        print(f"❌ Snapshot {source_snapshot_id} not found")
        return None

    # Create new snapshot marked as fork
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO chapter_snapshots
        (chapter_num, version_num, title, content, commit_message,
         created_by_user_id, parent_snapshot_id, is_fork, fork_source_id)
        VALUES (?, 1, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        chapter_num,
        f"{fork_name} (Fork)",
        source_snapshot['content'],
        f"Forked from Chapter {chapter_num} v{source_snapshot['version_num']}",
        user_id,
        source_snapshot_id,
        source_snapshot_id
    ))

    forked_snapshot_id = cursor.lastrowid

    # Create fork record
    cursor.execute('''
        INSERT INTO user_chapter_forks
        (user_id, chapter_num, fork_name, source_snapshot_id,
         current_snapshot_id, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, chapter_num, fork_name, source_snapshot_id,
          forked_snapshot_id, description))

    fork_id = cursor.lastrowid

    db.commit()
    db.close()

    print(f"✅ Forked Chapter {chapter_num} as '{fork_name}'")
    print(f"   Fork ID: {fork_id}")
    print(f"   Snapshot ID: {forked_snapshot_id}")

    return fork_id


# =============================================================================
# HISTORY & VERSION VIEWING (like "git log")
# =============================================================================

def get_chapter_history(chapter_num: int, user_id: Optional[int] = None) -> List[Dict]:
    """
    Get version history for a chapter

    This is like "git log" - shows all past versions.

    Args:
        chapter_num: Chapter number
        user_id: Filter to user's forks only (optional)

    Returns:
        List of snapshots with metadata
    """
    db = get_db()

    if user_id:
        # Get user's forks
        query = '''
            SELECT s.*, u.username as author
            FROM chapter_snapshots s
            LEFT JOIN users u ON s.created_by_user_id = u.id
            WHERE s.chapter_num = ? AND s.created_by_user_id = ?
            ORDER BY s.created_at DESC
        '''
        snapshots = db.execute(query, (chapter_num, user_id)).fetchall()
    else:
        # Get official versions only
        query = '''
            SELECT s.*, u.username as author
            FROM chapter_snapshots s
            LEFT JOIN users u ON s.created_by_user_id = u.id
            WHERE s.chapter_num = ? AND s.is_fork = 0
            ORDER BY s.version_num DESC
        '''
        snapshots = db.execute(query, (chapter_num,)).fetchall()

    db.close()

    return [dict(s) for s in snapshots]


def get_snapshot(snapshot_id: int) -> Optional[Dict]:
    """Get a specific snapshot by ID"""
    db = get_db()

    snapshot = db.execute(
        'SELECT * FROM chapter_snapshots WHERE id = ?',
        (snapshot_id,)
    ).fetchone()

    db.close()

    if snapshot:
        result = dict(snapshot)
        result['content'] = json.loads(result['content'])
        return result

    return None


# =============================================================================
# PRINTF-STYLE OUTPUT (like Unix echo/printf)
# =============================================================================

def printf_diff(snapshot_id: int) -> str:
    """
    Format diff output like Unix diff command

    Uses ANSI colors for visual display (like git diff --color)
    """
    diffs = get_chapter_diffs(snapshot_id)

    output = []
    output.append(f"\n{'='*60}")
    output.append(f"DIFF: Snapshot #{snapshot_id}")
    output.append(f"{'='*60}\n")

    for diff in diffs:
        output.append(f"\n[{diff['diff_type'].upper()}] {diff['section']}")
        output.append(f"{'-'*60}")

        if diff.get('unified_diff'):
            for line in diff['unified_diff'].split('\n'):
                if line.startswith('+'):
                    output.append(f"+ {line[1:]}")  # Green (added)
                elif line.startswith('-'):
                    output.append(f"- {line[1:]}")  # Red (removed)
                else:
                    output.append(f"  {line}")      # White (unchanged)

    return '\n'.join(output)


def printf_history(chapter_num: int):
    """
    Print chapter history like `git log`

    Shows commit-style output with messages
    """
    history = get_chapter_history(chapter_num)

    print(f"\n{'='*60}")
    print(f"CHAPTER {chapter_num} HISTORY")
    print(f"{'='*60}\n")

    for snapshot in history:
        print(f"Version {snapshot['version_num']} (Snapshot #{snapshot['id']})")
        print(f"Author: {snapshot.get('author', 'Unknown')}")
        print(f"Date: {snapshot['created_at']}")
        print(f"Message: {snapshot['commit_message']}")
        print(f"{'-'*60}\n")


# =============================================================================
# INITIALIZATION - Seed Initial Snapshots
# =============================================================================

def seed_initial_snapshots():
    """
    Create initial snapshots from chapter_tutorials.py

    Run this once to populate the version control system.
    """
    from chapter_tutorials import CHAPTER_TUTORIALS

    print("\n🌱 Seeding initial chapter snapshots...")

    for chapter_num, tutorial in CHAPTER_TUTORIALS.items():
        # Check if already seeded
        db = get_db()
        existing = db.execute(
            'SELECT id FROM chapter_snapshots WHERE chapter_num = ?',
            (chapter_num,)
        ).fetchone()
        db.close()

        if existing:
            print(f"   ℹ️  Chapter {chapter_num} already seeded, skipping...")
            continue

        # Create initial snapshot
        snapshot_id = create_chapter_snapshot(
            chapter_num=chapter_num,
            title=tutorial.get('title', f'Chapter {chapter_num}'),
            content=tutorial,
            commit_message=f"Initial version of {tutorial.get('title')}",
            created_by_user_id=1  # Admin user
        )

        print(f"   ✅ Chapter {chapter_num}: {tutorial.get('title')}")

    print("\n✅ Seeding complete!\n")


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'seed':
            seed_initial_snapshots()

        elif command == 'history' and len(sys.argv) > 2:
            chapter_num = int(sys.argv[2])
            printf_history(chapter_num)

        elif command == 'fork' and len(sys.argv) > 3:
            chapter_num = int(sys.argv[2])
            fork_name = sys.argv[3]
            fork_id = fork_chapter(
                user_id=1,
                chapter_num=chapter_num,
                fork_name=fork_name,
                description="Test fork from CLI"
            )
            print(f"\n✅ Created fork: {fork_id}")

        elif command == 'diff' and len(sys.argv) > 2:
            snapshot_id = int(sys.argv[2])
            print(printf_diff(snapshot_id))

        else:
            print(__doc__)
            print("\nUsage:")
            print("  python chapter_version_control.py seed")
            print("  python chapter_version_control.py history <chapter_num>")
            print("  python chapter_version_control.py fork <chapter_num> <fork_name>")
            print("  python chapter_version_control.py diff <snapshot_id>")

    else:
        print(__doc__)
        print("\nRun with 'seed' to initialize snapshots from chapters.")
