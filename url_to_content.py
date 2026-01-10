#!/usr/bin/env python3
"""
URL to Content Scraper - Extract structured content from any URL

Paste a URL → Get clean, structured content ready for blog posting

Features:
- Auto-detect content type (recipe, article, tutorial, etc.)
- Extract title, headings, paragraphs, images
- Clean HTML → Markdown
- Metadata extraction (author, date, description)
- Zero external API calls (pure Python + BeautifulSoup)

Usage:
    from url_to_content import scrape_url

    content = scrape_url('https://example.com/recipe')
    print(content['title'])
    print(content['content'])
    print(content['images'])
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional
import re
from datetime import datetime


class ContentScraper:
    """
    Intelligent content scraper that extracts structured data from URLs

    Learning: Web scraping 101
    - Fetch HTML with requests
    - Parse with BeautifulSoup
    - Extract semantic content
    - Clean and format for reuse
    """

    def __init__(self, url: str):
        """Initialize scraper with URL"""
        self.url = url
        self.domain = urlparse(url).netloc
        self.soup = None
        self.content_type = 'article'  # Default

    def fetch(self) -> bool:
        """
        Fetch URL and parse HTML

        Returns:
            True if successful, False otherwise
        """
        try:
            # Custom headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Soulfra/1.0; +https://soulfra.com)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse with BeautifulSoup
            self.soup = BeautifulSoup(response.content, 'html.parser')

            return True

        except Exception as e:
            print(f"Error fetching URL: {e}")
            return False

    def detect_content_type(self) -> str:
        """
        Auto-detect content type from page structure

        Returns:
            'recipe', 'tutorial', 'article', 'blog', or 'unknown'
        """
        if not self.soup:
            return 'unknown'

        # Look for recipe indicators
        recipe_indicators = [
            self.soup.find('div', class_=re.compile(r'recipe', re.I)),
            self.soup.find('article', class_=re.compile(r'recipe', re.I)),
            self.soup.find('section', class_=re.compile(r'ingredients', re.I)),
            self.soup.find(attrs={'itemtype': re.compile(r'schema.org/Recipe', re.I)})
        ]

        if any(recipe_indicators):
            return 'recipe'

        # Look for tutorial indicators
        tutorial_indicators = [
            'step-by-step' in str(self.soup).lower(),
            'tutorial' in str(self.soup.title).lower() if self.soup.title else False,
            len(self.soup.find_all(['h2', 'h3'], string=re.compile(r'step \d+', re.I))) > 2
        ]

        if any(tutorial_indicators):
            return 'tutorial'

        # Look for blog post indicators
        blog_indicators = [
            self.soup.find('article'),
            self.soup.find(attrs={'class': re.compile(r'blog|post', re.I)})
        ]

        if any(blog_indicators):
            return 'blog'

        # Default to article
        return 'article'

    def extract_title(self) -> str:
        """Extract page title"""
        if not self.soup:
            return ''

        # Try multiple title sources
        title_sources = [
            self.soup.find('meta', property='og:title'),
            self.soup.find('meta', attrs={'name': 'twitter:title'}),
            self.soup.find('h1'),
            self.soup.title
        ]

        for source in title_sources:
            if source:
                if hasattr(source, 'get'):
                    title = source.get('content', '')
                else:
                    title = source.get_text().strip()

                if title:
                    return title

        return 'Untitled'

    def extract_description(self) -> str:
        """Extract page description/summary"""
        if not self.soup:
            return ''

        # Try meta description
        desc_sources = [
            self.soup.find('meta', property='og:description'),
            self.soup.find('meta', attrs={'name': 'description'}),
            self.soup.find('meta', attrs={'name': 'twitter:description'})
        ]

        for source in desc_sources:
            if source and source.get('content'):
                return source.get('content').strip()

        # Fallback: First paragraph
        first_p = self.soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:200]

        return ''

    def extract_author(self) -> Optional[str]:
        """Extract author name"""
        if not self.soup:
            return None

        author_sources = [
            self.soup.find('meta', attrs={'name': 'author'}),
            self.soup.find('meta', property='article:author'),
            self.soup.find(attrs={'class': re.compile(r'author', re.I)})
        ]

        for source in author_sources:
            if source:
                if hasattr(source, 'get'):
                    author = source.get('content', '')
                else:
                    author = source.get_text().strip()

                if author:
                    return author

        return None

    def extract_date(self) -> Optional[str]:
        """Extract publication date"""
        if not self.soup:
            return None

        date_sources = [
            self.soup.find('meta', property='article:published_time'),
            self.soup.find('time'),
            self.soup.find(attrs={'class': re.compile(r'date|published', re.I)})
        ]

        for source in date_sources:
            if source:
                if hasattr(source, 'get'):
                    date = source.get('content') or source.get('datetime', '')
                else:
                    date = source.get_text().strip()

                if date:
                    return date

        return None

    def extract_content(self) -> str:
        """
        Extract main content as Markdown-like text

        Returns:
            Clean content with headings, paragraphs, lists
        """
        if not self.soup:
            return ''

        # Find main content container
        main_content = self._find_main_content()

        if not main_content:
            return ''

        # Extract structured content
        content_parts = []

        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'blockquote']):
            if element.name.startswith('h'):
                # Heading
                level = int(element.name[1])
                text = element.get_text().strip()
                content_parts.append(f"\n{'#' * level} {text}\n")

            elif element.name == 'p':
                # Paragraph
                text = element.get_text().strip()
                if len(text) > 10:  # Skip very short paragraphs
                    content_parts.append(f"{text}\n")

            elif element.name in ['ul', 'ol']:
                # List
                for li in element.find_all('li', recursive=False):
                    text = li.get_text().strip()
                    content_parts.append(f"- {text}\n")
                content_parts.append('\n')

            elif element.name == 'blockquote':
                # Quote
                text = element.get_text().strip()
                content_parts.append(f"> {text}\n\n")

        return '\n'.join(content_parts).strip()

    def _find_main_content(self):
        """Find the main content container"""
        if not self.soup:
            return None

        # Try common content containers
        content_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.content',
            '.post-content',
            '.article-content',
            '#content',
            '.entry-content'
        ]

        for selector in content_selectors:
            content = self.soup.select_one(selector)
            if content:
                return content

        # Fallback: body
        return self.soup.body

    def extract_images(self) -> List[Dict[str, str]]:
        """
        Extract images with URLs and alt text

        Returns:
            List of dicts with 'url', 'alt', 'caption'
        """
        if not self.soup:
            return []

        images = []
        main_content = self._find_main_content()

        if not main_content:
            return []

        for img in main_content.find_all('img'):
            src = img.get('src', '')

            # Make absolute URL
            if src and not src.startswith('http'):
                src = urljoin(self.url, src)

            # Skip tiny images (likely icons)
            if 'icon' in src.lower() or 'logo' in src.lower():
                continue

            images.append({
                'url': src,
                'alt': img.get('alt', ''),
                'caption': img.get('title', '')
            })

        return images

    def extract_keywords(self) -> List[str]:
        """Extract keywords from content"""
        if not self.soup:
            return []

        # Get keywords from meta tags
        keywords_tag = self.soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            keywords = [k.strip() for k in keywords_tag.get('content').split(',')]
            return keywords[:10]  # Limit to 10

        # Fallback: Extract from title
        title = self.extract_title()
        words = re.findall(r'\b[a-z]{4,}\b', title.lower())
        return words[:5]

    def scrape(self) -> Dict:
        """
        Main scraping method - extracts everything

        Returns:
            Dict with all extracted data
        """
        if not self.fetch():
            return {
                'error': 'Failed to fetch URL',
                'url': self.url
            }

        self.content_type = self.detect_content_type()

        return {
            'url': self.url,
            'domain': self.domain,
            'title': self.extract_title(),
            'description': self.extract_description(),
            'author': self.extract_author(),
            'date': self.extract_date(),
            'content': self.extract_content(),
            'images': self.extract_images(),
            'keywords': self.extract_keywords(),
            'content_type': self.content_type,
            'scraped_at': datetime.now().isoformat()
        }


def scrape_url(url: str) -> Dict:
    """
    Convenience function to scrape a URL

    Args:
        url: URL to scrape

    Returns:
        Dict with extracted content

    Example:
        >>> content = scrape_url('https://example.com/article')
        >>> print(content['title'])
        >>> print(content['content'])
    """
    scraper = ContentScraper(url)
    return scraper.scrape()


# ==============================================================================
# TESTING
# ==============================================================================

def test_scraper():
    """Test the scraper with example URLs"""
    print("=" * 70)
    print("🕷️  URL to Content Scraper - Test Mode")
    print("=" * 70)
    print()

    # Test URLs
    test_urls = [
        'https://example.com',  # Basic test (will work)
        # Add real URLs here for testing
    ]

    print("📝 Testing with example.com...\n")

    content = scrape_url('https://example.com')

    if 'error' in content:
        print(f"❌ Error: {content['error']}")
    else:
        print(f"✅ Title: {content['title']}")
        print(f"✅ Type: {content['content_type']}")
        print(f"✅ Content length: {len(content['content'])} chars")
        print(f"✅ Images found: {len(content['images'])}")
        print(f"✅ Keywords: {', '.join(content['keywords'])}")
        print()
        print("📄 First 300 chars of content:")
        print(content['content'][:300])
        print()

    print("=" * 70)
    print("✅ Scraper ready to use!")
    print()
    print("💡 Usage:")
    print("   from url_to_content import scrape_url")
    print("   content = scrape_url('https://your-url.com')")
    print("   print(content['title'], content['content'])")
    print()


if __name__ == '__main__':
    test_scraper()
