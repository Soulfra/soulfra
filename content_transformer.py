#!/usr/bin/env python3
"""
Content Transformer - The Missing Piece

Transform ONE piece of content into domain-specific versions using Ollama.

Example:
    Input: "The Problem with Browser Fingerprinting"

    Outputs:
    - soulfra.com: "The Philosophy of Digital Identity..."
    - deathtodata.com: "How to Block Browser Fingerprinting..."
    - calriven.com: "Technical Deep-Dive: Browser Fingerprinting APIs..."
    - howtocookathome.com: "Why Recipe Sites Track Your Browser..."

Usage:
    from content_transformer import ContentTransformer

    transformer = ContentTransformer()
    versions = transformer.transform_for_all_domains(
        title="Your Title",
        content="Your content..."
    )

    # Returns dict of {domain: {title, content, category}}
"""

import requests
import json
from typing import Dict, List, Any
from domain_manager import DomainManager


class ContentTransformer:
    """Transform content for different domain categories using Ollama"""

    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.domain_manager = DomainManager()

        # Category-specific transformation prompts
        self.category_prompts = {
            'tech': """You are a technical writer. Adapt this content for a technical audience interested in software engineering, system architecture, and code quality.

Focus on:
- Technical implementation details
- Best practices and patterns
- Code examples and architecture
- Performance and scalability

Original: {title}
{content}

Rewrite this with a technical angle. Keep it practical and code-focused.""",

            'privacy': """You are a privacy advocate. Adapt this content for readers concerned about data protection, surveillance, and digital rights.

Focus on:
- Privacy implications
- Data protection strategies
- Surveillance concerns
- Practical privacy tools

Original: {title}
{content}

Rewrite this with a privacy/security angle. Make it actionable.""",

            'cooking': """You are a food blogger. Adapt this content for home cooks and food enthusiasts.

Focus on:
- Practical cooking tips
- Recipe connections
- Food culture and techniques
- Quick, accessible advice

Original: {title}
{content}

Rewrite this connecting it to cooking, recipes, or food. Keep it fun and accessible.""",

            'business': """You are a business consultant. Adapt this content for entrepreneurs, startup founders, and business professionals.

Focus on:
- Business applications
- ROI and value proposition
- Market opportunities
- Practical business advice

Original: {title}
{content}

Rewrite this with a business/entrepreneurship angle. Focus on practical value.""",

            'health': """You are a health and wellness writer. Adapt this content for people interested in fitness, wellness, and healthy living.

Focus on:
- Health implications
- Wellness strategies
- Practical fitness tips
- Mental and physical health

Original: {title}
{content}

Rewrite this connecting it to health and wellness. Keep it motivating.""",

            'education': """You are an educational content creator. Adapt this content for learners and educators.

Focus on:
- Teaching concepts
- Learning strategies
- Educational applications
- Clear explanations

Original: {title}
{content}

Rewrite this as an educational resource. Make it clear and structured.""",

            'general': """You are a thoughtful writer. Adapt this content with a philosophical, meta-analytical perspective.

Focus on:
- Broader implications
- Philosophical angles
- Meta-commentary
- Thought-provoking insights

Original: {title}
{content}

Rewrite this with a philosophical, big-picture perspective. Make people think."""
        }

    def transform_for_domain(self, title: str, content: str, domain: str) -> Dict[str, str]:
        """
        Transform content for a specific domain

        Args:
            title: Original title
            content: Original content
            domain: Target domain (e.g., 'soulfra.com')

        Returns:
            dict: {'title': new_title, 'content': new_content, 'category': category}
        """
        # Get domain info
        domain_info = self.domain_manager.get_domain(domain)
        if not domain_info:
            # Fallback: return original
            return {
                'title': title,
                'content': content,
                'category': 'general',
                'error': f'Domain {domain} not found'
            }

        category = domain_info.get('category', 'general')

        # Get category-specific prompt
        prompt_template = self.category_prompts.get(category, self.category_prompts['general'])
        prompt = prompt_template.format(title=title, content=content)

        # Call Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': 'llama3.2:3b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.9  # High creativity for diverse outputs
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                transformed_content = result.get('response', content)

                # Extract new title from first line if it looks like a title
                lines = transformed_content.strip().split('\n')
                if lines and (lines[0].startswith('#') or len(lines[0]) < 100):
                    new_title = lines[0].replace('#', '').strip()
                    new_content = '\n'.join(lines[1:]).strip()
                else:
                    new_title = title
                    new_content = transformed_content

                return {
                    'title': new_title,
                    'content': new_content,
                    'category': category,
                    'domain': domain
                }
            else:
                # Ollama error - return original
                return {
                    'title': title,
                    'content': content,
                    'category': category,
                    'domain': domain,
                    'error': f'Ollama returned {response.status_code}'
                }

        except Exception as e:
            # Network/timeout error - return original
            return {
                'title': title,
                'content': content,
                'category': category,
                'domain': domain,
                'error': str(e)
            }

    def transform_for_all_domains(self, title: str, content: str) -> Dict[str, Dict[str, str]]:
        """
        Transform content for ALL domains

        Args:
            title: Original title
            content: Original content

        Returns:
            dict: {domain_name: {title, content, category}}
        """
        domains = self.domain_manager.get_all()
        results = {}

        print(f"\n🔄 Transforming content for {len(domains)} domains...")

        for domain_info in domains:
            domain = domain_info['domain']
            category = domain_info.get('category', 'general')

            print(f"   ✨ {domain} ({category})...")

            result = self.transform_for_domain(title, content, domain)
            results[domain] = result

            if 'error' in result:
                print(f"      ⚠️  {result['error']}")
            else:
                print(f"      ✅ Transformed")

        return results

    def preview_transformations(self, title: str, content: str) -> str:
        """
        Preview what transformations would look like

        Returns:
            str: Formatted preview text
        """
        results = self.transform_for_all_domains(title, content)

        preview = f"# Content Transformation Preview\n\n"
        preview += f"**Original Title:** {title}\n\n"
        preview += "---\n\n"

        for domain, result in results.items():
            preview += f"## {domain} ({result['category']})\n\n"
            preview += f"**Title:** {result['title']}\n\n"
            preview += f"**Content Preview:**\n{result['content'][:300]}...\n\n"
            preview += "---\n\n"

        return preview


def main():
    """CLI for testing content transformation"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 content_transformer.py <title> <content>")
        print("\nExample:")
        print('  python3 content_transformer.py "Browser Fingerprinting" "Websites track you..."')
        sys.exit(1)

    title = sys.argv[1]
    content = sys.argv[2]

    transformer = ContentTransformer()
    results = transformer.transform_for_all_domains(title, content)

    print("\n" + "="*60)
    print("TRANSFORMATION RESULTS")
    print("="*60 + "\n")

    for domain, result in results.items():
        print(f"\n📍 {domain} ({result['category']})")
        print(f"   Title: {result['title']}")
        print(f"   Content: {result['content'][:200]}...")
        if 'error' in result:
            print(f"   Error: {result['error']}")


if __name__ == '__main__':
    main()
