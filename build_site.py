#!/usr/bin/env python3
"""
Soulfra Static Site Generator

Generates all HTML pages from templates and content.
ONE source of truth → multiple outputs.
"""

import os
import sqlite3
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Optional
import json

class SiteBuilder:
    def __init__(self, voice_archive_dir: str = "voice-archive"):
        self.voice_archive = Path(voice_archive_dir)
        self.db_path = Path("soulfra.db")

        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.voice_archive / "_includes")),
            autoescape=True
        )

        # Base URL for production
        self.base_url = "https://soulfra.github.io/voice-archive"

    def build_all(self):
        """Build entire site"""
        print("\n🏗️  Building Soulfra Voice Archive Site...")
        print("="*60)

        # Build pages
        self.build_index()
        self.build_ideas_hub()
        self.build_audio_players()
        self.build_prediction_pages()
        self.build_inbox()

        print("\n✅ Site build complete!")
        print("="*60 + "\n")

    def build_index(self):
        """Build main gallery page"""
        print("\n📄 Building index.html...")

        # Get predictions from database or files
        predictions = self._get_predictions()

        html = self._render_template("gallery.html", {
            'title': 'Voice Predictions Archive',
            'description': 'Permanent decentralized voice memo archive',
            'predictions': predictions,
            'base_url': '.'
        })

        output_path = self.voice_archive / "index.html"
        output_path.write_text(html)
        print(f"   ✅ {output_path}")

    def build_ideas_hub(self):
        """Build ideas hub page"""
        print("\n📄 Building ideas/index.html...")

        # Get ideas from database
        ideas = self._get_ideas()

        html = self._render_template("ideas.html", {
            'title': 'Voice Ideas',
            'description': 'AI-extracted concepts from voice memos',
            'ideas': ideas,
            'total_ideas': len(ideas),
            'total_recordings': len(set(i['recording_id'] for i in ideas)),
            'base_url': '..'
        })

        output_path = self.voice_archive / "ideas" / "index.html"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(html)
        print(f"   ✅ {output_path}")

    def build_audio_players(self):
        """Build audio player pages"""
        print("\n📄 Building audio player pages...")

        # Get all recordings
        recordings = self._get_recordings()

        for rec in recordings:
            html = self._render_template("audio_player.html", {
                'title': f'Voice Recording #{rec["id"]}',
                'description': f'Voice recording from {rec["created_at"]}',
                'recording': rec,
                'base_url': '../..'
            })

            output_path = self.voice_archive / "audio" / str(rec['id']) / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
            print(f"   ✅ audio/{rec['id']}/index.html")

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render a template with context"""
        # Create full page template
        template_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{{% include 'head.html' %}}
</head>
<body>
{{% include 'nav.html' %}}

<div class="container">
{{% block content %}}
{{% endblock %}}
</div>

{{% include 'footer.html' %}}
</body>
</html>"""

        # Load specific template content
        if template_name == "gallery.html":
            content_block = self._gallery_template()
        elif template_name == "ideas.html":
            content_block = self._ideas_template()
        elif template_name == "audio_player.html":
            content_block = self._audio_player_template()
        elif template_name == "prediction.html":
            content_block = self._prediction_template()
        elif template_name == "inbox.html":
            content_block = self._inbox_template()
        else:
            content_block = ""

        # Combine
        full_template = template_html.replace("{% block content %}", content_block).replace("{% endblock %}", "")

        # Render with Jinja2
        template = self.env.from_string(full_template)
        return template.render(**context)

    def _gallery_template(self) -> str:
        """Template for main gallery"""
        return """
<header>
    <h1>🎤 Voice Predictions Archive</h1>
    <p class="subtitle">Permanent decentralized voice memo archive</p>
</header>

<div class="grid">
    {% for prediction in predictions %}
    <a href="{{ prediction.hash }}/" style="text-decoration: none; color: inherit;">
        <div class="card">
            <div class="card-header">
                <div class="card-id">#{{ prediction.pairing_id }}</div>
            </div>
            <h2 class="card-title">{{ prediction.title }}</h2>
            <p class="card-summary">{{ prediction.summary }}</p>

            <div class="card-domains">
                {% if 'calriven' in prediction.domains %}
                <span class="domain-badge badge-calriven">CalRiven</span>
                {% endif %}
                {% if 'deathtodata' in prediction.domains %}
                <span class="domain-badge badge-deathtodata">DeathToData</span>
                {% endif %}
                {% if 'soulfra' in prediction.domains %}
                <span class="domain-badge badge-soulfra">Soulfra</span>
                {% endif %}
            </div>
        </div>
    </a>
    {% endfor %}
</div>
"""

    def _ideas_template(self) -> str:
        """Template for ideas hub"""
        return """
<header>
    <h1>💡 Voice Ideas</h1>
    <p class="subtitle">AI-extracted concepts from voice memos</p>
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{{ total_ideas }}</div>
            <div class="stat-label">Ideas Extracted</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ total_recordings }}</div>
            <div class="stat-label">Voice Recordings</div>
        </div>
    </div>
</header>

<div class="grid">
    {% for idea in ideas %}
    <div class="card">
        <div class="card-header">
            <div class="card-id">#{{ idea.id }}</div>
        </div>
        <h2 class="card-title">{{ idea.title }}</h2>
        <p class="card-summary">{{ idea.summary }}</p>

        {% if idea.tags %}
        <div class="card-tags">
            {% for tag in idea.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}

        {% if idea.domains %}
        <div class="card-domains">
            {% for domain in idea.domains %}
            {% if domain == 'soulfra' %}
            <span class="domain-badge badge-soulfra">Soulfra</span>
            {% elif domain == 'calriven' %}
            <span class="domain-badge badge-calriven">CalRiven</span>
            {% elif domain == 'deathtodata' %}
            <span class="domain-badge badge-deathtodata">DeathToData</span>
            {% endif %}
            {% endfor %}
        </div>
        {% endif %}

        <div class="card-footer">
            <a href="idea-{{ idea.id }}-{{ idea.slug }}.md" class="card-link">View Full Idea →</a>
            <a href="../audio/{{ idea.recording_id }}/" class="card-link voice-link">🎤 Voice Recording</a>
        </div>
    </div>
    {% endfor %}
</div>
"""

    def _audio_player_template(self) -> str:
        """Template for audio player"""
        return """
<header>
    <h1>🎤 Voice Recording #{{ recording.id }}</h1>
</header>

<audio controls preload="metadata">
    <source src="recording.{{ recording.ext }}" type="audio/{{ recording.mime_type }}">
    Your browser doesn't support audio playback.
</audio>

<div class="meta">
    <p>Recorded: {{ recording.created_at }}</p>
    {% if recording.has_transcription %}
    <p><a href="../../ideas/">← Browse Ideas</a></p>
    {% endif %}
</div>
"""

    def _get_predictions(self) -> List[Dict]:
        """Get all predictions"""
        # Check if d489b26c directory exists
        pred_dir = self.voice_archive / "d489b26c"
        if pred_dir.exists():
            return [{
                'hash': 'd489b26c',
                'pairing_id': 1,
                'title': 'CringeProof Prediction',
                'summary': 'Voice prediction about ideas and CringeProof game',
                'domains': ['soulfra', 'calriven']
            }]
        return []

    def _get_ideas(self) -> List[Dict]:
        """Get all ideas from database"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute('''
            SELECT id, recording_id, title, text, ai_insight
            FROM voice_ideas
            ORDER BY id
        ''')

        ideas = []
        for row in cursor.fetchall():
            # Extract tags and domains from ai_insight JSON if available
            tags = []
            domains = []

            if row['ai_insight']:
                try:
                    insight = json.loads(row['ai_insight'])
                    tags = insight.get('tags', [])
                    domains = insight.get('domains', [])
                except (json.JSONDecodeError, TypeError):
                    pass

            # Extract summary from text
            summary = row['text'][:150] + "..." if len(row['text']) > 150 else row['text']

            # Create slug from title
            slug = row['title'].lower().replace(' ', '-').replace(',', '').replace('?', '')[:50]

            ideas.append({
                'id': row['id'],
                'recording_id': row['recording_id'],
                'title': row['title'],
                'summary': summary,
                'tags': tags,
                'domains': domains,
                'slug': slug
            })

        conn.close()
        return ideas

    def _get_recordings(self) -> List[Dict]:
        """Get all recordings"""
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute('''
            SELECT id, filename, transcription, created_at
            FROM simple_voice_recordings
            WHERE audio_data IS NOT NULL
            ORDER BY id
        ''')

        recordings = []
        for row in cursor.fetchall():
            filename = row['filename'] or f"recording_{row['id']}.webm"

            # Determine file extension and MIME type
            if filename.endswith('.wav'):
                ext = 'wav'
                mime_type = 'wav'
            else:
                ext = 'webm'
                mime_type = 'webm'

            recordings.append({
                'id': row['id'],
                'created_at': row['created_at'],
                'ext': ext,
                'mime_type': mime_type,
                'has_transcription': row['transcription'] is not None
            })

        conn.close()
        return recordings


    def build_prediction_pages(self):
        """Build prediction pages (content-addressed)"""
        print("\n📄 Building prediction pages...")

        # Find all prediction directories
        pred_dirs = [d for d in self.voice_archive.iterdir() if d.is_dir() and len(d.name) == 8 and d.name != 'database']

        for pred_dir in pred_dirs:
            # Read prediction metadata if exists
            metadata_file = pred_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    'title': 'Voice Prediction',
                    'pairing_id': 1,
                    'hash': pred_dir.name
                }

            html = self._render_template("prediction.html", {
                'title': metadata.get('title', 'Voice Prediction'),
                'description': 'Content-addressed voice prediction',
                'metadata': metadata,
                'hash': pred_dir.name,
                'base_url': '..'
            })

            output_path = pred_dir / "index.html"
            output_path.write_text(html)
            print(f"   ✅ {pred_dir.name}/index.html")

    def build_inbox(self):
        """Build inbox page"""
        print("\n📄 Building inbox.html...")

        # Get all recordings
        recordings = self._get_recordings()

        html = self._render_template("inbox.html", {
            'title': 'Voice Message Inbox',
            'description': 'Listen to all voice messages',
            'recordings': recordings,
            'base_url': '.'
        })

        output_path = self.voice_archive / "inbox.html"
        output_path.write_text(html)
        print(f"   ✅ inbox.html")

    def _prediction_template(self) -> str:
        """Template for prediction pages"""
        return """
<header>
    <h1>{{ metadata.title }}</h1>
</header>

<div class="prediction-meta">
    <span class="hash">Hash: {{ hash }}</span>
    <span class="pairing">Pairing #{{ metadata.pairing_id }}</span>
</div>

{% if metadata.audio_file %}
<audio controls preload="metadata">
    <source src="{{ metadata.audio_file }}" type="audio/webm">
    Your browser doesn't support audio playback.
</audio>
{% endif %}

<div class="prediction-content">
    {{ metadata.prediction | default("Voice prediction content") }}
</div>

<div class="nav-links">
    <a href="../">← Back to Gallery</a>
    <a href="../ideas/">Browse Ideas →</a>
</div>
"""

    def _inbox_template(self) -> str:
        """Template for inbox page"""
        return """
<header>
    <h1>📬 Voice Message Inbox</h1>
    <p class="subtitle">Listen to all voice messages</p>
</header>

<div class="messages">
    {% for rec in recordings %}
    <div class="message-card">
        <div class="message-header">
            <h3>Recording #{{ rec.id }}</h3>
            <span class="date">{{ rec.created_at }}</span>
        </div>

        <audio controls preload="metadata">
            <source src="audio/{{ rec.id }}/recording.{{ rec.ext }}" type="audio/{{ rec.mime_type }}">
        </audio>

        <div class="message-footer">
            <a href="audio/{{ rec.id }}/" class="card-link">Open Player →</a>
            {% if rec.has_transcription %}
            <a href="ideas/" class="card-link">View Ideas →</a>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
"""


if __name__ == '__main__':
    builder = SiteBuilder()
    builder.build_all()
