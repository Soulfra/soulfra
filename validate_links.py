#!/usr/bin/env python3
"""
Validate All Links Across Soulfra Ecosystem

Checks all HTML files, markdown files, and JSON files for broken links.
"""

import os
import re
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from typing import List, Dict, Set

class LinkValidator:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.checked_urls: Set[str] = set()

    def validate_all(self):
        """Validate all links in the project"""
        print("🔍 Scanning for links...")

        # Check HTML files
        for html_file in self.root_dir.rglob("*.html"):
            if ".git" not in str(html_file):
                self._check_html_file(html_file)

        # Check Markdown files
        for md_file in self.root_dir.rglob("*.md"):
            if ".git" not in str(md_file):
                self._check_markdown_file(md_file)

        # Check JSON files
        for json_file in self.root_dir.rglob("*.json"):
            if ".git" not in str(json_file) and "node_modules" not in str(json_file):
                self._check_json_file(json_file)

        self._print_report()

    def _check_html_file(self, file_path: Path):
        """Check all links in an HTML file"""
        try:
            content = file_path.read_text()

            # Find all href links
            href_pattern = r'href=["\']([^"\']+)["\']'
            for match in re.finditer(href_pattern, content):
                url = match.group(1)
                self._validate_link(url, file_path, "href")

            # Find all src links
            src_pattern = r'src=["\']([^"\']+)["\']'
            for match in re.finditer(src_pattern, content):
                url = match.group(1)
                self._validate_link(url, file_path, "src")

        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Failed to read file: {e}"
            })

    def _check_markdown_file(self, file_path: Path):
        """Check all links in a Markdown file"""
        try:
            content = file_path.read_text()

            # Find all markdown links [text](url)
            md_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            for match in re.finditer(md_pattern, content):
                url = match.group(2)
                self._validate_link(url, file_path, "markdown")

        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': f"Failed to read file: {e}"
            })

    def _check_json_file(self, file_path: Path):
        """Check all URLs in JSON files"""
        try:
            with open(file_path) as f:
                data = json.load(f)

            self._extract_urls_from_json(data, file_path)

        except Exception as e:
            self.warnings.append({
                'file': str(file_path),
                'warning': f"Failed to parse JSON: {e}"
            })

    def _extract_urls_from_json(self, obj, file_path: Path, path: str = ""):
        """Recursively extract URLs from JSON"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and (value.startswith('http') or value.startswith('/')):
                    self._validate_link(value, file_path, f"json:{new_path}")
                else:
                    self._extract_urls_from_json(value, file_path, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._extract_urls_from_json(item, file_path, f"{path}[{i}]")

    def _validate_link(self, url: str, file_path: Path, link_type: str):
        """Validate a single link"""
        # Skip anchor links, mailto, tel, etc.
        if url.startswith('#') or url.startswith('mailto:') or url.startswith('tel:'):
            return

        # Check if it's a relative path
        if not url.startswith('http'):
            self._validate_relative_path(url, file_path, link_type)
        else:
            self._validate_external_url(url, file_path, link_type)

    def _validate_relative_path(self, path: str, file_path: Path, link_type: str):
        """Validate a relative file path"""
        # Remove query strings and anchors
        path = path.split('?')[0].split('#')[0]

        # Resolve the path relative to the file
        file_dir = file_path.parent
        full_path = (file_dir / path).resolve()

        if not full_path.exists():
            self.errors.append({
                'file': str(file_path),
                'link': path,
                'type': link_type,
                'error': 'File not found (relative path)'
            })

    def _validate_external_url(self, url: str, file_path: Path, link_type: str):
        """Validate an external URL (cached)"""
        # Skip localhost URLs
        if 'localhost' in url or '127.0.0.1' in url or '192.168' in url:
            return

        # Only check each URL once
        if url in self.checked_urls:
            return

        self.checked_urls.add(url)

        try:
            # HEAD request to check if URL exists
            response = requests.head(url, timeout=5, allow_redirects=True)

            if response.status_code >= 400:
                self.errors.append({
                    'file': str(file_path),
                    'link': url,
                    'type': link_type,
                    'error': f'HTTP {response.status_code}'
                })
        except requests.exceptions.RequestException as e:
            self.warnings.append({
                'file': str(file_path),
                'link': url,
                'type': link_type,
                'warning': f'Could not check: {str(e)[:50]}'
            })

    def _print_report(self):
        """Print validation report"""
        print("\n" + "="*60)
        print("📊 LINK VALIDATION REPORT")
        print("="*60)

        if not self.errors and not self.warnings:
            print("\n✅ All links are valid!")
            return

        if self.errors:
            print(f"\n❌ {len(self.errors)} ERRORS FOUND:")
            print("-" * 60)
            for error in self.errors:
                print(f"\n📁 File: {error['file']}")
                print(f"   🔗 Link: {error.get('link', 'N/A')}")
                print(f"   📝 Type: {error.get('type', 'N/A')}")
                print(f"   ⚠️  Error: {error['error']}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} WARNINGS:")
            print("-" * 60)
            for warning in self.warnings:
                print(f"\n📁 File: {warning['file']}")
                if 'link' in warning:
                    print(f"   🔗 Link: {warning['link']}")
                print(f"   📝 Warning: {warning['warning']}")

        print("\n" + "="*60)
        print(f"✅ Checked {len(self.checked_urls)} unique external URLs")
        print("="*60 + "\n")


if __name__ == '__main__':
    validator = LinkValidator(".")
    validator.validate_all()
