#!/usr/bin/env python3
"""
Ollama GitHub Search - Query your GitHub repos/pages/blogs with AI

Integrates GitHub API with Ollama to search and answer questions about:
- Repository code and README files
- GitHub Pages content
- Issues and PR discussions
- Blog posts in repos

Usage:
    python3 ollama_github_search.py "How does my Flask app handle authentication?"
    python3 ollama_github_search.py --repo my-username/my-repo "What's in the README?"
"""

import json
import sys
import urllib.request
import urllib.error
from typing import List, Dict, Optional
from pathlib import Path


class GitHubSearcher:
    """Search GitHub repos and feed content to Ollama"""

    def __init__(
        self,
        github_token: Optional[str] = None,
        github_username: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3.2"
    ):
        self.github_token = github_token
        self.github_username = github_username
        self.ollama_url = ollama_url
        self.model = model

    def fetch_github(self, url: str) -> Dict:
        """Fetch data from GitHub API"""
        req = urllib.request.Request(url)

        # Add auth header if token provided
        if self.github_token:
            req.add_header('Authorization', f'token {self.github_token}')

        req.add_header('Accept', 'application/vnd.github.v3+json')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"⚠️  GitHub API error: {e.code} {e.reason}", file=sys.stderr)
            return {}

    def search_repo_content(self, repo: str, query: str) -> List[Dict]:
        """Search for files in a repo matching query"""
        url = f"https://api.github.com/search/code?q={query}+repo:{repo}"
        data = self.fetch_github(url)

        results = []
        for item in data.get('items', []):
            # Fetch file content
            content_url = item.get('url')
            if content_url:
                file_data = self.fetch_github(content_url)

                # Decode base64 content
                import base64
                content = base64.b64decode(file_data.get('content', '')).decode('utf-8', errors='ignore')

                results.append({
                    'path': item.get('path', ''),
                    'url': item.get('html_url', ''),
                    'content': content[:5000]  # Limit to 5000 chars
                })

        return results

    def get_repo_readme(self, repo: str) -> Optional[str]:
        """Get README content from repo"""
        url = f"https://api.github.com/repos/{repo}/readme"
        data = self.fetch_github(url)

        if data and 'content' in data:
            import base64
            return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
        return None

    def list_user_repos(self, username: Optional[str] = None) -> List[str]:
        """List all repos for a user"""
        username = username or self.github_username
        if not username:
            return []

        url = f"https://api.github.com/users/{username}/repos?per_page=100"
        data = self.fetch_github(url)

        return [repo['full_name'] for repo in data if isinstance(data, list)]

    def ask_ollama(self, question: str, context: str) -> Optional[str]:
        """Ask Ollama with GitHub context"""
        prompt = f"""You are a helpful assistant that answers questions about GitHub repositories.

GitHub Context:
{context}

User Question: {question}

Provide a detailed answer based on the GitHub content above. Include specific file paths or code snippets when relevant."""

        try:
            url = f"{self.ollama_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')

        except Exception as e:
            print(f"❌ Ollama error: {e}", file=sys.stderr)
            return None

    def search_and_answer(
        self,
        question: str,
        repo: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Optional[str]:
        """Search GitHub and answer with Ollama"""

        # If no repo specified, try to find from user's repos
        if not repo and self.github_username:
            repos = self.list_user_repos()
            if repos:
                print(f"🔍 Searching across {len(repos)} repos...")
                repo = repos[0]  # Use first repo for now
            else:
                print("❌ No repos found for user", file=sys.stderr)
                return None

        if not repo:
            print("❌ No repo specified", file=sys.stderr)
            return None

        print(f"📚 Fetching content from {repo}...")

        # Build context from multiple sources
        context = ""

        # 1. Get README
        readme = self.get_repo_readme(repo)
        if readme:
            context += f"\n\n--- README.md ---\n{readme[:3000]}\n"

        # 2. Search code if query provided
        if search_query:
            code_results = self.search_repo_content(repo, search_query)
            for result in code_results[:3]:  # Limit to 3 results
                context += f"\n\n--- {result['path']} ---\n{result['content']}\n"

        if not context:
            print("⚠️  No content found", file=sys.stderr)
            return None

        # Ask Ollama
        print(f"🤖 Asking Ollama ({self.model})...\n")
        return self.ask_ollama(question, context)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Search GitHub repos with Ollama')
    parser.add_argument('question', type=str, nargs='?', help='Question to ask')
    parser.add_argument('--repo', type=str, help='GitHub repo (username/repo)')
    parser.add_argument('--username', type=str, help='GitHub username')
    parser.add_argument('--token', type=str, help='GitHub token (for private repos)')
    parser.add_argument('--search', type=str, help='Search query for code files')
    parser.add_argument('--model', type=str, default='llama3.2', help='Ollama model')
    parser.add_argument('--list-repos', action='store_true', help='List user repos')

    args = parser.parse_args()

    searcher = GitHubSearcher(
        github_token=args.token,
        github_username=args.username,
        model=args.model
    )

    if args.list_repos:
        repos = searcher.list_user_repos(args.username)
        print(f"\n📚 Found {len(repos)} repos:\n")
        for repo in repos:
            print(f"   • {repo}")
        return

    if not args.question:
        parser.print_help()
        return

    answer = searcher.search_and_answer(
        args.question,
        repo=args.repo,
        search_query=args.search
    )

    if answer:
        print(f"\n💡 Answer:\n{answer}\n")
    else:
        print("\n❌ Could not generate answer\n", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
