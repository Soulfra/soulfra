#!/usr/bin/env python3
"""
ONE BUTTON VOICE → GITHUB PUBLISHER

Record voice → Ollama enhances → Export to GitHub → Live website

Usage:
    python3 publish_voice.py --id 17              # Publish recording #17
    python3 publish_voice.py --latest             # Publish most recent
    python3 publish_voice.py --id 17 --domain cringeproof  # Force specific domain
"""

import sqlite3
import os
import json
import subprocess
import argparse
import qrcode
import requests
from pathlib import Path
from datetime import datetime


# Configuration
DB_PATH = "soulfra.db"
VOICE_ARCHIVE_PATH = Path("/Users/matthewmauer/Desktop/voice-archive")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.1.87:11434")

# Domain routing rules (Ollama will choose based on content)
DOMAIN_THEMES = {
    'cringeproof': 'Voice predictions, ideas, anonymous creative thoughts, cringe-proof self-expression',
    'soulfra': 'Personal growth, authenticity, vulnerability, community, trust',
    'calriven': 'Data analysis, metrics, proof, game theory, technical discussions',
    'deathtodata': 'Calling out BS, fake systems, corruption, anti-establishment',
    'howtocookathome': 'Cooking tips, recipes, kitchen hacks, simple food advice'
}


def get_recording(recording_id=None, latest=False):
    """Get voice recording from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if latest:
        query = "SELECT * FROM simple_voice_recordings ORDER BY id DESC LIMIT 1"
        rec = conn.execute(query).fetchone()
    else:
        query = "SELECT * FROM simple_voice_recordings WHERE id = ?"
        rec = conn.execute(query, (recording_id,)).fetchone()

    conn.close()

    if not rec:
        raise ValueError(f"Recording not found: {recording_id or 'latest'}")

    return dict(rec)


def enhance_with_ollama(transcript, domain_hint=None):
    """
    Use Ollama to:
    1. Choose domain (if not forced)
    2. Enhance transcript into polished content
    3. Generate README/marketing copy
    """

    domain_list = "\n".join([f"- {k}: {v}" for k, v in DOMAIN_THEMES.items()])

    prompt = f"""You are a content strategist. Analyze this voice transcript and:

1. Choose the best domain for it (unless specified):
{domain_list}

2. Enhance the transcript into polished, engaging content
3. Create a catchy title (5-10 words)
4. Write a one-line summary (max 140 chars - tweetable)
5. Generate full README content in Markdown

Transcript: "{transcript}"

{"Domain MUST be: " + domain_hint if domain_hint else ""}

Respond ONLY with valid JSON:
{{
  "domain": "chosen_domain",
  "title": "Catchy Title Here",
  "summary": "One-line summary (140 chars max)",
  "enhanced_transcript": "Polished version of the transcript",
  "readme_content": "# Full Markdown README content here\\n\\n...",
  "reasoning": "Why this domain and approach"
}}"""

    print(f"\n🤖 Sending to Ollama for enhancement...")

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    result = response.json()
    response_text = result.get("response", "")

    # Extract JSON from response
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        analysis = json.loads(json_str)
    except Exception as e:
        print(f"⚠️  Ollama response parsing failed: {e}")
        print(f"Raw response: {response_text[:500]}")
        # Fallback
        analysis = {
            "domain": domain_hint or "cringeproof",
            "title": transcript[:50] + "...",
            "summary": transcript[:140],
            "enhanced_transcript": transcript,
            "readme_content": f"# Voice Idea\n\n{transcript}",
            "reasoning": "Fallback - Ollama parsing failed"
        }

    return analysis


def generate_qr_code(idea_id, url):
    """Generate QR code for idea"""
    qr_dir = VOICE_ARCHIVE_PATH / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = qr_dir / f"{idea_id}.png"
    img.save(qr_path)

    print(f"📱 QR code generated: {qr_path}")
    return qr_path


def export_audio(recording, idea_id):
    """Export audio file to voice-archive"""
    audio_dir = VOICE_ARCHIVE_PATH / "audio" / str(idea_id)
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension
    filename = recording['filename'] or 'recording.webm'
    ext = '.webm' if filename.endswith('.webm') else '.wav'

    # Export audio
    audio_path = audio_dir / f"recording{ext}"
    with open(audio_path, 'wb') as f:
        f.write(recording['audio_data'])

    # Export metadata
    metadata = {
        'id': idea_id,
        'filename': filename,
        'has_transcription': recording['transcription'] is not None,
        'created_at': recording['created_at'],
        'audio_file': f"recording{ext}"
    }

    metadata_path = audio_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"🎵 Audio exported: {audio_path}")
    return audio_path


def create_idea_page(idea_id, analysis, recording):
    """Create HTML page for idea"""
    ideas_dir = VOICE_ARCHIVE_PATH / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{analysis['title']} | CringeProof</title>
<meta name="description" content="{analysis['summary']}">
<link rel="stylesheet" href="../css/soulfra.css">
<style>
body {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
    padding: 2rem;
}}

.idea-container {{
    max-width: 800px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 3rem;
    border: 2px solid rgba(255, 255, 255, 0.2);
}}

.idea-header {{
    text-align: center;
    margin-bottom: 2rem;
}}

.idea-title {{
    font-size: 2.5rem;
    font-weight: 900;
    margin-bottom: 1rem;
}}

.idea-summary {{
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 2rem;
}}

.idea-meta {{
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
    font-size: 0.9rem;
    opacity: 0.7;
}}

.audio-player {{
    margin: 2rem 0;
    text-align: center;
}}

.audio-player audio {{
    width: 100%;
    max-width: 600px;
}}

.transcript {{
    background: rgba(0, 0, 0, 0.3);
    padding: 2rem;
    border-radius: 12px;
    margin: 2rem 0;
    line-height: 1.8;
}}

.qr-code {{
    text-align: center;
    margin: 2rem 0;
}}

.qr-code img {{
    max-width: 200px;
    border: 8px solid white;
    border-radius: 12px;
}}

.share-buttons {{
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
}}

.share-btn {{
    background: #ff006e;
    color: white;
    padding: 1rem 2rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 900;
    border: 3px solid #000;
    box-shadow: 5px 5px 0 #000;
    transition: all 0.1s;
}}

.share-btn:hover {{
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0 #000;
}}
</style>
</head>
<body>

<nav class="soulfra-nav">
    <div class="soulfra-nav-container">
        <a href="/" class="soulfra-logo">🚫 CringeProof</a>
        <div class="soulfra-links">
            <a href="/wall.html">The Wall</a>
            <a href="/ideas/">All Ideas</a>
            <a href="/voice-recorder.html">🎤 Record</a>
        </div>
    </div>
</nav>

<div class="idea-container">
    <div class="idea-header">
        <h1 class="idea-title">{analysis['title']}</h1>
        <p class="idea-summary">{analysis['summary']}</p>

        <div class="idea-meta">
            <span>💡 Idea #{idea_id}</span>
            <span>🏷️ {analysis['domain']}</span>
            <span>📅 {recording['created_at'][:10]}</span>
        </div>
    </div>

    <div class="audio-player">
        <h3>🎤 Original Voice Recording</h3>
        <audio controls src="/audio/{idea_id}/recording.webm">
            Your browser does not support audio playback.
        </audio>
    </div>

    <div class="transcript">
        <h3>📝 Enhanced Version</h3>
        <p>{analysis['enhanced_transcript']}</p>
    </div>

    <div class="qr-code">
        <h3>📱 Share This Idea</h3>
        <img src="/qr/{idea_id}.png" alt="QR Code">
        <p style="margin-top: 1rem; opacity: 0.8;">
            Scan to share this idea with others
        </p>
    </div>

    <div class="share-buttons">
        <a href="https://twitter.com/intent/tweet?text={analysis['summary']}&url=https://cringeproof.com/ideas/{idea_id}.html" class="share-btn">
            🐦 Tweet
        </a>
        <a href="mailto:?subject={analysis['title']}&body={analysis['summary']}%0A%0Ahttps://cringeproof.com/ideas/{idea_id}.html" class="share-btn">
            ✉️ Email
        </a>
        <a href="#" onclick="navigator.clipboard.writeText(window.location.href); this.textContent='✅ Copied!'; return false;" class="share-btn">
            📋 Copy Link
        </a>
    </div>
</div>

</body>
</html>"""

    page_path = ideas_dir / f"{idea_id}.html"
    with open(page_path, 'w') as f:
        f.write(page_html)

    print(f"📄 Idea page created: {page_path}")
    return page_path


def create_readme(analysis, idea_id):
    """Create README.md for the idea"""
    readme_path = VOICE_ARCHIVE_PATH / "ideas" / f"README-{idea_id}.md"

    with open(readme_path, 'w') as f:
        f.write(analysis['readme_content'])

    print(f"📖 README created: {readme_path}")
    return readme_path


def git_publish():
    """Git commit and push to GitHub"""
    os.chdir(VOICE_ARCHIVE_PATH)

    print("\n📤 Publishing to GitHub...")

    # Git add all changes
    subprocess.run(["git", "add", "."], check=True)

    # Commit with message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run([
        "git", "commit", "-m",
        f"🎤 Published voice idea - {timestamp}\n\n🤖 Generated with Ollama\nCo-Authored-By: Claude <noreply@anthropic.com>"
    ], check=False)  # Don't fail if nothing to commit

    # Push to GitHub
    result = subprocess.run(["git", "push"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Successfully pushed to GitHub Pages!")
    else:
        print(f"⚠️  Git push warning: {result.stderr}")

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="ONE BUTTON: Voice → GitHub Publisher")
    parser.add_argument("--id", type=int, help="Recording ID to publish")
    parser.add_argument("--latest", action="store_true", help="Publish most recent recording")
    parser.add_argument("--domain", help="Force specific domain (overrides Ollama routing)")

    args = parser.parse_args()

    if not args.id and not args.latest:
        parser.error("Must specify --id or --latest")

    print("🎙️  ONE BUTTON VOICE → GITHUB PUBLISHER")
    print("=" * 60)

    # Step 1: Get recording
    print("\n📥 Fetching recording from database...")
    recording = get_recording(recording_id=args.id, latest=args.latest)
    idea_id = recording['id']
    transcript = recording['transcription']

    if not transcript:
        print("❌ Error: No transcription available for this recording")
        return

    print(f"✅ Recording #{idea_id} loaded")
    print(f"   Transcript preview: {transcript[:100]}...")

    # Step 2: Enhance with Ollama
    analysis = enhance_with_ollama(transcript, domain_hint=args.domain)

    print(f"\n🎯 Ollama Routing:")
    print(f"   Domain: {analysis['domain']}")
    print(f"   Title: {analysis['title']}")
    print(f"   Summary: {analysis['summary']}")

    # Step 3: Export audio
    export_audio(recording, idea_id)

    # Step 4: Generate QR code
    idea_url = f"https://cringeproof.com/ideas/{idea_id}.html"
    generate_qr_code(idea_id, idea_url)

    # Step 5: Create idea page
    create_idea_page(idea_id, analysis, recording)

    # Step 6: Create README
    create_readme(analysis, idea_id)

    # Step 7: Update manifest
    manifest_path = VOICE_ARCHIVE_PATH / "audio" / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"recordings": []}

    # Add or update this recording
    existing = next((r for r in manifest['recordings'] if r['id'] == idea_id), None)
    if not existing:
        manifest['recordings'].append({
            'id': idea_id,
            'size': len(recording['audio_data']),
            'published_at': datetime.now().isoformat()
        })

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"📋 Manifest updated")

    # Step 8: Git publish
    if git_publish():
        print(f"\n🎉 SUCCESS! Idea published:")
        print(f"   🌐 Live URL: {idea_url}")
        print(f"   📱 QR Code: /voice-archive/qr/{idea_id}.png")
        print(f"   🎵 Audio: /voice-archive/audio/{idea_id}/")
    else:
        print(f"\n⚠️  Files created locally, but git push had issues")
        print(f"   Check /voice-archive/ directory")


if __name__ == "__main__":
    main()
