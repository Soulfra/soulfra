#!/usr/bin/env python3
"""
Deploy All - One-command deployment across the SOULFRA ecosystem

This script:
1. Builds waitlist (all languages)
2. Builds domain manager
3. Copies everything to soulfra.github.io repo
4. (Future) Pushes to multiple domain repos

Usage:
    python3 deploy_all.py                    # Dry run (build only)
    python3 deploy_all.py --push             # Build + push to GitHub
    python3 deploy_all.py --deploy-to calriven  # Deploy to specific domain
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# Paths
SOULFRA_SIMPLE_DIR = os.path.dirname(__file__)
SOULFRA_GITHUB_IO_DIR = '/Users/matthewmauer/Desktop/soulfra.github.io'

# Deployment targets
DEPLOYMENT_TARGETS = {
    'soulfra.github.io': {
        'local_path': SOULFRA_GITHUB_IO_DIR,
        'repo': 'github.com/Soulfra/soulfra.github.io',
        'enabled': True
    },
    'calriven': {
        'local_path': '/Users/matthewmauer/Desktop/calriven',
        'repo': 'github.com/Soulfra/calriven',
        'enabled': False  # Enable when you set up the repo
    },
    'deathtodata': {
        'local_path': '/Users/matthewmauer/Desktop/deathtodata-clean',
        'repo': 'github.com/Soulfra/deathtodata',
        'enabled': False
    },
    'cringeproof': {
        'local_path': '/Users/matthewmauer/Desktop/cringeproof-vertical',
        'repo': 'github.com/Soulfra/cringeproof',
        'enabled': False
    }
}


def run_command(cmd, cwd=None):
    """Run shell command and return output"""
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ❌ Error: {result.stderr}")
        return False

    if result.stdout:
        print(f"  {result.stdout.strip()}")

    return True


def build_waitlist():
    """Build static waitlist site (all languages)"""
    print("\n" + "="*60)
    print("📦 BUILDING WAITLIST")
    print("="*60)

    if not run_command('python3 build_waitlist.py', cwd=SOULFRA_SIMPLE_DIR):
        return False

    print("✅ Waitlist built successfully")
    return True


def build_domain_manager():
    """Build domain manager UI"""
    print("\n" + "="*60)
    print("🌐 BUILDING DOMAIN MANAGER")
    print("="*60)

    if not run_command('python3 build_domains_manager.py', cwd=SOULFRA_SIMPLE_DIR):
        return False

    print("✅ Domain manager built successfully")
    return True


def copy_to_github_io():
    """Copy built files to soulfra.github.io repo"""
    print("\n" + "="*60)
    print("📋 COPYING TO SOULFRA.GITHUB.IO")
    print("="*60)

    if not os.path.exists(SOULFRA_GITHUB_IO_DIR):
        print(f"❌ Error: {SOULFRA_GITHUB_IO_DIR} not found")
        return False

    # Create directories
    waitlist_dest = os.path.join(SOULFRA_GITHUB_IO_DIR, 'waitlist')
    domains_dest = os.path.join(SOULFRA_GITHUB_IO_DIR, 'domains')

    os.makedirs(waitlist_dest, exist_ok=True)
    os.makedirs(domains_dest, exist_ok=True)

    # Copy waitlist
    waitlist_src = os.path.join(SOULFRA_SIMPLE_DIR, 'output/waitlist')
    if os.path.exists(waitlist_src):
        shutil.copytree(waitlist_src, waitlist_dest, dirs_exist_ok=True)
        print(f"  ✓ Waitlist copied to {waitlist_dest}")
    else:
        print(f"  ⚠️  Warning: {waitlist_src} not found")

    # Copy domain manager
    domains_src = os.path.join(SOULFRA_SIMPLE_DIR, 'output/domains')
    if os.path.exists(domains_src):
        shutil.copytree(domains_src, domains_dest, dirs_exist_ok=True)
        print(f"  ✓ Domain manager copied to {domains_dest}")
    else:
        print(f"  ⚠️  Warning: {domains_src} not found")

    print("✅ Files copied successfully")
    return True


def push_to_github(target_name='soulfra.github.io'):
    """Push changes to GitHub"""
    print("\n" + "="*60)
    print(f"🚀 PUSHING TO {target_name.upper()}")
    print("="*60)

    target = DEPLOYMENT_TARGETS.get(target_name)
    if not target:
        print(f"❌ Unknown target: {target_name}")
        return False

    if not target['enabled']:
        print(f"⚠️  Target '{target_name}' is not enabled yet")
        return False

    local_path = target['local_path']

    if not os.path.exists(local_path):
        print(f"❌ Error: {local_path} not found")
        return False

    # Git status
    print("\n1. Checking git status...")
    run_command('git status', cwd=local_path)

    # Git add
    print("\n2. Adding changes...")
    if not run_command('git add waitlist/ domains/', cwd=local_path):
        return False

    # Git commit
    print("\n3. Committing changes...")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"🚀 Auto-deploy: {timestamp}\\n\\n✅ Waitlist updated\\n✅ Domain manager updated"

    # Check if there are changes to commit
    result = subprocess.run('git diff --staged --quiet', shell=True, cwd=local_path)
    if result.returncode == 0:
        print("  ℹ️  No changes to commit")
        return True

    if not run_command(f'git commit -m "{commit_msg}"', cwd=local_path):
        return False

    # Git push
    print("\n4. Pushing to GitHub...")
    if not run_command('git push', cwd=local_path):
        return False

    print(f"\n✅ Successfully pushed to {target['repo']}")
    return True


def show_deployment_summary():
    """Show what will be deployed"""
    print("\n" + "="*60)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*60)

    print("\nEnabled targets:")
    for name, target in DEPLOYMENT_TARGETS.items():
        status = "✅ Enabled" if target['enabled'] else "⏸️  Disabled"
        print(f"  {name:<20} {status}")
        print(f"    → {target['local_path']}")
        print(f"    → {target['repo']}\n")

    print("\nTo enable a target:")
    print("  1. Set up the GitHub repo")
    print("  2. Clone it locally")
    print("  3. Edit deploy_all.py and set 'enabled': True")


def main():
    """Main deployment flow"""
    # Parse args
    args = sys.argv[1:]
    should_push = '--push' in args
    deploy_to = None

    for arg in args:
        if arg.startswith('--deploy-to='):
            deploy_to = arg.split('=')[1]

    print("\n" + "="*60)
    print("🚀 SOULFRA DEPLOYMENT SYSTEM")
    print("="*60)
    print(f"Mode: {'BUILD + PUSH' if should_push else 'BUILD ONLY (DRY RUN)'}")
    if deploy_to:
        print(f"Target: {deploy_to}")
    print("="*60)

    # Step 1: Build waitlist
    if not build_waitlist():
        print("\n❌ Waitlist build failed. Aborting.")
        sys.exit(1)

    # Step 2: Build domain manager
    if not build_domain_manager():
        print("\n❌ Domain manager build failed. Aborting.")
        sys.exit(1)

    # Step 3: Copy to soulfra.github.io
    if not copy_to_github_io():
        print("\n❌ Copy to GitHub.io failed. Aborting.")
        sys.exit(1)

    # Step 4: Push to GitHub (if requested)
    if should_push:
        target = deploy_to if deploy_to else 'soulfra.github.io'

        if not push_to_github(target):
            print("\n❌ Push to GitHub failed.")
            sys.exit(1)
    else:
        print("\n" + "="*60)
        print("ℹ️  DRY RUN - No changes pushed to GitHub")
        print("="*60)
        print("\nTo push changes, run:")
        print("  python3 deploy_all.py --push")

    # Show deployment summary
    show_deployment_summary()

    print("\n" + "="*60)
    print("✅ DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"\n📍 Local preview:")
    print(f"  Waitlist: file://{os.path.join(SOULFRA_GITHUB_IO_DIR, 'waitlist/index.html')}")
    print(f"  Domains:  file://{os.path.join(SOULFRA_GITHUB_IO_DIR, 'domains/index.html')}")

    if should_push:
        print(f"\n🌐 Live URLs (after GitHub Pages builds):")
        print(f"  https://soulfra.github.io/waitlist/")
        print(f"  https://soulfra.github.io/domains/")

    print()


if __name__ == '__main__':
    main()
