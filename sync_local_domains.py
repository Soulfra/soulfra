#!/usr/bin/env python3
"""
Sync Local Domains - The Homebrew Mirror System

Reads your local domain "formulas" from output/ and syncs to database:
- Parses README.md files
- Extracts wordmaps
- Stores in domain_wordmaps table
- Generates metadata (colors, avatars, etc.)

Like: `brew tap` but for your domains

Usage:
    python3 sync_local_domains.py                  # Sync all domains
    python3 sync_local_domains.py --domain soulfra # Sync one domain
    python3 sync_local_domains.py --list           # List local domains
"""

import os
import json
from pathlib import Path
from database import get_db
from github_readme_parser import parse_readme_to_wordmap
from wordmap_css_generator import word_to_color

# Your domain "formulas" directory (like /opt/homebrew/Library/Taps/)
DOMAINS_DIR = Path(__file__).parent / 'output'

# Your 4 founder domains
FOUNDER_DOMAINS = ['soulfra', 'cringeproof', 'calriven', 'deathtodata']

def discover_local_domains():
    """
    Discover all domain folders in output/
    Returns list of domain names
    """
    if not DOMAINS_DIR.exists():
        print(f"❌ Domains directory not found: {DOMAINS_DIR}")
        return []

    domains = []
    for item in DOMAINS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it has a README
            readme_path = item / 'README.md'
            if readme_path.exists():
                domains.append(item.name)

    return domains

def read_domain_readme(domain_name):
    """
    Read README.md for a domain
    Returns content as string, or None if not found
    """
    readme_path = DOMAINS_DIR / domain_name / 'README.md'

    if not readme_path.exists():
        return None

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {readme_path}: {e}")
        return None

def read_domain_cname(domain_name):
    """
    Read CNAME file for a domain (the actual domain it maps to)
    Returns domain string like "soulfra.com" or None
    """
    cname_path = DOMAINS_DIR / domain_name / 'CNAME'

    if not cname_path.exists():
        return f"{domain_name}.com"  # Default

    try:
        with open(cname_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"⚠️  Could not read CNAME for {domain_name}: {e}")
        return f"{domain_name}.com"

def sync_domain_to_db(domain_name):
    """
    Sync a single domain from local files to database

    Steps:
    1. Read README.md
    2. Extract wordmap
    3. Generate colors from top words
    4. Store in domain_wordmaps table
    5. Update domain metadata

    Returns: dict with sync results
    """
    print(f"\n🔄 Syncing {domain_name}...")

    # Read README
    readme_content = read_domain_readme(domain_name)
    if not readme_content:
        return {
            'success': False,
            'domain': domain_name,
            'error': 'No README.md found'
        }

    # Parse to wordmap
    wordmap = parse_readme_to_wordmap(readme_content)

    if not wordmap:
        return {
            'success': False,
            'domain': domain_name,
            'error': 'No valid words in README'
        }

    # Get actual domain name from CNAME
    actual_domain = read_domain_cname(domain_name)

    # Store in database
    db = get_db()
    wordmap_json = json.dumps(wordmap)

    # Check if exists
    existing = db.execute(
        'SELECT domain FROM domain_wordmaps WHERE domain = ?',
        (domain_name,)
    ).fetchone()

    if existing:
        db.execute('''
            UPDATE domain_wordmaps
            SET wordmap_json = ?, last_updated = CURRENT_TIMESTAMP
            WHERE domain = ?
        ''', (wordmap_json, domain_name))
        action = 'updated'
    else:
        db.execute('''
            INSERT INTO domain_wordmaps (domain, wordmap_json, contributor_count, total_recordings)
            VALUES (?, ?, 0, 0)
        ''', (domain_name, wordmap_json))
        action = 'created'

    db.commit()

    # Generate metadata
    top_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:5]
    colors = [word_to_color(word) for word, count in top_words]

    result = {
        'success': True,
        'domain': domain_name,
        'actual_domain': actual_domain,
        'action': action,
        'total_words': sum(wordmap.values()),
        'unique_words': len(wordmap),
        'top_words': [{'word': w, 'count': c, 'color': word_to_color(w)} for w, c in top_words],
        'primary_color': colors[0] if colors else '#000000',
        'is_founder': domain_name in FOUNDER_DOMAINS
    }

    print(f"   ✅ {action.capitalize()}: {domain_name}")
    print(f"   📊 {result['total_words']} total words, {result['unique_words']} unique")
    print(f"   🎨 Primary color: {result['primary_color']}")
    print(f"   🔝 Top words: {', '.join([w['word'] for w in result['top_words'][:3]])}")

    return result

def sync_all_domains():
    """
    Sync all discovered domains to database
    Returns list of results
    """
    domains = discover_local_domains()

    if not domains:
        print("❌ No domains found in output/")
        return []

    print(f"📦 Found {len(domains)} local domains: {', '.join(domains)}")

    results = []
    for domain in domains:
        result = sync_domain_to_db(domain)
        results.append(result)

    return results

def list_local_domains():
    """
    List all local domains with their status
    """
    domains = discover_local_domains()

    if not domains:
        print("❌ No domains found in output/")
        return

    print(f"\n📦 Local Domains ({len(domains)}):\n")

    db = get_db()

    for domain in domains:
        # Check if in database
        in_db = db.execute(
            'SELECT last_updated FROM domain_wordmaps WHERE domain = ?',
            (domain,)
        ).fetchone()

        # Check if founder domain
        is_founder = "🔒 FOUNDER" if domain in FOUNDER_DOMAINS else ""

        # Get CNAME
        cname = read_domain_cname(domain)

        # Get README word count
        readme = read_domain_readme(domain)
        word_count = len(readme.split()) if readme else 0

        status = f"✅ Synced ({in_db['last_updated']})" if in_db else "⚠️  Not synced"

        print(f"  {domain:20} → {cname:25} {status:30} {word_count:5} words {is_founder}")

def main():
    import sys

    if '--list' in sys.argv:
        list_local_domains()
    elif '--domain' in sys.argv:
        idx = sys.argv.index('--domain')
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]
            result = sync_domain_to_db(domain)
            print(f"\n{'='*60}")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Usage: python3 sync_local_domains.py --domain DOMAIN_NAME")
    else:
        # Sync all
        results = sync_all_domains()

        # Summary
        print(f"\n{'='*60}")
        print("📊 Sync Summary:")
        print(f"   Total domains: {len(results)}")
        print(f"   Successful: {sum(1 for r in results if r['success'])}")
        print(f"   Failed: {sum(1 for r in results if not r['success'])}")
        print(f"   Founder domains: {sum(1 for r in results if r.get('is_founder'))}")

if __name__ == '__main__':
    main()
