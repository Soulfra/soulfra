#!/usr/bin/env python3
"""
Local Domain Tester - Multi-Domain Testing Without DNS

Enables local testing of the complete tiered affiliate funnel system
using /etc/hosts for domain mapping.

🎯 PURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test the complete Amazon affiliate-style tiered system locally:
- Entry domain (soulfra.com) always free (Tier 0)
- Additional domains unlock via GitHub stars (Tier 1-4)
- Ownership percentages increase with engagement
- Referral tracking between domains
- Ollama accessible from all local domains

🌐 LOCAL DOMAIN MAPPING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maps domains to localhost for testing:

127.0.0.1  soulfra.local           # Tier 0 - Always free
127.0.0.1  deathtodata.local       # Tier 1 - Unlock with 1 star
127.0.0.1  calriven.local          # Tier 1 - Unlock with 1 star
127.0.0.1  howtocookathome.local   # Tier 2 - Unlock with rotation
127.0.0.1  stpetepros.local        # Tier 2 - Unlock with rotation

📡 ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Browser Request:
  http://soulfra.local:5001
    ↓
/etc/hosts:
  127.0.0.1 → localhost
    ↓
Flask subdomain_router.py:
  Detects domain → Loads brand theme
    ↓
Tier progression engine:
  Checks user tier → Shows/hides domains
    ↓
Ollama (dual-tier):
  localhost:11434 (dev) + 192.168.1.87:11434 (network)

🧪 TESTING FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Setup /etc/hosts (requires sudo)
2. Start Flask on port 5001
3. Visit http://soulfra.local:5001 (Tier 0 - works)
4. Visit http://deathtodata.local:5001 (Tier 1 - locked)
5. Star soulfra/deathtodata repo on GitHub
6. Reload → deathtodata.local unlocked + 2% ownership
7. Test affiliate link tracking
8. Verify Ollama accessible from all domains

Usage:
    # Setup local domains
    sudo python3 local_domain_tester.py --setup

    # Test all domains
    python3 local_domain_tester.py --test-all

    # Cleanup /etc/hosts
    sudo python3 local_domain_tester.py --cleanup

    # Test specific domain
    python3 local_domain_tester.py --test soulfra.local
"""

import subprocess
import sys
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional
import json

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(msg):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ️  {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


# =============================================================================
# LOCAL DOMAIN CONFIGURATION
# =============================================================================

LOCAL_DOMAINS = {
    'soulfra.local': {
        'tier': 0,
        'description': 'Soulfra - Entry point (always free)',
        'repo': {'owner': 'soulfra', 'repo': 'soulfra'},
        'ownership_default': 5.0,
        'color': '#6366f1'
    },
    'deathtodata.local': {
        'tier': 1,
        'description': 'DeathToData - Privacy advocacy',
        'repo': {'owner': 'soulfra', 'repo': 'deathtodata'},
        'unlock_requirement': '1 GitHub star',
        'ownership_unlock': 2.0,
        'color': '#dc2626'
    },
    'calriven.local': {
        'tier': 1,
        'description': 'Calriven - Creative AI tools',
        'repo': {'owner': 'soulfra', 'repo': 'calriven'},
        'unlock_requirement': '1 GitHub star',
        'ownership_unlock': 2.0,
        'color': '#10b981'
    },
    'howtocookathome.local': {
        'tier': 2,
        'description': 'HowToCookAtHome - Cooking community',
        'repo': {'owner': 'soulfra', 'repo': 'howtocookathome'},
        'unlock_requirement': '2+ GitHub stars',
        'ownership_unlock': 5.0,
        'color': '#f59e0b'
    },
    'stpetepros.local': {
        'tier': 2,
        'description': 'StPetePros - Local services',
        'repo': {'owner': 'soulfra', 'repo': 'stpetepros'},
        'unlock_requirement': '2+ GitHub stars',
        'ownership_unlock': 5.0,
        'color': '#8b5cf6'
    }
}

FLASK_PORT = 5001
OLLAMA_LOCALHOST = 'http://localhost:11434'
OLLAMA_NETWORK = 'http://192.168.1.87:11434'
HOSTS_FILE = '/etc/hosts'
HOSTS_MARKER_START = '# === SOULFRA LOCAL DOMAINS START ==='
HOSTS_MARKER_END = '# === SOULFRA LOCAL DOMAINS END ==='


# =============================================================================
# /etc/hosts MANAGEMENT
# =============================================================================

def check_sudo():
    """Check if running with sudo"""
    if os.geteuid() != 0:
        print_error("This operation requires sudo")
        print_info("Run: sudo python3 local_domain_tester.py --setup")
        return False
    return True


def backup_hosts_file():
    """Backup /etc/hosts before modification"""
    backup_path = f"{HOSTS_FILE}.backup"

    try:
        subprocess.run(
            ['cp', HOSTS_FILE, backup_path],
            check=True,
            capture_output=True
        )
        print_success(f"Backed up {HOSTS_FILE} → {backup_path}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to backup hosts file: {e}")
        return False


def setup_local_domains():
    """Add local domain mappings to /etc/hosts"""
    print_step("SETUP: Adding Local Domains to /etc/hosts")

    if not check_sudo():
        return False

    # Backup first
    if not backup_hosts_file():
        return False

    # Read current hosts file
    try:
        with open(HOSTS_FILE, 'r') as f:
            hosts_content = f.read()
    except Exception as e:
        print_error(f"Failed to read {HOSTS_FILE}: {e}")
        return False

    # Check if already configured
    if HOSTS_MARKER_START in hosts_content:
        print_warning("Local domains already configured in /etc/hosts")
        print_info("Run with --cleanup first to remove old entries")
        return False

    # Generate domain entries
    domain_entries = [
        '',
        HOSTS_MARKER_START,
        '# Local testing domains for Soulfra multi-brand system',
        '# Added by local_domain_tester.py',
        ''
    ]

    for domain, config in LOCAL_DOMAINS.items():
        tier = config['tier']
        desc = config['description']
        domain_entries.append(f"127.0.0.1    {domain}    # Tier {tier}: {desc}")

    domain_entries.extend([
        '',
        HOSTS_MARKER_END,
        ''
    ])

    # Append to hosts file
    try:
        with open(HOSTS_FILE, 'a') as f:
            f.write('\n'.join(domain_entries))

        print_success("Local domains added to /etc/hosts")

        # Flush DNS cache
        print_info("Flushing DNS cache...")
        try:
            subprocess.run(
                ['dscacheutil', '-flushcache'],
                check=True,
                capture_output=True
            )
            print_success("DNS cache flushed")
        except subprocess.CalledProcessError:
            print_warning("Could not flush DNS cache (may require restart)")

        # Show what was added
        print_info("\nAdded domains:")
        for domain in LOCAL_DOMAINS:
            print(f"  • http://{domain}:{FLASK_PORT}")

        return True

    except Exception as e:
        print_error(f"Failed to write to {HOSTS_FILE}: {e}")
        return False


def cleanup_local_domains():
    """Remove local domain mappings from /etc/hosts"""
    print_step("CLEANUP: Removing Local Domains from /etc/hosts")

    if not check_sudo():
        return False

    # Backup first
    if not backup_hosts_file():
        return False

    # Read current hosts file
    try:
        with open(HOSTS_FILE, 'r') as f:
            hosts_content = f.read()
    except Exception as e:
        print_error(f"Failed to read {HOSTS_FILE}: {e}")
        return False

    # Check if configured
    if HOSTS_MARKER_START not in hosts_content:
        print_warning("No local domains found in /etc/hosts")
        return False

    # Remove section between markers
    lines = hosts_content.split('\n')
    new_lines = []
    skip = False

    for line in lines:
        if HOSTS_MARKER_START in line:
            skip = True
            continue
        if HOSTS_MARKER_END in line:
            skip = False
            continue
        if not skip:
            new_lines.append(line)

    # Write back
    try:
        with open(HOSTS_FILE, 'w') as f:
            f.write('\n'.join(new_lines))

        print_success("Local domains removed from /etc/hosts")

        # Flush DNS cache
        try:
            subprocess.run(['dscacheutil', '-flushcache'], check=True, capture_output=True)
            print_success("DNS cache flushed")
        except:
            pass

        return True

    except Exception as e:
        print_error(f"Failed to write to {HOSTS_FILE}: {e}")
        return False


# =============================================================================
# DOMAIN TESTING
# =============================================================================

def test_flask_running():
    """Check if Flask is running on port 5001"""
    try:
        response = requests.get(f'http://localhost:{FLASK_PORT}/api/health', timeout=2)
        if response.status_code == 200:
            print_success(f"Flask running on port {FLASK_PORT}")
            return True
        else:
            print_warning(f"Flask responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print_error(f"Flask not running on port {FLASK_PORT}")
        print_info("Start Flask: python3 app.py")
        return False


def test_ollama_endpoints():
    """Test both Ollama endpoints"""
    print_step("Testing Ollama Endpoints")

    results = {}

    # Test localhost
    try:
        response = requests.get(f'{OLLAMA_LOCALHOST}/api/tags', timeout=2)
        if response.status_code == 200:
            print_success(f"Ollama localhost accessible: {OLLAMA_LOCALHOST}")
            results['localhost'] = True
        else:
            print_error(f"Ollama localhost returned {response.status_code}")
            results['localhost'] = False
    except requests.exceptions.RequestException as e:
        print_error(f"Ollama localhost not accessible: {e}")
        results['localhost'] = False

    # Test network
    try:
        response = requests.get(f'{OLLAMA_NETWORK}/api/tags', timeout=2)
        if response.status_code == 200:
            print_success(f"Ollama network accessible: {OLLAMA_NETWORK}")
            results['network'] = True
        else:
            print_error(f"Ollama network returned {response.status_code}")
            results['network'] = False
    except requests.exceptions.RequestException as e:
        print_error(f"Ollama network not accessible: {e}")
        results['network'] = False

    return results


def test_domain(domain: str, verbose: bool = True):
    """
    Test if local domain is working

    Args:
        domain: Domain name (e.g., 'soulfra.local')
        verbose: Print detailed results

    Returns:
        Dict with test results
    """
    if verbose:
        print_info(f"\nTesting: {domain}")

    config = LOCAL_DOMAINS.get(domain)
    if not config:
        print_error(f"Unknown domain: {domain}")
        return {'success': False, 'error': 'unknown_domain'}

    url = f'http://{domain}:{FLASK_PORT}'

    results = {
        'domain': domain,
        'tier': config['tier'],
        'url': url,
        'tests': {}
    }

    # Test 1: Can resolve domain?
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        results['tests']['accessible'] = response.status_code == 200

        if verbose:
            if results['tests']['accessible']:
                print_success(f"  Accessible: {url}")
            else:
                print_error(f"  Not accessible: {response.status_code}")
    except requests.exceptions.RequestException as e:
        results['tests']['accessible'] = False
        if verbose:
            print_error(f"  Connection failed: {e}")

    # Test 2: Correct brand theme loaded?
    try:
        response = requests.get(url, timeout=5)
        html = response.text

        # Check for brand name in HTML
        brand_name = config['description'].split(' - ')[0]
        results['tests']['correct_brand'] = brand_name.lower() in html.lower()

        if verbose:
            if results['tests']['correct_brand']:
                print_success(f"  Brand theme: {brand_name}")
            else:
                print_warning(f"  Brand theme not detected: {brand_name}")
    except:
        results['tests']['correct_brand'] = False

    # Test 3: API endpoints working?
    try:
        api_url = f'http://{domain}:{FLASK_PORT}/api/comments/1'
        response = requests.get(api_url, timeout=5)
        results['tests']['api_working'] = response.status_code < 500

        if verbose:
            if results['tests']['api_working']:
                print_success(f"  API working: {api_url}")
            else:
                print_error(f"  API error: {response.status_code}")
    except:
        results['tests']['api_working'] = False

    # Overall success
    results['success'] = all(results['tests'].values())

    return results


def test_all_domains():
    """Test all local domains"""
    print_step("Testing All Local Domains")

    # Check Flask first
    if not test_flask_running():
        return False

    results = []

    for domain in LOCAL_DOMAINS:
        result = test_domain(domain, verbose=True)
        results.append(result)

    # Summary
    print_step("Test Summary")

    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)

    print(f"\n{success_count}/{total_count} domains working\n")

    for result in results:
        status = "✅" if result['success'] else "❌"
        tier = result['tier']
        print(f"  {status} Tier {tier}: {result['domain']}")

    return success_count == total_count


def test_tier_progression(github_username: str):
    """
    Test tier progression for a GitHub user

    Args:
        github_username: GitHub username to test
    """
    print_step(f"Testing Tier Progression for @{github_username}")

    # This will integrate with tier_progression_engine.py once created
    # For now, show what WOULD happen

    print_info("Checking GitHub stars...")

    # Check which repos user has starred
    starred_repos = []

    for domain, config in LOCAL_DOMAINS.items():
        if 'repo' in config:
            repo = config['repo']
            # Would check via github_star_validator.py
            print(f"  • {repo['owner']}/{repo['repo']}: Not yet implemented")

    print_warning("\nTier progression engine not yet implemented")
    print_info("Will be created in tier_progression_engine.py")


# =============================================================================
# MAIN CLI
# =============================================================================

def print_usage():
    """Print usage information"""
    print(f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║     SOULFRA LOCAL DOMAIN TESTER                          ║
║     Multi-Domain Testing Without DNS                     ║
╚═══════════════════════════════════════════════════════════╝
{Colors.ENDC}

Usage:
    # Setup local domains in /etc/hosts
    sudo python3 local_domain_tester.py --setup

    # Test all domains
    python3 local_domain_tester.py --test-all

    # Test specific domain
    python3 local_domain_tester.py --test soulfra.local

    # Test tier progression for user
    python3 local_domain_tester.py --test-tier <github_username>

    # Test Ollama endpoints
    python3 local_domain_tester.py --test-ollama

    # Remove local domains from /etc/hosts
    sudo python3 local_domain_tester.py --cleanup

Local Domains:
""")

    for domain, config in LOCAL_DOMAINS.items():
        tier = config['tier']
        desc = config['description']
        print(f"  • Tier {tier}: http://{domain}:{FLASK_PORT}")
        print(f"    {desc}")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1]

    if command == '--setup':
        success = setup_local_domains()
        return 0 if success else 1

    elif command == '--cleanup':
        success = cleanup_local_domains()
        return 0 if success else 1

    elif command == '--test-all':
        success = test_all_domains()
        return 0 if success else 1

    elif command == '--test':
        if len(sys.argv) < 3:
            print_error("Missing domain argument")
            print_info("Usage: python3 local_domain_tester.py --test <domain>")
            return 1

        domain = sys.argv[2]
        result = test_domain(domain, verbose=True)
        return 0 if result['success'] else 1

    elif command == '--test-tier':
        if len(sys.argv) < 3:
            print_error("Missing GitHub username")
            print_info("Usage: python3 local_domain_tester.py --test-tier <username>")
            return 1

        username = sys.argv[2]
        test_tier_progression(username)
        return 0

    elif command == '--test-ollama':
        test_ollama_endpoints()
        return 0

    else:
        print_error(f"Unknown command: {command}")
        print_usage()
        return 1


if __name__ == '__main__':
    sys.exit(main())
