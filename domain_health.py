#!/usr/bin/env python3
"""
Domain Health Checker

Checks DNS, GitHub Pages status, and SSL for all Soulfra brands.

Usage:
    python3 domain_health.py              # Check all brands
    python3 domain_health.py soulfra      # Check specific brand
"""

import subprocess
import sys
import requests
from datetime import datetime

# GitHub Pages IPs (official)
GITHUB_PAGES_IPS = {
    '185.199.108.153',
    '185.199.109.153',
    '185.199.110.153',
    '185.199.111.153'
}

# All Soulfra brands
BRANDS = {
    'soulfra': {
        'domain': 'soulfra.com',
        'github_repo': 'soulfra',
        'has_custom_domain': True
    },
    'calriven': {
        'domain': 'calriven.com',
        'github_repo': 'calriven',
        'has_custom_domain': True
    },
    'deathtodata': {
        'domain': 'deathtodata.com',
        'github_repo': 'deathtodata',
        'has_custom_domain': True
    },
    'dealordelete': {
        'domain': None,
        'github_repo': 'dealordelete-site',
        'has_custom_domain': False
    },
    'finishthisrepo': {
        'domain': None,
        'github_repo': 'finishthisrepo-site',
        'has_custom_domain': False
    },
    'mascotrooms': {
        'domain': None,
        'github_repo': 'mascotrooms-site',
        'has_custom_domain': False
    },
    'saveorsink': {
        'domain': None,
        'github_repo': 'saveorsink-site',
        'has_custom_domain': False
    },
    'sellthismvp': {
        'domain': None,
        'github_repo': 'sellthismvp-site',
        'has_custom_domain': False
    },
    'shiprekt': {
        'domain': None,
        'github_repo': 'shiprekt-site',
        'has_custom_domain': False
    }
}


def run_dig(domain):
    """Run dig command and return IPs"""
    try:
        result = subprocess.run(
            ['dig', domain, '+short'],
            capture_output=True,
            text=True,
            timeout=5
        )
        ips = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return ips
    except Exception as e:
        return []


def check_dns(domain):
    """Check if DNS is pointed correctly"""
    ips = run_dig(domain)

    if not ips:
        return {
            'status': 'ERROR',
            'message': 'No DNS records found',
            'ips': []
        }

    # Check if all IPs are GitHub Pages IPs
    unknown_ips = set(ips) - GITHUB_PAGES_IPS

    if unknown_ips:
        return {
            'status': 'WARNING',
            'message': f'Found non-GitHub IPs: {", ".join(unknown_ips)}',
            'ips': ips
        }

    return {
        'status': 'OK',
        'message': f'All {len(ips)} IPs point to GitHub Pages',
        'ips': ips
    }


def check_github_pages(username, repo):
    """Check if GitHub Pages is accessible"""
    url = f"https://{username}.github.io/{repo}/"

    try:
        response = requests.head(url, timeout=5, allow_redirects=True)

        if response.status_code == 200:
            return {
                'status': 'OK',
                'message': f'GitHub Pages is live',
                'url': url
            }
        elif response.status_code == 404:
            return {
                'status': 'ERROR',
                'message': 'GitHub Pages not found (404)',
                'url': url
            }
        else:
            return {
                'status': 'WARNING',
                'message': f'Unexpected status: {response.status_code}',
                'url': url
            }
    except requests.RequestException as e:
        return {
            'status': 'ERROR',
            'message': f'Cannot reach GitHub Pages: {str(e)}',
            'url': url
        }


def check_ssl(domain):
    """Check if SSL is working"""
    try:
        response = requests.head(f'https://{domain}', timeout=5, allow_redirects=True)
        return {
            'status': 'OK',
            'message': 'SSL certificate valid'
        }
    except requests.exceptions.SSLError:
        return {
            'status': 'ERROR',
            'message': 'SSL certificate invalid or missing'
        }
    except requests.exceptions.RequestException:
        return {
            'status': 'WARNING',
            'message': 'Cannot verify SSL (domain may not be live yet)'
        }


def print_status(status):
    """Print colored status"""
    colors = {
        'OK': '\033[92m',      # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',   # Red
    }
    reset = '\033[0m'

    color = colors.get(status, '')
    symbol = '✓' if status == 'OK' else ('⚠' if status == 'WARNING' else '✗')

    return f"{color}{symbol} {status}{reset}"


def check_brand(brand_name, brand_info, username='Soulfra'):
    """Check health of a single brand"""
    print(f"\n{'='*70}")
    print(f"Brand: {brand_name.upper()}")
    print(f"{'='*70}")

    # Check GitHub Pages
    print(f"\n1. GitHub Pages Check")
    github_result = check_github_pages(username, brand_info['github_repo'])
    print(f"   Status: {print_status(github_result['status'])}")
    print(f"   URL: {github_result['url']}")
    print(f"   {github_result['message']}")

    # Check custom domain if it exists
    if brand_info['has_custom_domain'] and brand_info['domain']:
        domain = brand_info['domain']

        print(f"\n2. DNS Check ({domain})")
        dns_result = check_dns(domain)
        print(f"   Status: {print_status(dns_result['status'])}")
        print(f"   {dns_result['message']}")
        if dns_result['ips']:
            print(f"   IPs: {', '.join(dns_result['ips'])}")

        print(f"\n3. SSL Check ({domain})")
        ssl_result = check_ssl(domain)
        print(f"   Status: {print_status(ssl_result['status'])}")
        print(f"   {ssl_result['message']}")

        # Overall health
        all_ok = all([
            github_result['status'] == 'OK',
            dns_result['status'] == 'OK',
            ssl_result['status'] == 'OK'
        ])

        print(f"\n{'─'*70}")
        if all_ok:
            print(f"Overall: {print_status('OK')} - {domain} is fully operational")
        else:
            print(f"Overall: {print_status('WARNING')} - {domain} has issues")
    else:
        print(f"\n   (No custom domain configured - GitHub Pages only)")
        print(f"\n{'─'*70}")
        if github_result['status'] == 'OK':
            print(f"Overall: {print_status('OK')} - GitHub Pages operational")
        else:
            print(f"Overall: {print_status('ERROR')} - GitHub Pages has issues")


def main():
    """Main function"""
    print(f"\n🔍 Soulfra Domain Health Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if specific brand requested
    if len(sys.argv) > 1:
        brand_name = sys.argv[1].lower()
        if brand_name in BRANDS:
            check_brand(brand_name, BRANDS[brand_name])
        else:
            print(f"\nError: Unknown brand '{brand_name}'")
            print(f"Available brands: {', '.join(BRANDS.keys())}")
            sys.exit(1)
    else:
        # Check all brands
        for brand_name, brand_info in BRANDS.items():
            check_brand(brand_name, brand_info)

    print(f"\n{'='*70}")
    print("Health check complete!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
