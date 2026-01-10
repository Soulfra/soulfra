#!/usr/bin/env python3
"""
Dependency Analyzer - Safe Refactoring Tool
NO libraries - Pure Python stdlib (Bun/Zig style)

Analyzes 325 Python files to understand what imports what
Outputs: Dependency graph, core files, bloat files

Usage:
    python3 analyze_dependencies.py

Output:
    - dependencies.json (what imports what)
    - core_files.txt (essential, keep in /core)
    - bloat_files.txt (email stuff, move to /optional)
"""

import os
import re
import ast
import json
from collections import defaultdict
from typing import Dict, List, Set

# ==============================================================================
# CONFIG
# ==============================================================================

ROOT_DIR = '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple'
IGNORE_DIRS = {'archive', '__pycache__', '.git', 'venv', 'node_modules'}

# Core technologies (keep these)
CORE_TECH = {
    'ollama', 'sqlite', 'database', 'flask', 'soulfra_types'
}

# Bloat technologies (move to /optional)
BLOAT_TECH = {
    'smtplib', 'imaplib', 'email.mime', 'mesh_network', 'blamechain'
}

# ==============================================================================
# AST PARSER - Find Imports
# ==============================================================================

def find_imports(file_path: str) -> Set[str]:
    """
    Parse Python file and extract all imports

    Returns:
        Set of module names imported
    """
    imports = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        for node in ast.walk(tree):
            # import foo
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])

            # from foo import bar
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        pass

    return imports


# ==============================================================================
# FILE SCANNER
# ==============================================================================

def scan_directory(root_dir: str) -> Dict[str, Set[str]]:
    """
    Scan all Python files and build dependency graph

    Returns:
        {file_path: set of imported modules}
    """
    dependencies = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(file_path, root_dir)

                imports = find_imports(file_path)
                dependencies[rel_path] = imports

    return dependencies


# ==============================================================================
# CATEGORIZER
# ==============================================================================

def categorize_files(dependencies: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Categorize files into core, bloat, and neutral

    Returns:
        {
            'core': [files using core tech],
            'bloat': [files using email/mesh network],
            'neutral': [files with no tech dependencies]
        }
    """
    categorized = {
        'core': [],
        'bloat': [],
        'neutral': []
    }

    for file_path, imports in dependencies.items():
        imports_str = ' '.join(imports).lower()

        # Check for bloat
        is_bloat = any(tech in imports_str for tech in BLOAT_TECH)
        if is_bloat:
            categorized['bloat'].append(file_path)
            continue

        # Check for core
        is_core = any(tech in imports_str for tech in CORE_TECH)
        if is_core:
            categorized['core'].append(file_path)
            continue

        # Neutral
        categorized['neutral'].append(file_path)

    return categorized


# ==============================================================================
# DEPENDENCY GRAPH BUILDER
# ==============================================================================

def build_graph(dependencies: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Build a reverse dependency graph

    Returns:
        {module: [files that import it]}
    """
    graph = defaultdict(list)

    for file_path, imports in dependencies.items():
        for imp in imports:
            graph[imp].append(file_path)

    return dict(graph)


# ==============================================================================
# ANALYZER
# ==============================================================================

def analyze():
    """Main analysis function"""
    print("🔍 Analyzing Dependencies")
    print(f"Root: {ROOT_DIR}")
    print()

    # Scan all files
    print("📂 Scanning Python files...")
    dependencies = scan_directory(ROOT_DIR)
    total_files = len(dependencies)
    print(f"   Found {total_files} Python files")
    print()

    # Categorize
    print("🏷️  Categorizing files...")
    categorized = categorize_files(dependencies)

    core_count = len(categorized['core'])
    bloat_count = len(categorized['bloat'])
    neutral_count = len(categorized['neutral'])

    print(f"   Core files (Ollama/SQLite): {core_count}")
    print(f"   Bloat files (Email/Mesh): {bloat_count}")
    print(f"   Neutral files: {neutral_count}")
    print()

    # Build graph
    print("📊 Building dependency graph...")
    graph = build_graph(dependencies)
    print(f"   {len(graph)} unique modules imported")
    print()

    # Top imports
    print("🔝 Top 10 Most Imported Modules:")
    sorted_modules = sorted(graph.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for module, files in sorted_modules:
        print(f"   {module}: {len(files)} files")
    print()

    # Save results
    print("💾 Saving results...")

    # dependencies.json
    with open('dependencies.json', 'w') as f:
        # Convert sets to lists for JSON
        deps_json = {k: list(v) for k, v in dependencies.items()}
        json.dump(deps_json, f, indent=2)
    print("   ✅ dependencies.json")

    # core_files.txt
    with open('core_files.txt', 'w') as f:
        f.write('\n'.join(sorted(categorized['core'])))
    print(f"   ✅ core_files.txt ({core_count} files)")

    # bloat_files.txt
    with open('bloat_files.txt', 'w') as f:
        f.write('\n'.join(sorted(categorized['bloat'])))
    print(f"   ✅ bloat_files.txt ({bloat_count} files)")

    # module_graph.json
    with open('module_graph.json', 'w') as f:
        json.dump(graph, f, indent=2)
    print("   ✅ module_graph.json")

    print()
    print("🎉 Analysis complete!")
    print()
    print("Next steps:")
    print("  1. Review core_files.txt - These are essential")
    print("  2. Review bloat_files.txt - Move these to /optional")
    print("  3. Run refactor_folders.py to reorganize safely")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    analyze()
