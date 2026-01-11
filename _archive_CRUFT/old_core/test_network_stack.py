#!/usr/bin/env python3
"""
Network Stack Tester - Tests all 9 layers of Soulfra deployment

This script tests EVERY layer from OS to domain and shows you:
1. Which layers are working
2. WHERE each connection point is (file/line/config)
3. How to fix broken layers
4. Next steps to progress to next tier

Usage:
    python3 test_network_stack.py
    python3 test_network_stack.py --verbose
    python3 test_network_stack.py --fix-suggestions
"""

import socket
import subprocess
import sys
import os
import requests
import platform
from pathlib import Path
from typing import Dict, List, Tuple
import json

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


class NetworkStackTester:
    """Tests all 9 layers of the network stack"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = []
        self.working_dir = Path(__file__).parent

    def print_header(self):
        """Print test header"""
        print(f"\n{BOLD}{'=' * 80}{RESET}")
        print(f"{BOLD}{BLUE}SOULFRA NETWORK STACK TESTER{RESET}")
        print(f"{GRAY}Testing all 9 layers from OS → Domain{RESET}")
        print(f"{BOLD}{'=' * 80}{RESET}\n")

    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')
        total = len(self.results)

        print(f"\n{BOLD}{'=' * 80}{RESET}")
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print(f"{BOLD}{'=' * 80}{RESET}")
        print(f"{GREEN}✓ Passed:  {passed}/{total}{RESET}")
        print(f"{RED}✗ Failed:  {failed}/{total}{RESET}")
        print(f"{YELLOW}⊘ Skipped: {skipped}/{total}{RESET}")
        print(f"{BOLD}{'=' * 80}{RESET}\n")

        # Show current tier
        if passed >= 4:
            print(f"{GREEN}{BOLD}🎉 TIER 1 WORKING: localhost access{RESET}")
        if passed >= 6:
            print(f"{GREEN}{BOLD}🎉 TIER 2 WORKING: LAN access{RESET}")
        if passed >= 7:
            print(f"{GREEN}{BOLD}🎉 TIER 3 WORKING: Public IP access{RESET}")
        if passed >= 9:
            print(f"{GREEN}{BOLD}🎉 TIER 4 WORKING: Domain access{RESET}")

        # Next steps
        print(f"\n{BOLD}NEXT STEPS:{RESET}")
        if passed < 4:
            print(f"{YELLOW}→ Fix basic setup to enable localhost access{RESET}")
        elif passed < 6:
            print(f"{YELLOW}→ Configure network/firewall to enable LAN access{RESET}")
        elif passed < 7:
            print(f"{YELLOW}→ Configure router port forwarding for public IP{RESET}")
        elif passed < 9:
            print(f"{YELLOW}→ Configure DNS records for domain access{RESET}")
        else:
            print(f"{GREEN}→ All tiers working! Consider adding HTTPS (SSL/TLS){RESET}")

    def test_layer(self, layer_num: int, name: str, test_func) -> Dict:
        """Run a single layer test"""
        print(f"\n{BOLD}[{layer_num}/9] {name}{RESET}")
        print(f"{GRAY}{'─' * 80}{RESET}")

        try:
            result = test_func()
            result['layer'] = layer_num
            result['name'] = name
            self.results.append(result)

            # Print result
            status_color = GREEN if result['status'] == 'PASS' else (YELLOW if result['status'] == 'SKIP' else RED)
            status_symbol = '✓' if result['status'] == 'PASS' else ('⊘' if result['status'] == 'SKIP' else '✗')

            print(f"{status_color}{BOLD}Status: {status_symbol} {result['status']}{RESET}")
            print(f"{CYAN}Connection Point: {result['connection_point']}{RESET}")

            if result.get('current_value'):
                print(f"{GRAY}Current Value: {result['current_value']}{RESET}")

            if result['status'] == 'FAIL' and result.get('fix'):
                print(f"{YELLOW}How to Fix: {result['fix']}{RESET}")

            if self.verbose and result.get('details'):
                print(f"{GRAY}Details: {result['details']}{RESET}")

            return result

        except Exception as e:
            result = {
                'layer': layer_num,
                'name': name,
                'status': 'FAIL',
                'connection_point': 'Unknown',
                'fix': f'Exception occurred: {str(e)}',
                'error': str(e)
            }
            self.results.append(result)
            print(f"{RED}{BOLD}Status: ✗ FAIL{RESET}")
            print(f"{RED}Error: {str(e)}{RESET}")
            return result

    # ========== LAYER TESTS ==========

    def layer1_os(self) -> Dict:
        """Layer 1: Operating System - Can bind to network ports?"""

        # Test if we can create a socket
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Try to bind to port 5001
            try:
                test_socket.bind(('127.0.0.1', 5001))
                test_socket.close()
                port_available = True
                port_status = "Available"
            except OSError:
                # Port in use - that's actually good! Means server might be running
                port_available = False
                port_status = "In use (server may be running)"

            os_info = f"{platform.system()} {platform.release()}"

            return {
                'status': 'PASS',
                'connection_point': 'Python socket.socket() → OS network stack',
                'current_value': f"OS: {os_info}, Port 5001: {port_status}",
                'details': f'Python can create sockets and access OS network layer'
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'connection_point': 'Python socket.socket() → OS network stack',
                'fix': 'Check OS permissions. You may need to run as administrator/root for ports < 1024',
                'error': str(e)
            }

    def layer2_python(self) -> Dict:
        """Layer 2: Python - Is Python and required modules installed?"""

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Check Flask
        try:
            import flask
            flask_version = flask.__version__
            flask_ok = True
        except ImportError:
            flask_version = "Not installed"
            flask_ok = False

        # Check if app.py exists
        app_py = self.working_dir / "app.py"
        app_exists = app_py.exists()

        if flask_ok and app_exists:
            return {
                'status': 'PASS',
                'connection_point': 'requirements.txt → pip → Python modules',
                'current_value': f"Python {python_version}, Flask {flask_version}",
                'details': f'app.py exists at {app_py}'
            }
        else:
            fixes = []
            if not flask_ok:
                fixes.append("pip3 install -r requirements.txt")
            if not app_exists:
                fixes.append(f"app.py not found at {app_py}")

            return {
                'status': 'FAIL',
                'connection_point': 'requirements.txt → pip → Python modules',
                'current_value': f"Python {python_version}, Flask {flask_version}",
                'fix': '; '.join(fixes)
            }

    def layer3_flask(self) -> Dict:
        """Layer 3: Flask - Can Flask app be imported and configured?"""

        try:
            # Try to import app
            sys.path.insert(0, str(self.working_dir))

            # Check if app module exists
            app_py = self.working_dir / "app.py"

            # Read app.py to find host/port configuration
            with open(app_py, 'r') as f:
                content = f.read()

                # Look for app.run() call
                if "app.run(" in content:
                    # Extract host and port
                    for line in content.split('\n'):
                        if 'app.run(' in line and not line.strip().startswith('#'):
                            host = "0.0.0.0" if "host='0.0.0.0'" in line or 'host="0.0.0.0"' in line else "127.0.0.1"
                            port = "5001" if "5001" in line else "5000"

                            return {
                                'status': 'PASS',
                                'connection_point': 'app.py:app.run() → Flask HTTP server',
                                'current_value': f"Host: {host}, Port: {port}",
                                'details': f'Found in {app_py}. host=0.0.0.0 enables LAN access'
                            }

            return {
                'status': 'FAIL',
                'connection_point': 'app.py:app.run() → Flask HTTP server',
                'fix': 'Add app.run(host="0.0.0.0", port=5001) to app.py',
                'current_value': 'No app.run() call found'
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'connection_point': 'app.py → Flask application',
                'fix': f'Check app.py syntax: {str(e)}',
                'error': str(e)
            }

    def layer4_server(self) -> Dict:
        """Layer 4: Server - Is Flask dev server or gunicorn running?"""

        # Check if server is running on port 5001
        try:
            response = requests.get('http://127.0.0.1:5001', timeout=2)

            # Server is running!
            server_header = response.headers.get('Server', 'Unknown')

            # Detect server type
            if 'gunicorn' in server_header.lower():
                server_type = 'gunicorn (production)'
            elif 'Werkzeug' in server_header:
                server_type = 'Flask development server'
            else:
                server_type = server_header

            return {
                'status': 'PASS',
                'connection_point': 'Flask/gunicorn → HTTP socket on 0.0.0.0:5001',
                'current_value': f"Server: {server_type}, Status: {response.status_code}",
                'details': f'Server accessible at http://127.0.0.1:5001'
            }

        except requests.exceptions.ConnectionError:
            return {
                'status': 'FAIL',
                'connection_point': 'Flask/gunicorn → HTTP socket on 0.0.0.0:5001',
                'fix': 'Start server: python3 app.py OR gunicorn -w 4 -b 0.0.0.0:5001 app:app',
                'current_value': 'Server not responding on port 5001'
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'connection_point': 'Flask/gunicorn → HTTP socket on 0.0.0.0:5001',
                'fix': f'Check server status: {str(e)}',
                'error': str(e)
            }

    def layer5_nginx(self) -> Dict:
        """Layer 5: Nginx - Is nginx reverse proxy configured? (Optional)"""

        # Check if nginx is installed
        try:
            result = subprocess.run(['which', 'nginx'], capture_output=True, text=True)
            nginx_installed = result.returncode == 0
        except:
            nginx_installed = False

        if not nginx_installed:
            return {
                'status': 'SKIP',
                'connection_point': 'nginx.conf → proxy_pass → Flask server',
                'current_value': 'nginx not installed (optional for development)',
                'details': 'nginx is optional but recommended for production'
            }

        # Check if nginx is running
        try:
            result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
            nginx_configured = result.returncode == 0

            # Check if soulfra config exists
            nginx_configs = [
                '/etc/nginx/sites-enabled/soulfra',
                '/etc/nginx/conf.d/soulfra.conf',
                '/usr/local/etc/nginx/servers/soulfra.conf'
            ]

            soulfra_config = None
            for config in nginx_configs:
                if Path(config).exists():
                    soulfra_config = config
                    break

            if soulfra_config:
                return {
                    'status': 'PASS',
                    'connection_point': f'{soulfra_config} → proxy_pass http://localhost:5001',
                    'current_value': 'nginx configured for Soulfra',
                    'details': f'Config found at {soulfra_config}'
                }
            else:
                return {
                    'status': 'SKIP',
                    'connection_point': 'nginx.conf → proxy_pass → Flask server',
                    'current_value': 'nginx installed but no Soulfra config found',
                    'fix': 'Create /etc/nginx/sites-enabled/soulfra with proxy_pass to localhost:5001'
                }

        except Exception as e:
            return {
                'status': 'SKIP',
                'connection_point': 'nginx.conf → proxy_pass → Flask server',
                'current_value': f'nginx check failed: {str(e)}',
                'details': 'nginx is optional for development'
            }

    def layer6_lan(self) -> Dict:
        """Layer 6: LAN - Can access from other devices on local network?"""

        # Get local IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "Unknown"

        # Check if server is bound to 0.0.0.0 (required for LAN access)
        app_py = self.working_dir / "app.py"

        try:
            with open(app_py, 'r') as f:
                content = f.read()

                if "host='0.0.0.0'" in content or 'host="0.0.0.0"' in content:
                    return {
                        'status': 'PASS',
                        'connection_point': 'app.py:app.run(host="0.0.0.0") → All network interfaces',
                        'current_value': f'LAN IP: {local_ip}:5001',
                        'details': f'Server should be accessible from LAN at http://{local_ip}:5001'
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'connection_point': 'app.py:app.run(host="127.0.0.1") → localhost only',
                        'current_value': f'Server bound to localhost only',
                        'fix': 'Change app.run(host="127.0.0.1") to app.run(host="0.0.0.0") in app.py'
                    }
        except Exception as e:
            return {
                'status': 'FAIL',
                'connection_point': 'app.py:app.run() → network binding',
                'fix': f'Could not read app.py: {str(e)}',
                'error': str(e)
            }

    def layer7_public_ip(self) -> Dict:
        """Layer 7: Public IP - Can access from internet via public IP?"""

        # Get public IP
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            public_ip = response.json()['ip']
        except:
            public_ip = "Unknown"

        # Check if port forwarding might be configured
        # (We can't actually test this without external access)

        return {
            'status': 'SKIP',
            'connection_point': 'Router port forwarding: WAN:5001 → LAN_IP:5001',
            'current_value': f'Public IP: {public_ip}',
            'details': 'Requires router port forwarding configuration',
            'fix': 'Configure router: forward port 5001 to your local IP. Then test with http://' + public_ip + ':5001'
        }

    def layer8_dns(self) -> Dict:
        """Layer 8: DNS - Are DNS records configured?"""

        # Check .env for domain configuration
        env_file = self.working_dir / ".env"
        domain = None

        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DOMAIN='):
                        domain = line.split('=')[1].strip()
                    elif line.startswith('BASE_URL='):
                        url = line.split('=')[1].strip()
                        if 'localhost' not in url:
                            # Extract domain from URL
                            domain = url.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]

        if not domain or domain == 'localhost':
            return {
                'status': 'SKIP',
                'connection_point': '.env:DOMAIN → DNS A/CNAME records',
                'current_value': 'No domain configured',
                'details': 'Using localhost - no DNS needed',
                'fix': 'Set DOMAIN=yourdomain.com in .env and configure DNS records'
            }

        # Try to resolve domain
        try:
            ip = socket.gethostbyname(domain)

            return {
                'status': 'PASS',
                'connection_point': f'DNS A record: {domain} → {ip}',
                'current_value': f'Domain: {domain} resolves to {ip}',
                'details': f'Use: python3 dns_setup_guide.py to configure DNS'
            }

        except socket.gaierror:
            return {
                'status': 'FAIL',
                'connection_point': f'DNS records for {domain}',
                'current_value': f'Domain {domain} does not resolve',
                'fix': f'Add DNS A record: {domain} → YOUR_PUBLIC_IP at your domain registrar'
            }

    def layer9_domain(self) -> Dict:
        """Layer 9: Domain - Can access via domain name?"""

        # Check .env for domain
        env_file = self.working_dir / ".env"
        domain = None
        base_url = None

        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DOMAIN='):
                        domain = line.split('=')[1].strip()
                    elif line.startswith('BASE_URL='):
                        base_url = line.split('=')[1].strip()

        if not domain or domain == 'localhost':
            return {
                'status': 'SKIP',
                'connection_point': 'Domain URL → DNS → Public IP → Router → Server',
                'current_value': 'No domain configured',
                'details': 'Using localhost - no domain needed for development'
            }

        # Try to access via domain
        if base_url and 'localhost' not in base_url:
            try:
                response = requests.get(base_url, timeout=5)

                return {
                    'status': 'PASS',
                    'connection_point': f'{base_url} → Full network stack → Flask server',
                    'current_value': f'Domain accessible! Status: {response.status_code}',
                    'details': f'Complete chain working: Domain → DNS → IP → Server'
                }

            except requests.exceptions.ConnectionError:
                return {
                    'status': 'FAIL',
                    'connection_point': f'{base_url} → DNS/Router/Server chain',
                    'current_value': 'Domain resolves but server not accessible',
                    'fix': 'Check: 1) Server running, 2) Port forwarding configured, 3) Firewall allows port 5001'
                }
            except Exception as e:
                return {
                    'status': 'FAIL',
                    'connection_point': f'{base_url} → Full network stack',
                    'fix': f'Error accessing domain: {str(e)}',
                    'error': str(e)
                }
        else:
            return {
                'status': 'SKIP',
                'connection_point': 'BASE_URL → Full network stack',
                'current_value': 'BASE_URL not configured for domain',
                'fix': 'Set BASE_URL=http://yourdomain.com in .env'
            }

    def run_all_tests(self):
        """Run all 9 layer tests"""
        self.print_header()

        # Run each layer test
        self.test_layer(1, "Operating System (Network Stack)", self.layer1_os)
        self.test_layer(2, "Python Environment", self.layer2_python)
        self.test_layer(3, "Flask Application", self.layer3_flask)
        self.test_layer(4, "HTTP Server (Flask/gunicorn)", self.layer4_server)
        self.test_layer(5, "Nginx Reverse Proxy (Optional)", self.layer5_nginx)
        self.test_layer(6, "Local Area Network (LAN)", self.layer6_lan)
        self.test_layer(7, "Public IP Access", self.layer7_public_ip)
        self.test_layer(8, "DNS Configuration", self.layer8_dns)
        self.test_layer(9, "Domain Access", self.layer9_domain)

        # Print summary
        self.print_summary()

        # Return results
        return self.results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Soulfra network stack (all 9 layers)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    args = parser.parse_args()

    tester = NetworkStackTester(verbose=args.verbose)
    results = tester.run_all_tests()

    if args.json:
        print("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
