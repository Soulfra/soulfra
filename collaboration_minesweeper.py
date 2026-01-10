#!/usr/bin/env python3
"""
Collaboration Minesweeper - Interview Edition

Like minesweeper, but for revealing collaboration networks through STAR interview stories.

Game Mechanics:
- Record voice answering interview questions
- But flip it: Shine light on TEAMMATES, not yourself
- Each story reveals connections
- Board fills in as network grows
- Numbers = how many times someone gets mentioned
- Win = Full collaboration graph revealed

STAR Format:
- Situation: What was the context?
- Task: What needed to be done?
- Action: What did YOUR TEAMMATE do?
- Result: What was the outcome?

Example:
"Tell me about a time a teammate solved a hard problem"
→ Extract: {person: "Sarah", skill: "debugging", outcome: "found race condition"}
→ Sarah's score += 1
→ Link created in collaboration graph
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
import json
from datetime import datetime
import re

collab_bp = Blueprint('collaboration', __name__)

def create_collaboration_tables():
    """Create tables for collaboration tracking"""
    db = get_db()

    # People mentioned in stories
    db.execute('''
        CREATE TABLE IF NOT EXISTS collaboration_people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            github_username TEXT,
            mention_count INTEGER DEFAULT 0,
            positive_mentions INTEGER DEFAULT 0,
            skills_mentioned TEXT,  -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Individual stories (STAR format)
    db.execute('''
        CREATE TABLE IF NOT EXISTS star_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recording_id INTEGER REFERENCES simple_voice_recordings(id),
            storyteller_id INTEGER REFERENCES users(id),
            person_mentioned TEXT,  -- Who they're shining light on
            situation TEXT,
            task TEXT,
            action TEXT,  -- What the TEAMMATE did
            result TEXT,
            skills_demonstrated TEXT,  -- JSON array
            impact_level INTEGER,  -- 1-5 scale
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Collaboration graph (connections between people)
    db.execute('''
        CREATE TABLE IF NOT EXISTS collaboration_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_a TEXT,
            person_b TEXT,
            project TEXT,
            interaction_type TEXT,  -- "mentored", "paired", "collaborated"
            story_id INTEGER REFERENCES star_stories(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Minesweeper board state
    db.execute('''
        CREATE TABLE IF NOT EXISTS minesweeper_board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT UNIQUE,
            revealed BOOLEAN DEFAULT FALSE,
            adjacent_mentions INTEGER DEFAULT 0,  -- Like the numbers in minesweeper
            x_position INTEGER,
            y_position INTEGER
        )
    ''')

    db.commit()

# Initialize tables
try:
    create_collaboration_tables()
except:
    pass

def extract_person_from_transcript(transcript):
    """
    Extract person's name from interview story
    Uses simple heuristics - can be enhanced with Ollama
    """
    # Common patterns:
    # "I worked with Sarah..."
    # "My teammate John..."
    # "Sarah helped me..."

    patterns = [
        r"worked with (\w+)",
        r"teammate (\w+)",
        r"(\w+) helped",
        r"(\w+) showed me",
        r"paired with (\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def extract_star_components(transcript):
    """
    Extract STAR components from transcript
    Can be enhanced with Ollama for better extraction
    """
    # Simple keyword-based extraction
    # In production, use Ollama to properly parse

    components = {
        'situation': '',
        'task': '',
        'action': '',
        'result': '',
        'skills': []
    }

    # Look for result indicators
    result_keywords = ['resulted in', 'outcome was', 'ended up', 'finally', 'succeeded']
    for keyword in result_keywords:
        if keyword in transcript.lower():
            idx = transcript.lower().index(keyword)
            components['result'] = transcript[idx:idx+200]

    # Look for action indicators
    action_keywords = ['they ', 'she ', 'he ', 'fixed', 'debugged', 'refactored', 'designed']
    for keyword in action_keywords:
        if keyword in transcript.lower():
            idx = transcript.lower().index(keyword)
            components['action'] = transcript[idx:idx+200]

    # Extract skills
    skill_keywords = ['debugging', 'refactoring', 'design', 'leadership', 'communication',
                     'problem solving', 'architecture', 'testing', 'mentoring']
    components['skills'] = [skill for skill in skill_keywords if skill in transcript.lower()]

    return components

@collab_bp.route('/api/collaboration/record-story', methods=['POST'])
def record_star_story():
    """
    Record a STAR interview story about a teammate

    POST body:
    {
        "recording_id": 16,
        "transcript": "I worked with Sarah on...",
        "question": "Tell me about a time a teammate solved a hard problem"
    }
    """
    data = request.json
    recording_id = data.get('recording_id')
    transcript = data.get('transcript', '')
    question = data.get('question', '')

    if not recording_id:
        return jsonify({'error': 'recording_id required'}), 400

    db = get_db()

    # Extract person mentioned
    person_name = extract_person_from_transcript(transcript)

    if not person_name:
        return jsonify({
            'success': False,
            'error': 'Could not identify teammate in story',
            'tip': 'Try mentioning their name explicitly'
        }), 400

    # Extract STAR components
    star = extract_star_components(transcript)

    # Store story
    cursor = db.execute('''
        INSERT INTO star_stories (
            recording_id, person_mentioned, situation, task, action, result, skills_demonstrated
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        recording_id,
        person_name,
        star.get('situation', ''),
        question,  # The interview question IS the task
        star.get('action', ''),
        star.get('result', ''),
        json.dumps(star.get('skills', []))
    ))
    story_id = cursor.lastrowid

    # Update person's mention count
    existing = db.execute(
        'SELECT id, mention_count, skills_mentioned FROM collaboration_people WHERE name = ?',
        (person_name,)
    ).fetchone()

    if existing:
        # Merge skills
        existing_skills = json.loads(existing['skills_mentioned'] or '[]')
        new_skills = list(set(existing_skills + star.get('skills', [])))

        db.execute('''
            UPDATE collaboration_people
            SET mention_count = mention_count + 1,
                positive_mentions = positive_mentions + 1,
                skills_mentioned = ?
            WHERE name = ?
        ''', (json.dumps(new_skills), person_name))
    else:
        # Create new person
        db.execute('''
            INSERT INTO collaboration_people (name, mention_count, positive_mentions, skills_mentioned)
            VALUES (?, 1, 1, ?)
        ''', (person_name, json.dumps(star.get('skills', []))))

    db.commit()

    return jsonify({
        'success': True,
        'story_id': story_id,
        'person_mentioned': person_name,
        'mention_count': (existing['mention_count'] + 1) if existing else 1,
        'skills_found': star.get('skills', []),
        'message': f'✨ You shined a light on {person_name}!'
    })


@collab_bp.route('/api/collaboration/board')
def get_minesweeper_board():
    """
    Get current minesweeper board state

    Returns grid of people with mention counts (like minesweeper numbers)
    """
    db = get_db()

    people = db.execute('''
        SELECT name, mention_count, positive_mentions, skills_mentioned
        FROM collaboration_people
        ORDER BY mention_count DESC
    ''').fetchall()

    board = []
    for person in people:
        board.append({
            'name': person['name'],
            'mentions': person['mention_count'],  # The "number" in minesweeper
            'positive': person['positive_mentions'],
            'skills': json.loads(person['skills_mentioned'] or '[]'),
            'revealed': True  # They've been mentioned, so "revealed"
        })

    return jsonify({
        'success': True,
        'board': board,
        'total_people': len(board),
        'total_stories': db.execute('SELECT COUNT(*) as count FROM star_stories').fetchone()['count']
    })


@collab_bp.route('/api/collaboration/person/<name>')
def get_person_details(name):
    """Get all stories mentioning this person"""
    db = get_db()

    person = db.execute(
        'SELECT * FROM collaboration_people WHERE name = ?',
        (name,)
    ).fetchone()

    if not person:
        return jsonify({'error': 'Person not found'}), 404

    stories = db.execute('''
        SELECT s.*, r.transcription, r.created_at
        FROM star_stories s
        LEFT JOIN simple_voice_recordings r ON s.recording_id = r.id
        WHERE s.person_mentioned = ?
        ORDER BY s.created_at DESC
    ''', (name,)).fetchall()

    return jsonify({
        'success': True,
        'person': {
            'name': person['name'],
            'github_username': person['github_username'],
            'mention_count': person['mention_count'],
            'positive_mentions': person['positive_mentions'],
            'skills': json.loads(person['skills_mentioned'] or '[]')
        },
        'stories': [
            {
                'id': s['id'],
                'task': s['task'],
                'action': s['action'],
                'result': s['result'],
                'skills': json.loads(s['skills_demonstrated'] or '[]'),
                'created_at': s['created_at'],
                'full_transcript': s['transcription']
            }
            for s in stories
        ]
    })


@collab_bp.route('/api/collaboration/stats')
def collaboration_stats():
    """Overall collaboration network stats"""
    db = get_db()

    stats = {
        'total_people_mentioned': db.execute('SELECT COUNT(*) as count FROM collaboration_people').fetchone()['count'],
        'total_stories': db.execute('SELECT COUNT(*) as count FROM star_stories').fetchone()['count'],
        'most_mentioned': None,
        'network_density': 0
    }

    # Most mentioned person
    top_person = db.execute('''
        SELECT name, mention_count, skills_mentioned
        FROM collaboration_people
        ORDER BY mention_count DESC
        LIMIT 1
    ''').fetchone()

    if top_person:
        stats['most_mentioned'] = {
            'name': top_person['name'],
            'mentions': top_person['mention_count'],
            'skills': json.loads(top_person['skills_mentioned'] or '[]')
        }

    return jsonify({
        'success': True,
        **stats
    })
