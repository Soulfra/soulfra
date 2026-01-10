#!/usr/bin/env python3
"""
Domain Researcher - AI-powered domain analysis

Ollama uses these tools to research domains:
- Fetch website (HTTP/HTTPS, even without SSL)
- DNS lookup
- Extract metadata
- Analyze content
- Suggest category, emoji, tagline, etc.

Usage:
    from domain_researcher import research_domain

    result = research_domain('myblog.com')
    print(result['suggested'])  # Ollama's suggestions
    print(result['research_data'])  # What Ollama found
"""

import socket
import json
import urllib.request
import urllib.error
import ssl
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
import re


class DomainResearcher:
    """Research a domain using multiple tools"""

    def __init__(self, domain: str):
        """Initialize researcher for a domain"""
        self.domain = domain.lower().strip()
        # Remove http/https if present
        self.domain = self.domain.replace('http://', '').replace('https://', '')
        # Remove trailing slash
        self.domain = self.domain.rstrip('/')
        # Remove www
        if self.domain.startswith('www.'):
            self.domain = self.domain[4:]

    def dns_lookup(self) -> Dict[str, Any]:
        """
        Check if domain exists and get DNS info

        Returns:
            {
                'exists': bool,
                'ip': str or None,
                'error': str or None
            }
        """
        try:
            ip = socket.gethostbyname(self.domain)
            return {
                'exists': True,
                'ip': ip,
                'error': None
            }
        except socket.gaierror as e:
            return {
                'exists': False,
                'ip': None,
                'error': f'Domain not found: {e}'
            }
        except Exception as e:
            return {
                'exists': False,
                'ip': None,
                'error': str(e)
            }

    def fetch_website(self) -> Dict[str, Any]:
        """
        Fetch website content (tries HTTPS then HTTP, ignores SSL errors)

        Returns:
            {
                'success': bool,
                'html': str or None,
                'url': str (final URL after redirects),
                'status_code': int,
                'error': str or None
            }
        """

        # Try HTTPS first (with SSL verification disabled for dev domains)
        for protocol in ['https', 'http']:
            try:
                url = f'{protocol}://{self.domain}'

                # Create SSL context that doesn't verify certificates
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                # Custom headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; Soulfra/1.0; +https://soulfra.com)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

                req = urllib.request.Request(url, headers=headers)

                # Fetch
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    return {
                        'success': True,
                        'html': html,
                        'url': response.url,
                        'status_code': response.status,
                        'error': None,
                        'protocol': protocol
                    }

            except urllib.error.HTTPError as e:
                # Try next protocol
                continue
            except urllib.error.URLError as e:
                # Try next protocol
                continue
            except Exception as e:
                # Try next protocol
                continue

        # Both failed
        return {
            'success': False,
            'html': None,
            'url': None,
            'status_code': None,
            'error': 'Could not fetch website (tried HTTP and HTTPS)',
            'protocol': None
        }

    def extract_metadata(self, html: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML

        Returns:
            {
                'title': str,
                'description': str,
                'keywords': list,
                'og_title': str (Open Graph),
                'og_description': str,
                'content_preview': str (first 500 chars of text)
            }
        """

        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        # Title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else ''

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ''

        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords_str = meta_keywords.get('content', '') if meta_keywords else ''
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

        # Open Graph
        og_title = soup.find('meta', property='og:title')
        og_title = og_title.get('content', '').strip() if og_title else ''

        og_desc = soup.find('meta', property='og:description')
        og_desc = og_desc.get('content', '').strip() if og_desc else ''

        # Extract visible text for content preview
        # Remove script and style tags
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        content_preview = text[:500] if text else ''

        return {
            'title': title or og_title,
            'description': description or og_desc,
            'keywords': keywords,
            'og_title': og_title,
            'og_description': og_desc,
            'content_preview': content_preview
        }

    def analyze_with_ollama(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send research data to Ollama for analysis

        Returns:
            {
                'success': bool,
                'suggested': {
                    'category': str,
                    'name': str,
                    'brand_type': str,
                    'emoji': str,
                    'tagline': str,
                    'target_audience': str,
                    'purpose': str
                },
                'error': str or None
            }
        """

        # Build context for Ollama
        context = f"""Domain: {self.domain}

DNS Status: {'Active (IP: ' + research_data['dns']['ip'] + ')' if research_data['dns']['exists'] else 'Not found / Not configured'}

Website Status: {'Found' if research_data['website']['success'] else 'Not accessible'}
"""

        if research_data['website']['success']:
            meta = research_data['metadata']
            context += f"""
Title: {meta.get('title', 'N/A')}
Description: {meta.get('description', 'N/A')}
Keywords: {', '.join(meta.get('keywords', []))}

Content Preview:
{meta.get('content_preview', 'N/A')}
"""

        # Ollama prompt
        prompt = f"""{context}

Based on the domain name and website research above, suggest details for a website database.

Choose the best category from: cooking, tech, privacy, business, health, art, education, gaming, finance, local

Respond ONLY with valid JSON in this exact format:
{{
  "category": "tech",
  "name": "My Site",
  "brand_type": "blog",
  "emoji": "🚀",
  "tagline": "Short catchy phrase (3-7 words)",
  "target_audience": "Who visits this site",
  "purpose": "What this site does"
}}

JSON response:"""

        try:
            # Call Ollama
            data = json.dumps({
                'model': 'llama3.2:3b',
                'prompt': prompt,
                'stream': False,
                'format': 'json',
                'options': {
                    'temperature': 0.7
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            result = urllib.request.urlopen(req, timeout=60)
            response = json.loads(result.read())

            # Parse Ollama's JSON response
            suggested = json.loads(response['response'])

            # Ensure all fields present
            suggested.setdefault('category', 'tech')
            suggested.setdefault('name', self.domain.split('.')[0].title())
            suggested.setdefault('brand_type', 'blog')
            suggested.setdefault('emoji', '🌐')
            suggested.setdefault('tagline', '')
            suggested.setdefault('target_audience', '')
            suggested.setdefault('purpose', '')

            return {
                'success': True,
                'suggested': suggested,
                'error': None
            }

        except Exception as e:
            # Fallback if Ollama fails
            return {
                'success': False,
                'suggested': {
                    'category': 'tech',
                    'name': self.domain.split('.')[0].title(),
                    'brand_type': 'blog',
                    'emoji': '🌐',
                    'tagline': '',
                    'target_audience': '',
                    'purpose': ''
                },
                'error': f'Ollama error: {e}'
            }


def research_domain(domain: str) -> Dict[str, Any]:
    """
    Research a domain using all available tools

    Returns:
        {
            'domain': str,
            'research_data': {
                'dns': {...},
                'website': {...},
                'metadata': {...}
            },
            'suggested': {
                'category': str,
                'name': str,
                'brand_type': str,
                'emoji': str,
                'tagline': str,
                'target_audience': str,
                'purpose': str
            },
            'errors': list
        }
    """

    researcher = DomainResearcher(domain)
    errors = []

    # DNS lookup
    print(f"[1/3] DNS lookup for {researcher.domain}...")
    dns_data = researcher.dns_lookup()
    if dns_data['error']:
        errors.append(dns_data['error'])

    # Fetch website
    print(f"[2/3] Fetching website...")
    website_data = researcher.fetch_website()
    if website_data['error']:
        errors.append(website_data['error'])

    # Extract metadata
    metadata = {}
    if website_data['success']:
        print(f"[3/3] Extracting metadata...")
        metadata = researcher.extract_metadata(website_data['html'])

    # Build research data
    research_data = {
        'dns': dns_data,
        'website': website_data,
        'metadata': metadata
    }

    # Analyze with Ollama
    print(f"🤖 Analyzing with Ollama...")
    ollama_result = researcher.analyze_with_ollama(research_data)

    if ollama_result['error']:
        errors.append(ollama_result['error'])

    return {
        'domain': researcher.domain,
        'research_data': research_data,
        'suggested': ollama_result['suggested'],
        'errors': errors
    }


# CLI usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 domain_researcher.py <domain>")
        print("Example: python3 domain_researcher.py myblog.com")
        sys.exit(1)

    domain = sys.argv[1]

    print(f"\n🔍 Researching domain: {domain}\n")
    print("="*60)

    result = research_domain(domain)

    print("\n📊 RESEARCH RESULTS")
    print("="*60)

    # DNS
    dns = result['research_data']['dns']
    print(f"\n✅ DNS: {'Active' if dns['exists'] else 'Not found'}")
    if dns['ip']:
        print(f"   IP: {dns['ip']}")

    # Website
    web = result['research_data']['website']
    print(f"\n✅ Website: {'Found' if web['success'] else 'Not accessible'}")
    if web['success']:
        print(f"   URL: {web['url']}")
        print(f"   Protocol: {web['protocol'].upper()}")

    # Metadata
    if result['research_data']['metadata']:
        meta = result['research_data']['metadata']
        print(f"\n✅ Metadata:")
        print(f"   Title: {meta.get('title', 'N/A')}")
        print(f"   Description: {meta.get('description', 'N/A')[:80]}...")

    # Ollama suggestions
    print(f"\n🤖 OLLAMA SUGGESTIONS")
    print("="*60)
    suggested = result['suggested']
    print(f"Name: {suggested['name']}")
    print(f"Category: {suggested['category']}")
    print(f"Emoji: {suggested['emoji']}")
    print(f"Type: {suggested['brand_type']}")
    print(f"Tagline: {suggested['tagline']}")
    print(f"Audience: {suggested['target_audience']}")
    print(f"Purpose: {suggested['purpose']}")

    # Errors
    if result['errors']:
        print(f"\n⚠️  WARNINGS:")
        for error in result['errors']:
            print(f"   - {error}")

    print("\n" + "="*60)
