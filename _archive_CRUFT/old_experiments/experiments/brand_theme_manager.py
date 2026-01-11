#!/usr/bin/env python3
"""
Brand Theme Manager

Export and import brand themes as ZIP packages.
Themes can be downloaded, shared, and imported into any Soulfra instance.

Usage:
    from brand_theme_manager import BrandThemeManager

    manager = BrandThemeManager()

    # Export brand as ZIP
    zip_path = manager.export_brand('ocean-dreams')

    # Import brand from ZIP
    brand_id = manager.import_brand('ocean-dreams.zip')
"""

import zipfile
import json
import yaml
import io
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from database import get_db


class BrandThemeManager:
    """Manage brand theme export/import"""

    def __init__(self):
        """Initialize theme manager"""
        self.project_root = Path(__file__).parent.parent
        print('🎨 Brand Theme Manager initialized')

    def export_brand(self, brand_slug: str, output_dir: str = None) -> Optional[str]:
        """
        Export brand as ZIP theme package

        Args:
            brand_slug: Brand slug (e.g., 'ocean-dreams')
            output_dir: Output directory (default: soulfra-simple/exports/)

        Returns:
            Path to ZIP file, or None if brand not found
        """
        db = get_db()

        # Get brand from database
        brand_row = db.execute('''
            SELECT * FROM brands WHERE slug = ?
        ''', (brand_slug,)).fetchone()

        if not brand_row:
            print(f"❌ Brand '{brand_slug}' not found")
            return None

        brand = dict(brand_row)

        # Parse config JSON
        brand_config = json.loads(brand['config_json']) if brand['config_json'] else {}

        print(f"\n📦 Exporting brand: {brand['name']}")

        # Create output directory
        if output_dir is None:
            output_dir = Path(__file__).parent / 'exports'
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create ZIP file
        zip_filename = f"{brand_slug}-theme.zip"
        zip_path = output_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Add brand config (YAML) - STANDARDIZED FORMAT
            # Get license type from database
            license_row = db.execute('''
                SELECT license_type FROM brand_licenses WHERE brand_id = ? LIMIT 1
            ''', (brand['id'],)).fetchone()
            license_type = license_row['license_type'] if license_row else 'cc0'

            standardized_config = {
                'name': brand['name'],
                'slug': brand['slug'],
                'personality': brand['personality'],
                'tone': brand['tone'],
                'license_type': license_type,
                'colors': brand_config.get('colors', {
                    'primary': '#667eea',
                    'secondary': '#764ba2'
                })
            }
            # Add other fields from config if present
            for key in ['target_audience', 'story_theme', 'emoji', 'class', 'tier']:
                if key in brand_config:
                    standardized_config[key] = brand_config[key]

            config_yaml = yaml.dump(standardized_config, default_flow_style=False)
            zipf.writestr('brand.yaml', config_yaml)
            print(f"  ✅ Added brand.yaml (license: {license_type})")

            # 2. Add brand metadata (JSON)
            metadata = {
                'name': brand['name'],
                'slug': brand['slug'],
                'personality': brand['personality'],
                'tone': brand['tone'],
                'target_audience': brand['target_audience'],
                'story_theme': brand['story_theme'],
                'exported_at': datetime.now().isoformat(),
                'exported_from': 'soulfra-simple'
            }
            zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
            print(f"  ✅ Added metadata.json")

            # 3. Add images from database
            images_rows = db.execute('''
                SELECT hash, data, mime_type, metadata FROM images
                WHERE json_extract(metadata, '$.brand_id') = ?
            ''', (brand['id'],)).fetchall()

            images_count = 0
            for img in images_rows:
                img_metadata = json.loads(img['metadata'])
                img_type = img_metadata.get('type', 'unknown')
                filename = img_metadata.get('filename', f'{img_type}.png')

                # Write image to ZIP
                zipf.writestr(f'images/{filename}', img['data'])
                images_count += 1

            print(f"  ✅ Added {images_count} images")

            # 4. Add story posts
            posts = db.execute('''
                SELECT title, slug, content FROM posts
                WHERE brand_id = ?
                ORDER BY published_at ASC
            ''', (brand['id'],)).fetchall()

            stories_count = 0
            for i, post in enumerate(posts, 1):
                story_md = f"# {post['title']}\n\n{post['content']}"
                zipf.writestr(f'stories/chapter-{i}.md', story_md)
                stories_count += 1

            print(f"  ✅ Added {stories_count} story chapters")

            # 5. Add ML models (wordmap & emoji patterns)
            from brand_vocabulary_trainer import BrandVocabularyTrainer
            trainer = BrandVocabularyTrainer()

            # Try to load existing wordmap
            try:
                wordmap = trainer.load_brand_wordmap(brand['id'])
                if wordmap:
                    zipf.writestr('ml_models/wordmap.json', json.dumps(wordmap, indent=2))
                    print(f"  ✅ Added ml_models/wordmap.json")
            except:
                print(f"  ⚠️  No wordmap found for brand")

            # Try to load emoji patterns
            try:
                emoji_patterns = trainer.load_brand_emoji_patterns(brand['id'])
                if emoji_patterns:
                    zipf.writestr('ml_models/emoji_patterns.json', json.dumps(emoji_patterns, indent=2))
                    print(f"  ✅ Added ml_models/emoji_patterns.json")
            except:
                print(f"  ⚠️  No emoji patterns found for brand")

            # 6. Add SOPs (Standard Operating Procedures)
            try:
                sop_rows = db.execute('''
                    SELECT * FROM brand_sops WHERE brand_id = ?
                ''', (brand['id'],)).fetchall()

                if sop_rows:
                    from brand_sop_templates import SOPTemplateLibrary
                    library = SOPTemplateLibrary()

                    for sop_row in sop_rows:
                        sop_data = json.loads(sop_row['sop_data'])
                        template_id = sop_row['template_id']

                        # Export as YAML
                        sop_yaml = library.export_as_yaml(sop_data)
                        zipf.writestr(f'sops/{template_id}.yaml', sop_yaml)

                        # Export as Markdown
                        sop_md = library.export_as_markdown(sop_data)
                        zipf.writestr(f'sops/{template_id}.md', sop_md)

                    print(f"  ✅ Added {len(sop_rows)} SOPs (YAML + Markdown)")
                else:
                    print(f"  ⚠️  No SOPs found for brand")
            except Exception as e:
                print(f"  ⚠️  Could not export SOPs: {e}")

            # 7. Add LICENSE.txt
            from standardize_brand_zip import generate_license_txt
            license_txt = generate_license_txt(license_type, brand['name'])
            zipf.writestr('LICENSE.txt', license_txt)
            print(f"  ✅ Added LICENSE.txt")

            # 7. Add README with installation instructions
            readme = f"""# {brand['name']} Theme

{brand['personality']}

## Installation

1. Extract this ZIP to your soulfra-simple directory
2. Run the import command:
   ```bash
   python3 -c "from brand_theme_manager import BrandThemeManager; BrandThemeManager().import_brand('{zip_filename}')"
   ```

3. View the brand at: http://localhost:5001/brand/{brand_slug}

## Theme Details

- **Personality**: {brand['personality']}
- **Values**: {', '.join(json.loads(brand['brand_values']) if brand['brand_values'] else [])}
- **Tone**: {brand['tone']}
- **Target Audience**: {brand['target_audience']}
- **Stories**: {stories_count} chapters
- **Images**: {images_count} assets

## License

This theme is part of the Soulfra platform.
Fork, modify, and distribute freely.

---

Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            zipf.writestr('README.md', readme)
            print(f"  ✅ Added README.md")

        print(f"\n✅ Theme exported: {zip_path}")
        print(f"   Size: {zip_path.stat().st_size / 1024:.1f} KB")

        return str(zip_path)

    def import_brand(self, zip_path: str) -> Optional[int]:
        """
        Import brand from ZIP theme package

        Args:
            zip_path: Path to ZIP file

        Returns:
            Brand ID, or None if import failed
        """
        zip_path = Path(zip_path)

        if not zip_path.exists():
            print(f"❌ ZIP file not found: {zip_path}")
            return None

        print(f"\n📥 Importing brand theme from: {zip_path.name}")

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # 1. Extract and load brand config
            brand_yaml = zipf.read('brand.yaml').decode('utf-8')
            brand_config = yaml.safe_load(brand_yaml)

            print(f"  ✅ Loaded brand config: {brand_config['name']}")

            # 2. Load metadata
            metadata_json = zipf.read('metadata.json').decode('utf-8')
            metadata = json.loads(metadata_json)

            # 3. Import brand using BrandDatabaseIntegration
            import sys
            sys.path.insert(0, str(self.project_root / 'lib'))

            from brand_database_integration import BrandDatabaseIntegration

            integrator = BrandDatabaseIntegration()

            # Store brand in database
            brand_id = integrator.store_brand(brand_config)

            # 4. Extract and store images
            image_files = [f for f in zipf.namelist() if f.startswith('images/')]

            for img_file in image_files:
                img_data = zipf.read(img_file)
                img_type = Path(img_file).stem

                # Save to temporary file
                temp_dir = Path('/tmp/brand-import')
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / Path(img_file).name

                with open(temp_path, 'wb') as f:
                    f.write(img_data)

                # Store in database
                integrator.store_image(str(temp_path), brand_id, img_type)

            print(f"  ✅ Imported {len(image_files)} images")

            # 5. Extract and store stories
            story_files = [f for f in zipf.namelist() if f.startswith('stories/')]

            if story_files:
                # Save stories to temporary directory
                temp_stories_dir = Path('/tmp/brand-import/stories')
                temp_stories_dir.mkdir(parents=True, exist_ok=True)

                for story_file in story_files:
                    story_content = zipf.read(story_file).decode('utf-8')
                    temp_story_path = temp_stories_dir / Path(story_file).name

                    with open(temp_story_path, 'w') as f:
                        f.write(story_content)

                # Store stories as posts
                post_ids = integrator.store_brand_stories(
                    brand_id,
                    str(temp_stories_dir),
                    brand_config['name']
                )

                print(f"  ✅ Imported {len(post_ids)} story chapters")

            print(f"\n✅ Brand imported successfully!")
            print(f"   Brand ID: {brand_id}")
            print(f"   View at: http://localhost:5001/brand/{metadata['slug']}")

            return brand_id

    def list_exported_themes(self) -> list:
        """
        List all exported theme ZIPs

        Returns:
            List of theme metadata dicts
        """
        exports_dir = Path(__file__).parent / 'exports'

        if not exports_dir.exists():
            return []

        themes = []

        for zip_file in exports_dir.glob('*.zip'):
            try:
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    metadata_json = zipf.read('metadata.json').decode('utf-8')
                    metadata = json.loads(metadata_json)
                    metadata['zip_file'] = str(zip_file)
                    metadata['file_size_kb'] = zip_file.stat().st_size / 1024
                    themes.append(metadata)
            except Exception as e:
                print(f"⚠️  Could not read {zip_file.name}: {e}")

        return themes


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import sys

    manager = BrandThemeManager()

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  Export: python3 brand_theme_manager.py export <brand-slug>")
        print("  Import: python3 brand_theme_manager.py import <theme.zip>")
        print("  List:   python3 brand_theme_manager.py list")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'export':
        if len(sys.argv) < 3:
            print("Usage: python3 brand_theme_manager.py export <brand-slug>")
            sys.exit(1)

        brand_slug = sys.argv[2]
        zip_path = manager.export_brand(brand_slug)

        if zip_path:
            print(f"\n🎉 Success! Theme ready to share:")
            print(f"   {zip_path}")

    elif command == 'import':
        if len(sys.argv) < 3:
            print("Usage: python3 brand_theme_manager.py import <theme.zip>")
            sys.exit(1)

        zip_path = sys.argv[2]
        brand_id = manager.import_brand(zip_path)

        if brand_id:
            print(f"\n🎉 Import successful! Brand ID: {brand_id}")

    elif command == 'list':
        themes = manager.list_exported_themes()

        if themes:
            print(f"\n📦 Exported Themes ({len(themes)}):\n")
            for theme in themes:
                print(f"  • {theme['name']}")
                print(f"    Slug: {theme['slug']}")
                print(f"    File: {Path(theme['zip_file']).name}")
                print(f"    Size: {theme['file_size_kb']:.1f} KB")
                print(f"    Exported: {theme['exported_at'][:10]}")
                print()
        else:
            print("\n📦 No exported themes found")
            print("   Export a theme with: python3 brand_theme_manager.py export <brand-slug>")

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
