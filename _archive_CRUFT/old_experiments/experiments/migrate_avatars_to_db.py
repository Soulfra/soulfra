#!/usr/bin/env python3
"""
Migrate Avatar Images to Database

Reads static/avatars/generated/*.png and stores in images table.
Marks them with type='avatar' in metadata for easy querying.
"""

import os
import hashlib
import json
from PIL import Image
from database import get_db

def migrate_avatars():
    """Load avatar images into database"""
    db = get_db()

    avatar_dir = 'static/avatars/generated'
    if not os.path.exists(avatar_dir):
        print(f"❌ {avatar_dir}/ not found")
        return

    # Find all PNG files
    avatar_files = [f for f in os.listdir(avatar_dir) if f.endswith('.png')]

    print(f"📁 Found {len(avatar_files)} avatars in {avatar_dir}/\n")

    migrated = 0
    skipped = 0

    for filename in sorted(avatar_files):
        filepath = os.path.join(avatar_dir, filename)

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

        # Parse username from filename
        # Format: username.png (e.g., alice.png, calriven.png)
        username = filename.replace('.png', '')

        metadata = json.dumps({
            'filename': filename,
            'type': 'avatar',
            'username': username,
            'source': 'avatar_generator'
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

    print(f"\n📊 Avatar migration complete:")
    print(f"   • Migrated: {migrated}")
    print(f"   • Skipped: {skipped}")
    print(f"   • Total: {migrated + skipped}")


if __name__ == '__main__':
    print("🎨 Migrating avatars to database...\n")
    migrate_avatars()
