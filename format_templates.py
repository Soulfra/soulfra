#!/usr/bin/env python3
"""
Template Formatter - Replace Template Variables

Replaces all `${VARIABLE}` and `example.com` placeholders with actual values.

**Usage:**

```bash
# Replace with production values
python3 format_templates.py \
  --base-domain soulfra.com \
  --github-repo Soulfra/voice-archive \
  --environment production

# Replace with localhost values (development)
python3 format_templates.py --environment development

# Dry run (show what would be replaced)
python3 format_templates.py --dry-run
```

**What it does:**

1. Loads template variables from `config.template.py`
2. Replaces `${VAR}` with actual values in all files
3. Replaces `example.com` with actual domain
4. Updates `.env` file with secrets
5. Git commits changes (optional)

**Files processed:**
- `*.py` (Python files)
- `*.md` (Documentation)
- `*.html` (Templates)
- `*.yml` (GitHub Actions)
- `.env.example` → `.env`
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from config.template import TEMPLATE_VARS, DEFAULT_VALUES, PRODUCTION_EXAMPLE


# ==============================================================================
# FILE PROCESSING
# ==============================================================================

def find_template_files(root_dir: Path = Path('.')) -> List[Path]:
    """
    Find all files that may contain template variables

    Returns:
        List of file paths
    """
    patterns = [
        '**/*.py',
        '**/*.md',
        '**/*.html',
        '**/*.yml',
        '**/*.yaml',
        '**/*.js',
        '**/*.json',
        '.env.example',
    ]

    # Exclude these directories
    exclude_dirs = {
        '.git',
        '__pycache__',
        'node_modules',
        'venv',
        'voice-archive',  # Don't modify published archive
        'temp',
        'archive',  # Don't modify archived code
    }

    files = []

    for pattern in patterns:
        for file_path in root_dir.glob(pattern):
            # Check if any parent is excluded
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            if file_path.is_file():
                files.append(file_path)

    return files


def replace_variables_in_file(
    file_path: Path,
    replacements: Dict[str, str],
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Replace template variables in a file

    Args:
        file_path: Path to file
        replacements: Dict of {variable: value}
        dry_run: If True, don't write changes

    Returns:
        (num_replacements, list_of_changes)
    """
    try:
        content = file_path.read_text()
        original_content = content
        changes = []
        num_replacements = 0

        # Replace ${VARIABLE} patterns
        for var, value in replacements.items():
            pattern = re.escape(f'${{{var}}}')
            matches = re.findall(pattern, content)

            if matches:
                content = re.sub(pattern, value, content)
                num_replacements += len(matches)
                changes.append(f"  ${{{var}}} → {value} ({len(matches)} times)")

        # Replace example.com with actual domain
        if 'BASE_DOMAIN' in replacements and 'example.com' in content:
            domain = replacements['BASE_DOMAIN']
            example_matches = content.count('example.com')

            if example_matches > 0:
                content = content.replace('example.com', domain)
                num_replacements += example_matches
                changes.append(f"  example.com → {domain} ({example_matches} times)")

        # Write changes if not dry run
        if not dry_run and content != original_content:
            file_path.write_text(content)

        return num_replacements, changes

    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return 0, []


# ==============================================================================
# ENV FILE HANDLING
# ==============================================================================

def create_env_file(replacements: Dict[str, str], dry_run: bool = False) -> bool:
    """
    Create .env file from .env.example with actual values

    Args:
        replacements: Dict of variable values
        dry_run: If True, don't write .env

    Returns:
        True if created, False otherwise
    """
    env_example = Path('.env.example')
    env_file = Path('.env')

    if not env_example.exists():
        print("⚠️  .env.example not found")
        return False

    if env_file.exists():
        print("⚠️  .env already exists - skipping (delete manually to recreate)")
        return False

    try:
        content = env_example.read_text()

        # Replace template variables
        for var, value in replacements.items():
            pattern = re.escape(f'${{{var}}}')
            content = re.sub(pattern, value, content)

        if not dry_run:
            env_file.write_text(content)
            print(f"✅ Created .env with {len(replacements)} variables")
        else:
            print(f"[DRY RUN] Would create .env with {len(replacements)} variables")

        return True

    except Exception as e:
        print(f"❌ Error creating .env: {e}")
        return False


# ==============================================================================
# MAIN FORMATTER
# ==============================================================================

def format_templates(
    environment: str = 'development',
    base_domain: str = None,
    github_repo: str = None,
    dry_run: bool = False,
    verbose: bool = False
) -> Dict:
    """
    Format all template files with variable replacements

    Args:
        environment: 'development' or 'production'
        base_domain: Override base domain
        github_repo: Override GitHub repo
        dry_run: Don't write changes
        verbose: Show all replacements

    Returns:
        {
            'files_processed': int,
            'total_replacements': int,
            'files_changed': List[Path]
        }
    """
    print(f"\n{'='*60}")
    print(f"  TEMPLATE FORMATTER - {environment.upper()} MODE")
    print(f"{'='*60}\n")

    # Load replacement values
    if environment == 'production':
        replacements = PRODUCTION_EXAMPLE.copy()
    else:
        replacements = DEFAULT_VALUES.copy()

    # Override with command line args
    if base_domain:
        replacements['BASE_DOMAIN'] = base_domain
        replacements['API_DOMAIN'] = f'api.{base_domain}'
        replacements['AUTH_DOMAIN'] = f'auth.{base_domain}'
        replacements['AI_DOMAIN'] = f'ai.{base_domain}'

    if github_repo:
        replacements['GITHUB_REPO'] = github_repo
        username = github_repo.split('/')[0]
        replacements['GITHUB_USERNAME'] = username

    # Find all template files
    files = find_template_files()
    print(f"📁 Found {len(files)} files to process\n")

    # Process each file
    total_replacements = 0
    files_changed = []

    for file_path in files:
        num_replacements, changes = replace_variables_in_file(
            file_path,
            replacements,
            dry_run=dry_run
        )

        if num_replacements > 0:
            total_replacements += num_replacements
            files_changed.append(file_path)

            if dry_run:
                print(f"[DRY RUN] {file_path} - {num_replacements} replacements")
            else:
                print(f"✅ {file_path} - {num_replacements} replacements")

            if verbose and changes:
                for change in changes:
                    print(change)

    # Create .env file
    create_env_file(replacements, dry_run=dry_run)

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}\n")
    print(f"Files processed:      {len(files)}")
    print(f"Files changed:        {len(files_changed)}")
    print(f"Total replacements:   {total_replacements}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - No files were modified")
    else:
        print(f"\n✅ Template formatting complete!")

    return {
        'files_processed': len(files),
        'total_replacements': total_replacements,
        'files_changed': files_changed
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Format template files with variable replacements'
    )

    parser.add_argument(
        '--environment',
        choices=['development', 'production', 'localhost'],
        default='development',
        help='Deployment environment'
    )

    parser.add_argument(
        '--base-domain',
        type=str,
        help='Override base domain (e.g., soulfra.com)'
    )

    parser.add_argument(
        '--github-repo',
        type=str,
        help='Override GitHub repo (e.g., Soulfra/voice-archive)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be replaced without writing'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show all replacement details'
    )

    args = parser.parse_args()

    format_templates(
        environment=args.environment,
        base_domain=args.base_domain,
        github_repo=args.github_repo,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
