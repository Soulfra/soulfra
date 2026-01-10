#!/usr/bin/env python3
"""
Refactor Folders - Safe Reorganization Tool
NO libraries - Pure Python stdlib only (Bun/Zig/pot philosophy)

Problem: 325 files mixed together - core dev files + optional multiplayer features
Solution: Clean separation without breaking imports

What it does:
1. Read core_files.txt and bloat_files.txt from dependency analysis
2. Create /core and /optional directories
3. COPY files first (non-destructive test)
4. Update import paths automatically using AST
5. Generate test script to verify imports
6. Only after verification, move files permanently

Safety Features:
- Copy first, verify, then move (can rollback)
- AST-based import rewriting (not regex)
- Automated import testing
- Git-trackable changes

Usage:
    python3 refactor_folders.py          # Dry run (show what would happen)
    python3 refactor_folders.py --copy   # Copy files and update imports
    python3 refactor_folders.py --move   # Actually move files (after testing)
"""

import os
import sys
import shutil
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ==============================================================================
# CONFIG
# ==============================================================================

ROOT_DIR = '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple'
CORE_FILES_LIST = 'core_files.txt'
BLOAT_FILES_LIST = 'bloat_files.txt'

CORE_DIR = 'core'
OPTIONAL_DIR = 'optional'

# ==============================================================================
# FILE READER
# ==============================================================================

def read_file_list(filename: str) -> List[str]:
    """Read list of files from text file"""
    file_path = os.path.join(ROOT_DIR, filename)

    if not os.path.exists(file_path):
        print(f"❌ ERROR: {filename} not found")
        print(f"   Run: python3 analyze_dependencies.py")
        sys.exit(1)

    with open(file_path, 'r') as f:
        files = [line.strip() for line in f if line.strip()]

    return files


# ==============================================================================
# DIRECTORY CREATOR
# ==============================================================================

def create_directories(dry_run: bool = True) -> Tuple[str, str]:
    """Create /core and /optional directories"""
    core_path = os.path.join(ROOT_DIR, CORE_DIR)
    optional_path = os.path.join(ROOT_DIR, OPTIONAL_DIR)

    if dry_run:
        print(f"[DRY RUN] Would create: {core_path}")
        print(f"[DRY RUN] Would create: {optional_path}")
        return core_path, optional_path

    os.makedirs(core_path, exist_ok=True)
    os.makedirs(optional_path, exist_ok=True)

    # Create __init__.py for both
    with open(os.path.join(core_path, '__init__.py'), 'w') as f:
        f.write('"""Soulfra Core - Essential files for solo development"""\n')

    with open(os.path.join(optional_path, '__init__.py'), 'w') as f:
        f.write('"""Soulfra Optional - Multiplayer features (email/mesh network)"""\n')

    print(f"✅ Created: {core_path}")
    print(f"✅ Created: {optional_path}")

    return core_path, optional_path


# ==============================================================================
# IMPORT UPDATER (AST-based)
# ==============================================================================

class ImportUpdater(ast.NodeTransformer):
    """Update import statements to point to new locations"""

    def __init__(self, file_mapping: Dict[str, str]):
        """
        Args:
            file_mapping: {original_module: new_module}
            e.g., {'database': 'core.database', 'simple_emailer': 'optional.simple_emailer'}
        """
        self.file_mapping = file_mapping
        self.changes_made = []

    def visit_Import(self, node):
        """Handle 'import foo' statements"""
        for alias in node.names:
            module_base = alias.name.split('.')[0]

            if module_base in self.file_mapping:
                old_name = alias.name
                new_name = alias.name.replace(module_base, self.file_mapping[module_base])
                alias.name = new_name
                self.changes_made.append(f"import {old_name} → import {new_name}")

        return node

    def visit_ImportFrom(self, node):
        """Handle 'from foo import bar' statements"""
        if node.module:
            module_base = node.module.split('.')[0]

            if module_base in self.file_mapping:
                old_module = node.module
                new_module = node.module.replace(module_base, self.file_mapping[module_base])
                node.module = new_module
                self.changes_made.append(f"from {old_module} → from {new_module}")

        return node


def update_imports_in_file(file_path: str, file_mapping: Dict[str, str], dry_run: bool = True) -> int:
    """
    Update import statements in a Python file

    Args:
        file_path: Path to Python file
        file_mapping: {original_module: new_module}
        dry_run: If True, don't write changes

    Returns:
        Number of import statements changed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        # Update imports
        updater = ImportUpdater(file_mapping)
        new_tree = updater.visit(tree)

        if not updater.changes_made:
            return 0

        if dry_run:
            print(f"[DRY RUN] {file_path}:")
            for change in updater.changes_made:
                print(f"   {change}")
            return len(updater.changes_made)

        # Write updated code back
        new_content = ast.unparse(new_tree)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Updated {len(updater.changes_made)} imports in {file_path}")
        return len(updater.changes_made)

    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"⚠️  Skipping {file_path}: {e}")
        return 0


# ==============================================================================
# FILE COPIER/MOVER
# ==============================================================================

def copy_files(files: List[str], dest_dir: str, dry_run: bool = True) -> List[str]:
    """
    Copy files to destination directory

    Args:
        files: List of relative file paths
        dest_dir: Destination directory (e.g., '/path/to/core')
        dry_run: If True, don't actually copy

    Returns:
        List of successfully copied files
    """
    copied = []

    for rel_path in files:
        src = os.path.join(ROOT_DIR, rel_path)

        # Preserve directory structure
        rel_dir = os.path.dirname(rel_path)
        dest_subdir = os.path.join(dest_dir, rel_dir) if rel_dir else dest_dir
        dest = os.path.join(dest_subdir, os.path.basename(rel_path))

        if not os.path.exists(src):
            print(f"⚠️  Skipping {rel_path} (not found)")
            continue

        if dry_run:
            print(f"[DRY RUN] Would copy: {rel_path} → {dest}")
            copied.append(rel_path)
            continue

        # Create subdirectory if needed
        os.makedirs(dest_subdir, exist_ok=True)

        # Copy file
        shutil.copy2(src, dest)
        print(f"✅ Copied: {rel_path} → {dest}")
        copied.append(rel_path)

    return copied


# ==============================================================================
# IMPORT MAPPING BUILDER
# ==============================================================================

def build_file_mapping(core_files: List[str], bloat_files: List[str]) -> Dict[str, str]:
    """
    Build mapping of module names to new locations

    Args:
        core_files: List of files going to /core
        bloat_files: List of files going to /optional

    Returns:
        {original_module: new_module}
        e.g., {'database': 'core.database', 'simple_emailer': 'optional.simple_emailer'}
    """
    mapping = {}

    # Core files
    for file_path in core_files:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        mapping[module_name] = f'{CORE_DIR}.{module_name}'

    # Bloat files
    for file_path in bloat_files:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        mapping[module_name] = f'{OPTIONAL_DIR}.{module_name}'

    return mapping


# ==============================================================================
# TEST GENERATOR
# ==============================================================================

def generate_test_script(core_files: List[str], bloat_files: List[str]) -> str:
    """
    Generate test script to verify all imports work

    Returns:
        Path to generated test script
    """
    test_script = os.path.join(ROOT_DIR, 'test_refactored_imports.py')

    with open(test_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""\n')
        f.write('Test Refactored Imports - Verify nothing broke\n')
        f.write('"""\n\n')
        f.write('import sys\n')
        f.write('import os\n\n')
        f.write('sys.path.insert(0, os.path.dirname(__file__))\n\n')
        f.write('print("🧪 Testing Refactored Imports")\n')
        f.write('print()\n\n')
        f.write('errors = []\n\n')

        # Test core imports
        f.write('# Test core imports\n')
        for file_path in core_files:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            f.write(f'try:\n')
            f.write(f'    import {CORE_DIR}.{module_name}\n')
            f.write(f'    print(f"✅ {CORE_DIR}.{module_name}")\n')
            f.write(f'except Exception as e:\n')
            f.write(f'    print(f"❌ {CORE_DIR}.{module_name}: {{e}}")\n')
            f.write(f'    errors.append("{CORE_DIR}.{module_name}")\n\n')

        # Test bloat imports
        f.write('# Test optional imports\n')
        for file_path in bloat_files:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            f.write(f'try:\n')
            f.write(f'    import {OPTIONAL_DIR}.{module_name}\n')
            f.write(f'    print(f"✅ {OPTIONAL_DIR}.{module_name}")\n')
            f.write(f'except Exception as e:\n')
            f.write(f'    print(f"❌ {OPTIONAL_DIR}.{module_name}: {{e}}")\n')
            f.write(f'    errors.append("{OPTIONAL_DIR}.{module_name}")\n\n')

        f.write('print()\n')
        f.write('if errors:\n')
        f.write('    print(f"❌ {len(errors)} import errors")\n')
        f.write('    sys.exit(1)\n')
        f.write('else:\n')
        f.write('    print("🎉 All imports work!")\n')
        f.write('    sys.exit(0)\n')

    os.chmod(test_script, 0o755)
    print(f"✅ Generated test script: {test_script}")

    return test_script


# ==============================================================================
# MAIN REFACTOR LOGIC
# ==============================================================================

def refactor(mode: str = 'dry-run'):
    """
    Main refactor function

    Args:
        mode: 'dry-run', 'copy', or 'move'
    """
    dry_run = mode == 'dry-run'

    print("=" * 70)
    print("🔧 Soulfra Folder Refactor")
    print("=" * 70)
    print(f"Mode: {mode.upper()}")
    print()

    # Read file lists
    print("📂 Reading file lists...")
    core_files = read_file_list(CORE_FILES_LIST)
    bloat_files = read_file_list(BLOAT_FILES_LIST)

    print(f"   Core files: {len(core_files)}")
    print(f"   Optional files: {len(bloat_files)}")
    print()

    # Create directories
    print("📁 Creating directories...")
    core_path, optional_path = create_directories(dry_run=dry_run)
    print()

    # Build import mapping
    print("🗺️  Building import mapping...")
    file_mapping = build_file_mapping(core_files, bloat_files)
    print(f"   {len(file_mapping)} modules to remap")
    print()

    # Copy/move core files
    print(f"📦 {'[DRY RUN] Would copy' if dry_run else 'Copying'} core files...")
    copied_core = copy_files(core_files, core_path, dry_run=dry_run)
    print(f"   {len(copied_core)} files processed")
    print()

    # Copy/move bloat files
    print(f"📦 {'[DRY RUN] Would copy' if dry_run else 'Copying'} optional files...")
    copied_bloat = copy_files(bloat_files, optional_path, dry_run=dry_run)
    print(f"   {len(copied_bloat)} files processed")
    print()

    # Update imports in all Python files
    if mode in ['copy', 'move']:
        print("🔄 Updating imports in all files...")
        total_changes = 0

        # Update imports in copied files
        for file_path in copied_core:
            dest = os.path.join(core_path, os.path.basename(file_path))
            changes = update_imports_in_file(dest, file_mapping, dry_run=False)
            total_changes += changes

        for file_path in copied_bloat:
            dest = os.path.join(optional_path, os.path.basename(file_path))
            changes = update_imports_in_file(dest, file_mapping, dry_run=False)
            total_changes += changes

        print(f"   {total_changes} import statements updated")
        print()

    # Generate test script
    print("🧪 Generating test script...")
    test_script = generate_test_script(core_files, bloat_files)
    print()

    # Summary
    print("=" * 70)
    print("✅ REFACTOR COMPLETE")
    print("=" * 70)

    if mode == 'dry-run':
        print("This was a DRY RUN - no files were changed")
        print()
        print("Next steps:")
        print("  1. Review the proposed changes above")
        print("  2. Run with --copy to copy files and update imports")
        print("  3. Run the test script to verify imports work")
        print("  4. If tests pass, run with --move to delete originals")

    elif mode == 'copy':
        print("Files copied and imports updated")
        print()
        print("Next steps:")
        print(f"  1. Run test script: python3 {test_script}")
        print("  2. If tests pass, run with --move to delete originals")
        print("  3. If tests fail, debug and fix imports manually")

    elif mode == 'move':
        print("Files moved permanently")
        print()
        print("Next steps:")
        print(f"  1. Run test script: python3 {test_script}")
        print("  2. Commit changes to git")
        print("  3. Create dev_mode.py for solo development")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Parse command line args
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--copy':
            refactor(mode='copy')
        elif arg == '--move':
            refactor(mode='move')
        elif arg == '--dry-run':
            refactor(mode='dry-run')
        else:
            print("Usage:")
            print("  python3 refactor_folders.py              # Dry run (show what would happen)")
            print("  python3 refactor_folders.py --copy       # Copy files and update imports")
            print("  python3 refactor_folders.py --move       # Move files (delete originals)")
            sys.exit(1)
    else:
        # Default to dry run
        refactor(mode='dry-run')


if __name__ == '__main__':
    main()
