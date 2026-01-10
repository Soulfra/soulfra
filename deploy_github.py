#!/usr/bin/env python3
"""
GitHub Pages Deployer - Push Static Sites to GitHub

Automates deployment of exported static sites to GitHub Pages.

Usage:
    python3 deploy_github.py --brand howtocookathome
    python3 deploy_github.py --all

Requirements:
    - GitHub CLI (gh) installed: brew install gh
    - gh authenticated: gh auth login

This script will:
    1. Export the brand to static HTML (via export_static.py)
    2. Create a GitHub repo (if doesn't exist)
    3. Initialize git in output directory
    4. Commit and push to GitHub
    5. Enable GitHub Pages
    6. Show deployment URL
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run shell command and return output"""
    print(f"   🔧 {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    if result.returncode != 0 and check:
        print(f"   ❌ Error: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result.stdout.strip()


def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")

    # Check gh CLI
    try:
        version = run_command("gh --version", check=False)
        if "gh version" not in version:
            print("   ❌ GitHub CLI (gh) not found")
            print("   Install: brew install gh")
            return False
        print(f"   ✅ {version.split()[0]} {version.split()[2]}")
    except:
        print("   ❌ GitHub CLI (gh) not found")
        print("   Install: brew install gh")
        return False

    # Check gh auth
    try:
        auth_status = run_command("gh auth status", check=False)
        if "Logged in" not in auth_status:
            print("   ❌ GitHub CLI not authenticated")
            print("   Run: gh auth login")
            return False
        print("   ✅ GitHub CLI authenticated")
    except:
        print("   ❌ GitHub CLI not authenticated")
        print("   Run: gh auth login")
        return False

    return True


def load_brand_domains():
    """Load brand domain configuration"""
    config_path = Path(__file__).parent / 'brand_domains.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def create_cname_file(site_dir, brand_slug):
    """
    Create CNAME file for custom domain

    Args:
        site_dir: Path to site directory
        brand_slug: Brand slug (e.g., 'soulfra')
    """
    domains = load_brand_domains()

    if brand_slug in domains and 'domain' in domains[brand_slug]:
        domain = domains[brand_slug]['domain']
        cname_file = site_dir / 'CNAME'
        cname_file.write_text(domain)
        print(f"   ✅ Created CNAME file: {domain}")
        return domain
    else:
        print(f"   ℹ️  No custom domain configured for {brand_slug}")
        print(f"   💡 Add to brand_domains.json to enable custom domain")
        return None


def export_brand(brand_slug):
    """Export brand to static HTML"""
    print(f"\n📦 Exporting {brand_slug}...")
    try:
        run_command(f"python3 export_static.py --brand {brand_slug}")
        return True
    except Exception as e:
        print(f"   ❌ Export failed: {e}")
        return False


def deploy_to_github(brand_slug, output_dir='output'):
    """
    Deploy a brand to GitHub Pages

    Args:
        brand_slug: Brand slug (e.g., 'howtocookathome')
        output_dir: Base output directory

    Returns:
        GitHub Pages URL or None
    """
    site_dir = Path(output_dir) / brand_slug

    if not site_dir.exists():
        print(f"   ❌ Site directory not found: {site_dir}")
        print(f"   Run: python3 export_static.py --brand {brand_slug}")
        return None

    print(f"\n🚀 Deploying {brand_slug} to GitHub Pages...")

    # Create CNAME file for custom domain
    custom_domain = create_cname_file(site_dir, brand_slug)

    # Get GitHub username
    try:
        gh_user = run_command("gh api user -q .login")
        print(f"   📝 GitHub username: {gh_user}")
    except Exception as e:
        print(f"   ❌ Failed to get GitHub username: {e}")
        return None

    repo_name = brand_slug

    # Check if repo exists
    print(f"\n📋 Checking if repo exists...")
    repo_exists = False
    try:
        run_command(f"gh repo view {gh_user}/{repo_name}", check=False)
        repo_exists = True
        print(f"   ✅ Repo exists: {gh_user}/{repo_name}")
    except:
        print(f"   ℹ️  Repo does not exist yet")

    # Initialize git in site directory
    git_dir = site_dir / '.git'
    if not git_dir.exists():
        print(f"\n📝 Initializing git...")
        run_command("git init", cwd=site_dir)
        run_command("git branch -M main", cwd=site_dir)

    # Add all files
    print(f"\n📝 Adding files to git...")
    run_command("git add .", cwd=site_dir)

    # Check if there are changes to commit
    status = run_command("git status --porcelain", cwd=site_dir, check=False)
    if status:
        print(f"\n📝 Committing changes...")
        run_command('git commit -m "Update site content"', cwd=site_dir)
    else:
        print(f"   ℹ️  No changes to commit")

    # Create repo if doesn't exist
    if not repo_exists:
        print(f"\n📝 Creating GitHub repo...")
        run_command(
            f'gh repo create {repo_name} --public --source=. --description "Static site for {brand_slug}" --disable-issues --disable-wiki',
            cwd=site_dir
        )

    # Add remote if not exists
    try:
        run_command("git remote get-url origin", cwd=site_dir, check=False)
    except:
        print(f"\n📝 Adding remote...")
        run_command(f"git remote add origin https://github.com/{gh_user}/{repo_name}.git", cwd=site_dir)

    # Push to GitHub
    print(f"\n📤 Pushing to GitHub...")
    try:
        run_command("git push -u origin main", cwd=site_dir, check=False)
    except:
        # If push fails, try force push (for updates)
        print(f"   ℹ️  Regular push failed, trying force push...")
        run_command("git push -u origin main --force", cwd=site_dir)

    # Enable GitHub Pages
    print(f"\n🌐 Enabling GitHub Pages...")
    try:
        run_command(
            f"gh api repos/{gh_user}/{repo_name}/pages -X POST -f source[branch]=main -f source[path]=/",
            check=False
        )
        print(f"   ✅ GitHub Pages enabled")
    except:
        print(f"   ℹ️  GitHub Pages might already be enabled")

    # Get GitHub Pages URL
    pages_url = f"https://{gh_user}.github.io/{repo_name}"

    print(f"\n" + "=" * 70)
    print(f"✅ Deployment complete!")
    print(f"=" * 70)
    print(f"🌐 GitHub Pages URL: {pages_url}")
    print(f"📦 Repo URL: https://github.com/{gh_user}/{repo_name}")

    if custom_domain:
        print(f"🎯 Custom Domain: {custom_domain}")
        print(f"")
        print(f"Next steps:")
        print(f"  1. Wait 1-2 minutes for GitHub Pages to build")
        print(f"  2. Visit: {pages_url} (should work immediately)")
        print(f"  3. Configure DNS for {custom_domain}:")
        print(f"     ")
        print(f"     Option A (Recommended): CNAME Record")
        print(f"     ----------------------------------------")
        print(f"     Type:  CNAME")
        print(f"     Name:  @")
        print(f"     Value: {gh_user}.github.io")
        print(f"     ")
        print(f"     Option B (Root Domain): A Records")
        print(f"     ----------------------------------------")
        print(f"     Type:  A")
        print(f"     Name:  @")
        print(f"     Value: 185.199.108.153")
        print(f"            185.199.109.153")
        print(f"            185.199.110.153")
        print(f"            185.199.111.153")
        print(f"     ")
        print(f"  4. Wait 5-60 minutes for DNS propagation")
        print(f"  5. Visit: https://{custom_domain}")
        print(f"  6. Enable HTTPS in repo settings (auto-provisions SSL)")
    else:
        print(f"")
        print(f"Next steps:")
        print(f"  1. Wait 1-2 minutes for GitHub Pages to build")
        print(f"  2. Visit: {pages_url}")
        print(f"  3. To add custom domain, edit brand_domains.json")
    print(f"")

    return pages_url


def deploy_all_brands(output_dir='output'):
    """Deploy all brands in output directory"""
    print("=" * 70)
    print("🚀 DEPLOYING ALL SITES TO GITHUB PAGES")
    print("=" * 70)
    print()

    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"❌ Output directory not found: {output_dir}")
        print(f"Run: python3 export_static.py")
        return 0

    # Get all brand directories
    brands = [d.name for d in output_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not brands:
        print(f"❌ No brands found in {output_dir}")
        return 0

    print(f"📋 Found {len(brands)} brand(s): {', '.join(brands)}")
    print()

    deployed = 0
    for brand_slug in brands:
        try:
            url = deploy_to_github(brand_slug, output_dir)
            if url:
                deployed += 1
        except Exception as e:
            print(f"   ❌ Deployment failed: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"✅ Deployed {deployed}/{len(brands)} site(s)")
    print("=" * 70)

    return deployed


def main():
    """CLI for GitHub Pages deployer"""

    if '--help' in sys.argv:
        print(__doc__)
        return

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    specific_brand = None
    deploy_all = '--all' in sys.argv

    # Check for --brand flag
    if '--brand' in sys.argv:
        idx = sys.argv.index('--brand')
        if idx + 1 < len(sys.argv):
            specific_brand = sys.argv[idx + 1]
        else:
            print("Error: --brand requires a brand slug")
            return

    if specific_brand:
        # Export first
        if not export_brand(specific_brand):
            sys.exit(1)

        # Deploy
        url = deploy_to_github(specific_brand)
        if not url:
            sys.exit(1)

    elif deploy_all:
        deploy_all_brands()

    else:
        print(__doc__)
        print("\nError: Must specify --brand <slug> or --all")
        sys.exit(1)


if __name__ == '__main__':
    main()
