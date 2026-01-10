#!/usr/bin/env python3
"""
Deployment Verification System

Automatically verifies that pushed code is actually live on production domains.
Compares GitHub repo commits vs what's served, alerts on cache issues.
"""

import requests
import subprocess
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time

# Domain → GitHub Repo mapping
DEPLOYMENTS = {
    'cringeproof.com': {
        'repo': 'Soulfra/voice-archive',
        'branch': 'main',
        'critical_files': [
            'encyclopedia.html',
            'popup-ui.js',
            'popup-ui.css',
            'voice-feedback.js'
        ]
    },
    'soulfra.com': {
        'repo': 'Soulfra/soulfra',  # TODO: verify actual repo name
        'branch': 'main',
        'critical_files': ['index.html']
    },
    'calriven.com': {
        'repo': 'Soulfra/calriven',  # TODO: verify actual repo name
        'branch': 'main',
        'critical_files': ['index.html']
    }
}


def get_latest_commit_sha(repo, branch='main'):
    """Get latest commit SHA from GitHub repo"""
    url = f"https://api.github.com/repos/{repo}/commits/{branch}"
    try:
        response = requests.get(url, timeout=10)
        if response.ok:
            data = response.json()
            return {
                'sha': data['sha'][:7],
                'message': data['commit']['message'].split('\n')[0],
                'date': data['commit']['committer']['date'],
                'author': data['commit']['author']['name']
            }
    except Exception as e:
        print(f"❌ Failed to fetch commit for {repo}: {e}")
    return None


def check_file_exists(domain, file_path):
    """Check if file exists on production domain"""
    url = f"https://{domain}/{file_path}"
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except Exception as e:
        return False


def get_cache_headers(domain):
    """Get caching headers from production"""
    url = f"https://{domain}/"
    try:
        response = requests.head(url, timeout=10)
        return {
            'last_modified': response.headers.get('Last-Modified'),
            'etag': response.headers.get('ETag'),
            'cache_control': response.headers.get('Cache-Control'),
            'age': response.headers.get('Age'),
            'server': response.headers.get('Server'),
            'x_cache': response.headers.get('X-Cache')
        }
    except Exception as e:
        return {'error': str(e)}


def parse_github_date(date_str):
    """Parse GitHub date to timestamp"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        return dt.timestamp()
    except:
        return 0


def parse_http_date(date_str):
    """Parse HTTP Last-Modified date to timestamp"""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.timestamp()
    except:
        return 0


def verify_deployment(domain, config):
    """Verify a single deployment"""
    print(f"\n{'='*60}")
    print(f"🔍 Verifying: {domain}")
    print(f"{'='*60}")

    # 1. Get latest commit from GitHub
    commit = get_latest_commit_sha(config['repo'], config['branch'])
    if not commit:
        print(f"❌ Could not fetch latest commit from {config['repo']}")
        return False

    print(f"\n📦 Latest Commit:")
    print(f"   SHA: {commit['sha']}")
    print(f"   Message: {commit['message']}")
    print(f"   Date: {commit['date']}")
    print(f"   Author: {commit['author']}")

    # 2. Check cache headers
    headers = get_cache_headers(domain)
    print(f"\n🌐 Production Cache:")
    print(f"   Server: {headers.get('server', 'Unknown')}")
    print(f"   Last-Modified: {headers.get('last_modified', 'Unknown')}")
    print(f"   Cache Status: {headers.get('x_cache', 'Unknown')}")
    print(f"   Age: {headers.get('age', 'Unknown')} seconds")

    # 3. Compare timestamps
    commit_time = parse_github_date(commit['date'])
    cache_time = parse_http_date(headers.get('last_modified', ''))

    if cache_time and commit_time:
        time_diff = commit_time - cache_time
        if time_diff > 300:  # More than 5 minutes old
            print(f"\n⚠️  WARNING: Cache is stale!")
            print(f"   Commit pushed: {datetime.fromtimestamp(commit_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Site built: {datetime.fromtimestamp(cache_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Difference: {int(time_diff/60)} minutes behind")
            return False
        else:
            print(f"\n✅ Cache is fresh (within 5 minutes)")

    # 4. Verify critical files exist
    print(f"\n📄 Checking Critical Files:")
    all_files_exist = True
    for file_path in config['critical_files']:
        exists = check_file_exists(domain, file_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_files_exist = False

    return all_files_exist and (not time_diff or time_diff < 300)


def verify_all_deployments():
    """Verify all configured deployments"""
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT VERIFICATION")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}
    for domain, config in DEPLOYMENTS.items():
        try:
            results[domain] = verify_deployment(domain, config)
        except Exception as e:
            print(f"\n❌ Error verifying {domain}: {e}")
            results[domain] = False

    # Summary
    print(f"\n\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")

    for domain, success in results.items():
        status = "✅ LIVE" if success else "❌ STALE/BROKEN"
        print(f"{status} {domain}")

    all_pass = all(results.values())

    if not all_pass:
        print(f"\n⚠️  Some deployments are broken!")
        print(f"\n🔧 Recommended Actions:")
        print(f"   1. Check GitHub Actions: https://github.com/{list(DEPLOYMENTS.values())[0]['repo']}/actions")
        print(f"   2. Force rebuild: git commit --allow-empty -m 'Rebuild' && git push")
        print(f"   3. Clear CDN cache")
        print(f"   4. Wait 2-3 minutes and re-run this script")
    else:
        print(f"\n✅ All deployments are live!")

    return all_pass


def watch_deployment(domain, interval=30, timeout=300):
    """Watch a deployment until it goes live or times out"""
    print(f"\n👀 Watching {domain} for deployment...")
    print(f"   Will check every {interval} seconds for {timeout//60} minutes")

    config = DEPLOYMENTS.get(domain)
    if not config:
        print(f"❌ Unknown domain: {domain}")
        return False

    start_time = time.time()
    attempt = 1

    while time.time() - start_time < timeout:
        print(f"\n[Attempt {attempt}] Checking...")

        if verify_deployment(domain, config):
            print(f"\n✅ {domain} is LIVE!")
            return True

        elapsed = int(time.time() - start_time)
        remaining = timeout - elapsed

        if remaining > 0:
            print(f"\n⏳ Waiting {interval} seconds... ({remaining}s remaining)")
            time.sleep(interval)
            attempt += 1

    print(f"\n❌ Timeout: {domain} did not go live within {timeout//60} minutes")
    return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'watch' and len(sys.argv) > 2:
            domain = sys.argv[2]
            watch_deployment(domain)
        elif command == 'verify' and len(sys.argv) > 2:
            domain = sys.argv[2]
            config = DEPLOYMENTS.get(domain)
            if config:
                verify_deployment(domain, config)
            else:
                print(f"❌ Unknown domain: {domain}")
        else:
            print("Usage:")
            print("  python3 deployment_verifier.py              # Verify all deployments")
            print("  python3 deployment_verifier.py verify <domain>")
            print("  python3 deployment_verifier.py watch <domain>")
    else:
        verify_all_deployments()
