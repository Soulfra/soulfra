#!/usr/bin/env python3
"""
Migrate existing image files to database
Reads showcase/*.png and stores in images table
"""

import os
import hashlib
import json
from PIL import Image
from database import get_db

def migrate_images():
    """Load showcase images into database"""
    db = get_db()

    showcase_dir = 'showcase'
    if not os.path.exists(showcase_dir):
        print(f"❌ {showcase_dir}/ not found")
        return

    # Find all PNG files
    image_files = [f for f in os.listdir(showcase_dir) if f.endswith('.png')]

    print(f"📁 Found {len(image_files)} images in {showcase_dir}/\n")

    migrated = 0
    skipped = 0

    for filename in sorted(image_files):
        filepath = os.path.join(showcase_dir, filename)

        # Read image data
        with open(filepath, 'rb') as f:
            image_data = f.read()

        # Calculate hash
        image_hash = hashlib.sha256(image_data).hexdigest()

        # Get image dimensions
        try:
            img = Image.open(filepath)
            width, height = img.size
        except:
            width, height = None, None

        # Parse metadata from filename
        # Format: username_type.png (e.g., alice_viz.png, calriven_qr.png)
        base_name = filename.replace('.png', '')
        parts = base_name.split('_')

        if len(parts) >= 2:
            username = parts[0]
            image_type = '_'.join(parts[1:])  # Handle cases like showcase_grid
        else:
            username = None
            image_type = base_name

        metadata = json.dumps({
            'filename': filename,
            'type': image_type,
            'username': username,
            'source': 'showcase'
        })

        # Check if already exists
        existing = db.execute('SELECT id FROM images WHERE hash = ?', (image_hash,)).fetchone()

        if existing:
            print(f"   ⏭️  {filename} (already in database)")
            skipped += 1
            continue

        # Insert into database
        try:
            db.execute('''
                INSERT INTO images (hash, data, mime_type, width, height, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_hash, image_data, 'image/png', width, height, metadata))

            print(f"   ✅ {filename} → {image_hash[:12]}... ({width}x{height})")
            migrated += 1

        except Exception as e:
            print(f"   ❌ {filename}: {e}")

    db.commit()
    db.close()

    print(f"\n📊 Migration complete:")
    print(f"   • Migrated: {migrated}")
    print(f"   • Skipped: {skipped}")
    print(f"   • Total: {migrated + skipped}")


if __name__ == '__main__':
    print("🖼️  Migrating images to database...\n")
    migrate_images()
