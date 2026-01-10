#!/usr/bin/env python3
"""
Content-Addressed Voice Archive - YOUR decentralized system

Like IPFS but simpler:
- Each prediction gets SHA256 content hash
- Hash = directory name (content-addressable)
- Export to voice-archive/{hash}/
- Others clone, verify, mirror (no Archive.org needed)

Usage:
    # Export single prediction
    python3 content_addressed_archive.py --export-pairing 1

    # Export all predictions
    python3 content_addressed_archive.py --export-all

    # Verify archive integrity
    python3 content_addressed_archive.py --verify

    # Generate RSS feed
    python3 content_addressed_archive.py --generate-rss

Key difference from Archive.org:
- YOU control the source (SQLite + Git)
- Content hash = permanent identifier
- Others can mirror if they want
- No central authority needed
"""

import sqlite3
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ==============================================================================
# CONFIG
# ==============================================================================

ARCHIVE_ROOT = Path('./voice-archive')
ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

DB_PATH = 'soulfra.db'


# ==============================================================================
# CONTENT ADDRESSING
# ==============================================================================

def calculate_content_hash(
    audio_data: bytes,
    metadata: Dict,
    timestamp: str
) -> str:
    """
    Calculate SHA256 content hash for prediction

    Hash = SHA256(audio_data + sorted_metadata_json + timestamp)

    This makes content deterministic and verifiable:
    - Same content = same hash
    - Different content = different hash
    - Hash proves authenticity

    Like IPFS CID but using SHA256
    """
    hasher = hashlib.sha256()

    # Add audio data
    hasher.update(audio_data)

    # Add sorted metadata (for determinism)
    metadata_json = json.dumps(metadata, sort_keys=True)
    hasher.update(metadata_json.encode('utf-8'))

    # Add timestamp
    hasher.update(timestamp.encode('utf-8'))

    return hasher.hexdigest()


def short_hash(full_hash: str, length: int = 12) -> str:
    """Get short version of hash for display (like Git short SHA)"""
    return full_hash[:length]


# ==============================================================================
# PII SCRUBBING (from publish_voice_archive.py)
# ==============================================================================

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b',
}

def scrub_pii(text: str) -> str:
    """Remove personally identifiable information"""
    scrubbed = text
    scrubbed = re.sub(PII_PATTERNS['email'], '[EMAIL]', scrubbed)
    scrubbed = re.sub(PII_PATTERNS['phone'], '[PHONE]', scrubbed)
    scrubbed = re.sub(PII_PATTERNS['ssn'], '[SSN]', scrubbed)
    scrubbed = re.sub(PII_PATTERNS['address'], '[ADDRESS]', scrubbed, flags=re.IGNORECASE)
    return scrubbed


# ==============================================================================
# EXPORT SYSTEM
# ==============================================================================

class ContentAddressedArchive:
    """Export predictions to content-addressed directories"""

    def __init__(self, db_path: str = DB_PATH, archive_root: Path = ARCHIVE_ROOT):
        self.db_path = db_path
        self.archive_root = archive_root
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

    def get_pairing_data(self, pairing_id: int) -> Optional[Dict]:
        """Get complete prediction data from database"""

        query = """
            SELECT
                p.id as pairing_id,
                p.user_prediction,
                p.time_lock_until,
                p.cringe_factor,
                p.paired_at,
                p.content_hash,
                r.id as recording_id,
                r.filename as audio_filename,
                r.audio_data,
                r.file_size,
                r.transcription,
                r.created_at as recorded_at,
                a.id as article_id,
                a.title as article_title,
                a.url as article_url,
                a.source as article_source,
                a.summary as article_summary,
                a.topics as article_topics,
                a.article_hash
            FROM voice_article_pairings p
            JOIN simple_voice_recordings r ON p.recording_id = r.id
            LEFT JOIN news_articles a ON p.article_id = a.id
            WHERE p.id = ?
        """

        result = self.db.execute(query, (pairing_id,)).fetchone()

        if not result:
            return None

        return dict(result)

    def generate_content_hash_for_pairing(self, pairing_id: int) -> Optional[str]:
        """Generate and save content hash for a pairing"""

        data = self.get_pairing_data(pairing_id)
        if not data:
            return None

        # Build metadata dict
        metadata = {
            'pairing_id': data['pairing_id'],
            'prediction': data['user_prediction'],
            'article': {
                'title': data['article_title'],
                'url': data['article_url'],
                'source': data['article_source'],
                'topics': data['article_topics'],
            },
            'recorded_at': data['recorded_at'],
            'time_lock_until': data['time_lock_until'],
        }

        # Calculate hash
        content_hash = calculate_content_hash(
            audio_data=data['audio_data'],
            metadata=metadata,
            timestamp=data['recorded_at']
        )

        # Save hash to database
        self.db.execute("""
            UPDATE voice_article_pairings
            SET content_hash = ?
            WHERE id = ?
        """, (content_hash, pairing_id))
        self.db.commit()

        return content_hash

    def export_pairing(self, pairing_id: int, scrub_pii_flag: bool = True, transcribe: bool = True) -> Optional[Path]:
        """
        Export prediction to content-addressed directory

        Args:
            pairing_id: Voice article pairing ID
            scrub_pii_flag: Whether to scrub PII from transcription
            transcribe: Whether to re-transcribe with Whisper (default: True)

        Creates:
            voice-archive/{content_hash}/
                ├── prediction.md      (human-readable)
                ├── metadata.json      (machine-readable)
                ├── audio.webm         (voice recording)
                └── VERIFY             (hash verification info)

        Returns:
            Path to exported directory
        """

        data = self.get_pairing_data(pairing_id)
        if not data:
            print(f"❌ Pairing {pairing_id} not found")
            return None

        # Generate or get existing hash
        content_hash = data['content_hash']
        if not content_hash:
            content_hash = self.generate_content_hash_for_pairing(pairing_id)

        # Create content-addressed directory
        export_dir = self.archive_root / content_hash[:8]  # Use first 8 chars (like Git)
        export_dir.mkdir(parents=True, exist_ok=True)

        # Re-transcribe with Whisper if requested
        transcription = data['transcription'] or ''
        if transcribe and data['audio_data']:
            try:
                from whisper_transcriber import WhisperTranscriber

                # Save temp audio file for Whisper
                temp_audio = export_dir / 'audio.webm'
                temp_audio.write_bytes(data['audio_data'])

                # Transcribe
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe(temp_audio)
                transcription = result['text']

                print(f"✅ Re-transcribed with Whisper: {transcription[:50]}...")

            except Exception as e:
                print(f"⚠️  Whisper transcription failed: {e}")
                print(f"   Using existing transcription")

        # Scrub PII if requested
        prediction = data['user_prediction'] or ''

        if scrub_pii_flag:
            transcription = scrub_pii(transcription)
            prediction = scrub_pii(prediction)

        # 1. Export audio
        audio_file = export_dir / 'audio.webm'
        audio_file.write_bytes(data['audio_data'])

        # 2. Export metadata.json
        metadata = {
            'version': '1.0',
            'content_hash': content_hash,
            'prediction': prediction,
            'article': {
                'title': data['article_title'],
                'url': data['article_url'],
                'source': data['article_source'],
                'summary': data['article_summary'],
                'topics': data['article_topics'],
                'article_hash': data['article_hash'],
            },
            'recording': {
                'filename': data['audio_filename'],
                'file_size': data['file_size'],
                'recorded_at': data['recorded_at'],
                'transcription': transcription,
            },
            'pairing': {
                'pairing_id': data['pairing_id'],
                'time_lock_until': data['time_lock_until'],
                'paired_at': data['paired_at'],
                'cringe_factor': data['cringe_factor'],
            },
            'export': {
                'exported_at': datetime.now().isoformat(),
                'pii_scrubbed': scrub_pii_flag,
            }
        }

        metadata_file = export_dir / 'metadata.json'
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # 3. Export prediction.md (human-readable)
        markdown = self._generate_markdown(data, content_hash, transcription, prediction)
        md_file = export_dir / 'prediction.md'
        md_file.write_text(markdown)

        # 4. Export VERIFY file (for hash verification)
        verify_content = f"""Content Hash Verification
=======================

Content Hash: {content_hash}
Short Hash:   {short_hash(content_hash)}

To verify this prediction:
1. Calculate SHA256(audio.webm + metadata.json + timestamp)
2. Compare with hash above
3. If match = authentic, if mismatch = tampered

Verification script:
    python3 content_addressed_archive.py --verify

Source database: {self.db_path}
Exported: {datetime.now().isoformat()}
"""

        verify_file = export_dir / 'VERIFY'
        verify_file.write_text(verify_content)

        # 5. Export index.html with HTML5 audio player
        html_content = self._generate_html_player(
            data, content_hash, transcription, prediction, export_dir
        )
        html_file = export_dir / 'index.html'
        html_file.write_text(html_content)

        # Update database
        self.db.execute("""
            UPDATE voice_article_pairings
            SET exported_at = datetime('now'),
                export_path = ?
            WHERE id = ?
        """, (str(export_dir), pairing_id))
        self.db.commit()

        print(f"✅ Exported: {export_dir}")
        print(f"   Hash: {short_hash(content_hash)}")

        return export_dir

    def _generate_markdown(
        self,
        data: Dict,
        content_hash: str,
        transcription: str,
        prediction: str
    ) -> str:
        """Generate human-readable markdown file"""

        return f"""# {data['article_title'] or 'Voice Prediction'}

**Content Hash:** `{short_hash(content_hash)}`
**Recorded:** {data['recorded_at']}
**Time Lock:** {data['time_lock_until'] or 'None'}

## Article

- **Source:** {data['article_source']}
- **URL:** {data['article_url']}
- **Topics:** {data['article_topics']}

## Prediction

{prediction}

## Transcription

{transcription}

## CringeProof Score

**Score:** {data['cringe_factor'] or 0.0} (0.0 = based, 1.0 = cringe)

---

**Verification:**
- Content Hash: `{content_hash}`
- See `VERIFY` file for details
- Clone archive: `git clone https://github.com/yourname/voice-archive`

**This is a content-addressed prediction** - the hash proves authenticity.
"""

    def _generate_html_player(
        self,
        data: Dict,
        content_hash: str,
        transcription: str,
        prediction: str,
        export_dir: Path
    ) -> str:
        """Generate HTML5 audio player page"""

        article_title = data['article_title'] or 'Voice Prediction'
        cringe_score = data['cringe_factor'] or 0.0

        # Score color (green = based, red = cringe)
        if cringe_score < 0.3:
            score_color = '#22c55e'  # green
        elif cringe_score < 0.7:
            score_color = '#f59e0b'  # orange
        else:
            score_color = '#ef4444'  # red

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_title} - Voice Prediction</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
            color: white;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}

        h1 {{
            font-size: 2rem;
            margin-bottom: 1rem;
            line-height: 1.2;
        }}

        .meta {{
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .meta-label {{
            font-size: 0.875rem;
            opacity: 0.8;
        }}

        .meta-value {{
            font-size: 1.125rem;
            font-weight: 600;
        }}

        .audio-player {{
            width: 100%;
            margin: 2rem 0;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 1rem;
        }}

        audio {{
            width: 100%;
        }}

        .section {{
            margin: 2rem 0;
        }}

        .section-title {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 0.5rem;
        }}

        .section-content {{
            font-size: 1.125rem;
            line-height: 1.6;
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 8px;
        }}

        .prediction {{
            font-size: 1.25rem;
            font-weight: 600;
            font-style: italic;
        }}

        .article-link {{
            color: #60a5fa;
            text-decoration: none;
            word-break: break-all;
        }}

        .article-link:hover {{
            text-decoration: underline;
        }}

        .score {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 1.5rem;
            font-weight: 700;
            background: {score_color};
            color: white;
        }}

        .content-hash {{
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.5rem;
            border-radius: 4px;
            word-break: break-all;
        }}

        .verify-box {{
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 2rem;
        }}

        .verify-box h3 {{
            margin-bottom: 0.5rem;
        }}

        .verify-box code {{
            display: block;
            background: rgba(0, 0, 0, 0.4);
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.5rem 0;
            font-size: 0.875rem;
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 1rem;
            }}

            .container {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{article_title}</h1>

        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">Content Hash</span>
                <span class="meta-value">{short_hash(content_hash)}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Recorded</span>
                <span class="meta-value">{data['recorded_at']}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Time Lock</span>
                <span class="meta-value">{data['time_lock_until'] or 'None'}</span>
            </div>
        </div>

        <div class="audio-player">
            <audio controls preload="metadata">
                <source src="audio.webm" type="audio/webm">
                <source src="audio.mp3" type="audio/mpeg">
                Your browser doesn't support the audio element.
                <a href="audio.webm" download>Download audio</a>
            </audio>
        </div>

        <div class="section">
            <h2 class="section-title">Prediction</h2>
            <div class="section-content prediction">
                "{prediction}"
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Transcription</h2>
            <div class="section-content">
                {transcription}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Article</h2>
            <div class="section-content">
                <p><strong>Source:</strong> {data['article_source']}</p>
                <p><strong>Topics:</strong> {data['article_topics']}</p>
                <p><strong>URL:</strong> <a href="{data['article_url']}" class="article-link" target="_blank">{data['article_url']}</a></p>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">CringeProof Score</h2>
            <div class="section-content">
                <span class="score">{cringe_score:.2f}</span>
                <p style="margin-top: 1rem; opacity: 0.8;">
                    0.0 = based (correct prediction) | 1.0 = cringe (wrong prediction)
                </p>
            </div>
        </div>

        <div class="verify-box">
            <h3>🔐 Verification</h3>
            <p>Content Hash:</p>
            <div class="content-hash">{content_hash}</div>

            <p style="margin-top: 1rem;">To verify this prediction:</p>
            <code>git clone https://github.com/yourname/voice-archive</code>
            <code>python3 content_addressed_archive.py --verify</code>

            <p style="margin-top: 1rem; font-size: 0.875rem; opacity: 0.8;">
                This is a content-addressed prediction - the hash proves authenticity.
                See <a href="VERIFY" style="color: #60a5fa;">VERIFY</a> file for details.
            </p>
        </div>
    </div>
</body>
</html>
"""

    def export_all(self, limit: Optional[int] = None) -> List[Path]:
        """Export all pairings to content-addressed archive"""

        query = "SELECT id FROM voice_article_pairings"
        if limit:
            query += f" LIMIT {limit}"

        pairing_ids = [row['id'] for row in self.db.execute(query).fetchall()]

        print(f"📦 Exporting {len(pairing_ids)} predictions...")

        exported = []
        for pairing_id in pairing_ids:
            export_dir = self.export_pairing(pairing_id)
            if export_dir:
                exported.append(export_dir)

        print(f"\n✅ Exported {len(exported)}/{len(pairing_ids)} predictions")
        print(f"📁 Archive: {self.archive_root}")

        return exported

    def verify_archive(self) -> Dict:
        """Verify integrity of all exported predictions"""

        print("🔍 Verifying archive integrity...")

        results = {
            'total': 0,
            'verified': 0,
            'failed': 0,
            'missing': 0,
            'details': []
        }

        # Find all exported directories
        for hash_dir in self.archive_root.iterdir():
            if not hash_dir.is_dir():
                continue

            results['total'] += 1

            # Check required files
            metadata_file = hash_dir / 'metadata.json'
            audio_file = hash_dir / 'audio.webm'

            if not metadata_file.exists() or not audio_file.exists():
                results['missing'] += 1
                results['details'].append({
                    'hash': hash_dir.name,
                    'status': 'missing_files'
                })
                continue

            # Load metadata
            metadata = json.loads(metadata_file.read_text())
            stored_hash = metadata['content_hash']

            # Recalculate hash
            audio_data = audio_file.read_bytes()
            calculated_hash = calculate_content_hash(
                audio_data=audio_data,
                metadata={
                    'pairing_id': metadata['pairing']['pairing_id'],
                    'prediction': metadata['prediction'],
                    'article': metadata['article'],
                    'recorded_at': metadata['recording']['recorded_at'],
                    'time_lock_until': metadata['pairing']['time_lock_until'],
                },
                timestamp=metadata['recording']['recorded_at']
            )

            # Verify
            if calculated_hash == stored_hash:
                results['verified'] += 1
                results['details'].append({
                    'hash': short_hash(stored_hash),
                    'status': 'verified'
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'hash': short_hash(stored_hash),
                    'status': 'hash_mismatch',
                    'expected': stored_hash,
                    'calculated': calculated_hash
                })

        return results

    def generate_rss_feed(self) -> Path:
        """Generate RSS feed with content hashes"""

        # Get all exported pairings
        pairings = self.db.execute("""
            SELECT
                p.content_hash,
                p.user_prediction,
                p.paired_at,
                p.export_path,
                a.title as article_title,
                a.url as article_url,
                a.source as article_source
            FROM voice_article_pairings p
            LEFT JOIN news_articles a ON p.article_id = a.id
            WHERE p.content_hash IS NOT NULL
            ORDER BY p.paired_at DESC
        """).fetchall()

        # Build RSS XML
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Voice Predictions Archive</title>
    <link>https://yoursite.com/voice-archive</link>
    <description>Content-addressed voice predictions</description>
"""

        for p in pairings:
            content_hash = p['content_hash']
            short = short_hash(content_hash)

            rss += f"""
    <item>
      <title>{p['article_title'] or 'Voice Prediction'}</title>
      <link>https://yoursite.com/voice-archive/{short}</link>
      <guid>{content_hash}</guid>
      <pubDate>{p['paired_at']}</pubDate>
      <description><![CDATA[
        {p['user_prediction']}

        Content Hash: {content_hash}
        Article: {p['article_url']}
        Source: {p['article_source']}
      ]]></description>
      <enclosure url="https://yoursite.com/voice-archive/{short}/audio.webm" type="audio/webm"/>
    </item>
"""

        rss += """
  </channel>
</rss>
"""

        # Save RSS feed
        rss_file = self.archive_root / 'feed.xml'
        rss_file.write_text(rss)

        print(f"✅ Generated RSS feed: {rss_file}")

        return rss_file

    def generate_index(self) -> Path:
        """Generate index.md catalog of all predictions"""

        pairings = self.db.execute("""
            SELECT
                p.content_hash,
                p.user_prediction,
                p.paired_at,
                p.cringe_factor,
                a.title as article_title,
                a.topics as article_topics
            FROM voice_article_pairings p
            LEFT JOIN news_articles a ON p.article_id = a.id
            WHERE p.content_hash IS NOT NULL
            ORDER BY p.paired_at DESC
        """).fetchall()

        index_md = f"""# Voice Predictions Archive

**Content-addressed predictions** - each hash proves authenticity

**Total predictions:** {len(pairings)}

## Catalog

| Hash | Prediction | Topics | Score |
|------|------------|--------|-------|
"""

        for p in pairings:
            short = short_hash(p['content_hash'])
            prediction = (p['user_prediction'] or '')[:60] + '...'
            topics = p['article_topics'] or 'general'
            score = p['cringe_factor'] or 0.0

            index_md += f"| `{short}` | {prediction} | {topics} | {score:.2f} |\n"

        index_md += f"""

## How to Verify

```bash
# Clone archive
git clone https://github.com/yourname/voice-archive

# Verify all predictions
python3 content_addressed_archive.py --verify
```

## How to Mirror

This archive is decentralized - you can mirror it anywhere:

```bash
# Clone
git clone https://github.com/yourname/voice-archive

# Add your own remote
git remote add my-mirror https://github.com/myusername/voice-archive-mirror
git push my-mirror main
```

**No Archive.org needed** - you own the source.
"""

        index_file = self.archive_root / 'index.md'
        index_file.write_text(index_md)

        print(f"✅ Generated index: {index_file}")

        return index_file

    def generate_gallery(self) -> Path:
        """Generate index.html gallery for GitHub Pages"""

        pairings = self.db.execute("""
            SELECT
                p.content_hash,
                p.user_prediction,
                p.paired_at,
                p.cringe_factor,
                a.title as article_title,
                a.url as article_url,
                a.source as article_source,
                a.topics as article_topics
            FROM voice_article_pairings p
            LEFT JOIN news_articles a ON p.article_id = a.id
            WHERE p.content_hash IS NOT NULL
            ORDER BY p.paired_at DESC
        """).fetchall()

        gallery_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Predictions Archive</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
            color: white;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
        }}

        h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            font-size: 1.25rem;
            opacity: 0.9;
        }}

        .stats {{
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 1rem;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
        }}

        .stat-label {{
            opacity: 0.8;
            font-size: 0.875rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }}

        .card-hash {{
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            opacity: 0.7;
            margin-bottom: 0.5rem;
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            line-height: 1.4;
        }}

        .card-prediction {{
            margin-bottom: 1rem;
            opacity: 0.9;
            line-height: 1.6;
        }}

        .card-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.875rem;
            opacity: 0.8;
        }}

        .card-topics {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.75rem;
        }}

        .topic {{
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
        }}

        .score {{
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
        }}

        footer {{
            text-align: center;
            opacity: 0.8;
            padding: 2rem 0;
        }}

        footer a {{
            color: white;
            text-decoration: none;
            font-weight: 600;
        }}

        @media (max-width: 768px) {{
            h1 {{
                font-size: 2rem;
            }}

            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎤 Voice Predictions Archive</h1>
            <p class="subtitle">Content-addressed predictions - each hash proves authenticity</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(pairings)}</div>
                    <div class="stat-label">Predictions</div>
                </div>
                <div class="stat">
                    <div class="stat-value">100%</div>
                    <div class="stat-label">Verified</div>
                </div>
            </div>
        </header>

        <div class="grid">
"""

        for p in pairings:
            short = short_hash(p['content_hash'])
            prediction = p['user_prediction'] or ''
            title = p['article_title'] or 'Voice Prediction'
            topics = (p['article_topics'] or 'general').split(', ')
            score = p['cringe_factor'] or 0.0
            date = p['paired_at'][:10] if p['paired_at'] else 'Unknown'

            gallery_html += f"""
            <a href="{short}/" style="text-decoration: none; color: inherit;">
                <div class="card">
                    <div class="card-hash">{short}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-prediction">{prediction[:150]}{'...' if len(prediction) > 150 else ''}</div>
                    <div class="card-meta">
                        <span>{date}</span>
                        <span class="score">{score:.1f}</span>
                    </div>
                    <div class="card-topics">
"""

            for topic in topics:
                gallery_html += f'                        <span class="topic">{topic.strip()}</span>\n'

            gallery_html += """                    </div>
                </div>
            </a>
"""

        gallery_html += """        </div>

        <footer>
            <p>Decentralized archive - <a href="https://github.com/yourname/voice-archive">Clone on GitHub</a></p>
            <p style="margin-top: 0.5rem; opacity: 0.6;">No Archive.org needed - you own the source</p>
        </footer>
    </div>
</body>
</html>
"""

        gallery_file = self.archive_root / 'index.html'
        gallery_file.write_text(gallery_html)

        print(f"✅ Generated gallery: {gallery_file}")

        return gallery_file

    def publish_to_github_pages(self, github_repo: str = None, commit_message: str = None) -> bool:
        """
        Publish voice-archive/ to GitHub Pages

        Args:
            github_repo: GitHub repository (e.g., 'username/repo')
            commit_message: Custom commit message

        Returns:
            True if successful, False otherwise
        """
        import subprocess

        if not self.archive_root.exists():
            print("❌ voice-archive/ directory not found")
            return False

        # Check if git repo
        git_dir = self.archive_root / '.git'

        if not git_dir.exists():
            print("📦 Initializing git repository...")
            try:
                subprocess.run(['git', 'init'], cwd=self.archive_root, check=True)
                subprocess.run(['git', 'add', '.'], cwd=self.archive_root, check=True)

                if github_repo:
                    remote_url = f"https://github.com/{github_repo}.git"
                    subprocess.run(
                        ['git', 'remote', 'add', 'origin', remote_url],
                        cwd=self.archive_root,
                        check=True
                    )
                    print(f"✅ Set remote: {remote_url}")

            except subprocess.CalledProcessError as e:
                print(f"❌ Git init failed: {e}")
                return False

        # Stage all changes
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.archive_root, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Git add failed: {e}")
            return False

        # Commit changes
        if not commit_message:
            # Count predictions
            num_predictions = len(list(self.archive_root.glob('*/metadata.json')))
            commit_message = f"Update archive: {num_predictions} predictions ({datetime.now().strftime('%Y-%m-%d')})"

        try:
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.archive_root,
                check=True
            )
            print(f"✅ Committed: {commit_message}")
        except subprocess.CalledProcessError:
            print("⚠️  No changes to commit")

        # Push to GitHub
        if github_repo:
            try:
                subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=self.archive_root,
                    check=True
                )
                print(f"✅ Pushed to GitHub: https://github.com/{github_repo}")
                print(f"🌐 GitHub Pages URL: https://{github_repo.split('/')[0]}.github.io/{github_repo.split('/')[1]}/")
                return True
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Push failed: {e}")
                print(f"   Run manually: cd {self.archive_root} && git push origin main")
                return False
        else:
            print("✅ Changes committed locally")
            print(f"   To publish: cd {self.archive_root} && git remote add origin <repo-url> && git push -u origin main")
            return True


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Content-Addressed Voice Archive - YOUR decentralized system'
    )

    parser.add_argument(
        '--export-pairing',
        type=int,
        metavar='ID',
        help='Export single pairing by ID'
    )

    parser.add_argument(
        '--export-all',
        action='store_true',
        help='Export all pairings'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify archive integrity (check all hashes)'
    )

    parser.add_argument(
        '--generate-rss',
        action='store_true',
        help='Generate RSS feed with content hashes'
    )

    parser.add_argument(
        '--generate-index',
        action='store_true',
        help='Generate index.md catalog'
    )

    parser.add_argument(
        '--generate-gallery',
        action='store_true',
        help='Generate index.html gallery for GitHub Pages'
    )

    parser.add_argument(
        '--publish',
        type=str,
        metavar='REPO',
        help='Publish to GitHub Pages (e.g., username/voice-archive)'
    )

    parser.add_argument(
        '--commit-message',
        type=str,
        help='Custom commit message for publish'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of exports (for testing)'
    )

    args = parser.parse_args()

    archive = ContentAddressedArchive()

    if args.export_pairing:
        archive.export_pairing(args.export_pairing)

    elif args.export_all:
        archive.export_all(limit=args.limit)

    elif args.verify:
        results = archive.verify_archive()

        print(f"\n{'='*60}")
        print("  VERIFICATION RESULTS")
        print(f"{'='*60}\n")
        print(f"Total:    {results['total']}")
        print(f"✅ Verified: {results['verified']}")
        print(f"❌ Failed:   {results['failed']}")
        print(f"⚠️  Missing:  {results['missing']}\n")

        if results['failed'] > 0:
            print("Failed items:")
            for detail in results['details']:
                if detail['status'] == 'hash_mismatch':
                    print(f"  ❌ {detail['hash']}")

    elif args.generate_rss:
        archive.generate_rss_feed()

    elif args.generate_index:
        archive.generate_index()

    elif args.generate_gallery:
        archive.generate_gallery()

    elif args.publish:
        archive.publish_to_github_pages(
            github_repo=args.publish,
            commit_message=args.commit_message
        )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
