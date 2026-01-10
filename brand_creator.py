#!/usr/bin/env python3
"""
Brand Creator - Create brands in database from Ollama analysis
"""

import sqlite3
from typing import Dict, Optional
from ollama_domain_analyzer import OllamaDomainAnalyzer


class BrandCreator:
    def __init__(self, db_path="soulfra.db"):
        self.db_path = db_path

    def create_brand_from_analysis(self, analysis: Dict) -> Optional[int]:
        """
        Create brand in database from Ollama analysis

        Returns brand_id if successful, None otherwise
        """
        domain = analysis['domain']
        category = analysis.get('category', 'general')
        tagline = analysis.get('tagline', '')

        # Extract name from domain
        name = domain.split('.')[0].title()

        # Get personality
        personality = analysis.get('personality', {})
        tone = personality.get('tone', 'friendly')
        voice = personality.get('voice', 'informative')

        # Get colors
        colors = analysis.get('colors', {})
        color_primary = colors.get('primary', '#667eea')
        color_secondary = colors.get('secondary', '#764ba2')
        color_accent = colors.get('accent', '#f093fb')

        # Create slug
        slug = domain.split('.')[0].lower()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if brand already exists
            cursor.execute('SELECT id FROM brands WHERE domain = ?', (domain,))
            existing = cursor.fetchone()

            if existing:
                print(f"✅ Brand already exists for {domain} (id: {existing[0]})")
                return existing[0]

            # Insert brand
            cursor.execute('''
                INSERT INTO brands (
                    name, slug, domain, category, tagline,
                    color_primary, color_secondary, color_accent,
                    personality_tone, ai_style,
                    brand_type, network_role
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name, slug, domain, category, tagline,
                color_primary, color_secondary, color_accent,
                tone, voice,
                'blog', 'member'
            ))

            brand_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"✅ Created brand: {name} ({domain}) - ID: {brand_id}")
            return brand_id

        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return None


    def create_brand_with_ollama(self, domain: str) -> Optional[int]:
        """
        Full workflow: Analyze domain with Ollama, then create brand
        """
        print(f"🔍 Analyzing {domain} with Ollama...")

        analyzer = OllamaDomainAnalyzer()
        analysis = analyzer.analyze_domain(domain)

        if not analysis:
            print("❌ Ollama analysis failed")
            return None

        print(f"✅ Ollama analysis complete!")
        print(f"   Category: {analysis.get('category')}")
        print(f"   Tagline: {analysis.get('tagline')}")
        print(f"   Tone: {analysis.get('personality', {}).get('tone')}")

        brand_id = self.create_brand_from_analysis(analysis)

        return brand_id


# CLI for testing
if __name__ == '__main__':
    import sys

    creator = BrandCreator()

    if len(sys.argv) < 2:
        print("Usage: python3 brand_creator.py <domain>")
        print("Example: python3 brand_creator.py hollowtown.com")
        sys.exit(1)

    domain = sys.argv[1]
    brand_id = creator.create_brand_with_ollama(domain)

    if brand_id:
        print(f"\n🎉 Brand created successfully! ID: {brand_id}")
    else:
        print("\n❌ Failed to create brand")
