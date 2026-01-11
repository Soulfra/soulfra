#!/usr/bin/env python3
"""
Contributor Rewards - Track GitHub Contributions → Ownership %

Tracks contributions across projects and calculates ownership rewards:
- Stars = interest signal
- PRs = code contributions
- Issues = bug reports/features
- Commits = direct work
- Comments = community engagement

Year 1 = Build phase → Ownership solidifies at end

Run: python3 contributor_rewards.py --help
"""

import sys
import argparse
from database import get_db
from datetime import datetime, timedelta
import requests
import os

# =============================================================================
# GITHUB API
# =============================================================================

def get_github_repo_contributors(owner, repo, github_token=None):
    """
    Fetch contributors from GitHub API

    Args:
        owner: GitHub repo owner
        repo: Repo name
        github_token: GitHub API token (optional, but recommended for rate limits)

    Returns:
        List of contributor dicts with stats
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"

    headers = {}
    if github_token:
        headers['Authorization'] = f"token {github_token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        contributors = response.json()

        return [{
            'github_username': c['login'],
            'contributions': c['contributions'],
            'avatar_url': c['avatar_url'],
            'profile_url': c['html_url']
        } for c in contributors]

    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub API error: {e}")
        return []


def get_github_repo_stars(owner, repo, github_token=None):
    """
    Get star count for a repo

    Args:
        owner: GitHub repo owner
        repo: Repo name
        github_token: GitHub API token (optional)

    Returns:
        Star count
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {}
    if github_token:
        headers['Authorization'] = f"token {github_token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get('stargazers_count', 0)

    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub API error: {e}")
        return 0


# =============================================================================
# CONTRIBUTION TRACKING
# =============================================================================

def sync_contributors_from_github(project_slug, github_token=None):
    """
    Sync contributors from GitHub API to database

    Args:
        project_slug: Project slug
        github_token: GitHub API token (optional)

    Returns:
        Number of contributors synced
    """
    db = get_db()

    # Get project
    project = db.execute('''
        SELECT * FROM projects WHERE slug = ?
    ''', (project_slug,)).fetchone()

    if not project:
        print(f"❌ Project not found: {project_slug}")
        return 0

    owner = project['github_owner']
    repo = project['github_repo']

    print(f"📡 Fetching contributors from GitHub: {owner}/{repo}")

    # Fetch from GitHub
    github_contributors = get_github_repo_contributors(owner, repo, github_token)

    if not github_contributors:
        print("⚠️  No contributors found (repo may not exist yet)")
        return 0

    synced = 0

    for contrib in github_contributors:
        username = contrib['github_username']
        contribution_count = contrib['contributions']

        # Calculate ownership based on contributions
        # Formula: Base 1% for first contribution + 0.1% per additional 10 contributions
        ownership = 1.0 + (contribution_count // 10) * 0.1

        # Cap at 10% per contributor (to prevent single-person takeover)
        ownership = min(ownership, 10.0)

        # Check if contributor exists
        existing = db.execute('''
            SELECT * FROM project_contributors
            WHERE project_id = ? AND github_username = ?
        ''', (project['id'], username)).fetchone()

        if existing:
            # Update existing
            db.execute('''
                UPDATE project_contributors
                SET contribution_count = ?,
                    ownership_earned = ?,
                    last_contribution = datetime('now')
                WHERE id = ?
            ''', (contribution_count, ownership, existing['id']))
            print(f"  ✅ Updated: {username} ({contribution_count} commits → {ownership:.2f}%)")
        else:
            # Insert new
            db.execute('''
                INSERT INTO project_contributors
                (project_id, github_username, contribution_type, contribution_count, ownership_earned, last_contribution)
                VALUES (?, ?, 'commit', ?, ?, datetime('now'))
            ''', (project['id'], username, contribution_count, ownership))
            print(f"  ✅ Added: {username} ({contribution_count} commits → {ownership:.2f}%)")

        synced += 1

    db.commit()
    db.close()

    return synced


def calculate_project_ownership_distribution(project_slug):
    """
    Calculate total ownership distribution for a project

    Args:
        project_slug: Project slug

    Returns:
        Dict with ownership breakdown
    """
    db = get_db()

    # Get project
    project = db.execute('''
        SELECT * FROM projects WHERE slug = ?
    ''', (project_slug,)).fetchone()

    if not project:
        return None

    # Get all contributors
    contributors = db.execute('''
        SELECT * FROM project_contributors
        WHERE project_id = ?
        ORDER BY ownership_earned DESC
    ''', (project['id'],)).fetchall()

    # Calculate totals
    total_ownership = sum(c['ownership_earned'] for c in contributors)
    remaining_ownership = 100.0 - total_ownership

    db.close()

    return {
        'project': dict(project),
        'contributors': [dict(c) for c in contributors],
        'total_distributed': total_ownership,
        'remaining_pool': max(0, remaining_ownership),
        'contributor_count': len(contributors)
    }


def get_contributor_portfolio(github_username):
    """
    Get all projects a contributor is involved in

    Args:
        github_username: GitHub username

    Returns:
        List of projects with ownership earned
    """
    db = get_db()

    contributions = db.execute('''
        SELECT
            pc.*,
            p.slug,
            p.name,
            p.primary_domain,
            p.status
        FROM project_contributors pc
        JOIN projects p ON pc.project_id = p.id
        WHERE pc.github_username = ?
        ORDER BY pc.ownership_earned DESC
    ''', (github_username,)).fetchall()

    db.close()

    if not contributions:
        return None

    total_ownership = sum(c['ownership_earned'] for c in contributions)

    return {
        'github_username': github_username,
        'total_ownership': total_ownership,
        'projects': [dict(c) for c in contributions],
        'project_count': len(contributions)
    }


# =============================================================================
# LEADERBOARD
# =============================================================================

def get_global_contributor_leaderboard(limit=10):
    """
    Get top contributors across ALL projects

    Args:
        limit: Number of top contributors to return

    Returns:
        List of top contributors
    """
    db = get_db()

    # Aggregate ownership across all projects
    leaderboard = db.execute(f'''
        SELECT
            github_username,
            COUNT(DISTINCT project_id) as project_count,
            SUM(ownership_earned) as total_ownership,
            SUM(contribution_count) as total_contributions
        FROM project_contributors
        GROUP BY github_username
        ORDER BY total_ownership DESC
        LIMIT {limit}
    ''').fetchall()

    db.close()

    return [dict(row) for row in leaderboard]


# =============================================================================
# CLI COMMANDS
# =============================================================================

def cmd_sync(args):
    """CLI: Sync contributors from GitHub"""
    github_token = os.getenv('GITHUB_TOKEN') or args.token

    if not github_token:
        print("⚠️  No GitHub token provided - API rate limits will apply")
        print("   Set GITHUB_TOKEN env var or use --token flag")
        print()

    count = sync_contributors_from_github(args.project, github_token)
    print(f"\n✅ Synced {count} contributors")


def cmd_ownership(args):
    """CLI: Show ownership distribution"""
    dist = calculate_project_ownership_distribution(args.project)

    if not dist:
        print(f"❌ Project not found: {args.project}")
        return

    proj = dist['project']

    print(f"\n📊 Ownership Distribution: {proj['name']}")
    print(f"{'='*70}")
    print(f"Total Distributed: {dist['total_distributed']:.2f}%")
    print(f"Remaining Pool: {dist['remaining_pool']:.2f}%")
    print(f"Contributors: {dist['contributor_count']}")
    print()

    print("Top Contributors:")
    for i, contrib in enumerate(dist['contributors'][:10], 1):
        print(f"  {i}. {contrib['github_username']}: {contrib['ownership_earned']:.2f}%")
        print(f"     {contrib['contribution_count']} {contrib['contribution_type']}s")


def cmd_portfolio(args):
    """CLI: Show contributor portfolio"""
    portfolio = get_contributor_portfolio(args.username)

    if not portfolio:
        print(f"❌ No contributions found for: {args.username}")
        return

    print(f"\n📁 Contributor Portfolio: {portfolio['github_username']}")
    print(f"{'='*70}")
    print(f"Total Ownership: {portfolio['total_ownership']:.2f}%")
    print(f"Projects: {portfolio['project_count']}")
    print()

    print("Project Breakdown:")
    for proj in portfolio['projects']:
        print(f"  • {proj['name']} ({proj['slug']})")
        print(f"    Domain: {proj['primary_domain']}")
        print(f"    Ownership: {proj['ownership_earned']:.2f}%")
        print(f"    Contributions: {proj['contribution_count']} {proj['contribution_type']}s")
        print()


def cmd_leaderboard(args):
    """CLI: Show global contributor leaderboard"""
    leaderboard = get_global_contributor_leaderboard(limit=args.limit)

    print(f"\n🏆 Top {args.limit} Contributors Across All Projects")
    print(f"{'='*70}\n")

    for i, contrib in enumerate(leaderboard, 1):
        print(f"{i}. {contrib['github_username']}")
        print(f"   Total Ownership: {contrib['total_ownership']:.2f}%")
        print(f"   Projects: {contrib['project_count']}")
        print(f"   Contributions: {contrib['total_contributions']}")
        print()


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Contributor Rewards System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Sync command
    parser_sync = subparsers.add_parser('sync', help='Sync contributors from GitHub')
    parser_sync.add_argument('project', help='Project slug')
    parser_sync.add_argument('--token', help='GitHub API token')

    # Ownership command
    parser_ownership = subparsers.add_parser('ownership', help='Show ownership distribution')
    parser_ownership.add_argument('project', help='Project slug')

    # Portfolio command
    parser_portfolio = subparsers.add_parser('portfolio', help='Show contributor portfolio')
    parser_portfolio.add_argument('username', help='GitHub username')

    # Leaderboard command
    parser_leaderboard = subparsers.add_parser('leaderboard', help='Show global leaderboard')
    parser_leaderboard.add_argument('--limit', type=int, default=10,
                                   help='Number of top contributors')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'sync':
        cmd_sync(args)
        return 0

    if args.command == 'ownership':
        cmd_ownership(args)
        return 0

    if args.command == 'portfolio':
        cmd_portfolio(args)
        return 0

    if args.command == 'leaderboard':
        cmd_leaderboard(args)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
