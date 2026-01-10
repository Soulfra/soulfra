#!/usr/bin/env python3
"""
Voice → AI → Repo Pipeline
Record voice memo → Ollama analyzes → Routes to correct domain/repo → Creates component → Pushes to GitHub

Usage:
    python3 voice_to_repo.py --transcript "your voice transcript here"
    python3 voice_to_repo.py --file path/to/transcript.txt
    python3 voice_to_repo.py --interactive  # Talk through mic
"""

import os
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import requests

# Load domain manifest
DOMAINS_FILE = Path(__file__).parent / "domains.json"
with open(DOMAINS_FILE) as f:
    DOMAINS = json.load(f)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.1.87:11434")


def analyze_theme_with_ollama(transcript: str) -> dict:
    """
    Use Ollama to analyze transcript and determine:
    - Which domain it belongs to
    - What type of content (component, story, docs, etc.)
    - Suggested file name
    - Code/content to generate
    """

    domain_themes = "\n".join([
        f"- {name}: {info['theme']}"
        for name, info in DOMAINS['domains'].items()
    ])

    prompt = f"""Analyze this voice transcript and determine:
1. Which domain it belongs to (choose ONE):
{domain_themes}

2. Content type: component, story, documentation, script, or note
3. Suggested filename (lowercase, dashes, with extension)
4. Generate the actual content/code

Transcript: "{transcript}"

Respond ONLY with valid JSON:
{{
  "domain": "domain_name",
  "content_type": "component|story|documentation|script|note",
  "filename": "suggested-filename.ext",
  "content": "the actual generated content here",
  "reasoning": "why this domain and type"
}}"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    response_text = result.get("response", "")

    # Extract JSON from response
    try:
        # Find JSON block in response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        analysis = json.load(json_str) if json_str else {}
    except:
        # Fallback if Ollama returns non-JSON
        analysis = {
            "domain": "soulfra",
            "content_type": "note",
            "filename": f"voice-note-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md",
            "content": f"# Voice Note\n\n{transcript}",
            "reasoning": "Fallback - couldn't parse AI response"
        }

    return analysis


def set_folder_color(folder_path: str, color_tag: str):
    """
    Set macOS Finder color tag on folder

    Colors: Red, Orange, Yellow, Green, Blue, Purple, Pink, Gray
    """
    color_mapping = DOMAINS['finder_colors']
    color_num = color_mapping.get(color_tag, 0)

    applescript = f'''
    tell application "Finder"
        set theFolder to POSIX file "{folder_path}" as alias
        set label index of theFolder to {color_num}
    end tell
    '''

    try:
        subprocess.run(['osascript', '-e', applescript], check=True)
        print(f"✅ Set folder color: {color_tag}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Couldn't set folder color: {e}")


def create_and_push_to_repo(domain_name: str, filename: str, content: str, commit_message: str):
    """
    Create file in local repo → git add → commit → push
    """

    domain_info = DOMAINS['domains'].get(domain_name)
    if not domain_info:
        print(f"❌ Unknown domain: {domain_name}")
        return False

    # Determine local repo path (assumes repos are in ~/Desktop/Soulfra/ or similar)
    # Adjust this path to match your setup
    repo_name = domain_info['repo'].split('/')[-1]
    local_repo_path = Path.home() / "Desktop" / "roommate-chat" / "soulfra-simple" / repo_name

    if not local_repo_path.exists():
        print(f"⚠️  Repo not found locally: {local_repo_path}")
        print(f"   Creating placeholder directory...")
        local_repo_path.mkdir(parents=True, exist_ok=True)

    # Create file
    file_path = local_repo_path / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {file_path}")

    # Set folder color
    set_folder_color(str(local_repo_path), domain_info.get('finder_tag', 'Gray'))

    # Git add, commit, push
    try:
        os.chdir(local_repo_path)

        # Initialize git if needed
        if not (local_repo_path / '.git').exists():
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', f"https://github.com/{domain_info['repo']}.git"], check=False)

        subprocess.run(['git', 'add', filename], check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Ask before pushing
        print(f"\n📤 Ready to push to {domain_info['repo']}")
        push = input("   Push to GitHub? (y/N): ").strip().lower()

        if push == 'y':
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            print(f"✅ Pushed to GitHub: {domain_info['repo']}")
        else:
            print(f"⏸️  Skipped push (committed locally)")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Voice → AI → Repo Pipeline")
    parser.add_argument('--transcript', type=str, help="Voice transcript text")
    parser.add_argument('--file', type=Path, help="Path to transcript file")
    parser.add_argument('--interactive', action='store_true', help="Interactive mode (not implemented yet)")

    args = parser.parse_args()

    # Get transcript
    if args.transcript:
        transcript = args.transcript
    elif args.file:
        with open(args.file) as f:
            transcript = f.read()
    elif args.interactive:
        print("📼 Interactive voice recording not implemented yet")
        print("   Use record-simple.html for now, then run with --file")
        return
    else:
        print("❌ Must provide --transcript, --file, or --interactive")
        parser.print_help()
        return

    print(f"🎤 Transcript: {transcript[:100]}...")

    # Analyze with AI
    print(f"\n🧠 Analyzing with Ollama...")
    analysis = analyze_theme_with_ollama(transcript)

    print(f"\n📊 Analysis:")
    print(f"   Domain: {analysis['domain']}")
    print(f"   Type: {analysis['content_type']}")
    print(f"   File: {analysis['filename']}")
    print(f"   Reasoning: {analysis['reasoning']}")

    # Confirm
    proceed = input(f"\n🚀 Create '{analysis['filename']}' in {analysis['domain']}? (Y/n): ").strip().lower()

    if proceed == 'n':
        print("❌ Cancelled")
        return

    # Create and push
    commit_msg = f"Add {analysis['content_type']}: {analysis['filename']} (from voice memo)"
    success = create_and_push_to_repo(
        analysis['domain'],
        analysis['filename'],
        analysis['content'],
        commit_msg
    )

    if success:
        domain_info = DOMAINS['domains'][analysis['domain']]
        print(f"\n✅ Complete!")
        print(f"   Repo: {domain_info['repo']}")
        print(f"   File: {analysis['filename']}")
        print(f"   Color: {domain_info['finder_tag']}")


if __name__ == '__main__':
    main()
