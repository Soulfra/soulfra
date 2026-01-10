#!/usr/bin/env python3
"""
Audio Enhancer - Voice Isolation & Noise Reduction

Cleans up voice recordings by removing background noise and isolating voice.
Makes recordings "more crisp" for better transcription quality.

**Methods:**
1. FFmpeg filters (fast, no dependencies) - afftdn, highpass, anlmdn
2. ML-based (optional) - noisereduce library with spectral gating

**Features:**
- Remove background noise (furnace, fans, HVAC)
- Isolate voice frequencies (80Hz-8kHz)
- Normalize audio levels
- Batch processing
- Re-transcribe enhanced audio

**Usage:**
```python
from audio_enhancer import AudioEnhancer

enhancer = AudioEnhancer()

# Enhance single file
result = enhancer.enhance('recording.webm')
print(f"Enhanced: {result['output_path']}")

# Batch enhance all recordings
results = enhancer.enhance_all_recordings()
```

**CLI:**
```bash
# Enhance single file
python3 audio_enhancer.py recording.webm

# Enhance all recordings in database
python3 audio_enhancer.py --enhance-all

# Re-transcribe enhanced recordings
python3 audio_enhancer.py --enhance-all --retranscribe

# Use ML-based enhancement (requires noisereduce)
python3 audio_enhancer.py recording.webm --method ml
```

**Installation:**
```bash
# FFmpeg required (already installed)
brew install ffmpeg  # macOS
apt install ffmpeg   # Linux

# Optional ML enhancement
pip install noisereduce scipy librosa
```
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime


# ==============================================================================
# CONFIG
# ==============================================================================

ENHANCED_AUDIO_DIR = Path('./voice_recordings/enhanced')
ENHANCED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# FFmpeg noise reduction settings
NOISE_REDUCTION_LEVEL = 0.2  # 0.0-1.0 (higher = more aggressive)
HIGHPASS_FREQ = 80  # Hz (remove low rumble)
LOWPASS_FREQ = 8000  # Hz (remove high frequency noise)


# ==============================================================================
# AUDIO ENHANCER
# ==============================================================================

class AudioEnhancer:
    """
    Voice isolation and noise reduction for audio recordings
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = ENHANCED_AUDIO_DIR,
        method: str = 'ffmpeg'  # 'ffmpeg' or 'ml'
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.method = method

        # Check ffmpeg availability
        if not self._check_ffmpeg():
            print("⚠️  Warning: ffmpeg not found. Install with: brew install ffmpeg")


    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


    def enhance(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        noise_reduction: float = NOISE_REDUCTION_LEVEL,
        highpass: int = HIGHPASS_FREQ,
        lowpass: int = LOWPASS_FREQ,
        normalize: bool = True
    ) -> Dict:
        """
        Enhance audio file with noise reduction and voice isolation

        Args:
            audio_path: Input audio file
            output_path: Output file (default: auto-generated in enhanced/)
            noise_reduction: Noise reduction level (0.0-1.0)
            highpass: High-pass filter frequency (Hz)
            lowpass: Low-pass filter frequency (Hz)
            normalize: Normalize audio levels

        Returns:
            {
                'success': bool,
                'input_path': str,
                'output_path': str,
                'method': str,
                'duration': float,
                'size_before': int,
                'size_after': int
            }
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            return {
                'success': False,
                'error': f'File not found: {audio_path}'
            }

        # Determine output path
        if output_path is None:
            # Create enhanced filename: original_enhanced.webm
            stem = audio_path.stem
            suffix = audio_path.suffix
            output_path = self.output_dir / f"{stem}_enhanced{suffix}"
        else:
            output_path = Path(output_path)

        print(f"\n🎧 Enhancing: {audio_path.name}")
        print(f"   Method: {self.method}")
        print(f"   Noise reduction: {noise_reduction}")
        print(f"   Frequency range: {highpass}Hz - {lowpass}Hz")

        # Get original file size
        size_before = audio_path.stat().st_size

        # Enhance based on method
        if self.method == 'ml':
            result = self._enhance_ml(
                audio_path,
                output_path,
                noise_reduction
            )
        else:  # ffmpeg
            result = self._enhance_ffmpeg(
                audio_path,
                output_path,
                noise_reduction,
                highpass,
                lowpass,
                normalize
            )

        if result['success']:
            size_after = output_path.stat().st_size
            print(f"   ✅ Enhanced: {output_path.name}")
            print(f"   Size: {size_before:,} → {size_after:,} bytes")

            result.update({
                'input_path': str(audio_path),
                'output_path': str(output_path),
                'size_before': size_before,
                'size_after': size_after
            })
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

        return result


    def _enhance_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        noise_reduction: float,
        highpass: int,
        lowpass: int,
        normalize: bool
    ) -> Dict:
        """
        Enhance using ffmpeg filters

        Filter chain:
        1. afftdn - Adaptive FFT denoiser (removes steady background noise)
        2. highpass - Remove low frequency rumble
        3. lowpass - Remove high frequency noise
        4. loudnorm - Normalize audio levels (optional)
        """
        # Build filter chain
        filters = []

        # 1. Adaptive FFT denoiser (main noise reduction)
        filters.append(f'afftdn=nr={noise_reduction*100}:nf=-25')

        # 2. High-pass filter (remove rumble below 80Hz)
        filters.append(f'highpass=f={highpass}')

        # 3. Low-pass filter (remove noise above 8kHz)
        filters.append(f'lowpass=f={lowpass}')

        # 4. Normalize levels
        if normalize:
            filters.append('loudnorm=I=-16:LRA=11:TP=-1.5')

        filter_complex = ','.join(filters)

        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-af', filter_complex,
            '-ar', '16000',  # 16kHz sample rate (good for voice)
            '-ac', '1',  # Mono (voice doesn't need stereo)
            '-c:a', 'libopus',  # Opus codec (good for voice)
            '-b:a', '24k',  # 24kbps bitrate (sufficient for voice)
            '-y',  # Overwrite output
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'success': True,
                'method': 'ffmpeg',
                'filters': filter_complex
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'ffmpeg failed: {e.stderr}'
            }


    def _enhance_ml(
        self,
        input_path: Path,
        output_path: Path,
        noise_reduction: float
    ) -> Dict:
        """
        Enhance using ML-based noise reduction (noisereduce library)

        This uses spectral gating to analyze noise profile and remove it.
        Better quality than ffmpeg but slower and requires extra dependencies.
        """
        try:
            import librosa
            import soundfile as sf
            import noisereduce as nr
        except ImportError:
            return {
                'success': False,
                'error': 'ML dependencies not installed. Run: pip install noisereduce scipy librosa soundfile'
            }

        try:
            # Load audio
            audio, sr = librosa.load(str(input_path), sr=16000, mono=True)

            # Reduce noise
            # Uses first 1 second as noise profile
            reduced_noise = nr.reduce_noise(
                y=audio,
                sr=sr,
                prop_decrease=noise_reduction,
                stationary=True
            )

            # Save enhanced audio
            sf.write(
                str(output_path),
                reduced_noise,
                sr,
                format='OGG',
                subtype='OPUS'
            )

            return {
                'success': True,
                'method': 'ml',
                'sample_rate': sr
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'ML enhancement failed: {e}'
            }


    def enhance_all_recordings(
        self,
        retranscribe: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        Enhance all recordings in database

        Args:
            retranscribe: Re-transcribe enhanced audio
            **kwargs: Enhancement options (noise_reduction, etc.)

        Returns:
            List of enhancement results
        """
        from database import get_db
        import tempfile

        db = get_db()
        recordings = db.execute('''
            SELECT id, audio_data, filename
            FROM simple_voice_recordings
            WHERE audio_data IS NOT NULL
            ORDER BY id
        ''').fetchall()

        if not recordings:
            print("No recordings found in database")
            return []

        print(f"\n{'='*70}")
        print(f"🎧 BATCH AUDIO ENHANCEMENT")
        print(f"{'='*70}")
        print(f"Found {len(recordings)} recording(s) to enhance\n")

        results = []

        for i, rec in enumerate(recordings, 1):
            recording_id = rec['id']
            audio_data = rec['audio_data']
            filename = rec['filename']

            print(f"[{i}/{len(recordings)}] Processing #{recording_id}: {filename}")

            # Extract audio BLOB to temp file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                # Enhance
                result = self.enhance(tmp_path, **kwargs)
                result['recording_id'] = recording_id
                results.append(result)

                # Re-transcribe if requested
                if retranscribe and result['success']:
                    print(f"   🎤 Re-transcribing enhanced audio...")
                    try:
                        from whisper_transcriber import WhisperTranscriber

                        transcriber = WhisperTranscriber()
                        trans_result = transcriber.transcribe(result['output_path'])

                        # Update database with new transcription
                        db.execute('''
                            UPDATE simple_voice_recordings
                            SET transcription = ?,
                                enhanced_path = ?
                            WHERE id = ?
                        ''', (
                            trans_result['text'],
                            result['output_path'],
                            recording_id
                        ))
                        db.commit()

                        print(f"   ✅ Re-transcribed: {trans_result['text'][:50]}...\n")

                        result['retranscribed'] = True
                        result['new_transcription'] = trans_result['text']

                    except Exception as e:
                        print(f"   ⚠️  Re-transcription failed: {e}\n")
                        result['retranscribed'] = False

            finally:
                # Clean up temp file
                try:
                    Path(tmp_path).unlink()
                except:
                    pass

        # Summary
        print(f"\n{'='*70}")
        print(f"📊 ENHANCEMENT COMPLETE")
        print(f"{'='*70}")

        success_count = sum(1 for r in results if r.get('success'))
        print(f"Successfully enhanced: {success_count}/{len(results)}")

        if retranscribe:
            retrans_count = sum(1 for r in results if r.get('retranscribed'))
            print(f"Re-transcribed: {retrans_count}/{success_count}")

        print(f"{'='*70}\n")

        return results


# ==============================================================================
# DATABASE MIGRATION (Add enhanced_path column)
# ==============================================================================

def migrate_database():
    """Add enhanced_path column to simple_voice_recordings table"""
    from database import get_db

    db = get_db()

    # Check if column exists
    columns = db.execute('''
        PRAGMA table_info(simple_voice_recordings)
    ''').fetchall()

    column_names = [col['name'] for col in columns]

    if 'enhanced_path' not in column_names:
        print("Adding enhanced_path column to database...")
        db.execute('''
            ALTER TABLE simple_voice_recordings
            ADD COLUMN enhanced_path TEXT
        ''')
        db.commit()
        print("✅ Database migration complete")
    else:
        print("✅ Database already up to date")


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Audio Enhancer - Voice Isolation & Noise Reduction'
    )
    parser.add_argument(
        'audio',
        type=str,
        nargs='?',
        help='Audio file to enhance'
    )
    parser.add_argument(
        '--enhance-all',
        action='store_true',
        help='Enhance all recordings in database'
    )
    parser.add_argument(
        '--retranscribe',
        action='store_true',
        help='Re-transcribe enhanced audio (use with --enhance-all)'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['ffmpeg', 'ml'],
        default='ffmpeg',
        help='Enhancement method (ffmpeg or ml)'
    )
    parser.add_argument(
        '--noise-reduction',
        type=float,
        default=NOISE_REDUCTION_LEVEL,
        help=f'Noise reduction level 0.0-1.0 (default: {NOISE_REDUCTION_LEVEL})'
    )
    parser.add_argument(
        '--highpass',
        type=int,
        default=HIGHPASS_FREQ,
        help=f'High-pass filter frequency (default: {HIGHPASS_FREQ}Hz)'
    )
    parser.add_argument(
        '--lowpass',
        type=int,
        default=LOWPASS_FREQ,
        help=f'Low-pass filter frequency (default: {LOWPASS_FREQ}Hz)'
    )
    parser.add_argument(
        '--migrate-db',
        action='store_true',
        help='Add enhanced_path column to database'
    )

    args = parser.parse_args()

    try:
        if args.migrate_db:
            migrate_database()

        elif args.enhance_all:
            # Enhance all recordings
            enhancer = AudioEnhancer(method=args.method)
            results = enhancer.enhance_all_recordings(
                retranscribe=args.retranscribe,
                noise_reduction=args.noise_reduction,
                highpass=args.highpass,
                lowpass=args.lowpass
            )

        elif args.audio:
            # Enhance single file
            enhancer = AudioEnhancer(method=args.method)
            result = enhancer.enhance(
                args.audio,
                noise_reduction=args.noise_reduction,
                highpass=args.highpass,
                lowpass=args.lowpass
            )

            if result['success']:
                print(f"\n✅ Enhanced audio saved to: {result['output_path']}")
            else:
                print(f"\n❌ Enhancement failed: {result.get('error')}")
                exit(1)

        else:
            # Show help
            print("Audio Enhancer - Voice Isolation & Noise Reduction\n")
            print("Usage:")
            print("  python3 audio_enhancer.py recording.webm")
            print("  python3 audio_enhancer.py --enhance-all")
            print("  python3 audio_enhancer.py --enhance-all --retranscribe")
            print("  python3 audio_enhancer.py recording.webm --method ml\n")
            print("First run: python3 audio_enhancer.py --migrate-db\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
