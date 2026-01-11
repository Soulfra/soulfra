#!/usr/bin/env python3
"""
Drop Box Watcher - Auto-Process AirDrops

Watches ~/Public/Drop Box/ for files you AirDrop from your phone.
Auto-processes them and updates GitHub Pages.

Usage:
    python3 dropbox-watcher.py

Then AirDrop files:
- professionals.csv → Auto-import → Auto-export → Auto-deploy
- signup-JoePlumbing.txt → Auto-add → Auto-export → Auto-deploy
- logo.png → Auto-add to assets → Auto-deploy

ZERO terminal commands. Just drop files.
"""

import time
import subprocess
from pathlib import Path
import hashlib

# Configuration
DROPBOX_DIR = Path.home() / 'Public' / 'Drop Box'
PROCESSED_DIR = DROPBOX_DIR / '_processed'
DB_PATH = Path(__file__).parent / 'soulfra.db'
EXPORT_SCRIPT = Path(__file__).parent / 'export-to-github-pages.py'
CSV_MANAGER = Path(__file__).parent / 'csv-manager.py'

# State tracking
seen_files = set()


def get_file_hash(filepath):
    """Get MD5 hash of file"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def process_csv_file(filepath):
    """Process CSV file (professionals list)"""
    print(f"📊 Processing CSV: {filepath.name}")

    # Import to database
    result = subprocess.run(
        ['python3', str(CSV_MANAGER), 'import', str(filepath)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"   ✅ Imported to database")

        # Export to GitHub Pages
        print(f"   🌐 Exporting to GitHub Pages...")
        result2 = subprocess.run(
            ['python3', str(EXPORT_SCRIPT)],
            capture_output=True,
            text=True
        )

        if result2.returncode == 0:
            print(f"   ✅ Exported to GitHub Pages")
            print(f"   📦 Ready to deploy (auto-deploy will handle it)")
            return True
        else:
            print(f"   ❌ Export failed: {result2.stderr}")
            return False
    else:
        print(f"   ❌ Import failed: {result.stderr}")
        return False


def process_text_file(filepath):
    """Process text file (signup info)"""
    print(f"📝 Processing signup: {filepath.name}")

    try:
        content = filepath.read_text()

        # Try to parse signup info
        # Expected format:
        # Business: Joe's Plumbing
        # Category: plumbing
        # Email: joe@example.com
        # Phone: (727) 555-1234

        data = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                data[key] = value

        if not data.get('business'):
            print(f"   ⚠️  No 'Business:' field found, skipping")
            return False

        # Create CSV with this one entry
        import csv
        temp_csv = DROPBOX_DIR / f'_temp_{filepath.stem}.csv'

        with open(temp_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'business_name', 'category', 'email', 'phone', 'bio', 'website', 'address', 'city', 'zip_code', 'approval_status', 'created_at'])
            writer.writerow([
                '',
                data.get('business', ''),
                data.get('category', ''),
                data.get('email', ''),
                data.get('phone', ''),
                data.get('bio', ''),
                data.get('website', ''),
                data.get('address', ''),
                data.get('city', ''),
                data.get('zip_code', ''),
                'approved',  # Auto-approve
                ''
            ])

        # Process the CSV
        success = process_csv_file(temp_csv)

        # Clean up temp file
        temp_csv.unlink()

        return success

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def process_image_file(filepath):
    """Process image file (logo, QR code, etc.)"""
    print(f"🖼️  Processing image: {filepath.name}")

    # Copy to GitHub Pages assets folder
    assets_dir = Path.home() / 'Desktop' / 'soulfra.github.io' / 'stpetepros' / 'assets'
    assets_dir.mkdir(exist_ok=True)

    import shutil
    dest = assets_dir / filepath.name
    shutil.copy(filepath, dest)

    print(f"   ✅ Copied to: {dest}")
    print(f"   🌐 Will be live at: /stpetepros/assets/{filepath.name}")
    return True


def move_to_processed(filepath):
    """Move processed file to _processed folder"""
    PROCESSED_DIR.mkdir(exist_ok=True)
    dest = PROCESSED_DIR / filepath.name

    # If file exists, append timestamp
    if dest.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = PROCESSED_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"

    filepath.rename(dest)
    print(f"   📁 Moved to: {dest}")


def scan_dropbox():
    """Scan Drop Box for new files"""
    if not DROPBOX_DIR.exists():
        DROPBOX_DIR.mkdir(parents=True)
        return []

    new_files = []

    for filepath in DROPBOX_DIR.rglob('*'):
        # Skip directories, processed folder, and hidden files
        if filepath.is_dir() or filepath.name.startswith('.') or filepath.name.startswith('_'):
            continue

        file_hash = get_file_hash(filepath)
        if file_hash and file_hash not in seen_files:
            new_files.append(filepath)
            seen_files.add(file_hash)

    return new_files


def process_file(filepath):
    """Process file based on type"""
    suffix = filepath.suffix.lower()

    # CSV files
    if suffix == '.csv':
        success = process_csv_file(filepath)

    # Text files (signup info)
    elif suffix in ['.txt', '.text']:
        success = process_text_file(filepath)

    # Image files
    elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        success = process_image_file(filepath)

    else:
        print(f"⚠️  Unknown file type: {filepath.name}")
        print(f"   Supported: .csv, .txt, .png, .jpg")
        success = False

    if success:
        move_to_processed(filepath)

    print()


def main():
    print()
    print("=" * 60)
    print("  Drop Box Watcher")
    print("=" * 60)
    print()
    print(f"📂 Watching: {DROPBOX_DIR}")
    print()
    print("AirDrop files to trigger auto-processing:")
    print("  • professionals.csv → Auto-import to database")
    print("  • signup-JoePlumbing.txt → Auto-add professional")
    print("  • logo.png → Auto-add to assets")
    print()
    print("Stop with: Ctrl+C")
    print()

    # Create Drop Box folder if it doesn't exist
    DROPBOX_DIR.mkdir(parents=True, exist_ok=True)

    # Initial scan (mark existing files as seen)
    for filepath in DROPBOX_DIR.rglob('*'):
        if filepath.is_file() and not filepath.name.startswith('.') and not filepath.name.startswith('_'):
            file_hash = get_file_hash(filepath)
            if file_hash:
                seen_files.add(file_hash)

    print(f"👀 Watching {len(seen_files)} existing files...")
    print()

    try:
        while True:
            new_files = scan_dropbox()

            for filepath in new_files:
                print(f"🔔 New file detected: {filepath.name}")
                process_file(filepath)

            time.sleep(2)  # Check every 2 seconds

    except KeyboardInterrupt:
        print()
        print("⏹️  Drop Box watcher stopped")
        print()


if __name__ == '__main__':
    main()
