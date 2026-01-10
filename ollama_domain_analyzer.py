#!/usr/bin/env python3
"""
Ollama Domain Analyzer - Intelligent domain analysis
Analyzes domain names and suggests:
- Category (tech/privacy/cooking/gaming/etc.)
- Tags for SEO
- Personality/tone
- Color scheme
- Target audience
- Content strategy
"""

import requests
import json
from typing import Dict, Optional


class OllamaDomainAnalyzer:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"

    def analyze_domain(self, domain: str) -> Optional[Dict]:
        """
        Analyze a domain name and return intelligent suggestions

        Returns:
        {
            "domain": "hollowtown.com",
            "category": "gaming",
            "subcategory": "mystery/horror",
            "tags": ["gaming", "mystery", "horror", "community"],
            "personality": {
                "tone": "mysterious",
                "formality": "casual",
                "voice": "enigmatic storyteller"
            },
            "colors": {
                "primary": "#2c1810",
                "secondary": "#8b4513",
                "accent": "#ff6b35"
            },
            "target_audience": "Gamers interested in mystery/horror experiences",
            "content_strategy": "Mystery game reviews, horror gaming news, community stories",
            "tagline": "Where mysteries unfold",
            "initial_content_ideas": [
                "Top 10 mystery games of 2025",
                "How to create suspense in game design",
                "Community spotlight: Best horror game mods"
            ]
        }
        """

        prompt = f"""Analyze this domain name and provide UNIQUE, CREATIVE branding suggestions: {domain}

IMPORTANT: Make this brand VERY DIFFERENT from typical websites in its category. Be creative and distinctive!

Based ONLY on the domain name "{domain}", suggest:
1. Primary category (tech, privacy, cooking, gaming, business, education, art, health, etc.)
2. Specific subcategory or niche
3. SEO tags (5-7 UNIQUE keywords, not generic)
4. Brand personality (tone, formality, voice) - BE SPECIFIC, not generic
5. Color scheme (hex codes for primary, secondary, accent) - CHOOSE COLORS THAT MATCH THE VIBE
6. Target audience description (be specific about demographics/psychographics)
7. Content strategy (what SPECIFIC topics to cover)
8. Catchy tagline (5-7 words) - MAKE IT MEMORABLE AND UNIQUE TO THIS DOMAIN
9. 3 initial blog post ideas (CREATIVE, not generic)

Examples of GOOD vs BAD taglines:
- BAD: "Where gaming mysteries unfold" (too generic)
- GOOD: "Pixel ghosts haunt these servers" (specific, memorable)

Respond ONLY with valid JSON in this exact format:
{{
    "category": "gaming",
    "subcategory": "mystery/horror",
    "tags": ["gaming", "mystery", "horror", "community", "reviews"],
    "personality": {{
        "tone": "mysterious",
        "formality": "casual",
        "voice": "enigmatic storyteller"
    }},
    "colors": {{
        "primary": "#2c1810",
        "secondary": "#8b4513",
        "accent": "#ff6b35"
    }},
    "target_audience": "Gamers aged 18-35 interested in mystery and horror experiences",
    "content_strategy": "Mystery game reviews, horror gaming news, community stories, developer interviews",
    "tagline": "Where gaming mysteries unfold",
    "initial_content_ideas": [
        "Top 10 mystery games that will keep you guessing",
        "The psychology of horror in game design",
        "Community spotlight: Best mystery game mods"
    ]
}}"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Request JSON format
                    "options": {
                        "temperature": 0.9,      # Moderate creativity (default: 0.8)
                        "top_p": 0.9,            # Nucleus sampling for diversity
                        "top_k": 40,             # Consider top 40 tokens
                        "repeat_penalty": 1.2,   # Avoid repetitive phrases
                        "num_predict": 1000      # Allow longer responses
                    }
                },
                timeout=30
            )

            if response.status_code != 200:
                print(f"❌ Ollama error: {response.status_code}")
                return None

            ollama_data = response.json()
            response_text = ollama_data.get('response', '{}')

            # Parse JSON response
            analysis = json.loads(response_text)

            # Add domain to result
            analysis['domain'] = domain

            return analysis

        except requests.exceptions.Timeout:
            print(f"❌ Ollama timeout analyzing {domain}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON from Ollama: {e}")
            print(f"Response: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"❌ Error analyzing {domain}: {e}")
            return None


    def analyze_domain_simple(self, domain: str) -> Dict:
        """
        Fallback: Simple analysis without Ollama (for testing)
        """
        # Extract base name
        base_name = domain.split('.')[0]

        # Basic keyword matching
        keywords = {
            'gaming': ['game', 'play', 'quest', 'arcade', 'town'],
            'privacy': ['death', 'privacy', 'secure', 'vault'],
            'cooking': ['cook', 'recipe', 'food', 'eat', 'kitchen'],
            'tech': ['tech', 'code', 'dev', 'ai', 'cal'],
            'mystery': ['hollow', 'mystery', 'secret', 'dark'],
            'business': ['deal', 'sell', 'mvp', 'consulting'],
        }

        category = 'general'
        for cat, words in keywords.items():
            if any(word in base_name.lower() for word in words):
                category = cat
                break

        return {
            'domain': domain,
            'category': category,
            'subcategory': 'general',
            'tags': [base_name.lower(), category],
            'personality': {
                'tone': 'friendly',
                'formality': 'casual',
                'voice': 'informative'
            },
            'colors': {
                'primary': '#667eea',
                'secondary': '#764ba2',
                'accent': '#f093fb'
            },
            'target_audience': f"Users interested in {category}",
            'content_strategy': f"General {category} content",
            'tagline': f"Your {category} destination",
            'initial_content_ideas': [
                f"Introduction to {base_name}",
                f"Why choose {base_name}",
                f"{base_name} community guide"
            ]
        }


# CLI for testing
if __name__ == '__main__':
    import sys

    analyzer = OllamaDomainAnalyzer()

    if len(sys.argv) < 2:
        print("Usage: python3 ollama_domain_analyzer.py <domain>")
        print("Example: python3 ollama_domain_analyzer.py hollowtown.com")
        sys.exit(1)

    domain = sys.argv[1]
    print(f"🔍 Analyzing {domain}...")

    result = analyzer.analyze_domain(domain)

    if result:
        print("✅ Analysis complete!")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Analysis failed, using simple fallback...")
        result = analyzer.analyze_domain_simple(domain)
        print(json.dumps(result, indent=2))
