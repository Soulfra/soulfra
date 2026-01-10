#!/usr/bin/env python3
"""
Portfolio JSON Generator - For Static GitHub Pages

Generates static JSON files from portfolio scanner for consumption by
GitHub Pages sites (soulfra.github.io, calriven.com, etc.)

NO MORE CLOUDFLARE TUNNEL NEEDED!

Usage:
    python3 generate_portfolio_json.py
    python3 generate_portfolio_json.py --output ../soulfra.github.io/api/portfolio.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Import the portfolio scanner
from portfolio_scanner import PortfolioScanner


def generate_portfolio_json(output_path=None):
    """
    Run portfolio scanner and output to JSON file

    Args:
        output_path: Path to output JSON file (default: soulfra.github.io/api/portfolio.json)
    """
    # Default output to soulfra.github.io repo
    if not output_path:
        desktop = Path.home() / 'Desktop'
        output_path = desktop / 'soulfra.github.io' / 'api' / 'portfolio.json'

    output_path = Path(output_path)

    # Create api directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("📊 PORTFOLIO JSON GENERATOR")
    print("=" * 80)
    print(f"Output: {output_path}")
    print()

    # Run scanner
    scanner = PortfolioScanner()
    inventory = scanner.scan_all()

    # Save to output path
    with open(output_path, 'w') as f:
        json.dump(inventory, f, indent=2)

    print()
    print("=" * 80)
    print(f"✅ Generated: {output_path}")
    print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("📡 Static URL (after git push):")
    print("   https://soulfra.github.io/api/portfolio.json")
    print()
    print("🔧 Next steps:")
    print("   cd ~/Desktop/soulfra.github.io")
    print("   git add api/portfolio.json")
    print("   git commit -m '📊 Update portfolio data'")
    print("   git push")
    print("=" * 80)

    return inventory


def generate_lorem_ipsum_data():
    """
    Generate Lorem Ipsum placeholder data for development

    Returns static mock data that looks realistic but doesn't require
    running the full portfolio scanner.
    """
    return {
        "scan_time": datetime.utcnow().isoformat(),
        "local_repos": {
            "soulfra-simple": {
                "exists": True,
                "path": "/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple",
                "files": 342,
                "size_mb": 15.2,
                "file_types": {".py": 45, ".html": 28, ".js": 12, ".md": 8},
                "qr_codes": [],
                "readmes": ["README.md"],
                "templates": ["voice-archive/index.html", "voice-archive/login.html"],
                "blog_posts": []
            },
            "calriven": {
                "exists": True,
                "path": "/Users/matthewmauer/Desktop/calriven",
                "files": 28,
                "size_mb": 0.5,
                "file_types": {".html": 12, ".md": 8, ".xml": 2},
                "qr_codes": [],
                "readmes": ["README.md"],
                "templates": [],
                "blog_posts": ["post/fully-automated-calos-publishing-system-live-on-calriven.html"]
            }
        },
        "github_repos": {
            "soulfra-simple": {
                "description": "Flask backend + CringeProof voice memos",
                "url": "https://github.com/Soulfra/soulfra-simple",
                "stars": 0,
                "forks": 0,
                "language": "Python",
                "updated_at": "2026-01-09T00:00:00Z",
                "topics": []
            },
            "calriven": {
                "description": "Best AI for the job. Every time.",
                "url": "https://github.com/Soulfra/calriven",
                "stars": 0,
                "forks": 0,
                "language": "HTML",
                "updated_at": "2026-01-09T00:00:00Z",
                "topics": ["ai", "blog"]
            }
        },
        "voice_memos": [
            {
                "id": 1,
                "created_at": "2026-01-09T10:00:00",
                "transcript_preview": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. This is a test voice memo...",
                "file_size": 245632,
                "filename": "test-memo-1.wav"
            },
            {
                "id": 2,
                "created_at": "2026-01-08T15:30:00",
                "transcript_preview": "Another test voice recording about AI and automation systems working together...",
                "file_size": 189234,
                "filename": "test-memo-2.wav"
            }
        ],
        "blog_posts": [
            {
                "repo": "calriven",
                "path": "post/fully-automated-calos-publishing-system-live-on-calriven.html",
                "file": "fully-automated-calos-publishing-system-live-on-calriven.html"
            },
            {
                "repo": "calriven",
                "path": "post/second-test-automated-build-and-deploy-success.html",
                "file": "second-test-automated-build-and-deploy-success.html"
            }
        ],
        "qr_codes": [],
        "templates": [
            "voice-archive/index.html",
            "voice-archive/login.html",
            "voice-archive/record.html"
        ],
        "admin_dashboards": [
            {
                "repo": "soulfra-simple",
                "path": "voice-archive/soul-dashboard.html",
                "file": "soul-dashboard.html"
            },
            {
                "repo": "soulfra-simple",
                "path": "voice-archive/command-center.html",
                "file": "command-center.html"
            }
        ],
        "highlights": [],
        "duplicates": [
            {
                "file": "index.html",
                "locations": ["soulfra-simple", "calriven"],
                "count": 2
            }
        ],
        "missing_links": [
            "46 admin dashboards not linked from any public site"
        ],
        "statistics": {
            "total_local_repos": 6,
            "total_github_repos": 30,
            "total_files": 62374,
            "total_size_mb": 1832.6,
            "voice_memos": 6,
            "blog_posts": 25,
            "admin_dashboards": 46,
            "templates": 225,
            "duplicates": 14,
            "missing_links": 2
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Portfolio JSON Generator for Static Sites')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    parser.add_argument('--mock', action='store_true', help='Generate Lorem Ipsum mock data instead of scanning')

    args = parser.parse_args()

    if args.mock:
        # Generate mock data
        output_path = args.output or Path.home() / 'Desktop' / 'soulfra.github.io' / 'api' / 'portfolio-mock.json'
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print("📝 Generating Lorem Ipsum mock data...")
        data = generate_lorem_ipsum_data()

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Mock data saved to: {output_path}")
    else:
        # Real scan
        generate_portfolio_json(args.output)


if __name__ == '__main__':
    main()
