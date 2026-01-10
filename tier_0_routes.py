#!/usr/bin/env python3
"""
Tier 0 Routes - Pure Information Layer (soulfra.com)

NO commerce, NO selling, NO paywalls
Gateway to entire platform - discovery layer

Routes:
- / - Homepage (browse content)
- /discover - Content discovery
- /about - Platform explanation
- /tiers - Tier system explanation (unlock roadmap)
- /domains - Available domains showcase
- /post/<slug> - Read individual posts (public)
- /category/<category> - Browse by category
- /search - Search all content
- /github-login - GitHub OAuth (tier assignment)

All routes are READ-ONLY and publicly accessible.
No login required except for tier unlocking.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database import get_db
from ownership_ledger import (
    get_unlocked_domains,
    calculate_tier_from_github,
    get_user_ownership_summary
)
from github_faucet import GitHubFaucet
import os

# Blueprint for tier 0 routes
tier_0 = Blueprint('tier_0', __name__)


# ==============================================================================
# HOMEPAGE & DISCOVERY
# ==============================================================================

@tier_0.route('/')
def homepage():
    """
    Homepage - Browse recent content across all domains

    Public, no login required
    Shows what the platform is about
    """
    conn = get_db()

    # Get recent posts from all domains
    posts = conn.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.published_at,
            u.username,
            u.display_name,
            d.domain_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN domains d ON p.domain_id = d.id
        WHERE p.published_at IS NOT NULL
        ORDER BY p.published_at DESC
        LIMIT 20
    ''').fetchall()

    conn.close()

    return render_template('tier_0/homepage.html', posts=posts)


@tier_0.route('/discover')
def discover():
    """
    Content discovery - Explore by category, tag, domain

    Public, no login required
    """
    conn = get_db()

    # Get all categories with post counts
    categories = conn.execute('''
        SELECT category, COUNT(*) as count
        FROM posts
        WHERE published_at IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    ''').fetchall()

    # Get all domains with post counts
    domains = conn.execute('''
        SELECT
            d.domain_name,
            d.category,
            d.tier_requirement,
            COUNT(p.id) as post_count
        FROM domains d
        LEFT JOIN posts p ON d.id = p.domain_id
        GROUP BY d.id
        ORDER BY d.tier_requirement, d.domain_name
    ''').fetchall()

    conn.close()

    return render_template('tier_0/discover.html',
                          categories=categories,
                          domains=domains)


# ==============================================================================
# POST READING (PUBLIC)
# ==============================================================================

@tier_0.route('/post/<slug>')
def read_post(slug):
    """
    Read individual post - Public access

    No login required
    Show tier unlock prompt if viewing tier 1+ domain
    """
    conn = get_db()

    post = conn.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.published_at,
            u.username,
            u.display_name,
            u.bio,
            d.domain_name,
            d.tier_requirement
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN domains d ON p.domain_id = d.id
        WHERE p.slug = ?
    ''', (slug,)).fetchone()

    if not post:
        return render_template('error.html', message='Post not found'), 404

    # Get related posts (same category)
    related = conn.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            d.domain_name
        FROM posts p
        LEFT JOIN domains d ON p.domain_id = d.id
        WHERE p.category = ? AND p.slug != ?
        ORDER BY p.published_at DESC
        LIMIT 5
    ''', (post['category'] if 'category' in post.keys() else None, slug)).fetchall()

    conn.close()

    # Check if user needs to unlock tier to comment
    user_tier = session.get('tier', 0)
    can_comment = user_tier >= 1  # Tier 1+ can comment

    return render_template('tier_0/post.html',
                          post=post,
                          related=related,
                          can_comment=can_comment)


@tier_0.route('/category/<category>')
def browse_category(category):
    """
    Browse posts by category

    Public, no login required
    """
    conn = get_db()

    posts = conn.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.published_at,
            u.username,
            u.display_name,
            d.domain_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN domains d ON p.domain_id = d.id
        WHERE p.category = ?
        ORDER BY p.published_at DESC
    ''', (category,)).fetchall()

    conn.close()

    return render_template('tier_0/category.html',
                          category=category,
                          posts=posts)


@tier_0.route('/search')
def search():
    """
    Search all public content

    No login required
    """
    query = request.args.get('q', '')

    if not query:
        return render_template('tier_0/search.html', results=[], query='')

    conn = get_db()

    # Simple full-text search (SQLite FTS would be better for production)
    results = conn.execute('''
        SELECT
            p.id,
            p.title,
            p.slug,
            p.content,
            p.published_at,
            u.username,
            d.domain_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN domains d ON p.domain_id = d.id
        WHERE p.title LIKE ? OR p.content LIKE ?
        ORDER BY p.published_at DESC
        LIMIT 50
    ''', (f'%{query}%', f'%{query}%')).fetchall()

    conn.close()

    return render_template('tier_0/search.html',
                          results=results,
                          query=query)


# ==============================================================================
# PLATFORM INFORMATION
# ==============================================================================

@tier_0.route('/about')
def about():
    """
    About the platform - Explain the vision

    Public, no login required
    """
    return render_template('tier_0/about.html')


@tier_0.route('/tiers')
def tiers_explained():
    """
    Tier system explanation - Show unlock roadmap

    Public, no login required
    Shows what you get at each tier
    """

    tier_info = {
        0: {
            'name': 'Entry (FREE)',
            'domain': 'soulfra.com',
            'requirements': 'None',
            'actions': ['Browse', 'Read content', 'View comments'],
            'ownership': '0%',
            'revenue': 'N/A'
        },
        1: {
            'name': 'Commenter',
            'domains': ['soulfra.com', 'deathtodata.com', 'calriven.com'],
            'requirements': 'Star 1 GitHub repo',
            'actions': ['Comment', 'Leave reviews', 'Submit ideas', 'Voice memos'],
            'ownership': '5% base + 2% per domain',
            'revenue': '$0-50/month'
        },
        2: {
            'name': 'Contributor',
            'domains': ['All foundation domains', '1 creative domain (choose)'],
            'requirements': 'Star 2+ repos, Post 5+ comments',
            'actions': ['Post content', 'Create threads', 'Voice-to-blog', 'Moderate'],
            'ownership': '7% base + 5% per domain',
            'revenue': '$50-500/month'
        },
        3: {
            'name': 'Creator',
            'domains': ['All previous + daily rotation domain'],
            'requirements': 'Star 10+ repos OR 50+ public repos',
            'actions': ['Full blog creation', 'Moderate comments', 'Admin features', 'Voice-to-pitch-deck'],
            'ownership': '10% base + 10% per domain',
            'revenue': '$500-5,000/month'
        },
        4: {
            'name': 'VIP',
            'domains': ['ALL 50+ domains + premium selection'],
            'requirements': '100+ repos + 50+ followers',
            'actions': ['Full admin', 'Revenue sharing', 'Domain selection', 'API access'],
            'ownership': '25% base + 25% per domain',
            'revenue': '$5,000-50,000+/month'
        }
    }

    return render_template('tier_0/tiers.html', tier_info=tier_info)


@tier_0.route('/domains')
def domains_showcase():
    """
    Available domains showcase - See what's possible

    Public, no login required
    """
    conn = get_db()

    # Get all domains grouped by tier
    domains = conn.execute('''
        SELECT
            d.domain_name,
            d.tier_requirement,
            d.category,
            COUNT(p.id) as post_count
        FROM domains d
        LEFT JOIN posts p ON d.id = p.domain_id
        GROUP BY d.id
        ORDER BY d.tier_requirement, d.domain_name
    ''').fetchall()

    conn.close()

    # Group by tier
    tier_domains = {0: [], 1: [], 2: [], 3: [], 4: []}
    for domain in domains:
        tier = domain['tier_requirement']
        if tier in tier_domains:
            tier_domains[tier].append(domain)

    return render_template('tier_0/domains.html', tier_domains=tier_domains)


# ==============================================================================
# GITHUB OAUTH (TIER UNLOCKING)
# ==============================================================================

@tier_0.route('/github-login')
def github_login():
    """
    Start GitHub OAuth flow

    User clicks "Unlock Tiers" → redirects to GitHub
    """

    # Check if already logged in
    if 'user_id' in session:
        return redirect(url_for('tier_0.dashboard'))

    faucet = GitHubFaucet()

    # Generate auth URL (user_id will be created after callback)
    auth_url = faucet.get_auth_url(state='tier_unlock')

    return redirect(auth_url)


@tier_0.route('/github-callback')
def github_callback():
    """
    GitHub OAuth callback - Process tier assignment

    GitHub redirects here with code
    Exchange code for access token
    Fetch GitHub profile
    Calculate tier
    Create/update user
    """

    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return render_template('error.html', message='GitHub authentication failed'), 400

    faucet = GitHubFaucet()

    # Exchange code for access token and get user data
    result = faucet.process_callback(code)

    if 'error' in result:
        return render_template('error.html', message=result['error']), 400

    # Result contains: api_key, tier, github_username, github_data
    github_username = result['github_username']
    tier = result['tier']
    api_key = result['api_key']
    github_data = result['github_data']

    # Create or update user in database
    conn = get_db()

    # Check if user exists
    user = conn.execute(
        'SELECT id FROM users WHERE username = ?',
        (github_username,)
    ).fetchone()

    if user:
        user_id = user['id']
    else:
        # Create new user
        cursor = conn.execute('''
            INSERT INTO users (username, email, password_hash, display_name)
            VALUES (?, ?, ?, ?)
        ''', (
            github_username,
            f"{github_username}@github.placeholder",  # Placeholder email
            'github_oauth',  # No password for OAuth users
            github_data.get('name', github_username)
        ))
        user_id = cursor.lastrowid

    # Store GitHub profile
    conn.execute('''
        INSERT INTO github_profiles (
            user_id, github_username, github_id,
            total_repos, total_stars, total_followers,
            api_key, tier
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            total_repos = excluded.total_repos,
            total_stars = excluded.total_stars,
            total_followers = excluded.total_followers,
            api_key = excluded.api_key,
            tier = excluded.tier,
            last_synced = CURRENT_TIMESTAMP
    ''', (
        user_id,
        github_username,
        github_data['id'],
        github_data.get('repos', 0),
        github_data.get('stars', 0),
        github_data.get('followers', 0),
        api_key,
        tier
    ))

    conn.commit()
    conn.close()

    # Set session
    session['user_id'] = user_id
    session['username'] = github_username
    session['tier'] = tier

    # Redirect to dashboard
    return redirect(url_for('tier_0.dashboard'))


@tier_0.route('/dashboard')
def dashboard():
    """
    User dashboard - Show ownership, unlocked domains, stats

    Requires login (GitHub OAuth)
    """

    if 'user_id' not in session:
        return redirect(url_for('tier_0.github_login'))

    user_id = session['user_id']

    # Get ownership summary
    summary = get_user_ownership_summary(user_id)

    # Get unlocked domains
    unlocked = get_unlocked_domains(user_id)

    return render_template('tier_0/dashboard.html',
                          summary=summary,
                          unlocked=unlocked)


@tier_0.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('tier_0.homepage'))


# ==============================================================================
# API ENDPOINTS (READ-ONLY)
# ==============================================================================

@tier_0.route('/api/tiers')
def api_tiers():
    """
    API endpoint for tier information

    Public, no auth required
    """
    tier_info = {
        0: {'name': 'Entry', 'ownership_base': 0.0},
        1: {'name': 'Commenter', 'ownership_base': 5.0},
        2: {'name': 'Contributor', 'ownership_base': 7.0},
        3: {'name': 'Creator', 'ownership_base': 10.0},
        4: {'name': 'VIP', 'ownership_base': 25.0}
    }

    return jsonify(tier_info)


@tier_0.route('/api/domains')
def api_domains():
    """
    API endpoint for all domains

    Public, no auth required
    """
    conn = get_db()

    domains = conn.execute('''
        SELECT
            domain_name,
            tier_requirement,
            category
        FROM domains
        WHERE active = 1
        ORDER BY tier_requirement, domain_name
    ''').fetchall()

    conn.close()

    return jsonify([dict(d) for d in domains])


@tier_0.route('/api/stats')
def api_stats():
    """
    Platform stats

    Public, no auth required
    """
    conn = get_db()

    stats = {
        'total_posts': conn.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count'],
        'total_users': conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
        'total_domains': conn.execute('SELECT COUNT(*) as count FROM domains WHERE active = 1').fetchone()['count'],
        'total_comments': conn.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']
    }

    conn.close()

    return jsonify(stats)


# ==============================================================================
# EXPORTS
# ==============================================================================

def register_tier_0_routes(app):
    """
    Register tier 0 blueprint with Flask app

    Usage in app.py:
        from tier_0_routes import register_tier_0_routes
        register_tier_0_routes(app)
    """
    app.register_blueprint(tier_0)


if __name__ == '__main__':
    print("Tier 0 routes defined:")
    print("  GET  /")
    print("  GET  /discover")
    print("  GET  /post/<slug>")
    print("  GET  /category/<category>")
    print("  GET  /search")
    print("  GET  /about")
    print("  GET  /tiers")
    print("  GET  /domains")
    print("  GET  /github-login")
    print("  GET  /github-callback")
    print("  GET  /dashboard")
    print("  GET  /logout")
    print()
    print("API:")
    print("  GET  /api/tiers")
    print("  GET  /api/domains")
    print("  GET  /api/stats")
