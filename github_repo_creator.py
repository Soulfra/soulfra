#!/usr/bin/env python3
"""
GitHub Repo Auto-Creator
Creates GitHub repos for new domains automatically
"""

import os
import requests
import subprocess
from pathlib import Path
from typing import Optional


class GitHubRepoCreator:
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize with GitHub token

        Get token from: https://github.com/settings/tokens
        Needs 'repo' scope
        """
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        self.org_name = "Soulfra"
        self.repos_base_path = Path(__file__).parent.parent / 'github-repos'

    def create_repo(self, domain: str) -> dict:
        """
        Create GitHub repo for domain

        Returns:
        {
            'success': True,
            'repo_name': 'hollowtown-site',
            'repo_url': 'https://github.com/Soulfra/hollowtown-site',
            'local_path': '/path/to/github-repos/hollowtown-site'
        }
        """
        # Generate repo name from domain
        base_name = domain.split('.')[0]
        repo_name = f"{base_name}-site"

        # Check if already exists on GitHub
        if self._repo_exists(repo_name):
            print(f"✅ Repo already exists: {repo_name}")
            return {
                'success': True,
                'repo_name': repo_name,
                'repo_url': f"https://github.com/{self.org_name}/{repo_name}",
                'local_path': str(self.repos_base_path / repo_name),
                'already_existed': True
            }

        # Create repo via GitHub API
        print(f"📦 Creating GitHub repo: {repo_name}")

        if not self.github_token:
            print("❌ No GitHub token found. Set GITHUB_TOKEN environment variable.")
            return {'success': False, 'error': 'No GitHub token'}

        response = requests.post(
            f"https://api.github.com/orgs/{self.org_name}/repos",
            headers={
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            json={
                'name': repo_name,
                'description': f"Website for {domain}",
                'homepage': f"https://{domain}",
                'private': False,
                'has_issues': True,
                'has_projects': False,
                'has_wiki': False,
                'auto_init': True  # Initialize with README
            }
        )

        if response.status_code == 201:
            repo_data = response.json()
            print(f"✅ Created: {repo_data['html_url']}")

            # Clone locally
            local_path = self._clone_repo(repo_name)

            # Initialize with basic structure
            self._initialize_repo_structure(local_path, domain)

            return {
                'success': True,
                'repo_name': repo_name,
                'repo_url': repo_data['html_url'],
                'local_path': str(local_path),
                'clone_url': repo_data['clone_url']
            }
        else:
            print(f"❌ Failed to create repo: {response.status_code}")
            print(response.json())
            return {
                'success': False,
                'error': response.json()
            }

    def _repo_exists(self, repo_name: str) -> bool:
        """Check if repo already exists on GitHub"""
        if not self.github_token:
            return False

        response = requests.get(
            f"https://api.github.com/repos/{self.org_name}/{repo_name}",
            headers={
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        return response.status_code == 200

    def _clone_repo(self, repo_name: str) -> Path:
        """Clone repo to local github-repos/ folder"""
        self.repos_base_path.mkdir(parents=True, exist_ok=True)
        local_path = self.repos_base_path / repo_name

        if local_path.exists():
            print(f"📁 Already cloned: {local_path}")
            # Pull latest
            subprocess.run(['git', 'pull'], cwd=local_path, check=True)
        else:
            print(f"📥 Cloning to: {local_path}")
            clone_url = f"https://github.com/{self.org_name}/{repo_name}.git"
            subprocess.run(
                ['git', 'clone', clone_url, str(local_path)],
                check=True
            )

        return local_path

    def _initialize_repo_structure(self, repo_path: Path, domain: str):
        """
        Initialize repo with basic folder structure

        Creates:
        - posts/
        - api/
        - docs/
        - index.html (basic landing page)
        """
        # Create folders
        (repo_path / 'posts').mkdir(exist_ok=True)
        (repo_path / 'api').mkdir(exist_ok=True)
        (repo_path / 'docs').mkdir(exist_ok=True)

        # Create basic index.html if it doesn't exist
        index_file = repo_path / 'index.html'
        if not index_file.exists():
            index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }}
        h1 {{ color: #333; }}
        .posts {{ margin-top: 2rem; }}
        .post {{ margin-bottom: 1rem; padding: 1rem; background: #f5f5f5; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>Welcome to {domain}</h1>
    <p>This site is powered by the Soulfra platform.</p>

    <div class="posts">
        <h2>Latest Posts</h2>
        <p>No posts yet. Check back soon!</p>
    </div>
</body>
</html>
"""
            index_file.write_text(index_content)

        # Create README if it doesn't exist
        readme_file = repo_path / 'README.md'
        if not readme_file.exists():
            readme_content = f"""# {domain}

Website repository for {domain}.

## Structure

- `posts/` - Blog posts and content
- `api/` - API documentation
- `docs/` - General documentation
- `index.html` - Landing page

## Publishing

Content is published via the Soulfra Studio platform.

GitHub Pages: https://{self.org_name.lower()}.github.io/{repo_path.name}
"""
            readme_file.write_text(readme_content)

        # Git commit and push
        try:
            subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
            subprocess.run(
                ['git', 'commit', '-m', 'Initialize repo structure'],
                cwd=repo_path,
                check=False  # Don't fail if nothing to commit
            )
            subprocess.run(['git', 'push'], cwd=repo_path, check=True)
            print(f"✅ Initialized structure for {domain}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git push failed (might need authentication): {e}")


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 github_repo_creator.py <domain>")
        print("Example: python3 github_repo_creator.py hollowtown.com")
        print("\nSet GITHUB_TOKEN environment variable first:")
        print("export GITHUB_TOKEN='your_token_here'")
        sys.exit(1)

    domain = sys.argv[1]
    creator = GitHubRepoCreator()

    result = creator.create_repo(domain)

    if result['success']:
        print(f"\n🎉 Success!")
        print(f"   Repo: {result['repo_url']}")
        print(f"   Local: {result['local_path']}")
        print(f"\n📝 Next steps:")
        print(f"   1. Run domain onboarding: python3 domain_onboarding.py {domain}")
        print(f"   2. Go to Studio: http://localhost:5001/studio")
        print(f"   3. Write content and publish!")
    else:
        print(f"\n❌ Failed: {result.get('error')}")
