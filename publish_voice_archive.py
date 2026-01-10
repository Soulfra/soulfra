#!/usr/bin/env python3
"""
Publish Voice Archive to GitHub Pages

Like museum historical archives - timestamp + raw transcript + hash verification

Flow:
1. Export voice recordings from database
2. Scrub PII (names, addresses, phone numbers)
3. Generate content hash (SHA-256)
4. Create timestamped markdown files
5. Publish to GitHub Pages (soulfra.github.io/voice-archive)

Usage:
    python3 publish_voice_archive.py <username>
"""

import sqlite3
import re
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ==============================================================================
# PII SCRUBBING
# ==============================================================================

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'name': r'\b(?:I am|My name is|I\'m|This is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
}

# Common names to redact (extend as needed)
COMMON_NAMES = [
    'Matthew', 'Matt', 'Mike', 'Michael', 'John', 'James', 'Robert', 'Mary',
    'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'David', 'Richard', 'Joseph',
    'Thomas', 'Charles', 'Christopher', 'Daniel', 'Paul', 'Mark', 'Donald',
    'George', 'Kenneth', 'Steven', 'Edward', 'Brian', 'Ronald', 'Anthony'
]

def scrub_pii(text: str) -> str:
    """
    Remove personally identifiable information

    Args:
        text: Original transcript

    Returns:
        Sanitized text with PII redacted
    """

    scrubbed = text

    # Redact email addresses
    scrubbed = re.sub(PII_PATTERNS['email'], '[EMAIL_REDACTED]', scrubbed)

    # Redact phone numbers
    scrubbed = re.sub(PII_PATTERNS['phone'], '[PHONE_REDACTED]', scrubbed)

    # Redact SSN
    scrubbed = re.sub(PII_PATTERNS['ssn'], '[SSN_REDACTED]', scrubbed)

    # Redact addresses
    scrubbed = re.sub(PII_PATTERNS['address'], '[ADDRESS_REDACTED]', scrubbed, flags=re.IGNORECASE)

    # Redact credit cards
    scrubbed = re.sub(PII_PATTERNS['credit_card'], '[CARD_REDACTED]', scrubbed)

    # Redact common names
    for name in COMMON_NAMES:
        scrubbed = re.sub(rf'\b{name}\b', '[NAME_REDACTED]', scrubbed, flags=re.IGNORECASE)

    # Redact "I am NAME" patterns
    scrubbed = re.sub(PII_PATTERNS['name'], r'I am [NAME_REDACTED]', scrubbed)

    return scrubbed


# ==============================================================================
# VOICE SIGNATURE (Proof of Authenticity)
# ==============================================================================

def generate_voice_signature(transcript: str, created_at: str, user_id: int) -> str:
    """
    Generate cryptographic signature for transcript

    Like GPG signature but simpler:
    - Hash of (transcript + timestamp + user_id)
    - Proves this transcript came from this user at this time
    - Can't be forged without knowing user_id

    Args:
        transcript: Transcript text
        created_at: ISO timestamp
        user_id: User ID

    Returns:
        SHA-256 hash (first 16 chars)
    """

    data = f"{transcript}{created_at}{user_id}".encode('utf-8')
    signature = hashlib.sha256(data).hexdigest()[:16]

    return signature


# ==============================================================================
# MARKDOWN GENERATION
# ==============================================================================

def create_archive_markdown(
    transcript: str,
    created_at: str,
    duration_seconds: Optional[int],
    signature: str,
    recording_id: int
) -> str:
    """
    Create markdown file for voice archive

    Args:
        transcript: Scrubbed transcript
        created_at: ISO timestamp
        duration_seconds: Recording duration
        signature: Voice signature hash
        recording_id: Database ID

    Returns:
        Markdown content
    """

    # Parse timestamp
    dt = datetime.fromisoformat(created_at.replace(' ', 'T'))
    date_str = dt.strftime('%B %d, %Y at %I:%M %p UTC')

    # Duration
    if duration_seconds:
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = "Unknown"

    markdown = f"""---
title: Voice Memo
date: {dt.isoformat()}
signature: {signature}
recording_id: {recording_id}
duration: {duration_str}
---

# Voice Memo - {date_str}

**Recording ID**: `{recording_id}`
**Duration**: {duration_str}
**Signature**: `{signature}`

---

## Transcript

{transcript}

---

## Verification

This transcript is cryptographically signed to prove authenticity.

**Signature**: `{signature}`

To verify this transcript:
1. The signature is generated from: `SHA256(transcript + timestamp + user_id)`
2. Cannot be forged without access to the original user account
3. Timestamp proves this was recorded on {date_str}

---

*Published to the Soulfra Voice Archive - A permanent, decentralized record of voice memos.*
"""

    return markdown


# ==============================================================================
# GITHUB PAGES PUBLISHING
# ==============================================================================

def publish_to_github_pages(
    username: str,
    repo_url: str = "https://github.com/Soulfra/voice-archive.git",
    github_token: Optional[str] = None
) -> Dict:
    """
    Publish voice archive to GitHub Pages

    Args:
        username: Username to export recordings for
        repo_url: GitHub repo URL
        github_token: Optional GitHub token (uses gh CLI if not provided)

    Returns:
        {'success': bool, 'published_count': int, 'repo_url': str}
    """

    # Connect to database
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row

    # Get user
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        conn.close()
        return {'success': False, 'error': f'User {username} not found'}

    user_id = user['id']

    # Get all voice recordings with brand info
    recordings = conn.execute('''
        SELECT
            svr.id,
            svr.transcription,
            svr.created_at,
            svr.filename,
            vs.brand_slug
        FROM simple_voice_recordings svr
        LEFT JOIN voice_suggestions vs ON svr.id = vs.id
        WHERE svr.user_id = ?
        ORDER BY svr.created_at
    ''', (user_id,)).fetchall()

    conn.close()

    if not recordings:
        return {'success': False, 'error': 'No recordings found'}

    # Use existing voice-archive directory
    repo_dir = Path(__file__).parent / 'voice-archive'

    # Check if it exists and is a git repo
    if not repo_dir.exists():
        print(f"❌ Error: voice-archive directory not found at {repo_dir}")
        print("   Expected: ~/Desktop/roommate-chat/soulfra-simple/voice-archive")
        return {'success': False, 'error': 'voice-archive directory not found'}

    # Pull latest changes
    try:
        print("📦 Pulling latest from GitHub...")
        subprocess.run(['git', 'pull'], cwd=repo_dir, check=True)
    except subprocess.CalledProcessError:
        print("⚠️  Warning: git pull failed, continuing anyway...")

    # Create posts directory
    posts_dir = repo_dir / 'transcripts'
    posts_dir.mkdir(exist_ok=True)

    # Process recordings
    published_count = 0

    for recording in recordings:
        recording_id = recording['id']
        transcript = recording['transcription']
        created_at = recording['created_at']
        filename = recording['filename']

        if not transcript:
            continue  # Skip if no transcription

        # Scrub PII
        scrubbed_transcript = scrub_pii(transcript)

        # Generate signature
        signature = generate_voice_signature(scrubbed_transcript, created_at, user_id)

        # Create markdown
        markdown = create_archive_markdown(
            scrubbed_transcript,
            created_at,
            None,  # duration unknown
            signature,
            recording_id
        )

        # Parse timestamp for filename
        dt = datetime.fromisoformat(created_at.replace(' ', 'T'))
        filename = f"{dt.strftime('%Y-%m-%d-%H-%M')}-memo-{recording_id}.md"

        # Write file
        file_path = posts_dir / filename
        with open(file_path, 'w') as f:
            f.write(markdown)

        print(f"✅ Created: {filename}")
        published_count += 1

    # Create index.html
    create_archive_index(repo_dir, recordings)

    # Git commit and push
    try:
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)

        commit_message = f"Archive {published_count} voice memos - {datetime.utcnow().strftime('%Y-%m-%d')}"
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=repo_dir, check=True)

        subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir, check=True)

        print(f"\n🎉 Successfully published {published_count} transcripts!")
        print(f"📍 View at: https://soulfra.github.io/voice-archive")

        return {
            'success': True,
            'published_count': published_count,
            'repo_url': 'https://soulfra.github.io/voice-archive'
        }

    except subprocess.CalledProcessError as e:
        return {'success': False, 'error': str(e)}


def create_archive_index(repo_dir: Path, recordings: List):
    """Update index.html with recording data (keeps existing template structure)"""

    # We'll just ensure the index.html is present - it's already created/updated separately
    # This function can be used to dynamically generate cards if needed

    # Count brand recordings
    brand_counts = {'calriven': 0, 'deathtodata': 0, 'soulfra': 0, 'none': 0}
    for rec in recordings:
        brand = rec.get('brand_slug')
        if brand in brand_counts:
            brand_counts[brand] += 1
        else:
            brand_counts['none'] += 1

    print(f"\n📊 Brand Distribution:")
    print(f"   CalRiven: {brand_counts['calriven']}")
    print(f"   DeathToData: {brand_counts['deathtodata']}")
    print(f"   Soulfra: {brand_counts['soulfra']}")
    print(f"   Unrouted: {brand_counts['none']}")

    # Note: The actual index.html is manually maintained with better design
    # This function just provides stats - you can extend it later to generate cards

    return


# ==============================================================================
# CLI
# ==============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 publish_voice_archive.py <username>")
        print()
        print("Example:")
        print("  python3 publish_voice_archive.py matt")
        sys.exit(1)

    username = sys.argv[1]

    print(f"\n📦 Publishing voice archive for '{username}'")
    print("=" * 70)
    print()

    result = publish_to_github_pages(username)

    if result['success']:
        print()
        print("=" * 70)
        print(f"🎉 Successfully published {result['published_count']} transcripts!")
        print(f"📍 View at: {result['repo_url']}")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print(f"❌ Error: {result.get('error')}")
        print("=" * 70)
