#!/usr/bin/env python3
"""
Analyze Code Duplicates - Find What to DELETE

Shows "negative numbers" - code reduction opportunities.
Zero Dependencies: Python stdlib only
"""

import os
import re


def count_lines(filepath):
    """Count lines in file"""
    try:
        with open(filepath, 'r') as f:
            return len(f.readlines())
    except:
        return 0


def analyze_ollama_duplicates():
    """Find duplicate Ollama implementations"""
    files = {
        'ollama_auto_commenter.py': 'Duplicate',
        'ollama_chat.py': 'Duplicate',
        'prove_it_works.py': 'Duplicate',
        'ollama_discussion.py': 'Duplicate',
        'ai_orchestrator.py': 'KEEP (unified)'
    }

    results = []
    total_duplicate_lines = 0

    for filepath, status in files.items():
        if os.path.exists(filepath):
            lines = count_lines(filepath)
            results.append({
                'file': filepath,
                'lines': lines,
                'status': status
            })
            if status == 'Duplicate':
                total_duplicate_lines += lines

    return results, total_duplicate_lines


def find_unused_files():
    """Find potentially unused Python files"""
    # Files that are probably old/unused based on naming
    suspicious_patterns = [
        'test_*.py',
        'prove_*.py',
        '*_test.py',
        'dogfood_*.py',
        'create_*_post.py'
    ]

    unused = []
    for pattern in suspicious_patterns:
        import glob
        for filepath in glob.glob(pattern):
            if os.path.exists(filepath):
                lines = count_lines(filepath)
                unused.append({
                    'file': filepath,
                    'lines': lines,
                    'reason': 'Test/proof/dogfood file'
                })

    return unused


def main():
    print("🔍 Analyzing Code Duplicates")
    print("=" * 70)

    # Analyze Ollama duplicates
    print("\n📦 Ollama Implementations:")
    ollama_files, ollama_duplicate_lines = analyze_ollama_duplicates()

    for item in ollama_files:
        status_icon = "❌" if item['status'] == 'Duplicate' else "✅"
        print(f"   {status_icon} {item['file']}: {item['lines']} lines - {item['status']}")

    print(f"\n   💡 Can DELETE: {ollama_duplicate_lines} lines")

    # Find unused files
    print("\n📁 Potentially Unused Files:")
    unused = find_unused_files()

    unused_lines = 0
    for item in unused[:10]:  # Show first 10
        print(f"   ⚠️  {item['file']}: {item['lines']} lines - {item['reason']}")
        unused_lines += item['lines']

    if len(unused) > 10:
        remaining_unused = sum(count_lines(item['file']) for item in unused[10:])
        unused_lines += remaining_unused
        print(f"   ... and {len(unused) - 10} more files")

    print(f"\n   💡 Can DELETE: {unused_lines} lines")

    # Total reduction
    total_reduction = ollama_duplicate_lines + unused_lines
    total_lines = sum(count_lines(f) for f in os.listdir('.') if f.endswith('.py'))

    print("\n" + "=" * 70)
    print("📊 REDUCTION OPPORTUNITY:")
    print(f"   Current codebase: {total_lines:,} lines")
    print(f"   Can remove: -{total_reduction:,} lines")
    print(f"   After cleanup: {total_lines - total_reduction:,} lines")
    print(f"   Reduction: {(total_reduction / total_lines * 100):.1f}%")
    print("\n💡 These are the 'negative numbers' you wanted!")


if __name__ == '__main__':
    main()
