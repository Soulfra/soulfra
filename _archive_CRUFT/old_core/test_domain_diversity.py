#!/usr/bin/env python3
"""
Test Domain Diversity - Compare multiple domains to see if Ollama generates unique branding
"""

from ollama_domain_analyzer import OllamaDomainAnalyzer
import json


def test_diversity():
    """Test that similar domains get DIFFERENT branding"""

    analyzer = OllamaDomainAnalyzer()

    test_domains = [
        "hollowtown.com",
        "oofbox.com",
        "niceleak.com",
        "howtocookathome.com",
        "deathtodata.com"
    ]

    results = {}

    print("🧪 Testing Domain Diversity\n")
    print("="*60)

    for domain in test_domains:
        print(f"\n🔍 Analyzing: {domain}")
        analysis = analyzer.analyze_domain(domain)

        if analysis:
            results[domain] = {
                'tagline': analysis.get('tagline'),
                'category': analysis.get('category'),
                'tone': analysis.get('personality', {}).get('tone'),
                'primary_color': analysis.get('colors', {}).get('primary')
            }
            print(f"   Tagline: {analysis.get('tagline')}")
            print(f"   Tone: {analysis.get('personality', {}).get('tone')}")
            print(f"   Color: {analysis.get('colors', {}).get('primary')}")
        else:
            print(f"   ❌ Analysis failed")

    print("\n" + "="*60)
    print("📊 DIVERSITY CHECK\n")

    # Check for duplicates
    taglines = [r['tagline'] for r in results.values() if r.get('tagline')]
    colors = [r['primary_color'] for r in results.values() if r.get('primary_color')]

    duplicate_taglines = [t for t in taglines if taglines.count(t) > 1]
    duplicate_colors = [c for c in colors if colors.count(c) > 1]

    if duplicate_taglines:
        print(f"⚠️  DUPLICATE TAGLINES: {set(duplicate_taglines)}")
    else:
        print("✅ All taglines unique!")

    if duplicate_colors:
        print(f"⚠️  DUPLICATE COLORS: {set(duplicate_colors)}")
    else:
        print("✅ All colors unique!")

    print("\n📋 Full Results:")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    test_diversity()
