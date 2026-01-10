#!/usr/bin/env python3
"""
GitHub Domain Scraper - Resource Allocation Game System

Scrapes stats from domain repos to determine resource allocation:
- Stars = user interest/votes
- Commits = developer activity
- Issues = engagement/feedback
- Signups = user growth

Each domain backed by 2 repos:
- {domain}-content (blog posts, lore, content)
- {domain}-data (datasets, configs, game data)

Output: stats.json for each domain → used for resource allocation
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# GitHub API (no auth needed for public repos, but rate-limited to 60/hour)
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Optional: set for 5000 req/hour

# Domain Configuration - Each domain has 2 repos
DOMAINS = {
    'calriven': {
        'repos': ['calriven-content', 'calriven-data'],
        'owner': 'soulfra',  # Change to your GitHub username
        'type': 'LIGHT',  # WORK/professional
        'icon': '📊'
    },
    'cringeproof': {
        'repos': ['cringeproof-content', 'cringeproof-data'],
        'owner': 'soulfra',
        'type': 'SHADOW',  # IDEAS/creative
        'icon': '🎭'
    },
    'deathtodata': {
        'repos': ['deathtodata-content', 'deathtodata-data'],
        'owner': 'soulfra',
        'type': 'LIGHT',  # Privacy/security
        'icon': '🔥'
    },
    'soulfra': {
        'repos': ['soulfra-content', 'soulfra-data'],
        'owner': 'soulfra',
        'type': 'NEUTRAL',  # Hub/spiritual
        'icon': '💜'
    }
}


def get_github_headers():
    """Get headers for GitHub API requests"""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    return headers


def scrape_repo_stats(owner: str, repo: str) -> Optional[Dict]:
    """
    Scrape stats for a single repo

    Returns:
        dict: {
            'stars': int,
            'watchers': int,
            'forks': int,
            'open_issues': int,
            'commits_last_week': int,
            'contributors': int
        }
    """
    headers = get_github_headers()

    try:
        # Get repo metadata
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        response = requests.get(repo_url, headers=headers, timeout=10)

        if response.status_code == 404:
            print(f"⚠️  Repo not found: {owner}/{repo} (will create placeholder)")
            return create_placeholder_stats()

        if response.status_code != 200:
            print(f"⚠️  GitHub API error for {owner}/{repo}: {response.status_code}")
            return None

        repo_data = response.json()

        # Get commits from last week
        since = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
        commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits?since={since}"
        commits_response = requests.get(commits_url, headers=headers, timeout=10)
        commits_last_week = len(commits_response.json()) if commits_response.status_code == 200 else 0

        # Get contributors count
        contributors_url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors"
        contributors_response = requests.get(contributors_url, headers=headers, timeout=10)
        contributors = len(contributors_response.json()) if contributors_response.status_code == 200 else 0

        return {
            'stars': repo_data.get('stargazers_count', 0),
            'watchers': repo_data.get('watchers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'open_issues': repo_data.get('open_issues_count', 0),
            'commits_last_week': commits_last_week,
            'contributors': contributors,
            'last_push': repo_data.get('pushed_at', ''),
            'created_at': repo_data.get('created_at', ''),
            'size_kb': repo_data.get('size', 0)
        }

    except Exception as e:
        print(f"❌ Error scraping {owner}/{repo}: {e}")
        return None


def create_placeholder_stats() -> Dict:
    """Create placeholder stats for repos that don't exist yet"""
    return {
        'stars': 0,
        'watchers': 0,
        'forks': 0,
        'open_issues': 0,
        'commits_last_week': 0,
        'contributors': 0,
        'last_push': '',
        'created_at': '',
        'size_kb': 0,
        'placeholder': True
    }


def scrape_domain_stats(domain_name: str, domain_config: Dict) -> Dict:
    """
    Scrape all stats for a domain (both repos)

    Returns:
        dict: {
            'domain': str,
            'type': str,
            'icon': str,
            'repos': list,
            'total_stars': int,
            'total_commits_last_week': int,
            'total_contributors': int,
            'activity_score': float,
            'allocation_priority': int,
            'timestamp': str
        }
    """
    owner = domain_config['owner']
    repos = domain_config['repos']

    print(f"\n📊 Scraping {domain_name}...")

    # Scrape both repos
    repo_stats = []
    for repo in repos:
        print(f"  → {repo}")
        stats = scrape_repo_stats(owner, repo)
        if stats:
            repo_stats.append({
                'repo': repo,
                'stats': stats
            })

    # Aggregate stats
    total_stars = sum(r['stats']['stars'] for r in repo_stats)
    total_watchers = sum(r['stats']['watchers'] for r in repo_stats)
    total_commits_last_week = sum(r['stats']['commits_last_week'] for r in repo_stats)
    total_contributors = sum(r['stats']['contributors'] for r in repo_stats)
    total_open_issues = sum(r['stats']['open_issues'] for r in repo_stats)

    # Calculate activity score (weighted formula)
    # Stars = long-term interest
    # Commits = recent activity
    # Contributors = community size
    # Issues = engagement
    activity_score = (
        (total_stars * 10) +           # Stars worth 10 points each
        (total_commits_last_week * 5) + # Recent commits worth 5 points
        (total_contributors * 20) +     # Contributors worth 20 points
        (total_open_issues * 2)         # Issues worth 2 points
    )

    return {
        'domain': domain_name,
        'type': domain_config['type'],
        'icon': domain_config['icon'],
        'repos': repo_stats,
        'total_stars': total_stars,
        'total_watchers': total_watchers,
        'total_commits_last_week': total_commits_last_week,
        'total_contributors': total_contributors,
        'total_open_issues': total_open_issues,
        'activity_score': activity_score,
        'allocation_priority': 0,  # Calculated later based on ranking
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def calculate_allocation_priorities(domain_stats: List[Dict]) -> List[Dict]:
    """
    Rank domains by activity and assign allocation priorities

    Priority 1 = Most resources/attention
    Priority N = Least resources (gets breadcrumbed TO from higher priority)
    """
    # Sort by activity score (highest first)
    sorted_domains = sorted(domain_stats, key=lambda d: d['activity_score'], reverse=True)

    # Assign priorities
    for i, domain in enumerate(sorted_domains, start=1):
        domain['allocation_priority'] = i
        domain['allocation_percent'] = calculate_allocation_percent(i, len(sorted_domains))

    return sorted_domains


def calculate_allocation_percent(priority: int, total_domains: int) -> float:
    """
    Calculate what % of resources each domain gets

    Priority 1 gets most (e.g., 40%)
    Priority 2 gets less (e.g., 30%)
    Priority 3 gets less (e.g., 20%)
    Priority 4 gets least (e.g., 10%)
    """
    if priority == 1:
        return 40.0
    elif priority == 2:
        return 30.0
    elif priority == 3:
        return 20.0
    else:
        return 10.0


def save_domain_stats(domain_stats: List[Dict], output_dir: str = 'soulfra.github.io'):
    """Save stats.json for each domain + master stats"""
    os.makedirs(output_dir, exist_ok=True)

    # Save individual domain stats
    for domain in domain_stats:
        domain_dir = os.path.join(output_dir, domain['domain'])
        os.makedirs(domain_dir, exist_ok=True)

        output_file = os.path.join(domain_dir, 'stats.json')
        with open(output_file, 'w') as f:
            json.dump(domain, f, indent=2)

        print(f"✅ Saved {output_file}")

    # Save master stats (all domains ranked)
    master_file = os.path.join(output_dir, 'domain-stats.json')
    with open(master_file, 'w') as f:
        json.dump({
            'domains': domain_stats,
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'next_update': (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        }, f, indent=2)

    print(f"✅ Saved {master_file}")


def main():
    """Main scraper function"""
    print("=" * 70)
    print("🎮 GitHub Domain Resource Allocation Scraper")
    print("=" * 70)

    if not GITHUB_TOKEN:
        print("⚠️  No GITHUB_TOKEN set - limited to 60 requests/hour")
        print("   Set GITHUB_TOKEN env var for 5000 requests/hour")

    # Scrape all domains
    all_domain_stats = []
    for domain_name, domain_config in DOMAINS.items():
        stats = scrape_domain_stats(domain_name, domain_config)
        all_domain_stats.append(stats)

    # Calculate priorities
    ranked_domains = calculate_allocation_priorities(all_domain_stats)

    # Display rankings
    print("\n" + "=" * 70)
    print("📊 DOMAIN RESOURCE ALLOCATION RANKINGS")
    print("=" * 70)
    for domain in ranked_domains:
        print(f"#{domain['allocation_priority']} {domain['icon']} {domain['domain'].upper()}")
        print(f"   Activity Score: {domain['activity_score']}")
        print(f"   Allocation: {domain['allocation_percent']}%")
        print(f"   Stars: {domain['total_stars']} | Commits (7d): {domain['total_commits_last_week']}")
        print(f"   Contributors: {domain['total_contributors']} | Issues: {domain['total_open_issues']}")
        print()

    # Save to JSON files
    save_domain_stats(ranked_domains)

    print("=" * 70)
    print("✅ Scraping complete! Stats saved to soulfra.github.io/*/stats.json")
    print("=" * 70)


if __name__ == '__main__':
    main()
