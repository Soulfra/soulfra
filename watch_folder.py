#!/usr/bin/env python3
"""
Folder Watcher - Auto-Import Files

Watch a folder for new files and automatically import them.

**Use Cases:**
- Phone → Laptop: AirDrop/Bluetooth files to watched folder
- Cloud sync: Dropbox/iCloud folder auto-imports
- Temp files: Automatically process temporary files

**Usage:**
```bash
# Watch a folder
python3 watch_folder.py ~/Desktop/sync/

# With custom brand/category
python3 watch_folder.py ~/Desktop/sync/ --brand me --category imports

# Process existing files once
python3 watch_folder.py ~/Desktop/sync/ --once
```

**How It Works:**
1. Watch folder for new files
2. When file added → auto-import via file_importer.py
3. Route to @brand/category/filename
4. Move processed file to archive/
"""

import os
import time
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_importer import FileImporter
from content_pipeline import ContentPipeline


# ==============================================================================
# CONFIG
# ==============================================================================

DEFAULT_BRAND = os.environ.get('WATCH_BRAND', 'imports')
DEFAULT_CATEGORY = os.environ.get('WATCH_CATEGORY', 'auto')
DEFAULT_USER_ID = int(os.environ.get('WATCH_USER_ID', '1'))
ARCHIVE_DIR_NAME = '.processed'


# ==============================================================================
# FILE HANDLER
# ==============================================================================

class FileImportHandler(FileSystemEventHandler):
    """
    Handle new files in watched directory
    """

    def __init__(
        self,
        watch_path: Path,
        brand: str = DEFAULT_BRAND,
        category: str = DEFAULT_CATEGORY,
        user_id: int = DEFAULT_USER_ID,
        use_pipeline: bool = True
    ):
        self.watch_path = Path(watch_path)
        self.brand = brand
        self.category = category
        self.user_id = user_id
        self.use_pipeline = use_pipeline

        # Archive directory for processed files
        self.archive_dir = self.watch_path / ARCHIVE_DIR_NAME
        self.archive_dir.mkdir(exist_ok=True)

        # Initialize importer
        if use_pipeline:
            self.processor = ContentPipeline()
        else:
            self.processor = FileImporter()

        print(f'\n👀 Watching: {self.watch_path}')
        print(f'   Brand: {self.brand}')
        print(f'   Category: {self.category}')
        print(f'   Archive: {self.archive_dir}\n')


    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore hidden files and archive directory
        if file_path.name.startswith('.') or file_path.parent == self.archive_dir:
            return

        # Wait a moment to ensure file is fully written
        time.sleep(0.5)

        # Import file
        self.import_file(file_path)


    def import_file(self, file_path: Path):
        """Import a file"""
        print(f'\n📥 New file detected: {file_path.name}')

        try:
            # Process file
            if self.use_pipeline:
                result = self.processor.process_file(
                    file_path=str(file_path),
                    brand=self.brand,
                    category=self.category,
                    user_id=self.user_id
                )
            else:
                result = self.processor.import_file(
                    file_path=str(file_path),
                    brand=self.brand,
                    category=self.category,
                    user_id=self.user_id
                )

            if result.get('success', True):
                print(f'   ✅ Imported: {result["route"]}')
                print(f'   📍 URL: {result["url"]}')

                # Move to archive
                archive_path = self.archive_dir / file_path.name
                file_path.rename(archive_path)
                print(f'   📦 Archived: {archive_path.name}\n')

            else:
                print(f'   ❌ Import failed!')
                for error in result.get('errors', []):
                    print(f'      {error}')
                print()

        except Exception as e:
            print(f'   ❌ Error: {e}\n')


# ==============================================================================
# FOLDER WATCHER
# ==============================================================================

class FolderWatcher:
    """
    Watch a folder and auto-import files
    """

    def __init__(
        self,
        watch_path: str,
        brand: str = DEFAULT_BRAND,
        category: str = DEFAULT_CATEGORY,
        user_id: int = DEFAULT_USER_ID,
        use_pipeline: bool = True
    ):
        self.watch_path = Path(watch_path).expanduser().resolve()

        # Create directory if doesn't exist
        self.watch_path.mkdir(parents=True, exist_ok=True)

        # Create handler
        self.handler = FileImportHandler(
            watch_path=self.watch_path,
            brand=brand,
            category=category,
            user_id=user_id,
            use_pipeline=use_pipeline
        )

        # Create observer
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.watch_path), recursive=False)


    def start(self):
        """Start watching"""
        print('🚀 Starting folder watcher...\n')
        print('   Press Ctrl+C to stop\n')

        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


    def stop(self):
        """Stop watching"""
        print('\n\n🛑 Stopping folder watcher...')
        self.observer.stop()
        self.observer.join()
        print('✅ Stopped\n')


    def process_existing(self):
        """Process all existing files in folder (one-time)"""
        print('📂 Processing existing files...\n')

        files = list(self.watch_path.glob('*'))
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]

        if not files:
            print('   No files found\n')
            return

        for file_path in files:
            self.handler.import_file(file_path)

        print(f'✅ Processed {len(files)} files\n')


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Folder Watcher - Auto-Import Files')
    parser.add_argument('path', type=str, help='Path to watch')
    parser.add_argument('--brand', type=str, default=DEFAULT_BRAND, help='Brand name')
    parser.add_argument('--category', type=str, default=DEFAULT_CATEGORY, help='Category')
    parser.add_argument('--user-id', type=int, default=DEFAULT_USER_ID, help='User ID')
    parser.add_argument('--once', action='store_true', help='Process existing files once and exit')
    parser.add_argument('--simple', action='store_true', help='Use simple importer (skip pipeline)')

    args = parser.parse_args()

    # Check if watchdog is installed
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print('\n❌ Error: watchdog not installed')
        print('\nInstall it with:')
        print('   pip install watchdog\n')
        exit(1)

    # Create watcher
    watcher = FolderWatcher(
        watch_path=args.path,
        brand=args.brand,
        category=args.category,
        user_id=args.user_id,
        use_pipeline=not args.simple
    )

    if args.once:
        # Process existing files and exit
        watcher.process_existing()
    else:
        # Watch continuously
        watcher.start()
