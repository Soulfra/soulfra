#!/usr/bin/env python3
"""
Network Diagram Generator - Visual representation of Soulfra's network stack

Generates ASCII art diagrams showing:
1. Your actual network topology (with real IPs)
2. Which layers are working vs not working
3. Connection points between layers
4. The full path from localhost → domain

Usage:
    python3 network_diagram.py
    python3 network_diagram.py --simple
    python3 network_diagram.py --live    # Auto-updates every 5 seconds
"""

import socket
import subprocess
import sys
import os
import requests
from pathlib import Path
import time

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


class NetworkDiagram:
    """Generates network diagrams"""

    def __init__(self):
        self.working_dir = Path(__file__).parent
        self.local_ip = self._get_local_ip()
        self.public_ip = self._get_public_ip()
        self.domain = self._get_domain()
        self.server_running = self._check_server()

    def _get_local_ip(self) -> str:
        """Get local LAN IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"

    def _get_public_ip(self) -> str:
        """Get public IP address"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return "Unknown"

    def _get_domain(self) -> str:
        """Get configured domain from .env"""
        env_file = self.working_dir / ".env"

        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DOMAIN='):
                        domain = line.split('=')[1].strip()
                        if domain and domain != 'localhost':
                            return domain
                    elif line.startswith('BASE_URL='):
                        url = line.split('=')[1].strip()
                        if 'localhost' not in url:
                            return url.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]

        return "Not configured"

    def _check_server(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get('http://127.0.0.1:5001', timeout=2)
            return True
        except:
            return False

    def draw_full_stack(self):
        """Draw the complete network stack diagram"""

        server_status = f"{GREEN}RUNNING{RESET}" if self.server_running else f"{RED}STOPPED{RESET}"

        diagram = f"""
{BOLD}{'=' * 100}{RESET}
{BOLD}{BLUE}SOULFRA NETWORK STACK - FULL TOPOLOGY{RESET}
{BOLD}{'=' * 100}{RESET}

{BOLD}Your Computer{RESET}
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                │
│  {BOLD}[Layer 1] Operating System{RESET}                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ {GRAY}Darwin 24.3.0 (macOS){RESET}                                                                 │  │
│  │ Network Stack: TCP/IP, Sockets, Port Binding                                           │  │
│  │ {CYAN}Connection: Python socket() → OS network layer{RESET}                                       │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ↓                                                    │
│  {BOLD}[Layer 2] Python Environment{RESET}                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Python 3.13.4                                                                            │  │
│  │ Installed: Flask 3.0.0, requests, pandas, etc.                                          │  │
│  │ {CYAN}Connection: requirements.txt → pip → Python modules{RESET}                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ↓                                                    │
│  {BOLD}[Layer 3] Flask Application{RESET}                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ File: app.py                                                                             │  │
│  │ Routes: /, /admin, /api/v1/*, /generate, etc.                                           │  │
│  │ Config: host='0.0.0.0', port=5001                                                        │  │
│  │ {CYAN}Connection: app.run() → Flask HTTP server{RESET}                                            │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ↓                                                    │
│  {BOLD}[Layer 4] HTTP Server{RESET}                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Server: Flask development server (Werkzeug)                                              │  │
│  │ Status: {server_status}                                                              │  │
│  │ Binding: 0.0.0.0:5001 (all network interfaces)                                           │  │
│  │ {CYAN}Connection: Flask → HTTP socket on 0.0.0.0:5001{RESET}                                      │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ↓                                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            ↓
{BOLD}Local Network{RESET}
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                │
│  {BOLD}[Layer 5] Network Interfaces{RESET}                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                          │  │
│  │  127.0.0.1:5001  ← Localhost (loopback)                                                 │  │
│  │  {GREEN}✓ http://localhost:5001{RESET}                                                            │  │
│  │                                                                                          │  │
│  │  {self.local_ip}:5001  ← LAN IP (local network)                                           │  │
│  │  {GREEN}✓ http://{self.local_ip}:5001{RESET}                                                        │  │
│  │                                                                                          │  │
│  │ {CYAN}Connection: host='0.0.0.0' → All network interfaces{RESET}                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            ↓
{BOLD}Router / Gateway{RESET}
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                │
│  {BOLD}[Layer 6] NAT & Port Forwarding{RESET}                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Internal: {self.local_ip}:5001                                                             │  │
│  │ External: {self.public_ip}:5001                                                      │  │
│  │                                                                                          │  │
│  │ Port Forwarding Rule:                                                                    │  │
│  │ {GRAY}WAN:5001 → {self.local_ip}:5001{RESET}                                                        │  │
│  │ {YELLOW}⚠ Configure this in your router settings{RESET}                                            │  │
│  │                                                                                          │  │
│  │ {CYAN}Connection: Router NAT → LAN IP{RESET}                                                       │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            ↓
{BOLD}Public Internet{RESET}
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                │
│  {BOLD}[Layer 7] Public IP Access{RESET}                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Public IP: {self.public_ip}                                                          │  │
│  │ URL: http://{self.public_ip}:5001                                                   │  │
│  │                                                                                          │  │
│  │ {CYAN}Connection: Public IP → Router → LAN → Server{RESET}                                         │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                            ↓
{BOLD}DNS & Domain{RESET}
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                │
│  {BOLD}[Layer 8] DNS Resolution{RESET}                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Domain: {self.domain:<68}                       │  │
│  │                                                                                          │  │
│  │ DNS Records (configure at registrar):                                                    │  │
│  │   A record:    {self.domain} → {self.public_ip}                               │  │
│  │   CNAME:       www → {self.domain}                                             │  │
│  │                                                                                          │  │
│  │ {CYAN}Connection: Domain name → DNS → Public IP{RESET}                                             │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                │
│  {BOLD}[Layer 9] Domain Access{RESET}                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ URL: http://{self.domain}                                                        │  │
│  │ HTTPS: https://{self.domain} (requires SSL certificate)                          │  │
│  │                                                                                          │  │
│  │ {CYAN}Connection: Domain → DNS → IP → Router → Server{RESET}                                       │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

{BOLD}{'=' * 100}{RESET}
{BOLD}ACCESS URLS{RESET}
{BOLD}{'=' * 100}{RESET}
"""

        if self.server_running:
            diagram += f"""
{GREEN}✓ Localhost:{RESET}     http://localhost:5001
{GREEN}✓ LAN:{RESET}           http://{self.local_ip}:5001
{YELLOW}○ Public IP:{RESET}     http://{self.public_ip}:5001 {GRAY}(requires port forwarding){RESET}
"""
            if self.domain != "Not configured":
                diagram += f"{GRAY}○ Domain:{RESET}        http://{self.domain} {GRAY}(requires DNS + port forwarding){RESET}\n"
        else:
            diagram += f"{RED}✗ Server not running{RESET}\n"
            diagram += f"{YELLOW}Start server: python3 app.py{RESET}\n"

        diagram += f"\n{BOLD}{'=' * 100}{RESET}\n"

        print(diagram)

    def draw_simple_flow(self):
        """Draw simplified request flow diagram"""

        diagram = f"""
{BOLD}{'=' * 80}{RESET}
{BOLD}{BLUE}SIMPLIFIED REQUEST FLOW{RESET}
{BOLD}{'=' * 80}{RESET}

{BOLD}User types URL{RESET}
    ↓
┌───────────────────────────────────────────────────────────────────────┐
│ {CYAN}http://{self.domain if self.domain != 'Not configured' else 'localhost:5001'}{RESET}
└───────────────────────────────────────────────────────────────────────┘
    ↓
{BOLD}[1] DNS Lookup{RESET}
    │ Domain → IP address
    │ {self.domain} → {self.public_ip}
    ↓
{BOLD}[2] Route to Public IP{RESET}
    │ Internet routing
    │ Request arrives at {self.public_ip}
    ↓
{BOLD}[3] Router Port Forwarding{RESET}
    │ {self.public_ip}:5001 → {self.local_ip}:5001
    │ NAT translation
    ↓
{BOLD}[4] Local Network{RESET}
    │ Request arrives at your computer
    │ IP: {self.local_ip}
    ↓
{BOLD}[5] Operating System{RESET}
    │ OS network stack receives packet
    │ Port 5001 → Python process
    ↓
{BOLD}[6] Flask Server{RESET}
    │ Flask receives HTTP request
    │ app.py:app.run(host='0.0.0.0', port=5001)
    ↓
{BOLD}[7] Application Logic{RESET}
    │ Routes, templates, database
    │ Generate response HTML
    ↓
{BOLD}[8] Response{RESET}
    │ HTML page sent back
    │ Same path in reverse
    ↓
┌───────────────────────────────────────────────────────────────────────┐
│ {GREEN}User sees webpage{RESET}
└───────────────────────────────────────────────────────────────────────┘

{BOLD}{'=' * 80}{RESET}
"""

        print(diagram)

    def draw_connection_points(self):
        """Draw diagram showing WHERE each connection is made"""

        diagram = f"""
{BOLD}{'=' * 80}{RESET}
{BOLD}{BLUE}CONNECTION POINTS (Where Each Layer Connects){RESET}
{BOLD}{'=' * 80}{RESET}

{BOLD}1. Python ↔ OS{RESET}
   File:  app.py
   Line:  if __name__ == "__main__":
          app.run(host='0.0.0.0', port=5001)

   {CYAN}This binds Python process to OS network stack on ALL interfaces{RESET}

{BOLD}2. Flask ↔ Network{RESET}
   File:  app.py
   Code:  @app.route('/')
          def index():
              return render_template('index.html')

   {CYAN}Flask routes map URLs to Python functions{RESET}

{BOLD}3. Server ↔ Clients{RESET}
   Config:  host='0.0.0.0'  ← CRITICAL for LAN access
            port=5001

   {CYAN}0.0.0.0 means "listen on ALL network interfaces"{RESET}
   {CYAN}127.0.0.1 would mean "localhost only" (no LAN){RESET}

{BOLD}4. Router ↔ Internet{RESET}
   Device:  Your router (192.168.1.1 typically)
   Config:  Port forwarding rule
            External: {self.public_ip}:5001
            Internal: {self.local_ip}:5001

   {CYAN}Configure this in your router's admin panel{RESET}

{BOLD}5. DNS ↔ IP{RESET}
   Provider: Your domain registrar (GoDaddy, Namecheap, etc.)
   Records:
            A      {self.domain}  →  {self.public_ip}
            CNAME  www            →  {self.domain}

   {CYAN}Configure DNS records at your registrar's control panel{RESET}

{BOLD}6. Domain ↔ User{RESET}
   File:  .env
   Config:  DOMAIN={self.domain}
            BASE_URL=http://{self.domain}

   {CYAN}This tells Soulfra what domain to use for links{RESET}

{BOLD}{'=' * 80}{RESET}
"""

        print(diagram)

    def draw_live(self, interval=5):
        """Draw diagram and update live"""

        print(f"{BOLD}Live Network Monitor{RESET}")
        print(f"Updating every {interval} seconds. Press Ctrl+C to stop.\n")

        try:
            while True:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')

                # Refresh data
                self.__init__()

                # Draw diagram
                self.draw_full_stack()

                # Wait
                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Stopped.{RESET}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Soulfra network diagrams')
    parser.add_argument('--simple', action='store_true', help='Show simplified request flow')
    parser.add_argument('--connections', action='store_true', help='Show connection points')
    parser.add_argument('--live', action='store_true', help='Live updating diagram')
    parser.add_argument('--interval', type=int, default=5, help='Update interval for live mode (seconds)')

    args = parser.parse_args()

    diagram = NetworkDiagram()

    if args.live:
        diagram.draw_live(args.interval)
    elif args.simple:
        diagram.draw_simple_flow()
    elif args.connections:
        diagram.draw_connection_points()
    else:
        diagram.draw_full_stack()


if __name__ == "__main__":
    main()
