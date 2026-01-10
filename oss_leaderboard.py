#!/usr/bin/env python3
"""
OSS Contributor Leaderboard - Rank Developers by Domain Contributions

Scrapes GitHub contributor data for each domain's repos and ranks them:
- Total commits
- Pull requests merged
- Issues opened/resolved
- Stars given to repos
- Lines of code added

Output: leaderboard.json for each domain + global leaderboard

Usage:
    python3 oss_leaderboard.py
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


# GitHub API
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Domains from github_domain_scraper.py
DOMAINS = {
    'calriven': {'repos': ['calriven-content', 'calriven-data'], 'owner': 'soulfra'},
    'cringeproof': {'repos': ['cringeproof-content', 'cringeproof-data'], 'owner': 'soulfra'},
    'deathtodata': {'repos': ['deathtodata-content', 'deathtodata-data'], 'owner': 'soulfra'},
    'soulfra': {'repos': ['soulfra-content', 'soulfra-data'], 'owner': 'soulfra'}
}


def get_github_headers():
    """Get headers for GitHub API requests"""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    return headers


def get_repo_contributors(owner: str, repo: str) -> List[Dict]:
    """
    Get all contributors for a repo

    Returns:
        list: [{
            'login': str,
            'contributions': int,  # Number of commits
            'avatar_url': str,
            'html_url': str
        }]
    """
    headers = get_github_headers()
    contributors_url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors"

    try:
        response = requests.get(contributors_url, headers=headers, timeout=10)
        if response.status_code == 404:
            return []  # Repo doesn't exist yet
        if response.status_code != 200:
            print(f"⚠️  GitHub API error for {owner}/{repo}: {response.status_code}")
            return []

        return response.json()
    except Exception as e:
        print(f"❌ Error fetching contributors for {owner}/{repo}: {e}")
        return []


def get_user_pull_requests(owner: str, repo: str, username: str) -> int:
    """Get number of merged PRs by user in a repo"""
    headers = get_github_headers()

    # Search for merged PRs by user
    query = f"repo:{owner}/{repo} is:pr is:merged author:{username}"
    search_url = f"{GITHUB_API}/search/issues?q={query}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('total_count', 0)
        return 0
    except:
        return 0


def get_user_issues(owner: str, repo: str, username: str) -> Dict:
    """Get number of issues opened/closed by user"""
    headers = get_github_headers()

    # Issues opened
    opened_query = f"repo:{owner}/{repo} is:issue author:{username}"
    opened_url = f"{GITHUB_API}/search/issues?q={opened_query}"

    try:
        opened_response = requests.get(opened_url, headers=headers, timeout=10)
        opened_count = opened_response.json().get('total_count', 0) if opened_response.status_code == 200 else 0
    except:
        opened_count = 0

    return {
        'opened': opened_count,
        'total': opened_count
    }


def calculate_contributor_score(contributor_data: Dict) -> int:
    """
    Calculate overall score for a contributor

    Formula:
    - Commits: 10 points each
    - Merged PRs: 50 points each
    - Issues opened: 5 points each
    - Repos contributed to: 100 points each
    """
    score = (
        (contributor_data['total_commits'] * 10) +
        (contributor_data['total_prs'] * 50) +
        (contributor_data['total_issues'] * 5) +
        (contributor_data['repos_count'] * 100)
    )
    return score


def get_contributor_tier(score: int) -> Dict:
    """
    Assign tier based on score

    Tiers:
    - Champion: 10000+ points
    - Hero: 5000+ points
    - Contributor: 1000+ points
    - Supporter: 100+ points
    - Newcomer: < 100 points
    """
    if score >= 10000:
        return {'tier': 'Champion', 'emoji': '🏆', 'color': '#FFD700'}
    elif score >= 5000:
        return {'tier': 'Hero', 'emoji': '⭐', 'color': '#C0C0C0'}
    elif score >= 1000:
        return {'tier': 'Contributor', 'emoji': '💎', 'color': '#CD7F32'}
    elif score >= 100:
        return {'tier': 'Supporter', 'emoji': '👍', 'color': '#4A90E2'}
    else:
        return {'tier': 'Newcomer', 'emoji': '🌱', 'color': '#7ED321'}


def scrape_domain_contributors(domain_name: str, domain_config: Dict) -> Dict:
    """
    Scrape all contributors for a domain (both repos)

    Returns:
        dict: {
            'domain': str,
            'contributors': [{
                'username': str,
                'total_commits': int,
                'total_prs': int,
                'total_issues': int,
                'repos_count': int,
                'score': int,
                'tier': str,
                'avatar_url': str,
                'profile_url': str
            }]
        }
    """
    owner = domain_config['owner']
    repos = domain_config['repos']

    print(f"\n👥 Scraping contributors for {domain_name}...")

    # Aggregate contributors across both repos
    contributor_map = defaultdict(lambda: {
        'username': '',
        'avatar_url': '',
        'profile_url': '',
        'total_commits': 0,
        'total_prs': 0,
        'total_issues': 0,
        'repos_count': 0,
        'repos': []
    })

    for repo in repos:
        print(f"  → {repo}")
        contributors = get_repo_contributors(owner, repo)

        for contrib in contributors:
            username = contrib['login']
            commits = contrib['contributions']

            # Update contributor data
            contributor_map[username]['username'] = username
            contributor_map[username]['avatar_url'] = contrib['avatar_url']
            contributor_map[username]['profile_url'] = contrib['html_url']
            contributor_map[username]['total_commits'] += commits
            contributor_map[username]['repos_count'] += 1
            contributor_map[username]['repos'].append({
                'repo': repo,
                'commits': commits
            })

            # Get PRs and issues (slow, so limit to top contributors)
            if commits > 5:  # Only check for contributors with > 5 commits
                prs = get_user_pull_requests(owner, repo, username)
                issues = get_user_issues(owner, repo, username)
                contributor_map[username]['total_prs'] += prs
                contributor_map[username]['total_issues'] += issues['total']

    # Convert to list and calculate scores
    contributors_list = []
    for username, data in contributor_map.items():
        score = calculate_contributor_score(data)
        tier_info = get_contributor_tier(score)

        contributors_list.append({
            **data,
            'score': score,
            'tier': tier_info['tier'],
            'tier_emoji': tier_info['emoji'],
            'tier_color': tier_info['color']
        })

    # Sort by score (highest first)
    contributors_list.sort(key=lambda c: c['score'], reverse=True)

    return {
        'domain': domain_name,
        'total_contributors': len(contributors_list),
        'contributors': contributors_list,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def generate_global_leaderboard(domain_leaderboards: Dict[str, Dict]) -> Dict:
    """
    Merge all domain leaderboards into one global leaderboard

    Users who contribute to multiple domains get boosted scores
    """
    global_contributor_map = defaultdict(lambda: {
        'username': '',
        'avatar_url': '',
        'profile_url': '',
        'total_commits': 0,
        'total_prs': 0,
        'total_issues': 0,
        'domains_count': 0,
        'domains': []
    })

    for domain_name, leaderboard in domain_leaderboards.items():
        for contrib in leaderboard['contributors']:
            username = contrib['username']

            # Aggregate across domains
            global_contributor_map[username]['username'] = username
            global_contributor_map[username]['avatar_url'] = contrib['avatar_url']
            global_contributor_map[username]['profile_url'] = contrib['profile_url']
            global_contributor_map[username]['total_commits'] += contrib['total_commits']
            global_contributor_map[username]['total_prs'] += contrib['total_prs']
            global_contributor_map[username]['total_issues'] += contrib['total_issues']
            global_contributor_map[username]['domains_count'] += 1
            global_contributor_map[username]['domains'].append({
                'domain': domain_name,
                'commits': contrib['total_commits'],
                'score': contrib['score']
            })

    # Convert to list and calculate global scores
    global_contributors = []
    for username, data in global_contributor_map.items():
        # Global score includes domain diversity bonus
        base_score = calculate_contributor_score(data)
        domain_bonus = data['domains_count'] * 500  # 500 points per domain
        global_score = base_score + domain_bonus

        tier_info = get_contributor_tier(global_score)

        global_contributors.append({
            **data,
            'score': global_score,
            'tier': tier_info['tier'],
            'tier_emoji': tier_info['emoji'],
            'tier_color': tier_info['color']
        })

    # Sort by global score
    global_contributors.sort(key=lambda c: c['score'], reverse=True)

    return {
        'total_contributors': len(global_contributors),
        'contributors': global_contributors,
        'generated_at': datetime.utcnow().isoformat() + 'Z'
    }


def save_leaderboards(domain_leaderboards: Dict, global_leaderboard: Dict, output_dir: str = 'soulfra.github.io'):
    """Save leaderboard files"""
    os.makedirs(output_dir, exist_ok=True)

    # Save per-domain leaderboards
    for domain_name, leaderboard in domain_leaderboards.items():
        domain_dir = os.path.join(output_dir, domain_name)
        os.makedirs(domain_dir, exist_ok=True)

        output_file = os.path.join(domain_dir, 'leaderboard.json')
        with open(output_file, 'w') as f:
            json.dump(leaderboard, f, indent=2)

        print(f"✅ Saved {output_file}")

    # Save global leaderboard
    global_file = os.path.join(output_dir, 'global-leaderboard.json')
    with open(global_file, 'w') as f:
        json.dump(global_leaderboard, f, indent=2)

    print(f"✅ Saved {global_file}")


def display_leaderboard(domain_leaderboards: Dict, global_leaderboard: Dict):
    """Print leaderboard to console"""
    print("\n" + "=" * 70)
    print("🏆 OSS CONTRIBUTOR LEADERBOARD")
    print("=" * 70)

    # Display per-domain leaders
    for domain_name, leaderboard in sorted(domain_leaderboards.items()):
        contributors = leaderboard['contributors'][:5]  # Top 5

        if contributors:
            print(f"\n📊 {domain_name.upper()} - Top Contributors:")
            for i, contrib in enumerate(contributors, 1):
                print(f"  #{i} {contrib['tier_emoji']} {contrib['username']}")
                print(f"     Score: {contrib['score']} | Tier: {contrib['tier']}")
                print(f"     Commits: {contrib['total_commits']} | PRs: {contrib['total_prs']} | Issues: {contrib['total_issues']}")
        else:
            print(f"\n📊 {domain_name.upper()}: No contributors yet")

    # Display global leaders
    print(f"\n🌐 GLOBAL LEADERBOARD - Top 10:")
    for i, contrib in enumerate(global_leaderboard['contributors'][:10], 1):
        print(f"  #{i} {contrib['tier_emoji']} {contrib['username']}")
        print(f"     Score: {contrib['score']} | Tier: {contrib['tier']}")
        print(f"     Commits: {contrib['total_commits']} | Domains: {contrib['domains_count']}")


def main():
    """Main leaderboard function"""
    print("=" * 70)
    print("🏆 OSS Contributor Leaderboard Generator")
    print("=" * 70)

    if not GITHUB_TOKEN:
        print("⚠️  No GITHUB_TOKEN set - limited to 60 requests/hour")
        print("   Set GITHUB_TOKEN env var for 5000 requests/hour")

    # Scrape contributors for each domain
    domain_leaderboards = {}
    for domain_name, domain_config in DOMAINS.items():
        leaderboard = scrape_domain_contributors(domain_name, domain_config)
        domain_leaderboards[domain_name] = leaderboard

    # Generate global leaderboard
    print("\n🌐 Generating global leaderboard...")
    global_leaderboard = generate_global_leaderboard(domain_leaderboards)

    # Display results
    display_leaderboard(domain_leaderboards, global_leaderboard)

    # Save to JSON files
    print("\n💾 Saving leaderboards...")
    save_leaderboards(domain_leaderboards, global_leaderboard)

    print("\n" + "=" * 70)
    print("✅ Leaderboard generation complete!")
    print("=" * 70)
    print("\nFiles saved:")
    print("  - soulfra.github.io/*/leaderboard.json (per-domain)")
    print("  - soulfra.github.io/global-leaderboard.json (all domains)")
    print("\nNext steps:")
    print("  1. Display leaderboards on domain homepages")
    print("  2. Add contributor badges/profiles")
    print("  3. Set up GitHub Actions to update hourly")
    print("=" * 70)


if __name__ == '__main__':
    main()
