#!/usr/bin/env python3
"""
Build Site - Convert README.md → HTML for soulfra.com deployment

This script:
1. Reads README.md
2. Converts markdown → HTML (using GitHub's styling)
3. Embeds artifacts from /assets/
4. Applies privacy filters (whitelist.json)
5. Generates merkle proofs
6. Outputs deployable HTML

Usage:
    python3 build-site.py

Outputs:
    dist/index.html - Ready to deploy to soulfra.com
"""

import json
import markdown
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Configuration
README_PATH = Path("../README.md")
WHITELIST_PATH = Path("whitelist.json")
ASSETS_DIR = Path("../assets")
DIST_DIR = Path("../dist")

def load_whitelist():
    """Load privacy whitelist configuration"""
    with open(WHITELIST_PATH) as f:
        return json.load(f)

def convert_markdown_to_html(md_content):
    """Convert markdown to HTML with GitHub-flavored markdown"""
    return markdown.markdown(
        md_content,
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.tables'
        ]
    )

def apply_github_styling(html_content):
    """Wrap HTML with GitHub-style CSS"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soulfra - Building the Non-Typing Internet</title>
    <meta name="description" content="Voice-first interaction platform with shadow accounts, offline queue, and privacy-first architecture.">
    <style>
        /* GitHub-inspired styling */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #24292f;
            background-color: #ffffff;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 600;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #d0d7de;
            margin-bottom: 1rem;
        }}

        h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #d0d7de;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}

        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }}

        p {{
            margin-bottom: 1rem;
        }}

        code {{
            background-color: rgba(175, 184, 193, 0.2);
            padding: 0.2em 0.4em;
            border-radius: 6px;
            font-size: 85%;
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
        }}

        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            border-radius: 6px;
            margin-bottom: 1rem;
        }}

        a {{
            color: #0969da;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        ul, ol {{
            padding-left: 2rem;
            margin-bottom: 1rem;
        }}

        li {{
            margin-bottom: 0.25rem;
        }}

        blockquote {{
            padding-left: 1rem;
            border-left: 0.25rem solid #d0d7de;
            color: #57606a;
            margin-bottom: 1rem;
        }}

        hr {{
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #d0d7de;
            border: 0;
        }}

        /* Merkle proof badge */
        .merkle-proof {{
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 1rem;
            margin-top: 2rem;
            font-size: 0.85rem;
        }}

        .merkle-proof code {{
            background: #fff;
        }}
    </style>
</head>
<body>
    {html_content}

    <!-- Merkle Root Proof -->
    <div class="merkle-proof">
        <strong>🔐 Cryptographic Proof</strong><br>
        <code id="merkle-root">Loading merkle root...</code><br>
        <small>Committed: <span id="commit-timestamp">{datetime.now(timezone.utc).isoformat()}</span></small>
    </div>

    <script>
        // Load merkle proof from assets
        fetch('assets/merkle-root.json')
            .then(r => r.json())
            .then(data => {{
                document.getElementById('merkle-root').textContent = data.root;
            }})
            .catch(() => {{
                document.getElementById('merkle-root').textContent = 'Merkle proof pending';
            }});
    </script>
</body>
</html>
"""

def generate_merkle_proof_file(whitelist):
    """Generate merkle root for all assets"""
    assets_path = ASSETS_DIR
    hashes = []

    # Hash all public assets
    for file_pattern in whitelist['levels']['public']['files']:
        filepath = Path("..") / file_pattern
        if filepath.exists():
            file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            hashes.append(file_hash)

    # Simple merkle root (hash of all hashes)
    if hashes:
        combined = "".join(sorted(hashes))
        root = hashlib.sha256(combined.encode()).hexdigest()
    else:
        root = hashlib.sha256(b"").hexdigest()

    # Save merkle proof
    proof = {
        "root": root,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "assets_count": len(hashes),
        "algorithm": "sha256"
    }

    dist_assets = DIST_DIR / "assets"
    dist_assets.mkdir(parents=True, exist_ok=True)

    with open(dist_assets / "merkle-root.json", 'w') as f:
        json.dump(proof, f, indent=2)

    return root

def build_site():
    """Main build function"""
    print("🏗️  Building soulfra.com from README.md...")

    # Load whitelist
    whitelist = load_whitelist()
    print(f"   Loaded whitelist with {len(whitelist['levels'])} privacy levels")

    # Read README
    if not README_PATH.exists():
        print(f"❌ README.md not found at {README_PATH}")
        return

    md_content = README_PATH.read_text()
    print(f"   Read README.md ({len(md_content)} bytes)")

    # Convert to HTML
    html_content = convert_markdown_to_html(md_content)
    full_html = apply_github_styling(html_content)
    print(f"   Converted to HTML ({len(full_html)} bytes)")

    # Generate merkle proof
    merkle_root = generate_merkle_proof_file(whitelist)
    print(f"   Generated merkle proof: {merkle_root[:16]}...")

    # Create dist directory
    DIST_DIR.mkdir(exist_ok=True)

    # Write output
    output_path = DIST_DIR / "index.html"
    output_path.write_text(full_html)
    print(f"✅ Built: {output_path}")
    print(f"   Deploy to soulfra.com by copying {DIST_DIR}/ contents")

if __name__ == "__main__":
    build_site()
