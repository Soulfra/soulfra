#!/usr/bin/env python3
"""
Share Points System - Cross-domain linking for the Soulfra network

Creates "share points" (clickable links) that connect related content across
all 9 domains, building a web of interconnected content.

What it does:
1. Finds related content across domains (using semantic similarity)
2. Generates cross-domain links ("share points")
3. Posts links to relevant domains
4. Builds navigation web

Example:
    Document: "Privacy Email List Guide" on deathtodata.com
    Share points created:
    - soulfra.com/cross-ref/privacy-email-guide (technical perspective)
    - calriven.com/analysis/privacy-email-guide (AI analysis)
    - cringeproof.com/easy-version/privacy-email-guide (simplified)

Usage:
    # Create share points for a document
    python3 share_points.py --file voice-archive/docs/OSI_7_LAYER.md

    # Find connections for all docs in a domain
    python3 share_points.py --domain deathtodata

    # Build full network connection graph
    python3 share_points.py --build-graph
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
import sys

# Import existing calriven_post functionality
sys.path.insert(0, '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple')
from archive.experiments.calriven_post import create_ai_post


class SharePointsSystem:
    """
    Builds cross-domain connections ("the knot")

    Creates share points that link related content across all 9 domains
    """

    def __init__(self):
        self.base_path = Path('/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple')
        self.voice_archive_path = self.base_path / 'voice-archive'
        self.domains_file = self.base_path / 'domains.json'
        self.domains = self.load_domains()

        # Where share points are stored
        self.share_points_path = self.voice_archive_path / 'share_points'
        self.share_points_path.mkdir(exist_ok=True)

        print("🔗 Share Points System initialized")
        print(f"   {len(self.domains)} domains in network")

    def load_domains(self):
        """Load domain configuration"""
        with open(self.domains_file, 'r') as f:
            data = json.load(f)
        return data['domains']

    def extract_keywords(self, text):
        """
        Extract keywords from text content

        Returns list of important keywords for matching
        """
        # Remove markdown formatting
        text = re.sub(r'[#*`]', '', text)

        # Common technical/content keywords to look for
        keywords = []

        # Extract capitalized phrases (likely important concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        keywords.extend(capitalized)

        # Extract code/technical terms
        code_terms = re.findall(r'`([^`]+)`', text)
        keywords.extend(code_terms)

        # Deduplicate
        return list(set(keywords))

    def find_related_docs(self, doc_path, content):
        """
        Find related documents across all domains

        Uses keyword matching and semantic similarity
        Returns list of related document paths
        """
        print(f"\n🔍 Finding related docs for: {doc_path.name}")

        doc_keywords = self.extract_keywords(content)
        related = []

        # Search across all markdown files in voice-archive
        for md_file in self.voice_archive_path.glob('**/*.md'):
            if md_file == doc_path:
                continue  # Skip self

            try:
                other_content = md_file.read_text()
                other_keywords = self.extract_keywords(other_content)

                # Find overlap
                overlap = set(doc_keywords).intersection(set(other_keywords))

                if len(overlap) >= 3:  # At least 3 shared keywords
                    related.append({
                        'path': str(md_file),
                        'keywords_match': list(overlap),
                        'strength': len(overlap)
                    })
            except Exception as e:
                pass  # Skip files that can't be read

        # Sort by connection strength
        related.sort(key=lambda x: x['strength'], reverse=True)

        print(f"   Found {len(related)} related documents")
        return related[:10]  # Top 10

    def determine_domain_for_doc(self, doc_path):
        """
        Determine which domain a document belongs to

        Based on path structure or content analysis
        """
        path_str = str(doc_path)

        for domain in self.domains:
            slug = domain['slug']
            if f'/{slug}/' in path_str or path_str.endswith(f'{slug}.md'):
                return slug

        # Default to soulfra if unclear
        return 'soulfra'

    def create_share_points(self, doc_path):
        """
        Generate cross-domain share points for a document

        Returns list of share point URLs
        """
        print(f"\n📍 Creating share points for: {doc_path.name}")

        # Read document
        content = doc_path.read_text()

        # Find related documents
        related_docs = self.find_related_docs(doc_path, content)

        if not related_docs:
            print("   No related documents found")
            return []

        # Generate share point URLs
        share_points = []

        doc_slug = doc_path.stem  # Filename without extension
        primary_domain = self.determine_domain_for_doc(doc_path)

        for related in related_docs:
            related_path = Path(related['path'])
            related_domain = self.determine_domain_for_doc(related_path)

            # Create cross-reference URL
            share_url = f"https://{related_domain}.com/cross-ref/{doc_slug}"

            share_points.append({
                'url': share_url,
                'domain': related_domain,
                'related_doc': related_path.name,
                'connection_strength': related['strength'],
                'shared_keywords': related['keywords_match']
            })

        print(f"   Created {len(share_points)} share points")
        return share_points

    def post_cross_reference(self, doc_path, share_point):
        """
        Post a cross-reference link on a domain

        Creates a small post saying "Related content from X domain"
        """
        domain_slug = share_point['domain']
        doc_slug = doc_path.stem

        content = f"""# Cross-Reference: {doc_path.stem.replace('-', ' ').title()}

This content is related to material on {self.determine_domain_for_doc(doc_path)}.com.

## Connection

Shared themes: {', '.join(share_point['shared_keywords'][:5])}

Connection strength: {share_point['connection_strength']} shared keywords

## Read More

[View on {self.determine_domain_for_doc(doc_path)}.com →](https://{ self.determine_domain_for_doc(doc_path)}.com/docs/{doc_slug})

---

*🔗 Auto-generated share point by Calriven*
"""

        try:
            result = create_ai_post(
                ai_username='calriven',
                title=f'Cross-ref: {doc_path.stem.replace("-", " ").title()}',
                slug=f'cross-ref-{doc_slug}-{domain_slug}',
                content_markdown=content,
                tags=['cross-reference', 'share-point', domain_slug]
            )

            if result:
                print(f"   ✅ Posted cross-reference to {domain_slug}")
            return result
        except Exception as e:
            print(f"   ❌ Error posting to {domain_slug}: {e}")
            return None

    def build_connection_graph(self):
        """
        Build full network connection graph

        Shows how all domains are connected through content
        """
        print("\n🕸️  Building full network connection graph...")

        graph = {
            'generated_at': datetime.now().isoformat(),
            'domains': {},
            'connections': []
        }

        # Scan all markdown files
        all_docs = list(self.voice_archive_path.glob('**/*.md'))

        print(f"   Analyzing {len(all_docs)} documents...")

        for doc in all_docs:
            domain = self.determine_domain_for_doc(doc)

            if domain not in graph['domains']:
                graph['domains'][domain] = {
                    'docs': [],
                    'connections': []
                }

            graph['domains'][domain]['docs'].append(doc.name)

            # Find connections
            try:
                content = doc.read_text()
                related = self.find_related_docs(doc, content)

                for rel in related:
                    rel_domain = self.determine_domain_for_doc(Path(rel['path']))

                    if rel_domain != domain:
                        graph['connections'].append({
                            'from_domain': domain,
                            'to_domain': rel_domain,
                            'from_doc': doc.name,
                            'to_doc': Path(rel['path']).name,
                            'strength': rel['strength']
                        })
            except Exception as e:
                pass

        # Save graph
        graph_file = self.share_points_path / 'connection-graph.json'
        with open(graph_file, 'w') as f:
            json.dump(graph, f, indent=2)

        print(f"✅ Connection graph built: {graph_file}")
        print(f"   Total connections: {len(graph['connections'])}")

        return graph

    def generate_share_points_report(self, doc_path):
        """
        Generate a report showing all share points for a document

        Posts to calriven.com
        """
        share_points = self.create_share_points(doc_path)

        if not share_points:
            print("No share points to report")
            return None

        content = f"""# Share Points Report: {doc_path.stem.replace('-', ' ').title()}

Generated {len(share_points)} share points across the network.

## Cross-Domain Links

"""

        for sp in share_points:
            content += f"""### {sp['domain'].title()}
- URL: {sp['url']}
- Connection strength: {sp['connection_strength']}
- Shared concepts: {', '.join(sp['shared_keywords'][:3])}

"""

        content += """

---

*🔗 Generated by Share Points System*
*Building the web of interconnected content*
"""

        try:
            result = create_ai_post(
                ai_username='calriven',
                title=f'Share Points: {doc_path.stem.replace("-", " ").title()}',
                slug=f'share-points-{doc_path.stem}',
                content_markdown=content,
                tags=['share-points', 'connections', 'network']
            )

            if result:
                print(f"\n✅ Posted share points report to calriven.com")
            return result
        except Exception as e:
            print(f"\n❌ Error posting report: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Share Points System - Cross-domain linking',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--file', help='Document file to create share points for')
    parser.add_argument('--domain', help='Find connections for all docs in domain')
    parser.add_argument('--build-graph', action='store_true',
                       help='Build full network connection graph')

    args = parser.parse_args()

    system = SharePointsSystem()

    if args.build_graph:
        system.build_connection_graph()

    elif args.file:
        doc_path = Path(args.file)
        if not doc_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

        share_points = system.create_share_points(doc_path)
        system.generate_share_points_report(doc_path)

    elif args.domain:
        # Find all docs in domain
        domain_path = system.voice_archive_path / args.domain
        if not domain_path.exists():
            print(f"❌ Domain path not found: {domain_path}")
            sys.exit(1)

        docs = list(domain_path.glob('**/*.md'))
        print(f"Found {len(docs)} documents in {args.domain}")

        for doc in docs:
            system.create_share_points(doc)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
