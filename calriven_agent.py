#!/usr/bin/env python3
"""
Calriven Agent - AI alter ego that scans, processes, and posts automatically

This is the missing piece - the automatic agent that RUNS calriven_post.py daily.

What it does:
1. Scans all 9 domains for content
2. Extracts emails, links, themes
3. Finds connections between domains
4. Posts results to calriven.com using calriven_post.py
5. Builds email lists
6. Generates newsletters

Usage:
    # Run once
    python3 calriven_agent.py

    # Run with scheduling (daily at 3am)
    python3 calriven_agent.py --schedule

    # Run specific task
    python3 calriven_agent.py --task scan_domains
    python3 calriven_agent.py --task extract_emails
    python3 calriven_agent.py --task build_connections
"""

import argparse
import json
import os
import re
import glob
from datetime import datetime
from pathlib import Path
import sys

# ✅ FIXED: Import from cal_auto_publish instead of deleted calriven_post
from cal_auto_publish import create_blog_post, push_to_github


class CalrivenAgent:
    """
    Your AI alter ego - like a dog that digs and does your work

    Scans all domains, extracts data, builds connections, posts results
    """

    def __init__(self):
        self.base_path = Path('/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple')
        self.voice_archive_path = self.base_path / 'voice-archive'
        self.domains_file = self.base_path / 'domains.json'
        self.domains = self.load_domains()

        # Where Calriven stores his findings
        self.output_path = self.voice_archive_path / 'calriven_output'
        self.output_path.mkdir(exist_ok=True)

        print("🤖 Calriven Agent initialized")
        print(f"   Monitoring {len(self.domains)} domains")
        print(f"   Output: {self.output_path}")

    def load_domains(self):
        """Load domain configuration"""
        with open(self.domains_file, 'r') as f:
            data = json.load(f)
        return data['domains']

    def scan_all_domains(self):
        """
        Scan all 9 domains for content

        Returns dict with content from each domain
        """
        print("\n📡 Scanning all domains...")

        results = {}

        for domain in self.domains:
            slug = domain['slug']
            print(f"   Scanning {slug}...")

            # Scan voice-archive markdown files
            content = self.scan_domain_content(slug)

            results[slug] = {
                'domain': domain['domain'],
                'content': content,
                'files_found': len(content['files']),
                'total_words': content['total_words'],
                'scanned_at': datetime.now().isoformat()
            }

        print(f"✅ Scanned {len(results)} domains")
        return results

    def scan_domain_content(self, domain_slug):
        """
        Scan content for a specific domain

        Looks in:
        - voice-archive/{domain_slug}/
        - brands/{domain_slug}/
        - *.md files mentioning domain
        """
        content = {
            'files': [],
            'total_words': 0,
            'emails': [],
            'links': [],
            'themes': []
        }

        # Scan voice-archive
        voice_path = self.voice_archive_path / domain_slug
        if voice_path.exists():
            for md_file in voice_path.glob('**/*.md'):
                content['files'].append(str(md_file))
                text = md_file.read_text()
                content['total_words'] += len(text.split())

                # Extract emails
                emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
                content['emails'].extend(emails)

                # Extract links
                links = re.findall(r'https?://[^\s]+', text)
                content['links'].extend(links)

        # Scan brands/ folder
        brands_path = self.base_path / 'brands' / domain_slug
        if brands_path.exists():
            for md_file in brands_path.glob('**/*.md'):
                content['files'].append(str(md_file))
                text = md_file.read_text()
                content['total_words'] += len(text.split())

        # Deduplicate
        content['emails'] = list(set(content['emails']))
        content['links'] = list(set(content['links']))

        return content

    def extract_emails(self, scan_results):
        """
        Extract all email addresses from scan results

        Builds mailing lists by domain
        """
        print("\n📧 Extracting email addresses...")

        email_lists = {}
        total_emails = 0

        for domain_slug, data in scan_results.items():
            emails = data['content']['emails']
            email_lists[domain_slug] = {
                'count': len(emails),
                'emails': emails,
                'domain': data['domain']
            }
            total_emails += len(emails)

        # Save to file
        output_file = self.output_path / f'email-lists-{datetime.now().strftime("%Y-%m-%d")}.json'
        with open(output_file, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_subscribers': total_emails,
                'by_domain': email_lists
            }, f, indent=2)

        print(f"✅ Found {total_emails} email addresses")
        print(f"   Saved to: {output_file}")

        return email_lists

    def find_connections(self, scan_results):
        """
        Find connections between domains

        Looks for:
        - Shared links
        - Common themes/keywords
        - Cross-references
        """
        print("\n🔗 Finding connections between domains...")

        connections = []

        domains = list(scan_results.keys())

        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                # Find shared links
                links1 = set(scan_results[domain1]['content']['links'])
                links2 = set(scan_results[domain2]['content']['links'])
                shared_links = links1.intersection(links2)

                if shared_links:
                    connections.append({
                        'domain1': domain1,
                        'domain2': domain2,
                        'shared_links': list(shared_links),
                        'connection_type': 'shared_urls',
                        'strength': len(shared_links)
                    })

        print(f"✅ Found {len(connections)} connections")
        return connections

    def compare_domains(self, scan_results):
        """
        Compare domains to find themes and overlaps

        Returns analysis of how domains relate
        """
        print("\n📊 Comparing domains...")

        comparison = {
            'generated_at': datetime.now().isoformat(),
            'domains': {}
        }

        for domain_slug, data in scan_results.items():
            comparison['domains'][domain_slug] = {
                'files': data['files_found'],
                'words': data['total_words'],
                'emails': len(data['content']['emails']),
                'links': len(data['content']['links']),
                'domain_url': data['domain']
            }

        return comparison

    def post_daily_report(self, scan_results, email_lists, connections):
        """
        Post daily report to calriven.com

        Uses existing calriven_post.py to create post
        """
        print("\n📝 Creating daily report...")

        today = datetime.now().strftime('%Y-%m-%d')

        # Build markdown content
        content = f"""# Calriven Daily Report - {today}

## Network Scan Summary

Scanned **{len(scan_results)} domains** across the Soulfra network.

### Domain Activity

"""

        for domain_slug, data in scan_results.items():
            content += f"""**{domain_slug}.com**
- Files scanned: {data['files_found']}
- Total words: {data['total_words']:,}
- Emails found: {len(data['content']['emails'])}
- Links extracted: {len(data['content']['links'])}

"""

        content += f"""## Email Lists

Total subscribers across network: **{sum(lst['count'] for lst in email_lists.values())}**

"""

        for domain_slug, lst in email_lists.items():
            content += f"- {domain_slug}: {lst['count']} emails\n"

        content += f"""

## Connections Found

Discovered **{len(connections)}** cross-domain connections.

"""

        for conn in connections[:5]:  # Top 5
            content += f"- {conn['domain1']} ↔ {conn['domain2']}: {conn['strength']} shared links\n"

        content += """

## Next Steps

- Building email lists for newsletters
- Generating cross-domain link maps
- Analyzing content themes

---

*🤖 Generated automatically by Calriven Agent*
*Like a dog that digs and does your work - but you can see where I bury my findings!*
"""

        # ✅ FIXED: Post using cal_auto_publish.py
        try:
            title = f'Daily Network Report - {today}'

            # Create blog post
            filepath = create_blog_post(title, content, author="Calriven")
            print(f"✅ Created blog post: {filepath}")

            # Push to GitHub
            commit_message = "🤖 Calriven daily report"
            push_to_github(filepath, commit_message)
            print(f"✅ Posted daily report to calriven.com")

            return filepath

        except Exception as e:
            print(f"❌ Error posting daily report: {e}")
            return None

    def generate_newsletter(self, scan_results):
        """
        Generate newsletter content

        Creates weekly roundup of activity across domains
        """
        print("\n📰 Generating newsletter...")

        week = datetime.now().strftime('%Y-W%V')

        content = f"""# Soulfra Network Newsletter - {week}

## This Week Across the Network

"""

        for domain_slug, data in scan_results.items():
            domain_obj = next(d for d in self.domains if d['slug'] == domain_slug)
            content += f"""### {domain_obj['name']} ({domain_obj['domain']})
*{domain_obj['tagline']}*

- Active files: {data['files_found']}
- Content volume: {data['total_words']:,} words

"""

        content += """

---

*🤖 Curated by Calriven*
*Unsubscribe: [Link would go here]*
"""

        # Save to file
        output_file = self.output_path / f'newsletter-{week}.md'
        output_file.write_text(content)

        print(f"✅ Newsletter generated: {output_file}")
        return content

    def run_all_tasks(self):
        """
        Run all Calriven tasks in sequence

        This is the main "dog does your work" function
        """
        print("\n🐕 Calriven starting work...")
        print("   (Like a dog: loyal, tireless, always digging)")

        # Task 1: Scan all domains
        scan_results = self.scan_all_domains()

        # Task 2: Extract emails
        email_lists = self.extract_emails(scan_results)

        # Task 3: Find connections
        connections = self.find_connections(scan_results)

        # Task 4: Post daily report
        report = self.post_daily_report(scan_results, email_lists, connections)

        # Task 5: Generate newsletter
        newsletter = self.generate_newsletter(scan_results)

        print("\n✅ Calriven finished all tasks!")
        print("   Check calriven.com for results")

        return {
            'scan_results': scan_results,
            'email_lists': email_lists,
            'connections': connections,
            'report': report,
            'newsletter': newsletter
        }


def main():
    parser = argparse.ArgumentParser(
        description='Calriven Agent - AI that scans, processes, and posts automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--task',
                       choices=['scan_domains', 'extract_emails', 'build_connections', 'post_report', 'newsletter', 'all'],
                       default='all',
                       help='Specific task to run (default: all)')

    parser.add_argument('--schedule', action='store_true',
                       help='Run on schedule (daily at 3am)')

    args = parser.parse_args()

    agent = CalrivenAgent()

    if args.schedule:
        try:
            import schedule
            import time

            print("⏰ Scheduling Calriven to run daily at 3:00 AM")
            print("   Press Ctrl+C to stop")

            schedule.every().day.at("03:00").do(agent.run_all_tasks)

            while True:
                schedule.run_pending()
                time.sleep(60)

        except ImportError:
            print("❌ 'schedule' module not installed")
            print("   Install with: pip install schedule")
            sys.exit(1)
    else:
        # Run once
        if args.task == 'scan_domains':
            agent.scan_all_domains()
        elif args.task == 'extract_emails':
            results = agent.scan_all_domains()
            agent.extract_emails(results)
        elif args.task == 'build_connections':
            results = agent.scan_all_domains()
            agent.find_connections(results)
        elif args.task == 'post_report':
            results = agent.scan_all_domains()
            emails = agent.extract_emails(results)
            connections = agent.find_connections(results)
            agent.post_daily_report(results, emails, connections)
        elif args.task == 'newsletter':
            results = agent.scan_all_domains()
            agent.generate_newsletter(results)
        else:  # all
            agent.run_all_tasks()


if __name__ == '__main__':
    main()
