#!/usr/bin/env python3
"""
Password Protection Generator

Creates Shopify-style password gates for static pages.

Usage:
    python3 password_protect.py --password mypass123 --url /tools/debug.html

Generates:
    - output/soulfra/password-gate.html (the gate page)
    - SHA-256 hash of password (stored in page)
    - Session-based unlock (no cookies)
"""

import hashlib
import sys
from pathlib import Path
from jinja2 import Template


def hash_password(password: str) -> str:
    """Generate SHA-256 hash of password"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_password_gate(password: str, protected_url: str, output_path: Path):
    """
    Create password-protected gate page

    Args:
        password: The password (will be hashed)
        protected_url: URL to redirect to after successful unlock
        output_path: Where to save the gate HTML
    """

    # Read template
    template_path = Path(__file__).parent / 'templates' / 'password-gate.html'

    with open(template_path) as f:
        template = Template(f.read())

    # Generate hash
    password_hash = hash_password(password)

    # Render template
    html = template.render(
        password_hash=password_hash,
        protected_url=protected_url
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ Password gate created: {output_path}")
    print(f"🔑 Password: {password}")
    print(f"🔒 Protected URL: {protected_url}")
    print(f"📝 Password hash: {password_hash}")


def protect_debug_tools(password: str):
    """
    Protect all debug tools with a password gate

    Creates a password-gate.html that unlocks:
    - /debug.html
    - /tools/debug/
    - /tools/brand/
    - /tools/ccna/
    """

    output_dir = Path('output/soulfra')

    # Create main gate
    create_password_gate(
        password=password,
        protected_url='/debug.html',
        output_path=output_dir / 'admin.html'
    )

    # Create protected check script
    unlock_check_js = f'''
// Password protection check
// Place this at the top of any protected page

(function() {{
    const PASSWORD_HASH = '{hash_password(password)}';
    const UNLOCK_KEY = 'soulfra_unlocked';

    // Check if unlocked
    if (sessionStorage.getItem(UNLOCK_KEY) !== PASSWORD_HASH) {{
        // Not unlocked - redirect to gate
        window.location.href = '/admin.html';
    }}
}})();
'''

    # Save unlock check script
    script_path = output_dir / 'unlock-check.js'
    with open(script_path, 'w') as f:
        f.write(unlock_check_js)

    print(f"\n📄 Unlock check script: {script_path}")
    print("\nTo protect a page, add this to the <head>:")
    print('<script src="/unlock-check.js"></script>')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create password-protected pages')
    parser.add_argument('--password', required=True, help='Password for protection')
    parser.add_argument('--url', default='/debug.html', help='URL to protect')
    parser.add_argument('--output', default='output/soulfra/admin.html', help='Output path')

    args = parser.parse_args()

    if args.url == '/debug.html':
        # Protect all debug tools
        protect_debug_tools(args.password)
    else:
        # Protect single page
        create_password_gate(
            password=args.password,
            protected_url=args.url,
            output_path=Path(args.output)
        )
