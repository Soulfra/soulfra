#!/usr/bin/env python3
"""
Wordmap → Pitch Deck Integrator

Combines brand wordmap analysis with voice-to-pitch-deck generation.

Flow:
1. Extract brand wordmap from voice transcript
2. Use wordmap to guide Ollama pitch deck generation
3. Create pitch deck that speaks in the brand's voice

This is the "binary filter" - uses wordmap to decide if content is brand-aligned.
"""

from typing import Dict, List, Optional
from collections import Counter
import re
from database import get_db
from voice_content_generator import VoiceContentGenerator


def tokenize(text: str) -> List[str]:
    """Simple tokenization - lowercase, alphanumeric only"""
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    return words


def extract_wordmap_from_transcript(transcript: str, top_n: int = 30) -> Dict[str, int]:
    """
    Extract wordmap (top vocabulary) from transcript

    Args:
        transcript: Voice memo transcript
        top_n: Number of top words to extract

    Returns:
        dict: {'word': count, ...}
    """
    # Tokenize
    words = tokenize(transcript)

    # Count word frequencies
    word_counts = Counter(words)

    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'from', 'by', 'as', 'is', 'was', 'are', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'it', 'its', 'we', 'you', 'they', 'them', 'their', 'i', 'me', 'my',
        'your', 'our', 'like', 'just', 'really', 'very', 'so', 'yeah', 'know'
    }

    # Filter stop words and short words
    filtered_counts = {
        word: count for word, count in word_counts.items()
        if word not in stop_words and len(word) > 3
    }

    # Get top N
    top_words = Counter(filtered_counts).most_common(top_n)

    return dict(top_words)


def calculate_wordmap_alignment(wordmap: Dict[str, int], text: str) -> float:
    """
    Calculate how well text aligns with wordmap (0.0 - 1.0)

    This is the "binary filter" - decides if content matches brand voice.

    Args:
        wordmap: Brand wordmap {'word': frequency}
        text: Text to check

    Returns:
        float: Alignment score (0.0 = no match, 1.0 = perfect match)
    """
    if not wordmap:
        return 0.0

    # Tokenize text
    words = tokenize(text)
    word_counts = Counter(words)

    # Count how many wordmap words appear in text
    matches = 0
    total_wordmap_words = len(wordmap)

    for word in wordmap:
        if word in word_counts:
            matches += 1

    # Calculate alignment percentage
    alignment = matches / total_wordmap_words if total_wordmap_words > 0 else 0.0

    return alignment


def generate_brand_aware_pitch_deck(
    recording_id: int,
    brand: Optional[str] = None,
    model: str = 'llama3.2:3b'
) -> Dict:
    """
    Generate pitch deck using wordmap-guided Ollama generation

    Args:
        recording_id: Voice recording ID
        brand: Optional brand slug (defaults to user's primary domain)
        model: Ollama model to use

    Returns:
        {
            'pitch_deck': {...},
            'wordmap': {'word': count, ...},
            'alignment_score': float (0.0-1.0),
            'brand': str
        }
    """
    db = get_db()

    # Get recording
    recording = db.execute('''
        SELECT id, filename, transcription, user_id, created_at
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return {'error': f'Recording {recording_id} not found'}

    if not recording['transcription']:
        return {
            'error': 'Recording has no transcription',
            'recording_id': recording_id
        }

    transcript = recording['transcription']

    # Get brand (user's primary domain if not specified)
    if not brand:
        from domain_unlock_engine import get_primary_domain
        primary_domain = get_primary_domain(recording['user_id'])
        brand = primary_domain['domain'] if primary_domain else 'soulfra.com'

    # Extract wordmap from transcript
    wordmap = extract_wordmap_from_transcript(transcript, top_n=30)

    # Generate pitch deck using voice content generator
    generator = VoiceContentGenerator(model=model)

    # Build enhanced system prompt with wordmap guidance
    wordmap_words = ', '.join(list(wordmap.keys())[:15])

    enhanced_system_prompt = f"""You are a pitch deck expert helping {brand} create compelling presentations.

BRAND VOCABULARY: Focus on using these key terms that define {brand}'s voice:
{wordmap_words}

Transform voice transcripts into professional pitch deck slides.

Each slide should have:
- A clear title (5-10 words)
- 3-5 bullet points (short, punchy)
- Use the brand vocabulary where natural

Focus on: problem, solution, market, traction, team, ask.

Return valid JSON with this structure:
{{
    "title": "Overall deck title",
    "slides": [
        {{"title": "Slide Title", "bullets": ["Point 1", "Point 2", "Point 3"]}},
        ...
    ]
}}"""

    # Generate pitch deck with wordmap-guided prompt
    prompt = f"""Based on this voice memo, create a pitch deck:

"{transcript}"

Generate 5-7 slides that tell a compelling story about {brand}.
Use the brand's vocabulary naturally.
Return valid JSON only."""

    try:
        result = generator.client.generate(
            prompt=prompt,
            model=model,
            system_prompt=enhanced_system_prompt,
            temperature=0.7,
            max_tokens=1200,
            timeout=90
        )

        if not result['success']:
            return {
                'error': result.get('error', 'Ollama generation failed'),
                'brand': brand,
                'wordmap': wordmap
            }

        # Parse Ollama JSON response
        response_text = result['response'].strip()
        pitch_data = generator._extract_json(response_text)

        if not pitch_data:
            return {
                'error': 'Failed to parse pitch deck JSON',
                'raw_response': response_text[:500],
                'brand': brand,
                'wordmap': wordmap
            }

        # Calculate alignment score - how well does the pitch deck use brand wordmap?
        pitch_text = ' '.join([
            pitch_data.get('title', ''),
            ' '.join([
                slide.get('title', '') + ' ' + ' '.join(slide.get('bullets', []))
                for slide in pitch_data.get('slides', [])
            ])
        ])

        alignment_score = calculate_wordmap_alignment(wordmap, pitch_text)

        # Add metadata
        pitch_data['domain'] = brand
        pitch_data['brand'] = brand
        pitch_data['total_slides'] = len(pitch_data.get('slides', []))
        pitch_data['recording_id'] = recording_id
        pitch_data['model'] = model
        pitch_data['wordmap'] = wordmap
        pitch_data['alignment_score'] = alignment_score
        pitch_data['alignment_quality'] = (
            '🟢 Excellent' if alignment_score > 0.6 else
            '🟡 Good' if alignment_score > 0.4 else
            '🟠 Fair' if alignment_score > 0.2 else
            '🔴 Weak'
        )

        return pitch_data

    except Exception as e:
        return {
            'error': str(e),
            'brand': brand,
            'wordmap': wordmap
        }


def batch_generate_brand_pitches(user_id: int, brand: Optional[str] = None, limit: int = 5) -> List[Dict]:
    """
    Generate brand-aware pitch decks for multiple voice recordings

    Args:
        user_id: User ID
        brand: Optional brand slug
        limit: Number of recordings to process

    Returns:
        List of pitch deck results with wordmap alignment scores
    """
    db = get_db()

    recordings = db.execute('''
        SELECT id
        FROM simple_voice_recordings
        WHERE user_id = ?
        AND transcription IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    results = []
    for rec in recordings:
        pitch_data = generate_brand_aware_pitch_deck(rec['id'], brand=brand)
        if pitch_data:
            results.append(pitch_data)

    return results


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 wordmap_pitch_integrator.py <recording_id>")
        print("  python3 wordmap_pitch_integrator.py <recording_id> <brand>")
        sys.exit(1)

    recording_id = int(sys.argv[1])
    brand = sys.argv[2] if len(sys.argv) > 2 else None

    result = generate_brand_aware_pitch_deck(recording_id, brand=brand)
    print(json.dumps(result, indent=2))
