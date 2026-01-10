#!/usr/bin/env python3
"""
Voice Pipeline - Voice Memo → Transcription → @Route

Complete pipeline for processing voice memos:
1. Receive voice memo (upload, AirDrop, Bluetooth)
2. Store in voice_inputs database
3. Transcribe with Whisper
4. Import as markdown with @routing
5. Generate QR codes and pSEO pages
6. Make accessible via browser

**Use Cases:**
- Accessibility: Talk instead of type (carpal tunnel relief)
- Quick notes: iPhone voice memo → instant @route
- Meeting notes: Record → transcribe → organize
- Blog posts: Speak your thoughts → auto-publish

**Usage:**
```python
from voice_pipeline import VoicePipeline

pipeline = VoicePipeline()

# Process voice memo
result = pipeline.process_voice_memo(
    audio_path='memo.wav',
    brand='me',
    category='voice',
    user_id=1
)

# Access at: http://localhost:5001/@me/voice/memo-title
print(result['route'])
```

**CLI:**
```bash
# Process single voice memo
python3 voice_pipeline.py memo.wav --brand me --category voice

# Process all pending transcriptions
python3 voice_pipeline.py --process-queue

# Watch folder for new voice memos
python3 voice_pipeline.py --watch ~/Desktop/voice-memos/

# Process voice memo with QR + voice integration
python3 voice_pipeline.py memo.wav --attach-to-scan 123
```
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from voice_input import add_audio, get_audio, list_audio, transcribe_audio
from whisper_transcriber import WhisperTranscriber, transcribe_voice_input
from file_importer import FileImporter
from content_pipeline import ContentPipeline
from qr_voice_integration import attach_voice_to_scan


# ==============================================================================
# CONFIG
# ==============================================================================

DEFAULT_BRAND = os.environ.get('VOICE_BRAND', 'me')
DEFAULT_CATEGORY = os.environ.get('VOICE_CATEGORY', 'voice')
DEFAULT_USER_ID = int(os.environ.get('VOICE_USER_ID', '1'))

TEMP_DIR = Path('./temp_voice')
TEMP_DIR.mkdir(exist_ok=True)


# ==============================================================================
# VOICE PIPELINE
# ==============================================================================

class VoicePipeline:
    """
    Complete voice memo processing pipeline
    """

    def __init__(self):
        self.transcriber = WhisperTranscriber()
        self.importer = FileImporter()
        self.pipeline = ContentPipeline()


    def process_voice_memo(
        self,
        audio_path: Union[str, Path],
        brand: str = DEFAULT_BRAND,
        category: str = DEFAULT_CATEGORY,
        user_id: int = DEFAULT_USER_ID,
        title: Optional[str] = None,
        auto_transcribe: bool = True,
        use_full_pipeline: bool = True,
        attach_to_scan: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process voice memo through complete pipeline

        Args:
            audio_path: Path to audio file
            brand: Brand name for @routing
            category: Category for organization
            user_id: User ID
            title: Custom title (default: from filename)
            auto_transcribe: Auto-transcribe with Whisper
            use_full_pipeline: Use content pipeline (QR codes, pSEO, etc.)
            attach_to_scan: Optional QR scan ID to attach voice to
            metadata: Additional metadata

        Returns:
            {
                'success': True,
                'audio_id': 123,
                'transcription': 'Text...',
                'route': '@me/voice/title',
                'url': 'http://localhost:5001/@me/voice/title',
                'qr_code': '/static/qr/...',
                'file_id': 456
            }
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f'\n🎤 Processing voice memo: {audio_path.name}\n')

        # Step 1: Store in voice_inputs database
        print('📥 Step 1: Storing audio...')
        audio_metadata = metadata or {}
        audio_metadata.update({
            'original_filename': audio_path.name,
            'brand': brand,
            'category': category,
            'user_id': user_id
        })

        audio_id = add_audio(
            file_path=str(audio_path),
            source='manual',
            metadata=audio_metadata
        )

        print(f'   ✓ Audio stored (ID: {audio_id})')

        # Step 2: Transcribe with Whisper
        transcription_text = None

        if auto_transcribe:
            print('\n🤖 Step 2: Transcribing...')

            try:
                transcription_result = transcribe_voice_input(audio_id)
                transcription_text = transcription_result['text']

                print(f'   ✓ Transcription: {transcription_text[:100]}...')

            except Exception as e:
                print(f'   ⚠️  Transcription failed: {e}')
                transcription_text = '[Transcription pending]'

        else:
            transcription_text = '[Transcription pending - manual]'

        # Step 3: Create markdown file
        print('\n📝 Step 3: Creating markdown...')

        title = title or self._generate_title_from_transcription(
            transcription_text,
            audio_path.stem
        )

        markdown_content = self._create_voice_memo_markdown(
            title=title,
            transcription=transcription_text,
            audio_path=audio_path,
            audio_id=audio_id,
            metadata=audio_metadata
        )

        # Save to temp file
        temp_md = TEMP_DIR / f'{audio_path.stem}.md'
        temp_md.write_text(markdown_content)

        print(f'   ✓ Markdown created: {temp_md.name}')

        # Step 4: Import through pipeline
        print('\n📦 Step 4: Importing to @routes...')

        if use_full_pipeline:
            # Use full content pipeline (with QR, pSEO, etc.)
            import_result = self.pipeline.process_file(
                file_path=str(temp_md),
                brand=brand,
                category=category,
                user_id=user_id
            )
        else:
            # Use simple file importer
            import_result = self.importer.import_file(
                file_path=str(temp_md),
                brand=brand,
                category=category,
                user_id=user_id
            )

        print(f'   ✓ Imported: {import_result["route"]}')

        # Step 5: Attach to QR scan (if requested)
        if attach_to_scan:
            print(f'\n🔗 Step 5: Attaching to QR scan {attach_to_scan}...')

            try:
                attach_voice_to_scan(
                    scan_id=attach_to_scan,
                    audio_file=str(audio_path),
                    transcription=transcription_text
                )
                print(f'   ✓ Attached to scan')

            except Exception as e:
                print(f'   ⚠️  Attachment failed: {e}')

        # Clean up temp file
        temp_md.unlink()

        # Return result
        result = {
            'success': True,
            'audio_id': audio_id,
            'audio_path': str(audio_path),
            'transcription': transcription_text,
            'title': title,
            **import_result
        }

        print(f'\n✅ Voice memo processed!')
        print(f'   Route: {result["route"]}')
        if result.get('url'):
            print(f'   URL: {result["url"]}')
        if result.get('qr_code'):
            print(f'   QR Code: {result["qr_code"]}')

        return result


    def process_queue(
        self,
        brand: str = DEFAULT_BRAND,
        category: str = DEFAULT_CATEGORY,
        user_id: int = DEFAULT_USER_ID,
        limit: int = 10,
        use_full_pipeline: bool = True
    ) -> List[Dict]:
        """
        Process all pending voice inputs

        Args:
            brand: Brand name
            category: Category
            user_id: User ID
            limit: Max number to process
            use_full_pipeline: Use full content pipeline

        Returns:
            List of processing results
        """
        # Get pending voice inputs
        pending = list_audio(status='pending', limit=limit)

        if not pending:
            print('✅ No pending voice memos')
            return []

        print(f'\n📋 Processing {len(pending)} pending voice memos...\n')

        results = []

        for audio in pending:
            try:
                # Extract brand/category from metadata if available
                audio_metadata = audio.get('metadata', {})
                audio_brand = audio_metadata.get('brand', brand)
                audio_category = audio_metadata.get('category', category)
                audio_user_id = audio_metadata.get('user_id', user_id)

                # Process
                result = self.process_voice_memo(
                    audio_path=audio['file_path'],
                    brand=audio_brand,
                    category=audio_category,
                    user_id=audio_user_id,
                    auto_transcribe=True,
                    use_full_pipeline=use_full_pipeline
                )

                results.append(result)

            except Exception as e:
                print(f'   ❌ Failed to process {audio["filename"]}: {e}')
                results.append({
                    'success': False,
                    'audio_id': audio['id'],
                    'error': str(e)
                })

        print(f'\n✅ Processed {len(results)} voice memos')

        return results


    def _generate_title_from_transcription(
        self,
        transcription: str,
        fallback: str
    ) -> str:
        """
        Generate title from transcription text

        Args:
            transcription: Transcribed text
            fallback: Fallback title

        Returns:
            Generated title
        """
        # Use first sentence or first 50 chars
        if transcription and transcription != '[Transcription pending]':
            # Get first sentence
            first_sentence = transcription.split('.')[0].strip()

            if len(first_sentence) > 50:
                first_sentence = first_sentence[:50]

            # Clean up
            title = first_sentence.replace('\n', ' ').strip()

            if title:
                return title

        # Fallback to filename
        return fallback.replace('-', ' ').replace('_', ' ').title()


    def _create_voice_memo_markdown(
        self,
        title: str,
        transcription: str,
        audio_path: Path,
        audio_id: int,
        metadata: Dict
    ) -> str:
        """
        Create markdown file for voice memo

        Args:
            title: Memo title
            transcription: Transcribed text
            audio_path: Audio file path
            audio_id: Voice input ID
            metadata: Additional metadata

        Returns:
            Markdown content
        """
        # Get audio duration
        duration = metadata.get('duration', 'unknown')

        # Create frontmatter
        frontmatter = {
            'title': title,
            'date': datetime.now().isoformat(),
            'type': 'voice-memo',
            'source': 'audio',
            'audio_id': audio_id,
            'audio_file': audio_path.name,
            'transcription_method': 'whisper',
            'duration': f'{duration}s' if duration != 'unknown' else duration,
        }

        # Add custom metadata
        for key, value in metadata.items():
            if key not in frontmatter and key not in ['original_filename']:
                frontmatter[key] = value

        # Build markdown
        lines = ['---']
        for key, value in frontmatter.items():
            lines.append(f'{key}: {value}')
        lines.append('---')
        lines.append('')
        lines.append(f'# {title}')
        lines.append('')
        lines.append(f'**Recorded:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append('')
        lines.append('## Transcription')
        lines.append('')
        lines.append(transcription)
        lines.append('')

        return '\n'.join(lines)


# ==============================================================================
# FOLDER WATCHING
# ==============================================================================

def watch_voice_folder(
    folder_path: str,
    brand: str = DEFAULT_BRAND,
    category: str = DEFAULT_CATEGORY,
    user_id: int = DEFAULT_USER_ID,
    use_full_pipeline: bool = True
) -> None:
    """
    Watch folder for new voice memos and auto-process

    Args:
        folder_path: Folder to watch
        brand: Brand name
        category: Category
        user_id: User ID
        use_full_pipeline: Use full content pipeline
    """
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import time

    class VoiceFileHandler(FileSystemEventHandler):
        def __init__(self):
            self.pipeline = VoicePipeline()
            self.processing = set()

        def on_created(self, event):
            if event.is_directory:
                return

            file_path = Path(event.src_path)

            # Only process audio files
            if file_path.suffix.lower() not in ['.wav', '.mp3', '.m4a', '.ogg', '.flac']:
                return

            # Ignore hidden files
            if file_path.name.startswith('.'):
                return

            # Avoid duplicate processing
            if str(file_path) in self.processing:
                return

            self.processing.add(str(file_path))

            # Wait for file to finish writing
            time.sleep(1)

            # Process
            try:
                result = self.pipeline.process_voice_memo(
                    audio_path=file_path,
                    brand=brand,
                    category=category,
                    user_id=user_id,
                    use_full_pipeline=use_full_pipeline
                )

                print(f'\n📍 Access at: {result.get("url", result["route"])}')

            except Exception as e:
                print(f'\n❌ Error processing {file_path.name}: {e}')

            finally:
                self.processing.remove(str(file_path))

    # Setup watcher
    folder_path = Path(folder_path).expanduser().resolve()
    folder_path.mkdir(parents=True, exist_ok=True)

    handler = VoiceFileHandler()
    observer = Observer()
    observer.schedule(handler, str(folder_path), recursive=False)

    print(f'\n👀 Watching: {folder_path}')
    print(f'   Brand: {brand}')
    print(f'   Category: {category}')
    print('\n   Waiting for voice memos... (Ctrl+C to stop)\n')

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print('\n\n✅ Stopped watching\n')

    observer.join()


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Voice Pipeline - Voice Memo Processing')
    parser.add_argument('audio', type=str, nargs='?', help='Audio file to process')
    parser.add_argument('--brand', type=str, default=DEFAULT_BRAND, help='Brand name')
    parser.add_argument('--category', type=str, default=DEFAULT_CATEGORY, help='Category')
    parser.add_argument('--user-id', type=int, default=DEFAULT_USER_ID, help='User ID')
    parser.add_argument('--title', type=str, help='Custom title')
    parser.add_argument('--no-transcribe', action='store_true', help='Skip transcription')
    parser.add_argument('--simple', action='store_true', help='Use simple importer (no QR/pSEO)')
    parser.add_argument('--attach-to-scan', type=int, help='Attach to QR scan ID')

    # Batch processing
    parser.add_argument('--process-queue', action='store_true', help='Process pending queue')
    parser.add_argument('--limit', type=int, default=10, help='Queue limit')

    # Folder watching
    parser.add_argument('--watch', type=str, help='Watch folder for new voice memos')

    args = parser.parse_args()

    try:
        pipeline = VoicePipeline()

        if args.watch:
            # Watch folder
            watch_voice_folder(
                folder_path=args.watch,
                brand=args.brand,
                category=args.category,
                user_id=args.user_id,
                use_full_pipeline=not args.simple
            )

        elif args.process_queue:
            # Process queue
            results = pipeline.process_queue(
                brand=args.brand,
                category=args.category,
                user_id=args.user_id,
                limit=args.limit,
                use_full_pipeline=not args.simple
            )

            print(f'\n📊 Summary:')
            success_count = sum(1 for r in results if r.get('success', False))
            print(f'   Success: {success_count}/{len(results)}')

        elif args.audio:
            # Process single file
            result = pipeline.process_voice_memo(
                audio_path=args.audio,
                brand=args.brand,
                category=args.category,
                user_id=args.user_id,
                title=args.title,
                auto_transcribe=not args.no_transcribe,
                use_full_pipeline=not args.simple,
                attach_to_scan=args.attach_to_scan
            )

        else:
            # Show help
            print('Voice Pipeline - Voice Memo Processing\n')
            print('Usage:')
            print('  python3 voice_pipeline.py memo.wav --brand me --category voice')
            print('  python3 voice_pipeline.py --process-queue')
            print('  python3 voice_pipeline.py --watch ~/Desktop/voice-memos/\n')
            print('Examples:')
            print('  # iPhone → MacBook AirDrop → Auto-process')
            print('  python3 voice_pipeline.py --watch ~/Downloads/\n')
            print('  # Process with QR code attachment')
            print('  python3 voice_pipeline.py memo.wav --attach-to-scan 123\n')

    except Exception as e:
        print(f'\n❌ Error: {e}')
        exit(1)
