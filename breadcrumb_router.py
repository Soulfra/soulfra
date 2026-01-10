#!/usr/bin/env python3
"""
Breadcrumb Router - Cross-Domain Traffic Flow System

Routes users between domains based on activity priorities:
- Hot domains (Priority #1) → Link to all others
- Medium domains (Priority #2-3) → Link to hotter + Soulfra
- Cold domains (Priority #4) → Receive all traffic (hub)

Generates breadcrumb.json for each domain with recommended links.

Usage:
    python3 breadcrumb_router.py
"""

import json
import os
from datetime import datetime
from typing import Dict, List


def load_domain_stats(stats_file: str = 'soulfra.github.io/domain-stats.json') -> Dict:
    """Load domain stats from scraper output"""
    try:
        with open(stats_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Stats file not found: {stats_file}")
        print("   Run github_domain_scraper.py first")
        return None


def generate_breadcrumb_routes(domain_stats: Dict) -> Dict[str, List[Dict]]:
    """
    Generate breadcrumb routes for each domain

    Routing Rules:
    - Priority #1 (hottest) → Links to #2, #3, #4
    - Priority #2 → Links to #1, #3, #4
    - Priority #3 → Links to #1, #2, #4
    - Priority #4 (coldest) → Hub (receives from all)

    Returns:
        dict: {
            'calriven': [breadcrumb_links],
            'cringeproof': [breadcrumb_links],
            ...
        }
    """
    domains = domain_stats['domains']
    breadcrumbs = {}

    # Sort domains by priority
    sorted_domains = sorted(domains, key=lambda d: d['allocation_priority'])

    # Domain metadata for links
    domain_info = {
        d['domain']: {
            'icon': d['icon'],
            'type': d['type'],
            'url': f"https://{d['domain']}.com",
            'github_page': f"{d['domain']}/index.html",
            'priority': d['allocation_priority'],
            'allocation_percent': d['allocation_percent'],
            'activity_score': d['activity_score']
        }
        for d in domains
    }

    for domain_data in domains:
        domain_name = domain_data['domain']
        priority = domain_data['allocation_priority']

        # Determine which domains to link to
        links = []

        if priority == 1:
            # Hottest domain → Link to all others
            # Strategy: "Explore our other projects"
            for other in sorted_domains:
                if other['domain'] != domain_name:
                    links.append({
                        'domain': other['domain'],
                        'reason': 'explore_network',
                        'cta': f"Explore {other['domain'].title()}",
                        **domain_info[other['domain']]
                    })

        elif priority == 2:
            # Medium-high → Link to hotter + colder
            # Strategy: "Level up or dive deeper"
            for other in sorted_domains:
                if other['domain'] != domain_name:
                    if other['allocation_priority'] == 1:
                        links.append({
                            'domain': other['domain'],
                            'reason': 'level_up',
                            'cta': f"Level up with {other['domain'].title()}",
                            **domain_info[other['domain']]
                        })
                    else:
                        links.append({
                            'domain': other['domain'],
                            'reason': 'discover_more',
                            'cta': f"Discover {other['domain'].title()}",
                            **domain_info[other['domain']]
                        })

        elif priority == 3:
            # Medium-low → Link to hotter domains + hub
            # Strategy: "Get more active or find your center"
            for other in sorted_domains:
                if other['domain'] != domain_name:
                    if other['allocation_priority'] < 3:
                        links.append({
                            'domain': other['domain'],
                            'reason': 'more_active',
                            'cta': f"More active: {other['domain'].title()}",
                            **domain_info[other['domain']]
                        })
                    elif other['allocation_priority'] == 4:
                        links.append({
                            'domain': other['domain'],
                            'reason': 'find_center',
                            'cta': f"Find your center: {other['domain'].title()}",
                            **domain_info[other['domain']]
                        })

        elif priority == 4:
            # Coldest domain (usually Soulfra) → Hub
            # Strategy: "Explore all active domains"
            for other in sorted_domains:
                if other['domain'] != domain_name:
                    links.append({
                        'domain': other['domain'],
                        'reason': 'hub_to_active',
                        'cta': f"Explore {other['domain'].title()}",
                        **domain_info[other['domain']]
                    })

        breadcrumbs[domain_name] = {
            'domain': domain_name,
            'priority': priority,
            'allocation_percent': domain_data['allocation_percent'],
            'breadcrumb_links': links,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

    return breadcrumbs


def generate_breadcrumb_html(breadcrumb_data: Dict, domain_name: str) -> str:
    """
    Generate HTML snippet for breadcrumb navigation

    Returns ready-to-embed HTML that can be added to domain pages
    """
    links = breadcrumb_data['breadcrumb_links']

    html = f"""
<!-- Breadcrumb Navigation (Auto-generated by breadcrumb_router.py) -->
<div class="soulfra-breadcrumb" style="
    margin: 2rem 0;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-radius: 12px;
    border-left: 4px solid rgba(102, 126, 234, 0.5);
">
    <h3 style="margin-bottom: 1rem; font-size: 1.25rem; opacity: 0.9;">
        🌐 Explore the Soulfra Network
    </h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem;">
"""

    for link in links:
        html += f"""
        <a href="{link['url']}" style="
            display: block;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        " onmouseover="this.style.background='rgba(255,255,255,0.2)'; this.style.transform='translateY(-2px)'"
           onmouseout="this.style.background='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)'">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{link['icon']}</div>
            <div style="font-weight: 600; margin-bottom: 0.25rem;">{link['domain'].title()}</div>
            <div style="font-size: 0.85rem; opacity: 0.7;">{link['cta']}</div>
            <div style="font-size: 0.75rem; opacity: 0.5; margin-top: 0.5rem;">
                Priority #{link['priority']} • {link['allocation_percent']}% active
            </div>
        </a>
"""

    html += """
    </div>
</div>
<!-- End Breadcrumb Navigation -->
"""

    return html


def save_breadcrumbs(breadcrumbs: Dict, output_dir: str = 'soulfra.github.io'):
    """Save breadcrumb data and HTML snippets for each domain"""
    os.makedirs(output_dir, exist_ok=True)

    for domain_name, breadcrumb_data in breadcrumbs.items():
        domain_dir = os.path.join(output_dir, domain_name)
        os.makedirs(domain_dir, exist_ok=True)

        # Save JSON data
        json_file = os.path.join(domain_dir, 'breadcrumbs.json')
        with open(json_file, 'w') as f:
            json.dump(breadcrumb_data, f, indent=2)

        print(f"✅ Saved {json_file}")

        # Save HTML snippet
        html_snippet = generate_breadcrumb_html(breadcrumb_data, domain_name)
        html_file = os.path.join(domain_dir, 'breadcrumb-nav.html')
        with open(html_file, 'w') as f:
            f.write(html_snippet)

        print(f"✅ Saved {html_file}")

    # Save master breadcrumb map
    master_file = os.path.join(output_dir, 'breadcrumb-map.json')
    with open(master_file, 'w') as f:
        json.dump({
            'breadcrumbs': breadcrumbs,
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'routing_strategy': 'priority_based'
        }, f, indent=2)

    print(f"✅ Saved {master_file}")


def visualize_routing_graph(breadcrumbs: Dict):
    """Print ASCII visualization of routing graph"""
    print("\n" + "=" * 70)
    print("🌐 BREADCRUMB ROUTING GRAPH")
    print("=" * 70)

    # Sort by priority
    sorted_breadcrumbs = sorted(breadcrumbs.items(), key=lambda x: x[1]['priority'])

    for domain_name, data in sorted_breadcrumbs:
        priority = data['priority']
        allocation = data['allocation_percent']
        links = data['breadcrumb_links']

        # Get icon from first link (hack, but works)
        domain_icon = "📊" if domain_name == "calriven" else \
                      "🎭" if domain_name == "cringeproof" else \
                      "🔥" if domain_name == "deathtodata" else "💜"

        print(f"\n#{priority} {domain_icon} {domain_name.upper()} ({allocation}% allocation)")
        print(f"   Routes to {len(links)} domains:")

        for link in links:
            print(f"     → {link['icon']} {link['domain']} (Priority #{link['priority']}) - {link['reason']}")


def generate_routing_strategy_docs(breadcrumbs: Dict) -> str:
    """Generate markdown documentation for routing strategy"""
    doc = """# Breadcrumb Routing Strategy

## Overview

The breadcrumb system routes users between domains based on activity priorities:

| Priority | Role | Routing Strategy |
|----------|------|------------------|
| #1 | Hottest | Links to all other domains (exploration hub) |
| #2 | Medium-High | Links to hotter domains (level up) + others |
| #3 | Medium-Low | Links to active domains + Soulfra hub |
| #4 | Coldest (Hub) | Links to all active domains (central hub) |

## Current Routing Map

"""

    sorted_breadcrumbs = sorted(breadcrumbs.items(), key=lambda x: x[1]['priority'])

    for domain_name, data in sorted_breadcrumbs:
        priority = data['priority']
        allocation = data['allocation_percent']
        links = data['breadcrumb_links']

        domain_icon = "📊" if domain_name == "calriven" else \
                      "🎭" if domain_name == "cringeproof" else \
                      "🔥" if domain_name == "deathtodata" else "💜"

        doc += f"\n### #{priority} {domain_icon} {domain_name.upper()} ({allocation}% allocation)\n\n"
        doc += f"Routes to **{len(links)} domains**:\n\n"

        for link in links:
            doc += f"- {link['icon']} **{link['domain'].title()}** (Priority #{link['priority']}) - {link['cta']}\n"

    doc += "\n## How to Use Breadcrumbs\n\n"
    doc += "Each domain gets two files:\n\n"
    doc += "1. **`breadcrumbs.json`** - Machine-readable routing data\n"
    doc += "2. **`breadcrumb-nav.html`** - Ready-to-embed HTML snippet\n\n"
    doc += "### Embed Breadcrumbs in Domain Pages\n\n"
    doc += "```html\n"
    doc += "<!-- In your domain's index.html -->\n"
    doc += '<div id="breadcrumb-container"></div>\n\n'
    doc += "<script>\n"
    doc += "fetch('breadcrumb-nav.html')\n"
    doc += "  .then(r => r.text())\n"
    doc += "  .then(html => {\n"
    doc += "    document.getElementById('breadcrumb-container').innerHTML = html;\n"
    doc += "  });\n"
    doc += "</script>\n"
    doc += "```\n"

    return doc


def main():
    """Main breadcrumb router function"""
    print("=" * 70)
    print("🌐 Breadcrumb Router - Cross-Domain Traffic Flow")
    print("=" * 70)

    # Load domain stats
    stats = load_domain_stats()
    if not stats:
        return

    # Generate breadcrumb routes
    print("\n📊 Generating breadcrumb routes...")
    breadcrumbs = generate_breadcrumb_routes(stats)

    # Visualize routing graph
    visualize_routing_graph(breadcrumbs)

    # Save breadcrumb files
    print("\n💾 Saving breadcrumb data...")
    save_breadcrumbs(breadcrumbs)

    # Generate documentation
    docs = generate_routing_strategy_docs(breadcrumbs)
    with open('soulfra.github.io/BREADCRUMB_ROUTING.md', 'w') as f:
        f.write(docs)
    print("✅ Saved soulfra.github.io/BREADCRUMB_ROUTING.md")

    print("\n" + "=" * 70)
    print("✅ Breadcrumb routing complete!")
    print("=" * 70)
    print("\nFiles generated:")
    print("  - soulfra.github.io/*/breadcrumbs.json (routing data)")
    print("  - soulfra.github.io/*/breadcrumb-nav.html (embed HTML)")
    print("  - soulfra.github.io/breadcrumb-map.json (master map)")
    print("  - soulfra.github.io/BREADCRUMB_ROUTING.md (docs)")
    print("\nNext steps:")
    print("  1. Embed breadcrumb-nav.html in each domain's homepage")
    print("  2. Test links work correctly")
    print("  3. Set up GitHub Actions to regenerate hourly")
    print("=" * 70)


if __name__ == '__main__':
    main()
