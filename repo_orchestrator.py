#!/usr/bin/env python3
"""
Repo Orchestrator - Master Controller for Soulfra Network

The "genius CTO" tool that manages all 6 repos as one unified system.

What it does:
- Scans all repos on Desktop (soulfra-simple, soulfra.github.io, calriven, etc.)
- Shows git status across entire network
- Deploys to GitHub Pages (all domains) with one command
- Health checks (Flask running? Cloudflare tunnel up? Databases synced?)
- Cross-repo operations (voice memo → blog post → git push)

Usage:
    python3 repo_orchestrator.py --status
    python3 repo_orchestrator.py --deploy-all
    python3 repo_orchestrator.py --health-check
    python3 repo_orchestrator.py --sync-voice-memos
"""

import os
import subprocess
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import argparse
import sys

class RepoOrchestrator:
    """Master controller for the entire Soulfra Network"""

    def __init__(self, desktop_path=None):
        self.desktop = Path(desktop_path or Path.home() / 'Desktop')

        # Known repos
        self.repos = {
            'soulfra-simple': {
                'path': self.desktop / 'roommate-chat' / 'soulfra-simple',
                'type': 'backend',
                'domains': ['cringeproof.com (via voice-archive)'],
                'description': 'Flask backend + CringeProof voice memos'
            },
            'soulfra.github.io': {
                'path': self.desktop / 'soulfra.github.io',
                'type': 'frontend',
                'domains': ['soulfra.com', 'soulfra.github.io'],
                'description': 'Main platform with QR codes'
            },
            'calriven': {
                'path': self.desktop / 'calriven',
                'type': 'blog',
                'domains': ['calriven.com'],
                'description': 'Calriven debugging blog'
            },
            'cringeproof-vertical': {
                'path': self.desktop / 'cringeproof-vertical',
                'type': 'frontend',
                'domains': ['cringeproof.com (vertical layout)'],
                'description': 'CringeProof alternative UI'
            },
            'deathtodata-clean': {
                'path': self.desktop / 'deathtodata-clean',
                'type': 'frontend',
                'domains': ['deathtodata.com'],
                'description': 'Privacy-first tools'
            },
            'soulfra-profile': {
                'path': self.desktop / 'soulfra-profile',
                'type': 'frontend',
                'domains': ['profile.soulfra.com'],
                'description': 'Profile management'
            }
        }

        print("🚀 Repo Orchestrator - Master Controller")
        print(f"Desktop: {self.desktop}")
        print(f"Managing {len(self.repos)} repositories\n")

    def check_repo_exists(self, repo_name):
        """Check if repo exists"""
        repo_path = self.repos[repo_name]['path']
        return repo_path.exists() and (repo_path / '.git').exists()

    def get_git_status(self, repo_name):
        """Get git status for a repo"""
        repo = self.repos[repo_name]
        repo_path = repo['path']

        if not self.check_repo_exists(repo_name):
            return {'exists': False, 'error': 'Repository not found'}

        try:
            # Get current branch
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                text=True
            ).strip()

            # Get uncommitted changes
            status_output = subprocess.check_output(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                text=True
            )
            uncommitted = len([line for line in status_output.split('\n') if line.strip()])

            # Get unpushed commits
            try:
                unpushed_output = subprocess.check_output(
                    ['git', 'log', f'origin/{branch}..HEAD', '--oneline'],
                    cwd=repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                unpushed = len([line for line in unpushed_output.split('\n') if line.strip()])
            except:
                unpushed = 0

            # Get last commit
            try:
                last_commit = subprocess.check_output(
                    ['git', 'log', '-1', '--pretty=format:%h - %s (%ar)'],
                    cwd=repo_path,
                    text=True
                ).strip()
            except:
                last_commit = 'No commits'

            # Get remote URL
            try:
                remote_url = subprocess.check_output(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=repo_path,
                    text=True
                ).strip()
            except:
                remote_url = 'No remote'

            return {
                'exists': True,
                'branch': branch,
                'uncommitted_changes': uncommitted,
                'unpushed_commits': unpushed,
                'last_commit': last_commit,
                'remote_url': remote_url,
                'clean': uncommitted == 0 and unpushed == 0
            }

        except subprocess.CalledProcessError as e:
            return {'exists': True, 'error': str(e)}

    def show_network_status(self):
        """Show status of entire network"""
        print("=" * 80)
        print("SOULFRA NETWORK STATUS")
        print("=" * 80)
        print()

        for repo_name, repo_info in self.repos.items():
            print(f"📦 {repo_name}")
            print(f"   Type: {repo_info['type']}")
            print(f"   Domains: {', '.join(repo_info['domains'])}")
            print(f"   Path: {repo_info['path']}")

            status = self.get_git_status(repo_name)

            if not status.get('exists'):
                print(f"   ❌ NOT FOUND")
            elif status.get('error'):
                print(f"   ⚠️  ERROR: {status['error']}")
            else:
                status_emoji = "✅" if status['clean'] else "⚠️ "
                print(f"   {status_emoji} Branch: {status['branch']}")
                print(f"   📝 Uncommitted: {status['uncommitted_changes']}")
                print(f"   🔼 Unpushed: {status['unpushed_commits']}")
                print(f"   💬 Last: {status['last_commit']}")

            print()

        # Show overall health
        existing_repos = [name for name in self.repos if self.check_repo_exists(name)]
        clean_repos = [
            name for name in existing_repos
            if self.get_git_status(name).get('clean', False)
        ]

        print("=" * 80)
        print(f"SUMMARY: {len(existing_repos)}/{len(self.repos)} repos found")
        print(f"         {len(clean_repos)}/{len(existing_repos)} repos clean")
        print("=" * 80)

    def deploy_repo(self, repo_name, commit_message=None):
        """Deploy a single repo to GitHub Pages"""
        repo = self.repos[repo_name]
        repo_path = repo['path']

        if not self.check_repo_exists(repo_name):
            print(f"❌ {repo_name} not found")
            return False

        print(f"\n🚀 Deploying {repo_name}...")

        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)

            # Commit
            if not commit_message:
                commit_message = f"🤖 Auto-deploy via orchestrator ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=repo_path,
                check=False  # Don't fail if nothing to commit
            )

            # Push
            result = subprocess.run(
                ['git', 'push'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ {repo_name} deployed successfully")
                print(f"   Domains: {', '.join(repo['domains'])}")
                return True
            else:
                print(f"⚠️  Push warning: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Deploy failed: {e}")
            return False

    def deploy_all(self, commit_message=None):
        """Deploy all repos to GitHub Pages"""
        print("\n" + "=" * 80)
        print("DEPLOYING ALL REPOS")
        print("=" * 80)

        results = {}
        for repo_name in self.repos:
            if self.check_repo_exists(repo_name):
                results[repo_name] = self.deploy_repo(repo_name, commit_message)
            else:
                print(f"⏭️  Skipping {repo_name} (not found)")
                results[repo_name] = None

        # Summary
        print("\n" + "=" * 80)
        print("DEPLOY SUMMARY")
        print("=" * 80)

        successful = [name for name, result in results.items() if result is True]
        failed = [name for name, result in results.items() if result is False]
        skipped = [name for name, result in results.items() if result is None]

        print(f"✅ Successful: {len(successful)} {successful}")
        if failed:
            print(f"❌ Failed: {len(failed)} {failed}")
        if skipped:
            print(f"⏭️  Skipped: {len(skipped)} {skipped}")

        return results

    def health_check(self):
        """Check health of entire network"""
        print("\n" + "=" * 80)
        print("HEALTH CHECK")
        print("=" * 80)
        print()

        # Check Flask backend
        print("🔍 Flask Backend (soulfra-simple):")
        try:
            import requests
            response = requests.get('http://localhost:5001/health', timeout=3)
            if response.ok:
                print("   ✅ Flask running on :5001")
            else:
                print(f"   ⚠️  Flask returned {response.status_code}")
        except:
            print("   ❌ Flask not responding")

        # Check database
        print("\n🔍 Database:")
        db_path = self.repos['soulfra-simple']['path'] / 'soulfra.db'
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM simple_voice_recordings")
                count = cursor.fetchone()[0]
                print(f"   ✅ Database accessible ({count} voice memos)")
                conn.close()
            except Exception as e:
                print(f"   ⚠️  Database error: {e}")
        else:
            print("   ❌ Database not found")

        # Check Cloudflare tunnel
        print("\n🔍 Cloudflare Tunnel:")
        config_path = self.repos['soulfra-simple']['path'] / 'voice-archive' / 'config.js'
        if config_path.exists():
            content = config_path.read_text()
            import re
            match = re.search(r'return \'(https://[^\']+\.trycloudflare\.com)\'', content)
            if match:
                tunnel_url = match.group(1)
                print(f"   📡 Tunnel URL: {tunnel_url}")
                try:
                    response = requests.get(tunnel_url + '/health', timeout=5)
                    if response.ok:
                        print("   ✅ Tunnel reachable")
                    else:
                        print(f"   ⚠️  Tunnel returned {response.status_code}")
                except:
                    print("   ❌ Tunnel not reachable (restart cloudflared?)")
            else:
                print("   ⚠️  Tunnel URL not found in config.js")

        # Check Ollama
        print("\n🔍 Ollama:")
        try:
            from ollama_smart_client import get_ollama_status
            status = get_ollama_status()
            if status['available']:
                print(f"   ✅ Ollama running ({status['endpoint']})")
                print(f"   📦 Models: {len(status['models'])}")
            else:
                print(f"   ⚠️  {status['message']}")
        except:
            print("   ⚠️  ollama_smart_client not available")

        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Repo Orchestrator - Master Controller')
    parser.add_argument('--status', action='store_true', help='Show network status')
    parser.add_argument('--deploy-all', action='store_true', help='Deploy all repos')
    parser.add_argument('--deploy', type=str, help='Deploy specific repo')
    parser.add_argument('--health-check', action='store_true', help='Run health checks')
    parser.add_argument('--message', '-m', type=str, help='Custom commit message')

    args = parser.parse_args()

    orchestrator = RepoOrchestrator()

    if args.status:
        orchestrator.show_network_status()
    elif args.deploy_all:
        orchestrator.deploy_all(args.message)
    elif args.deploy:
        orchestrator.deploy_repo(args.deploy, args.message)
    elif args.health_check:
        orchestrator.health_check()
    else:
        # Default: show status
        orchestrator.show_network_status()


if __name__ == '__main__':
    main()
