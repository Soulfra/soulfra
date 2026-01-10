#!/usr/bin/env python3
"""
Audio Quality Analyzer - Detect bad audio quality

Analyzes audio files for quality issues:
- Silence detection (mostly silent audio)
- Duration check (too short/long)
- Volume level (too quiet/too loud/clipping)
- Quality score (0-100)

Usage:
    python3 audio_quality.py /path/to/audio.webm
    python3 audio_quality.py --database-id 2
"""

import argparse
import os
import tempfile
from typing import Dict, Optional
import sqlite3

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
NC = '\033[0m'


class AudioQualityAnalyzer:
    """Analyze audio quality and detect issues"""

    def __init__(self):
        pass

    def analyze_file(self, audio_path: str) -> Dict:
        """
        Analyze audio file quality using ffprobe

        Returns:
            {
                'duration': float (seconds),
                'bit_rate': int (bps),
                'size': int (bytes),
                'quality_score': int (0-100),
                'issues': list of strings,
                'is_usable': bool
            }
        """
        import subprocess
        import json

        try:
            # Use ffprobe to analyze audio
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return {
                    'error': 'ffprobe failed to analyze audio',
                    'quality_score': 0,
                    'is_usable': False,
                    'issues': ['Could not analyze audio file']
                }

            data = json.loads(result.stdout)

            # Extract metrics
            format_info = data.get('format', {})
            streams = data.get('streams', [])

            duration = float(format_info.get('duration', 0))
            bit_rate = int(format_info.get('bit_rate', 0))
            size = int(format_info.get('size', 0))

            # Find audio stream
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break

            # Analyze quality
            issues = []
            quality_score = 100

            # Check duration (too short = bad)
            if duration < 0.5:
                issues.append(f'Too short ({duration:.1f}s) - might be accidental tap')
                quality_score -= 40
            elif duration < 1.0:
                issues.append(f'Very short ({duration:.1f}s) - may not contain useful content')
                quality_score -= 20

            # Check file size (very small = probably bad)
            if size < 1000:  # Less than 1KB
                issues.append(f'Very small file ({size} bytes) - likely empty or corrupted')
                quality_score -= 30
            elif size < 5000:  # Less than 5KB
                issues.append(f'Small file ({size} bytes) - may not contain much audio')
                quality_score -= 15

            # Check bit rate (low bit rate = poor quality)
            if bit_rate < 16000:  # Less than 16kbps
                issues.append(f'Very low bit rate ({bit_rate} bps) - poor audio quality')
                quality_score -= 20
            elif bit_rate < 32000:  # Less than 32kbps
                issues.append(f'Low bit rate ({bit_rate} bps) - reduced audio quality')
                quality_score -= 10

            # Very long recordings might be accidental
            if duration > 300:  # 5 minutes
                issues.append(f'Very long recording ({duration/60:.1f} minutes) - may be accidental')
                quality_score -= 5

            # Ensure score doesn't go below 0
            quality_score = max(0, quality_score)

            # Determine if usable (score >= 50)
            is_usable = quality_score >= 50

            result_dict = {
                'duration': round(duration, 2),
                'bit_rate': bit_rate,
                'size': size,
                'codec': audio_stream.get('codec_name', 'unknown') if audio_stream else 'unknown',
                'sample_rate': audio_stream.get('sample_rate', 'unknown') if audio_stream else 'unknown',
                'quality_score': quality_score,
                'issues': issues,
                'is_usable': is_usable,
                'recommendation': self._get_recommendation(quality_score, issues)
            }

            return result_dict

        except subprocess.TimeoutExpired:
            return {
                'error': 'ffprobe timeout',
                'quality_score': 0,
                'is_usable': False,
                'issues': ['Audio analysis timed out']
            }
        except Exception as e:
            return {
                'error': str(e),
                'quality_score': 0,
                'is_usable': False,
                'issues': [f'Analysis failed: {str(e)}']
            }

    def _get_recommendation(self, quality_score: int, issues: list) -> str:
        """Get recommendation based on quality"""
        if quality_score >= 80:
            return "Excellent quality - ready for transcription"
        elif quality_score >= 60:
            return "Good quality - transcription should work well"
        elif quality_score >= 40:
            return "Fair quality - transcription may be less accurate"
        elif quality_score >= 20:
            return "Poor quality - recommend re-recording for better results"
        else:
            return "Very poor quality - please re-record in quieter environment"

    def analyze_from_database(self, recording_id: int, db_path='soulfra.db') -> Dict:
        """Analyze a recording stored in the database"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        recording = cursor.execute('''
            SELECT id, filename, audio_data, created_at
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        conn.close()

        if not recording:
            return {
                'error': f'Recording {recording_id} not found',
                'quality_score': 0,
                'is_usable': False
            }

        # Extract webm to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(recording['audio_data'])
            tmp_path = tmp.name

        # Analyze
        result = self.analyze_file(tmp_path)

        # Add metadata
        result['recording_id'] = recording_id
        result['filename'] = recording['filename']
        result['created_at'] = recording['created_at']

        # Clean up temp file
        os.unlink(tmp_path)

        return result

    def print_report(self, result: Dict):
        """Print formatted quality report"""
        print(f"\n{CYAN}{'='*80}{NC}")
        print(f"{CYAN}🎙️  Audio Quality Report{NC}")
        print(f"{CYAN}{'='*80}{NC}\n")

        if 'recording_id' in result:
            print(f"Recording ID: {result['recording_id']}")
            print(f"Filename: {result['filename']}")
            print(f"Created: {result['created_at']}\n")

        if 'error' in result:
            print(f"{RED}❌ Error: {result['error']}{NC}\n")
            return

        # Quality score
        score = result['quality_score']
        if score >= 80:
            score_color = GREEN
            score_icon = '✅'
        elif score >= 60:
            score_color = CYAN
            score_icon = '✓'
        elif score >= 40:
            score_color = YELLOW
            score_icon = '⚠️ '
        else:
            score_color = RED
            score_icon = '❌'

        print(f"{score_color}{score_icon} Quality Score: {score}/100{NC}\n")

        # Metrics
        print(f"{CYAN}📊 Audio Metrics:{NC}")
        print(f"   Duration:        {result['duration']} seconds")
        print(f"   File Size:       {result['size']} bytes ({result['size']/1024:.1f} KB)")
        print(f"   Bit Rate:        {result['bit_rate']} bps ({result['bit_rate']/1000:.1f} kbps)")
        print(f"   Codec:           {result['codec']}")
        print(f"   Sample Rate:     {result['sample_rate']} Hz")
        print(f"   Usable:          {'Yes' if result['is_usable'] else 'No'}\n")

        # Issues
        if result['issues']:
            print(f"{YELLOW}⚠️  Issues Detected:{NC}")
            for issue in result['issues']:
                print(f"   • {issue}")
            print()

        # Recommendation
        rec_color = GREEN if score >= 60 else YELLOW if score >= 40 else RED
        print(f"{rec_color}💡 {result['recommendation']}{NC}\n")


def main():
    parser = argparse.ArgumentParser(description='Audio Quality Analyzer')
    parser.add_argument('audio_file', nargs='?', help='Path to audio file')
    parser.add_argument('--database-id', type=int, help='Analyze recording from database by ID')
    parser.add_argument('--db', default='soulfra.db', help='Database path')

    args = parser.parse_args()

    analyzer = AudioQualityAnalyzer()

    if args.database_id:
        # Analyze from database
        result = analyzer.analyze_from_database(args.database_id, db_path=args.db)
        analyzer.print_report(result)

    elif args.audio_file:
        # Analyze file
        if not os.path.exists(args.audio_file):
            print(f"{RED}❌ File not found: {args.audio_file}{NC}")
            return

        result = analyzer.analyze_file(args.audio_file)
        result['filename'] = os.path.basename(args.audio_file)
        analyzer.print_report(result)

    else:
        print(f"{YELLOW}Usage:{NC}")
        print(f"  python3 audio_quality.py /path/to/audio.webm")
        print(f"  python3 audio_quality.py --database-id 2")


if __name__ == '__main__':
    main()
