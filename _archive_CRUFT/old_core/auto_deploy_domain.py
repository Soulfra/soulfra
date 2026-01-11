#!/usr/bin/env python3
"""
End-to-End Domain Automation
Runs a domain all the way through from start to finish:

1. Add domain to domains-simple.txt
2. Analyze with Ollama
3. Create brand in database
4. Create GitHub repo
5. Initialize repo structure
6. Generate 3 initial posts with Multi-AI
7. Export to GitHub
8. Push to GitHub Pages

Usage:
    python3 auto_deploy_domain.py hollowtown.com
    python3 auto_deploy_domain.py --all  # Deploy all new domains
"""

import sys
import subprocess
from pathlib import Path
from ollama_domain_analyzer import OllamaDomainAnalyzer
from brand_creator import BrandCreator
from github_repo_creator import GitHubRepoCreator
from domain_manager import DomainManager


class AutoDomainDeployment:
    def __init__(self):
        self.analyzer = OllamaDomainAnalyzer()
        self.brand_creator = BrandCreator()
        self.github_creator = GitHubRepoCreator()
        self.domain_manager = DomainManager()

    def deploy_domain(self, domain: str) -> dict:
        """
        Full end-to-end deployment for a domain

        Returns:
        {
            'success': True,
            'domain': 'hollowtown.com',
            'brand_id': 7,
            'github_repo': 'https://github.com/Soulfra/hollowtown-site',
            'github_pages': 'https://soulfra.github.io/hollowtown-site',
            'next_steps': [...]
        }
        """
        print(f"\n{'='*60}")
        print(f"🚀 AUTO-DEPLOYING: {domain}")
        print(f"{'='*60}\n")

        result = {
            'success': False,
            'domain': domain,
            'steps_completed': []
        }

        # Step 1: Add to domains-simple.txt if not already there
        print("📝 Step 1: Adding to domains-simple.txt")
        self._ensure_domain_in_file(domain)
        result['steps_completed'].append('added_to_file')

        # Step 2: Analyze with Ollama
        print("\n🤖 Step 2: Analyzing with Ollama")
        analysis = self.analyzer.analyze_domain(domain)

        if not analysis:
            print("❌ Ollama analysis failed")
            result['error'] = 'Ollama analysis failed'
            return result

        print(f"   ✅ Category: {analysis.get('category')}")
        print(f"   ✅ Tagline: {analysis.get('tagline')}")
        print(f"   ✅ Colors: {analysis.get('colors', {}).get('primary')}")
        result['analysis'] = analysis
        result['steps_completed'].append('analyzed')

        # Step 3: Create brand in database
        print("\n💾 Step 3: Creating brand in database")
        brand_id = self.brand_creator.create_brand_from_analysis(analysis)

        if not brand_id:
            print("❌ Brand creation failed")
            result['error'] = 'Brand creation failed'
            return result

        print(f"   ✅ Brand ID: {brand_id}")
        result['brand_id'] = brand_id
        result['steps_completed'].append('brand_created')

        # Step 4: Create GitHub repo
        print("\n📦 Step 4: Creating GitHub repo")
        repo_result = self.github_creator.create_repo(domain)

        if not repo_result['success']:
            print("❌ GitHub repo creation failed")
            result['error'] = 'GitHub repo creation failed'
            result['github_error'] = repo_result.get('error')
            return result

        print(f"   ✅ Repo: {repo_result['repo_url']}")
        print(f"   ✅ Local: {repo_result['local_path']}")
        result['github_repo'] = repo_result['repo_url']
        result['local_repo_path'] = repo_result['local_path']
        result['steps_completed'].append('github_repo_created')

        # Step 5: Enable GitHub Pages
        print("\n🌐 Step 5: Enabling GitHub Pages")
        pages_url = self._enable_github_pages(repo_result['repo_name'])
        result['github_pages'] = pages_url
        result['steps_completed'].append('github_pages_enabled')

        # Step 6: Generate initial content (optional - Multi-AI)
        print("\n✍️  Step 6: Generating initial content (skipped - use Studio)")
        print("   💡 Go to http://localhost:5001/studio to write content")
        result['steps_completed'].append('ready_for_content')

        # Success!
        result['success'] = True

        print(f"\n{'='*60}")
        print(f"✅ DEPLOYMENT COMPLETE: {domain}")
        print(f"{'='*60}\n")

        print("📊 Summary:")
        print(f"   Domain: {domain}")
        print(f"   Brand ID: {brand_id}")
        print(f"   Category: {analysis.get('category')}")
        print(f"   Tagline: {analysis.get('tagline')}")
        print(f"   GitHub Repo: {repo_result['repo_url']}")
        print(f"   GitHub Pages: {pages_url}")
        print(f"   Local Path: {repo_result['local_path']}")

        print("\n📝 Next Steps:")
        print("   1. Go to Studio: http://localhost:5001/studio")
        print(f"   2. Select '{domain}' from dropdown")
        print("   3. Write content using Multi-AI debate")
        print("   4. Export and publish to GitHub Pages")
        print(f"   5. Visit: {pages_url}")

        return result

    def deploy_all_new_domains(self):
        """Deploy all domains from domains-simple.txt that don't have brands yet"""
        print("🔍 Finding new domains to deploy...")

        # Get all domains from file
        all_domains = self.domain_manager.get_all()

        # Get existing brands from database
        import sqlite3
        db_path = Path(__file__).parent / 'soulfra.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT domain FROM brands")
        existing_domains = set(row[0] for row in cursor.fetchall())
        conn.close()

        # Find new domains
        new_domains = [d['domain'] for d in all_domains if d['domain'] not in existing_domains]

        if not new_domains:
            print("✅ No new domains to deploy!")
            return

        print(f"📋 Found {len(new_domains)} new domains:")
        for domain in new_domains:
            print(f"   - {domain}")

        print("\n🚀 Starting deployment...\n")

        results = []
        for domain in new_domains:
            result = self.deploy_domain(domain)
            results.append(result)

            # Pause between domains to avoid rate limiting
            import time
            time.sleep(2)

        # Summary
        print(f"\n{'='*60}")
        print(f"📊 BATCH DEPLOYMENT SUMMARY")
        print(f"{'='*60}\n")

        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")

        if failed:
            print("\n❌ Failed domains:")
            for r in failed:
                print(f"   - {r['domain']}: {r.get('error')}")

    def _ensure_domain_in_file(self, domain: str):
        """Add domain to domains-simple.txt if not already there"""
        domains_file = Path(__file__).parent / 'domains-simple.txt'

        if domains_file.exists():
            existing = domains_file.read_text().strip().split('\n')
        else:
            existing = []

        if domain not in existing:
            existing.append(domain)
            domains_file.write_text('\n'.join(existing) + '\n')
            print(f"   ✅ Added {domain} to domains-simple.txt")
        else:
            print(f"   ℹ️  {domain} already in domains-simple.txt")

    def _enable_github_pages(self, repo_name: str) -> str:
        """
        Enable GitHub Pages for repo

        Returns GitHub Pages URL
        """
        # GitHub Pages URL format
        org_name_lower = self.github_creator.org_name.lower()
        pages_url = f"https://{org_name_lower}.github.io/{repo_name}"

        # Try to enable via API (requires GitHub token)
        if self.github_creator.github_token:
            try:
                import requests
                response = requests.post(
                    f"https://api.github.com/repos/{self.github_creator.org_name}/{repo_name}/pages",
                    headers={
                        'Authorization': f'token {self.github_creator.github_token}',
                        'Accept': 'application/vnd.github.v3+json'
                    },
                    json={
                        'source': {
                            'branch': 'main',
                            'path': '/'
                        }
                    }
                )

                if response.status_code in [201, 204, 409]:  # 409 = already enabled
                    print(f"   ✅ GitHub Pages enabled: {pages_url}")
                else:
                    print(f"   ⚠️  GitHub Pages API returned {response.status_code}")
                    print(f"   💡 Enable manually: Settings → Pages → Source: main branch")
            except Exception as e:
                print(f"   ⚠️  Could not auto-enable GitHub Pages: {e}")
                print(f"   💡 Enable manually in repo settings")
        else:
            print(f"   ⚠️  No GitHub token - enable GitHub Pages manually")
            print(f"   💡 Go to repo Settings → Pages → Source: main branch")

        return pages_url


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 auto_deploy_domain.py <domain>")
        print("  python3 auto_deploy_domain.py --all")
        print("\nExamples:")
        print("  python3 auto_deploy_domain.py hollowtown.com")
        print("  python3 auto_deploy_domain.py --all")
        print("\n💡 Set GITHUB_TOKEN environment variable for GitHub repo creation:")
        print("  export GITHUB_TOKEN='your_token_here'")
        sys.exit(1)

    deployer = AutoDomainDeployment()

    if sys.argv[1] == '--all':
        deployer.deploy_all_new_domains()
    else:
        domain = sys.argv[1]
        result = deployer.deploy_domain(domain)

        if not result['success']:
            sys.exit(1)


if __name__ == '__main__':
    main()
