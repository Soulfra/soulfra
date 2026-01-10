#!/usr/bin/env python3
"""
Add Audio Page to CringeProof

Creates a new audio page with HTML5 player for GitHub Pages

Usage:
    python add_audio_page.py my_audio.wav "Recording Title" "Transcription text here"
    python add_audio_page.py recording.webm "My Idea" "This is what I said in the recording"

Output:
    - Creates /voice-archive/audio/N/index.html
    - Copies audio file to /voice-archive/audio/N/recording.{ext}
    - Ready to git push to cringeproof.com
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

VOICE_ARCHIVE_DIR = Path(__file__).parent.parent / "github-repos" / "voice-archive"
AUDIO_DIR = VOICE_ARCHIVE_DIR / "audio"

def get_next_audio_number():
    """Find the next available audio number"""
    if not AUDIO_DIR.exists():
        return 1

    existing = [
        int(d.name) for d in AUDIO_DIR.iterdir()
        if d.is_dir() and d.name.isdigit()
    ]

    return max(existing) + 1 if existing else 1


def create_audio_page(audio_file, title, transcription):
    """
    Create a new audio page

    Args:
        audio_file: Path to audio file (wav, webm, mp3, m4a)
        title: Title for the page
        transcription: Transcription text
    """
    audio_path = Path(audio_file)

    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False

    # Get file extension and MIME type
    ext = audio_path.suffix.lower()
    mime_types = {
        '.wav': 'audio/wav',
        '.webm': 'audio/webm',
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg'
    }

    if ext not in mime_types:
        print(f"❌ Unsupported audio format: {ext}")
        print(f"   Supported: {', '.join(mime_types.keys())}")
        return False

    mime_type = mime_types[ext]

    # Get next audio number
    audio_num = get_next_audio_number()
    output_dir = AUDIO_DIR / str(audio_num)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy audio file
    dest_audio = output_dir / f"recording{ext}"
    shutil.copy2(audio_path, dest_audio)

    # Create HTML page
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - CringeProof</title>
<meta name="description" content="Voice recording: {title}">
<link rel="stylesheet" href="../../css/soulfra.css">
</head>
<body>
<nav class="soulfra-nav">
    <div class="soulfra-nav-container">
        <a href="https://cringeproof.com/" class="soulfra-logo">
            🚫 CringeProof
        </a>

        <div class="soulfra-links">
            <a href="https://cringeproof.com/ideas/">💡 Ideas</a>
            <a href="https://cringeproof.com/">🎤 Voice Archive</a>
            <a href="https://cringeproof.com/record-simple.html" class="soulfra-record-btn">🎙️ Record</a>
        </div>
    </div>
</nav>

<div class="container">

<header>
    <h1>🎤 {title}</h1>
    <p class="subtitle">Recorded: {datetime.now().strftime("%B %d, %Y")}</p>
</header>

<style>
.transcription-box {{
    background: #fff;
    border: 5px solid #000;
    border-radius: 8px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: 8px 8px 0 #000;
}}

.transcription-box h2 {{
    font-size: 1.5rem;
    font-weight: 900;
    margin-bottom: 1rem;
    text-transform: uppercase;
    color: #ff006e;
}}

.transcription-text {{
    line-height: 1.8;
    font-size: 1.1rem;
    color: #333;
}}

audio {{
    width: 100%;
    margin-bottom: 1.5rem;
    border: 3px solid #000;
    border-radius: 4px;
}}
</style>

<div class="transcription-box">
    <h2>🎤 Listen to Recording</h2>
    <audio controls preload="metadata">
        <source src="recording{ext}" type="{mime_type}">
        Your browser does not support the audio element.
    </audio>

    <h2>📝 Transcription</h2>
    <p class="transcription-text">{transcription}</p>
</div>

<div class="meta-links">
    <a href="https://cringeproof.com/" style="color: #ff006e; font-weight: 700;">← Back to Archive</a>
    <a href="https://cringeproof.com/record-simple.html" style="color: #ff006e; font-weight: 700;">🎙️ Record Your Own</a>
</div>

</div>

<footer style="text-align: center; padding: 2rem; opacity: 0.7; margin-top: 4rem;">
    <p><strong>CringeProof</strong> - Voice ideas without the performance anxiety</p>
    <p style="margin-top: 0.5rem;">
        <a href="https://cringeproof.com/">Home</a> |
        <a href="https://cringeproof.com/ideas/">Ideas</a> |
        <a href="https://github.com/Soulfra/voice-archive">GitHub</a>
    </p>
</footer>
</body>
</html>
'''

    # Write HTML file
    html_file = output_dir / "index.html"
    html_file.write_text(html)

    # Success
    print(f"\n✅ Created audio page #{audio_num}")
    print(f"   📁 Location: {output_dir}")
    print(f"   🎵 Audio: recording{ext}")
    print(f"   📄 HTML: index.html")
    print(f"\n🌐 URL: https://cringeproof.com/audio/{audio_num}/")
    print(f"\n📤 Next steps:")
    print(f"   cd voice-archive")
    print(f"   git add audio/{audio_num}/")
    print(f"   git commit -m \"Add audio recording #{audio_num}: {title}\"")
    print(f"   git push")

    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python add_audio_page.py <audio_file> <title> [transcription]")
        print("\nExample:")
        print('  python add_audio_page.py my_recording.wav "My Great Idea" "This is the transcription"')
        sys.exit(1)

    audio_file = sys.argv[1]
    title = sys.argv[2]
    transcription = sys.argv[3] if len(sys.argv) > 3 else "Transcription not available yet."

    success = create_audio_page(audio_file, title, transcription)

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
