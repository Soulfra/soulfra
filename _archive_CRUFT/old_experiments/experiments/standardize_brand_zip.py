#!/usr/bin/env python3
"""
Standardize Brand ZIP Format

Ensures perfect symmetry between:
- Export (brand_theme_manager.py export)
- Submission (brand/submit upload)
- Import (brand_theme_manager.py import)

All three use the SAME ZIP structure, making the system predictable.

Standard ZIP Structure:
──────────────────────
brand-theme.zip
├── brand.yaml              # Complete brand config
│   name: CalRiven
│   slug: calriven
│   personality: Technical, analytical
│   tone: Professional
│   license_type: cc0
│   colors:
│     primary: #2196f3
│     secondary: #1976d2
│
├── ml_models/
│   ├── wordmap.json        # Vocabulary patterns
│   └── emoji_patterns.json # Emoji usage
│
├── images/
│   ├── logo.png            # Brand logo
│   └── banner.png          # Header image
│
├── stories/
│   ├── post-1.md           # Example posts
│   ├── post-2.md
│   └── post-3.md
│
└── LICENSE.txt             # Auto-generated from license_type

Usage:
    from standardize_brand_zip import validate_brand_zip, fix_brand_zip

    # Check if ZIP is valid
    is_valid, issues = validate_brand_zip('brand.zip')

    # Fix ZIP to match standard
    fixed_zip = fix_brand_zip('brand.zip')
"""

import zipfile
import json
import yaml
from pathlib import Path
from typing import Tuple, List, Optional


# License templates
LICENSE_TEMPLATES = {
    'cc0': """CC0 1.0 Universal (Public Domain Dedication)

This work has been dedicated to the public domain under the CC0 1.0 Universal license.

You can:
✅ Use for any purpose (commercial or non-commercial)
✅ Modify and adapt
✅ Distribute and publish
✅ Create derivative works
❌ No attribution required (but appreciated!)

Full license: https://creativecommons.org/publicdomain/zero/1.0/
""",

    'cc-by': """Creative Commons Attribution 4.0 International (CC BY 4.0)

You are free to:
✅ Share — copy and redistribute
✅ Adapt — remix, transform, and build upon
✅ Commercial use allowed

Under the following terms:
✅ Attribution REQUIRED — You must give appropriate credit

Full license: https://creativecommons.org/licenses/by/4.0/
""",

    'licensed': """Licensed Brand Theme

This brand theme is licensed for specific use only.

Permissions:
✅ Personal use allowed
❌ Commercial use requires license
⚠️  Modifications may be restricted
✅ Attribution required

Contact the brand owner for commercial licensing terms.
""",

    'proprietary': """Proprietary Brand Theme - All Rights Reserved

This brand theme is proprietary and protected by copyright law.

Restrictions:
❌ Cannot use without purchase/license
❌ Cannot redistribute
❌ Cannot modify
❌ All rights reserved

For licensing inquiries, contact the brand owner.
"""
}


def validate_brand_zip(zip_path: str) -> Tuple[bool, List[str]]:
    """
    Validate if ZIP matches standard brand format

    Args:
        zip_path: Path to ZIP file

    Returns:
        (is_valid, issues) where issues is list of problems found
    """
    issues = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()

            # Check 1: brand.yaml exists
            if not any('brand.yaml' in f or 'brand.yml' in f for f in files):
                issues.append("Missing brand.yaml")
            else:
                # Validate brand.yaml structure
                try:
                    brand_yaml = None
                    for f in files:
                        if 'brand.yaml' in f or 'brand.yml' in f:
                            brand_yaml = yaml.safe_load(zf.read(f))
                            break

                    required_fields = ['name', 'slug', 'personality', 'tone']
                    for field in required_fields:
                        if field not in brand_yaml:
                            issues.append(f"brand.yaml missing required field: {field}")

                    # Check license_type
                    if 'license_type' not in brand_yaml:
                        issues.append("brand.yaml missing license_type")

                except Exception as e:
                    issues.append(f"Invalid brand.yaml: {e}")

            # Check 2: ML models directory
            has_wordmap = any('wordmap.json' in f for f in files)
            has_emoji = any('emoji_patterns.json' in f for f in files)

            if not has_wordmap:
                issues.append("Missing ml_models/wordmap.json")
            if not has_emoji:
                issues.append("Missing ml_models/emoji_patterns.json")

            # Check 3: Stories directory (at least 1 post)
            story_files = [f for f in files if f.startswith('stories/') and f.endswith('.md')]
            if len(story_files) < 1:
                issues.append("Missing stories/ directory or no .md files (need at least 1)")

            # Check 4: LICENSE.txt
            if 'LICENSE.txt' not in files:
                issues.append("Missing LICENSE.txt")

            # Check 5: Images (recommended but not required)
            image_files = [f for f in files if f.startswith('images/')]
            if len(image_files) == 0:
                issues.append("WARNING: No images found (recommended: logo.png, banner.png)")

    except zipfile.BadZipFile:
        issues.append("File is not a valid ZIP archive")
    except Exception as e:
        issues.append(f"Error reading ZIP: {e}")

    is_valid = len([i for i in issues if not i.startswith('WARNING')]) == 0
    return is_valid, issues


def generate_license_txt(license_type: str, brand_name: str = "") -> str:
    """Generate LICENSE.txt content from license type"""
    template = LICENSE_TEMPLATES.get(license_type, LICENSE_TEMPLATES['cc0'])

    header = f"# {brand_name} Brand Theme License\n\n" if brand_name else ""
    return header + template


def fix_brand_zip(zip_path: str, output_path: Optional[str] = None) -> str:
    """
    Fix brand ZIP to match standard format

    Args:
        zip_path: Path to input ZIP
        output_path: Path to output ZIP (default: {input}_fixed.zip)

    Returns:
        Path to fixed ZIP file
    """
    if output_path is None:
        output_path = str(Path(zip_path).with_stem(Path(zip_path).stem + '_fixed'))

    print(f"🔧 Fixing brand ZIP: {Path(zip_path).name}")
    print()

    with zipfile.ZipFile(zip_path, 'r') as zf_in:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:

            # Copy all existing files
            for item in zf_in.namelist():
                zf_out.writestr(item, zf_in.read(item))
                print(f"  ✅ Copied: {item}")

            # Load brand.yaml to check for missing fields
            brand_yaml = None
            for f in zf_in.namelist():
                if 'brand.yaml' in f or 'brand.yml' in f:
                    brand_yaml = yaml.safe_load(zf_in.read(f))
                    break

            if brand_yaml:
                # Add missing LICENSE.txt if needed
                if 'LICENSE.txt' not in zf_in.namelist():
                    license_type = brand_yaml.get('license_type', 'cc0')
                    brand_name = brand_yaml.get('name', '')
                    license_content = generate_license_txt(license_type, brand_name)
                    zf_out.writestr('LICENSE.txt', license_content)
                    print(f"  ✅ Added: LICENSE.txt ({license_type})")

                # Add missing license_type to brand.yaml if needed
                if 'license_type' not in brand_yaml:
                    brand_yaml['license_type'] = 'cc0'
                    zf_out.writestr('brand.yaml', yaml.dump(brand_yaml, default_flow_style=False))
                    print(f"  ✅ Updated: brand.yaml (added license_type)")

    print()
    print(f"✅ Fixed ZIP created: {output_path}")

    return output_path


def create_brand_zip_from_dict(brand_data: dict, output_path: str) -> str:
    """
    Create standard brand ZIP from dictionary

    Args:
        brand_data: Dict with keys: name, slug, personality, tone, license_type,
                    wordmap, emoji_patterns, stories, images
        output_path: Path to output ZIP file

    Returns:
        Path to created ZIP file
    """
    print(f"📦 Creating standard brand ZIP: {brand_data.get('name', 'Unknown')}")
    print()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:

        # 1. brand.yaml
        brand_yaml = {
            'name': brand_data['name'],
            'slug': brand_data['slug'],
            'personality': brand_data.get('personality', ''),
            'tone': brand_data.get('tone', ''),
            'license_type': brand_data.get('license_type', 'cc0'),
            'colors': brand_data.get('colors', {
                'primary': '#667eea',
                'secondary': '#764ba2'
            })
        }
        zf.writestr('brand.yaml', yaml.dump(brand_yaml, default_flow_style=False))
        print("  ✅ Added brand.yaml")

        # 2. ML models
        if 'wordmap' in brand_data:
            zf.writestr('ml_models/wordmap.json', json.dumps(brand_data['wordmap'], indent=2))
            print("  ✅ Added ml_models/wordmap.json")

        if 'emoji_patterns' in brand_data:
            zf.writestr('ml_models/emoji_patterns.json', json.dumps(brand_data['emoji_patterns'], indent=2))
            print("  ✅ Added ml_models/emoji_patterns.json")

        # 3. Stories
        stories = brand_data.get('stories', [])
        for i, story in enumerate(stories, 1):
            zf.writestr(f'stories/post-{i}.md', story)
        print(f"  ✅ Added {len(stories)} stories")

        # 4. Images
        images = brand_data.get('images', {})
        for img_name, img_data in images.items():
            zf.writestr(f'images/{img_name}', img_data)
        print(f"  ✅ Added {len(images)} images")

        # 5. LICENSE.txt
        license_txt = generate_license_txt(
            brand_data.get('license_type', 'cc0'),
            brand_data.get('name', '')
        )
        zf.writestr('LICENSE.txt', license_txt)
        print("  ✅ Added LICENSE.txt")

    print()
    print(f"✅ Standard brand ZIP created: {output_path}")

    return output_path


def main():
    """Test validation and fixing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 standardize_brand_zip.py validate <zip_file>")
        print("  python3 standardize_brand_zip.py fix <zip_file>")
        return

    command = sys.argv[1]

    if command == 'validate':
        if len(sys.argv) < 3:
            print("Error: Missing ZIP file path")
            return

        zip_path = sys.argv[2]
        is_valid, issues = validate_brand_zip(zip_path)

        print("=" * 70)
        print("🔍 BRAND ZIP VALIDATION")
        print("=" * 70)
        print()
        print(f"File: {zip_path}")
        print()

        if is_valid:
            print("✅ ZIP file is valid!")
        else:
            print("❌ ZIP file has issues:")
            for issue in issues:
                if issue.startswith('WARNING'):
                    print(f"  ⚠️  {issue}")
                else:
                    print(f"  ❌ {issue}")
        print()

    elif command == 'fix':
        if len(sys.argv) < 3:
            print("Error: Missing ZIP file path")
            return

        zip_path = sys.argv[2]
        fixed_path = fix_brand_zip(zip_path)

        print()
        print("Validate the fixed ZIP:")
        print(f"  python3 standardize_brand_zip.py validate {fixed_path}")
        print()


if __name__ == '__main__':
    main()
