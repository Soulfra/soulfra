#!/usr/bin/env python3
"""
List and Categorize All Python Scripts

Scans all .py files and categorizes them by purpose:
- Core (required for basic functionality)
- Tools (utility scripts)
- Demos (proof of concept)
- Homework (chat → blog → newsletter)
- Admin (management scripts)

Usage:
    python3 list_scripts.py
    python3 list_scripts.py --markdown  # Output as markdown table
"""

import sys
from pathlib import Path
import re


# Script categorization
CATEGORIES = {
    'core': {
        'name': '🎯 Core (Required)',
        'description': 'Essential scripts for basic functionality',
        'scripts': [
            'app.py', 'database.py', 'soulfra_zero.py',
            'health_check.py', 'list_scripts.py'
        ]
    },
    'tools': {
        'name': '🛠  Tools (Utilities)',
        'description': 'Standalone tools and utilities',
        'scripts': [
            'issue_tracker.py', 'email_server.py', 'voice_input.py',
            'binary_protocol.py', 'qr_encoder_stdlib.py', 'qr_auth.py',
            'generate_proof.py', 'verify_proof.py'
        ]
    },
    'demos': {
        'name': '🧪 Demos (Proof of Concept)',
        'description': 'Demonstration scripts showing what works',
        'scripts': [
            'show_me_it_works.py', 'prove_it_works.py', 'prove_everything.py',
            'show_me_the_matrix.py'
        ]
    },
    'homework': {
        'name': '📚 Homework (Content Workflow)',
        'description': 'Chat → Blog → Newsletter pipeline',
        'scripts': [
            'ollama_chat.py', 'compile_chats.py', 'newsletter_digest.py',
            'ollama_auto_commenter.py'
        ]
    },
    'admin': {
        'name': '👨‍💼 Admin (Management)',
        'description': 'Administrative and setup scripts',
        'scripts': [
            'build.py', 'static_site.py', 'init_db.py', 'seed_data.py',
            'migrate.py', 'backup.py'
        ]
    }
}


def get_script_description(filepath: Path) -> str:
    """Extract description from script docstring"""
    try:
        with open(filepath, 'r') as f:
            content = f.read(500)  # Read first 500 chars

            # Look for docstring
            match = re.search(r'"""([^"]+)"""', content)
            if match:
                doc = match.group(1).strip()
                # Get first line
                first_line = doc.split('\n')[0].strip()
                return first_line

            # Look for # comment on line 2-3
            lines = content.split('\n')
            for line in lines[1:4]:
                if line.startswith('#') and len(line) > 3:
                    return line[1:].strip()

        return '(no description)'

    except:
        return '(error reading file)'


def categorize_script(filename: str) -> str:
    """Determine category for a script"""
    for category, data in CATEGORIES.items():
        if filename in data['scripts']:
            return category

    # Auto-categorize based on name patterns
    if any(x in filename for x in ['test_', '_test', 'example_']):
        return 'test'
    elif any(x in filename for x in ['ml_', 'neural_', 'train_']):
        return 'ml'
    elif any(x in filename for x in ['reasoning_', 'soul_']):
        return 'reasoning'
    else:
        return 'other'


def list_scripts(markdown=False):
    """List all Python scripts by category"""
    # Get all .py files
    all_scripts = sorted([p for p in Path('.').glob('*.py')
                         if not p.name.startswith('__')])

    # Categorize
    categorized = {}
    for script in all_scripts:
        category = categorize_script(script.name)

        if category not in categorized:
            categorized[category] = []

        categorized[category].append({
            'name': script.name,
            'description': get_script_description(script),
            'size': script.stat().st_size
        })

    # Print results
    if markdown:
        print_markdown(categorized)
    else:
        print_terminal(categorized)


def print_terminal(categorized: dict):
    """Print categorized scripts to terminal"""
    print("=" * 70)
    print("📋 SOULFRA SIMPLE - SCRIPT INVENTORY")
    print("=" * 70)
    print()

    total_count = sum(len(scripts) for scripts in categorized.values())
    print(f"Total: {total_count} Python scripts")
    print()

    # Print known categories first
    for category_key in ['core', 'tools', 'demos', 'homework', 'admin']:
        if category_key not in categorized:
            continue

        category_data = CATEGORIES[category_key]
        scripts = categorized[category_key]

        print(category_data['name'])
        print(f"  {category_data['description']}")
        print()

        for script in scripts:
            print(f"  • {script['name']}")
            print(f"    {script['description']}")
            print()

        print()

    # Print other categories
    for category_key, scripts in categorized.items():
        if category_key in ['core', 'tools', 'demos', 'homework', 'admin']:
            continue

        print(f"📦 {category_key.upper()}")
        print()

        for script in scripts:
            print(f"  • {script['name']}")
            print(f"    {script['description']}")
            print()

        print()


def print_markdown(categorized: dict):
    """Print categorized scripts as markdown"""
    print("# Soulfra Simple - Script Inventory")
    print()

    total_count = sum(len(scripts) for scripts in categorized.values())
    print(f"**Total: {total_count} Python scripts**")
    print()

    # Print known categories first
    for category_key in ['core', 'tools', 'demos', 'homework', 'admin']:
        if category_key not in categorized:
            continue

        category_data = CATEGORIES[category_key]
        scripts = categorized[category_key]

        print(f"## {category_data['name']}")
        print()
        print(category_data['description'])
        print()
        print("| Script | Description |")
        print("|--------|-------------|")

        for script in scripts:
            desc = script['description'].replace('|', '\\|')
            print(f"| `{script['name']}` | {desc} |")

        print()

    # Print other categories
    for category_key, scripts in categorized.items():
        if category_key in ['core', 'tools', 'demos', 'homework', 'admin']:
            continue

        print(f"## {category_key.upper()}")
        print()
        print("| Script | Description |")
        print("|--------|-------------|")

        for script in scripts:
            desc = script['description'].replace('|', '\\|')
            print(f"| `{script['name']}` | {desc} |")

        print()


def search_scripts(query: str):
    """Search scripts by name or description"""
    all_scripts = sorted([p for p in Path('.').glob('*.py')
                         if not p.name.startswith('__')])

    print(f"🔍 Searching for: {query}")
    print()

    matches = []
    for script in all_scripts:
        if query.lower() in script.name.lower():
            matches.append(script)
        else:
            desc = get_script_description(script)
            if query.lower() in desc.lower():
                matches.append(script)

    if not matches:
        print("No matches found.")
        return

    print(f"Found {len(matches)} matches:")
    print()

    for script in matches:
        print(f"• {script.name}")
        print(f"  {get_script_description(script)}")
        print()


def main():
    """Main entry point"""
    if '--markdown' in sys.argv or '-m' in sys.argv:
        list_scripts(markdown=True)
    elif '--search' in sys.argv or '-s' in sys.argv:
        if len(sys.argv) < 3:
            print("Usage: python3 list_scripts.py --search <query>")
            sys.exit(1)
        query = sys.argv[2]
        search_scripts(query)
    elif '--help' in sys.argv or '-h' in sys.argv:
        print("Usage:")
        print("  python3 list_scripts.py           # List all scripts")
        print("  python3 list_scripts.py --markdown  # Output as markdown")
        print("  python3 list_scripts.py --search <query>  # Search scripts")
    else:
        list_scripts(markdown=False)


if __name__ == '__main__':
    main()
