#!/usr/bin/env python3
"""
Dynamic DNS (DDNS) Updater

Automatically updates DNS records when your public IP changes (for home internet with dynamic IPs).

Supports:
- Namecheap
- GoDaddy
- Cloudflare
- No-IP
- DuckDNS

Usage:
    # Run once to update DNS:
    python3 ddns_updater.py update

    # Run continuously (check every hour):
    python3 ddns_updater.py daemon

    # Check current IP:
    python3 ddns_updater.py check

Configuration:
    Create ddns_config.json with your DNS provider credentials:
    {
        "provider": "namecheap",
        "domain": "cringeproof.com",
        "subdomain": "api",
        "api_key": "your-api-key",
        "api_password": "your-api-password",
        "check_interval": 3600
    }
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path


CONFIG_FILE = Path(__file__).parent / 'ddns_config.json'
STATE_FILE = Path(__file__).parent / 'ddns_state.json'


def load_config():
    """Load DDNS configuration from JSON file"""
    if not CONFIG_FILE.exists():
        print(f"❌ Config file not found: {CONFIG_FILE}")
        print("\nCreate ddns_config.json with your DNS provider info:")
        print('''
{
    "provider": "namecheap|godaddy|cloudflare|noip|duckdns",
    "domain": "cringeproof.com",
    "subdomain": "api",
    "api_key": "your-api-key",
    "api_password": "your-api-password",
    "check_interval": 3600
}
        ''')
        return None

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def load_state():
    """Load previous state (last IP, last update time)"""
    if not STATE_FILE.exists():
        return {'last_ip': None, 'last_update': None}

    with open(STATE_FILE, 'r') as f:
        return json.load(f)


def save_state(ip, update_time):
    """Save current state"""
    state = {
        'last_ip': ip,
        'last_update': update_time
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_public_ip():
    """
    Get current public IP address

    Returns:
        str: Public IP address (e.g., "123.45.67.89")
    """
    try:
        # Try multiple services in case one is down
        services = [
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'https://icanhazip.com'
        ]

        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # Validate IP format
                    if ip.count('.') == 3 and all(0 <= int(part) <= 255 for part in ip.split('.')):
                        return ip
            except:
                continue

        print("❌ Failed to get public IP from all services")
        return None

    except Exception as e:
        print(f"❌ Error getting public IP: {e}")
        return None


def update_namecheap(config, ip):
    """
    Update Namecheap DNS A record

    Docs: https://www.namecheap.com/support/knowledgebase/article.aspx/29/11/how-to-dynamically-update-the-hosts-ip-with-an-http-request/

    Args:
        config (dict): Config with domain, subdomain, api_password
        ip (str): New IP address

    Returns:
        bool: Success
    """
    domain = config['domain']
    subdomain = config['subdomain']
    password = config.get('api_password')

    if not password:
        print("❌ Namecheap requires 'api_password' (Dynamic DNS password)")
        return False

    url = f"https://dynamicdns.park-your-domain.com/update"
    params = {
        'host': subdomain,
        'domain': domain,
        'password': password,
        'ip': ip
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200 and '<ErrCount>0</ErrCount>' in response.text:
            print(f"✅ Namecheap DNS updated: {subdomain}.{domain} → {ip}")
            return True
        else:
            print(f"❌ Namecheap update failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Namecheap update error: {e}")
        return False


def update_godaddy(config, ip):
    """
    Update GoDaddy DNS A record via API

    Docs: https://developer.godaddy.com/doc/endpoint/domains#/v1/recordReplaceTypeName

    Args:
        config (dict): Config with domain, subdomain, api_key, api_secret
        ip (str): New IP address

    Returns:
        bool: Success
    """
    domain = config['domain']
    subdomain = config['subdomain']
    api_key = config.get('api_key')
    api_secret = config.get('api_secret')

    if not api_key or not api_secret:
        print("❌ GoDaddy requires 'api_key' and 'api_secret'")
        return False

    url = f"https://api.godaddy.com/v1/domains/{domain}/records/A/{subdomain}"
    headers = {
        'Authorization': f'sso-key {api_key}:{api_secret}',
        'Content-Type': 'application/json'
    }
    data = [{'data': ip, 'ttl': 3600}]

    try:
        response = requests.put(url, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"✅ GoDaddy DNS updated: {subdomain}.{domain} → {ip}")
            return True
        else:
            print(f"❌ GoDaddy update failed: {response.status_code} {response.text}")
            return False

    except Exception as e:
        print(f"❌ GoDaddy update error: {e}")
        return False


def update_cloudflare(config, ip):
    """
    Update Cloudflare DNS A record via API

    Docs: https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-update-dns-record

    Args:
        config (dict): Config with domain, subdomain, zone_id, api_token, record_id
        ip (str): New IP address

    Returns:
        bool: Success
    """
    zone_id = config.get('zone_id')
    record_id = config.get('record_id')
    api_token = config.get('api_token')
    subdomain = config['subdomain']
    domain = config['domain']

    if not zone_id or not record_id or not api_token:
        print("❌ Cloudflare requires 'zone_id', 'record_id', and 'api_token'")
        return False

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'type': 'A',
        'name': f"{subdomain}.{domain}",
        'content': ip,
        'ttl': 1  # Auto TTL
    }

    try:
        response = requests.put(url, json=data, headers=headers, timeout=10)
        result = response.json()

        if result.get('success'):
            print(f"✅ Cloudflare DNS updated: {subdomain}.{domain} → {ip}")
            return True
        else:
            print(f"❌ Cloudflare update failed: {result.get('errors')}")
            return False

    except Exception as e:
        print(f"❌ Cloudflare update error: {e}")
        return False


def update_noip(config, ip):
    """
    Update No-IP hostname

    Docs: https://www.noip.com/integrate/request

    Args:
        config (dict): Config with hostname, username, password
        ip (str): New IP address

    Returns:
        bool: Success
    """
    hostname = f"{config['subdomain']}.{config['domain']}"
    username = config.get('username')
    password = config.get('api_password')

    if not username or not password:
        print("❌ No-IP requires 'username' and 'api_password'")
        return False

    url = f"https://dynupdate.no-ip.com/nic/update"
    params = {'hostname': hostname, 'myip': ip}

    try:
        response = requests.get(url, params=params, auth=(username, password), timeout=10)

        if response.status_code == 200 and ('good' in response.text or 'nochg' in response.text):
            print(f"✅ No-IP DNS updated: {hostname} → {ip}")
            return True
        else:
            print(f"❌ No-IP update failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ No-IP update error: {e}")
        return False


def update_duckdns(config, ip):
    """
    Update DuckDNS hostname

    Docs: https://www.duckdns.org/spec.jsp

    Args:
        config (dict): Config with subdomain, api_token
        ip (str): New IP address

    Returns:
        bool: Success
    """
    subdomain = config['subdomain']
    token = config.get('api_token')

    if not token:
        print("❌ DuckDNS requires 'api_token'")
        return False

    url = f"https://www.duckdns.org/update"
    params = {
        'domains': subdomain,
        'token': token,
        'ip': ip
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200 and response.text.strip() == 'OK':
            print(f"✅ DuckDNS updated: {subdomain}.duckdns.org → {ip}")
            return True
        else:
            print(f"❌ DuckDNS update failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ DuckDNS update error: {e}")
        return False


def update_dns(config, ip):
    """
    Update DNS based on provider

    Args:
        config (dict): DDNS configuration
        ip (str): New IP address

    Returns:
        bool: Success
    """
    provider = config.get('provider', '').lower()

    if provider == 'namecheap':
        return update_namecheap(config, ip)
    elif provider == 'godaddy':
        return update_godaddy(config, ip)
    elif provider == 'cloudflare':
        return update_cloudflare(config, ip)
    elif provider == 'noip':
        return update_noip(config, ip)
    elif provider == 'duckdns':
        return update_duckdns(config, ip)
    else:
        print(f"❌ Unknown provider: {provider}")
        print("Supported: namecheap, godaddy, cloudflare, noip, duckdns")
        return False


def check_and_update():
    """
    Main function: Check if IP changed and update DNS if needed

    Returns:
        dict: Result
            {
                'current_ip': '123.45.67.89',
                'last_ip': '123.45.67.88',
                'changed': True,
                'updated': True
            }
    """
    config = load_config()
    if not config:
        return {'error': 'Config not found'}

    state = load_state()
    current_ip = get_public_ip()

    if not current_ip:
        return {'error': 'Failed to get public IP'}

    last_ip = state.get('last_ip')
    changed = (current_ip != last_ip)

    result = {
        'current_ip': current_ip,
        'last_ip': last_ip,
        'changed': changed,
        'updated': False
    }

    if changed or not last_ip:
        print(f"\n🔄 IP changed: {last_ip} → {current_ip}")

        if update_dns(config, current_ip):
            save_state(current_ip, datetime.now().isoformat())
            result['updated'] = True
        else:
            result['error'] = 'DNS update failed'
    else:
        print(f"✅ IP unchanged: {current_ip}")

    return result


def run_daemon(config):
    """
    Run DDNS updater in daemon mode (continuous checking)

    Args:
        config (dict): DDNS configuration
    """
    interval = config.get('check_interval', 3600)  # Default: 1 hour
    print(f"🔄 DDNS Daemon started (checking every {interval} seconds)")
    print(f"   Provider: {config.get('provider')}")
    print(f"   Domain: {config.get('subdomain')}.{config.get('domain')}")
    print("\nPress Ctrl+C to stop\n")

    try:
        while True:
            check_and_update()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n✅ DDNS Daemon stopped")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Dynamic DNS Updater")
        print("\nUsage:")
        print("  python3 ddns_updater.py check   # Check current IP")
        print("  python3 ddns_updater.py update  # Update DNS if IP changed")
        print("  python3 ddns_updater.py daemon  # Run continuously")
        sys.exit(1)

    command = sys.argv[1]

    if command == "check":
        ip = get_public_ip()
        if ip:
            print(f"Current public IP: {ip}")
            state = load_state()
            if state.get('last_ip'):
                print(f"Last known IP: {state['last_ip']}")
                if ip == state['last_ip']:
                    print("✅ IP unchanged")
                else:
                    print("⚠️  IP has changed!")
        else:
            print("❌ Failed to get IP")

    elif command == "update":
        result = check_and_update()
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            sys.exit(1)

    elif command == "daemon":
        config = load_config()
        if config:
            run_daemon(config)
        else:
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
