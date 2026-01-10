#!/usr/bin/env python3
"""
Analyze soulfra-simple system to understand what we have
"""

import sqlite3
import re
import requests

DB_FILE = "soulfra.db"
APP_FILE = "app.py"

def analyze_database():
    """Get all tables and their record counts"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get all tables
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    table_info = {}
    for (table_name,) in tables:
        if table_name == 'sqlite_sequence':
            continue
        count = cursor.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
        table_info[table_name] = count

    conn.close()
    return table_info

def analyze_routes():
    """Extract all routes from app.py"""
    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Find all @app.route declarations
    route_pattern = r"@app\.route\('([^']+)'(?:, methods=\['([^']+)'\])?\)"
    routes = re.findall(route_pattern, content)

    route_info = {}
    for path, method in routes:
        method = method if method else 'GET'
        if path not in route_info:
            route_info[path] = []
        route_info[path].append(method)

    return route_info

def categorize_routes(routes):
    """Group routes by category"""
    categories = {
        'API': [],
        'QR System': [],
        'Dashboard/Admin': [],
        'User Pages': [],
        'Voice/AI': [],
        'Domains': [],
        'Other': []
    }

    for path, methods in routes.items():
        if path.startswith('/api'):
            categories['API'].append((path, methods))
        elif '/qr' in path:
            categories['QR System'].append((path, methods))
        elif '/dashboard' in path or '/debug' in path:
            categories['Dashboard/Admin'].append((path, methods))
        elif '/me' in path or path == '/':
            categories['User Pages'].append((path, methods))
        elif 'voice' in path or 'ai' in path or 'narrative' in path:
            categories['Voice/AI'].append((path, methods))
        elif '/domains' in path or '/<domain_slug>' in path:
            categories['Domains'].append((path, methods))
        else:
            categories['Other'].append((path, methods))

    return categories

def fetch_github_repos():
    """Get all repos from github.com/soulfra"""
    try:
        response = requests.get('https://api.github.com/users/soulfra/repos?per_page=100')
        if response.status_code == 200:
            repos = response.json()
            return [(r['name'], r.get('description', 'No description'), r.get('language')) for r in repos]
        else:
            return []
    except:
        return []

def generate_map():
    """Generate complete system map"""
    print("=" * 80)
    print("SOULFRA-SIMPLE SYSTEM MAP")
    print("=" * 80)

    # Database
    print("\n📊 DATABASE (soulfra.db)")
    print("-" * 80)
    tables = analyze_database()
    total_records = sum(tables.values())
    print(f"Total tables: {len(tables)}")
    print(f"Total records: {total_records}\n")

    for table, count in sorted(tables.items(), key=lambda x: x[1], reverse=True):
        print(f"  {table:40} {count:>6} records")

    # Routes
    print("\n🌐 ROUTES (app.py)")
    print("-" * 80)
    routes = analyze_routes()
    print(f"Total routes: {len(routes)}\n")

    categories = categorize_routes(routes)
    for category, route_list in categories.items():
        if route_list:
            print(f"\n  {category} ({len(route_list)} routes):")
            for path, methods in sorted(route_list)[:10]:  # Show first 10
                methods_str = ', '.join(methods)
                print(f"    {path:50} [{methods_str}]")
            if len(route_list) > 10:
                print(f"    ... and {len(route_list) - 10} more")

    # GitHub
    print("\n🐙 GITHUB REPOS (github.com/soulfra)")
    print("-" * 80)
    repos = fetch_github_repos()
    if repos:
        print(f"Total repos: {len(repos)}\n")
        for name, desc, lang in repos[:15]:
            lang_str = f"[{lang}]" if lang else "[?]"
            print(f"  {lang_str:12} {name:40}")
            if desc and desc != 'None':
                print(f"             {desc[:60]}")
        if len(repos) > 15:
            print(f"\n  ... and {len(repos) - 15} more repos")
    else:
        print("  Could not fetch GitHub repos")

    print("\n" + "=" * 80)
    print(f"System: soulfra-simple | Port: 5001 | Status: RUNNING")
    print("=" * 80)

if __name__ == "__main__":
    generate_map()
