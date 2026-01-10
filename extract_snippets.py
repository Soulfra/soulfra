#!/usr/bin/env python3
"""
Extract Code Snippets from Documentation

Scans all markdown files and extracts code blocks.
Useful for testing, examples, and reusing documented code.

Usage:
    python3 extract_snippets.py                    # Extract all snippets
    python3 extract_snippets.py --lang python      # Only Python snippets
    python3 extract_snippets.py --save snippets/   # Save to directory
"""

import re
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
import argparse


class SnippetExtractor:
    """Extract and manage code snippets from markdown documentation"""

    def __init__(self, docs_dir: str = "."):
        self.docs_dir = Path(docs_dir)
        self.snippets: List[Dict] = []

    def scan_all_docs(self) -> int:
        """
        Scan all markdown files in the docs directory
        Returns number of snippets found
        """
        count = 0

        for md_file in self.docs_dir.glob("*.md"):
            # Skip README (too generic)
            if md_file.name.lower() == 'readme.md':
                continue

            snippets = self.extract_from_file(md_file)
            count += len(snippets)

            for snippet in snippets:
                snippet['source_file'] = md_file.name

            self.snippets.extend(snippets)

        return count

    def extract_from_file(self, filepath: Path) -> List[Dict]:
        """
        Extract all code blocks from a markdown file
        Returns list of snippet dicts
        """
        snippets = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Pattern: ```language\ncode\n```
            pattern = r'```(\w+)\n(.*?)```'
            matches = re.finditer(pattern, content, re.DOTALL)

            for i, match in enumerate(matches, 1):
                language = match.group(1)
                code = match.group(2).strip()

                # Get context (heading before code block)
                context = self._get_context(content, match.start())

                snippets.append({
                    'id': i,
                    'language': language,
                    'code': code,
                    'lines': len(code.split('\n')),
                    'context': context,
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })

        except Exception as e:
            print(f"Error reading {filepath.name}: {e}", file=sys.stderr)

        return snippets

    def _get_context(self, content: str, pos: int) -> str:
        """
        Get the heading/context before a code block
        Searches backwards for the nearest # heading
        """
        lines_before = content[:pos].split('\n')

        # Search backwards for heading
        for line in reversed(lines_before[-10:]):  # Check last 10 lines
            if line.startswith('#'):
                # Remove # symbols and emoji
                heading = re.sub(r'^#+\s*', '', line)
                heading = re.sub(r'[^\w\s-]', '', heading).strip()
                return heading

        return "No context"

    def filter_by_language(self, language: str) -> List[Dict]:
        """
        Filter snippets by programming language
        Returns filtered list
        """
        return [s for s in self.snippets if s['language'].lower() == language.lower()]

    def save_to_files(self, output_dir: str):
        """
        Save each snippet to a separate file
        Organized by language and source doc
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for snippet in self.snippets:
            lang = snippet['language']
            source = snippet['source_file'].replace('.md', '')
            snippet_id = snippet['id']

            # Create language directory
            lang_dir = output_path / lang
            lang_dir.mkdir(exist_ok=True)

            # Determine file extension
            ext = self._get_extension(lang)

            # Save snippet
            filename = f"{source}_{snippet_id:02d}.{ext}"
            filepath = lang_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Source: {snippet['source_file']}\n")
                f.write(f"# Context: {snippet['context']}\n")
                f.write(f"# Language: {lang}\n\n")
                f.write(snippet['code'])

            print(f"Saved: {filepath}")

    def save_to_json(self, output_file: str):
        """
        Save all snippets to a JSON file
        Useful for programmatic access
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.snippets, f, indent=2)

        print(f"Saved {len(self.snippets)} snippets to {output_file}")

    def _get_extension(self, language: str) -> str:
        """
        Get file extension for a programming language
        """
        extensions = {
            'python': 'py',
            'bash': 'sh',
            'javascript': 'js',
            'typescript': 'ts',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'json': 'json',
            'yaml': 'yml',
            'markdown': 'md',
            'nginx': 'conf',
            'ini': 'ini',
            'toml': 'toml',
            'dockerfile': 'dockerfile',
            'go': 'go',
            'rust': 'rs',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'ruby': 'rb',
            'php': 'php',
        }

        return extensions.get(language.lower(), 'txt')

    def print_summary(self):
        """
        Print a summary of all snippets found
        """
        print("\n" + "="*60)
        print("📚 DOCUMENTATION CODE SNIPPETS SUMMARY")
        print("="*60 + "\n")

        # Total count
        print(f"Total snippets: {len(self.snippets)}\n")

        # Count by language
        lang_counts = {}
        for snippet in self.snippets:
            lang = snippet['language']
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        print("By Language:")
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang:15} {count:4} snippets")

        print()

        # Count by source file
        file_counts = {}
        for snippet in self.snippets:
            source = snippet['source_file']
            file_counts[source] = file_counts.get(source, 0) + 1

        print("By Source File (top 10):")
        for source, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {source:40} {count:4} snippets")

        print("\n" + "="*60 + "\n")

    def print_snippets(self, limit: Optional[int] = None):
        """
        Print snippets to console
        """
        snippets_to_print = self.snippets[:limit] if limit else self.snippets

        for snippet in snippets_to_print:
            print("\n" + "-"*60)
            print(f"Source: {snippet['source_file']}")
            print(f"Context: {snippet['context']}")
            print(f"Language: {snippet['language']}")
            print(f"Lines: {snippet['lines']}")
            print("-"*60)
            print(snippet['code'])
            print("-"*60)


def main():
    parser = argparse.ArgumentParser(
        description="Extract code snippets from markdown documentation"
    )

    parser.add_argument(
        '--lang',
        type=str,
        help='Filter by programming language (e.g., python, bash, javascript)'
    )

    parser.add_argument(
        '--save',
        type=str,
        metavar='DIR',
        help='Save snippets to files in specified directory'
    )

    parser.add_argument(
        '--json',
        type=str,
        metavar='FILE',
        help='Save snippets to JSON file'
    )

    parser.add_argument(
        '--print',
        action='store_true',
        help='Print snippets to console'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of snippets to print'
    )

    parser.add_argument(
        '--docs-dir',
        type=str,
        default='.',
        help='Directory containing markdown docs (default: current directory)'
    )

    args = parser.parse_args()

    # Create extractor
    extractor = SnippetExtractor(docs_dir=args.docs_dir)

    # Scan all docs
    print(f"📖 Scanning markdown files in {extractor.docs_dir}...")
    count = extractor.scan_all_docs()
    print(f"✅ Found {count} code snippets in {len(list(extractor.docs_dir.glob('*.md')))} files\n")

    # Filter by language if specified
    if args.lang:
        filtered = extractor.filter_by_language(args.lang)
        extractor.snippets = filtered
        print(f"🔍 Filtered to {len(filtered)} {args.lang} snippets\n")

    # Print summary (always)
    extractor.print_summary()

    # Save to files if requested
    if args.save:
        print(f"\n💾 Saving snippets to {args.save}/...")
        extractor.save_to_files(args.save)

    # Save to JSON if requested
    if args.json:
        print(f"\n💾 Saving snippets to {args.json}...")
        extractor.save_to_json(args.json)

    # Print snippets if requested
    if args.print:
        extractor.print_snippets(limit=args.limit)


if __name__ == '__main__':
    main()
