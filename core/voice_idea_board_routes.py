#!/usr/bin/env python3
"""
Voice Idea Board - MySpace-style Top Ideas from Voice Recordings

Backend for voice_idea_board.html:
- Save voice → Transcribe → AI extracts ideas
- Rank ideas by score (MySpace Top Friends style)
- Expand ideas with AI
- Merge similar ideas
- Living/Dead document lifecycle

Concepts:
- Living Side: Active, evolving ideas
- Dead Side: Archived "burned" ideas (1-year cycle)
- Rings/Challenges: Gamified progression through idea quality
"""

from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
from datetime import datetime, timedelta
import tempfile
import os
import json
from typing import List, Dict

voice_idea_bp = Blueprint('voice_ideas', __name__)


@voice_idea_bp.route('/voice-ideas')
def idea_board_page():
    """Voice Idea Board page"""
    return render_template('voice_idea_board.html')


@voice_idea_bp.route('/api/voice-ideas/save', methods=['POST'])
def save_voice_idea():
    """
    Save voice recording + extract ideas with AI

    Flow:
    1. Save audio
    2. Transcribe with Whisper
    3. Ollama extracts key ideas (top N)
    4. Score each idea (0-100)
    5. Store with "living" status

    Returns:
        - ideas: List of extracted ideas with scores
        - recording_id: Database ID
    """
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    if not audio_data:
        return jsonify({'success': False, 'error': 'Empty audio'}), 400

    user_id = session.get('user_id', 1)
    filename = f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

    # Transcribe with Whisper
    transcription = None

    try:
        from whisper_transcriber import WhisperTranscriber

        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(tmp_path)
        transcription = result['text']

        os.unlink(tmp_path)

    except Exception as e:
        print(f"⚠️  Transcription failed: {e}")
        transcription = "[NO TRANSCRIPTION]"

    # Save recording
    db = get_db()

    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, len(audio_data), transcription, 'whisper', user_id))

    recording_id = cursor.lastrowid
    db.commit()

    # Extract ideas with Ollama
    ideas = extract_ideas_from_transcript(transcription, recording_id, user_id)

    # Save ideas to database
    for idea in ideas:
        db.execute('''
            INSERT INTO voice_ideas (recording_id, user_id, title, text, score, ai_insight, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recording_id,
            user_id,
            idea['title'],
            idea['text'],
            idea['score'],
            idea.get('ai_insight'),
            'living',  # Start as "living" document
            datetime.now().isoformat()
        ))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'recording_id': recording_id,
        'ideas': ideas,
        'transcription': transcription
    })


def extract_ideas_from_transcript(transcription: str, recording_id: int, user_id: int) -> List[Dict]:
    """
    Extract top ideas from transcript using Ollama

    Args:
        transcription: Full transcript text
        recording_id: Recording ID
        user_id: User ID

    Returns:
        List of idea dicts with title, text, score, insight
    """
    if not transcription or transcription == "[NO TRANSCRIPTION]":
        return []

    try:
        from ollama_client import OllamaClient

        client = OllamaClient()

        system_prompt = """You are an idea extractor. Analyze voice transcripts and extract the TOP ideas.

For each idea, return:
- title: Short catchy title (3-5 words)
- text: Core idea (1-2 sentences)
- score: Quality score 0-100 (novelty + clarity + feasibility)
- insight: Why this idea matters (1 sentence)

Return JSON array of top 3-5 ideas. Focus on clarity and actionability."""

        prompt = f"""Extract the top ideas from this voice transcript:

"{transcription}"

Return JSON array of ideas with title, text, score, insight."""

        result = client.generate(
            prompt=prompt,
            model='llama3.2',
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800,
            timeout=30
        )

        if result['success']:
            response_text = result['response'].strip()

            # Extract JSON
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)

            if json_match:
                ideas = json.loads(json_match.group(0))
                return ideas[:5]  # Top 5 max

    except Exception as e:
        print(f"⚠️  Idea extraction failed: {e}")

    # Fallback: Create idea from transcript (smarter extraction)
    # Try to use first sentence as title
    sentences = transcription.split('.')
    first_sentence = sentences[0].strip() if sentences else transcription
    title_words = first_sentence.split()[:6]  # First 6 words
    title = ' '.join(title_words) if title_words else 'Voice Idea'

    return [{
        'title': title,
        'text': transcription[:300],  # More text for context
        'score': 50,
        'ai_insight': 'Needs AI extraction - Ollama may be offline. Click Expand to retry.'
    }]


@voice_idea_bp.route('/api/voice-ideas/list')
def list_ideas():
    """
    Get all ideas (living + dead), sorted by score

    Returns:
        - ideas: All ideas with metadata
        - stats: Total ideas, recordings, top score
    """
    user_id = session.get('user_id', 1)
    db = get_db()

    ideas = db.execute('''
        SELECT id, title, text, score, ai_insight, status, created_at, merged_count
        FROM voice_ideas
        WHERE user_id = ?
        ORDER BY score DESC, created_at DESC
    ''', (user_id,)).fetchall()

    total_recordings = db.execute('''
        SELECT COUNT(*) as count FROM simple_voice_recordings WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    db.close()

    ideas_list = [dict(idea) for idea in ideas]

    stats = {
        'total_ideas': len(ideas_list),
        'total_recordings': total_recordings,
        'top_score': ideas_list[0]['score'] if ideas_list else 0,
        'living_count': sum(1 for i in ideas_list if i['status'] == 'living'),
        'dead_count': sum(1 for i in ideas_list if i['status'] == 'dead')
    }

    return jsonify({
        'success': True,
        'ideas': ideas_list,
        'stats': stats
    })


@voice_idea_bp.route('/api/voice-ideas/expand', methods=['POST'])
def expand_idea():
    """
    Expand idea with more AI-generated detail

    Takes idea, sends to Ollama for elaboration
    """
    data = request.get_json()
    idea_id = data.get('idea_id')

    if not idea_id:
        return jsonify({'success': False, 'error': 'Missing idea_id'}), 400

    db = get_db()

    idea = db.execute('''
        SELECT id, title, text, score, ai_insight
        FROM voice_ideas
        WHERE id = ?
    ''', (idea_id,)).fetchone()

    if not idea:
        db.close()
        return jsonify({'success': False, 'error': 'Idea not found'}), 404

    # Expand with AI
    try:
        from ollama_client import OllamaClient

        client = OllamaClient()

        prompt = f"""Expand this idea with more detail and actionable steps:

Title: {idea['title']}
Idea: {idea['text']}

Provide:
1. Detailed explanation (2-3 sentences)
2. 3 actionable next steps
3. Potential challenges

Return as JSON with fields: explanation, steps[], challenges"""

        result = client.generate(
            prompt=prompt,
            model='llama3.2',
            temperature=0.7,
            max_tokens=500
        )

        if result['success']:
            # Parse expansion
            import re
            json_match = re.search(r'\{[\s\S]*\}', result['response'])

            if json_match:
                expansion = json.loads(json_match.group(0))

                # Update idea with expansion
                db.execute('''
                    UPDATE voice_ideas
                    SET ai_insight = ?, score = score + 5
                    WHERE id = ?
                ''', (json.dumps(expansion), idea_id))

                db.commit()
                db.close()

                return jsonify({
                    'success': True,
                    'expansion': expansion
                })

    except Exception as e:
        print(f"⚠️  Expansion failed: {e}")

    db.close()
    return jsonify({'success': False, 'error': 'Failed to expand'}), 500


@voice_idea_bp.route('/api/voice-ideas/merge', methods=['POST'])
def merge_idea():
    """
    Merge similar ideas together

    Finds similar ideas, combines them, increases score
    """
    data = request.get_json()
    idea_id = data.get('idea_id')

    if not idea_id:
        return jsonify({'success': False, 'error': 'Missing idea_id'}), 400

    user_id = session.get('user_id', 1)
    db = get_db()

    idea = db.execute('''
        SELECT id, title, text, score
        FROM voice_ideas
        WHERE id = ?
    ''', (idea_id,)).fetchone()

    if not idea:
        db.close()
        return jsonify({'success': False, 'error': 'Idea not found'}), 404

    # Find similar ideas (simple keyword matching for now)
    keywords = set(idea['text'].lower().split())

    similar_ideas = db.execute('''
        SELECT id, title, text, score
        FROM voice_ideas
        WHERE user_id = ? AND id != ? AND status = 'living'
    ''', (user_id, idea_id)).fetchall()

    merged_count = 0

    for similar in similar_ideas:
        similar_keywords = set(similar['text'].lower().split())
        overlap = len(keywords & similar_keywords)

        if overlap >= 3:  # At least 3 common words
            # Mark as merged
            db.execute('''
                UPDATE voice_ideas
                SET status = 'merged_into_' || ?
                WHERE id = ?
            ''', (idea_id, similar['id']))

            merged_count += 1

    # Boost main idea score
    if merged_count > 0:
        db.execute('''
            UPDATE voice_ideas
            SET score = score + (? * 10), merged_count = merged_count + ?
            WHERE id = ?
        ''', (merged_count, merged_count, idea_id))

    db.commit()
    db.close()

    return jsonify({
        'success': True if merged_count > 0 else False,
        'merged_count': merged_count
    })


@voice_idea_bp.route('/api/voice-ideas/burn', methods=['POST'])
def burn_idea():
    """
    "Burn" an idea - move to dead side

    Ideas older than 1 year auto-burn
    Or manually burn low-scoring ideas
    """
    data = request.get_json()
    idea_id = data.get('idea_id')

    db = get_db()

    db.execute('''
        UPDATE voice_ideas
        SET status = 'dead', burned_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), idea_id))

    db.commit()
    db.close()

    return jsonify({'success': True})


def init_voice_idea_tables():
    """Initialize voice idea board tables"""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER,
            user_id INTEGER,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            score INTEGER DEFAULT 50,
            ai_insight TEXT,
            status TEXT DEFAULT 'living',
            merged_count INTEGER DEFAULT 0,
            burned_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Voice idea tables created")


def register_voice_idea_routes(app):
    """Register voice idea board routes"""
    app.register_blueprint(voice_idea_bp)
    print("✅ Voice Idea Board routes registered:")
    print("   - /voice-ideas (Idea board page)")
    print("   - /api/voice-ideas/save (Save + extract ideas)")
    print("   - /api/voice-ideas/list (Get all ideas)")
    print("   - /api/voice-ideas/expand (AI expand idea)")
    print("   - /api/voice-ideas/merge (Merge similar ideas)")
    print("   - /api/voice-ideas/burn (Archive idea)")


if __name__ == '__main__':
    init_voice_idea_tables()
