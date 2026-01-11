#!/usr/bin/env python3
"""
Project Cleanup - Delete 800MB+ of Logs and Fix Structure

Removes:
- Giant log files (803MB total)
- Nested .git directories
- Backup files (.bak)
- Test artifacts

Usage:
    python3 cleanup_project.py --dry-run    # Preview changes
    python3 cleanup_project.py              # Actually delete files
"""

import os
import shutil
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Files and directories to delete
CLEANUP_TARGETS = {
    'logs': [
        'logs/flask-out.log',
        'logs/flask-combined.log',
        'logs/cringeproof-combined.log',
        'logs/calriven-combined.log',
        'logs/deathtodata-combined.log',
        'logs/howtocookathome-combined.log',
        'logs/',  # Delete entire logs directory
    ],
    'git_directories': [
        'output/soulfra/.git',
        'soulfra-dotgithub/.git',
    ],
    'backups': [
        '**/*.bak',
        '**/*~',
        '**/*.swp',
    ],
    'cache': [
        '**/__pycache__',
        '**/.pytest_cache',
        '**/.DS_Store',
    ]
}


def get_size(path):
    """Get size of file or directory in bytes"""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except PermissionError:
            pass
        return total
    return 0


def format_size(bytes_size):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def preview_cleanup():
    """Show what will be deleted without actually deleting"""
    print("\n" + "="*70)
    print(" "*20 + "CLEANUP PREVIEW (DRY RUN)")
    print("="*70 + "\n")

    total_size = 0
    items_found = []

    # Check logs
    print("[1/4] Checking log files...")
    for log_path in CLEANUP_TARGETS['logs']:
        path = PROJECT_ROOT / log_path
        if path.exists():
            size = get_size(path)
            total_size += size
            items_found.append(('LOG', log_path, size))
            print(f"   🗑️  {log_path:<50} {format_size(size):>10}")

    # Check nested git directories
    print("\n[2/4] Checking nested .git directories...")
    for git_path in CLEANUP_TARGETS['git_directories']:
        path = PROJECT_ROOT / git_path
        if path.exists():
            size = get_size(path)
            total_size += size
            items_found.append(('GIT', git_path, size))
            print(f"   🗑️  {git_path:<50} {format_size(size):>10}")

    # Check backups
    print("\n[3/4] Checking backup files...")
    for pattern in CLEANUP_TARGETS['backups']:
        for path in PROJECT_ROOT.glob(pattern):
            if path.exists():
                size = get_size(path)
                total_size += size
                rel_path = str(path.relative_to(PROJECT_ROOT))
                items_found.append(('BAK', rel_path, size))
                print(f"   🗑️  {rel_path:<50} {format_size(size):>10}")

    # Check cache
    print("\n[4/4] Checking cache directories...")
    for pattern in CLEANUP_TARGETS['cache']:
        for path in PROJECT_ROOT.glob(pattern):
            if path.exists():
                size = get_size(path)
                total_size += size
                rel_path = str(path.relative_to(PROJECT_ROOT))
                items_found.append(('CACHE', rel_path, size))
                print(f"   🗑️  {rel_path:<50} {format_size(size):>10}")

    # Summary
    print("\n" + "="*70)
    print(f"Total items to delete: {len(items_found)}")
    print(f"Total space to free:   {format_size(total_size)}")
    print("="*70 + "\n")

    print("💡 To actually delete these files, run:")
    print("   python3 cleanup_project.py")
    print()

    return items_found, total_size


def execute_cleanup():
    """Actually delete the files"""
    print("\n" + "="*70)
    print(" "*20 + "EXECUTING CLEANUP")
    print("="*70 + "\n")

    total_size = 0
    deleted_count = 0

    # Delete logs
    print("[1/4] Deleting log files...")
    for log_path in CLEANUP_TARGETS['logs']:
        path = PROJECT_ROOT / log_path
        if path.exists():
            size = get_size(path)
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                total_size += size
                deleted_count += 1
                print(f"   ✅ Deleted: {log_path} ({format_size(size)})")
            except Exception as e:
                print(f"   ❌ Failed: {log_path} - {e}")

    # Delete nested git directories
    print("\n[2/4] Deleting nested .git directories...")
    for git_path in CLEANUP_TARGETS['git_directories']:
        path = PROJECT_ROOT / git_path
        if path.exists():
            size = get_size(path)
            try:
                shutil.rmtree(path)
                total_size += size
                deleted_count += 1
                print(f"   ✅ Deleted: {git_path} ({format_size(size)})")
            except Exception as e:
                print(f"   ❌ Failed: {git_path} - {e}")

    # Delete backups
    print("\n[3/4] Deleting backup files...")
    for pattern in CLEANUP_TARGETS['backups']:
        for path in PROJECT_ROOT.glob(pattern):
            if path.exists():
                size = get_size(path)
                rel_path = str(path.relative_to(PROJECT_ROOT))
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    total_size += size
                    deleted_count += 1
                    print(f"   ✅ Deleted: {rel_path} ({format_size(size)})")
                except Exception as e:
                    print(f"   ❌ Failed: {rel_path} - {e}")

    # Delete cache
    print("\n[4/4] Deleting cache directories...")
    for pattern in CLEANUP_TARGETS['cache']:
        for path in PROJECT_ROOT.glob(pattern):
            if path.exists():
                size = get_size(path)
                rel_path = str(path.relative_to(PROJECT_ROOT))
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    total_size += size
                    deleted_count += 1
                    print(f"   ✅ Deleted: {rel_path} ({format_size(size)})")
                except Exception as e:
                    print(f"   ❌ Failed: {rel_path} - {e}")

    # Summary
    print("\n" + "="*70)
    print(f"✅ Cleanup complete!")
    print(f"   Files deleted:  {deleted_count}")
    print(f"   Space freed:    {format_size(total_size)}")
    print("="*70 + "\n")

    return deleted_count, total_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean up project files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what will be deleted without actually deleting')
    args = parser.parse_args()

    if args.dry_run:
        preview_cleanup()
    else:
        # Show preview first
        items, size = preview_cleanup()

        # Confirm deletion
        print("⚠️  WARNING: This will permanently delete the files above!")
        response = input("   Type 'yes' to continue: ")

        if response.lower() == 'yes':
            execute_cleanup()
        else:
            print("\n❌ Cleanup cancelled.")
