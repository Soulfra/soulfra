#!/usr/bin/env python3
"""
Voice Podcast Chapters - Turn Voice Recordings into Tutorial Series

Convert voice recordings into structured podcast/tutorial content:
- Upload voice → Auto-transcribe → Generate chapters
- AI extracts key points, timestamps, questions
- Creates tutorial-style learning content
- Integrates with chapter_tutorials.py system

Use cases:
- Record training seminar → Auto-generate tutorial
- Upload podcast episode → Extract chapters + quiz questions
- Voice brain dump → Structured learning content

Usage:
    # Create podcast from voice recording
    python3 voice_podcast_chapters.py --recording-id 5

    # Create from file
    python3 voice_podcast_chapters.py --file seminar.webm --title "Brand Building 101"

    # Generate chapters with timestamps
    python3 voice_podcast_chapters.py --recording-id 3 --auto-chapters
"""

import argparse
from typing import List, Dict, Optional
from database import get_db
from datetime import datetime
import json


def create_podcast_from_recording(recording_id: int, title: Optional[str] = None,
                                   description: Optional[str] = None,
                                   auto_chapters: bool = True) -> Dict:
    """
    Convert voice recording into podcast episode with chapters

    Args:
        recording_id: Database ID of recording
        title: Episode title
        description: Episode description
        auto_chapters: Auto-generate chapters with AI

    Returns:
        Podcast episode dict with chapters
    """
    db = get_db()

    # Get recording
    recording = db.execute('''
        SELECT id, filename, transcription, created_at, user_id
        FROM simple_voice_recordings
        WHERE id = ?
    ''', (recording_id,)).fetchone()

    if not recording:
        return {'error': f'Recording {recording_id} not found'}

    if not recording['transcription']:
        return {'error': 'Recording has no transcription'}

    transcription = recording['transcription']

    # Auto-generate title/description if not provided
    if not title or not description:
        print("🤖 Generating title and description with AI...")
        try:
            from voice_ollama_processor import VoiceOllamaProcessor
            processor = VoiceOllamaProcessor()

            analysis = processor.analyze_transcript(transcription)

            if not title:
                # Use first topic or generate from content
                topics = analysis.get('key_topics', [])
                title = topics[0] if topics else f"Episode from {recording['created_at']}"

            if not description:
                # Use brand voice version or first 200 chars
                brand_voice = analysis.get('brand_voice', transcription)
                description = brand_voice[:200] + "..." if len(brand_voice) > 200 else brand_voice

        except:
            title = title or f"Episode {recording_id}"
            description = description or transcription[:200]

    # Generate chapters
    chapters = []

    if auto_chapters:
        print("📖 Generating chapters...")
        chapters = generate_chapters_from_transcript(transcription)

    # Create podcast episode in database
    cursor = db.execute('''
        INSERT INTO voice_podcast_episodes
        (recording_id, title, description, transcription, chapters_json, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        recording_id,
        title,
        description,
        transcription,
        json.dumps(chapters),
        recording['user_id'],
        datetime.now().isoformat()
    ))

    episode_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"✅ Created podcast episode #{episode_id}")
    print(f"   Title: {title}")
    print(f"   Chapters: {len(chapters)}")

    return {
        'episode_id': episode_id,
        'title': title,
        'description': description,
        'chapters': chapters,
        'recording_id': recording_id
    }


def generate_chapters_from_transcript(transcription: str) -> List[Dict]:
    """
    Generate podcast chapters from transcript using AI

    Args:
        transcription: Full transcript text

    Returns:
        List of chapter dicts with title, content, timestamp
    """
    try:
        from ollama_client import OllamaClient

        client = OllamaClient()

        # Build prompt for chapter generation
        system_prompt = """You are a podcast chapter generator.
Analyze the transcript and break it into logical chapters.

For each chapter, provide:
- title: Short descriptive title
- key_points: 2-3 main points covered
- timestamp: Estimated start time (format: "0:00", "5:30", etc.)
- quiz_question: A question to test understanding

Return valid JSON array of chapters."""

        chapter_prompt = f"""Analyze this transcript and create chapters:

"{transcription[:2000]}"

Return JSON array of chapters with title, key_points, timestamp, quiz_question."""

        result = client.generate(
            prompt=chapter_prompt,
            model='llama3.2',
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )

        if result['success']:
            # Try to parse JSON from response
            response_text = result['response'].strip()

            # Extract JSON from response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response_text)

            if json_match:
                chapters = json.loads(json_match.group(0))
                print(f"   Generated {len(chapters)} chapters")
                return chapters

    except Exception as e:
        print(f"   ⚠️ Chapter generation failed: {e}")

    # Fallback: Simple chapter split by paragraphs
    paragraphs = [p.strip() for p in transcription.split('\n\n') if p.strip()]

    chapters = []
    for i, para in enumerate(paragraphs[:5], 1):  # Max 5 chapters
        chapters.append({
            'title': f'Chapter {i}',
            'content': para[:200],
            'timestamp': f"{(i-1)*2}:00",  # Estimate 2 min per chapter
            'key_points': [para[:50] + "..."],
            'quiz_question': None
        })

    return chapters


def generate_quiz_from_episode(episode_id: int) -> List[Dict]:
    """
    Generate quiz questions from podcast episode

    Args:
        episode_id: Episode ID

    Returns:
        List of quiz question dicts
    """
    db = get_db()

    episode = db.execute('''
        SELECT chapters_json, transcription
        FROM voice_podcast_episodes
        WHERE id = ?
    ''', (episode_id,)).fetchone()

    if not episode:
        return []

    chapters = json.loads(episode['chapters_json']) if episode['chapters_json'] else []

    # Extract quiz questions from chapters
    quiz_questions = []

    for chapter in chapters:
        if chapter.get('quiz_question'):
            quiz_questions.append({
                'question': chapter['quiz_question'],
                'chapter_title': chapter.get('title'),
                'answer_hint': chapter.get('key_points', [])
            })

    # Generate additional questions with AI
    if len(quiz_questions) < 3:
        try:
            from voice_ollama_processor import VoiceOllamaProcessor
            processor = VoiceOllamaProcessor()

            # Use transcript to generate questions
            analysis = processor.analyze_transcript(episode['transcription'])

            if 'follow_up_questions' in analysis:
                for q in analysis['follow_up_questions'][:3]:
                    quiz_questions.append({
                        'question': q,
                        'chapter_title': 'General',
                        'answer_hint': analysis.get('key_topics', [])
                    })

        except:
            pass

    db.close()

    return quiz_questions


def convert_episode_to_tutorial(episode_id: int, chapter_num: int = None) -> Dict:
    """
    Convert podcast episode into chapter_tutorials.py format

    Args:
        episode_id: Episode ID
        chapter_num: Chapter number in tutorial system

    Returns:
        Tutorial dict compatible with chapter_tutorials.py
    """
    db = get_db()

    episode = db.execute('''
        SELECT title, description, chapters_json
        FROM voice_podcast_episodes
        WHERE id = ?
    ''', (episode_id,)).fetchone()

    if not episode:
        return {'error': 'Episode not found'}

    chapters = json.loads(episode['chapters_json']) if episode['chapters_json'] else []

    # Convert to tutorial format
    tutorial = {
        'title': episode['title'],
        'description': episode['description'],
        'steps': []
    }

    for i, chapter in enumerate(chapters, 1):
        step = {
            'title': chapter.get('title', f'Step {i}'),
            'content': chapter.get('content', ''),
            'timestamp': chapter.get('timestamp'),
            'key_points': chapter.get('key_points', [])
        }

        if chapter.get('quiz_question'):
            step['quiz_question'] = chapter['quiz_question']
            step['quiz_options'] = []  # Can be filled in manually
            step['quiz_answer'] = 0

        tutorial['steps'].append(step)

    db.close()

    return tutorial


def init_podcast_tables():
    """Initialize podcast/chapter tables"""
    db = get_db()

    # Podcast episodes
    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_podcast_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            transcription TEXT,
            chapters_json TEXT,
            duration_seconds INTEGER,
            user_id INTEGER,
            published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recording_id) REFERENCES simple_voice_recordings(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Episode quiz questions
    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_podcast_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            chapter_title TEXT,
            answer_hint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (episode_id) REFERENCES voice_podcast_episodes(id)
        )
    ''')

    # Episode completion tracking
    db.execute('''
        CREATE TABLE IF NOT EXISTS voice_podcast_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            completed_chapters JSON,
            quiz_score INTEGER,
            completed_at TIMESTAMP,
            FOREIGN KEY (episode_id) REFERENCES voice_podcast_episodes(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(episode_id, user_id)
        )
    ''')

    db.commit()
    db.close()

    print("✅ Podcast tables initialized")


def main():
    parser = argparse.ArgumentParser(description="Voice Podcast Chapters")
    parser.add_argument('--init', action='store_true', help='Initialize podcast tables')
    parser.add_argument('--recording-id', type=int, help='Recording ID to convert')
    parser.add_argument('--file', type=str, help='Upload webm file and create podcast')
    parser.add_argument('--title', type=str, help='Episode title')
    parser.add_argument('--description', type=str, help='Episode description')
    parser.add_argument('--auto-chapters', action='store_true', default=True, help='Auto-generate chapters')
    parser.add_argument('--quiz', type=int, help='Generate quiz from episode ID')
    parser.add_argument('--to-tutorial', type=int, help='Convert episode to tutorial format')

    args = parser.parse_args()

    if args.init:
        init_podcast_tables()

    elif args.recording_id:
        result = create_podcast_from_recording(
            args.recording_id,
            title=args.title,
            description=args.description,
            auto_chapters=args.auto_chapters
        )

        if 'error' not in result:
            print("\n📖 Podcast Episode Created:")
            print(json.dumps(result, indent=2))

    elif args.file:
        # Upload file first, then create podcast
        print("📂 Uploading file...")
        # (Would integrate with test_voice_integration.py)
        print("⚠️  Use test_voice_integration.py first to upload file")

    elif args.quiz:
        questions = generate_quiz_from_episode(args.quiz)
        print(f"\n📝 Quiz Questions for Episode {args.quiz}:")
        print(json.dumps(questions, indent=2))

    elif args.to_tutorial:
        tutorial = convert_episode_to_tutorial(args.to_tutorial)
        print(f"\n📚 Tutorial Format:")
        print(json.dumps(tutorial, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
