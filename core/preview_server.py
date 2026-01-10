#!/usr/bin/env python3
"""
Local Preview Server for Domain Repos
Serves each domain on a different port so you can preview before pushing to GitHub

Usage:
    python3 preview_server.py

Then visit:
    http://192.168.1.87:8001  → soulfra
    http://192.168.1.87:8002  → hollowtown-site
    http://192.168.1.87:8003  → oofbox-site
    ...

Works on:
    - Laptop browser
    - iPhone Safari (same WiFi network)
    - No internet needed
"""

from flask import Flask, send_from_directory, jsonify
from pathlib import Path
import subprocess
import socket

class DomainPreviewServer:
    def __init__(self, github_repos_path=None):
        if github_repos_path is None:
            github_repos_path = Path(__file__).parent.parent / 'github-repos'

        self.github_repos_path = Path(github_repos_path)
        self.apps = {}
        self.port_mapping = {}

    def discover_domains(self):
        """Find all domain repos in github-repos/"""
        domains = []

        if not self.github_repos_path.exists():
            print(f"❌ github-repos not found at: {self.github_repos_path}")
            return domains

        for repo_dir in self.github_repos_path.iterdir():
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                index_file = repo_dir / 'index.html'
                if index_file.exists():
                    domains.append({
                        'name': repo_dir.name,
                        'path': repo_dir,
                        'index': index_file
                    })

        return domains

    def create_app_for_domain(self, domain_name, domain_path):
        """Create a Flask app that serves a single domain"""
        app = Flask(domain_name)

        @app.route('/')
        def index():
            return send_from_directory(domain_path, 'index.html')

        @app.route('/<path:filename>')
        def serve_file(filename):
            return send_from_directory(domain_path, filename)

        @app.route('/post/<path:filename>')
        def serve_post(filename):
            return send_from_directory(domain_path / 'post', filename)

        @app.errorhandler(404)
        def not_found(e):
            return f"""
            <h1>404 - File Not Found</h1>
            <p>Looking for: {e}</p>
            <p>Domain: {domain_name}</p>
            <p><a href="/">Back to home</a></p>
            """, 404

        return app

    def start_preview_servers(self, start_port=8001):
        """Start preview servers for all domains"""
        domains = self.discover_domains()

        if not domains:
            print("❌ No domains found with index.html files")
            return

        print(f"\n{'='*60}")
        print(f"🌐 LOCAL PREVIEW SERVER")
        print(f"{'='*60}\n")

        # Get local IP
        local_ip = self.get_local_ip()

        print(f"📱 Access from laptop OR iPhone (same WiFi):\n")

        current_port = start_port
        for domain in domains:
            app = self.create_app_for_domain(domain['name'], domain['path'])
            self.apps[domain['name']] = app
            self.port_mapping[domain['name']] = current_port

            print(f"   {domain['name']:20s} → http://{local_ip}:{current_port}")

            # Start server in background thread
            from threading import Thread
            thread = Thread(target=app.run, kwargs={
                'host': '0.0.0.0',  # Accessible from network
                'port': current_port,
                'debug': False,
                'use_reloader': False
            })
            thread.daemon = True
            thread.start()

            current_port += 1

        print(f"\n{'='*60}")
        print(f"✅ All preview servers running!")
        print(f"{'='*60}\n")
        print("💡 Tips:")
        print("   - On iPhone: Open Safari, type the URL")
        print("   - Changes refresh on page reload")
        print("   - Press Ctrl+C to stop all servers\n")

        # Keep main thread alive
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopping preview servers...")

    def get_local_ip(self):
        """Get local network IP address"""
        try:
            # Create a socket to find local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "localhost"


def main():
    server = DomainPreviewServer()
    server.start_preview_servers()


if __name__ == '__main__':
    main()
