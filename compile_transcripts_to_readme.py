#!/usr/bin/env python3
"""
Transcript Compiler → README.md Generator

This is the heart of the 2045 Email System:
- Pulls ALL voice transcripts from soulfra.db
- Groups by domain (CringeProof, Soulfra, DeathToData, CalRiven, StPetePros)
- Generates massive README.md as your "database of transcripts"
- Pushes to github.com/soulfra/soulfra/README.md
- This becomes the canonical knowledge base for the neural network

Why README.md as Database?
- GitHub Pages can read it (no CORS issues)
- Git tracks changes (full history)
- CDN-distributed (fast worldwide access)
- Can be cloned/forked (resilient)
- Free hosting (GitHub's bandwidth)

Usage:
    python3 compile_transcripts_to_readme.py
    python3 compile_transcripts_to_readme.py --push  # Auto-commit to GitHub
"""

import sqlite3
from datetime import datetime
from collections import defaultdict
from brand_router import BRAND_KEYWORDS, detect_brand_from_prediction
import subprocess
import os

def get_all_transcripts():
    """
    Pull all voice transcripts from database

    Returns:
        List of dicts with: id, transcription, created_at, brand
    """
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row

    transcripts = db.execute('''
        SELECT
            id,
            transcription,
            created_at,
            user_id,
            filename
        FROM simple_voice_recordings
        WHERE transcription IS NOT NULL
        AND transcription != ''
        ORDER BY created_at DESC
    ''').fetchall()

    db.close()

    # Detect brand for each transcript
    results = []
    for t in transcripts:
        brand = detect_brand_from_prediction(t['transcription'] or '')
        results.append({
            'id': t['id'],
            'transcription': t['transcription'],
            'created_at': t['created_at'],
            'user_id': t['user_id'],
            'filename': t['filename'],
            'brand': brand
        })

    return results


def group_by_brand(transcripts):
    """Group transcripts by detected brand"""
    grouped = defaultdict(list)

    for t in transcripts:
        grouped[t['brand']].append(t)

    return dict(grouped)


def generate_readme_markdown(transcripts):
    """
    Generate massive README.md from all transcripts

    Format:
    # Soulfra Transcript Database (2024-2045)

    > Your voice memos, compiled across all domains
    > Neural network learns from these patterns to generate new domains
    > Device fingerprint = Your identity across the multiverse

    ## Stats
    - Total Transcripts: 1,234
    - Domains: 5 (CringeProof, Soulfra, DeathToData, CalRiven, StPetePros)
    - Date Range: 2024-01-01 to 2045-12-31

    ## CringeProof Voice Memos
    ...

    ## Soulfra Community Posts
    ...

    etc.
    """
    total = len(transcripts)
    grouped = group_by_brand(transcripts)

    # Calculate date range
    if total > 0:
        dates = sorted([t['created_at'] for t in transcripts])
        start_date = dates[0][:10]
        end_date = dates[-1][:10]
    else:
        start_date = end_date = datetime.now().strftime('%Y-%m-%d')

    md = f"""# Soulfra Transcript Database (2024-2045)

> **Your voice memos, compiled across all domains**
>
> Neural network learns from these patterns to generate new domains
>
> Device fingerprint = Your identity across the multiverse

## 📊 Stats

- **Total Transcripts:** {total:,}
- **Domains:** {len(grouped)} (CringeProof, Soulfra, DeathToData, CalRiven, StPetePros)
- **Date Range:** {start_date} to {end_date}
- **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

## 🎯 Purpose

This README.md is your **persistent knowledge base**:
- Acts as a database (no server needed)
- Trains the neural network (Cal reasoning engine)
- Enables multi-domain email system
- Device fingerprint proves identity
- GitHub Pages serves it worldwide (free CDN)

---

"""

    # Brand descriptions
    brand_info = {
        'cringeproof': {
            'name': '🔥 CringeProof',
            'tagline': 'Call out the cringe, voice your ideas',
            'color': '#ff006e'
        },
        'soulfra': {
            'name': '💜 Soulfra',
            'tagline': 'Building the non-typing internet',
            'color': '#667eea'
        },
        'deathtodata': {
            'name': '🔒 DeathToData',
            'tagline': 'Privacy + Crypto truth',
            'color': '#1a1a1a'
        },
        'calriven': {
            'name': '🏡 CalRiven',
            'tagline': 'Real estate intelligence',
            'color': '#2c5f2d'
        },
        'stpetepros': {
            'name': '🌴 StPetePros',
            'tagline': 'St. Petersburg professional directory',
            'color': '#0ea5e9'
        }
    }

    # Generate sections for each brand
    for brand, transcripts_list in sorted(grouped.items()):
        info = brand_info.get(brand, {'name': brand.title(), 'tagline': '', 'color': '#666'})

        md += f"""## {info['name']}

*{info['tagline']}*

**Transcripts:** {len(transcripts_list)}

<details>
<summary>View All {info['name']} Transcripts ({len(transcripts_list)} total)</summary>

"""

        for t in transcripts_list[:100]:  # Limit to 100 per brand to avoid massive file
            date = t['created_at'][:19] if t['created_at'] else 'Unknown'
            transcript_preview = (t['transcription'][:200] + '...') if len(t['transcription']) > 200 else t['transcription']

            md += f"""### 📝 Recording #{t['id']} - {date}

```
{transcript_preview}
```

---

"""

        if len(transcripts_list) > 100:
            md += f"\n*({len(transcripts_list) - 100} more transcripts not shown - check database)*\n\n"

        md += "</details>\n\n"

    # Footer
    md += f"""---

## 🚀 2045 Email System

This transcript database powers the **multi-domain identity system**:

1. **Device Fingerprint** = Your persistent identity
2. **First-Name-Only Email** = Claim `yourname@cringeproof.com`, `yourname@soulfra.com`, etc.
3. **Neural Network** = Analyzes transcripts, generates new domains
4. **QR Codes** = Login keys across all devices
5. **GitHub README.md** = Your persistent database (no server needed)

## 🧠 Neural Network Training

Cal (reasoning engine) reads these transcripts and:
- Detects patterns in your speech
- Suggests new domains to create
- Routes emails to correct brand
- Learns your communication style
- Generates personalized responses

## 📧 Email Routing Rules

Based on keywords in transcripts:
- Real estate → CalRiven
- Crypto/privacy → DeathToData
- Cringe/ideas → CringeProof
- Community → Soulfra
- Local St. Pete → StPetePros

## 🔮 Built for 2045

This system assumes a future where:
- Everyone claims first-name-only emails across domains
- Voice memos are the primary input method
- AI routing is the norm
- Device fingerprints replace passwords
- GitHub Pages is the universal CDN

---

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Source:** `compile_transcripts_to_readme.py`
**Database:** `soulfra.db`
**Total Records:** {total:,}
"""

    return md


def write_readme(markdown_content, output_path='README.md'):
    """Write README.md to disk"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✅ README.md written to {output_path}")
    print(f"   File size: {len(markdown_content):,} bytes")


def push_to_github(commit_message="Update transcript database from voice memos"):
    """
    Commit and push README.md to GitHub

    Requires:
    - Git repo initialized
    - Remote origin set to github.com/soulfra/soulfra
    """
    try:
        # Check if in git repo
        subprocess.run(['git', 'status'], check=True, capture_output=True)

        # Add README.md
        subprocess.run(['git', 'add', 'README.md'], check=True)

        # Commit
        full_message = f"""{commit_message}

Compiled from soulfra.db voice transcripts
Auto-generated by compile_transcripts_to_readme.py

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
"""
        subprocess.run(['git', 'commit', '-m', full_message], check=True)

        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Pushed to GitHub!")
        print("   View at: https://github.com/soulfra/soulfra/blob/main/README.md")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        print("   Make sure you're in a git repo with remote origin set")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Compile voice transcripts to README.md')
    parser.add_argument('--push', action='store_true', help='Auto-commit and push to GitHub')
    parser.add_argument('--output', default='README.md', help='Output file path')
    args = parser.parse_args()

    print("🎤 Compiling voice transcripts from soulfra.db...")

    # Get all transcripts
    transcripts = get_all_transcripts()
    print(f"   Found {len(transcripts)} transcripts")

    # Generate README
    readme_content = generate_readme_markdown(transcripts)

    # Write to disk
    write_readme(readme_content, args.output)

    # Optionally push to GitHub
    if args.push:
        print("\n📤 Pushing to GitHub...")
        push_to_github()

    print("\n✨ Done!")
    print(f"\nTo push to GitHub later, run:")
    print(f"   python3 compile_transcripts_to_readme.py --push")
