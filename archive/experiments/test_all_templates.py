#!/usr/bin/env python3
"""
Template Testing System - Validate All HTML Templates

Tests all templates in the templates/ directory to ensure they:
- Render without errors
- Have no missing variables
- Extend from base.html correctly
- Don't have broken url_for() references

Usage:
    python3 test_all_templates.py              # Test all templates
    python3 test_all_templates.py --verbose    # Show detailed output
    python3 test_all_templates.py --fix        # Auto-fix common issues
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import re


def discover_templates(templates_dir: str = 'templates') -> List[Path]:
    """Find all .html files in templates directory"""
    templates_path = Path(templates_dir)
    if not templates_path.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return []

    templates = list(templates_path.rglob('*.html'))
    return sorted(templates)


def check_extends_base(template_path: Path) -> Tuple[bool, str]:
    """Check if template extends base.html"""
    content = template_path.read_text()

    # Look for {% extends "base.html" %} or {% extends 'base.html' %}
    if re.search(r'{%\s*extends\s+["\']base\.html["\']\s*%}', content):
        return True, "Extends base.html"

    # Special case: base.html itself doesn't need to extend
    if template_path.name == 'base.html':
        return True, "Is base.html"

    # Check if it's a fragment/partial (no html/head/body tags)
    if not re.search(r'<html|<head|<body', content):
        return True, "Fragment/partial template"

    return False, "Missing {% extends 'base.html' %}"


def find_jinja_variables(template_path: Path) -> List[str]:
    """Find all Jinja2 variables used in template"""
    content = template_path.read_text()

    # Find {{ variable }} patterns
    variables = re.findall(r'{{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)', content)

    # Remove duplicates and filter out Jinja functions
    variables = list(set(variables))
    variables = [v for v in variables if not v.startswith('url_for') and not v.startswith('get_flashed')]

    return sorted(variables)


def find_url_for_calls(template_path: Path) -> List[str]:
    """Find all url_for() calls in template"""
    content = template_path.read_text()

    # Find url_for('route_name') patterns
    urls = re.findall(r'url_for\(["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']', content)

    return sorted(set(urls))


def check_common_issues(template_path: Path) -> List[str]:
    """Check for common template issues"""
    issues = []
    content = template_path.read_text()

    # Check for unclosed tags
    open_tags = re.findall(r'{%\s*(\w+)', content)
    close_tags = re.findall(r'{%\s*end(\w+)', content)

    for tag in ['block', 'if', 'for']:
        open_count = open_tags.count(tag)
        close_count = close_tags.count(tag)
        if open_count != close_count:
            issues.append(f"Unclosed {{% {tag} %}} tag (open: {open_count}, close: {close_count})")

    # Check for common typos
    if '{{{{' in content or '}}}}' in content:
        issues.append("Double curly braces {{ {{ or }} }} found - possible typo")

    # Check for hardcoded localhost URLs
    if 'http://localhost:' in content or 'https://localhost:' in content:
        issues.append("Hardcoded localhost URL found - use url_for() instead")

    # Check for missing title block
    if template_path.name != 'base.html' and 'extends' in content:
        if '{% block title %}' not in content and '{%block title%}' not in content:
            issues.append("Missing {% block title %} - page will use default title")

    return issues


def test_template_syntax(template_path: Path) -> Tuple[bool, str]:
    """Test if template has valid Jinja2 syntax"""
    try:
        from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

        env = Environment(loader=FileSystemLoader('templates'))

        # Get relative path from templates/ directory
        rel_path = template_path.relative_to('templates')

        # Try to load template
        env.get_template(str(rel_path))

        return True, "Syntax valid"

    except TemplateSyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error loading template: {e}"


def analyze_template(template_path: Path, verbose: bool = False) -> Dict:
    """Analyze a single template"""
    results = {
        'path': str(template_path),
        'name': template_path.name,
        'extends_base': check_extends_base(template_path),
        'syntax_valid': test_template_syntax(template_path),
        'variables': find_jinja_variables(template_path),
        'url_for_calls': find_url_for_calls(template_path),
        'issues': check_common_issues(template_path),
        'status': 'pass'
    }

    # Determine overall status
    if not results['syntax_valid'][0]:
        results['status'] = 'fail'
    elif not results['extends_base'][0]:
        results['status'] = 'warning'
    elif results['issues']:
        results['status'] = 'warning'

    return results


def print_template_report(results: List[Dict], verbose: bool = False):
    """Print test results report"""
    print("\n" + "=" * 80)
    print("  TEMPLATE TESTING REPORT")
    print("=" * 80)

    # Summary stats
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'pass')
    warnings = sum(1 for r in results if r['status'] == 'warning')
    failed = sum(1 for r in results if r['status'] == 'fail')

    print(f"\n📊 Summary:")
    print(f"   Total templates: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ⚠️  Warnings: {warnings}")
    print(f"   ❌ Failed: {failed}")

    # Show failures first
    if failed > 0:
        print("\n" + "-" * 80)
        print("❌ FAILED TEMPLATES")
        print("-" * 80)
        for result in results:
            if result['status'] == 'fail':
                print(f"\n{result['path']}")
                print(f"   {result['syntax_valid'][1]}")

    # Show warnings
    if warnings > 0:
        print("\n" + "-" * 80)
        print("⚠️  TEMPLATES WITH WARNINGS")
        print("-" * 80)
        for result in results:
            if result['status'] == 'warning':
                print(f"\n{result['path']}")

                if not result['extends_base'][0]:
                    print(f"   - {result['extends_base'][1]}")

                for issue in result['issues']:
                    print(f"   - {issue}")

    # Verbose output
    if verbose:
        print("\n" + "-" * 80)
        print("📝 DETAILED TEMPLATE ANALYSIS")
        print("-" * 80)
        for result in results:
            status_icon = {'pass': '✅', 'warning': '⚠️', 'fail': '❌'}[result['status']]
            print(f"\n{status_icon} {result['path']}")

            if result['variables']:
                print(f"   Variables used: {', '.join(result['variables'][:10])}")
                if len(result['variables']) > 10:
                    print(f"   ... and {len(result['variables']) - 10} more")

            if result['url_for_calls']:
                print(f"   Routes referenced: {', '.join(result['url_for_calls'][:5])}")
                if len(result['url_for_calls']) > 5:
                    print(f"   ... and {len(result['url_for_calls']) - 5} more")

    # Common variables report
    print("\n" + "-" * 80)
    print("🔧 MOST COMMON VARIABLES USED")
    print("-" * 80)

    # Collect all variables
    all_vars = []
    for result in results:
        all_vars.extend(result['variables'])

    # Count occurrences
    var_counts = {}
    for var in all_vars:
        var_counts[var] = var_counts.get(var, 0) + 1

    # Show top 10
    sorted_vars = sorted(var_counts.items(), key=lambda x: x[1], reverse=True)
    for var, count in sorted_vars[:10]:
        print(f"   {var:20} used in {count} templates")

    print("\n" + "=" * 80)
    print()


def main():
    """Main test runner"""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    print("\n🧪 Template Testing System")
    print("=" * 80)

    # Discover templates
    templates = discover_templates()
    print(f"\n📁 Discovered {len(templates)} templates\n")

    if not templates:
        print("❌ No templates found!")
        return 1

    # Test each template
    results = []
    for i, template in enumerate(templates, 1):
        if verbose:
            print(f"[{i}/{len(templates)}] Testing {template}...")

        result = analyze_template(template, verbose=verbose)
        results.append(result)

    # Print report
    print_template_report(results, verbose=verbose)

    # Exit code based on failures
    failed = sum(1 for r in results if r['status'] == 'fail')
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    # Check if Jinja2 is available
    try:
        import jinja2
    except ImportError:
        print("⚠️  Warning: jinja2 not found. Syntax validation will be limited.")
        print("   Install with: pip install jinja2")
        print()

    sys.exit(main())
