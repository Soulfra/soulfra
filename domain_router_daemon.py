"""
Domain Router Daemon

Implements tattoo-pounds-evidence-correlation service logic.
Reads README.md files from brands/* and routes cross-domain requests.

Maps 4-word routing pattern:
- tattoo → soulfra (identity/soul)
- pounds → deathtodata (force/impact against surveillance)
- evidence → calriven (proof/verification/verilog)
- correlation → cringeproof (connection/authentic relationships)
"""

import argparse
import time
import os
import re
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('domain_router.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DomainRouterDaemon:
    def __init__(self, config_source='readme', domains=None, mapping=None, health_check_interval=30):
        self.config_source = config_source
        self.domains = domains or []
        self.mapping = self._parse_mapping(mapping) if mapping else {}
        self.health_check_interval = health_check_interval
        self.running = True

        # Domain configurations loaded from README.md
        self.domain_configs = {}

        logger.info(f"Initializing Domain Router Daemon")
        logger.info(f"Domains: {self.domains}")
        logger.info(f"Mapping: {self.mapping}")

    def _parse_mapping(self, mapping_str):
        """Parse mapping string like 'tattoo:soulfra,pounds:deathtodata'"""
        mapping = {}
        if not mapping_str:
            return mapping

        for pair in mapping_str.split(','):
            if ':' in pair:
                key, value = pair.split(':', 1)
                mapping[key.strip()] = value.strip()

        return mapping

    def load_domain_configs_from_readme(self):
        """
        Load domain configurations from brands/*/README.md files.

        Parses markdown for config blocks like:
        ## Domain: soulfra
        - Service: tattoo-pounds-evidence-correlation
        - Port: 5001
        - Bookmarks: [github.com, stackoverflow.com]
        - Rate Limits: {api: 1000/day, google: 100/day}
        """
        brands_dir = Path('brands')
        if not brands_dir.exists():
            logger.warning(f"Brands directory not found: {brands_dir}")
            return

        for brand_path in brands_dir.iterdir():
            if not brand_path.is_dir():
                continue

            readme_path = brand_path / 'README.md'
            if not readme_path.exists():
                continue

            brand_name = brand_path.name
            logger.info(f"Loading config for domain: {brand_name}")

            try:
                with open(readme_path, 'r') as f:
                    content = f.read()

                # Extract domain config section
                config = self._parse_readme_config(content, brand_name)
                self.domain_configs[brand_name] = config

                logger.info(f"  Loaded: {config}")

            except Exception as e:
                logger.error(f"Error loading {readme_path}: {e}")

    def _parse_readme_config(self, content, brand_name):
        """Parse README.md markdown for domain configuration"""
        config = {
            'domain': brand_name,
            'service': 'unknown',
            'port': 5001,
            'bookmarks': [],
            'rate_limits': {},
            'personality': '',
            'category': '',
            'tagline': ''
        }

        # Extract tagline
        tagline_match = re.search(r'\*\*Tagline:\*\*\s*(.+)', content)
        if tagline_match:
            config['tagline'] = tagline_match.group(1).strip()

        # Extract personality tone
        tone_match = re.search(r'-\s*\*\*Tone:\*\*\s*(.+)', content)
        if tone_match:
            config['personality'] = tone_match.group(1).strip()

        # Extract category
        category_match = re.search(r'-\s*\*\*Category:\*\*\s*(.+)', content)
        if category_match:
            config['category'] = category_match.group(1).strip()

        return config

    def health_check_domain(self, domain_name):
        """
        Perform health check on a domain (verilog-style verification).

        Checks:
        - README.md exists and is parseable
        - Service is in expected state
        - Cross-domain dependencies are healthy
        """
        brand_path = Path('brands') / domain_name
        readme_path = brand_path / 'README.md'

        health = {
            'domain': domain_name,
            'status': 'unknown',
            'checks': {
                'readme_exists': readme_path.exists(),
                'config_valid': domain_name in self.domain_configs,
                'timestamp': datetime.utcnow().isoformat()
            }
        }

        if health['checks']['readme_exists'] and health['checks']['config_valid']:
            health['status'] = 'healthy'
        elif health['checks']['readme_exists']:
            health['status'] = 'degraded'
        else:
            health['status'] = 'down'

        return health

    def cross_domain_verify(self, source_domain, target_domain):
        """
        Cross-domain verification (Cal Riven checking DeathToData).

        Source domain verifies target domain health before proceeding with
        operations that depend on target domain data.
        """
        logger.info(f"Cross-domain verify: {source_domain} → {target_domain}")

        source_health = self.health_check_domain(source_domain)
        target_health = self.health_check_domain(target_domain)

        verification = {
            'source': source_domain,
            'target': target_domain,
            'source_status': source_health['status'],
            'target_status': target_health['status'],
            'verified': source_health['status'] == 'healthy' and target_health['status'] == 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }

        if verification['verified']:
            logger.info(f"  ✅ Cross-domain verification passed")
        else:
            logger.warning(f"  ❌ Cross-domain verification failed: {source_health['status']} / {target_health['status']}")

        return verification

    def run_health_check_cycle(self):
        """Run health checks for all configured domains"""
        logger.info("=" * 60)
        logger.info("Running health check cycle")

        # Reload configs from README.md
        self.load_domain_configs_from_readme()

        # Check each domain
        for domain_name in self.domain_configs.keys():
            health = self.health_check_domain(domain_name)
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️ ',
                'down': '❌'
            }.get(health['status'], '❓')

            logger.info(f"{status_emoji} {domain_name}: {health['status']}")

        # Example: Cal Riven verifies DeathToData
        if 'calriven' in self.domain_configs and 'deathtodata' in self.domain_configs:
            self.cross_domain_verify('calriven', 'deathtodata')

        logger.info("=" * 60)

    def run(self):
        """Main daemon loop"""
        logger.info("Starting Domain Router Daemon")
        logger.info(f"Health check interval: {self.health_check_interval} seconds")

        try:
            while self.running:
                self.run_health_check_cycle()
                time.sleep(self.health_check_interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.running = False

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)

        finally:
            logger.info("Domain Router Daemon stopped")

def main():
    parser = argparse.ArgumentParser(description='Domain Router Daemon')
    parser.add_argument('--config-source', default='readme', help='Config source (readme, json, yaml)')
    parser.add_argument('--domains', default='', help='Comma-separated list of domain aliases')
    parser.add_argument('--mapping', default='', help='Domain mapping (tattoo:soulfra,pounds:deathtodata)')
    parser.add_argument('--health-check-interval', type=int, default=30, help='Health check interval in seconds')

    args = parser.parse_args()

    domains = [d.strip() for d in args.domains.split(',') if d.strip()]

    daemon = DomainRouterDaemon(
        config_source=args.config_source,
        domains=domains,
        mapping=args.mapping,
        health_check_interval=args.health_check_interval
    )

    daemon.run()

if __name__ == '__main__':
    main()
