#!/usr/bin/env python3
"""
README ↔ Chapter Bi-Directional Sync

Syncs between GitHub README.md files and chapter_snapshots:

Direction 1: README → Chapter
- Fetches README.md from GitHub
- Converts to chapter_snapshot
- Tracks version history

Direction 2: Chapter → README
- Takes chapter_snapshot content
- Formats as README.md
- Pushes back to GitHub (via local git)

Like: Your README is a living document you can talk to
"""

import json
import re
from pathlib import Path
from database import get_db
from github_readme_parser import fetch_github_readme, parse_readme_to_wordmap
from datetime import datetime

# Local domain repos (like ~/Desktop/roommate-chat/soulfra-simple/output/)
OUTPUT_DIR = Path(__file__).parent / 'output'

def readme_to_chapter(domain_name, github_owner=None, github_repo=None, source='local'):
    """
    Convert README.md to chapter_snapshot

    Args:
        domain_name: Domain name (e.g., 'soulfra')
        github_owner: GitHub owner (if source='github')
        github_repo: Repo name (if source='github')
        source: 'local' or 'github'

    Returns:
        dict with chapter info
    """
    db = get_db()

    # Get README content
    if source == 'local':
        readme_path = OUTPUT_DIR / domain_name / 'README.md'
        if not readme_path.exists():
            return {'success': False, 'error': f'No local README for {domain_name}'}

        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    else:
        # Fetch from GitHub
        readme_content = fetch_github_readme(github_owner, github_repo)
        if not readme_content:
            return {'success': False, 'error': 'Could not fetch GitHub README'}

    # Extract title from first header
    title_match = re.search(r'^#\s+(.+)$', readme_content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"{domain_name.capitalize()} README"

    # Get next chapter number
    max_chapter = db.execute('''
        SELECT MAX(chapter_num) as max_num
        FROM chapter_snapshots
    ''').fetchone()

    chapter_num = (max_chapter['max_num'] or 0) + 1

    # Create chapter
    cursor = db.execute('''
        INSERT INTO chapter_snapshots
        (chapter_num, version_num, title, content, commit_message, created_by_user_id, is_fork, fork_source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        chapter_num,
        1,
        title,
        readme_content,
        f"Synced from {domain_name} README ({source})",
        1,  # System user
        0,
        None
    ))

    chapter_id = cursor.lastrowid
    db.commit()

    return {
        'success': True,
        'chapter_id': chapter_id,
        'chapter_num': chapter_num,
        'domain': domain_name,
        'title': title,
        'source': source,
        'preview': readme_content[:200] + '...'
    }

def chapter_to_readme(chapter_id, domain_name, mode='preview'):
    """
    Convert chapter_snapshot to README.md

    Args:
        chapter_id: ID from chapter_snapshots
        domain_name: Target domain (e.g., 'soulfra')
        mode: 'preview' (return string) or 'write' (write to local file)

    Returns:
        dict with README content or write status
    """
    db = get_db()

    # Get chapter
    chapter = db.execute('''
        SELECT title, content, created_at
        FROM chapter_snapshots
        WHERE id = ?
    ''', (chapter_id,)).fetchone()

    if not chapter:
        return {'success': False, 'error': f'Chapter {chapter_id} not found'}

    # Format as README
    readme_content = chapter['content']

    # Add metadata footer
    footer = f"\n\n---\n*Generated from chapter snapshot on {datetime.now().strftime('%Y-%m-%d')}*\n"
    readme_content += footer

    if mode == 'preview':
        return {
            'success': True,
            'domain': domain_name,
            'content': readme_content,
            'preview': readme_content[:300] + '...'
        }

    # Write to local file
    readme_path = OUTPUT_DIR / domain_name / 'README.md'

    if not readme_path.parent.exists():
        return {'success': False, 'error': f'Domain directory not found: {domain_name}'}

    try:
        # Backup existing README
        if readme_path.exists():
            backup_path = readme_path.with_suffix('.md.backup')
            readme_path.rename(backup_path)

        # Write new README
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        return {
            'success': True,
            'domain': domain_name,
            'path': str(readme_path),
            'backed_up': True
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def sync_readme_and_chapter(domain_name, direction='readme-to-chapter', **kwargs):
    """
    Bi-directional sync wrapper

    Args:
        domain_name: Domain to sync
        direction: 'readme-to-chapter' or 'chapter-to-readme'
        **kwargs: Additional args for specific direction

    Returns:
        dict with sync results
    """
    if direction == 'readme-to-chapter':
        return readme_to_chapter(domain_name, **kwargs)
    elif direction == 'chapter-to-readme':
        return chapter_to_readme(**kwargs)
    else:
        return {'success': False, 'error': f'Invalid direction: {direction}'}

def batch_sync_all_readmes(source='local'):
    """
    Sync all local domain READMEs to chapters

    Returns:
        list of results
    """
    if not OUTPUT_DIR.exists():
        return [{'success': False, 'error': f'Output directory not found: {OUTPUT_DIR}'}]

    results = []
    for domain_dir in OUTPUT_DIR.iterdir():
        if domain_dir.is_dir() and not domain_dir.name.startswith('.'):
            readme_path = domain_dir / 'README.md'
            if readme_path.exists():
                result = readme_to_chapter(domain_dir.name, source=source)
                results.append(result)

    return results

def find_chapters_for_domain(domain_name):
    """
    Find all chapters associated with a domain

    Returns:
        list of chapter dicts
    """
    db = get_db()

    chapters = db.execute('''
        SELECT id, chapter_num, version_num, title, created_at, commit_message
        FROM chapter_snapshots
        WHERE commit_message LIKE ?
        OR title LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{domain_name}%', f'%{domain_name}%')).fetchall()

    return [dict(c) for c in chapters]

def main():
    import sys

    if '--readme-to-chapter' in sys.argv:
        # Sync README → Chapter
        idx = sys.argv.index('--readme-to-chapter')
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]
            source = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else 'local'

            print(f"🔄 Converting {domain} README → Chapter (source: {source})...")
            result = readme_to_chapter(domain, source=source)
            print(json.dumps(result, indent=2))
        else:
            print("❌ Usage: python3 readme_chapter_sync.py --readme-to-chapter DOMAIN [local|github]")

    elif '--chapter-to-readme' in sys.argv:
        # Sync Chapter → README
        idx = sys.argv.index('--chapter-to-readme')
        if idx + 2 < len(sys.argv):
            chapter_id = int(sys.argv[idx + 1])
            domain = sys.argv[idx + 2]
            mode = sys.argv[idx + 3] if idx + 3 < len(sys.argv) else 'preview'

            print(f"🔄 Converting Chapter #{chapter_id} → {domain} README (mode: {mode})...")
            result = chapter_to_readme(chapter_id, domain, mode=mode)
            print(json.dumps(result, indent=2))
        else:
            print("❌ Usage: python3 readme_chapter_sync.py --chapter-to-readme CHAPTER_ID DOMAIN [preview|write]")

    elif '--batch' in sys.argv:
        # Batch sync all READMEs
        print("🔄 Syncing all local READMEs to chapters...\n")
        results = batch_sync_all_readmes()

        print(f"\n{'='*60}")
        print(f"✅ Converted {len([r for r in results if r['success']])} READMEs")
        print(f"❌ Failed {len([r for r in results if not r['success']])}")

        for result in results:
            if result['success']:
                print(f"   ✅ {result['domain']} → Chapter #{result['chapter_num']}")

    elif '--list' in sys.argv:
        # List chapters for domain
        idx = sys.argv.index('--list')
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]
            chapters = find_chapters_for_domain(domain)

            print(f"\n📚 Chapters for {domain}:\n")
            for ch in chapters:
                print(f"   Chapter #{ch['chapter_num']}.{ch['version_num']}: {ch['title']}")
                print(f"      Created: {ch['created_at']}")
                print(f"      Source: {ch['commit_message']}\n")
        else:
            print("❌ Usage: python3 readme_chapter_sync.py --list DOMAIN")

    else:
        print("README ↔ Chapter Bi-Directional Sync")
        print("")
        print("Usage:")
        print("  python3 readme_chapter_sync.py --readme-to-chapter DOMAIN [local|github]")
        print("  python3 readme_chapter_sync.py --chapter-to-readme CHAPTER_ID DOMAIN [preview|write]")
        print("  python3 readme_chapter_sync.py --batch")
        print("  python3 readme_chapter_sync.py --list DOMAIN")

if __name__ == '__main__':
    main()
