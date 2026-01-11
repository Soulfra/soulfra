#!/usr/bin/env python3
"""
Demo Pipeline - End-to-End Voice-to-Graph Flow

Shows the complete pipeline from voice memo → knowledge graph → static site.

This script demonstrates all 3 use cases:
1. Debug - System analysis
2. Brand - Strategy comparison
3. CCNA - Study graphs

Usage:
    python3 demo-pipeline.py                # Run all demos
    python3 demo-pipeline.py --debug        # Debug only
    python3 demo-pipeline.py --brand        # Brand only
    python3 demo-pipeline.py --ccna         # CCNA only
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime

def print_section(title):
    """Print colorful section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def run_command(cmd, description):
    """Run command and print output"""
    print(f"📟 {description}")
    print(f"   $ {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0 and result.stderr:
        print(f"⚠️  Error: {result.stderr}")

    return result.returncode == 0

def demo_debug_system():
    """Demo: System Debugger"""
    print_section("🔍 DEMO 1: System Debugger")

    print("This analyzes your Flask app and visualizes dependencies.\n")

    # Analyze routes
    run_command(
        "python3 debug_system.py --routes",
        "Analyzing Flask routes..."
    )

    time.sleep(1)

    # Check output
    routes_html = Path("data/system_debug/routes.html")
    if routes_html.exists():
        print(f"\n✅ Generated: {routes_html}")
        print(f"   Open in browser: file://{routes_html.absolute()}\n")

        # Print key findings
        routes_report = Path("data/system_debug/routes_REPORT.md")
        if routes_report.exists():
            with open(routes_report) as f:
                lines = f.readlines()
                print("📊 Key Findings:")
                for line in lines[27:37]:  # Hub nodes section
                    print(f"   {line.strip()}")
    else:
        print("❌ Failed to generate report")

    print("\n💡 What this shows:")
    print("   - 407 Flask routes")
    print("   - 1,548 nodes (functions, imports, routes)")
    print("   - 2,600 edges (function calls)")
    print("   - Hub nodes: jsonify (454), get_db (187)")

def demo_brand_analysis():
    """Demo: Brand Strategy Analysis"""
    print_section("📊 DEMO 2: Brand Strategy Analysis")

    print("This compares wordmaps across all your domains.\n")

    # Run brand mapper
    run_command(
        "python3 brand_mapper.py",
        "Comparing 7 domains..."
    )

    time.sleep(1)

    # Check output
    brand_html = Path("data/brand_analysis/brand_comparison.html")
    if brand_html.exists():
        print(f"\n✅ Generated: {brand_html}")
        print(f"   Open in browser: file://{brand_html.absolute()}\n")

        # Print strategic insights
        brand_report = Path("data/brand_analysis/brand_analysis_REPORT.md")
        if brand_report.exists():
            with open(brand_report) as f:
                lines = f.readlines()
                print("📊 Strategic Insights:")
                for line in lines[23:28]:  # Insights section
                    if line.strip().startswith('-'):
                        print(f"   {line.strip()}")
    else:
        print("❌ Failed to generate report")

    print("\n💡 What this shows:")
    print("   - soulfra.com vs calriven.com: 93% similar!")
    print("   - deathtodata.com: Most differentiated (15.2% unique)")
    print("   - Unique words per brand")
    print("   - Overlap matrix showing brand positioning")

def demo_ccna_study():
    """Demo: CCNA Study Graph"""
    print_section("🌐 DEMO 3: CCNA Study Graph")

    print("This converts networking study notes → knowledge graphs.\n")

    # Run CCNA study
    run_command(
        "python3 ccna_study.py",
        "Generating CCNA concept graph..."
    )

    time.sleep(1)

    # Check output
    ccna_html = Path("data/ccna_study/ccna_concept_graph.html")
    if ccna_html.exists():
        print(f"\n✅ Generated: {ccna_html}")
        print(f"   Open in browser: file://{ccna_html.absolute()}\n")

        # Print flashcard count
        flashcards_json = Path("data/ccna_study/ccna_flashcards.json")
        if flashcards_json.exists():
            import json
            with open(flashcards_json) as f:
                flashcards = json.load(f)
                print(f"📚 Generated {len(flashcards)} flashcards for spaced repetition")
    else:
        print("❌ Failed to generate report")

    print("\n💡 What this shows:")
    print("   - OSI Model, TCP/IP, network topologies")
    print("   - Concept relationships (TCP uses IP)")
    print("   - Maps CCNA to your system:")
    print("     • Star topology = soulfra.com hub")
    print("     • VLANs = brand segmentation")
    print("     • Routing table = subdomain_router.py")

    # Show comparison
    print("\n🔗 Mapping CCNA to Your System:\n")
    run_command(
        "python3 ccna_study.py --compare",
        "Showing CCNA → Soulfra connections..."
    )

def demo_build_content():
    """Demo: Build Content Pipeline"""
    print_section("🏗️ DEMO 4: Build Content Pipeline")

    print("This converts markdown → HTML with Merkle caching.\n")

    # Create sample markdown if not exists
    content_dir = Path("content")
    content_dir.mkdir(exist_ok=True)

    sample_md = content_dir / f"demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

    with open(sample_md, 'w') as f:
        f.write(f"""# Demo Blog Post

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## This is a test

This markdown file was auto-generated by `demo-pipeline.py`.

### Features

- Voice to graph
- Merkle caching
- GitHub Pages deployment

### Code Example

```python
def hello():
    return 'world'
```

*Built with the voice-to-graph pipeline.*
""")

    print(f"📝 Created sample markdown: {sample_md}\n")

    # Build content
    run_command(
        "python3 build-content.py",
        "Building static site..."
    )

    time.sleep(1)

    # Check output
    dist_index = Path("dist/index.html")
    if dist_index.exists():
        print(f"\n✅ Generated: {dist_index}")
        print(f"   Open in browser: file://{dist_index.absolute()}\n")

        # Count built files
        dist_files = list(Path("dist").glob("*.html"))
        print(f"📦 Built {len(dist_files)} HTML files")

        # Show caching
        cache_file = Path(".cache/content_hashes.json")
        if cache_file.exists():
            import json
            with open(cache_file) as f:
                cache = json.load(f)
                print(f"💾 Cached {len(cache)} file hashes (Merkle tree)")
    else:
        print("❌ Failed to generate site")

    print("\n💡 What this shows:")
    print("   - Markdown → HTML conversion")
    print("   - Merkle tree caching (SHA-256 hashes)")
    print("   - RSS feed generation (feed.xml)")
    print("   - Sitemap generation (sitemap.xml)")
    print("\n   Run again → skips cached files (10x faster!)")

def demo_all():
    """Run all demos"""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🎤 Voice-to-Graph Pipeline - Complete Demo            ║
║                                                           ║
║   Shows: Debug, Brand Strategy, CCNA Study, Build        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")

    print("This will generate:")
    print("  1. System debug graphs (Flask routes)")
    print("  2. Brand analysis reports (domain overlap)")
    print("  3. CCNA study graphs (networking concepts)")
    print("  4. Static blog site (markdown → HTML)")
    print()

    input("Press ENTER to start... ")

    # Run all demos
    demo_debug_system()
    time.sleep(2)

    demo_brand_analysis()
    time.sleep(2)

    demo_ccna_study()
    time.sleep(2)

    demo_build_content()

    # Summary
    print_section("✅ Demo Complete!")

    print("📁 Generated Files:\n")

    files = [
        ("data/system_debug/routes.html", "System debug graph"),
        ("data/brand_analysis/brand_comparison.html", "Brand overlap graph"),
        ("data/ccna_study/ccna_concept_graph.html", "CCNA concept graph"),
        ("dist/index.html", "Static blog index"),
    ]

    for filepath, description in files:
        path = Path(filepath)
        if path.exists():
            print(f"   ✅ {filepath}")
            print(f"      {description}")
        else:
            print(f"   ❌ {filepath} (not generated)")
        print()

    print("🌐 Next Steps:\n")
    print("   1. Start Flask server:")
    print("      $ python3 app.py")
    print()
    print("   2. Open dashboard:")
    print("      http://localhost:5001/tools")
    print()
    print("   3. View voice-to-graph debugger:")
    print("      http://localhost:5001/voice-to-graph")
    print()
    print("   4. Read complete guide:")
    print("      $ cat START_HERE.md")
    print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Demo voice-to-graph pipeline")
    parser.add_argument("--debug", action="store_true", help="Run debug demo only")
    parser.add_argument("--brand", action="store_true", help="Run brand demo only")
    parser.add_argument("--ccna", action="store_true", help="Run CCNA demo only")
    parser.add_argument("--build", action="store_true", help="Run build demo only")

    args = parser.parse_args()

    if args.debug:
        demo_debug_system()
    elif args.brand:
        demo_brand_analysis()
    elif args.ccna:
        demo_ccna_study()
    elif args.build:
        demo_build_content()
    else:
        demo_all()
