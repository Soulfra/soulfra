#!/usr/bin/env python3
"""
Simple Domain Import - Just paste domain names, Ollama does the rest!

Usage:
    python3 import_domains_simple.py

What this does:
1. Reads domain names from domains-simple.txt
2. For each domain, Ollama analyzes and suggests:
   - Category (cooking, tech, privacy, etc.)
   - Emoji
   - Brand type (blog, game, platform, etc.)
   - Tagline
   - Target audience
   - Purpose
3. Shows you a preview of all suggestions
4. You approve in bulk
5. Imports to database

No complex CSV needed!
"""

import sys
import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path

# Config
DOMAIN_FILE = "domains-simple.txt"
DB_FILE = "soulfra.db"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Valid categories
VALID_CATEGORIES = ['cooking', 'tech', 'privacy', 'business', 'health', 'art', 'education', 'gaming', 'finance', 'local']

def read_domains():
    """Read domain names from text file"""
    if not Path(DOMAIN_FILE).exists():
        print(f"❌ Error: {DOMAIN_FILE} not found")
        print(f"   Create it and add your domain names (one per line)")
        sys.exit(1)

    with open(DOMAIN_FILE, 'r') as f:
        lines = f.readlines()

    # Filter out comments and empty lines
    domains = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Basic validation
            if '.' in line and len(line) > 3:
                domains.append(line.lower())

    return domains

def analyze_domain_with_ollama(domain):
    """Ask Ollama to analyze a domain and suggest details"""

    prompt = f"""Analyze this domain and suggest details for a website database.

Domain: {domain}

Based on the domain name, suggest:
1. Category (choose ONE from: cooking, tech, privacy, business, health, art, education, gaming, finance, local)
2. Brand name (readable version of domain)
3. Brand type (choose ONE from: blog, game, community, platform, directory)
4. Emoji (one emoji that represents this brand)
5. Tagline (short catchy phrase, 3-7 words)
6. Target audience (who visits this site?)
7. Purpose (what does this site do?)

Respond ONLY with valid JSON in this exact format:
{{
  "category": "tech",
  "name": "My Site",
  "brand_type": "blog",
  "emoji": "🚀",
  "tagline": "Short catchy phrase",
  "target_audience": "Developers and tech enthusiasts",
  "purpose": "Tutorials and code examples"
}}

JSON response:"""

    try:
        # Call Ollama
        data = json.dumps({
            'model': 'llama3.2:3b',
            'prompt': prompt,
            'stream': False,
            'format': 'json'
        }).encode('utf-8')

        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        result = urllib.request.urlopen(req, timeout=60)
        response = json.loads(result.read())

        # Parse Ollama's response
        suggested = json.loads(response['response'])

        # Validate category
        if suggested.get('category') not in VALID_CATEGORIES:
            suggested['category'] = 'tech'  # Default fallback

        # Ensure all fields present
        suggested.setdefault('name', domain.split('.')[0].title())
        suggested.setdefault('brand_type', 'blog')
        suggested.setdefault('emoji', '🌐')
        suggested.setdefault('tagline', '')
        suggested.setdefault('target_audience', '')
        suggested.setdefault('purpose', '')

        return suggested

    except Exception as e:
        print(f"⚠️  Ollama error for {domain}: {e}")
        print(f"   Using defaults...")

        # Fallback defaults if Ollama fails
        return {
            'category': 'tech',
            'name': domain.split('.')[0].title(),
            'brand_type': 'blog',
            'emoji': '🌐',
            'tagline': '',
            'target_audience': '',
            'purpose': ''
        }

def show_preview(domain_data):
    """Show preview of all suggested domain details"""
    print("\n" + "="*80)
    print("📋 PREVIEW OF SUGGESTED DOMAIN DETAILS")
    print("="*80 + "\n")

    for i, data in enumerate(domain_data, 1):
        print(f"{i}. {data['emoji']} {data['name']} ({data['domain']})")
        print(f"   Category: {data['category']}")
        print(f"   Type: {data['brand_type']}")
        print(f"   Tagline: {data['tagline']}")
        print(f"   Audience: {data['target_audience']}")
        print(f"   Purpose: {data['purpose']}")
        print()

    print("="*80)

def import_domains():
    """Main import process"""

    # Check Ollama is running
    try:
        urllib.request.urlopen('http://localhost:11434/api/version', timeout=5)
    except:
        print("❌ Error: Ollama is not running")
        print("   Start it with: ollama serve")
        print("   Or install from: https://ollama.ai")
        sys.exit(1)

    # Read domains
    print("📖 Reading domains from domains-simple.txt...")
    domains = read_domains()

    if not domains:
        print("❌ No domains found in file")
        print("   Add domain names (one per line) and try again")
        sys.exit(1)

    print(f"   Found {len(domains)} domains\n")

    # Analyze each domain with Ollama
    print("🤖 Analyzing domains with Ollama...")
    print("   (This may take 30-60 seconds per domain)\n")

    domain_data = []
    for i, domain in enumerate(domains, 1):
        print(f"   [{i}/{len(domains)}] Analyzing {domain}...", end=' ')

        suggested = analyze_domain_with_ollama(domain)
        suggested['domain'] = domain
        domain_data.append(suggested)

        print(f"✅ {suggested['name']} ({suggested['category']})")

    # Show preview
    show_preview(domain_data)

    # Ask for approval
    print("\nDo you want to import these domains? (y/n): ", end='')
    response = input().strip().lower()

    if response != 'y':
        print("❌ Import cancelled")
        sys.exit(0)

    # Import to database
    print("\n📥 Importing to database...")

    db = sqlite3.connect(DB_FILE)
    cursor = db.cursor()

    imported = 0
    skipped = 0

    for data in domain_data:
        domain = data['domain']
        name = data['name']
        slug = domain.replace('.com', '').replace('.', '-').lower()

        # Check if already exists
        existing = cursor.execute(
            'SELECT id FROM brands WHERE slug = ? OR domain = ?',
            (slug, domain)
        ).fetchone()

        if existing:
            print(f"⏭️  Skipping {name} (already exists)")
            skipped += 1
            continue

        # Insert
        try:
            cursor.execute('''
                INSERT INTO brands (
                    name, slug, domain, category, tier, emoji, brand_type, tagline, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (
                name,
                slug,
                domain,
                data['category'],
                'foundation',  # Default tier
                data['emoji'],
                data['brand_type'],
                data['tagline']
            ))

            imported += 1
            print(f"✅ Imported: {name} ({domain})")

        except sqlite3.Error as e:
            print(f"❌ Error importing {name}: {e}")
            skipped += 1

    # Commit
    db.commit()
    db.close()

    # Summary
    print("\n" + "="*80)
    print("📊 Import Summary:")
    print(f"   Imported: {imported}")
    print(f"   Skipped:  {skipped}")
    print(f"   Total:    {imported + skipped}")
    print("="*80)

    if imported > 0:
        print(f"\n✅ Success! {imported} domains imported to database")
        print(f"   Visit: http://localhost:5001/admin/domains")
        print(f"   Or: http://localhost:5001/control")

if __name__ == '__main__':
    import_domains()
