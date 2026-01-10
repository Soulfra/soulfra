#!/usr/bin/env python3
"""
Voice Dev Studio - Code Without Typing
Speak your code, AI writes it for you.

Routes:
  /voice-dev - Voice-to-code interface
  /voice-content - Voice-to-content pipeline
  /voice-studio - Voice dev dashboard

  /api/voice/transcribe - Transcribe audio
  /api/voice/code-gen - Generate code from voice
  /api/voice/content-gen - Generate content from voice
"""

from flask import Blueprint, render_template, request, jsonify, session
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

voice_dev_bp = Blueprint('voice_dev', __name__)

# Ollama config
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def call_ollama(prompt, model='llama3.2:latest'):
    """Call local Ollama for code/content generation"""
    try:
        data = {
            'model': model,
            'prompt': prompt,
            'stream': False
        }

        req = urllib.request.Request(
            f'{OLLAMA_HOST}/api/generate',
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '')
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return f"Error: {e}"


def transcribe_audio(audio_path):
    """Transcribe audio using Whisper (local or API)"""
    # TODO: Add Whisper integration
    # For now, return mock transcription
    return "[Transcription: User said something about building a Flask route]"


@voice_dev_bp.route('/voice-dev')
def voice_dev_interface():
    """Voice-to-Code Interface"""
    return render_template('voice_dev.html')


@voice_dev_bp.route('/voice-content')
def voice_content_interface():
    """Voice-to-Content Pipeline"""
    return render_template('voice_content.html')


@voice_dev_bp.route('/voice-studio')
def voice_studio_dashboard():
    """Voice Dev Dashboard - manage all voice recordings"""
    # Get all voice recordings
    voice_dir = Path('voice_recordings')
    voice_dir.mkdir(exist_ok=True)

    recordings = []
    for file in voice_dir.glob('*.webm'):
        recordings.append({
            'filename': file.name,
            'timestamp': file.stat().st_mtime,
            'size': file.stat().st_size,
            'type': 'unknown'  # TODO: AI categorization
        })

    recordings.sort(key=lambda x: x['timestamp'], reverse=True)

    return render_template('voice_studio.html', recordings=recordings)


@voice_dev_bp.route('/shortcuts')
def shortcuts_page():
    """Siri Shortcuts download and setup page"""
    return render_template('shortcuts.html')


@voice_dev_bp.route('/api/voice/transcribe', methods=['POST'])
def api_transcribe():
    """
    Transcribe audio file to text

    Request:
      - audio file (webm/mp3/wav)

    Response:
      {
        "success": true,
        "transcription": "Build me a Flask route...",
        "confidence": 0.95
      }
    """
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio = request.files['audio']

    # Save audio
    voice_dir = Path('voice_recordings')
    voice_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'voice_dev_{timestamp}.webm'
    audio_path = voice_dir / filename

    audio.save(str(audio_path))

    # Transcribe
    transcription = transcribe_audio(str(audio_path))

    return jsonify({
        'success': True,
        'transcription': transcription,
        'confidence': 0.95,
        'audio_url': f'/voice_recordings/{filename}'
    })


@voice_dev_bp.route('/api/voice/code-gen', methods=['POST'])
def api_code_gen():
    """
    Generate code from voice transcription

    Request:
      {
        "transcription": "Build me a Flask route that handles user auth",
        "language": "python",
        "context": "This is for a web app..."
      }

    Response:
      {
        "success": true,
        "code": "from flask import...",
        "explanation": "This code creates...",
        "filename": "auth_route.py"
      }
    """
    data = request.json
    transcription = data.get('transcription', '')
    language = data.get('language', 'python')
    context = data.get('context', '')

    if not transcription:
        return jsonify({'success': False, 'error': 'No transcription provided'}), 400

    # Build prompt for code generation
    prompt = f"""You are a code generator. The user said:

"{transcription}"

Context: {context}

Generate clean, working {language} code based on what they said.
Include comments and follow best practices.
Only output the code, no explanations outside code comments.

Code:"""

    # Generate code using Ollama
    code = call_ollama(prompt)

    # Clean up code (remove markdown if present)
    if '```' in code:
        code = code.split('```')[1]
        if code.startswith('python\n'):
            code = code[7:]

    # Generate filename
    filename = f"voice_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    # Generate explanation
    explain_prompt = f"""Explain this code in 2-3 sentences:

{code}

Explanation:"""

    explanation = call_ollama(explain_prompt)

    # Format for Siri Shortcuts
    result = {
        'success': True,
        'code': code.strip(),
        'explanation': explanation.strip(),
        'filename': filename,
        'language': language,
        # Siri-specific fields
        'clipboard_text': code.strip(),
        'notification': f"✅ {language.title()} code generated! Paste with Cmd+V",
        'speak_text': "Code is ready in your clipboard"
    }

    return jsonify(result)


@voice_dev_bp.route('/api/voice/content-gen', methods=['POST'])
def api_content_gen():
    """
    Generate content (blog, tweet, video script) from voice

    Request:
      {
        "transcription": "I was thinking about how programmers...",
        "format": "blog|tweet|video|docs"
      }

    Response:
      {
        "success": true,
        "content": {
          "blog": "# How Programmers...",
          "tweet_thread": ["1/ ...", "2/ ..."],
          "video_script": "Intro: ...",
          "docs": "## Documentation..."
        }
      }
    """
    data = request.json
    transcription = data.get('transcription', '')
    output_format = data.get('format', 'all')

    if not transcription:
        return jsonify({'success': False, 'error': 'No transcription provided'}), 400

    content = {}

    # Generate blog post
    if output_format in ['blog', 'all']:
        blog_prompt = f"""Convert this voice memo into a blog post:

"{transcription}"

Write a professional blog post with:
- Catchy title
- Introduction
- 3-5 main points
- Conclusion
- Markdown formatting

Blog post:"""

        content['blog'] = call_ollama(blog_prompt)

    # Generate tweet thread
    if output_format in ['tweet', 'all']:
        tweet_prompt = f"""Convert this into a Twitter thread (max 280 chars per tweet):

"{transcription}"

Create 5-7 tweets numbered 1/, 2/, etc.

Thread:"""

        thread = call_ollama(tweet_prompt)
        content['tweet_thread'] = thread.split('\n\n')

    # Generate video script
    if output_format in ['video', 'all']:
        video_prompt = f"""Convert this into a video script:

"{transcription}"

Format:
[INTRO - 0:00-0:15]
Hook and intro

[MAIN CONTENT - 0:15-2:00]
Key points

[OUTRO - 2:00-2:30]
Call to action

Script:"""

        content['video_script'] = call_ollama(video_prompt)

    # Generate documentation
    if output_format in ['docs', 'all']:
        docs_prompt = f"""Convert this into technical documentation:

"{transcription}"

Format as proper markdown docs with:
- Title
- Overview
- Usage
- Examples

Docs:"""

        content['docs'] = call_ollama(docs_prompt)

    # Format for Siri Shortcuts
    result = {
        'success': True,
        'content': content,
        'original': transcription,
        # Siri-specific fields
        'clipboard_text': content.get('blog', ''),
        'notification': f"✅ Generated {len(content)} content formats!",
        'speak_text': "Your content is ready. Check your clipboard for the blog post."
    }

    return jsonify(result)


@voice_dev_bp.route('/api/voice/categorize', methods=['POST'])
def api_categorize():
    """
    Categorize voice recording

    Request:
      {
        "transcription": "..."
      }

    Response:
      {
        "category": "code_request|content_idea|bug_report|feature_request|general",
        "priority": "high|medium|low",
        "tags": ["flask", "authentication"]
      }
    """
    data = request.json
    transcription = data.get('transcription', '')

    categorize_prompt = f"""Categorize this voice memo:

"{transcription}"

Respond in JSON:
{{
  "category": "code_request|content_idea|bug_report|feature_request|general",
  "priority": "high|medium|low",
  "tags": ["tag1", "tag2"]
}}

JSON:"""

    result = call_ollama(categorize_prompt)

    try:
        categorization = json.loads(result)
    except:
        categorization = {
            'category': 'general',
            'priority': 'medium',
            'tags': []
        }

    return jsonify(categorization)


def register_voice_dev_routes(app):
    """Register voice dev routes with Flask app"""
    app.register_blueprint(voice_dev_bp)
    print('🎤 Voice Dev Studio routes registered')
    print('   Interface: /voice-dev')
    print('   Content: /voice-content')
    print('   Dashboard: /voice-studio')
    print('   Siri Shortcuts: /shortcuts')


# Testing
if __name__ == '__main__':
    print('🎤 Voice Dev Studio')
    print('Routes:')
    print('  /voice-dev - Voice-to-code interface')
    print('  /voice-content - Voice-to-content pipeline')
    print('  /voice-studio - Voice dev dashboard')
