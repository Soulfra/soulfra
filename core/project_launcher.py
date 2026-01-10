#!/usr/bin/env python3
"""
Project Launcher - Announce and Track Projects Across Domains

Connects projects (like CringeProof) with:
- Primary domain (where it lives)
- GitHub repo (where code lives)
- Contributor tracking
- Launch announcements
- Cross-domain partnerships

Run: python3 project_launcher.py --help
"""

import sys
import argparse
from pathlib import Path
from database import get_db
from datetime import datetime
import json

# =============================================================================
# PROJECT LOADING
# =============================================================================

def load_projects_from_file():
    """
    Load projects from projects.txt

    Format: project_slug | primary_domain | github_repo | status | tagline

    Returns:
        List of project dicts
    """
    projects_file = Path("projects.txt")

    if not projects_file.exists():
        print("❌ projects.txt not found")
        return []

    projects = []
    with open(projects_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    owner, repo = parts[2].split('/') if '/' in parts[2] else ('', parts[2])

                    projects.append({
                        'slug': parts[0],
                        'primary_domain': parts[1],
                        'github_owner': owner,
                        'github_repo': repo,
                        'status': parts[3],
                        'tagline': parts[4]
                    })

    return projects


# =============================================================================
# DATABASE SCHEMA
# =============================================================================

def create_project_tables():
    """
    Create database tables for project tracking

    Tables:
        - projects: All projects across all domains
        - project_launches: Launch announcements
        - project_contributors: Contributors and their rewards
        - project_partnerships: Cross-domain project partnerships
    """
    db = get_db()

    # Projects table
    db.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            tagline TEXT,
            primary_domain TEXT NOT NULL,
            github_owner TEXT NOT NULL,
            github_repo TEXT NOT NULL,
            status TEXT DEFAULT 'planning',
            launch_date TIMESTAMP,
            build_phase_end TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Project launches table
    db.execute('''
        CREATE TABLE IF NOT EXISTS project_launches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            announcement_url TEXT,
            github_url TEXT,
            launch_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    # Project contributors table
    db.execute('''
        CREATE TABLE IF NOT EXISTS project_contributors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            github_username TEXT NOT NULL,
            contribution_type TEXT NOT NULL,
            contribution_count INTEGER DEFAULT 0,
            ownership_earned REAL DEFAULT 0.0,
            last_contribution TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            UNIQUE(project_id, github_username)
        )
    ''')

    # Project partnerships table (for cross-domain promotions)
    db.execute('''
        CREATE TABLE IF NOT EXISTS project_partnerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            partner_domain TEXT NOT NULL,
            partnership_type TEXT NOT NULL,
            revenue_share REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Project tables created successfully")


# =============================================================================
# PROJECT MANAGEMENT
# =============================================================================

def sync_projects_from_file():
    """
    Sync projects from projects.txt into database

    Returns:
        Number of projects synced
    """
    projects = load_projects_from_file()

    if not projects:
        print("❌ No projects found in projects.txt")
        return 0

    db = get_db()
    synced = 0

    for proj in projects:
        # Check if project exists
        existing = db.execute('''
            SELECT id FROM projects WHERE slug = ?
        ''', (proj['slug'],)).fetchone()

        if existing:
            # Update existing
            db.execute('''
                UPDATE projects
                SET primary_domain = ?,
                    github_owner = ?,
                    github_repo = ?,
                    status = ?,
                    tagline = ?
                WHERE slug = ?
            ''', (proj['primary_domain'], proj['github_owner'], proj['github_repo'],
                  proj['status'], proj['tagline'], proj['slug']))
            print(f"  ✅ Updated: {proj['slug']}")
        else:
            # Insert new
            # Convert slug to name (cringeproof -> CringeProof)
            name = proj['slug'].replace('-', ' ').title()

            db.execute('''
                INSERT INTO projects
                (slug, name, primary_domain, github_owner, github_repo, status, tagline)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (proj['slug'], name, proj['primary_domain'], proj['github_owner'],
                  proj['github_repo'], proj['status'], proj['tagline']))
            print(f"  ✅ Added: {proj['slug']}")

        synced += 1

    db.commit()
    db.close()

    return synced


def list_projects(status=None, domain=None):
    """
    List all projects

    Args:
        status: Filter by status (optional)
        domain: Filter by primary domain (optional)

    Returns:
        List of project dicts
    """
    db = get_db()

    query = 'SELECT * FROM projects WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status)

    if domain:
        query += ' AND primary_domain = ?'
        params.append(domain)

    query += ' ORDER BY created_at DESC'

    rows = db.execute(query, params).fetchall()
    projects = [dict(row) for row in rows]

    db.close()

    return projects


def create_launch_announcement(project_slug, launch_type='initial',
                               description=None):
    """
    Create a launch announcement for a project

    Args:
        project_slug: Project slug
        launch_type: Type of launch ('initial', 'beta', 'v1', 'update')
        description: Launch description

    Returns:
        Launch ID
    """
    db = get_db()

    # Get project
    project = db.execute('''
        SELECT * FROM projects WHERE slug = ?
    ''', (project_slug,)).fetchone()

    if not project:
        print(f"❌ Project not found: {project_slug}")
        return None

    project_id = project['id']

    # Generate URLs
    announcement_url = f"https://{project['github_owner']}.github.io/{project['primary_domain'].split('.')[0]}/{project_slug}"
    github_url = f"https://github.com/{project['github_owner']}/{project['github_repo']}"

    # Create launch
    cursor = db.execute('''
        INSERT INTO project_launches
        (project_id, announcement_url, github_url, launch_type, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (project_id, announcement_url, github_url, launch_type, description))

    launch_id = cursor.lastrowid

    # Update project launch_date if this is initial launch
    if launch_type == 'initial':
        db.execute('''
            UPDATE projects
            SET launch_date = datetime('now')
            WHERE id = ?
        ''', (project_id,))

    db.commit()
    db.close()

    print(f"✅ Launch announcement created for {project['name']}")
    print(f"   Announcement: {announcement_url}")
    print(f"   GitHub: {github_url}")
    print(f"   Type: {launch_type}")

    return launch_id


def add_cross_domain_partnership(project_slug, partner_domain,
                                 partnership_type='promotion', revenue_share=0.0):
    """
    Add a cross-domain partnership for a project

    Example: CringeProof (Soulfra) partners with DeathToData

    Args:
        project_slug: Project slug
        partner_domain: Partner domain (e.g., 'deathtodata.com')
        partnership_type: Type ('promotion', 'integration', 'revenue_share')
        revenue_share: Revenue share percentage

    Returns:
        Partnership ID
    """
    db = get_db()

    # Get project
    project = db.execute('''
        SELECT * FROM projects WHERE slug = ?
    ''', (project_slug,)).fetchone()

    if not project:
        print(f"❌ Project not found: {project_slug}")
        return None

    # Create partnership
    cursor = db.execute('''
        INSERT INTO project_partnerships
        (project_id, partner_domain, partnership_type, revenue_share)
        VALUES (?, ?, ?, ?)
    ''', (project['id'], partner_domain, partnership_type, revenue_share))

    partnership_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Partnership created: {project['name']} ↔ {partner_domain}")
    print(f"   Type: {partnership_type}")
    if revenue_share > 0:
        print(f"   Revenue Share: {revenue_share}%")

    return partnership_id


def get_project_ecosystem(project_slug):
    """
    Get complete project ecosystem

    Args:
        project_slug: Project slug

    Returns:
        Dict with project, launches, contributors, partnerships
    """
    db = get_db()

    # Get project
    project = db.execute('''
        SELECT * FROM projects WHERE slug = ?
    ''', (project_slug,)).fetchone()

    if not project:
        return None

    project_id = project['id']

    # Get launches
    launches = db.execute('''
        SELECT * FROM project_launches
        WHERE project_id = ?
        ORDER BY created_at DESC
    ''', (project_id,)).fetchall()

    # Get contributors
    contributors = db.execute('''
        SELECT * FROM project_contributors
        WHERE project_id = ?
        ORDER BY ownership_earned DESC
    ''', (project_id,)).fetchall()

    # Get partnerships
    partnerships = db.execute('''
        SELECT * FROM project_partnerships
        WHERE project_id = ?
    ''', (project_id,)).fetchall()

    db.close()

    return {
        'project': dict(project),
        'launches': [dict(l) for l in launches],
        'contributors': [dict(c) for c in contributors],
        'partnerships': [dict(p) for p in partnerships]
    }


# =============================================================================
# CLI COMMANDS
# =============================================================================

def cmd_sync(args):
    """CLI: Sync projects from projects.txt"""
    print("📦 Syncing projects from projects.txt...\n")
    count = sync_projects_from_file()
    print(f"\n✅ Synced {count} projects")


def cmd_list(args):
    """CLI: List all projects"""
    projects = list_projects(status=args.status, domain=args.domain)

    if not projects:
        print("No projects found")
        return

    print(f"\n📋 Found {len(projects)} project(s):\n")

    for p in projects:
        print(f"  [{p['slug']}] {p['name']}")
        print(f"      Domain: {p['primary_domain']}")
        print(f"      GitHub: {p['github_owner']}/{p['github_repo']}")
        print(f"      Status: {p['status']}")
        print(f"      {p['tagline']}")
        print()


def cmd_launch(args):
    """CLI: Create launch announcement"""
    launch_id = create_launch_announcement(
        project_slug=args.project,
        launch_type=args.type,
        description=args.description
    )

    if launch_id:
        print(f"\n✅ Launch {launch_id} created successfully")


def cmd_partner(args):
    """CLI: Add cross-domain partnership"""
    partnership_id = add_cross_domain_partnership(
        project_slug=args.project,
        partner_domain=args.domain,
        partnership_type=args.type,
        revenue_share=args.revenue_share
    )

    if partnership_id:
        print(f"\n✅ Partnership {partnership_id} created successfully")


def cmd_show(args):
    """CLI: Show complete project ecosystem"""
    ecosystem = get_project_ecosystem(args.project)

    if not ecosystem:
        print(f"❌ Project not found: {args.project}")
        return

    proj = ecosystem['project']

    print(f"\n📊 Project Ecosystem: {proj['name']}")
    print(f"{'='*70}")
    print(f"Slug: {proj['slug']}")
    print(f"Domain: {proj['primary_domain']}")
    print(f"GitHub: https://github.com/{proj['github_owner']}/{proj['github_repo']}")
    print(f"Status: {proj['status']}")
    print(f"Tagline: {proj['tagline']}")

    if proj['launch_date']:
        print(f"Launched: {proj['launch_date']}")

    print(f"\n📢 Launches ({len(ecosystem['launches'])}):")
    for launch in ecosystem['launches']:
        print(f"  • {launch['launch_type']}: {launch['announcement_url']}")

    print(f"\n👥 Contributors ({len(ecosystem['contributors'])}):")
    for contrib in ecosystem['contributors']:
        print(f"  • {contrib['github_username']}: {contrib['ownership_earned']:.2f}% ownership")
        print(f"    {contrib['contribution_count']} {contrib['contribution_type']}s")

    print(f"\n🤝 Partnerships ({len(ecosystem['partnerships'])}):")
    for partner in ecosystem['partnerships']:
        print(f"  • {partner['partner_domain']} ({partner['partnership_type']})")
        if partner['revenue_share'] > 0:
            print(f"    Revenue share: {partner['revenue_share']}%")


# =============================================================================
# MAIN CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Project Launcher System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Setup command
    parser_setup = subparsers.add_parser('setup', help='Create database tables')

    # Sync command
    parser_sync = subparsers.add_parser('sync', help='Sync from projects.txt')

    # List command
    parser_list = subparsers.add_parser('list', help='List projects')
    parser_list.add_argument('--status', help='Filter by status')
    parser_list.add_argument('--domain', help='Filter by domain')

    # Launch command
    parser_launch = subparsers.add_parser('launch', help='Create launch announcement')
    parser_launch.add_argument('project', help='Project slug')
    parser_launch.add_argument('--type', default='initial',
                              choices=['initial', 'beta', 'v1', 'update'],
                              help='Launch type')
    parser_launch.add_argument('--description', help='Launch description')

    # Partner command
    parser_partner = subparsers.add_parser('partner', help='Add cross-domain partnership')
    parser_partner.add_argument('project', help='Project slug')
    parser_partner.add_argument('domain', help='Partner domain')
    parser_partner.add_argument('--type', default='promotion',
                               choices=['promotion', 'integration', 'revenue_share'],
                               help='Partnership type')
    parser_partner.add_argument('--revenue-share', type=float, default=0.0,
                               help='Revenue share percentage')

    # Show command
    parser_show = subparsers.add_parser('show', help='Show project ecosystem')
    parser_show.add_argument('project', help='Project slug')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'setup':
        create_project_tables()
        return 0

    if args.command == 'sync':
        cmd_sync(args)
        return 0

    if args.command == 'list':
        cmd_list(args)
        return 0

    if args.command == 'launch':
        cmd_launch(args)
        return 0

    if args.command == 'partner':
        cmd_partner(args)
        return 0

    if args.command == 'show':
        cmd_show(args)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
