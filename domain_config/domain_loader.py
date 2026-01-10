#!/usr/bin/env python3
"""
Domain Configuration Loader

Loads unified domain config from domain_config/domains.yaml
Single source of truth for all domain routing, auth, themes, etc.

Usage:
    from domain_config.domain_loader import DomainConfig

    config = DomainConfig()
    stpete_config = config.get_domain('stpetepros')
    all_domains = config.get_all_domains()
    requires_auth = config.requires_auth('stpetepros')
"""

import yaml
import os
from pathlib import Path
from typing import Optional, Dict, List


class DomainConfig:
    """Unified domain configuration loader"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Load domain configuration from YAML file

        Args:
            config_path: Path to domains.yaml (defaults to config/domains.yaml)
        """
        if config_path is None:
            # Default to config/domains.yaml relative to this file
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'domains.yaml'

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Domain config not found: {self.config_path}")
            print("   Using fallback configuration")
            return self._get_fallback_config()
        except yaml.YAMLError as e:
            print(f"⚠️  Error parsing domain config: {e}")
            return self._get_fallback_config()

    def _get_fallback_config(self) -> dict:
        """Fallback config if YAML file not found"""
        return {
            'domains': {
                'soulfra': {
                    'name': 'Soulfra',
                    'domain': 'soulfra.com',
                    'slug': 'soulfra',
                    'network_role': 'master',
                    'requires_auth': False,
                    'provides_auth': True
                }
            }
        }

    def get_domain(self, slug: str) -> Optional[Dict]:
        """
        Get configuration for a specific domain

        Args:
            slug: Domain slug (e.g. 'stpetepros', 'soulfra')

        Returns:
            Domain config dict or None if not found
        """
        return self.config.get('domains', {}).get(slug)

    def get_all_domains(self) -> Dict[str, Dict]:
        """Get all domain configurations"""
        return self.config.get('domains', {})

    def get_domain_by_hostname(self, hostname: str) -> Optional[Dict]:
        """
        Get domain config by hostname (e.g. 'stpetepros.com')

        Args:
            hostname: Domain hostname

        Returns:
            Domain config dict or None
        """
        # Strip port if present
        hostname = hostname.split(':')[0].lower()

        # Strip www prefix
        if hostname.startswith('www.'):
            hostname = hostname[4:]

        # Find matching domain
        for slug, domain_config in self.get_all_domains().items():
            if domain_config.get('domain') == hostname:
                # Add slug to config
                domain_config['slug'] = slug
                return domain_config

        return None

    def requires_auth(self, slug: str) -> bool:
        """Check if domain requires authentication"""
        domain = self.get_domain(slug)
        return domain.get('requires_auth', False) if domain else False

    def provides_auth(self, slug: str) -> bool:
        """Check if domain provides authentication (SSO provider)"""
        domain = self.get_domain(slug)
        return domain.get('provides_auth', False) if domain else False

    def get_master_auth_domain(self) -> str:
        """Get the master authentication domain"""
        return self.config.get('master_auth_domain', 'soulfra.com')

    def get_theme(self, slug: str) -> Dict[str, str]:
        """Get theme colors for domain"""
        domain = self.get_domain(slug)
        if domain and 'theme' in domain:
            return domain['theme']
        return {'primary': '#667eea', 'secondary': '#764ba2', 'accent': '#61dafb'}

    def get_silos(self, slug: str) -> List[Dict]:
        """Get content silos for domain"""
        domain = self.get_domain(slug)
        if domain and 'silos' in domain:
            return domain['silos']
        return []

    def get_silo_categories(self, slug: str, silo_slug: str) -> List[str]:
        """
        Get categories for a specific silo

        Args:
            slug: Domain slug
            silo_slug: Silo slug (e.g. 'professionals')

        Returns:
            List of category slugs
        """
        silos = self.get_silos(slug)
        for silo in silos:
            if silo.get('slug') == silo_slug:
                return silo.get('categories', [])
        return []

    def is_geo_restricted(self, slug: str) -> bool:
        """Check if domain is geo-restricted"""
        domain = self.get_domain(slug)
        return domain.get('geo_restricted', False) if domain else False

    def get_geo_config(self, slug: str) -> Optional[Dict]:
        """Get geo-restriction configuration"""
        domain = self.get_domain(slug)
        if domain and domain.get('geo_restricted'):
            return domain.get('geo_config', {})
        return None

    def get_features(self, slug: str) -> List[str]:
        """Get enabled features for domain"""
        domain = self.get_domain(slug)
        return domain.get('features', []) if domain else []

    def has_feature(self, slug: str, feature: str) -> bool:
        """Check if domain has specific feature enabled"""
        return feature in self.get_features(slug)

    def get_dev_mode_config(self) -> Dict:
        """Get development mode configuration"""
        return self.config.get('dev_mode', {
            'enabled': True,
            'default_domain': 'stpetepros',
            'geo_override_allowed': True
        })

    def get_auth_flow_config(self) -> Dict:
        """Get authentication flow configuration"""
        return self.config.get('auth_flow', {
            'signup_redirect_domain': 'soulfra.com',
            'login_endpoint': '/api/master/login',
            'signup_endpoint': '/api/master/signup',
            'verify_endpoint': '/api/master/verify',
            'token_expiry_hours': 168
        })


# Singleton instance
_domain_config = None


def get_domain_config() -> DomainConfig:
    """Get singleton DomainConfig instance"""
    global _domain_config
    if _domain_config is None:
        _domain_config = DomainConfig()
    return _domain_config


# Convenience functions
def get_domain(slug: str) -> Optional[Dict]:
    """Get domain configuration by slug"""
    return get_domain_config().get_domain(slug)


def get_domain_by_hostname(hostname: str) -> Optional[Dict]:
    """Get domain configuration by hostname"""
    return get_domain_config().get_domain_by_hostname(hostname)


def requires_auth(slug: str) -> bool:
    """Check if domain requires authentication"""
    return get_domain_config().requires_auth(slug)


def get_theme(slug: str) -> Dict[str, str]:
    """Get theme colors for domain"""
    return get_domain_config().get_theme(slug)


# CLI testing
if __name__ == '__main__':
    import sys

    config = DomainConfig()

    if len(sys.argv) > 1:
        slug = sys.argv[1]
        domain = config.get_domain(slug)
        if domain:
            print(f"\n✅ Domain: {domain['name']}")
            print(f"   URL: {domain['domain']}")
            print(f"   Requires auth: {config.requires_auth(slug)}")
            print(f"   Features: {', '.join(config.get_features(slug))}")
            print(f"   Silos: {len(config.get_silos(slug))}")
        else:
            print(f"\n❌ Domain '{slug}' not found")
    else:
        print("\n🌐 All Domains:")
        for slug, domain in config.get_all_domains().items():
            auth_status = "🔒" if config.requires_auth(slug) else "🌍"
            print(f"{auth_status} {domain['name']:20} → {domain['domain']}")
        print(f"\n📊 Total domains: {len(config.get_all_domains())}")
