#!/usr/bin/env python3
"""
Whisper Transcriber - Local AI Transcription

Offline-first voice transcription using whisper.cpp or OpenAI Whisper.
Privacy-focused: All processing happens locally on your machine.

**Features:**
- Local AI transcription (no cloud APIs)
- Multiple language support
- Timestamp support
- Fast CPU/GPU inference
- Integrates with voice_input.py

**Usage:**
```python
from whisper_transcriber import WhisperTranscriber

transcriber = WhisperTranscriber()

# Transcribe audio file
result = transcriber.transcribe('audio.wav')
print(result['text'])

# Transcribe with timestamps
result = transcriber.transcribe('audio.wav', timestamps=True)
for segment in result['segments']:
    print(f"[{segment['start']}s - {segment['end']}s] {segment['text']}")
```

**CLI:**
```bash
# Transcribe single file
python3 whisper_transcriber.py audio.wav

# Transcribe with language hint
python3 whisper_transcriber.py audio.wav --language en

# Process queue from voice_input.py
python3 whisper_transcriber.py --process-queue

# Transcribe and import to @routes
python3 whisper_transcriber.py audio.wav --import --brand me --category voice
```

**Installation:**
```bash
# Option 1: Python whisper (easiest)
pip install openai-whisper

# Option 2: whisper.cpp (faster)
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
./models/download-ggml-model.sh base.en
```
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime


# ==============================================================================
# CONFIG
# ==============================================================================

WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
WHISPER_CPP_PATH = os.environ.get('WHISPER_CPP_PATH', None)  # Path to whisper.cpp
WHISPER_LANGUAGE = os.environ.get('WHISPER_LANGUAGE', 'en')  # Default language

DEFAULT_TEMP_DIR = Path('./temp_audio')
DEFAULT_TEMP_DIR.mkdir(exist_ok=True)


# ==============================================================================
# WHISPER TRANSCRIBER
# ==============================================================================

class WhisperTranscriber:
    """
    Local voice transcription using Whisper
    """

    def __init__(
        self,
        model: str = WHISPER_MODEL,
        whisper_cpp_path: Optional[str] = WHISPER_CPP_PATH,
        language: str = WHISPER_LANGUAGE
    ):
        self.model = model
        self.whisper_cpp_path = whisper_cpp_path
        self.language = language
        self.backend = self._detect_backend()


    def _detect_backend(self) -> str:
        """
        Detect which Whisper backend is available
        """
        # Check for whisper.cpp
        if self.whisper_cpp_path and Path(self.whisper_cpp_path).exists():
            return 'whisper.cpp'

        # Check for Python whisper
        try:
            import whisper
            return 'python-whisper'
        except ImportError:
            pass

        return 'none'


    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        timestamps: bool = False,
        **kwargs
    ) -> Dict:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file
            language: Language code (en, es, fr, etc.) or auto-detect
            timestamps: Include word-level timestamps
            **kwargs: Additional backend-specific options

        Returns:
            {
                'text': 'Transcribed text...',
                'language': 'en',
                'segments': [...],  # If timestamps=True
                'backend': 'whisper.cpp',
                'model': 'base',
                'duration': 12.5
            }
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        language = language or self.language

        print(f'\n🎤 Transcribing: {audio_path.name}')
        print(f'   Backend: {self.backend}')
        print(f'   Model: {self.model}')
        print(f'   Language: {language}\n')

        if self.backend == 'whisper.cpp':
            return self._transcribe_whisper_cpp(audio_path, language, timestamps, **kwargs)
        elif self.backend == 'python-whisper':
            return self._transcribe_python_whisper(audio_path, language, timestamps, **kwargs)
        else:
            return self._transcribe_fallback(audio_path)


    def _transcribe_whisper_cpp(
        self,
        audio_path: Path,
        language: str,
        timestamps: bool,
        **kwargs
    ) -> Dict:
        """
        Transcribe using whisper.cpp (faster)
        """
        # Build command
        cmd = [
            str(Path(self.whisper_cpp_path) / 'main'),
            '-m', str(Path(self.whisper_cpp_path) / 'models' / f'ggml-{self.model}.bin'),
            '-f', str(audio_path),
            '-l', language,
        ]

        if timestamps:
            cmd.append('--print-timestamps')

        # Add any additional flags
        for key, value in kwargs.items():
            cmd.extend([f'--{key}', str(value)])

        # Run transcription
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"whisper.cpp failed: {result.stderr}")

        # Parse output
        text = result.stdout.strip()

        return {
            'text': text,
            'language': language,
            'backend': 'whisper.cpp',
            'model': self.model,
            'duration': self._get_audio_duration(audio_path)
        }


    def _transcribe_python_whisper(
        self,
        audio_path: Path,
        language: str,
        timestamps: bool,
        **kwargs
    ) -> Dict:
        """
        Transcribe using Python whisper library
        """
        import whisper

        # Load model
        model = whisper.load_model(self.model)

        # Transcribe
        result = model.transcribe(
            str(audio_path),
            language=language if language != 'auto' else None,
            **kwargs
        )

        # Extract segments if timestamps requested
        segments = []
        if timestamps and 'segments' in result:
            segments = [
                {
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'].strip()
                }
                for seg in result['segments']
            ]

        return {
            'text': result['text'].strip(),
            'language': result.get('language', language),
            'segments': segments if timestamps else [],
            'backend': 'python-whisper',
            'model': self.model,
            'duration': self._get_audio_duration(audio_path)
        }


    def _transcribe_fallback(self, audio_path: Path) -> Dict:
        """
        Fallback: Return placeholder when no backend available
        """
        print('⚠️  No Whisper backend found!')
        print('   Install with: pip install openai-whisper')
        print('   Or use whisper.cpp for faster inference\n')

        return {
            'text': '[Transcription not available - install Whisper]',
            'language': 'unknown',
            'backend': 'none',
            'model': 'none',
            'duration': self._get_audio_duration(audio_path),
            'error': 'No Whisper backend installed'
        }


    def _get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """
        Get audio file duration using ffprobe
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries',
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                 str(audio_path)],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except:
            return None


    def transcribe_and_save(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict:
        """
        Transcribe and save to text file

        Args:
            audio_path: Audio file
            output_path: Output text file (default: audio_path.txt)
            **kwargs: Transcription options

        Returns:
            Transcription result
        """
        result = self.transcribe(audio_path, **kwargs)

        # Determine output path
        if output_path is None:
            output_path = Path(audio_path).with_suffix('.txt')
        else:
            output_path = Path(output_path)

        # Save text
        output_path.write_text(result['text'])

        print(f'✅ Transcription saved: {output_path}')

        result['output_path'] = str(output_path)
        return result


# ==============================================================================
# VOICE INPUT INTEGRATION
# ==============================================================================

def transcribe_voice_input(audio_id: int, **kwargs) -> Dict:
    """
    Transcribe audio from voice_inputs database

    Args:
        audio_id: Voice input ID
        **kwargs: Transcription options

    Returns:
        Transcription result
    """
    from voice_input import get_audio, transcribe_audio

    # Get audio record
    audio = get_audio(audio_id)

    if not audio:
        raise ValueError(f"Audio ID {audio_id} not found")

    if audio['status'] == 'transcribed':
        print(f'⚠️  Audio {audio_id} already transcribed')
        return {
            'text': audio['transcription'],
            'already_transcribed': True
        }

    # Transcribe
    transcriber = WhisperTranscriber()
    result = transcriber.transcribe(audio['file_path'], **kwargs)

    # Save to database
    transcribe_audio(audio_id, result['text'], method='whisper')

    print(f'✅ Audio {audio_id} transcribed and saved to database')

    # Trigger mesh network cascade (auto-propagate to economy)
    try:
        from economy_mesh_network import on_voice_transcribed
        print(f'🎭 Triggering economy mesh network cascade...')
        on_voice_transcribed(audio_id)
    except Exception as e:
        print(f'⚠️  Mesh network cascade failed: {e}')

    return result


def process_transcription_queue(limit: int = 10, **kwargs) -> List[Dict]:
    """
    Process pending transcriptions from voice_inputs queue

    Args:
        limit: Max number to process
        **kwargs: Transcription options

    Returns:
        List of transcription results
    """
    from voice_input import list_audio

    # Get pending audio
    pending = list_audio(status='pending', limit=limit)

    if not pending:
        print('✅ No pending transcriptions')
        return []

    print(f'\n📋 Processing {len(pending)} pending transcriptions...\n')

    results = []
    transcriber = WhisperTranscriber()

    for audio in pending:
        try:
            result = transcriber.transcribe(audio['file_path'], **kwargs)

            # Save to database
            from voice_input import transcribe_audio
            transcribe_audio(audio['id'], result['text'], method='whisper')

            results.append({
                'audio_id': audio['id'],
                'filename': audio['filename'],
                'text': result['text'],
                'success': True
            })

            print(f'   ✅ {audio["filename"]}: {result["text"][:50]}...')

        except Exception as e:
            print(f'   ❌ {audio["filename"]}: {e}')
            results.append({
                'audio_id': audio['id'],
                'filename': audio['filename'],
                'error': str(e),
                'success': False
            })

    print(f'\n✅ Processed {len(results)} transcriptions')

    return results


# ==============================================================================
# FILE IMPORT INTEGRATION
# ==============================================================================

def transcribe_and_import(
    audio_path: Union[str, Path],
    brand: str,
    category: str,
    user_id: int = 1,
    **kwargs
) -> Dict:
    """
    Transcribe audio and import as @route

    Args:
        audio_path: Audio file
        brand: Brand name
        category: Category
        user_id: User ID
        **kwargs: Transcription options

    Returns:
        Import result with route and transcription
    """
    from file_importer import FileImporter

    # Transcribe
    transcriber = WhisperTranscriber()
    result = transcriber.transcribe(audio_path, **kwargs)

    # Save transcript to temp file
    temp_md = DEFAULT_TEMP_DIR / f'{Path(audio_path).stem}.md'

    # Create markdown with metadata
    content = f"""---
title: Voice Memo - {Path(audio_path).stem}
date: {datetime.now().isoformat()}
type: voice-memo
source: audio
transcription_method: {result['backend']}
duration: {result.get('duration', 'unknown')}s
language: {result['language']}
---

# Voice Memo

**Transcribed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{result['text']}
"""

    temp_md.write_text(content)

    # Import to file system
    importer = FileImporter()
    import_result = importer.import_file(
        file_path=str(temp_md),
        brand=brand,
        category=category,
        user_id=user_id
    )

    # Clean up temp file
    temp_md.unlink()

    print(f'\n✅ Voice memo imported:')
    print(f'   Route: {import_result["route"]}')
    print(f'   URL: {import_result.get("url", "N/A")}')

    return {
        **import_result,
        'transcription': result['text'],
        'audio_duration': result.get('duration')
    }


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Whisper Transcriber - Local AI Transcription')
    parser.add_argument('audio', type=str, nargs='?', help='Audio file to transcribe')
    parser.add_argument('--language', type=str, default='en', help='Language code')
    parser.add_argument('--model', type=str, default=WHISPER_MODEL, help='Model size')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps')
    parser.add_argument('--output', type=str, help='Output file path')

    # Voice input integration
    parser.add_argument('--audio-id', type=int, help='Transcribe voice_input ID')
    parser.add_argument('--process-queue', action='store_true', help='Process pending queue')
    parser.add_argument('--limit', type=int, default=10, help='Queue limit')

    # File import integration
    parser.add_argument('--import', action='store_true', dest='import_file', help='Import as @route')
    parser.add_argument('--brand', type=str, help='Brand name')
    parser.add_argument('--category', type=str, help='Category')
    parser.add_argument('--user-id', type=int, default=1, help='User ID')

    args = parser.parse_args()

    try:
        if args.process_queue:
            # Process transcription queue
            results = process_transcription_queue(limit=args.limit, language=args.language)

            print(f'\n📊 Summary:')
            success_count = sum(1 for r in results if r['success'])
            print(f'   Success: {success_count}/{len(results)}')

        elif args.audio_id:
            # Transcribe specific voice input
            result = transcribe_voice_input(args.audio_id, language=args.language)
            print(f'\n✅ Transcription:')
            print(f'   {result["text"][:200]}...')

        elif args.audio:
            # Transcribe file
            transcriber = WhisperTranscriber(model=args.model)

            if args.import_file:
                # Transcribe and import
                if not args.brand or not args.category:
                    print('❌ Error: --brand and --category required for import')
                    exit(1)

                result = transcribe_and_import(
                    args.audio,
                    brand=args.brand,
                    category=args.category,
                    user_id=args.user_id,
                    language=args.language,
                    timestamps=args.timestamps
                )

            elif args.output:
                # Save to file
                result = transcriber.transcribe_and_save(
                    args.audio,
                    output_path=args.output,
                    language=args.language,
                    timestamps=args.timestamps
                )

            else:
                # Just transcribe
                result = transcriber.transcribe(
                    args.audio,
                    language=args.language,
                    timestamps=args.timestamps
                )

                print(f'\n📝 Transcription:')
                print(f'   {result["text"]}')
                print(f'\n📊 Info:')
                print(f'   Language: {result["language"]}')
                print(f'   Backend: {result["backend"]}')
                print(f'   Duration: {result.get("duration", "unknown")}s')

        else:
            # Show help
            print('Whisper Transcriber - Local AI Transcription\n')
            print('Usage:')
            print('  python3 whisper_transcriber.py audio.wav')
            print('  python3 whisper_transcriber.py audio.wav --language es')
            print('  python3 whisper_transcriber.py --process-queue')
            print('  python3 whisper_transcriber.py audio.wav --import --brand me --category voice\n')
            print('Install:')
            print('  pip install openai-whisper\n')

    except Exception as e:
        print(f'\n❌ Error: {e}')
        exit(1)
