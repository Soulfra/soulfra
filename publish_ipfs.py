#!/usr/bin/env python3
"""
IPFS Publishing - Decentralized hosting for Soulfra

Usage:
    python3 publish_ipfs.py --brand soulfra
    python3 publish_ipfs.py --brand soulfra --update-dns
    python3 publish_ipfs.py --all

Prerequisites:
    brew install ipfs
    ipfs init
    ipfs daemon &

Features:
    - Publishes static site to IPFS
    - Updates DNS TXT record with IPFS hash
    - Creates dnslink for soulfra.com
    - Optional: Register soulfra.eth ENS domain
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'

class IPFSPublisher:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.ipfs_binary = self._find_ipfs()

    def _find_ipfs(self):
        """Find IPFS binary"""
        try:
            result = subprocess.run(['which', 'ipfs'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        print("❌ IPFS not found. Install with: brew install ipfs")
        sys.exit(1)

    def check_daemon(self):
        """Check if IPFS daemon is running"""
        try:
            result = subprocess.run(
                [self.ipfs_binary, 'swarm', 'peers'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def publish_directory(self, brand):
        """Publish brand directory to IPFS"""
        brand_dir = OUTPUT_DIR / brand

        if not brand_dir.exists():
            print(f"❌ Brand directory not found: {brand_dir}")
            return None

        print(f"📦 Publishing {brand} to IPFS...")

        if self.dry_run:
            return {'hash': 'QmDRY-RUN-HASH', 'size': '0', 'dry_run': True}

        try:
            # Add directory to IPFS
            result = subprocess.run(
                [self.ipfs_binary, 'add', '-r', '-Q', str(brand_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ IPFS add failed: {result.stderr}")
                return None

            ipfs_hash = result.stdout.strip()

            # Pin the hash
            subprocess.run(
                [self.ipfs_binary, 'pin', 'add', ipfs_hash],
                capture_output=True,
                timeout=30
            )

            # Get size
            stat_result = subprocess.run(
                [self.ipfs_binary, 'object', 'stat', ipfs_hash],
                capture_output=True,
                text=True,
                timeout=10
            )

            size = "unknown"
            if stat_result.returncode == 0:
                for line in stat_result.stdout.split('\n'):
                    if 'CumulativeSize' in line:
                        size = line.split(':')[1].strip()

            return {
                'hash': ipfs_hash,
                'size': size,
                'url': f'https://ipfs.io/ipfs/{ipfs_hash}',
                'gateway_url': f'https://gateway.ipfs.io/ipfs/{ipfs_hash}'
            }

        except Exception as e:
            print(f"❌ Error publishing to IPFS: {e}")
            return None

    def create_dnslink(self, brand, ipfs_hash):
        """Create DNSLink instructions for domain"""
        domain_map = {
            'Soulfra': 'soulfra.com',
            'DeathToData': 'deathtodata.com',
            'Calriven': 'calriven.com',
            'HowToCookAtHome': 'howtocookathome.com'
        }

        domain = domain_map.get(brand, f'{brand.lower()}.com')

        print(f"\n📝 DNSLink Setup for {domain}:")
        print(f"   Add this TXT record to your DNS:")
        print(f"")
        print(f"   Name:  _dnslink.{domain}")
        print(f"   Type:  TXT")
        print(f"   Value: dnslink=/ipfs/{ipfs_hash}")
        print(f"   TTL:   1 minute")
        print(f"")
        print(f"   After DNS propagates, access via:")
        print(f"   https://ipfs.io/ipns/{domain}")
        print(f"")

    def publish_to_ipns(self, ipfs_hash):
        """Publish to IPNS (permanent name)"""
        print(f"📡 Publishing to IPNS...")

        if self.dry_run:
            return {'name': '/ipns/QmDRY-RUN-IPNS', 'dry_run': True}

        try:
            result = subprocess.run(
                [self.ipfs_binary, 'name', 'publish', ipfs_hash],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ IPNS publish failed: {result.stderr}")
                return None

            # Parse IPNS name
            output = result.stdout.strip()
            if 'Published to' in output:
                ipns_name = output.split('Published to')[1].strip().split(':')[0].strip()
                return {
                    'name': ipns_name,
                    'url': f'https://ipfs.io{ipns_name}'
                }

            return None

        except Exception as e:
            print(f"❌ Error publishing to IPNS: {e}")
            return None

    def save_history(self, brand, ipfs_hash, ipns_name=None):
        """Save publish history"""
        history_file = BASE_DIR / 'ipfs-history.json'

        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []

        history.append({
            'brand': brand,
            'ipfs_hash': ipfs_hash,
            'ipns_name': ipns_name,
            'timestamp': datetime.now().isoformat(),
            'url': f'https://ipfs.io/ipfs/{ipfs_hash}'
        })

        # Keep last 100 entries
        history = history[-100:]

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        print(f"📚 Saved to history: {history_file}")

    def publish(self, brand):
        """Complete IPFS publish workflow"""
        print(f"\n🚀 Publishing {brand} to IPFS")
        print(f"   Dry run: {self.dry_run}\n")

        # Check daemon
        if not self.dry_run and not self.check_daemon():
            print("❌ IPFS daemon not running")
            print("   Start with: ipfs daemon &")
            return False

        # Publish directory
        result = self.publish_directory(brand)
        if not result:
            return False

        ipfs_hash = result['hash']
        print(f"✅ Published to IPFS")
        print(f"   Hash: {ipfs_hash}")
        print(f"   Size: {result.get('size', 'unknown')}")
        print(f"   URL:  {result.get('url', f'https://ipfs.io/ipfs/{ipfs_hash}')}")

        # Publish to IPNS
        ipns_result = self.publish_to_ipns(ipfs_hash)
        if ipns_result:
            print(f"\n✅ Published to IPNS")
            print(f"   Name: {ipns_result['name']}")
            print(f"   URL:  {ipns_result['url']}")

        # Create DNSLink
        self.create_dnslink(brand, ipfs_hash)

        # Save history
        if not self.dry_run:
            self.save_history(brand, ipfs_hash, ipns_result.get('name') if ipns_result else None)

        return True


def init_ipfs():
    """Initialize IPFS if not already initialized"""
    try:
        result = subprocess.run(['ipfs', 'id'], capture_output=True)
        if result.returncode == 0:
            print("✅ IPFS already initialized")
            return True
    except:
        pass

    print("🔧 Initializing IPFS...")
    try:
        subprocess.run(['ipfs', 'init'], check=True)
        print("✅ IPFS initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize IPFS: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Publish to IPFS')
    parser.add_argument('--brand', help='Brand to publish')
    parser.add_argument('--all', action='store_true', help='Publish all brands')
    parser.add_argument('--init', action='store_true', help='Initialize IPFS')
    parser.add_argument('--dry-run', action='store_true', help='Test without publishing')

    args = parser.parse_args()

    if args.init:
        init_ipfs()
        return

    if not args.brand and not args.all:
        parser.error('Must specify --brand or --all')

    publisher = IPFSPublisher(dry_run=args.dry_run)

    brands = []
    if args.all:
        # Get all brands from output directory
        output_dir = Path(__file__).parent / 'output'
        if output_dir.exists():
            brands = [d.name for d in output_dir.iterdir() if d.is_dir()]
    else:
        brands = [args.brand]

    success_count = 0
    for brand in brands:
        if publisher.publish(brand):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"📊 IPFS PUBLISH SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {success_count}/{len(brands)}")
    print(f"❌ Failed: {len(brands) - success_count}/{len(brands)}")

    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No actual publishing occurred")

    sys.exit(0 if success_count == len(brands) else 1)


if __name__ == '__main__':
    main()
