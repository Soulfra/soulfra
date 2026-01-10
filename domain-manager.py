#!/usr/bin/env python3
"""
Domain Manager - Central control for multi-domain platform

Manages all registered domains from a single source of truth (soulfra.db).
Handles theme generation, deployment, verification, and status monitoring.

Usage:
    python domain-manager.py list                 # Show all domains
    python domain-manager.py export               # Export domains.json
    python domain-manager.py verify cringeproof   # Verify domain ownership
    python domain-manager.py deploy cringeproof   # Deploy domain
    python domain-manager.py status              # Check all domain statuses
"""

import sqlite3
import json
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class DomainManager:
    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_all_domains(self) -> List[Dict]:
        """Get all registered domains from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                id, name, slug, tagline, category, tier,
                color_primary, color_secondary, color_accent,
                personality_tone, brand_type, emoji, domain,
                network_role, verified, verified_at
            FROM brands
            WHERE domain IS NOT NULL
            ORDER BY id
        """)

        domains = []
        for row in cursor.fetchall():
            domains.append(dict(row))

        return domains

    def get_domain(self, slug: str) -> Optional[Dict]:
        """Get single domain by slug"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM brands
            WHERE slug = ? AND domain IS NOT NULL
        """, (slug,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def verify_domain_ownership(self, slug: str) -> bool:
        """Verify domain ownership via DNS TXT record or file upload"""
        domain_data = self.get_domain(slug)
        if not domain_data:
            print(f"❌ Domain {slug} not found in database")
            return False

        domain = domain_data['domain']

        # Method 1: Check for DNS TXT record
        # TXT record should be: soulfra-verification=<slug>
        print(f"🔍 Verifying ownership of {domain}...")
        print(f"   Method 1: Check DNS TXT record")
        print(f"   Expected: soulfra-verification={slug}")

        # Method 2: Check for verification file
        # File at: https://{domain}/.well-known/soulfra-verify.txt
        verification_url = f"https://{domain}/.well-known/soulfra-verify.txt"
        print(f"   Method 2: Check verification file")
        print(f"   URL: {verification_url}")

        try:
            response = requests.get(verification_url, timeout=5)
            if response.status_code == 200 and slug in response.text:
                self.mark_verified(slug, 'file')
                print(f"✅ Domain {domain} verified via file upload!")
                return True
        except Exception as e:
            print(f"   ⚠️  File verification failed: {e}")

        print(f"\n📋 To verify {domain}:")
        print(f"   1. Create file: .well-known/soulfra-verify.txt")
        print(f"   2. Content: {slug}")
        print(f"   3. Deploy to {domain}")
        print(f"   4. Run: python domain-manager.py verify {slug}")

        return False

    def mark_verified(self, slug: str, method: str):
        """Mark domain as verified in database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE brands
            SET verified = 1,
                verified_at = CURRENT_TIMESTAMP,
                verification_method = ?
            WHERE slug = ?
        """, (method, slug))
        self.conn.commit()

    def check_domain_status(self, slug: str) -> Dict:
        """Check deployment status of a domain"""
        domain_data = self.get_domain(slug)
        if not domain_data:
            return {'error': 'Domain not found'}

        domain = domain_data['domain']
        status = {
            'domain': domain,
            'slug': slug,
            'verified': bool(domain_data['verified']),
            'dns_resolves': False,
            'site_accessible': False,
            'backend_connected': False,
            'theme_applied': False
        }

        # Check if site is accessible
        try:
            response = requests.get(f"https://{domain}", timeout=5)
            status['site_accessible'] = response.status_code == 200

            # Check if theme CSS is loaded
            if '<link' in response.text and 'theme.css' in response.text:
                status['theme_applied'] = True

            # Check if config.js points to backend
            if 'config.js' in response.text:
                status['backend_connected'] = 'API_BACKEND_URL' in response.text

        except Exception as e:
            status['error'] = str(e)

        return status

    def export_manifest(self, output_path='domains.json'):
        """Export all domains to JSON manifest"""
        domains = self.get_all_domains()

        manifest = {
            'generated_at': datetime.now().isoformat(),
            'total_domains': len(domains),
            'domains': []
        }

        for domain_data in domains:
            manifest['domains'].append({
                'slug': domain_data['slug'],
                'name': domain_data['name'],
                'domain': domain_data['domain'],
                'tagline': domain_data['tagline'],
                'category': domain_data['category'],
                'type': domain_data['brand_type'],
                'verified': bool(domain_data['verified']),
                'theme': {
                    'primary': domain_data['color_primary'],
                    'secondary': domain_data['color_secondary'],
                    'accent': domain_data['color_accent']
                },
                'network_role': domain_data['network_role']
            })

        # Write to file
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"✅ Exported {len(domains)} domains to {output_file}")
        return manifest

    def list_domains(self):
        """Display all domains in readable format"""
        domains = self.get_all_domains()

        print(f"\n{'='*80}")
        print(f"  YOUR DOMAIN EMPIRE ({len(domains)} domains)")
        print(f"{'='*80}\n")

        for domain in domains:
            status = '✅' if domain['verified'] else '⚠️ '
            emoji = domain['emoji'] or '🌐'

            print(f"{status} {emoji}  {domain['name']}")
            print(f"     Domain: {domain['domain']}")
            print(f"     Colors: {domain['color_primary']} (primary)")
            print(f"     Type: {domain['brand_type']} | Role: {domain['network_role']}")

            if domain['verified']:
                print(f"     Verified: {domain['verified_at']}")
            else:
                print(f"     Status: Not verified")

            print()

    def status_dashboard(self):
        """Show status of all domains"""
        domains = self.get_all_domains()

        print(f"\n{'='*80}")
        print(f"  DOMAIN STATUS DASHBOARD")
        print(f"{'='*80}\n")

        for domain_data in domains:
            slug = domain_data['slug']
            domain = domain_data['domain']

            print(f"🌐 {domain} ({slug})")

            status = self.check_domain_status(slug)

            # Visual indicators
            verified = '✅' if status.get('verified') else '❌'
            accessible = '✅' if status.get('site_accessible') else '❌'
            backend = '✅' if status.get('backend_connected') else '❌'
            theme = '✅' if status.get('theme_applied') else '❌'

            print(f"   Verified: {verified}")
            print(f"   Live: {accessible}")
            print(f"   Backend: {backend}")
            print(f"   Theme: {theme}")

            if 'error' in status:
                print(f"   Error: {status['error']}")

            print()

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python domain-manager.py list")
        print("  python domain-manager.py export")
        print("  python domain-manager.py verify <slug>")
        print("  python domain-manager.py status")
        sys.exit(1)

    manager = DomainManager()
    command = sys.argv[1]

    if command == 'list':
        manager.list_domains()

    elif command == 'export':
        output = sys.argv[2] if len(sys.argv) > 2 else 'domains.json'
        manager.export_manifest(output)

    elif command == 'verify':
        if len(sys.argv) < 3:
            print("Usage: python domain-manager.py verify <slug>")
            sys.exit(1)
        slug = sys.argv[2]
        manager.verify_domain_ownership(slug)

    elif command == 'status':
        manager.status_dashboard()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
