#!/usr/bin/env python3
"""
Competitor Content Scraper - "Steal Their Research, Laugh at Them"

Scrapes workflow documentation from competitor sites and converts them
into our universal workflow system.

Strategy:
1. Scrape competitor workflow guides (Notion, Airtable, monday.com, etc.)
2. Parse their workflow stages
3. Generate improved versions using our system
4. Embed in GitHub README with tracking
5. When they link to us → capture their audience
6. Promote our services to their readers

Usage:
    python3 competitor_content_scraper.py --url "https://competitor.com/workflow-guide"
    python3 competitor_content_scraper.py --auto  # Auto-scrape known competitors
"""

import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import re
from typing import List, Dict, Optional
from datetime import datetime
import argparse


# Competitor targets (known workflow documentation sites)
COMPETITOR_TARGETS = [
    {
        'name': 'Notion Templates',
        'url': 'https://www.notion.so/templates',
        'industry': 'productivity',
        'scrape_strategy': 'notion'
    },
    {
        'name': 'Airtable Universe',
        'url': 'https://www.airtable.com/universe',
        'industry': 'database',
        'scrape_strategy': 'airtable'
    },
    {
        'name': 'Monday.com Templates',
        'url': 'https://monday.com/templates',
        'industry': 'project-management',
        'scrape_strategy': 'monday'
    },
    {
        'name': 'Trello Templates',
        'url': 'https://trello.com/templates',
        'industry': 'kanban',
        'scrape_strategy': 'trello'
    },
    {
        'name': 'Asana Templates',
        'url': 'https://asana.com/templates',
        'industry': 'project-management',
        'scrape_strategy': 'asana'
    },
]


def scrape_workflow_from_url(url: str, strategy: str = 'generic') -> Optional[Dict]:
    """
    Scrape a workflow from a competitor URL

    Returns:
        {
            'name': 'Content Production Workflow',
            'source_url': 'https://competitor.com/workflow',
            'stages': ['Research', 'Draft', 'Edit', 'Publish'],
            'description': 'How to create content',
            'industry': 'content-creation'
        }
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        if strategy == 'notion':
            return scrape_notion_template(soup, url)
        elif strategy == 'airtable':
            return scrape_airtable_template(soup, url)
        elif strategy == 'monday':
            return scrape_monday_template(soup, url)
        elif strategy == 'trello':
            return scrape_trello_template(soup, url)
        elif strategy == 'asana':
            return scrape_asana_template(soup, url)
        else:
            return scrape_generic_workflow(soup, url)

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None


def scrape_generic_workflow(soup: BeautifulSoup, url: str) -> Dict:
    """
    Generic workflow scraper - looks for common patterns

    Searches for:
    - Ordered lists (ol/ul)
    - Step-by-step sections
    - Headers with numbers
    - Workflow diagrams
    """
    workflow = {
        'name': soup.find('title').text if soup.find('title') else 'Unnamed Workflow',
        'source_url': url,
        'stages': [],
        'description': '',
        'industry': 'unknown'
    }

    # Try to find description (first paragraph or meta description)
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        workflow['description'] = meta_desc.get('content', '')
    else:
        first_p = soup.find('p')
        if first_p:
            workflow['description'] = first_p.text.strip()[:200]

    # Look for ordered/numbered lists as workflow stages
    for ol in soup.find_all('ol'):
        stages = [li.text.strip() for li in ol.find_all('li')]
        if len(stages) >= 3 and len(stages) <= 15:
            workflow['stages'].extend(stages)

    # Look for headers with numbers (Step 1, Stage 2, etc.)
    step_pattern = re.compile(r'^(Step|Stage|Phase)\s+\d+', re.IGNORECASE)
    for header in soup.find_all(['h2', 'h3', 'h4']):
        if step_pattern.match(header.text):
            stage_name = re.sub(r'^(Step|Stage|Phase)\s+\d+:\s*', '', header.text, flags=re.IGNORECASE)
            workflow['stages'].append(stage_name.strip())

    # Deduplicate stages while preserving order
    seen = set()
    unique_stages = []
    for stage in workflow['stages']:
        if stage not in seen:
            seen.add(stage)
            unique_stages.append(stage)

    workflow['stages'] = unique_stages[:10]  # Limit to 10 stages max

    return workflow


def scrape_notion_template(soup: BeautifulSoup, url: str) -> Dict:
    """Scrape Notion template pages"""
    # Notion-specific scraping logic
    # (Notion templates usually have a specific DOM structure)
    return scrape_generic_workflow(soup, url)


def scrape_airtable_template(soup: BeautifulSoup, url: str) -> Dict:
    """Scrape Airtable Universe templates"""
    return scrape_generic_workflow(soup, url)


def scrape_monday_template(soup: BeautifulSoup, url: str) -> Dict:
    """Scrape Monday.com templates"""
    return scrape_generic_workflow(soup, url)


def scrape_trello_template(soup: BeautifulSoup, url: str) -> Dict:
    """Scrape Trello templates"""
    return scrape_generic_workflow(soup, url)


def scrape_asana_template(soup: BeautifulSoup, url: str) -> Dict:
    """Scrape Asana templates"""
    return scrape_generic_workflow(soup, url)


def save_scraped_workflow(workflow: Dict) -> int:
    """
    Save scraped workflow to database

    Returns workflow_template_id
    """
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    # Check if we already scraped this URL
    existing = db.execute('''
        SELECT id FROM scraped_competitor_workflows WHERE source_url = ?
    ''', (workflow['source_url'],)).fetchone()

    if existing:
        print(f"⚠️  Already scraped: {workflow['source_url']}")
        return existing['id']

    # Save to scraped_competitor_workflows table
    cursor = db.execute('''
        INSERT INTO scraped_competitor_workflows (
            name, source_url, stages, description, industry, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        workflow['name'],
        workflow['source_url'],
        json.dumps(workflow['stages']),
        workflow['description'],
        workflow['industry'],
        datetime.now()
    ))

    workflow_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Saved workflow: {workflow['name']} ({len(workflow['stages'])} stages)")
    return workflow_id


def convert_to_universal_workflow(workflow: Dict) -> Dict:
    """
    Convert scraped workflow to our universal workflow format
    with improvements and cross-promotions
    """
    # Infer industry from workflow name/description
    industry = infer_industry(workflow['name'], workflow['description'])

    # Generate slug
    slug = re.sub(r'[^a-z0-9]+', '-', workflow['name'].lower()).strip('-')
    slug = f"scraped-{slug}"

    # Add stage configuration (time estimates, deliverables)
    stage_config = {}
    for stage in workflow['stages']:
        stage_config[stage] = {
            'time_estimate_hours': estimate_time(stage),
            'deliverable': infer_deliverable(stage),
            'notes': f"Improved from competitor: {workflow['source_url']}"
        }

    return {
        'slug': slug,
        'name': f"{workflow['name']} (Free Edition)",
        'description': f"{workflow['description']} - Free alternative to paid tools",
        'industry': industry,
        'stages': workflow['stages'],
        'stage_config': stage_config,
        'is_system_template': False,
        'source_url': workflow['source_url']
    }


def infer_industry(name: str, description: str) -> str:
    """Guess industry from workflow name/description"""
    text = f"{name} {description}".lower()

    industry_keywords = {
        'comics': ['comic', 'manga', 'graphic novel', 'illustration'],
        'video': ['video', 'film', 'movie', 'editing', 'production'],
        'music': ['music', 'audio', 'song', 'track', 'album'],
        'sales': ['sales', 'crm', 'lead', 'prospect', 'customer'],
        'content': ['content', 'blog', 'article', 'writing'],
        'design': ['design', 'ui', 'ux', 'prototype'],
        'development': ['software', 'dev', 'code', 'programming'],
        'marketing': ['marketing', 'campaign', 'advertising'],
    }

    for industry, keywords in industry_keywords.items():
        if any(keyword in text for keyword in keywords):
            return industry

    return 'general'


def estimate_time(stage_name: str) -> int:
    """Estimate time for a stage based on name"""
    # Simple heuristics
    if any(word in stage_name.lower() for word in ['research', 'planning', 'brainstorm']):
        return 4
    elif any(word in stage_name.lower() for word in ['draft', 'sketch', 'wireframe']):
        return 8
    elif any(word in stage_name.lower() for word in ['review', 'qa', 'test']):
        return 2
    elif any(word in stage_name.lower() for word in ['final', 'publish', 'deploy']):
        return 1
    else:
        return 6  # Default


def infer_deliverable(stage_name: str) -> str:
    """Infer deliverable based on stage name"""
    name_lower = stage_name.lower()

    if 'draft' in name_lower or 'write' in name_lower:
        return 'draft document'
    elif 'design' in name_lower or 'mockup' in name_lower:
        return 'design files'
    elif 'code' in name_lower or 'dev' in name_lower:
        return 'working code'
    elif 'test' in name_lower or 'qa' in name_lower:
        return 'test results'
    elif 'publish' in name_lower or 'launch' in name_lower:
        return 'live deployment'
    else:
        return 'completed work'


def create_database_tables():
    """Create tables for storing scraped workflows"""
    db = sqlite3.connect('soulfra.db')

    db.execute('''
        CREATE TABLE IF NOT EXISTS scraped_competitor_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source_url TEXT UNIQUE NOT NULL,
            stages TEXT NOT NULL,  -- JSON array
            description TEXT,
            industry TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            converted_to_template BOOLEAN DEFAULT 0
        )
    ''')

    db.commit()
    db.close()


def main():
    parser = argparse.ArgumentParser(description='Scrape competitor workflows')
    parser.add_argument('--url', help='URL to scrape')
    parser.add_argument('--auto', action='store_true', help='Auto-scrape known competitors')
    parser.add_argument('--convert', action='store_true', help='Convert scraped workflows to templates')

    args = parser.parse_args()

    create_database_tables()

    if args.url:
        # Scrape single URL
        print(f"🔍 Scraping: {args.url}")
        workflow = scrape_workflow_from_url(args.url)

        if workflow and workflow['stages']:
            workflow_id = save_scraped_workflow(workflow)
            print(f"\n📊 Scraped Workflow:")
            print(f"   Name: {workflow['name']}")
            print(f"   Stages: {', '.join(workflow['stages'])}")
            print(f"   Industry: {workflow['industry']}")

            if args.convert:
                universal = convert_to_universal_workflow(workflow)
                print(f"\n✨ Converted to Universal Workflow:")
                print(f"   Slug: {universal['slug']}")
                print(f"   Industry: {universal['industry']}")
        else:
            print("❌ No workflow stages found")

    elif args.auto:
        # Auto-scrape known competitors
        print("🤖 Auto-scraping known competitors...")
        print(f"   Targets: {len(COMPETITOR_TARGETS)}")
        print()

        for target in COMPETITOR_TARGETS:
            print(f"🔍 Scraping {target['name']}...")
            workflow = scrape_workflow_from_url(target['url'], target['scrape_strategy'])

            if workflow and workflow['stages']:
                save_scraped_workflow(workflow)

        print("\n✅ Auto-scrape complete")
        print("   Run with --convert to turn scraped workflows into templates")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
