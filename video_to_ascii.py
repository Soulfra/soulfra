#!/usr/bin/env python3
"""
Video to ASCII Converter - WebM → Terminal Animation

Convert video files (WebM, MP4, etc.) to ASCII art animations.
Syncs with Whisper transcription for word-level timing.

Features:
- Extract frames from WebM/MP4 using ffmpeg
- Convert each frame to ASCII art
- Sync with Whisper word-level timestamps
- Export as: terminal animation, web animation, or re-encoded video
- Play in terminal using ascii_player.py

Usage:
    # Convert video to ASCII frames
    python3 video_to_ascii.py video.webm

    # From database recording
    python3 video_to_ascii.py --from-db 5

    # Convert with word timing
    python3 video_to_ascii.py video.webm --with-words

    # Export as web animation
    python3 video_to_ascii.py video.webm --web-export

    # Play immediately
    python3 video_to_ascii.py video.webm --play

Like:
- Bad Apple!! ASCII animation
- Star Wars ASCII art in telnet
- Matrix digital rain but with your voice memos
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ==============================================================================
# CONFIG
# ==============================================================================

FRAMES_DIR = Path('./ascii_frames')
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# ASCII art settings
DEFAULT_WIDTH = 120  # Terminal width
DEFAULT_CHARSET = 'detailed'  # 'simple', 'detailed', or 'blocks'

# Frame extraction settings
DEFAULT_FPS = 15  # Frames per second (15 is smooth enough for ASCII)


# ==============================================================================
# VIDEO TO ASCII CONVERTER
# ==============================================================================

class VideoToASCII:
    """Convert video files to ASCII art animations"""

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        charset: str = DEFAULT_CHARSET,
        fps: int = DEFAULT_FPS
    ):
        self.width = width
        self.charset = charset
        self.fps = fps

        # Check dependencies
        if not self._check_ffmpeg():
            print("⚠️  Warning: ffmpeg not found. Install: brew install ffmpeg")


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


    def extract_frames(
        self,
        video_path: Path,
        output_dir: Path,
        fps: Optional[int] = None
    ) -> List[Path]:
        """
        Extract frames from video using ffmpeg

        Args:
            video_path: Input video file
            output_dir: Directory to save frames
            fps: Frames per second (None = use default)

        Returns:
            List of frame file paths
        """
        if fps is None:
            fps = self.fps

        print(f"\n🎬 Extracting frames from video...")
        print(f"   Video: {video_path.name}")
        print(f"   FPS: {fps}")
        print(f"   Output: {output_dir}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Frame pattern: frame_0001.png, frame_0002.png, ...
        frame_pattern = output_dir / "frame_%04d.png"

        # FFmpeg command to extract frames
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f'fps={fps}',  # Set frame rate
            '-q:v', '2',  # High quality
            '-y',  # Overwrite
            str(frame_pattern)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Get list of extracted frames
            frames = sorted(output_dir.glob("frame_*.png"))

            print(f"   ✅ Extracted {len(frames)} frames")

            return frames

        except subprocess.CalledProcessError as e:
            print(f"   ❌ Frame extraction failed: {e.stderr}")
            return []


    def frame_to_ascii(self, frame_path: Path) -> str:
        """
        Convert single frame to ASCII art

        Args:
            frame_path: Image frame file

        Returns:
            ASCII art string
        """
        from image_to_ascii import image_to_ascii

        try:
            ascii_art = image_to_ascii(
                str(frame_path),
                width=self.width,
                charset=self.charset
            )
            return ascii_art

        except Exception as e:
            print(f"   ⚠️  Failed to convert {frame_path.name}: {e}")
            return ""


    def convert_video(
        self,
        video_path: Path,
        output_name: Optional[str] = None
    ) -> Dict:
        """
        Convert video to ASCII animation frames

        Args:
            video_path: Input video file
            output_name: Output name (default: video filename)

        Returns:
            {
                'success': bool,
                'frames_dir': Path,
                'frame_count': int,
                'ascii_frames': List[str],
                'fps': int
            }
        """
        if not video_path.exists():
            return {
                'success': False,
                'error': f'Video not found: {video_path}'
            }

        if output_name is None:
            output_name = video_path.stem

        print(f"\n{'='*70}")
        print(f"🎥 VIDEO TO ASCII CONVERSION")
        print(f"{'='*70}")
        print(f"Input: {video_path}")
        print(f"ASCII Width: {self.width} chars")
        print(f"Charset: {self.charset}")
        print(f"FPS: {self.fps}")
        print(f"{'='*70}\n")

        # Create output directory for this video
        frames_dir = FRAMES_DIR / output_name
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract frames
        frame_files = self.extract_frames(video_path, frames_dir / 'png_frames')

        if not frame_files:
            return {
                'success': False,
                'error': 'Failed to extract frames'
            }

        # Step 2: Convert frames to ASCII
        print(f"\n🎨 Converting frames to ASCII...")

        ascii_frames = []
        ascii_frames_dir = frames_dir / 'ascii_frames'
        ascii_frames_dir.mkdir(parents=True, exist_ok=True)

        for i, frame_file in enumerate(frame_files, 1):
            print(f"   [{i}/{len(frame_files)}] {frame_file.name}", end='\r')

            ascii_art = self.frame_to_ascii(frame_file)

            if ascii_art:
                ascii_frames.append(ascii_art)

                # Save ASCII frame as text
                ascii_file = ascii_frames_dir / f"frame_{i:04d}.txt"
                ascii_file.write_text(ascii_art)

        print(f"   ✅ Converted {len(ascii_frames)} frames to ASCII{' '*20}")

        # Save metadata
        metadata = {
            'video_file': str(video_path),
            'frame_count': len(ascii_frames),
            'fps': self.fps,
            'width': self.width,
            'charset': self.charset,
            'created_at': datetime.now().isoformat()
        }

        metadata_file = frames_dir / 'metadata.json'
        metadata_file.write_text(json.dumps(metadata, indent=2))

        print(f"\n{'='*70}")
        print(f"✅ CONVERSION COMPLETE")
        print(f"{'='*70}")
        print(f"Frames: {len(ascii_frames)}")
        print(f"ASCII frames: {ascii_frames_dir}")
        print(f"Metadata: {metadata_file}")
        print(f"{'='*70}\n")

        return {
            'success': True,
            'frames_dir': frames_dir,
            'ascii_frames_dir': ascii_frames_dir,
            'frame_count': len(ascii_frames),
            'ascii_frames': ascii_frames,
            'fps': self.fps,
            'metadata': metadata
        }


    def convert_from_database(
        self,
        recording_id: int,
        with_transcription: bool = False
    ) -> Dict:
        """
        Convert video recording from database

        Args:
            recording_id: Database ID
            with_transcription: Include word-level timing

        Returns:
            Conversion result dict
        """
        from database import get_db

        db = get_db()

        # Get recording
        recording = db.execute('''
            SELECT id, filename, audio_data, transcription
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not recording:
            return {
                'success': False,
                'error': f'Recording #{recording_id} not found'
            }

        print(f"\n📊 Loading recording from database...")
        print(f"   ID: {recording_id}")
        print(f"   Filename: {recording['filename']}")
        print(f"   Size: {len(recording['audio_data']):,} bytes")

        # Extract video data to temp file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(recording['audio_data'])
            tmp_path = Path(tmp.name)

        try:
            # Convert video
            result = self.convert_video(
                tmp_path,
                output_name=f"recording_{recording_id}"
            )

            # Add transcription if available
            if with_transcription and recording['transcription']:
                print(f"\n📝 Adding word-level timing...")
                # TODO: Get word timestamps from Whisper
                result['transcription'] = recording['transcription']

            return result

        finally:
            # Clean up temp file
            tmp_path.unlink()


    def export_web_animation(
        self,
        ascii_frames: List[str],
        output_file: Path,
        fps: Optional[int] = None
    ) -> Path:
        """
        Export as HTML5 web animation

        Args:
            ascii_frames: List of ASCII art frames
            output_file: Output HTML file
            fps: Animation FPS

        Returns:
            Path to HTML file
        """
        if fps is None:
            fps = self.fps

        frame_delay_ms = int(1000 / fps)

        # Create HTML with CSS animation
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ASCII Animation</title>
    <style>
        body {{
            background: #000;
            color: #0f0;
            font-family: 'Courier New', monospace;
            font-size: 8px;
            line-height: 1.0;
            margin: 0;
            padding: 20px;
            overflow: hidden;
        }}

        #animation {{
            white-space: pre;
            text-align: center;
        }}

        .controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 255, 0, 0.1);
            padding: 10px;
            border: 1px solid #0f0;
            border-radius: 5px;
        }}

        button {{
            background: #000;
            color: #0f0;
            border: 1px solid #0f0;
            padding: 5px 15px;
            margin: 0 5px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
        }}

        button:hover {{
            background: #0f0;
            color: #000;
        }}
    </style>
</head>
<body>
    <pre id="animation"></pre>

    <div class="controls">
        <button id="play-pause">▶ Play</button>
        <button id="restart">⟲ Restart</button>
        <span id="frame-counter">Frame: 0 / {len(ascii_frames)}</span>
    </div>

    <script>
        const frames = {json.dumps(ascii_frames)};
        const frameDelay = {frame_delay_ms};

        let currentFrame = 0;
        let playing = false;
        let intervalId = null;

        const animationEl = document.getElementById('animation');
        const playPauseBtn = document.getElementById('play-pause');
        const restartBtn = document.getElementById('restart');
        const counterEl = document.getElementById('frame-counter');

        function showFrame(index) {{
            currentFrame = index % frames.length;
            animationEl.textContent = frames[currentFrame];
            counterEl.textContent = `Frame: ${{currentFrame + 1}} / ${{frames.length}}`;
        }}

        function play() {{
            playing = true;
            playPauseBtn.textContent = '⏸ Pause';

            intervalId = setInterval(() => {{
                currentFrame = (currentFrame + 1) % frames.length;
                showFrame(currentFrame);
            }}, frameDelay);
        }}

        function pause() {{
            playing = false;
            playPauseBtn.textContent = '▶ Play';

            if (intervalId) {{
                clearInterval(intervalId);
                intervalId = null;
            }}
        }}

        function restart() {{
            pause();
            currentFrame = 0;
            showFrame(currentFrame);
        }}

        playPauseBtn.addEventListener('click', () => {{
            if (playing) {{
                pause();
            }} else {{
                play();
            }}
        }});

        restartBtn.addEventListener('click', restart);

        // Show first frame
        showFrame(0);

        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                playing ? pause() : play();
            }} else if (e.code === 'KeyR') {{
                restart();
            }} else if (e.code === 'ArrowLeft') {{
                pause();
                currentFrame = Math.max(0, currentFrame - 1);
                showFrame(currentFrame);
            }} else if (e.code === 'ArrowRight') {{
                pause();
                currentFrame = Math.min(frames.length - 1, currentFrame + 1);
                showFrame(currentFrame);
            }}
        }});
    </script>
</body>
</html>
"""

        output_file.write_text(html_content)

        print(f"✅ Web animation exported: {output_file}")
        print(f"   Open in browser: file://{output_file.absolute()}")

        return output_file


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Video to ASCII Converter - WebM → Terminal Animation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert video
  python3 video_to_ascii.py video.webm

  # From database
  python3 video_to_ascii.py --from-db 5

  # Convert and play
  python3 video_to_ascii.py video.webm --play

  # Export as web animation
  python3 video_to_ascii.py video.webm --web-export
        """
    )

    parser.add_argument(
        'video',
        type=str,
        nargs='?',
        help='Video file to convert'
    )

    parser.add_argument(
        '--from-db',
        type=int,
        metavar='ID',
        help='Convert recording from database by ID'
    )

    parser.add_argument(
        '--with-words',
        action='store_true',
        help='Include word-level timing from transcription'
    )

    parser.add_argument(
        '--web-export',
        action='store_true',
        help='Export as HTML5 web animation'
    )

    parser.add_argument(
        '--play',
        action='store_true',
        help='Play animation in terminal after conversion'
    )

    parser.add_argument(
        '--width',
        type=int,
        default=DEFAULT_WIDTH,
        help=f'ASCII art width (default: {DEFAULT_WIDTH})'
    )

    parser.add_argument(
        '--charset',
        type=str,
        choices=['simple', 'detailed', 'blocks'],
        default=DEFAULT_CHARSET,
        help=f'ASCII character set (default: {DEFAULT_CHARSET})'
    )

    parser.add_argument(
        '--fps',
        type=int,
        default=DEFAULT_FPS,
        help=f'Frames per second (default: {DEFAULT_FPS})'
    )

    args = parser.parse_args()

    # Create converter
    converter = VideoToASCII(
        width=args.width,
        charset=args.charset,
        fps=args.fps
    )

    try:
        # Convert video
        if args.from_db:
            # From database
            result = converter.convert_from_database(
                args.from_db,
                with_transcription=args.with_words
            )

        elif args.video:
            # From file
            video_path = Path(args.video)
            result = converter.convert_video(video_path)

        else:
            parser.print_help()
            return

        if not result['success']:
            print(f"\n❌ Conversion failed: {result.get('error')}")
            sys.exit(1)

        # Export as web animation
        if args.web_export:
            web_file = result['frames_dir'] / 'animation.html'
            converter.export_web_animation(
                result['ascii_frames'],
                web_file,
                fps=result['fps']
            )

        # Play in terminal
        if args.play:
            print(f"\n🎬 Playing ASCII animation...")
            print(f"   Press Space to play, Q to quit\n")

            import time
            time.sleep(2)

            from ascii_player import ascii_player
            ascii_player(result['ascii_frames'], fps=result['fps'])

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
