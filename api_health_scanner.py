#!/usr/bin/env python3
"""
API Health Scanner - Automated endpoint testing with null detection

Tests ALL Flask routes on both localhost and LAN IP (192.168.1.87)
Detects null values, empty responses, and validates data quality

Usage:
    python3 api_health_scanner.py                    # Scan all endpoints
    python3 api_health_scanner.py --quick            # Test only API routes
    python3 api_health_scanner.py --ip-only          # Test only on LAN IP
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any
import time

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
NC = '\033[0m'


class APIHealthScanner:
    """Scan all API endpoints for health issues"""

    def __init__(self, localhost='http://localhost:5001', lan_ip='http://192.168.1.87:5001'):
        self.localhost = localhost
        self.lan_ip = lan_ip
        self.results = []
        self.start_time = None

    def fetch_routes(self, base_url: str) -> Dict:
        """Fetch all routes from /status/routes endpoint"""
        try:
            response = requests.get(f"{base_url}/status/routes", timeout=5)
            data = response.json()
            return data.get('routes', {})
        except Exception as e:
            print(f"{RED}❌ Failed to fetch routes: {e}{NC}")
            return {}

    def test_endpoint(self, base_url: str, route: str) -> Dict:
        """Test a single endpoint and analyze response"""
        result = {
            'route': route,
            'base_url': base_url,
            'status': 'PENDING',
            'http_code': None,
            'response_time': None,
            'nulls_found': [],
            'empty_fields': [],
            'issues': [],
            'data_quality': 'UNKNOWN'
        }

        # Skip routes with parameters
        if '<' in route or '>' in route:
            result['status'] = 'SKIPPED'
            result['issues'].append('Route has parameters - needs manual testing')
            return result

        start = time.time()

        try:
            # Try GET request
            response = requests.get(f"{base_url}{route}", timeout=10, allow_redirects=False)
            result['http_code'] = response.status_code
            result['response_time'] = round((time.time() - start) * 1000, 2)  # ms

            # Check if response is JSON
            if 'application/json' in response.headers.get('Content-Type', ''):
                data = response.json()
                result['nulls_found'] = self._find_nulls(data)
                result['empty_fields'] = self._find_empty_fields(data)

            # Check if response is HTML
            elif 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.content, 'html.parser')

                # Check for error messages
                if soup.find(text=lambda t: 'error' in t.lower() if t else False):
                    result['issues'].append('Error text found in HTML')

                # Check if page is mostly empty
                text_content = soup.get_text(strip=True)
                if len(text_content) < 50:
                    result['issues'].append('Very little content in HTML response')

            # Determine status
            if response.status_code == 200:
                if result['nulls_found'] or result['empty_fields']:
                    result['status'] = 'WARNING'
                    result['data_quality'] = 'HAS_NULLS'
                else:
                    result['status'] = 'OK'
                    result['data_quality'] = 'GOOD'
            elif response.status_code in [301, 302, 303, 307, 308]:
                result['status'] = 'REDIRECT'
                result['data_quality'] = 'N/A'
            elif response.status_code == 404:
                result['status'] = 'NOT_FOUND'
                result['issues'].append('Route returns 404')
            else:
                result['status'] = 'ERROR'
                result['issues'].append(f'HTTP {response.status_code}')

        except requests.Timeout:
            result['status'] = 'ERROR'
            result['issues'].append('Request timeout (>10s)')
        except requests.ConnectionError:
            result['status'] = 'ERROR'
            result['issues'].append('Connection failed - server not running?')
        except Exception as e:
            result['status'] = 'ERROR'
            result['issues'].append(f'Exception: {str(e)}')

        return result

    def _find_nulls(self, data: Any, path: str = '') -> List[str]:
        """Recursively find null values in JSON data"""
        nulls = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if value is None:
                    nulls.append(current_path)
                elif isinstance(value, (dict, list)):
                    nulls.extend(self._find_nulls(value, current_path))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if item is None:
                    nulls.append(current_path)
                elif isinstance(item, (dict, list)):
                    nulls.extend(self._find_nulls(item, current_path))

        return nulls

    def _find_empty_fields(self, data: Any, path: str = '') -> List[str]:
        """Find empty strings or empty arrays/objects"""
        empty = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if value == "" or value == [] or value == {}:
                    empty.append(current_path)
                elif isinstance(value, (dict, list)):
                    empty.extend(self._find_empty_fields(value, current_path))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if item == "" or item == [] or item == {}:
                    empty.append(current_path)
                elif isinstance(item, (dict, list)):
                    empty.extend(self._find_empty_fields(item, current_path))

        return empty

    def scan_all(self, quick_mode=False, ip_only=False):
        """Scan all endpoints"""
        self.start_time = datetime.now()

        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}🔍 API Health Scanner{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")
        print(f"Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Quick (API only)' if quick_mode else 'Full Scan'}")
        print(f"Testing: {'LAN IP only' if ip_only else 'Localhost + LAN IP'}\n")

        # Test hosts to scan
        hosts_to_test = [self.lan_ip] if ip_only else [self.localhost, self.lan_ip]

        for base_url in hosts_to_test:
            print(f"\n{CYAN}━━━ Testing {base_url} ━━━{NC}\n")

            routes = self.fetch_routes(base_url)

            if not routes:
                print(f"{RED}❌ Could not fetch routes from {base_url}{NC}")
                continue

            # Filter routes if quick mode
            if quick_mode:
                routes = {k: v for k, v in routes.items() if k == 'API Endpoints'}

            total_routes = sum(len(route_list) for route_list in routes.values())
            print(f"Found {total_routes} routes to test\n")

            tested = 0
            for category, route_list in routes.items():
                print(f"\n{category} ({len(route_list)} routes)")
                print("─" * 60)

                for route in route_list:
                    tested += 1
                    result = self.test_endpoint(base_url, route)
                    self.results.append(result)

                    # Print result
                    status_color = {
                        'OK': GREEN,
                        'WARNING': YELLOW,
                        'ERROR': RED,
                        'SKIPPED': CYAN,
                        'REDIRECT': CYAN,
                        'NOT_FOUND': RED
                    }.get(result['status'], NC)

                    status_icon = {
                        'OK': '✅',
                        'WARNING': '⚠️ ',
                        'ERROR': '❌',
                        'SKIPPED': '⊘ ',
                        'REDIRECT': '↪️ ',
                        'NOT_FOUND': '❌'
                    }.get(result['status'], '?')

                    print(f"{status_icon} {status_color}{result['status']:12}{NC} {route:50} ", end='')

                    if result['response_time']:
                        print(f"({result['response_time']}ms)", end='')

                    if result['nulls_found']:
                        print(f" - {len(result['nulls_found'])} nulls", end='')

                    print()  # newline

                    # Show issues
                    if result['issues']:
                        for issue in result['issues']:
                            print(f"         └─ {issue}")

        self._print_summary()
        self._save_report()

    def _print_summary(self):
        """Print summary statistics"""
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}📊 SUMMARY{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        total = len(self.results)
        ok = len([r for r in self.results if r['status'] == 'OK'])
        warning = len([r for r in self.results if r['status'] == 'WARNING'])
        error = len([r for r in self.results if r['status'] == 'ERROR'])
        skipped = len([r for r in self.results if r['status'] == 'SKIPPED'])

        print(f"Total Endpoints Tested: {total}")
        print(f"{GREEN}✅ OK:        {ok}{NC}")
        print(f"{YELLOW}⚠️  WARNING:  {warning}{NC}")
        print(f"{RED}❌ ERROR:     {error}{NC}")
        print(f"{CYAN}⊘  SKIPPED:   {skipped}{NC}\n")

        # Routes with nulls
        routes_with_nulls = [r for r in self.results if r['nulls_found']]
        if routes_with_nulls:
            print(f"{YELLOW}🔍 Routes with NULL values:{NC}\n")
            for r in routes_with_nulls:
                print(f"   {r['route']}")
                for null_path in r['nulls_found']:
                    print(f"      • {null_path}")
                print()

        # IP accessibility
        localhost_results = [r for r in self.results if 'localhost' in r['base_url']]
        lan_results = [r for r in self.results if '192.168' in r['base_url']]

        if localhost_results and lan_results:
            localhost_ok = len([r for r in localhost_results if r['status'] == 'OK'])
            lan_ok = len([r for r in lan_results if r['status'] == 'OK'])

            print(f"📡 IP Accessibility:")
            print(f"   Localhost: {localhost_ok}/{len(localhost_results)} OK")
            print(f"   LAN IP:    {lan_ok}/{len(lan_results)} OK")

            if lan_ok < localhost_ok:
                print(f"\n{RED}⚠️  LAN IP has fewer working endpoints than localhost!{NC}")
                print(f"   Roommates may not be able to access all features.\n")

    def _save_report(self):
        """Save report to JSON file"""
        report = {
            'scan_time': self.start_time.isoformat(),
            'total_endpoints': len(self.results),
            'summary': {
                'ok': len([r for r in self.results if r['status'] == 'OK']),
                'warning': len([r for r in self.results if r['status'] == 'WARNING']),
                'error': len([r for r in self.results if r['status'] == 'ERROR']),
                'skipped': len([r for r in self.results if r['status'] == 'SKIPPED'])
            },
            'results': self.results
        }

        with open('API_HEALTH_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{GREEN}✅ Report saved to API_HEALTH_REPORT.json{NC}\n")


def main():
    parser = argparse.ArgumentParser(description='API Health Scanner')
    parser.add_argument('--quick', action='store_true', help='Quick mode (API endpoints only)')
    parser.add_argument('--ip-only', action='store_true', help='Test LAN IP only')
    parser.add_argument('--localhost', default='http://localhost:5001', help='Localhost URL')
    parser.add_argument('--lan-ip', default='http://192.168.1.87:5001', help='LAN IP URL')

    args = parser.parse_args()

    scanner = APIHealthScanner(localhost=args.localhost, lan_ip=args.lan_ip)
    scanner.scan_all(quick_mode=args.quick, ip_only=args.ip_only)


if __name__ == '__main__':
    main()
