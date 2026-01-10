#!/usr/bin/env python3
"""
Portfolio Scanner - Find EVERYTHING

Scans all repos (Desktop + GitHub.com/Soulfra) and builds complete inventory.

What it finds:
- QR codes in READMEs
- Voice memos in databases
- Blog posts (published + drafts)
- Admin templates/dashboards
- Highlights and encoded sections
- Duplicates across repos
- Missing links

Output: network_map.json with complete inventory

Usage:
    python3 portfolio_scanner.py
    python3 portfolio_scanner.py --github-token YOUR_TOKEN
    python3 portfolio_scanner.py --output custom_map.json
"""

import os
import json
import sqlite3
import re
import base64
from pathlib import Path
from datetime import datetime
import argparse
import sys

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests not available - GitHub API scanning disabled")


class PortfolioScanner:
    """Complete inventory scanner for Soulfra Network"""

    def __init__(self, desktop_path=None, github_token=None):
        self.desktop = Path(desktop_path or Path.home() / 'Desktop')
        self.github_token = github_token
        self.github_username = 'Soulfra'

        # Local repos to scan
        self.local_repos = {
            'soulfra-simple': self.desktop / 'roommate-chat' / 'soulfra-simple',
            'soulfra.github.io': self.desktop / 'soulfra.github.io',
            'calriven': self.desktop / 'calriven',
            'cringeproof-vertical': self.desktop / 'cringeproof-vertical',
            'deathtodata-clean': self.desktop / 'deathtodata-clean',
            'soulfra-profile': self.desktop / 'soulfra-profile',
        }

        self.inventory = {
            'scan_time': datetime.utcnow().isoformat(),
            'local_repos': {},
            'github_repos': {},
            'voice_memos': [],
            'blog_posts': [],
            'qr_codes': [],
            'templates': [],
            'admin_dashboards': [],
            'highlights': [],
            'duplicates': [],
            'missing_links': [],
            'statistics': {}
        }

        print("🔍 Portfolio Scanner")
        print(f"Desktop: {self.desktop}")
        print(f"GitHub: {self.github_username}")
        print()

    def scan_local_repo(self, repo_name, repo_path):
        """Scan a local repository"""
        if not repo_path.exists():
            return {'exists': False}

        print(f"📦 Scanning {repo_name}...")

        info = {
            'exists': True,
            'path': str(repo_path),
            'files': 0,
            'size_mb': 0,
            'file_types': {},
            'qr_codes': [],
            'readmes': [],
            'templates': [],
            'blog_posts': []
        }

        # Count files and types
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                info['files'] += 1
                ext = file_path.suffix.lower()
                info['file_types'][ext] = info['file_types'].get(ext, 0) + 1

                try:
                    info['size_mb'] += file_path.stat().st_size / (1024 * 1024)
                except:
                    pass

        # Find QR codes in READMEs
        for readme in repo_path.rglob('README.md'):
            info['readmes'].append(str(readme.relative_to(repo_path)))
            try:
                content = readme.read_text()
                # Look for QR code references
                qr_matches = re.findall(r'(qr[_-]?code|QR|pair[_-]?code)', content, re.IGNORECASE)
                if qr_matches:
                    info['qr_codes'].append({
                        'file': str(readme.relative_to(repo_path)),
                        'mentions': len(qr_matches)
                    })
            except:
                pass

        # Find templates
        templates_dir = repo_path / 'templates'
        if templates_dir.exists():
            for template in templates_dir.rglob('*.html'):
                rel_path = str(template.relative_to(repo_path))
                info['templates'].append(rel_path)

                # Check if it's an admin dashboard
                if 'admin' in rel_path or 'dashboard' in rel_path:
                    self.inventory['admin_dashboards'].append({
                        'repo': repo_name,
                        'path': rel_path,
                        'file': template.name
                    })

        # Find blog posts in output/
        output_dir = repo_path / 'output'
        if output_dir.exists():
            for post in output_dir.rglob('*.html'):
                if 'post' in str(post):
                    rel_path = str(post.relative_to(repo_path))
                    info['blog_posts'].append(rel_path)
                    self.inventory['blog_posts'].append({
                        'repo': repo_name,
                        'path': rel_path,
                        'file': post.name
                    })

        return info

    def scan_voice_memos(self):
        """Scan voice memos from soulfra-simple database"""
        db_path = self.local_repos['soulfra-simple'] / 'soulfra.db'

        if not db_path.exists():
            print("  ⚠️  Database not found")
            return

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, created_at, transcription, file_size, filename
                FROM simple_voice_recordings
                ORDER BY created_at DESC
            ''')

            memos = cursor.fetchall()
            print(f"  🎙️  Found {len(memos)} voice memos")

            for memo in memos:
                self.inventory['voice_memos'].append({
                    'id': memo['id'],
                    'created_at': memo['created_at'],
                    'transcript_preview': memo['transcription'][:100] if memo['transcription'] else None,
                    'file_size': memo['file_size'],
                    'filename': memo['filename']
                })

            conn.close()

        except Exception as e:
            print(f"  ❌ Error scanning voice memos: {e}")

    def scan_github_repos(self):
        """Scan GitHub.com/Soulfra repos via API"""
        if not REQUESTS_AVAILABLE:
            print("⏭️  Skipping GitHub scan (requests not available)")
            return

        print(f"\n🌐 Scanning GitHub.com/{self.github_username}...")

        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'

            response = requests.get(
                f'https://api.github.com/users/{self.github_username}/repos',
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                print(f"  ⚠️  GitHub API returned {response.status_code}")
                return

            repos = response.json()
            print(f"  Found {len(repos)} repositories")

            for repo in repos:
                self.inventory['github_repos'][repo['name']] = {
                    'description': repo.get('description'),
                    'url': repo['html_url'],
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'language': repo.get('language'),
                    'updated_at': repo['updated_at'],
                    'topics': repo.get('topics', [])
                }

        except Exception as e:
            print(f"  ❌ Error scanning GitHub: {e}")

    def find_duplicates(self):
        """Find duplicate files across repos"""
        file_map = {}  # filename → [repos]

        for repo_name, repo_info in self.inventory['local_repos'].items():
            if not repo_info.get('exists'):
                continue

            for template in repo_info.get('templates', []):
                filename = Path(template).name
                if filename not in file_map:
                    file_map[filename] = []
                file_map[filename].append(repo_name)

        # Find duplicates
        for filename, repos in file_map.items():
            if len(repos) > 1:
                self.inventory['duplicates'].append({
                    'file': filename,
                    'locations': repos,
                    'count': len(repos)
                })

    def find_missing_links(self):
        """Find things that should be connected but aren't"""
        # Voice memos not published
        if self.inventory['voice_memos'] and not self.inventory['blog_posts']:
            self.inventory['missing_links'].append(
                "Voice memos exist but no blog posts found"
            )

        # Admin dashboards not publicly accessible
        if self.inventory['admin_dashboards']:
            self.inventory['missing_links'].append(
                f"{len(self.inventory['admin_dashboards'])} admin dashboards not linked from any public site"
            )

        # QR codes not documented
        qr_count = sum(
            len(repo_info.get('qr_codes', []))
            for repo_info in self.inventory['local_repos'].values()
            if repo_info.get('exists')
        )
        if qr_count > 0:
            self.inventory['missing_links'].append(
                f"{qr_count} QR code references found - consider documenting in main README"
            )

    def calculate_statistics(self):
        """Calculate summary statistics"""
        total_files = sum(
            repo_info.get('files', 0)
            for repo_info in self.inventory['local_repos'].values()
            if repo_info.get('exists')
        )

        total_size = sum(
            repo_info.get('size_mb', 0)
            for repo_info in self.inventory['local_repos'].values()
            if repo_info.get('exists')
        )

        self.inventory['statistics'] = {
            'total_local_repos': len([r for r in self.inventory['local_repos'].values() if r.get('exists')]),
            'total_github_repos': len(self.inventory['github_repos']),
            'total_files': total_files,
            'total_size_mb': round(total_size, 2),
            'voice_memos': len(self.inventory['voice_memos']),
            'blog_posts': len(self.inventory['blog_posts']),
            'admin_dashboards': len(self.inventory['admin_dashboards']),
            'templates': sum(len(r.get('templates', [])) for r in self.inventory['local_repos'].values() if r.get('exists')),
            'duplicates': len(self.inventory['duplicates']),
            'missing_links': len(self.inventory['missing_links'])
        }

    def scan_all(self):
        """Run complete scan"""
        print("=" * 80)
        print("FULL NETWORK SCAN")
        print("=" * 80)
        print()

        # Scan local repos
        for repo_name, repo_path in self.local_repos.items():
            info = self.scan_local_repo(repo_name, repo_path)
            self.inventory['local_repos'][repo_name] = info

        # Scan voice memos
        print("\n🎙️  Scanning voice memos...")
        self.scan_voice_memos()

        # Scan GitHub
        self.scan_github_repos()

        # Analysis
        print("\n🔍 Analyzing...")
        self.find_duplicates()
        self.find_missing_links()
        self.calculate_statistics()

        print("\n" + "=" * 80)
        print("SCAN COMPLETE")
        print("=" * 80)
        print()

        # Print summary
        stats = self.inventory['statistics']
        print(f"📊 Summary:")
        print(f"   Local repos: {stats['total_local_repos']}")
        print(f"   GitHub repos: {stats['total_github_repos']}")
        print(f"   Total files: {stats['total_files']:,}")
        print(f"   Total size: {stats['total_size_mb']:.1f} MB")
        print(f"   Voice memos: {stats['voice_memos']}")
        print(f"   Blog posts: {stats['blog_posts']}")
        print(f"   Admin dashboards: {stats['admin_dashboards']}")
        print(f"   Templates: {stats['templates']}")
        print(f"   Duplicates: {stats['duplicates']}")
        print(f"   Missing links: {stats['missing_links']}")

        return self.inventory

    def save_to_file(self, output_path='network_map.json'):
        """Save inventory to JSON file"""
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)

        print(f"\n💾 Saved to: {output_file}")
        print(f"   Size: {output_file.stat().st_size / 1024:.1f} KB")


def main():
    parser = argparse.ArgumentParser(description='Portfolio Scanner - Complete Inventory')
    parser.add_argument('--github-token', type=str, help='GitHub personal access token')
    parser.add_argument('--output', type=str, default='network_map.json', help='Output JSON file')
    parser.add_argument('--desktop', type=str, help='Custom desktop path')

    args = parser.parse_args()

    scanner = PortfolioScanner(
        desktop_path=args.desktop,
        github_token=args.github_token
    )

    inventory = scanner.scan_all()
    scanner.save_to_file(args.output)

    print("\n✅ Run complete!")
    print(f"   View results: cat {args.output}")
    print(f"   Or import in Python: import json; data = json.load(open('{args.output}'))")


if __name__ == '__main__':
    main()
