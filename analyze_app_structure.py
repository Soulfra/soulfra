#!/usr/bin/env python3
"""
App Structure Analyzer - Map the 18,843-line app.py beast
NO libraries - Pure Python stdlib (Bun/Zig/pot philosophy)

Problem: app.py is 18,843 lines and pulls from nested folders everywhere
Solution: Build complete dependency map showing what's ACTUALLY used

Output:
- FLAT_STRUCTURE.md - Human-readable map
- active_imports.json - Which Python files are imported
- active_templates.json - Which templates are rendered
- active_routes.json - All Flask routes
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# ==============================================================================
# CONFIG
# ==============================================================================

ROOT_DIR = '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple'
APP_FILE = 'app.py'

# ==============================================================================
# AST ANALYZER
# ==============================================================================

def analyze_app_py():
    """Parse app.py with AST to extract imports and routes"""

    app_path = os.path.join(ROOT_DIR, APP_FILE)

    with open(app_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    imports = []
    routes = []
    templates = []

    # Extract imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'as': alias.asname
                })

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append({
                    'type': 'from',
                    'module': module,
                    'name': alias.name,
                    'as': alias.asname
                })

    # Extract routes (regex - AST doesn't preserve decorators easily)
    route_pattern = r"@app\.route\('([^']+)'(?:,\s*methods=\[([^\]]+)\])?\)"
    for match in re.finditer(route_pattern, content):
        path = match.group(1)
        methods = match.group(2) if match.group(2) else 'GET'
        routes.append({
            'path': path,
            'methods': methods.replace("'", "").replace('"', '')
        })

    # Extract template renders
    template_pattern = r"render_template\('([^']+)'"
    for match in re.finditer(template_pattern, content):
        template = match.group(1)
        templates.append(template)

    return {
        'imports': imports,
        'routes': routes,
        'templates': list(set(templates))  # Unique templates
    }


# ==============================================================================
# FILE SYSTEM SCANNER
# ==============================================================================

def scan_templates():
    """Find all template files"""
    templates_dir = os.path.join(ROOT_DIR, 'templates')

    all_templates = []

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                all_templates.append(rel_path)

    return all_templates


def scan_python_files():
    """Find all Python files that could be imported"""
    python_files = []

    for file in os.listdir(ROOT_DIR):
        if file.endswith('.py') and file != APP_FILE:
            python_files.append(file[:-3])  # Remove .py

    return python_files


# ==============================================================================
# CROSS-REFERENCE
# ==============================================================================

def cross_reference(analysis, all_templates, all_python):
    """Cross-reference what's used vs what exists"""

    imported_modules = set()
    for imp in analysis['imports']:
        if imp['type'] == 'import':
            imported_modules.add(imp['module'])
        else:  # from X import Y
            imported_modules.add(imp['module'])

    used_templates = set(analysis['templates'])
    unused_templates = set(all_templates) - used_templates

    unused_python = set(all_python) - imported_modules

    return {
        'used_templates': sorted(used_templates),
        'unused_templates': sorted(unused_templates),
        'used_modules': sorted(imported_modules),
        'unused_python': sorted(unused_python)
    }


# ==============================================================================
# MARKDOWN GENERATOR
# ==============================================================================

def generate_flat_structure_md(analysis, cross_ref):
    """Generate FLAT_STRUCTURE.md"""

    md = []

    md.append("# Soulfra Flat Structure Map")
    md.append("")
    md.append("**Generated:** Auto-analyzed from 18,843-line app.py")
    md.append("")
    md.append("## Overview")
    md.append("")
    md.append(f"- **Total routes:** {len(analysis['routes'])}")
    md.append(f"- **Imported modules:** {len(cross_ref['used_modules'])}")
    md.append(f"- **Active templates:** {len(cross_ref['used_templates'])}")
    md.append(f"- **Unused templates:** {len(cross_ref['unused_templates'])}")
    md.append(f"- **Unused Python files:** {len(cross_ref['unused_python'])}")
    md.append("")

    md.append("---")
    md.append("")

    # Routes by category
    md.append("## Flask Routes (What app.py Actually Serves)")
    md.append("")

    # Group routes
    api_routes = [r for r in analysis['routes'] if r['path'].startswith('/api')]
    admin_routes = [r for r in analysis['routes'] if 'admin' in r['path'] or 'debug' in r['path']]
    user_routes = [r for r in analysis['routes'] if '/me' in r['path']]
    domain_routes = [r for r in analysis['routes'] if '/<' in r['path'] and 'domain' in r['path']]
    other_routes = [r for r in analysis['routes'] if r not in api_routes + admin_routes + user_routes + domain_routes]

    md.append(f"### API Routes ({len(api_routes)})")
    md.append("")
    for route in sorted(api_routes, key=lambda x: x['path'])[:20]:  # First 20
        md.append(f"- `{route['methods']}` `{route['path']}`")
    if len(api_routes) > 20:
        md.append(f"- ... and {len(api_routes) - 20} more")
    md.append("")

    md.append(f"### User/Profile Routes ({len(user_routes)})")
    md.append("")
    for route in sorted(user_routes, key=lambda x: x['path']):
        md.append(f"- `{route['methods']}` `{route['path']}`")
    md.append("")

    md.append(f"### Admin/Debug Routes ({len(admin_routes)})")
    md.append("")
    for route in sorted(admin_routes, key=lambda x: x['path']):
        md.append(f"- `{route['methods']}` `{route['path']}`")
    md.append("")

    # Templates
    md.append("---")
    md.append("")
    md.append("## Active Templates (Actually Rendered)")
    md.append("")

    template_groups = defaultdict(list)
    for tmpl in cross_ref['used_templates']:
        dir_name = os.path.dirname(tmpl) or 'root'
        template_groups[dir_name].append(tmpl)

    for dir_name in sorted(template_groups.keys()):
        md.append(f"### `{dir_name}/`")
        md.append("")
        for tmpl in sorted(template_groups[dir_name]):
            md.append(f"- {os.path.basename(tmpl)}")
        md.append("")

    # Unused templates
    md.append("---")
    md.append("")
    md.append(f"## Unused Templates ({len(cross_ref['unused_templates'])})")
    md.append("")
    md.append("These templates exist but are NEVER rendered by app.py:")
    md.append("")

    unused_groups = defaultdict(list)
    for tmpl in cross_ref['unused_templates']:
        dir_name = os.path.dirname(tmpl) or 'root'
        unused_groups[dir_name].append(tmpl)

    for dir_name in sorted(unused_groups.keys())[:10]:  # First 10 dirs
        md.append(f"### `{dir_name}/` - {len(unused_groups[dir_name])} files")
        md.append("")
        for tmpl in sorted(unused_groups[dir_name])[:5]:  # First 5 files
            md.append(f"- {os.path.basename(tmpl)}")
        if len(unused_groups[dir_name]) > 5:
            md.append(f"- ... and {len(unused_groups[dir_name]) - 5} more")
        md.append("")

    # Imported modules
    md.append("---")
    md.append("")
    md.append("## Imported Modules (ACTIVE)")
    md.append("")
    md.append("These Python files are imported by app.py:")
    md.append("")

    for mod in sorted(cross_ref['used_modules'])[:50]:  # First 50
        md.append(f"- `{mod}.py`")
    if len(cross_ref['used_modules']) > 50:
        md.append(f"- ... and {len(cross_ref['used_modules']) - 50} more")
    md.append("")

    # Unused Python files
    md.append("---")
    md.append("")
    md.append(f"## Unused Python Files ({len(cross_ref['unused_python'])})")
    md.append("")
    md.append("These .py files exist but are NEVER imported:")
    md.append("")

    for mod in sorted(cross_ref['unused_python'])[:30]:  # First 30
        md.append(f"- `{mod}.py`")
    if len(cross_ref['unused_python']) > 30:
        md.append(f"- ... and {len(cross_ref['unused_python']) - 30} more")
    md.append("")

    # Nested Soulfra confusion
    md.append("---")
    md.append("")
    md.append("## Nested Soulfra Folder (SEPARATE PROJECT)")
    md.append("")
    md.append("**Status:** NOT used by app.py (separate triple-domain system)")
    md.append("")
    md.append("```")
    md.append("Soulfra/")
    md.append("├── Soulfra.com/    (QR landing - port 8001)")
    md.append("├── Soulfra.ai/     (AI chat - port 5003)")
    md.append("└── Soulfraapi.com/ (API - port 5002)")
    md.append("```")
    md.append("")
    md.append("This is a SEPARATE mini-project with its own servers.")
    md.append("Main app.py runs on port 5001 - completely independent.")
    md.append("")

    # VR/3D
    md.append("---")
    md.append("")
    md.append("## VR/3D/Blender Features")
    md.append("")
    md.append("**Status:** DOES NOT EXIST YET")
    md.append("")
    md.append("No VR or 3D modeling code found.")
    md.append("Only 1 screenshot test in archive/experiments/.")
    md.append("")
    md.append("**Future idea:** Reverse-engineer VR spatial interfaces into flat 2D screens")
    md.append("")

    return '\n'.join(md)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 70)
    print("🔍 Analyzing 18,843-line app.py")
    print("=" * 70)
    print()

    # Analyze app.py
    print("📝 Parsing app.py with AST...")
    analysis = analyze_app_py()
    print(f"   Found {len(analysis['imports'])} imports")
    print(f"   Found {len(analysis['routes'])} routes")
    print(f"   Found {len(analysis['templates'])} unique templates")
    print()

    # Scan filesystem
    print("📂 Scanning filesystem...")
    all_templates = scan_templates()
    all_python = scan_python_files()
    print(f"   Found {len(all_templates)} total template files")
    print(f"   Found {len(all_python)} total Python files")
    print()

    # Cross-reference
    print("🔗 Cross-referencing...")
    cross_ref = cross_reference(analysis, all_templates, all_python)
    print(f"   Active templates: {len(cross_ref['used_templates'])}")
    print(f"   Unused templates: {len(cross_ref['unused_templates'])}")
    print(f"   Active modules: {len(cross_ref['used_modules'])}")
    print(f"   Unused Python files: {len(cross_ref['unused_python'])}")
    print()

    # Generate markdown
    print("📄 Generating FLAT_STRUCTURE.md...")
    md_content = generate_flat_structure_md(analysis, cross_ref)

    with open('FLAT_STRUCTURE.md', 'w') as f:
        f.write(md_content)

    print("   ✅ FLAT_STRUCTURE.md")
    print()

    # Save JSON data
    print("💾 Saving JSON data...")

    with open('active_imports.json', 'w') as f:
        json.dump(cross_ref['used_modules'], f, indent=2)
    print("   ✅ active_imports.json")

    with open('active_templates.json', 'w') as f:
        json.dump(cross_ref['used_templates'], f, indent=2)
    print("   ✅ active_templates.json")

    with open('active_routes.json', 'w') as f:
        json.dump(analysis['routes'], f, indent=2)
    print("   ✅ active_routes.json")

    with open('unused_templates.json', 'w') as f:
        json.dump(cross_ref['unused_templates'], f, indent=2)
    print("   ✅ unused_templates.json")

    with open('unused_python.json', 'w') as f:
        json.dump(cross_ref['unused_python'], f, indent=2)
    print("   ✅ unused_python.json")

    print()
    print("=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review FLAT_STRUCTURE.md")
    print("  2. Check unused_templates.json (candidates for archiving)")
    print("  3. Check unused_python.json (standalone scripts or dead code)")


if __name__ == '__main__':
    main()
