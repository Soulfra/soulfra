#!/usr/bin/env python3
"""
Build Waitlist - Export static HTML and JSON files

Generates enterprise-grade static site from database:
1. Renders HTML for each language (en, es, ja, zh, fr)
2. Exports JSON API endpoints
3. Ready for deployment to GitHub Pages, S3, or Cloudflare

Usage:
    python3 build_waitlist.py                    # Build all languages
    python3 build_waitlist.py --lang en          # Build only English
    python3 build_waitlist.py --output ./docs    # Custom output directory
"""

import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from launch_calculator import calculate_launch_date, get_leaderboard
from database import get_db

# Default output directory (GitHub Pages compatible)
OUTPUT_DIR = "./output/waitlist"


def load_translations():
    """Load translations from translations.json"""
    with open('translations.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def get_waitlist_stats():
    """Get current waitlist statistics from database"""
    db = get_db()

    # Get leaderboard
    leaderboard = get_leaderboard()

    # Get total signups
    total_signups = db.execute('SELECT COUNT(*) as count FROM waitlist').fetchone()['count']

    return {
        'domains': leaderboard,
        'total_signups': total_signups,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }


def generate_static_html(lang='en', output_dir=OUTPUT_DIR):
    """
    Generate static HTML for a specific language

    Args:
        lang (str): Language code (en, es, ja, zh, fr)
        output_dir (str): Output directory path

    Returns:
        str: Path to generated HTML file
    """
    translations = load_translations()
    t = translations.get(lang, translations['en'])  # Fallback to English

    stats = get_waitlist_stats()

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t['page_title']}</title>
    <meta name="description" content="{t['tagline']}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 50px;
        }}

        h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .tagline {{
            font-size: 1.3em;
            opacity: 0.9;
        }}

        .lang-switcher {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 10px;
        }}

        .lang-switcher a {{
            color: white;
            text-decoration: none;
            margin: 0 5px;
            padding: 5px 10px;
            border-radius: 5px;
            transition: background 0.3s;
        }}

        .lang-switcher a:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .lang-switcher a.active {{
            background: rgba(255,255,255,0.3);
            font-weight: bold;
        }}

        .stats-bar {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 40px;
            text-align: center;
        }}

        .total-signups {{
            font-size: 3em;
            font-weight: bold;
            color: #ffd700;
        }}

        .domains-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}

        .domain-card {{
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 2px solid rgba(255,255,255,0.2);
        }}

        .domain-card.launched {{
            background: rgba(76, 175, 80, 0.3);
            border-color: #4CAF50;
        }}

        .domain-card.rank-1 {{
            border-color: #ffd700;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
        }}

        .domain-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .domain-name {{
            font-size: 1.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .rank-badge {{
            background: #ffd700;
            color: #333;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
        }}

        .signup-count {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 15px 0;
            color: #ffd700;
        }}

        .countdown {{
            font-size: 1.3em;
            margin: 10px 0;
        }}

        .progress-bar {{
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 20px;
            margin: 20px 0;
            overflow: hidden;
        }}

        .progress-fill {{
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            height: 100%;
            border-radius: 10px;
        }}

        .letter-slots {{
            margin: 15px 0;
            font-size: 0.9em;
        }}

        .cta-button {{
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }}

        .cta-button:hover {{
            background: #45a049;
        }}

        .footer {{
            text-align: center;
            margin-top: 50px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 2em;
            }}
            .domains-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="lang-switcher">
        <a href="index.html" class="{'active' if lang == 'en' else ''}">EN</a>
        <a href="index.es.html" class="{'active' if lang == 'es' else ''}">ES</a>
        <a href="index.ja.html" class="{'active' if lang == 'ja' else ''}">JA</a>
        <a href="index.zh.html" class="{'active' if lang == 'zh' else ''}">ZH</a>
        <a href="index.fr.html" class="{'active' if lang == 'fr' else ''}">FR</a>
    </div>

    <div class="container">
        <header>
            <h1>{t['header_title']}</h1>
            <p class="tagline">{t['tagline']}</p>
        </header>

        <div class="stats-bar">
            <h2>{t['total_signups']}</h2>
            <div class="total-signups">{stats['total_signups']}</div>
        </div>

        <div class="domains-grid">
"""

    # Generate domain cards
    for rank, domain in enumerate(stats['domains'], 1):
        rank_class = 'rank-1' if rank == 1 else ''
        launched_class = 'launched' if domain.get('is_launched') else ''

        slots_remaining = 26 - domain['signups']

        status_text = ''
        if domain.get('is_launched'):
            status_text = f'<div class="countdown">{t["launched"]}</div>'
        elif domain['days_until'] == 0:
            status_text = f'<div class="countdown">{t["ready_to_launch"]}</div>'
        else:
            status_text = f'<div class="countdown">{domain["days_until"]} {t["days_until"]}</div>'

        html += f"""
            <div class="domain-card {rank_class} {launched_class}">
                <div class="domain-header">
                    <div class="domain-name">{domain['domain_name']}</div>
                    <div class="rank-badge">#{rank}</div>
                </div>

                <div class="signup-count">{domain['signups']} {t['signups']}</div>

                {status_text}

                <div class="progress-bar">
                    <div class="progress-fill" style="width: {domain.get('progress_pct', 0)}%"></div>
                </div>

                <div class="letter-slots">
                    {slots_remaining}/26 {t['slots_remaining']}
                </div>

                <a href="https://soulfra.github.io/waitlist" class="cta-button">{t['join_waitlist']}</a>
            </div>
"""

    html += f"""
        </div>

        <div class="footer">
            <p>{t['footer_text_1']}</p>
            <p>{t['footer_text_2']}</p>
            <p>{t['footer_text_3']}</p>
            <p style="margin-top: 20px;">Last updated: {stats['updated_at'][:19]}</p>
        </div>
    </div>
</body>
</html>
"""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Write HTML file
    if lang == 'en':
        filename = 'index.html'
    else:
        filename = f'index.{lang}.html'

    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Generated {filepath}")

    return filepath


def generate_json_api(output_dir=OUTPUT_DIR):
    """
    Generate static JSON API endpoints

    Args:
        output_dir (str): Output directory path

    Returns:
        list: Paths to generated JSON files
    """
    stats = get_waitlist_stats()

    api_dir = os.path.join(output_dir, 'api')
    os.makedirs(api_dir, exist_ok=True)

    files = []

    # 1. Full stats endpoint
    stats_path = os.path.join(api_dir, 'stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    files.append(stats_path)
    print(f"✅ Generated {stats_path}")

    # 2. Leaderboard endpoint
    leaderboard_path = os.path.join(api_dir, 'leaderboard.json')
    with open(leaderboard_path, 'w', encoding='utf-8') as f:
        json.dump(stats['domains'], f, indent=2, ensure_ascii=False)
    files.append(leaderboard_path)
    print(f"✅ Generated {leaderboard_path}")

    # 3. Individual domain endpoints
    for domain in stats['domains']:
        domain_path = os.path.join(api_dir, f"{domain['domain_name']}.json")
        with open(domain_path, 'w', encoding='utf-8') as f:
            json.dump(domain, f, indent=2, ensure_ascii=False)
        files.append(domain_path)
        print(f"✅ Generated {domain_path}")

    return files


def build_all(output_dir=OUTPUT_DIR, languages=None):
    """
    Build complete static site for all languages

    Args:
        output_dir (str): Output directory path
        languages (list): List of language codes to build (default: all)

    Returns:
        dict: Paths to all generated files
    """
    if languages is None:
        languages = ['en', 'es', 'ja', 'zh', 'fr']

    print(f"\n{'='*60}")
    print(f"BUILDING STATIC WAITLIST SITE")
    print(f"Output: {output_dir}")
    print(f"Languages: {', '.join(languages)}")
    print(f"{'='*60}\n")

    results = {
        'html': [],
        'json': []
    }

    # Generate HTML for each language
    for lang in languages:
        filepath = generate_static_html(lang, output_dir)
        results['html'].append(filepath)

    # Generate JSON API endpoints
    json_files = generate_json_api(output_dir)
    results['json'] = json_files

    print(f"\n{'='*60}")
    print(f"BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"HTML files: {len(results['html'])}")
    print(f"JSON files: {len(results['json'])}")
    print(f"\nDeploy to:")
    print(f"  - GitHub Pages: Copy {output_dir} → /docs/")
    print(f"  - S3: aws s3 sync {output_dir} s3://your-bucket/")
    print(f"  - Cloudflare: Upload {output_dir} to Pages")
    print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Build static waitlist site')
    parser.add_argument('--lang', help='Specific language to build (default: all)')
    parser.add_argument('--output', default=OUTPUT_DIR, help='Output directory')

    args = parser.parse_args()

    if args.lang:
        generate_static_html(args.lang, args.output)
        generate_json_api(args.output)
    else:
        build_all(args.output)
