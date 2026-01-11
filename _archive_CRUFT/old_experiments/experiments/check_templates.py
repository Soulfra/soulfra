#!/usr/bin/env python3
"""
Template Health Checker - Verify All Templates Are Working (WITH AUTO-HEALING)

Scans templates/ directory and app.py to:
- List all templates and their usage
- Identify unused templates
- Categorize templates by type
- Check for missing template files
- AUTO-HEAL: Generate missing templates from similar ones

Usage:
    python3 check_templates.py              # Full health check
    python3 check_templates.py --unused     # Show only unused templates
    python3 check_templates.py --summary    # Brief summary only
    python3 check_templates.py --auto-heal  # AUTO-FIX missing templates
"""

import re
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


def find_all_templates(templates_dir: str = 'templates') -> List[Path]:
    """
    Find all template files in templates directory

    Args:
        templates_dir: Templates directory path

    Returns:
        List of template file paths
    """
    templates_path = Path(templates_dir)

    if not templates_path.exists():
        print(f"[ERROR] Templates directory not found: {templates_dir}")
        return []

    # Find all .html files
    templates = list(templates_path.rglob('*.html'))

    return sorted(templates)


def find_template_usage(app_file: str = 'app.py') -> Dict[str, List[Tuple[int, str]]]:
    """
    Find all render_template() calls in app.py

    Args:
        app_file: Path to Flask app file

    Returns:
        Dict mapping template names to list of (line_number, route_function) tuples
    """
    app_path = Path(app_file)

    if not app_path.exists():
        print(f"[ERROR] App file not found: {app_file}")
        return {}

    content = app_path.read_text()
    lines = content.split('\n')

    # Pattern to match render_template('template_name.html', ...)
    # Also matches render_template("template_name.html", ...)
    pattern = r'render_template\([\'"]([^\'"\)]+\.html)[\'"]'

    usage = defaultdict(list)
    current_function = None

    for i, line in enumerate(lines, 1):
        # Track current function/route
        if line.strip().startswith('def '):
            match = re.match(r'\s*def\s+(\w+)\s*\(', line)
            if match:
                current_function = match.group(1)

        # Find render_template calls
        matches = re.findall(pattern, line)
        for template_name in matches:
            usage[template_name].append((i, current_function or 'unknown'))

    return dict(usage)


def categorize_templates(templates: List[Path]) -> Dict[str, List[str]]:
    """
    Categorize templates by their directory/name

    Args:
        templates: List of template paths

    Returns:
        Dict mapping category to list of template names
    """
    categories = defaultdict(list)

    for template in templates:
        # Get relative path from templates/
        rel_path = str(template.relative_to('templates'))

        # Categorize by directory or name patterns
        if 'admin' in rel_path or 'dashboard' in rel_path:
            categories['Admin & Dashboards'].append(rel_path)
        elif 'auth' in rel_path or 'login' in rel_path or 'signup' in rel_path:
            categories['Authentication'].append(rel_path)
        elif 'api' in rel_path or 'docs' in rel_path:
            categories['API & Documentation'].append(rel_path)
        elif 'error' in rel_path or rel_path.startswith('4') or rel_path.startswith('5'):
            categories['Error Pages'].append(rel_path)
        elif 'email' in rel_path or 'newsletter' in rel_path:
            categories['Email & Newsletter'].append(rel_path)
        elif 'brand' in rel_path or 'soul' in rel_path or 'persona' in rel_path:
            categories['AI & Personas'].append(rel_path)
        elif 'post' in rel_path or 'comment' in rel_path or 'feed' in rel_path:
            categories['Content & Posts'].append(rel_path)
        elif '/' in rel_path:  # Subdirectory templates
            subdir = rel_path.split('/')[0]
            categories[f'Feature: {subdir.title()}'].append(rel_path)
        else:
            categories['Core Pages'].append(rel_path)

    return dict(categories)


def check_template_health(templates_dir: str = 'templates', app_file: str = 'app.py') -> Dict:
    """
    Full health check of all templates

    Returns:
        Dict with health check results
    """
    # Find all templates
    all_templates = find_all_templates(templates_dir)
    template_names = {str(t.relative_to(templates_dir)) for t in all_templates}

    # Find usage in app.py
    usage = find_template_usage(app_file)

    # Find unused templates
    used_templates = set(usage.keys())
    unused_templates = template_names - used_templates

    # Find missing templates (referenced but don't exist)
    missing_templates = used_templates - template_names

    # Categorize
    categories = categorize_templates(all_templates)

    return {
        'total_templates': len(all_templates),
        'used_templates': len(used_templates),
        'unused_templates': len(unused_templates),
        'missing_templates': len(missing_templates),
        'template_names': template_names,
        'usage': usage,
        'unused': unused_templates,
        'missing': missing_templates,
        'categories': categories
    }


def print_health_report(health: Dict, show_unused_only: bool = False, summary_only: bool = False):
    """Print formatted health check report"""

    if summary_only:
        print("\n" + "=" * 70)
        print("TEMPLATE HEALTH CHECK SUMMARY")
        print("=" * 70)
        print(f"\nTotal Templates: {health['total_templates']}")
        print(f"Used Templates: {health['used_templates']}")
        print(f"Unused Templates: {health['unused_templates']}")
        print(f"Missing Templates: {health['missing_templates']}")

        if health['missing_templates'] > 0:
            print("\n[WARNING] Some templates are referenced but don't exist!")

        print("\n" + "=" * 70 + "\n")
        return

    if show_unused_only:
        print("\n" + "=" * 70)
        print("UNUSED TEMPLATES")
        print("=" * 70 + "\n")

        if health['unused']:
            for template in sorted(health['unused']):
                print(f"  - {template}")
            print(f"\nTotal: {len(health['unused'])} unused templates")
        else:
            print("[OK] All templates are being used!")

        print("\n" + "=" * 70 + "\n")
        return

    # Full report
    print("\n" + "=" * 70)
    print("TEMPLATE HEALTH CHECK")
    print("=" * 70)

    # Summary
    print(f"\nTotal Templates: {health['total_templates']}")
    print(f"Used Templates: {health['used_templates']}")
    print(f"Unused Templates: {health['unused_templates']}")
    print(f"Missing Templates: {health['missing_templates']}")

    # Missing templates (critical)
    if health['missing']:
        print("\n" + "-" * 70)
        print("[ERROR] MISSING TEMPLATES (referenced but don't exist):")
        print("-" * 70)
        for template in sorted(health['missing']):
            print(f"  - {template}")
            if template in health['usage']:
                for line_num, func in health['usage'][template]:
                    print(f"      Used in: {func}() at line {line_num}")

    # Templates by category
    print("\n" + "-" * 70)
    print("TEMPLATES BY CATEGORY")
    print("-" * 70)

    for category, templates in sorted(health['categories'].items()):
        print(f"\n{category} ({len(templates)} templates):")
        for template in sorted(templates):
            # Check if used
            status = "[USED]" if template in health['usage'] else "[UNUSED]"
            print(f"  {status:10} {template}")

            # Show usage
            if template in health['usage'] and len(health['usage'][template]) <= 3:
                for line_num, func in health['usage'][template]:
                    print(f"             └─ {func}() (line {line_num})")

    # Unused templates
    if health['unused']:
        print("\n" + "-" * 70)
        print(f"[INFO] UNUSED TEMPLATES ({len(health['unused'])} total):")
        print("-" * 70)
        for template in sorted(health['unused']):
            print(f"  - {template}")

    # Most used templates
    print("\n" + "-" * 70)
    print("MOST USED TEMPLATES (Top 10)")
    print("-" * 70)

    most_used = sorted(health['usage'].items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for template, usages in most_used:
        print(f"\n{template} ({len(usages)} uses):")
        for line_num, func in usages[:5]:  # Show first 5 uses
            print(f"  - {func}() (line {line_num})")
        if len(usages) > 5:
            print(f"  ... and {len(usages) - 5} more")

    print("\n" + "=" * 70 + "\n")


# ==============================================================================
# AUTO-HEALING FUNCTIONS
# ==============================================================================

def find_similar_template(missing_template: str, existing_templates: Set[str]) -> Optional[str]:
    """
    Find the most similar existing template to use as a base

    Args:
        missing_template: Name of missing template
        existing_templates: Set of existing template names

    Returns:
        Name of most similar template, or None
    """
    # Extract key parts of template name
    missing_parts = missing_template.replace('.html', '').split('_')

    # Pattern matching rules
    patterns = {
        'detail': ['profile', 'page', 'view', 'soul'],
        'stats': ['status', 'dashboard', 'analytics'],
        'visualize': ['debug', 'view', 'display'],
        'edit': ['form', 'update', 'create'],
        'admin': ['dashboard', 'panel', 'manage'],
        'list': ['index', 'all', 'browse'],
    }

    # Find templates with similar keywords
    candidates = []
    for template in existing_templates:
        template_parts = template.replace('.html', '').split('_')

        # Count matching parts
        matches = 0
        for part in missing_parts:
            if part in template_parts:
                matches += 1
            # Check pattern matches
            for pattern_key, pattern_values in patterns.items():
                if pattern_key in missing_parts and any(pv in template_parts for pv in pattern_values):
                    matches += 0.5

        if matches > 0:
            candidates.append((template, matches))

    if not candidates:
        # Fallback: Find templates in same category
        if 'ai_' in missing_template or 'soul' in missing_template:
            return next((t for t in existing_templates if 'soul' in t or 'ai_' in t), None)
        elif 'brand' in missing_template:
            return next((t for t in existing_templates if 'brand' in t), None)
        elif 'admin' in missing_template:
            return next((t for t in existing_templates if 'admin' in t), None)
        else:
            return None

    # Return template with highest match score
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def auto_heal_template(missing_template: str, base_template: str,
                       templates_dir: str = 'templates') -> bool:
    """
    Auto-generate missing template from a similar base template

    Args:
        missing_template: Name of missing template to create
        base_template: Name of existing template to use as base
        templates_dir: Templates directory path

    Returns:
        True if successful, False otherwise
    """
    templates_path = Path(templates_dir)
    base_path = templates_path / base_template
    new_path = templates_path / missing_template

    if not base_path.exists():
        print(f"[ERROR] Base template not found: {base_template}")
        return False

    try:
        # Read base template
        with open(base_path, 'r') as f:
            content = f.read()

        # Extract template name parts for replacements
        base_name = base_template.replace('.html', '').replace('_', ' ').title()
        new_name = missing_template.replace('.html', '').replace('_', ' ').title()

        # Smart replacements
        replacements = {
            base_template.replace('.html', ''): missing_template.replace('.html', ''),
            base_name: new_name,
            # Replace route patterns
            base_template.split('_')[0]: missing_template.split('_')[0],
        }

        # Apply replacements
        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)

        # Create backup directory if needed
        backup_dir = templates_path / '_auto_heal_backup'
        backup_dir.mkdir(exist_ok=True)

        # Save backup info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_info = backup_dir / f'heal_{timestamp}.txt'
        with open(backup_info, 'w') as f:
            f.write(f"Auto-healed template: {missing_template}\n")
            f.write(f"Based on: {base_template}\n")
            f.write(f"Timestamp: {timestamp}\n")

        # Write new template
        with open(new_path, 'w') as f:
            f.write(new_content)

        print(f"[AUTO-HEAL] ✅ Created {missing_template} based on {base_template}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to auto-heal {missing_template}: {e}")
        return False


def auto_heal_all_missing(health: Dict, templates_dir: str = 'templates') -> Dict:
    """
    Auto-heal all missing templates

    Args:
        health: Health check results dict
        templates_dir: Templates directory

    Returns:
        Dict with healing results
    """
    results = {
        'attempted': 0,
        'successful': 0,
        'failed': 0,
        'healed': [],
        'failed_list': []
    }

    if not health['missing']:
        print("[INFO] No missing templates to heal")
        return results

    print("\n" + "=" * 70)
    print("AUTO-HEALING MISSING TEMPLATES")
    print("=" * 70 + "\n")

    for missing_template in sorted(health['missing']):
        results['attempted'] += 1

        # Find similar template
        similar = find_similar_template(missing_template, health['template_names'])

        if not similar:
            print(f"[SKIP] No similar template found for: {missing_template}")
            results['failed'] += 1
            results['failed_list'].append(missing_template)
            continue

        print(f"\n[HEALING] {missing_template}")
        print(f"          └─ Using {similar} as base template")

        # Auto-heal
        success = auto_heal_template(missing_template, similar, templates_dir)

        if success:
            results['successful'] += 1
            results['healed'].append({
                'new': missing_template,
                'base': similar
            })
        else:
            results['failed'] += 1
            results['failed_list'].append(missing_template)

    # Print summary
    print("\n" + "-" * 70)
    print("AUTO-HEAL SUMMARY")
    print("-" * 70)
    print(f"Attempted: {results['attempted']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")

    if results['healed']:
        print("\n✅ Successfully healed:")
        for item in results['healed']:
            print(f"  - {item['new']} (based on {item['base']})")

    if results['failed_list']:
        print("\n❌ Failed to heal:")
        for template in results['failed_list']:
            print(f"  - {template}")

    print("\n" + "=" * 70 + "\n")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Template Health Checker with Auto-Healing')
    parser.add_argument('--unused', action='store_true', help='Show only unused templates')
    parser.add_argument('--summary', action='store_true', help='Show brief summary only')
    parser.add_argument('--auto-heal', action='store_true', help='AUTO-FIX missing templates')
    parser.add_argument('--templates-dir', default='templates', help='Templates directory (default: templates)')
    parser.add_argument('--app-file', default='app.py', help='Flask app file (default: app.py)')

    args = parser.parse_args()

    # Run health check
    health = check_template_health(args.templates_dir, args.app_file)

    # Auto-heal if requested
    if args.auto_heal:
        if health['missing_templates'] > 0:
            heal_results = auto_heal_all_missing(health, args.templates_dir)

            # Re-run health check to verify fixes
            print("\n[INFO] Re-running health check to verify auto-heal...")
            health = check_template_health(args.templates_dir, args.app_file)

            if health['missing_templates'] == 0:
                print("\n✅ SUCCESS! All templates healed. No missing templates.")
                exit(0)
            else:
                print(f"\n⚠️  {health['missing_templates']} template(s) still missing after auto-heal.")
                print_health_report(health, summary_only=True)
                exit(1)
        else:
            print("\n[INFO] No missing templates to heal. System is healthy!")
            exit(0)

    # Print report (normal mode)
    print_health_report(health, show_unused_only=args.unused, summary_only=args.summary)

    # Exit with error if missing templates
    if health['missing_templates'] > 0:
        print("\n💡 TIP: Run with --auto-heal to automatically fix missing templates")
        exit(1)
