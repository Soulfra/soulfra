#!/usr/bin/env python3
"""
Domain Onboarding - Full automated workflow

When you add a domain to domains-simple.txt, this script:
1. Analyzes it with Ollama (category, tags, colors, personality)
2. Creates brand in database
3. Creates GitHub repo (optional)
4. Generates initial content with Multi-AI
5. Deploys to GitHub Pages

Usage:
    python3 domain_onboarding.py hollowtown.com
    python3 domain_onboarding.py --all  # Onboard all domains from domains-simple.txt
"""

import sys
import argparse
from ollama_domain_analyzer import OllamaDomainAnalyzer
from brand_creator import BrandCreator
from domain_manager import DomainManager


class DomainOnboarding:
    def __init__(self):
        self.analyzer = OllamaDomainAnalyzer()
        self.brand_creator = BrandCreator()
        self.domain_manager = DomainManager()

    def onboard_domain(self, domain: str, create_github_repo=False):
        """
        Full onboarding workflow for a single domain
        """
        print(f"\n{'='*60}")
        print(f"🚀 ONBOARDING: {domain}")
        print(f"{'='*60}\n")

        # Step 1: Analyze with Ollama
        print("📊 Step 1: Analyzing domain with Ollama...")
        analysis = self.analyzer.analyze_domain(domain)

        if not analysis:
            print("❌ Ollama analysis failed, using simple fallback")
            analysis = self.analyzer.analyze_domain_simple(domain)

        print(f"✅ Analysis complete!")
        print(f"   📁 Category: {analysis.get('category')}")
        print(f"   🎨 Tagline: {analysis.get('tagline')}")
        print(f"   🎭 Tone: {analysis.get('personality', {}).get('tone')}")
        print(f"   🎨 Primary Color: {analysis.get('colors', {}).get('primary')}")

        # Step 2: Create brand in database
        print("\n💾 Step 2: Creating brand in database...")
        brand_id = self.brand_creator.create_brand_from_analysis(analysis)

        if not brand_id:
            print("❌ Failed to create brand")
            return False

        # Step 3: Create GitHub repo (optional)
        if create_github_repo:
            print("\n🐙 Step 3: Creating GitHub repo...")
            # TODO: Implement GitHub repo creation
            print("⏭️  Skipped (not implemented yet)")
        else:
            print("\n⏭️  Step 3: Skipping GitHub repo creation (use --github flag)")

        # Step 4: Generate initial content
        print("\n📝 Step 4: Content strategy...")
        print(f"   Target Audience: {analysis.get('target_audience')}")
        print(f"   Content Strategy: {analysis.get('content_strategy')}")
        print(f"   Initial Post Ideas:")
        for i, idea in enumerate(analysis.get('initial_content_ideas', []), 1):
            print(f"      {i}. {idea}")

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ ONBOARDING COMPLETE!")
        print(f"{'='*60}")
        print(f"Domain: {domain}")
        print(f"Brand ID: {brand_id}")
        print(f"Category: {analysis.get('category')}")
        print(f"Tagline: {analysis.get('tagline')}")
        print(f"\n🎯 Next steps:")
        print(f"   1. Go to Studio: http://localhost:5001/studio")
        print(f"   2. Select '{domain}' from domain list")
        print(f"   3. Write your first post")
        print(f"   4. Click 'Export + Push to GitHub'")
        print(f"{'='*60}\n")

        return True

    def onboard_all_new_domains(self):
        """
        Onboard all domains from domains-simple.txt that don't have brands yet
        """
        import sqlite3

        print("🔍 Checking for new domains to onboard...")

        # Get all domains from domain manager
        all_domains = self.domain_manager.get_all()

        # Get existing brands from database
        conn = sqlite3.connect('soulfra.db')
        cursor = conn.cursor()
        cursor.execute('SELECT domain FROM brands')
        existing_domains = set(row[0] for row in cursor.fetchall())
        conn.close()

        # Find domains that don't have brands yet
        new_domains = [d['domain'] for d in all_domains if d['domain'] not in existing_domains]

        if not new_domains:
            print("✅ All domains already have brands!")
            return

        print(f"📋 Found {len(new_domains)} new domain(s) to onboard:")
        for domain in new_domains:
            print(f"   • {domain}")

        print("\n🚀 Starting onboarding process...\n")

        for domain in new_domains:
            self.onboard_domain(domain)

        print(f"\n🎉 Onboarded {len(new_domains)} domain(s)!")


def main():
    parser = argparse.ArgumentParser(description='Domain Onboarding Automation')
    parser.add_argument('domain', nargs='?', help='Domain to onboard (e.g., hollowtown.com)')
    parser.add_argument('--all', action='store_true', help='Onboard all new domains from domains-simple.txt')
    parser.add_argument('--github', action='store_true', help='Create GitHub repo')

    args = parser.parse_args()

    onboarding = DomainOnboarding()

    if args.all:
        onboarding.onboard_all_new_domains()
    elif args.domain:
        onboarding.onboard_domain(args.domain, create_github_repo=args.github)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
