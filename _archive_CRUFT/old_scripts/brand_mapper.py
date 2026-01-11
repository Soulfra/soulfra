#!/usr/bin/env python3
"""
Brand Mapper - Compare Domain Wordmaps

Analyzes all domains to find:
- Unique words per brand (differentiation)
- Shared words across brands (platform identity)
- Semantic overlap (are brands too similar?)
- Positioning opportunities (gaps in wordmap coverage)

Output:
- brand_comparison.html - Interactive Venn diagram
- brand_positioning.json - Strategic recommendations
- brand_overlap_matrix.csv - Similarity scores
"""

import sqlite3
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from core.content_parser import ContentParser
from core.canvas_visualizer import CanvasVisualizer

# Domain list
DOMAINS_FILE = "domains-simple.txt"
OUTPUT_DIR = Path("data/brand_analysis")

def get_domains():
    """Read domains from config file"""
    if not Path(DOMAINS_FILE).exists():
        return ["soulfra.com", "calriven.com", "deathtodata.com",
                "howtocookathome.com", "hollowtown.com", "oofbox.com", "niceleak.com"]

    with open(DOMAINS_FILE) as f:
        return [line.strip() for line in f
                if line.strip() and not line.strip().startswith('#')]

def get_brand_content(domain):
    """Extract all content for a brand from database + markdown files"""
    content_parts = []

    # Database content
    db_path = "soulfra.db"
    if Path(db_path).exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get brand ID
        cursor.execute("SELECT id, name, tagline FROM brands WHERE domain = ?", (domain,))
        brand = cursor.fetchone()

        if brand:
            brand_id, name, tagline = brand
            content_parts.append(f"{name} {tagline or ''}")

            # Get posts (using brand column, not brand_id)
            cursor.execute("""
                SELECT title, content
                FROM posts
                WHERE brand = ?
            """, (domain.replace('.com', ''),))

            for title, content in cursor.fetchall():
                content_parts.append(f"{title} {content or ''}")

        conn.close()

    # Markdown files in output/DOMAIN/
    domain_slug = domain.replace('.com', '')
    output_path = Path(f"output/{domain_slug}")

    if output_path.exists():
        for md_file in output_path.glob("**/*.md"):
            try:
                content_parts.append(md_file.read_text())
            except:
                pass

    # Blog posts in blog/posts/
    blog_path = Path("blog/posts")
    if blog_path.exists():
        # Look for posts tagged with domain
        for html_file in blog_path.glob("*.html"):
            try:
                content = html_file.read_text()
                if domain_slug in content.lower():
                    content_parts.append(content)
            except:
                pass

    return "\n\n".join(content_parts)

def extract_wordmap(content):
    """Extract wordmap from content using fuzzy semantic extraction"""
    if not content.strip():
        return set()

    # Parse content to graph
    parser = ContentParser()

    # Try parsing as voice transcript (works for general text)
    try:
        graph = parser.parse(content, 'voice_transcript')
    except:
        # Fallback to simple word extraction
        words = re.findall(r'\b[a-z]{3,}\b', content.lower())
        return set(words)

    # Extract all node labels (these are the wordmap terms)
    words = set()
    for node in graph.get('nodes', []):
        label = node.get('label', '').lower().strip()
        if label and len(label) > 2:  # Skip very short words
            words.add(label)

    return words

def calculate_overlap(wordmap_a, wordmap_b):
    """Calculate Jaccard similarity between two wordmaps"""
    if not wordmap_a or not wordmap_b:
        return 0.0

    intersection = len(wordmap_a & wordmap_b)
    union = len(wordmap_a | wordmap_b)

    return intersection / union if union > 0 else 0.0

def analyze_brands():
    """Compare all brands and generate strategic insights"""

    domains = get_domains()
    print(f"🔍 Analyzing {len(domains)} brands...")

    # Extract wordmaps for each brand
    wordmaps = {}
    for domain in domains:
        print(f"\n📊 Processing {domain}...")
        content = get_brand_content(domain)
        wordmap = extract_wordmap(content)
        wordmaps[domain] = wordmap
        print(f"   Found {len(wordmap)} unique terms")

    # Calculate overlap matrix
    overlap_matrix = {}
    for domain_a in domains:
        overlap_matrix[domain_a] = {}
        for domain_b in domains:
            if domain_a == domain_b:
                overlap_matrix[domain_a][domain_b] = 1.0
            else:
                overlap = calculate_overlap(wordmaps[domain_a], wordmaps[domain_b])
                overlap_matrix[domain_a][domain_b] = overlap

    # Find unique words per brand
    unique_words = {}
    for domain in domains:
        # Words that appear in this brand but not in any other
        other_words = set()
        for other_domain in domains:
            if other_domain != domain:
                other_words |= wordmaps[other_domain]

        unique_words[domain] = wordmaps[domain] - other_words

    # Find shared platform words (appear in ALL brands)
    platform_words = set.intersection(*wordmaps.values()) if wordmaps else set()

    # Generate strategic insights
    insights = generate_insights(wordmaps, overlap_matrix, unique_words, platform_words)

    # Save results
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Save overlap matrix as CSV
    save_overlap_csv(overlap_matrix, OUTPUT_DIR / "brand_overlap_matrix.csv")

    # Save positioning data as JSON
    positioning_data = {
        "wordmaps": {k: list(v) for k, v in wordmaps.items()},
        "unique_words": {k: list(v) for k, v in unique_words.items()},
        "platform_words": list(platform_words),
        "overlap_matrix": overlap_matrix,
        "insights": insights
    }

    with open(OUTPUT_DIR / "brand_positioning.json", "w") as f:
        json.dump(positioning_data, f, indent=2)

    # Generate interactive visualization
    save_venn_diagram(wordmaps, unique_words, platform_words, OUTPUT_DIR / "brand_comparison.html")

    # Generate report
    save_report(wordmaps, overlap_matrix, unique_words, platform_words, insights, OUTPUT_DIR / "brand_analysis_REPORT.md")

    print(f"\n✅ Analysis complete!")
    print(f"📁 Results saved to {OUTPUT_DIR}/")
    print(f"   - brand_comparison.html (interactive Venn diagram)")
    print(f"   - brand_positioning.json (strategic data)")
    print(f"   - brand_overlap_matrix.csv (similarity scores)")
    print(f"   - brand_analysis_REPORT.md (insights)")

def generate_insights(wordmaps, overlap_matrix, unique_words, platform_words):
    """Generate strategic brand positioning insights"""
    insights = []

    # Most differentiated brand
    differentiation_scores = {
        domain: len(unique) / len(wordmaps[domain]) if wordmaps[domain] else 0
        for domain, unique in unique_words.items()
    }

    most_unique = max(differentiation_scores, key=differentiation_scores.get)
    insights.append({
        "type": "most_differentiated",
        "brand": most_unique,
        "score": differentiation_scores[most_unique],
        "message": f"{most_unique} has the most unique positioning ({differentiation_scores[most_unique]:.1%} unique words)"
    })

    # Most similar pair
    max_overlap = 0
    similar_pair = None
    for domain_a in overlap_matrix:
        for domain_b in overlap_matrix[domain_a]:
            if domain_a < domain_b:  # Avoid duplicates
                overlap = overlap_matrix[domain_a][domain_b]
                if overlap > max_overlap:
                    max_overlap = overlap
                    similar_pair = (domain_a, domain_b)

    if similar_pair:
        insights.append({
            "type": "most_similar",
            "brands": similar_pair,
            "overlap": max_overlap,
            "message": f"{similar_pair[0]} and {similar_pair[1]} are very similar ({max_overlap:.1%} overlap) - consider repositioning"
        })

    # Platform identity strength
    avg_words_per_brand = sum(len(w) for w in wordmaps.values()) / len(wordmaps) if wordmaps else 0
    platform_strength = len(platform_words) / avg_words_per_brand if avg_words_per_brand > 0 else 0

    insights.append({
        "type": "platform_identity",
        "platform_words": len(platform_words),
        "strength": platform_strength,
        "message": f"Platform identity: {len(platform_words)} shared words across all brands ({platform_strength:.1%} of average brand)"
    })

    # Opportunity gaps
    all_words = set.union(*wordmaps.values()) if wordmaps else set()
    for domain in wordmaps:
        missing_words = all_words - wordmaps[domain]
        if len(missing_words) > 100:  # Significant gap
            insights.append({
                "type": "opportunity_gap",
                "brand": domain,
                "missing_count": len(missing_words),
                "message": f"{domain} is missing {len(missing_words)} terms used by other brands - expansion opportunity"
            })

    return insights

def save_overlap_csv(overlap_matrix, output_file):
    """Save overlap matrix as CSV"""
    domains = sorted(overlap_matrix.keys())

    with open(output_file, "w") as f:
        # Header
        f.write("," + ",".join(domains) + "\n")

        # Rows
        for domain_a in domains:
            row = [domain_a]
            for domain_b in domains:
                overlap = overlap_matrix[domain_a][domain_b]
                row.append(f"{overlap:.3f}")
            f.write(",".join(row) + "\n")

def save_venn_diagram(wordmaps, unique_words, platform_words, output_file):
    """Generate interactive Venn diagram visualization"""

    # Create nodes for the graph
    nodes = []
    edges = []

    # Add brand nodes (positioned in circle)
    import math
    num_brands = len(wordmaps)
    for i, (domain, wordmap) in enumerate(wordmaps.items()):
        angle = (2 * math.pi * i) / num_brands
        x = 600 + 300 * math.cos(angle)
        y = 450 + 300 * math.sin(angle)

        nodes.append({
            "id": f"brand_{domain}",
            "label": domain.replace('.com', ''),
            "type": "brand",
            "x": x,
            "y": y,
            "wordcount": len(wordmap),
            "unique_count": len(unique_words.get(domain, set()))
        })

    # Add platform node (center)
    if platform_words:
        nodes.append({
            "id": "platform",
            "label": "Platform Core",
            "type": "platform",
            "x": 600,
            "y": 450,
            "wordcount": len(platform_words)
        })

        # Connect all brands to platform
        for domain in wordmaps:
            edges.append({
                "source": f"brand_{domain}",
                "target": "platform",
                "type": "shares_words"
            })

    # Add edges for high overlap
    for domain_a in wordmaps:
        for domain_b in wordmaps:
            if domain_a < domain_b:  # Avoid duplicates
                overlap = calculate_overlap(wordmaps[domain_a], wordmaps[domain_b])
                if overlap > 0.3:  # Significant overlap
                    edges.append({
                        "source": f"brand_{domain_a}",
                        "target": f"brand_{domain_b}",
                        "type": "similar",
                        "weight": overlap
                    })

    graph = {"nodes": nodes, "edges": edges}

    # Render using CanvasVisualizer
    viz = CanvasVisualizer(width=1200, height=900)

    # Do force-directed layout
    positions = viz.layout_force_directed(nodes, edges)

    # Render HTML
    viz.render_html_interactive(nodes, edges, positions, str(output_file))

def save_report(wordmaps, overlap_matrix, unique_words, platform_words, insights, output_file):
    """Generate markdown report"""

    with open(output_file, "w") as f:
        f.write("# Brand Analysis Report\n\n")
        f.write(f"**Generated:** {Path(output_file).stat().st_mtime}\n\n")

        f.write("## Overview\n\n")
        f.write(f"- **Total Brands:** {len(wordmaps)}\n")
        f.write(f"- **Platform Words:** {len(platform_words)}\n")
        f.write(f"- **Total Unique Terms:** {len(set.union(*wordmaps.values()))}\n\n")

        f.write("## Brand Wordmap Sizes\n\n")
        f.write("| Brand | Total Words | Unique Words | Uniqueness % |\n")
        f.write("|-------|-------------|--------------|---------------|\n")

        for domain in sorted(wordmaps.keys()):
            total = len(wordmaps[domain])
            unique = len(unique_words.get(domain, set()))
            pct = (unique / total * 100) if total > 0 else 0
            f.write(f"| {domain} | {total} | {unique} | {pct:.1f}% |\n")

        f.write("\n## Strategic Insights\n\n")
        for insight in insights:
            f.write(f"- **{insight['type'].replace('_', ' ').title()}**: {insight['message']}\n")

        f.write("\n## Platform Identity\n\n")
        f.write("Words shared across ALL brands:\n\n")
        for word in sorted(platform_words)[:50]:  # Top 50
            f.write(f"- {word}\n")

        if len(platform_words) > 50:
            f.write(f"\n... and {len(platform_words) - 50} more\n")

        f.write("\n## Brand Differentiation\n\n")
        for domain in sorted(wordmaps.keys()):
            unique = unique_words.get(domain, set())
            if unique:
                f.write(f"\n### {domain}\n\n")
                f.write(f"Unique to this brand ({len(unique)} terms):\n\n")
                for word in sorted(unique)[:20]:  # Top 20
                    f.write(f"- {word}\n")
                if len(unique) > 20:
                    f.write(f"\n... and {len(unique) - 20} more\n")

        f.write("\n## Overlap Matrix\n\n")
        f.write("Similarity scores between brands (0 = completely different, 1 = identical):\n\n")

        domains = sorted(overlap_matrix.keys())
        f.write("| Brand | " + " | ".join([d.replace('.com', '') for d in domains]) + " |\n")
        f.write("|" + "---|" * (len(domains) + 1) + "\n")

        for domain_a in domains:
            row = [domain_a.replace('.com', '')]
            for domain_b in domains:
                overlap = overlap_matrix[domain_a][domain_b]
                row.append(f"{overlap:.2f}")
            f.write("| " + " | ".join(row) + " |\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze brand positioning across domains")
    parser.add_argument("--domains", nargs="*", help="Specific domains to analyze (default: all)")

    args = parser.parse_args()

    if args.domains:
        # Override domains list
        with open(DOMAINS_FILE, "w") as f:
            for domain in args.domains:
                f.write(f"{domain}\n")

    analyze_brands()
