#!/usr/bin/env python3
"""
Voice Audio Cleaner - Remove background noise and isolate voice frequencies
Uses FFmpeg filters (no AI needed, fast, works on any audio)
"""

import subprocess
import tempfile
import os

def clean_audio(input_path, output_path=None, mode='balanced'):
    """
    Clean audio file using FFmpeg filters

    Args:
        input_path: Path to input audio file
        output_path: Path for cleaned output (auto-generated if None)
        mode: 'light', 'balanced', or 'aggressive'

    Returns:
        Path to cleaned audio file
    """

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"

    # Filter configurations
    filters = {
        'light': [
            'afftdn=nf=-15',  # Light noise reduction
            'highpass=f=100',  # Remove very low frequencies
            'lowpass=f=3500'   # Remove very high frequencies
        ],
        'balanced': [
            'afftdn=nf=-25',   # Moderate noise reduction
            'highpass=f=85',   # Human voice lower bound
            'lowpass=f=255',   # Human voice upper bound
            'volume=1.5'       # Slight volume boost
        ],
        'aggressive': [
            'afftdn=nf=-40',   # Heavy noise reduction
            'highpass=f=200',  # Aggressive low cut
            'lowpass=f=3000',  # Aggressive high cut
            'volume=2.0',      # Volume boost
            'anlmdn=s=10'      # Additional noise reduction
        ]
    }

    filter_chain = ','.join(filters.get(mode, filters['balanced']))

    # Run FFmpeg
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', filter_chain,
        '-y',  # Overwrite output
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✅ Audio cleaned: {output_path}")
            return output_path
        else:
            print(f"❌ FFmpeg failed: {result.stderr.decode()}")
            return None

    except subprocess.TimeoutExpired:
        print("⚠️  FFmpeg timeout (file too large?)")
        return None
    except Exception as e:
        print(f"⚠️  Error cleaning audio: {e}")
        return None


def extract_voice_only(input_path, output_path=None):
    """
    Extract ONLY voice frequencies (85-255 Hz typical human speech)
    Removes music, background noise, everything except voice
    """

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_voice_only{ext}"

    # Aggressive voice-only filter
    filter_chain = ','.join([
        'afftdn=nf=-30',       # Remove background noise
        'highpass=f=85',       # Human voice lower bound
        'lowpass=f=255',       # Human voice upper bound
        'bandpass=f=150:w=100',# Focus on primary speech frequency
        'volume=3.0',          # Boost volume (lost in filtering)
        'compand'              # Compress dynamic range
    ])

    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', filter_chain,
        '-y',
        output_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode == 0:
            print(f"✅ Voice extracted: {output_path}")
            return output_path
        else:
            print(f"❌ Voice extraction failed")
            return None
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return None


def analyze_audio(audio_path):
    """
    Analyze audio file to detect noise levels, voice presence, etc.
    Returns dict with audio stats
    """

    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration,size,bit_rate',
        '-show_entries', 'stream=codec_name,sample_rate,channels',
        '-of', 'json',
        audio_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout.decode())
            return data
        return None
    except Exception as e:
        print(f"⚠️  Audio analysis failed: {e}")
        return None


if __name__ == '__main__':
    # Test with recording 11
    test_file = '/tmp/recording_11.webm'

    if os.path.exists(test_file):
        print("🎤 Testing voice cleaner on recording_11.webm...")

        # Analyze original
        stats = analyze_audio(test_file)
        if stats:
            print(f"📊 Original audio: {stats}")

        # Clean with different modes
        clean_audio(test_file, '/tmp/recording_11_light.webm', mode='light')
        clean_audio(test_file, '/tmp/recording_11_balanced.webm', mode='balanced')
        clean_audio(test_file, '/tmp/recording_11_aggressive.webm', mode='aggressive')

        # Extract voice only
        extract_voice_only(test_file, '/tmp/recording_11_voice_only.webm')

        print("\n✅ Test complete! Listen to the cleaned versions:")
        print("   - /tmp/recording_11_light.webm (subtle)")
        print("   - /tmp/recording_11_balanced.webm (recommended)")
        print("   - /tmp/recording_11_aggressive.webm (heavy filtering)")
        print("   - /tmp/recording_11_voice_only.webm (ONLY voice frequencies)")
    else:
        print(f"❌ Test file not found: {test_file}")
        print("   Run this after extracting audio from database")
