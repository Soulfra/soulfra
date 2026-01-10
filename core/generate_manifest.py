#!/usr/bin/env python3
"""
System Manifest Generator

Scans entire Soulfra system and generates manifest files:
- manifest.json (JSON format for programmatic access)
- soulfra.plist (XML format like Apple's Info.plist)

This becomes the single source of truth for:
- All routes
- All tools/scripts
- All domains
- All database tables
- Service status
- File inventory

Usage:
    python3 generate_manifest.py
    python3 generate_manifest.py --output custom.json
"""

import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re
import csv


class ManifestGenerator:
    """Generate system manifest by scanning all components"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.manifest = {
            'metadata': {},
            'routes': [],
            'tools': [],
            'domains': [],
            'databases': {},
            'services': {},
            'files': {},
            'documentation': []
        }

    def generate(self) -> Dict[str, Any]:
        """Generate complete manifest"""
        print("🔍 Scanning Soulfra system...")

        self.scan_metadata()
        self.scan_routes()
        self.scan_tools()
        self.scan_domains()
        self.scan_databases()
        self.scan_services()
        self.scan_files()
        self.scan_documentation()

        print("✅ Manifest generated!")
        return self.manifest

    def scan_metadata(self):
        """Scan system metadata"""
        print("  📝 Scanning metadata...")

        self.manifest['metadata'] = {
            'name': 'Soulfra',
            'version': '1.0.0',
            'description': 'AI-powered multi-domain development platform',
            'generated_at': datetime.now().isoformat(),
            'root_dir': str(self.root_dir.absolute()),
            'platform': sys.platform,
            'python_version': sys.version.split()[0]
        }

    def scan_routes(self):
        """Scan all Flask routes from app.py"""
        print("  🛣️  Scanning routes...")

        app_file = self.root_dir / 'app.py'
        if not app_file.exists():
            return

        with open(app_file, 'r') as f:
            content = f.read()

        # Find all @app.route decorators
        route_pattern = r"@app\.route\('([^']+)'(?:,\s*methods=\[([^\]]+)\])?\)"
        routes = re.finditer(route_pattern, content)

        for match in routes:
            path = match.group(1)
            methods = match.group(2) if match.group(2) else 'GET'
            methods = [m.strip().replace("'", "").replace('"', '') for m in methods.split(',')]

            self.manifest['routes'].append({
                'path': path,
                'methods': methods,
                'file': 'app.py'
            })

        # Also scan route files (e.g., docs_routes.py)
        for route_file in self.root_dir.glob('*_routes.py'):
            with open(route_file, 'r') as f:
                content = f.read()

            routes = re.finditer(route_pattern, content)
            for match in routes:
                path = match.group(1)
                methods = match.group(2) if match.group(2) else 'GET'
                methods = [m.strip().replace("'", "").replace('"', '') for m in methods.split(',')] if methods else ['GET']

                self.manifest['routes'].append({
                    'path': path,
                    'methods': methods,
                    'file': route_file.name
                })

        print(f"     Found {len(self.manifest['routes'])} routes")

    def scan_tools(self):
        """Scan all Python tools/scripts"""
        print("  🔧 Scanning tools...")

        for py_file in self.root_dir.glob('*.py'):
            # Skip test files, __pycache__, etc.
            if py_file.name.startswith('test_') or py_file.name.startswith('__'):
                continue

            # Check if it's executable
            is_executable = os.access(py_file, os.X_OK)

            # Try to extract docstring
            doc = None
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    # Look for module docstring
                    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring_match:
                        doc = docstring_match.group(1).strip().split('\n')[0]  # First line only
            except:
                pass

            self.manifest['tools'].append({
                'name': py_file.stem,
                'file': py_file.name,
                'executable': is_executable,
                'description': doc or 'No description'
            })

        print(f"     Found {len(self.manifest['tools'])} tools")

    def scan_domains(self):
        """Scan domains from domains-master.csv and domains.txt"""
        print("  🌐 Scanning domains...")

        # Read domains-master.csv
        csv_file = self.root_dir / 'domains-master.csv'
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip empty rows or header templates
                    if not row.get('domain') or row['domain'].startswith('#'):
                        continue

                    self.manifest['domains'].append({
                        'name': row.get('name', ''),
                        'domain': row.get('domain', ''),
                        'category': row.get('category', ''),
                        'tier': row.get('tier', ''),
                        'emoji': row.get('emoji', ''),
                        'brand_type': row.get('brand_type', ''),
                        'tagline': row.get('tagline', ''),
                        'target_audience': row.get('target_audience', ''),
                        'purpose': row.get('purpose', ''),
                        'ssl_enabled': row.get('ssl_enabled', 'false') == 'true',
                        'deployed': row.get('deployed', 'false') == 'true',
                        'source': 'domains-master.csv'
                    })

        # Also read domains.txt
        txt_file = self.root_dir / 'domains.txt'
        if txt_file.exists():
            with open(txt_file, 'r') as f:
                for line in f:
                    # Skip comments
                    if line.startswith('#') or not line.strip():
                        continue

                    # Format: domain | category | tagline
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 1:
                        domain = parts[0]
                        # Check if already in list from CSV
                        if not any(d['domain'] == domain for d in self.manifest['domains']):
                            self.manifest['domains'].append({
                                'domain': domain,
                                'category': parts[1] if len(parts) > 1 else '',
                                'tagline': parts[2] if len(parts) > 2 else '',
                                'source': 'domains.txt'
                            })

        print(f"     Found {len(self.manifest['domains'])} domains")

    def scan_databases(self):
        """Scan SQLite databases and their schemas"""
        print("  🗄️  Scanning databases...")

        for db_file in self.root_dir.glob('*.db'):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]

                # Get row counts for each table
                table_info = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    table_info[table] = {
                        'row_count': count
                    }

                self.manifest['databases'][db_file.name] = {
                    'file': db_file.name,
                    'size_bytes': db_file.stat().st_size,
                    'tables': table_info,
                    'total_tables': len(tables)
                }

                conn.close()
            except Exception as e:
                print(f"     ⚠️  Error scanning {db_file.name}: {e}")

        print(f"     Found {len(self.manifest['databases'])} databases")

    def scan_services(self):
        """Check status of services (Ollama, Flask, etc.)"""
        print("  🚀 Checking services...")

        services = {}

        # Check Ollama
        try:
            import urllib.request
            req = urllib.request.Request('http://localhost:11434/api/tags')
            with urllib.request.urlopen(req, timeout=2) as response:
                services['ollama'] = {
                    'status': 'running',
                    'port': 11434,
                    'url': 'http://localhost:11434'
                }
        except:
            services['ollama'] = {
                'status': 'stopped',
                'port': 11434
            }

        # Check Flask (main app)
        try:
            import urllib.request
            req = urllib.request.Request('http://localhost:5001/')
            with urllib.request.urlopen(req, timeout=2) as response:
                services['flask_main'] = {
                    'status': 'running',
                    'port': 5001,
                    'url': 'http://localhost:5001'
                }
        except:
            services['flask_main'] = {
                'status': 'stopped',
                'port': 5001
            }

        self.manifest['services'] = services
        running_count = sum(1 for s in services.values() if s['status'] == 'running')
        print(f"     {running_count}/{len(services)} services running")

    def scan_files(self):
        """Scan file inventory"""
        print("  📁 Scanning files...")

        file_counts = {
            'markdown': 0,
            'python': 0,
            'html': 0,
            'css': 0,
            'javascript': 0,
            'json': 0,
            'total': 0
        }

        for pattern, key in [('*.md', 'markdown'), ('*.py', 'python'),
                              ('*.html', 'html'), ('*.css', 'css'),
                              ('*.js', 'javascript'), ('*.json', 'json')]:
            count = len(list(self.root_dir.glob(pattern)))
            file_counts[key] = count
            file_counts['total'] += count

        self.manifest['files'] = file_counts
        print(f"     Found {file_counts['total']} files")

    def scan_documentation(self):
        """Scan documentation files"""
        print("  📚 Scanning documentation...")

        docs = []
        for md_file in self.root_dir.glob('*.md'):
            # Skip README
            if md_file.name.lower() == 'readme.md':
                continue

            # Check if it's important (starred)
            is_starred = False
            try:
                with open(md_file, 'r') as f:
                    content = f.read()
                    is_starred = '✨' in content or 'START' in md_file.name.upper()
            except:
                pass

            docs.append({
                'file': md_file.name,
                'size_bytes': md_file.stat().st_size,
                'starred': is_starred
            })

        self.manifest['documentation'] = docs
        starred_count = sum(1 for d in docs if d['starred'])
        print(f"     Found {len(docs)} docs ({starred_count} starred)")

    def save_json(self, output_file: str = 'manifest.json'):
        """Save manifest as JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        print(f"\n💾 Saved JSON manifest: {output_file}")

    def save_plist(self, output_file: str = 'soulfra.plist'):
        """Save manifest as XML plist (like Apple's Info.plist)"""
        xml = self._dict_to_plist(self.manifest)

        full_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
{xml}
</plist>'''

        with open(output_file, 'w') as f:
            f.write(full_xml)
        print(f"💾 Saved plist manifest: {output_file}")

    def _dict_to_plist(self, obj, indent=0):
        """Convert Python dict to plist XML"""
        ind = "  " * indent

        if isinstance(obj, dict):
            xml = f"{ind}<dict>\n"
            for key, value in obj.items():
                xml += f"{ind}  <key>{key}</key>\n"
                xml += self._dict_to_plist(value, indent + 1)
            xml += f"{ind}</dict>\n"
            return xml

        elif isinstance(obj, list):
            xml = f"{ind}<array>\n"
            for item in obj:
                xml += self._dict_to_plist(item, indent + 1)
            xml += f"{ind}</array>\n"
            return xml

        elif isinstance(obj, bool):
            return f"{ind}<{'true' if obj else 'false'}/>\n"

        elif isinstance(obj, int):
            return f"{ind}<integer>{obj}</integer>\n"

        elif isinstance(obj, float):
            return f"{ind}<real>{obj}</real>\n"

        else:  # string
            return f"{ind}<string>{obj}</string>\n"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Soulfra system manifest")
    parser.add_argument('--output', '-o', type=str, help='Output JSON file (default: manifest.json)')
    parser.add_argument('--no-plist', action='store_true', help='Skip plist generation')

    args = parser.parse_args()

    # Generate manifest
    generator = ManifestGenerator()
    manifest = generator.generate()

    # Save JSON
    json_file = args.output or 'manifest.json'
    generator.save_json(json_file)

    # Save plist
    if not args.no_plist:
        generator.save_plist('soulfra.plist')

    print("\n✅ Done! Use these files:")
    print(f"   - {json_file} (for programmatic access)")
    if not args.no_plist:
        print("   - soulfra.plist (for Apple-style documentation)")


if __name__ == '__main__':
    main()
