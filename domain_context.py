#!/usr/bin/env python3
"""
Domain Context Trainer for Ollama

Reads domains-master.csv and trains Ollama with context about each domain:
- What the domain is for
- Target audience
- Purpose
- Category

When user asks "Tell me about howtocookathome.com", Ollama knows:
"This is a cooking blog targeting parents 25-45 with quick 30-minute recipes"

Usage:
    from domain_context import DomainContextManager

    manager = DomainContextManager()
    context = manager.get_domain_context('howtocookathome.com')
    # Use context in Ollama prompts
"""

import csv
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from logger import get_logger

logger = get_logger('domain-context')


class DomainContextManager:
    """Manage domain context for Ollama conversations"""

    def __init__(self, csv_file: str = 'domains-master.csv'):
        """
        Initialize domain context manager

        Args:
            csv_file: Path to domains-master.csv
        """
        self.csv_file = Path(csv_file)
        self.domains = {}
        self.load_domains()

    def load_domains(self):
        """Load all domains from CSV"""
        if not self.csv_file.exists():
            logger.warning(f"CSV file not found: {self.csv_file}")
            return

        logger.info(f"Loading domains from {self.csv_file}")

        with open(self.csv_file, 'r') as f:
            # Skip comment lines starting with # and empty lines
            lines = [line for line in f if not line.strip().startswith('#') and line.strip()]

        # Parse CSV from filtered lines
        reader = csv.DictReader(lines)

        for row in reader:
            # Skip empty rows or templates
            if not row.get('domain') or row['domain'].startswith('#'):
                continue

            domain = row['domain'].strip()

            self.domains[domain] = {
                    'name': row.get('name', '').strip(),
                    'category': row.get('category', '').strip(),
                    'tier': row.get('tier', '').strip(),
                    'emoji': row.get('emoji', '').strip(),
                    'brand_type': row.get('brand_type', '').strip(),
                    'tagline': row.get('tagline', '').strip(),
                    'target_audience': row.get('target_audience', '').strip(),
                    'purpose': row.get('purpose', '').strip(),
                    'ssl_enabled': row.get('ssl_enabled', 'false').lower() == 'true',
                    'deployed': row.get('deployed', 'false').lower() == 'true'
                }

        logger.info(f"Loaded {len(self.domains)} domains")

    def get_domain_context(self, domain: str) -> Optional[Dict]:
        """
        Get context for a specific domain

        Args:
            domain: Domain name (e.g., 'howtocookathome.com')

        Returns:
            Dict with domain context or None
        """
        domain = domain.lower().strip()
        return self.domains.get(domain)

    def get_all_domains(self) -> List[str]:
        """Get list of all known domains"""
        return list(self.domains.keys())

    def build_ollama_context(self, domain: str) -> str:
        """
        Build Ollama context string for a domain

        Args:
            domain: Domain name

        Returns:
            Formatted context string for Ollama
        """
        context = self.get_domain_context(domain)
        if not context:
            return f"No information available about {domain}"

        prompt = f"""Domain: {domain}
Name: {context['name']}
Category: {context['category']}
Type: {context['brand_type']}
Tagline: {context['tagline']}
Target Audience: {context['target_audience']}
Purpose: {context['purpose']}
Status: {"Deployed" if context['deployed'] else "Not deployed yet"}

This domain is part of the Soulfra multi-domain platform."""

        return prompt

    def build_all_domains_context(self) -> str:
        """
        Build Ollama context for ALL domains

        Returns:
            Formatted string describing all domains
        """
        if not self.domains:
            return "No domains configured yet."

        prompt = "# Soulfra Domain Portfolio\n\n"
        prompt += f"Managing {len(self.domains)} domains across multiple categories:\n\n"

        # Group by category
        by_category = {}
        for domain, info in self.domains.items():
            category = info['category'] or 'Other'
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((domain, info))

        for category, domains_list in sorted(by_category.items()):
            prompt += f"## {category.title()}\n"
            for domain, info in domains_list:
                status = "✅" if info['deployed'] else "⏳"
                prompt += f"- {status} **{domain}**: {info['tagline']}\n"
                if info['target_audience']:
                    prompt += f"  Target: {info['target_audience']}\n"
            prompt += "\n"

        return prompt

    def ask_ollama_about_domain(self, domain: str, question: str) -> Optional[str]:
        """
        Ask Ollama a question about a domain with context

        Args:
            domain: Domain name
            question: User's question

        Returns:
            Ollama's response or None if error
        """
        context = self.build_ollama_context(domain)

        prompt = f"""{context}

User question: {question}

Provide a helpful answer based on the domain information above."""

        try:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                answer = result.get('response', '')
                logger.info(f"Ollama answered question about {domain}")
                return answer

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    def generate_domain_strategy(self, domain: str) -> Optional[str]:
        """
        Use Ollama to generate a content strategy for a domain

        Args:
            domain: Domain name

        Returns:
            Strategy text or None
        """
        context = self.build_ollama_context(domain)

        prompt = f"""{context}

Based on this domain's purpose and target audience, generate a content strategy:

1. What type of content should we create?
2. What topics would resonate with the target audience?
3. How often should we publish?
4. What format works best (blog posts, tutorials, videos)?

Provide specific, actionable recommendations."""

        try:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                strategy = result.get('response', '')
                logger.info(f"Generated content strategy for {domain}")
                return strategy

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None


# Convenience function
def get_domain_context(domain: str) -> Optional[Dict]:
    """Get context for a domain"""
    manager = DomainContextManager()
    return manager.get_domain_context(domain)


if __name__ == '__main__':
    # Test domain context
    print("🧪 Testing Domain Context Manager\n")

    manager = DomainContextManager()

    print(f"📊 Loaded {len(manager.get_all_domains())} domains:\n")
    for domain in manager.get_all_domains():
        print(f"   • {domain}")

    print("\n" + "="*60)
    print("\n💬 Domain Context for howtocookathome.com:\n")
    context = manager.build_ollama_context('howtocookathome.com')
    print(context)

    print("\n" + "="*60)
    print("\n📚 All Domains Overview:\n")
    overview = manager.build_all_domains_context()
    print(overview)

    print("\n" + "="*60)
    print("\n🤖 Testing Ollama integration...")
    print("   (Asking: 'What kind of content should I create for howtocookathome.com?')\n")

    answer = manager.ask_ollama_about_domain(
        'howtocookathome.com',
        'What kind of content should I create?'
    )

    if answer:
        print(f"Ollama says:\n{answer}")
    else:
        print("⚠️  Ollama not available. Start with: ollama serve")
