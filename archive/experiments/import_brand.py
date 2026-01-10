#!/usr/bin/env python3
"""
Brand Import for Soulfra Simple

Usage:
    python import_brand.py <brand-export.json>
    python import_brand.py <brand-export.json> --validate-only
    python import_brand.py <brand-export.json> --sandbox

Purpose:
    - Import brand definitions from roommate-chat
    - Update newsletter templates with brand context
    - Add brand metadata to build output
    - Secure: signature verification, schema validation, string sanitization

Security:
    - JSON schema validation
    - Signature verification (SHA-256 HMAC)
    - No code execution
    - Sandbox mode for testing
"""

import argparse
import hashlib
import hmac
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# Secret for signature verification (must match export secret)
EXPORT_SECRET = 'calriven-brand-export-v1'  # In production, use env var

# Paths
TEMPLATES_DIR = Path('templates')
BRAND_CONFIG_FILE = Path('brand_config.json')


def main():
    parser = argparse.ArgumentParser(description='Import brand data into Soulfra Simple')
    parser.add_argument('brand_file', type=str, help='Path to brand export JSON file')
    parser.add_argument('--validate-only', action='store_true', help='Validate without applying changes')
    parser.add_argument('--sandbox', action='store_true', help='Test mode (no actual changes)')

    args = parser.parse_args()

    try:
        # Step 1: Load brand export file
        print(f"📦 Loading brand export: {args.brand_file}")
        with open(args.brand_file, 'r', encoding='utf-8') as f:
            brand_data = json.load(f)

        # Step 2: Validate schema
        print("✅ Validating JSON schema...")
        validate_schema(brand_data)

        # Step 3: Verify signature
        print("🔐 Verifying signature...")
        verify_signature(brand_data)

        # Step 4: Sanitize strings
        print("🧹 Sanitizing data...")
        sanitized = sanitize_import_data(brand_data)

        brand_name = sanitized['brand']
        print(f"✅ Brand: {brand_name}")
        print(f"   Version: {sanitized['version']}")
        print(f"   Exported: {sanitized['exported_at']}")

        if args.validate_only:
            print("✅ Validation successful! (no changes made)")
            return 0

        # Step 5: Apply import
        if args.sandbox:
            print("\n🧪 SANDBOX MODE - Showing what would be changed:\n")
            show_changes(sanitized)
            print("\nNo actual changes made. Run without --sandbox to apply.")
            return 0

        # Step 6: Apply changes
        print("\n📝 Applying brand configuration...")
        apply_brand_config(sanitized)

        print("\n✅ Brand import complete!")
        print(f"\nNext steps:")
        print(f"  1. Review templates/base.html for brand styling")
        print(f"  2. Run: python build.py")
        print(f"  3. Check docs/index.html for brand metadata")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def validate_schema(data):
    """Validate JSON schema"""
    errors = []

    # Required top-level fields
    if 'brand' not in data or not isinstance(data['brand'], str):
        errors.append('Missing or invalid "brand" field')

    if 'version' not in data or not isinstance(data['version'], str):
        errors.append('Missing or invalid "version" field')

    if 'exported_at' not in data or not isinstance(data['exported_at'], str):
        errors.append('Missing or invalid "exported_at" field')

    if 'signature' not in data or not isinstance(data['signature'], str):
        errors.append('Missing or invalid "signature" field')

    if 'data' not in data or not isinstance(data['data'], dict):
        errors.append('Missing or invalid "data" field')

    # Validate data structure
    if 'data' in data:
        if 'name' not in data['data'] or not isinstance(data['data']['name'], str):
            errors.append('Missing or invalid "data.name" field')

        if 'tagline' not in data['data'] or not isinstance(data['data']['tagline'], str):
            errors.append('Missing or invalid "data.tagline" field')

        if 'personality' not in data['data'] or not isinstance(data['data']['personality'], dict):
            errors.append('Missing or invalid "data.personality" field')

    if errors:
        raise ValueError(f"Schema validation failed: {', '.join(errors)}")


def verify_signature(data):
    """Verify HMAC signature"""
    # Extract signature
    provided_signature = data.get('signature', '')

    if not provided_signature.startswith('sha256:'):
        raise ValueError('Invalid signature format (expected sha256:...)')

    provided_hash = provided_signature.replace('sha256:', '')

    # Calculate expected signature
    canonical = json.dumps({
        'brand': data['brand'],
        'version': data['version'],
        'exported_at': data['exported_at'],
        'data': data['data']
    }, separators=(',', ':'))

    expected_hmac = hmac.new(
        EXPORT_SECRET.encode('utf-8'),
        canonical.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(provided_hash, expected_hmac):
        raise ValueError('Signature verification failed - export may be corrupted or tampered with')


def sanitize_import_data(data):
    """Sanitize import data (prevent injection)"""
    return {
        'brand': sanitize_string(data['brand']),
        'version': sanitize_string(data['version']),
        'exported_at': sanitize_string(data['exported_at']),
        'signature': sanitize_string(data['signature']),
        'data': {
            'name': sanitize_string(data['data']['name']),
            'tagline': sanitize_string(data['data']['tagline']),
            'category': sanitize_string(data['data'].get('category', '')),
            'tier': sanitize_string(data['data'].get('tier', '')),
            'personality': {
                'tone': sanitize_string(data['data']['personality'].get('tone', '')),
                'traits': [sanitize_string(t) for t in data['data']['personality'].get('traits', [])],
                'ai_style': sanitize_string(data['data']['personality'].get('ai_style', ''))
            },
            'colors': {
                'primary': sanitize_color(data['data'].get('colors', {}).get('primary', '#000000')),
                'secondary': sanitize_color(data['data'].get('colors', {}).get('secondary', '#ffffff')),
                'accent': sanitize_color(data['data'].get('colors', {}).get('accent', '#666666'))
            },
            'generated_content': data['data'].get('generated_content', None)
        }
    }


def sanitize_string(value):
    """Remove dangerous characters"""
    if not isinstance(value, str):
        return ''

    # Remove null bytes, control chars, script tags
    value = re.sub(r'\x00', '', value)
    value = re.sub(r'[\x00-\x1F\x7F]', '', value)
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE)
    value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE)

    return value.strip()


def sanitize_color(color):
    """Validate hex color"""
    if not isinstance(color, str):
        return '#000000'

    # Only allow hex colors
    match = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', color, re.IGNORECASE)
    return match.group(0) if match else '#000000'


def show_changes(brand_data):
    """Show what would be changed in sandbox mode"""
    data = brand_data['data']

    print(f"Brand: {data['name']}")
    print(f"Tagline: {data['tagline']}")
    print(f"Colors:")
    print(f"  Primary: {data['colors']['primary']}")
    print(f"  Secondary: {data['colors']['secondary']}")
    print(f"  Accent: {data['colors']['accent']}")
    print(f"\nPersonality:")
    print(f"  Tone: {data['personality']['tone']}")
    print(f"  Traits: {', '.join(data['personality']['traits'])}")
    print(f"\nWould update:")
    print(f"  - {BRAND_CONFIG_FILE}")
    print(f"  - {TEMPLATES_DIR / 'base.html'} (add brand metadata)")


def apply_brand_config(brand_data):
    """Apply brand configuration"""
    # Step 1: Save brand config to JSON file
    print(f"💾 Saving brand config to {BRAND_CONFIG_FILE}...")
    with open(BRAND_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(brand_data, f, indent=2)

    # Step 2: Update base.html template with brand metadata
    print(f"📝 Updating {TEMPLATES_DIR / 'base.html'}...")
    update_base_template(brand_data)

    print("✅ Configuration applied")


def update_base_template(brand_data):
    """Update base.html with brand metadata and CSS variables"""
    base_template = TEMPLATES_DIR / 'base.html'

    if not base_template.exists():
        print(f"⚠️  Warning: {base_template} not found, skipping template update")
        return

    with open(base_template, 'r', encoding='utf-8') as f:
        content = f.read()

    data = brand_data['data']

    # Build brand metadata
    brand_meta = f'''  <!-- Brand Metadata (imported from CalRiven) -->
  <meta name="brand" content="{data['name']}">
  <meta name="brand-tagline" content="{data['tagline']}">
  <meta name="brand-category" content="{data['category']}">
  <meta name="generator" content="CalRiven Brand System">
'''

    # Build brand CSS variables
    brand_css = f'''  <!-- Brand Styling -->
  <style>
    :root {{
      --brand-primary: {data['colors']['primary']};
      --brand-secondary: {data['colors']['secondary']};
      --brand-accent: {data['colors']['accent']};
    }}
  </style>
'''

    # Insert after <head> tag if not already present
    if '<!-- Brand Metadata' not in content:
        content = content.replace('<head>', f'<head>\n{brand_meta}')

    if '<!-- Brand Styling -->' not in content:
        content = content.replace('</head>', f'{brand_css}</head>')

    # Write back
    with open(base_template, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    sys.exit(main())
