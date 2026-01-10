#!/usr/bin/env python3
"""
Domain Deployer - Creates full domain deployment using CringeProof as template

Takes a domain from database and:
1. Creates folder structure (voice-archive/ as template)
2. Generates theme CSS from database colors
3. Creates config.js with backend URL
4. Optionally creates GitHub repo
5. Enables GitHub Pages

Usage:
    from domain_deployer import DomainDeployer

    deployer = DomainDeployer()
    result = deployer.deploy_domain('cringeproof')
"""

import os
import shutil
import sqlite3
import json
from pathlib import Path
from typing import Dict, Optional
import subprocess


class DomainDeployer:
    """Deploy domain using CringeProof template"""

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path
        self.template_dir = Path(__file__).parent / 'voice-archive'
        self.output_base = Path(__file__).parent / 'deployed-domains'
        self.output_base.mkdir(exist_ok=True)

    def get_domain_config(self, slug: str) -> Optional[Dict]:
        """Get domain configuration from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT
                id, name, slug, domain, tagline, category,
                color_primary, color_secondary, color_accent,
                emoji, brand_type, network_role
            FROM brands
            WHERE slug = ?
        """, (slug,)).fetchone()

        conn.close()

        if not row:
            return None

        return dict(row)

    def generate_theme_css(self, config: Dict) -> str:
        """Generate theme CSS from domain colors"""
        primary = config['color_primary'] or '#3498db'
        secondary = config['color_secondary'] or '#2ecc71'
        accent = config['color_accent'] or '#e74c3c'

        css = f"""/* Auto-generated theme for {config['name']} */
:root {{
    --color-primary: {primary};
    --color-secondary: {secondary};
    --color-accent: {accent};

    /* Light variants (30% lighter) */
    --color-primary-light: {self.lighten_color(primary, 0.3)};
    --color-secondary-light: {self.lighten_color(secondary, 0.3)};
    --color-accent-light: {self.lighten_color(accent, 0.3)};

    /* Dark variants (30% darker) */
    --color-primary-dark: {self.darken_color(primary, 0.3)};
    --color-secondary-dark: {self.darken_color(secondary, 0.3)};
    --color-accent-dark: {self.darken_color(accent, 0.3)};
}}

/* Apply theme to body */
body {{
    --brand-primary: var(--color-primary);
    --brand-secondary: var(--color-secondary);
    --brand-accent: var(--color-accent);
}}

/* Buttons */
.btn-primary {{
    background: var(--color-primary);
    border-color: var(--color-primary-dark);
}}

.btn-primary:hover {{
    background: var(--color-primary-light);
}}

/* Links */
a {{
    color: var(--color-accent);
}}

a:hover {{
    color: var(--color-accent-dark);
}}

/* Headers */
h1, h2, h3 {{
    color: var(--color-primary-dark);
}}
"""
        return css

    def lighten_color(self, hex_color: str, amount: float) -> str:
        """Lighten hex color by amount (0.0 to 1.0)"""
        # Simple approximation - in production use proper color library
        return hex_color  # TODO: Implement proper color manipulation

    def darken_color(self, hex_color: str, amount: float) -> str:
        """Darken hex color by amount (0.0 to 1.0)"""
        return hex_color  # TODO: Implement proper color manipulation

    def generate_config_js(self, config: Dict, backend_url: str = None) -> str:
        """Generate config.js for domain"""
        if not backend_url:
            backend_url = 'http://localhost:5001'

        js = f"""// Auto-generated config for {config['name']}
const {config['slug'].upper()}_CONFIG = {{
    API_BACKEND_URL: (() => {{
        const hostname = window.location.hostname;

        // Local testing
        if (hostname === 'localhost' || hostname === '127.0.0.1') {{
            return 'http://localhost:5001';
        }}

        // Production - your deployed backend
        return '{backend_url}';
    }})(),

    DOMAIN: '{config['slug']}',
    BRAND_NAME: '{config['name']}',
    TAGLINE: '{config['tagline'] or ''}',
    CATEGORY: '{config['category'] or ''}',
    THEME: {{
        primary: '{config['color_primary']}',
        secondary: '{config['color_secondary']}',
        accent: '{config['color_accent']}'
    }}
}};

// Export for compatibility
if (typeof window !== 'undefined') {{
    window.CRINGEPROOF_CONFIG = {config['slug'].upper()}_CONFIG;
}}
"""
        return js

    def deploy_domain(self, slug: str, backend_url: str = None) -> Dict:
        """
        Deploy domain using CringeProof template

        Returns:
        {{
            'success': True,
            'slug': 'cringeproof',
            'output_dir': '/path/to/deployed-domains/cringeproof',
            'files_created': ['index.html', 'config.js', 'theme.css', ...]
        }}
        """
        print(f"\n🚀 Deploying domain: {slug}")

        # Get domain config from database
        config = self.get_domain_config(slug)
        if not config:
            return {
                'success': False,
                'error': f'Domain {slug} not found in database'
            }

        print(f"   Name: {config['name']}")
        print(f"   Domain: {config['domain']}")
        print(f"   Colors: {config['color_primary']}, {config['color_secondary']}, {config['color_accent']}")

        # Create output directory
        output_dir = self.output_base / slug
        if output_dir.exists():
            print(f"   ⚠️  Directory exists, cleaning...")
            shutil.rmtree(output_dir)

        output_dir.mkdir(parents=True)

        # Copy template files
        print(f"   📁 Copying template from {self.template_dir}...")
        files_created = []

        # Copy all HTML files
        for html_file in self.template_dir.glob('*.html'):
            dest = output_dir / html_file.name
            shutil.copy(html_file, dest)
            files_created.append(html_file.name)

        # Copy JavaScript files
        for js_file in self.template_dir.glob('*.js'):
            if js_file.name != 'config.js':  # Don't copy config, we'll generate it
                dest = output_dir / js_file.name
                shutil.copy(js_file, dest)
                files_created.append(js_file.name)

        # Generate config.js
        print(f"   ⚙️  Generating config.js...")
        config_js = self.generate_config_js(config, backend_url)
        (output_dir / 'config.js').write_text(config_js)
        files_created.append('config.js')

        # Generate theme.css
        print(f"   🎨 Generating theme.css...")
        theme_css = self.generate_theme_css(config)
        (output_dir / 'theme.css').write_text(theme_css)
        files_created.append('theme.css')

        # Copy manifest.json if exists
        if (self.template_dir / 'manifest.json').exists():
            manifest = json.loads((self.template_dir / 'manifest.json').read_text())
            manifest['name'] = config['name']
            manifest['short_name'] = config['slug']
            manifest['description'] = config['tagline'] or config['name']
            manifest['theme_color'] = config['color_primary']
            (output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
            files_created.append('manifest.json')

        print(f"   ✅ Created {len(files_created)} files in {output_dir}")

        return {
            'success': True,
            'slug': slug,
            'domain': config['domain'],
            'name': config['name'],
            'output_dir': str(output_dir),
            'files_created': files_created
        }

    def deploy_to_github(self, slug: str, create_repo: bool = False) -> Dict:
        """
        Deploy domain to GitHub Pages

        If create_repo=True, creates new GitHub repo
        Otherwise assumes repo already exists
        """
        config = self.get_domain_config(slug)
        if not config:
            return {
                'success': False,
                'error': f'Domain {slug} not found'
            }

        repo_name = f"{slug}-site"
        output_dir = self.output_base / slug

        if not output_dir.exists():
            return {
                'success': False,
                'error': 'Domain not deployed yet. Run deploy_domain() first.'
            }

        print(f"\n📦 Deploying {slug} to GitHub Pages...")

        # Initialize git repo
        print(f"   🔧 Initializing git repo...")
        subprocess.run(['git', 'init'], cwd=output_dir, check=True)
        subprocess.run(['git', 'checkout', '-b', 'main'], cwd=output_dir, check=True)

        # Add all files
        subprocess.run(['git', 'add', '.'], cwd=output_dir, check=True)
        subprocess.run([
            'git', 'commit', '-m',
            f'Initial deployment of {config["name"]}'
        ], cwd=output_dir, check=True)

        if create_repo:
            # Create GitHub repo using gh CLI
            print(f"   🌐 Creating GitHub repo: {repo_name}...")
            try:
                subprocess.run([
                    'gh', 'repo', 'create', repo_name,
                    '--public',
                    '--description', config['tagline'] or config['name'],
                    '--source', str(output_dir),
                    '--push'
                ], check=True)

                # Enable GitHub Pages
                subprocess.run([
                    'gh', 'api',
                    f'repos/{{owner}}/{repo_name}/pages',
                    '-X', 'POST',
                    '-f', 'source[branch]=main',
                    '-f', 'source[path]=/'
                ], check=False)  # Might fail if already enabled

            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'GitHub repo creation failed: {e}'
                }

        github_pages_url = f'https://soulfra.github.io/{repo_name}'

        print(f"   ✅ Deployed to: {github_pages_url}")

        return {
            'success': True,
            'slug': slug,
            'repo_name': repo_name,
            'github_pages_url': github_pages_url,
            'local_path': str(output_dir)
        }

    def check_deployment_status(self, slug: str) -> Dict:
        """
        Check if domain has been deployed and to what state

        Returns:
        {{
            'deployed_locally': True,
            'has_git_repo': True,
            'github_pages_live': True,
            'backend_accessible': False
        }}
        """
        output_dir = self.output_base / slug

        status = {
            'slug': slug,
            'deployed_locally': output_dir.exists(),
            'has_git_repo': (output_dir / '.git').exists() if output_dir.exists() else False,
            'github_pages_live': False,  # TODO: Check with HTTP request
            'backend_accessible': False  # TODO: Ping backend
        }

        return status


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python domain_deployer.py <slug>                  # Deploy locally")
        print("  python domain_deployer.py <slug> --github         # Deploy to GitHub")
        print("  python domain_deployer.py <slug> --status         # Check status")
        sys.exit(1)

    deployer = DomainDeployer()
    slug = sys.argv[1]

    if '--status' in sys.argv:
        status = deployer.check_deployment_status(slug)
        print(json.dumps(status, indent=2))

    elif '--github' in sys.argv:
        # First deploy locally
        result = deployer.deploy_domain(slug)
        if not result['success']:
            print(f"❌ {result['error']}")
            sys.exit(1)

        # Then push to GitHub
        github_result = deployer.deploy_to_github(slug, create_repo=True)
        print(json.dumps(github_result, indent=2))

    else:
        # Just local deployment
        result = deployer.deploy_domain(slug)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
