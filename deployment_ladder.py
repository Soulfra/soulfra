#!/usr/bin/env python3
"""
Deployment Ladder - Climb from localhost to production step-by-step

This interactive tool helps you progressively deploy Soulfra:
  Rung 1: Localhost only (development)
  Rung 2: LAN access (test on other devices)
  Rung 3: Public IP (accessible from internet)
  Rung 4: Domain name (production ready)
  Rung 5: HTTPS/SSL (secure production)

Each rung tests what you have, configures what you need, and guides you to the next level.

Usage:
    python3 deployment_ladder.py
    python3 deployment_ladder.py --skip-tests    # Skip automated tests
    python3 deployment_ladder.py --rung 3        # Start at specific rung
"""

import os
import sys
import socket
import subprocess
import requests
import secrets
from pathlib import Path
import argparse

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


class DeploymentLadder:
    """Interactive deployment ladder"""

    def __init__(self, skip_tests=False, start_rung=1):
        self.skip_tests = skip_tests
        self.start_rung = start_rung
        self.working_dir = Path(__file__).parent
        self.app_py = self.working_dir / "app.py"
        self.env_file = self.working_dir / ".env"

        self.local_ip = None
        self.public_ip = None
        self.domain = None

    # ========== Helper Methods ==========

    def print_header(self, text):
        """Print section header"""
        print(f"\n{BOLD}{'=' * 80}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{'=' * 80}{RESET}\n")

    def print_rung(self, num, name, status=""):
        """Print rung header"""
        status_text = f" [{status}]" if status else ""
        print(f"\n{BOLD}{CYAN}╔═══════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{BOLD}{CYAN}║ RUNG {num}: {name:<60}{status_text:>9} ║{RESET}")
        print(f"{BOLD}{CYAN}╚═══════════════════════════════════════════════════════════════════════════╝{RESET}\n")

    def success(self, msg):
        print(f"{GREEN}✓ {msg}{RESET}")

    def error(self, msg):
        print(f"{RED}✗ {msg}{RESET}")

    def warning(self, msg):
        print(f"{YELLOW}⚠ {msg}{RESET}")

    def info(self, msg):
        print(f"{CYAN}→ {msg}{RESET}")

    def prompt(self, question, default="y"):
        """Prompt user for yes/no"""
        choices = "Y/n" if default == "y" else "y/N"
        response = input(f"{GRAY}{question} [{choices}]: {RESET}").strip().lower()

        if not response:
            return default == "y"

        return response.startswith('y')

    def input_text(self, question, default=""):
        """Prompt user for text input"""
        default_text = f" [{default}]" if default else ""
        response = input(f"{GRAY}{question}{default_text}: {RESET}").strip()

        return response if response else default

    def wait(self):
        """Wait for user to press Enter"""
        input(f"\n{GRAY}Press Enter to continue...{RESET}")

    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def get_public_ip(self):
        """Get public IP address"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return None

    def check_server_running(self, url="http://localhost:5001"):
        """Check if server is running"""
        try:
            response = requests.get(url, timeout=2)
            return True
        except:
            return False

    def read_file(self, filepath):
        """Read file contents"""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except:
            return None

    def write_file(self, filepath, content):
        """Write file contents"""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            self.error(f"Failed to write {filepath}: {e}")
            return False

    def update_env(self, key, value):
        """Update .env file"""
        if not self.env_file.exists():
            content = ""
        else:
            content = self.read_file(self.env_file)

        lines = content.split('\n')
        found = False

        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break

        if not found:
            lines.append(f"{key}={value}")

        new_content = '\n'.join(lines)
        return self.write_file(self.env_file, new_content)

    # ========== Rung Implementations ==========

    def rung1_localhost(self):
        """Rung 1: Localhost access"""

        self.print_rung(1, "Localhost Access (Development)", "TESTING")

        print(f"{GRAY}This rung ensures Soulfra runs on your local machine.{RESET}\n")

        # Check if server is running
        if not self.skip_tests:
            self.info("Testing localhost:5001...")

            if self.check_server_running():
                self.success("Server is already running!")
            else:
                self.error("Server is not running")

                print()
                if self.prompt("Start the server now?"):
                    self.info("Starting server...")
                    print(f"{YELLOW}Run this command in another terminal:{RESET}")
                    print(f"  {BOLD}python3 app.py{RESET}")
                    print()
                    self.wait()

                    if self.check_server_running():
                        self.success("Server started successfully!")
                    else:
                        self.error("Server still not responding. Please start it manually.")
                        return False
                else:
                    return False

        # Check app.py configuration
        self.info("Checking app.py configuration...")

        app_content = self.read_file(self.app_py)
        if app_content and "app.run(" in app_content:
            self.success("app.py found")

            # Check if debug mode
            if "debug=True" in app_content:
                self.warning("Debug mode enabled (OK for development)")
        else:
            self.error("app.py not found or invalid")
            return False

        # Success
        print()
        self.print_rung(1, "Localhost Access", f"{GREEN}COMPLETE{RESET}")
        self.success("You can access Soulfra at: http://localhost:5001")

        print()
        self.info("Next: Enable LAN access to test on other devices")

        return True

    def rung2_lan(self):
        """Rung 2: LAN access"""

        self.print_rung(2, "LAN Access (Local Network)", "CONFIGURING")

        print(f"{GRAY}This rung enables access from other devices on your network.{RESET}\n")

        # Get local IP
        self.local_ip = self.get_local_ip()

        if not self.local_ip:
            self.error("Could not detect local IP address")
            return False

        self.info(f"Your local IP: {self.local_ip}")

        # Check app.py host setting
        self.info("Checking host configuration...")

        app_content = self.read_file(self.app_py)

        if "host='0.0.0.0'" in app_content or 'host="0.0.0.0"' in app_content:
            self.success("Server bound to 0.0.0.0 (all interfaces)")
            needs_update = False
        elif "host='127.0.0.1'" in app_content or 'host="127.0.0.1"' in app_content:
            self.warning("Server bound to 127.0.0.1 (localhost only)")
            needs_update = True
        else:
            self.warning("Could not detect host binding")
            needs_update = True

        # Update if needed
        if needs_update:
            print()
            print(f"{YELLOW}To enable LAN access, you need to bind to 0.0.0.0{RESET}")
            print(f"{GRAY}This tells the server to listen on ALL network interfaces.{RESET}")

            print()
            if self.prompt("Update app.py to bind to 0.0.0.0?"):
                # Update app.py
                new_content = app_content.replace(
                    "host='127.0.0.1'",
                    "host='0.0.0.0'"
                ).replace(
                    'host="127.0.0.1"',
                    'host="0.0.0.0"'
                )

                if self.write_file(self.app_py, new_content):
                    self.success("Updated app.py")

                    print()
                    self.warning("You need to restart the server for changes to take effect!")
                    self.wait()
                else:
                    self.error("Failed to update app.py")
                    return False
            else:
                return False

        # Test LAN access
        if not self.skip_tests:
            self.info(f"Testing LAN access at {self.local_ip}:5001...")

            if self.check_server_running(f"http://{self.local_ip}:5001"):
                self.success("LAN access working!")
            else:
                self.error("LAN access not working")

                print()
                self.warning("Common issues:")
                print("  • Server not bound to 0.0.0.0")
                print("  • Server not restarted after config change")
                print("  • Firewall blocking connections")

                if not self.prompt("Continue anyway?"):
                    return False

        # Success
        print()
        self.print_rung(2, "LAN Access", f"{GREEN}COMPLETE{RESET}")
        self.success(f"Accessible from LAN at: http://{self.local_ip}:5001")

        print()
        self.info("Test on another device:")
        print(f"  • Connect phone/tablet to same WiFi")
        print(f"  • Visit: {BOLD}http://{self.local_ip}:5001{RESET}")

        print()
        self.info("Next: Configure router for public internet access")

        return True

    def rung3_public_ip(self):
        """Rung 3: Public IP access"""

        self.print_rung(3, "Public IP Access (Internet)", "CONFIGURING")

        print(f"{GRAY}This rung makes Soulfra accessible from the public internet.{RESET}\n")

        # Get public IP
        self.public_ip = self.get_public_ip()

        if not self.public_ip:
            self.error("Could not detect public IP address")
            return False

        self.info(f"Your public IP: {self.public_ip}")

        # Get local IP
        if not self.local_ip:
            self.local_ip = self.get_local_ip()

        # Explain port forwarding
        print()
        print(f"{YELLOW}{BOLD}PORT FORWARDING REQUIRED{RESET}")
        print(f"{GRAY}You need to configure port forwarding on your router.{RESET}")
        print()
        print("This tells your router to forward internet requests to your computer.")
        print()

        print(f"{BOLD}Configuration needed:{RESET}")
        print(f"  External Port:  5001")
        print(f"  Internal IP:    {self.local_ip}")
        print(f"  Internal Port:  5001")
        print(f"  Protocol:       TCP")

        print()
        print(f"{GRAY}Steps:{RESET}")
        print("  1. Access your router admin panel (usually http://192.168.1.1)")
        print("  2. Find 'Port Forwarding' or 'Virtual Server' settings")
        print("  3. Add the rule above")
        print("  4. Save and apply")

        print()
        if not self.prompt("Have you configured port forwarding?", default="n"):
            self.warning("Configure port forwarding and re-run this script")
            return False

        # Test (limited - can't test from inside network)
        print()
        self.warning("Testing public IP from inside your network is unreliable (NAT loopback)")

        print()
        print(f"{BOLD}Test from external network:{RESET}")
        print(f"  • Use phone cellular data (NOT WiFi)")
        print(f"  • Visit: {BOLD}http://{self.public_ip}:5001{RESET}")
        print()
        print("Or use online port checker:")
        print(f"  • Visit: https://www.yougetsignal.com/tools/open-ports/")
        print(f"  • Enter IP: {self.public_ip}, Port: 5001")

        print()
        if not self.prompt("Did the external test work?", default="n"):
            print()
            self.warning("Common issues:")
            print("  • Port forwarding not configured correctly")
            print("  • ISP blocks port 5001 (try different port)")
            print("  • Router firewall blocking")
            print("  • Server not running")

            if not self.prompt("Continue anyway?"):
                return False

        # Success
        print()
        self.print_rung(3, "Public IP Access", f"{GREEN}COMPLETE{RESET}")
        self.success(f"Accessible from internet at: http://{self.public_ip}:5001")

        print()
        self.info("Next: Configure domain name for professional URL")

        return True

    def rung4_domain(self):
        """Rung 4: Domain name"""

        self.print_rung(4, "Domain Name (Production)", "CONFIGURING")

        print(f"{GRAY}This rung gives you a professional domain name.{RESET}\n")

        # Check if domain already configured
        if self.env_file.exists():
            env_content = self.read_file(self.env_file)

            for line in env_content.split('\n'):
                if line.startswith('DOMAIN='):
                    existing_domain = line.split('=')[1].strip()
                    if existing_domain and existing_domain != 'localhost':
                        self.domain = existing_domain
                        self.info(f"Found configured domain: {self.domain}")
                        break

        # Get domain from user
        if not self.domain:
            print("You need a domain name. You can:")
            print("  • Buy one from GoDaddy, Namecheap, etc. (~$10-15/year)")
            print("  • Use a free subdomain from services like FreeDNS")

            print()
            self.domain = self.input_text("Enter your domain (e.g., soulfra.com)")

            if not self.domain or self.domain == 'localhost':
                self.warning("No domain provided")
                return False

        # Generate DNS records
        print()
        self.info("Generating DNS records...")

        if not self.public_ip:
            self.public_ip = self.get_public_ip()

        print()
        print(f"{BOLD}Add these DNS records at your domain registrar:{RESET}\n")
        print(f"  {CYAN}Type{RESET}    {CYAN}Name{RESET}    {CYAN}Value{RESET}")
        print(f"  {GRAY}────────────────────────────────────────────────────{RESET}")
        print(f"  A       @       {self.public_ip}")
        print(f"  A       www     {self.public_ip}")
        print(f"  CNAME   www     {self.domain}")

        verification_token = f"soulfra-verify-{secrets.token_hex(8)}"
        print(f"  TXT     @       {verification_token}")

        print()
        print(f"{GRAY}Steps:{RESET}")
        print("  1. Log in to your domain registrar")
        print("  2. Find 'DNS Management' or 'DNS Records'")
        print("  3. Add each record above")
        print("  4. Save changes")
        print("  5. Wait 5-60 minutes for DNS propagation")

        print()
        if not self.prompt("Have you added the DNS records?", default="n"):
            self.warning("Add DNS records and re-run this script")
            return False

        # Update .env
        print()
        self.info("Updating .env file...")

        self.update_env('DOMAIN', self.domain)
        self.update_env('BASE_URL', f'http://{self.domain}')

        self.success("Updated .env")

        # Test DNS
        print()
        self.info("Testing DNS resolution...")

        try:
            resolved_ip = socket.gethostbyname(self.domain)
            self.success(f"Domain resolves to: {resolved_ip}")

            if resolved_ip == self.public_ip:
                self.success("DNS points to your public IP!")
            else:
                self.warning(f"DNS points to {resolved_ip} but your public IP is {self.public_ip}")
                print(f"{GRAY}You may need to update the DNS A record.{RESET}")

        except socket.gaierror:
            self.error(f"Domain {self.domain} does not resolve")
            self.warning("DNS may still be propagating (wait 5-60 minutes)")

            if not self.prompt("Continue anyway?"):
                return False

        # Test domain access
        if not self.skip_tests:
            print()
            self.info(f"Testing domain access at http://{self.domain}...")

            try:
                if self.check_server_running(f"http://{self.domain}"):
                    self.success("Domain is accessible!")
                else:
                    self.error("Domain not accessible")
                    self.warning("Make sure port forwarding is configured (Rung 3)")
            except:
                self.error("Could not test domain")

        # Success
        print()
        self.print_rung(4, "Domain Name", f"{GREEN}COMPLETE{RESET}")
        self.success(f"Accessible at: http://{self.domain}")

        print()
        self.warning("IMPORTANT: Restart the server for .env changes to take effect!")

        print()
        self.info("Next: Add HTTPS/SSL for secure connections")

        return True

    def rung5_https(self):
        """Rung 5: HTTPS/SSL"""

        self.print_rung(5, "HTTPS/SSL (Secure Production)", "INFO")

        print(f"{GRAY}This rung adds HTTPS for secure, encrypted connections.{RESET}\n")

        print("There are several ways to add HTTPS:")
        print()

        print(f"{BOLD}Option 1: Let's Encrypt (Free, Recommended){RESET}")
        print("  • Free SSL certificates")
        print("  • Auto-renewal")
        print("  • Requires: certbot")
        print()
        print("  Steps:")
        print("    sudo apt install certbot python3-certbot-nginx")
        print("    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com")

        print()
        print(f"{BOLD}Option 2: Cloudflare (Free, Easy){RESET}")
        print("  • Free SSL + CDN + DDoS protection")
        print("  • No server configuration needed")
        print("  • Changes nameservers")
        print()
        print("  Steps:")
        print("    1. Sign up at cloudflare.com")
        print("    2. Add your domain")
        print("    3. Change nameservers at registrar")
        print("    4. Enable 'Flexible SSL' in Cloudflare")

        print()
        print(f"{BOLD}Option 3: Nginx + SSL Certificate{RESET}")
        print("  • Manual SSL setup")
        print("  • More control")
        print("  • Requires nginx configuration")

        print()
        print(f"{GRAY}These are advanced topics covered in separate guides.{RESET}")

        print()
        self.print_rung(5, "HTTPS/SSL", f"{YELLOW}OPTIONAL{RESET}")

        print()
        self.success("Congratulations! You've climbed the deployment ladder!")

        return True

    # ========== Main Ladder Flow ==========

    def climb(self):
        """Climb the deployment ladder"""

        self.print_header("SOULFRA DEPLOYMENT LADDER")

        print(f"{GRAY}This tool will guide you step-by-step from localhost to production.{RESET}")
        print(f"{GRAY}Each 'rung' tests what you have and configures what you need.{RESET}")

        print()
        print("The ladder:")
        print(f"  {CYAN}Rung 1:{RESET} Localhost (development)")
        print(f"  {CYAN}Rung 2:{RESET} LAN access (test on other devices)")
        print(f"  {CYAN}Rung 3:{RESET} Public IP (accessible from internet)")
        print(f"  {CYAN}Rung 4:{RESET} Domain name (production ready)")
        print(f"  {CYAN}Rung 5:{RESET} HTTPS/SSL (secure production)")

        self.wait()

        # Climb each rung
        rungs = [
            (1, self.rung1_localhost),
            (2, self.rung2_lan),
            (3, self.rung3_public_ip),
            (4, self.rung4_domain),
            (5, self.rung5_https),
        ]

        for num, rung_func in rungs:
            if num < self.start_rung:
                continue

            if not rung_func():
                print()
                self.error(f"Rung {num} incomplete")
                print()
                print(f"{YELLOW}Fix the issues above and re-run this script.{RESET}")
                return False

            if num < 5:  # Don't wait after last rung
                self.wait()

        # Success
        self.print_header("DEPLOYMENT COMPLETE!")

        print(f"{GREEN}{BOLD}🎉 You've successfully deployed Soulfra!{RESET}\n")

        print("Your deployment:")
        if self.local_ip:
            print(f"  {CYAN}LAN:{RESET}       http://{self.local_ip}:5001")
        if self.public_ip:
            print(f"  {CYAN}Public IP:{RESET} http://{self.public_ip}:5001")
        if self.domain:
            print(f"  {CYAN}Domain:{RESET}    http://{self.domain}")

        print()
        print("Next steps:")
        print("  • Set up systemd service for auto-start: see LAUNCHER_GUIDE.md")
        print("  • Add HTTPS with Let's Encrypt or Cloudflare")
        print("  • Configure nginx for better performance")
        print("  • Set up GitHub Actions for auto-deployment")

        return True


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Deploy Soulfra step-by-step')
    parser.add_argument('--skip-tests', action='store_true', help='Skip automated tests')
    parser.add_argument('--rung', type=int, choices=[1,2,3,4,5], help='Start at specific rung')

    args = parser.parse_args()

    ladder = DeploymentLadder(
        skip_tests=args.skip_tests,
        start_rung=args.rung or 1
    )

    success = ladder.climb()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
